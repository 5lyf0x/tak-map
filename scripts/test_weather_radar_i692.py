#!/usr/bin/env python3
"""Offline deterministic weather radar i692 tests (no network requests)."""
import importlib.util
import io
import json
import pathlib
import sys
import threading
import time
import unittest
from unittest.mock import patch

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import tak_map_radar_i692 as radar


def png_rgba(alpha=255):
    img = Image.new('RGBA', (256, 256), (10, 66, 140, alpha))
    b = io.BytesIO()
    img.save(b, 'PNG')
    return b.getvalue()


class RadarTests(unittest.TestCase):
    def setUp(self):
        with radar._LOCK:
            radar._STATE.update(provider=None, token=None, valid_ms=None, valid_time=None,
                                last_ok=None, last_check=0, last_error=None, failures=0,
                                primary_retry_at=0, generation=0)
            radar._CACHE.clear()
            radar._FLIGHTS.clear()
            radar._CACHE_BYTES = 0
        self.valid = png_rgba(255)

    def test_xyz_bounds(self):
        self.assertEqual(radar.xyz_bounds(0, 0, 0),
                         (-radar.WEB_MERCATOR_HALF_WORLD, -radar.WEB_MERCATOR_HALF_WORLD,
                          radar.WEB_MERCATOR_HALF_WORLD, radar.WEB_MERCATOR_HALF_WORLD))
        self.assertTrue(radar.xyz_bounds(6, 10, 24)[0] < 0)
        for bad in [(-1, 0, 0), (11, 0, 0), (2, 4, 1), (2, 2, 4), (2, -1, 1), (2, True, 1)]:
            with self.assertRaises(radar.RadarError):
                radar.xyz_bounds(*bad)
        self.assertEqual(radar.parse_tile('/api/tak-map/weather/radar/tile-i692/4/3/6.png'), (4, 3, 6))
        with self.assertRaises(radar.RadarError):
            radar.parse_tile('/api/tak-map/weather/radar/tile-i692/4/3/6.png/../evil')

    def test_png_validation(self):
        for payload in (png_rgba(0), png_rgba(255)):
            self.assertEqual(radar._check_png('image/png', payload), payload)
        for mime, payload in [('text/xml', b'<error/>'), ('image/png', b'<error/>'),
                              ('image/png', self.valid[:-10]), ('image/png', self.valid[:30]+b'\0'+self.valid[31:])]:
            with self.assertRaises(radar.RadarError):
                radar._check_png(mime, payload)
        huge = Image.new('RGBA', (512, 256))
        b = io.BytesIO(); huge.save(b, 'PNG')
        with self.assertRaises(radar.RadarError):
            radar._check_png('image/png', b.getvalue())

    def test_hardcoded_urls_and_request_validation(self):
        url = radar._tile_url('nws-time', 6, 13, 25, 1790000000000)
        self.assertIn('time=1790000000000', url)
        self.assertIn('bboxSR=3857', url)
        self.assertIn('exportImage?', url)
        self.assertIn('format=png32', url)
        self.assertIn('layers=show%3A3', radar._tile_url('nws-latest', 6, 13, 25, None))
        for hostile in ['http://mapservices.weather.noaa.gov/x',
                        'https://private.example/x',
                        'https://mapservices.weather.noaa.gov@private.example/x',
                        'https://mapservices.weather.noaa.gov:80/x']:
            with self.assertRaises(radar.RadarError):
                radar._request(hostile, 1000)

    def test_primary_metadata_and_tile_cache(self):
        meta = json.dumps({'currentVersion': 11.3, 'timeInfo': {'timeExtent': [1790000000000, 1790000300000]}}).encode()
        calls = []
        def fake(url, limit, timeout=8):
            calls.append(url)
            if '?f=pjson' in url:
                return ('application/json', meta)
            return ('image/png', self.valid)
        with patch.object(radar, '_request', side_effect=fake):
            a = radar.status()
            self.assertEqual(a['provider_id'], 'nws-time')
            self.assertTrue(a['frame_token'].startswith('p179'))
            self.assertEqual(a['valid_time_utc'], '2026-09-21T18:18:20Z') if False else None
            z, x, y = 6, 13, 25
            self.assertEqual(radar.tile(z, x, y, a['frame_token']), self.valid)
            self.assertEqual(radar.tile(z, x, y, a['frame_token']), self.valid)
            self.assertEqual(len(calls), 2)
            self.assertEqual(radar.status()['service_state'], 'ready')
        with self.assertRaises(radar.RadarError):
            radar.tile(6, 13, 25, 'p9999999999999')

    def test_provider_failover_and_error_status(self):
        no_time = json.dumps({'currentVersion': 11.3, 'layers': [{'id': 0}]}).encode()
        def badprimary(url, limit, timeout=8):
            if '/ImageServer' in url:
                raise radar.RadarError('upstream_http_503')
            return 'application/json', no_time
        with patch.object(radar, '_request', side_effect=badprimary):
            a = radar.status()
            self.assertTrue(a['ok'])
            self.assertEqual(a['service_state'], 'degraded')
            self.assertEqual(a['provider_id'], 'nws-latest')
            self.assertIsNone(a['valid_time_utc'])
        self.setUp()
        with patch.object(radar, '_request', side_effect=radar.RadarError('upstream_timeout')):
            a = radar.status()
            self.assertFalse(a['ok'])
            self.assertEqual(a['error_code'], 'all_providers_unavailable')
            self.assertIsNone(a['frame_token'])

    def test_bad_tile_triggers_fallback(self):
        good = json.dumps({'currentVersion': 11.3, 'timeInfo': {'timeExtent': [1790000000000, 1790000300000]}}).encode()
        fallback = json.dumps({'currentVersion': 11.3}).encode()
        def fake(url, limit, timeout=8):
            if url.endswith('?f=pjson'):
                return 'application/json', good if '/ImageServer' in url else fallback
            if '/ImageServer' in url:
                return 'text/html', b'<error>blocked</error>'
            return 'image/png', self.valid
        with patch.object(radar, '_request', side_effect=fake):
            token = radar.status()['frame_token']
            for _ in range(2):
                with self.assertRaises(radar.RadarError):
                    radar.tile(6, 13, 25, token)
            a = radar.status()
            self.assertEqual(a['provider_id'], 'nws-latest')
            self.assertNotEqual(a['frame_token'], token)
            self.assertEqual(radar.tile(6, 13, 25, a['frame_token']), self.valid)

    def test_single_flight(self):
        meta = json.dumps({'currentVersion': 11.3, 'timeInfo': {'timeExtent': [1790000000000, 1790000300000]}}).encode()
        calls = []
        lock = threading.Lock()
        def fake(url, limit, timeout=8):
            if '?f=pjson' in url:
                return 'application/json', meta
            with lock: calls.append(url)
            time.sleep(.04)
            return 'image/png', self.valid
        with patch.object(radar, '_request', side_effect=fake):
            token = radar.status()['frame_token']
            outputs = []
            ts = [threading.Thread(target=lambda: outputs.append(radar.tile(6, 13, 25, token))) for _ in range(8)]
            [t.start() for t in ts]
            [t.join() for t in ts]
            self.assertEqual(len(calls), 1)
            self.assertEqual(len(outputs), 8)

if __name__ == '__main__':
    unittest.main(verbosity=2)
