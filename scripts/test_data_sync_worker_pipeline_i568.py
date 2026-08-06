#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
import pathlib
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
DASH = ROOT / 'tak_dashboard.py'
CUSTOM_PATH = 'db450cbe-2fec-47fb-bd2b-ba2db89b035e/Incident Management/water point.png'

with tempfile.TemporaryDirectory(prefix='tak-map-i568-worker-pipeline-') as data_dir:
    os.environ['TAK_DASHBOARD_DATA_DIR'] = data_dir
    spec = importlib.util.spec_from_file_location('tak_dashboard_i568_worker_pipeline_test', DASH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)

    cfg = {
        'api_url': 'https://ots.pipeline.test',
        'base_url': 'https://ots.pipeline.test',
        'marti_url': 'https://ots.pipeline.test:8443',
    }
    sess = {
        'auth_mode': 'ots-user',
        'username': 'pipeline-user',
        'callsign': 'PIPELINE',
        'profile': {'username': 'pipeline-user'},
    }
    calls = []
    cot_xml = (
        '<event version="2.0" uid="CUSTOM-1" type="a-n-G" how="h-e" '
        'time="2026-07-27T12:00:00Z" start="2026-07-27T12:00:00Z" stale="2026-07-27T12:10:00Z">'
        '<point lat="34.1001" lon="-117.2002" hae="0" ce="10" le="10"/>'
        '<detail><contact callsign="WATER"/><usericon iconsetpath="' + CUSTOM_PATH + '"/></detail></event>'
    )

    def fake_request(cfg_arg, sess_arg, url, timeout=10):
        calls.append((url, timeout, time.monotonic()))
        time.sleep(0.06)
        if url.endswith('/api/missions') or url.endswith('/Marti/api/missions'):
            return {'ok': True, 'status': 200, 'body': [{'name': 'PIPELINE-MISSION'}], 'error': ''}
        if url.endswith('/contents'):
            return {
                'ok': True,
                'status': 200,
                'body': [
                    {
                        'uid': 'CUSTOM-1',
                        'details': {
                            'callsign': 'WATER',
                            'type': 'a-n-G',
                            'iconsetPath': CUSTOM_PATH,
                            'location': {'lat': 34.1001, 'lon': -117.2002},
                        },
                    },
                    {'uid': 'SOF-1', 'callsign': 'SOF', 'lat': 34.2, 'lon': -117.3, 'type': 'a-f-F-N-S'},
                ],
                'error': '',
            }
        if url.endswith('/cot'):
            return {'ok': True, 'status': 200, 'body': [cot_xml], 'error': ''}
        return {'ok': True, 'status': 200, 'body': {'name': 'PIPELINE-MISSION'}, 'error': ''}

    mod._i568_request_json_before = fake_request
    mod._i568_set_context('pipeline-token', sess)
    try:
        started = time.monotonic()
        result, acquired = mod._i568_build_snapshot(cfg, sess, 'pipeline-token', 'test')
        elapsed = time.monotonic() - started
    finally:
        mod._i568_clear_context()

    assert elapsed < 0.55, elapsed
    assert acquired['summary']['discovery_ok'] is True
    assert acquired['summary']['mission_count'] == 1
    assert acquired['summary']['mission_endpoint_count'] == 3
    assert len(calls) == 5, calls
    assert all(timeout <= 5 for _url, timeout, _started in calls)

    assert [m.get('name') for m in result.get('missions') or []] == ['PIPELINE-MISSION'], result.get('missions')
    by_uid = {str(row.get('uid') or row.get('event_uid') or ''): row for row in result.get('objects') or []}
    assert 'CUSTOM-1' in by_uid, by_uid.keys()
    assert 'SOF-1' in by_uid, by_uid.keys()
    custom = by_uid['CUSTOM-1']
    assert custom.get('data_sync_current_iconset_path_i567') == CUSTOM_PATH, custom
    assert custom.get('mil2525_file') in (None, ''), custom
    sof = by_uid['SOF-1']
    assert sof.get('mil2525_file') == 'friendly-ground-unit-special-forces.svg', sof
    assert result['data_sync_remote_seed_i568']['per_user_authenticated_source'] is True
    assert result['data_sync_background_worker_i568']['serial_browser_route_acquisition'] is False
    assert result['mission_api_user_scope_i512']['mission_count'] == 1
    assert result['mission_api_user_scope_i512']['effective_missions'] == ['PIPELINE-MISSION']

    scope_key = mod._i539_identity_key(sess, cfg)
    with mod._I539_SCOPE_LOCK:
        scope = dict(mod._I539_SCOPE_CACHE.get(scope_key) or {})
    assert scope.get('ok') is True and scope.get('missions') == ['PIPELINE-MISSION'], scope

    enrich_key = mod._i545_cache_key(cfg, sess)
    with mod._I545_ENRICH_LOCK:
        enrich = dict(mod._I545_ENRICH_CACHE.get(enrich_key) or {})
    assert enrich.get('ok') is True
    assert 'custom-1' in {str(key).casefold() for key in (enrich.get('events') or {})}, enrich

print('i568 bounded worker feeds per-user mission scope, Mission contents, CoT enrichment, custom icons, and reviewed MIL aliases into the final snapshot')
