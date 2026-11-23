#!/usr/bin/env python3
"""Deterministic i693 NWS radar proxy tests; no outbound network."""
import io, json, sys, threading, time, unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import tak_map_radar_i693 as r

def png(alpha=255):
    im=Image.new('RGBA',(256,256),(36,133,225,alpha));o=io.BytesIO();im.save(o,'PNG');return o.getvalue()

def meta():
    return json.dumps({'currentVersion':11.3,'timeInfo':{'timeExtent':[1790000000000,1790000500000]}}).encode()

def cat(t=1790000200000):
    return json.dumps({'features':[{'attributes':{'idp_validtime':t}}]}).encode()

class RadarI693Tests(unittest.TestCase):
    def setUp(self):
        with r._LOCK:
            r._STATE.update(provider=None,token=None,valid_ms=None,valid_time=None,last_ok=None,last_check=0.,last_error=None,failures=0,
              frame_source=None,tile_errors=0,tile_successes=0,last_tile_error=None,last_tile_error_at=0.,primary_retry_at=0.,generation=0)
            r._CACHE.clear();r._FLIGHTS.clear();r._RECENT_TILE_ERRORS.clear();r._CACHE_BYTES=0
        self.img=png()
    def fake(self,url,lim,timeout=8):
        if '/query?' in url:return ('application/json',cat())
        if '?f=pjson' in url:return ('application/json',meta())
        return ('image/png',self.img)
    def test_verified_catalog_frame_not_metadata_end(self):
        with patch.object(r,'_request',side_effect=self.fake):
            s=r.status()
            self.assertEqual(s['frame_token'],'p1790000200000')
            self.assertNotEqual(s['frame_token'],'p1790000500000')
            self.assertEqual(s['frame_source'],'catalog_observation')
            self.assertTrue(s['observation_verified'])
            self.assertEqual(r.tile(9,85,206,s['frame_token']),self.img)
            self.assertEqual(r.status()['service_state'],'ready')
    def test_provisional_time_is_labeled(self):
        def f(url,lim,timeout=8):
            if '/query?' in url:raise r.RadarError('upstream_http_503')
            if '?f=pjson' in url:return 'application/json',meta()
            return 'image/png',self.img
        with patch.object(r,'_request',side_effect=f):
            s=r.status()
            self.assertEqual(s['frame_source'],'time_range_provisional')
            self.assertFalse(s['observation_verified'])
    def test_isolated_tile_failure_no_global_provider_reset(self):
        failures={'n':0}
        def f(url,lim,timeout=8):
            if '/query?' in url or '?f=pjson' in url:return self.fake(url,lim,timeout)
            if 'bbox=' in url and 'exportImage' in url:
                # Fail first tile 3 attempts; other tiles still work
                if failures['n']<3:
                    failures['n']+=1;raise r.RadarError('upstream_http_503')
            return 'image/png',self.img
        with patch.object(r,'_request',side_effect=f), patch.object(r.time,'sleep',return_value=None):
            token=r.status()['frame_token']
            with self.assertRaises(r.RadarError):r.tile(9,85,206,token)
            self.assertEqual(r.status()['frame_token'],token)
            self.assertEqual(r.status()['provider_id'],'nws-time')
            self.assertEqual(r.tile(9,86,206,token),self.img)
            self.assertEqual(r.status()['frame_token'],token)
            self.assertEqual(r.status()['recent_tile_errors'],1)
    def test_tile_retry_success_and_cache(self):
        attempts=[]
        def f(url,lim,timeout=8):
            if '/query?' in url or '?f=pjson' in url:return self.fake(url,lim,timeout)
            attempts.append(url)
            if len(attempts)<3:raise r.RadarError('upstream_connection')
            return 'image/png',self.img
        with patch.object(r,'_request',side_effect=f), patch.object(r.time,'sleep',return_value=None):
            t=r.status()['frame_token'];self.assertEqual(r.tile(9,85,206,t),self.img)
            self.assertEqual(r.tile(9,85,206,t),self.img)
            self.assertEqual(len(attempts),3)
            self.assertEqual(r.status()['total_tile_errors'],0)
    def test_transparent_tile_is_valid(self):
        trans=png(0)
        def f(url,lim,timeout=8):
            if '/query?' in url or '?f=pjson' in url:return self.fake(url,lim,timeout)
            return 'image/png',trans
        with patch.object(r,'_request',side_effect=f):
            t=r.status()['frame_token'];self.assertEqual(r.tile(9,85,206,t),trans)
            self.assertEqual(r.status()['total_tile_successes'],1)
    def test_metadata_outage_retains_recent_frame(self):
        with patch.object(r,'_request',side_effect=self.fake):
            s=r.status();r.tile(9,85,206,s['frame_token'])
        with r._LOCK:r._STATE['last_check']=0
        with patch.object(r,'_request',side_effect=r.RadarError('upstream_connection')):
            s=r.status();self.assertTrue(s['ok']);self.assertEqual(s['frame_token'],'p1790000200000')
            self.assertEqual(s['service_state'],'degraded')
    def test_invalid_inputs_and_proxy_guard(self):
        for triple in [(11,1,1),(9,512,0),(9,-1,0),(9,0,512),(True,1,1)]:
            with self.assertRaises(r.RadarError):r.xyz_bounds(*triple)
        self.assertEqual(r.parse_tile('/api/tak-map/weather/radar/tile-i693/9/85/206.png'),(9,85,206))
        with self.assertRaises(r.RadarError):r.parse_tile('/api/tak-map/weather/radar/tile-i693/9/85/206.png/evil')
        for u in ['http://mapservices.weather.noaa.gov/foo','https://bad.example/x','https://mapservices.weather.noaa.gov@bad.example/x']:
            with self.assertRaises(r.RadarError):r._request(u,1000)
    def test_single_flight_deduplicates(self):
        calls=[];lk=threading.Lock()
        def f(url,lim,timeout=8):
            if '/query?' in url or '?f=pjson' in url:return self.fake(url,lim,timeout)
            with lk:calls.append(url)
            time.sleep(.04)
            return 'image/png',self.img
        with patch.object(r,'_request',side_effect=f):
            t=r.status()['frame_token'];got=[]
            threads=[threading.Thread(target=lambda:got.append(r.tile(9,85,206,t))) for _ in range(8)]
            [th.start() for th in threads];[th.join() for th in threads]
            self.assertEqual(len(calls),1);self.assertEqual(len(got),8)

if __name__=='__main__':unittest.main(verbosity=2)
