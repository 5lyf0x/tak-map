#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import json
import os
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
os.environ['TAK_MAP_DATA_DIR'] = tempfile.mkdtemp(prefix='tak-map-i595-authorized-merge-')
os.environ['TAK_MAP_MIL_ROOT'] = str(ROOT / 'assets/mil2525')
os.environ['TAK_MAP_TEST_SKIP_ADSB_WARMUP'] = '1'

spec = importlib.util.spec_from_file_location('tak_dashboard_i595_authorized_merge', ROOT / 'tak_dashboard.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader
spec.loader.exec_module(mod)

assert mod.TAK_MAP_ITERATION == 'i598'
assert mod.tak_map_config()['version'] == '1.3.0-i598'

sess = {'auth_mode': 'ots-user', 'username': 'alice', 'callsign': 'ALICE', 'tak_uid': 'alice-uid'}
cfg = {'api_url': 'https://ots', 'base_url': 'https://ots', 'marti_url': 'https://ots:8443'}
mission = 'LOCKED-ALPHA'
point_uid = 'AUTHORIZED-POINT-1'
file_uid = 'AUTHORIZED-FILE-1'

# The include-protected discovery row is complete and authoritative for Mission
# membership/content. The authorized single-Mission detail response intentionally
# omits both arrays, matching the installed OTS behavior that exposed the i594 bug.
discovery_row = {
    'name': mission,
    'passwordProtected': True,
    'description': 'Discovery description',
    'uids': [{
        'data': point_uid,
        'details': {
            'callsign': 'AUTHORIZED POINT',
            'type': 'a-f-G-U-C',
            'location': {'lat': 34.1234, 'lon': -117.4321},
        },
    }],
    'contents': [{'uid': file_uid, 'filename': 'authorized-package.zip', 'keywords': [mission]}],
}
detail_row = {
    'name': mission,
    'passwordProtected': True,
    'description': 'Authorized detail description',
    'tool': 'OpenTAKServer',
}
open_payload = {'version': 3, 'type': 'Mission', 'data': []}
protected_payload = {'version': 3, 'type': 'Mission', 'data': [discovery_row]}

def result(payload, status=200, ok=True):
    return {'ok': ok, 'status': status, 'json': payload, 'body': payload, 'error': ''}

def fake_parallel(tasks, cfg0, sess0, token0, deadline, max_workers):
    responses, timings = {}, []
    for url, path, label, timeout in tasks:
        payload = protected_payload if 'passwordProtected=true' in url else open_payload
        responses[url] = result(payload)
        timings.append({'endpoint': label, 'url_path': path, 'ok': True, 'status': 200, 'duration_seconds': 0.01, 'error': ''})
    return responses, timings

mission_calls = []
def fake_mission(path, method='GET', body=None, headers=None, token='', public_host='', timeout=25):
    mission_calls.append((path, token))
    if path.endswith('/cot'):
        cot = (f'<event version="2.0" uid="{point_uid}" type="a-f-G-U-C" how="h-e" '
               'time="2026-07-30T12:00:00Z" start="2026-07-30T12:00:00Z" stale="2026-07-30T12:10:00Z">'
               '<point lat="34.1234" lon="-117.4321" hae="0" ce="10" le="10"/>'
               '<detail><contact callsign="AUTHORIZED POINT"/></detail></event>')
        return {'ok': True, 'status': 200, 'json': {}, 'body': '<events>' + cot + '</events>', 'error': ''}
    return result({'version': 3, 'type': 'Mission', 'data': [detail_row]})

mod._i569_run_parallel = fake_parallel
mod._ots_mission_api_request = fake_mission
mod._i591_load_index = lambda sess=None: {}
mod._i591_remember_mission = lambda *a, **k: True
mod._i572_load_password = lambda name, sess=None: {'ok': True, 'configured': True, 'password': 'correct'}
mod._i572_creator_uid = lambda: 'alice-uid'
mod._i572_subscribe_with_password = lambda *a, **k: {'ok': True, 'status': 200, 'token': 'mission-token'}
mod._i591_mark_validated = lambda *a, **k: True
mod._candidate_ots_pg_uris = lambda: ([], [])
mod._I529_REQUEST_CONTEXT.session_token = 'session-token'

acquired = mod._i568_parallel_acquisition(cfg, sess)
assert acquired['summary']['authorized_protected_mission_count'] == 1, acquired['summary']
assert acquired['summary']['locked_protected_mission_count'] == 0, acquired['summary']
row = next(r for r in acquired['mission_rows'] if r.get('name') == mission)
assert row['description'] == 'Authorized detail description', row
assert row['tool'] == 'OpenTAKServer', row
assert row.get('authorized_discovery_merge_i595') is True, row
assert row.get('uids') == discovery_row['uids'], row
assert row.get('contents') == discovery_row['contents'], row

qbase = 'https://ots:8443/Marti/api/missions/LOCKED-ALPHA'
detail_payload = acquired['responses'][qbase]['json']
contents_payload = acquired['responses'][qbase + '/contents']['json']
assert detail_payload['data'][0]['uids'] == discovery_row['uids'], detail_payload
assert detail_payload['data'][0]['contents'] == discovery_row['contents'], detail_payload
assert contents_payload['data'] == discovery_row['contents'], contents_payload
assert any(path.endswith('/cot') and token == 'mission-token' for path, token in mission_calls), mission_calls

# Prove the merged discovery membership reaches the normal snapshot parser and
# creates the Mission object even though the detail endpoint omitted `uids`.
mod._I591_CONTEXT.locked_missions = []
snapshot = mod._i570_build_from_acquired(cfg, sess, acquired, previous=None, phase='i595-regression')
objects = list(snapshot.get('objects') or [])
assert any(str(obj.get('uid') or obj.get('event_uid') or obj.get('data')) == point_uid for obj in objects), objects
assert any(str(item.get('uid') or item.get('id') or '') == file_uid or item.get('filename') == 'authorized-package.zip'
           for item in list(snapshot.get('mission_content') or []) + list(snapshot.get('packages') or [])), snapshot

print(json.dumps({
    'ok': True,
    'version': 'i595',
    'detail_omitted_uids': True,
    'detail_omitted_contents': True,
    'discovery_uids_preserved_after_unlock': True,
    'discovery_contents_preserved_after_unlock': True,
    'objects_released_after_password_validation': True,
}, indent=2))
