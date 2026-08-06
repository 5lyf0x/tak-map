#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import json
import os
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
os.environ['TAK_MAP_DATA_DIR'] = tempfile.mkdtemp(prefix='tak-map-i594-discovery-')
os.environ['TAK_MAP_MIL_ROOT'] = str(ROOT / 'assets/mil2525')
os.environ['TAK_MAP_TEST_SKIP_ADSB_WARMUP'] = '1'

spec = importlib.util.spec_from_file_location('tak_dashboard_i594_discovery', ROOT / 'tak_dashboard.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

assert mod.TAK_MAP_ITERATION == 'i594'
assert mod.tak_map_config()['version'] == '1.3.0-i594'

sess = {'auth_mode': 'ots-user', 'username': 'alice', 'callsign': 'ALICE', 'tak_uid': 'alice-uid'}
cfg = {'api_url': 'https://ots', 'base_url': 'https://ots', 'marti_url': 'https://ots:8443'}

secret = {
    'name': 'LOCKED-ALPHA', 'passwordProtected': True,
    'description': 'MUST-NOT-LEAK', 'guid': 'HIDDEN-GUID', 'uid': 'HIDDEN-MISSION-UID',
    'uids': [{'uid': 'HIDDEN-POINT-UID', 'callsign': 'HIDDEN-POINT'}],
    'contents': [{'uid': 'HIDDEN-FILE-UID', 'filename': 'hidden.zip'}],
}
open_row = {
    'name': 'OPEN-BRAVO', 'passwordProtected': False,
    'description': 'Open Mission', 'uid': 'OPEN-MISSION-UID',
    'uids': [{'uid': 'OPEN-POINT-UID', 'callsign': 'OPEN-POINT'}],
    'contents': [],
}

def result(payload):
    return {'ok': True, 'status': 200, 'json': payload, 'body': payload, 'error': ''}

calls = []
def fake_parallel(tasks, cfg0, sess0, token0, deadline, max_workers):
    out, timings = {}, []
    for url, path, label, timeout in tasks:
        calls.append(url)
        payload = {'version': 3, 'type': 'Mission', 'data': [secret, open_row]} if 'passwordProtected=true' in url else {'version': 3, 'type': 'Mission', 'data': [open_row]}
        out[url] = result(payload)
        timings.append({'endpoint': label, 'url_path': path, 'ok': True, 'status': 200, 'duration_seconds': 0.01, 'error': ''})
    return out, timings

remembered = []
mod._i569_run_parallel = fake_parallel
mod._i591_load_index = lambda sess=None: {}
mod._i591_remember_mission = lambda mission, protected=True, sess=None: remembered.append((mission, bool(protected)))
mod._i572_load_password = lambda mission, sess=None: {'ok': False, 'configured': False}
mod._i572_creator_uid = lambda: 'alice-uid'
mod._i591_invalidate_validation = lambda *a, **k: True
mod._I529_REQUEST_CONTEXT.session_token = 'session-token'

acquired = mod._i568_parallel_acquisition(cfg, sess)
assert any('passwordProtected=true' in url for url in calls), calls
assert acquired['summary']['mission_names_visible_before_password'] is True
assert acquired['summary']['locked_contents_exposed'] is False
assert acquired['summary']['locked_protected_mission_count'] == 1
assert set(acquired['mission_names']) == {'LOCKED-ALPHA', 'OPEN-BRAVO'}
locked = next(row for row in acquired['mission_rows'] if row.get('name') == 'LOCKED-ALPHA')
assert locked['metadata_only'] is True and locked['locked'] is True
for forbidden in ('description', 'guid', 'uid', 'uids', 'contents'):
    assert forbidden not in locked, (forbidden, locked)
assert ('LOCKED-ALPHA', True) in remembered
assert mod._I591_CONTEXT.locked_missions == ['LOCKED-ALPHA']

safe_discovery = acquired['responses']['https://ots:8443/Marti/api/missions?passwordProtected=true']['json']
safe_locked = next(row for row in safe_discovery['data'] if row.get('name') == 'LOCKED-ALPHA')
serialized = json.dumps(safe_discovery)
for forbidden_value in ('MUST-NOT-LEAK', 'HIDDEN-GUID', 'HIDDEN-MISSION-UID', 'HIDDEN-POINT', 'hidden.zip'):
    assert forbidden_value not in serialized, forbidden_value
assert safe_locked['metadata_only'] is True

# The security view preserves a sanitized locked Mission row while removing all
# protected objects and content. Unlocked Mission data remains visible.
state = {'snapshot': {}}
mod._i591_locked_rows = lambda state0, sess0=None: [{'mission': 'LOCKED-ALPHA', 'protected': True, 'locked': True, 'unlocked': False}]
mod._i594_access_rows = lambda state0, sess0=None: [
    {'version': 'i594', 'mission': 'LOCKED-ALPHA', 'protected': True, 'password_protected': True, 'locked': True, 'unlocked': False},
    {'version': 'i594', 'mission': 'OPEN-BRAVO', 'protected': False, 'password_protected': False, 'locked': False, 'unlocked': True},
]
mod._i591_mark_locked_state = lambda state0, rows0, sess0=None: (['LOCKED-ALPHA'], {'hidden-point-uid', 'hidden-file-uid'})
payload = {
    'ok': True,
    'missions': [secret, open_row],
    'objects': [
        {'mission_name': 'LOCKED-ALPHA', 'uid': 'HIDDEN-POINT-UID', 'callsign': 'HIDDEN-POINT'},
        {'mission_name': 'OPEN-BRAVO', 'uid': 'OPEN-POINT-UID', 'callsign': 'OPEN-POINT'},
    ],
    'mission_content': [{'mission_name': 'LOCKED-ALPHA', 'uid': 'HIDDEN-FILE-UID', 'filename': 'hidden.zip'}],
    'mission_uids': [{'mission_name': 'LOCKED-ALPHA', 'uid': 'HIDDEN-POINT-UID'}],
    'packages': [{'mission_name': 'LOCKED-ALPHA', 'uid': 'HIDDEN-FILE-UID'}],
}
view, status = mod._i594_filter_security_view(payload, state, sess)
assert status == 200 and view['ok'] is True and view['locked'] is True
assert {row.get('name') for row in view['missions']} == {'LOCKED-ALPHA', 'OPEN-BRAVO'}
locked_view = next(row for row in view['missions'] if row.get('name') == 'LOCKED-ALPHA')
assert locked_view['metadata_only'] is True
assert [row['callsign'] for row in view['objects']] == ['OPEN-POINT']
assert view['mission_content'] == [] and view['mission_uids'] == [] and view['packages'] == []
assert 'HIDDEN' not in json.dumps(view)

# Locked metadata refresh is allowed. The content worker remains responsible for
# setting the PostgreSQL gate after sanitized discovery identifies locked names.
scheduled = []
mod._i591_schedule_before = lambda key, cfg0, sess0, token0, reason0, force=False: (scheduled.append((key, reason0, force)) or (True, 'scheduled'))
mod._i591_locked_rows = lambda state0, sess0=None: [{'mission': 'LOCKED-ALPHA', 'protected': True, 'locked': True, 'unlocked': False}]
mod._i591_mark_locked_state = lambda state0, rows0, sess0=None: (['LOCKED-ALPHA'], set())
assert mod._i568_schedule_refresh('key', cfg, sess, 'token', 'poll', False) == (True, 'scheduled')
assert scheduled == [('key', 'poll', False)]

# After the correct password is stored and accepted, the protected detail and
# CoT endpoints are fetched and the full authorized row may enter the snapshot.
mod._i591_load_index = lambda sess=None: {}
mod._i572_load_password = lambda mission, sess=None: ({'ok': True, 'configured': True, 'password': 'correct'} if mission == 'LOCKED-ALPHA' else {'ok': False})
mod._i572_subscribe_with_password = lambda mission, creator_uid, password, server_host='': {'ok': True, 'status': 200, 'token': 'mission-token'}
mod._i591_mark_validated = lambda *a, **k: True
protected_calls = []
def fake_mission(path, method='GET', body=None, headers=None, token='', public_host='', timeout=25):
    protected_calls.append((path, token))
    if path.endswith('/cot'):
        payload0 = {'version': 3, 'type': 'CoT', 'data': [{'uid': 'AUTHORIZED-COT'}]}
    else:
        payload0 = {'version': 3, 'type': 'Mission', 'data': [secret]}
    return result(payload0)
mod._ots_mission_api_request = fake_mission
calls.clear()
acquired_unlocked = mod._i568_parallel_acquisition(cfg, sess)
unlocked = next(row for row in acquired_unlocked['mission_rows'] if row.get('name') == 'LOCKED-ALPHA')
assert unlocked.get('contents') and unlocked.get('uids')
assert acquired_unlocked['summary']['authorized_protected_mission_count'] == 1
assert acquired_unlocked['summary']['locked_protected_mission_count'] == 0
assert any(path == '/Marti/api/missions/LOCKED-ALPHA' and token == 'mission-token' for path, token in protected_calls)
assert any(path.endswith('/cot') and token == 'mission-token' for path, token in protected_calls)

print(json.dumps({
    'ok': True,
    'version': 'i594',
    'discovered_locked_mission_visible': True,
    'locked_contents_exposed': False,
    'locked_refresh_allowed': True,
    'protected_content_after_password': True,
}, indent=2))
