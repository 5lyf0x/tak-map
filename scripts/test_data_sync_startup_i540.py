#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / 'tak_dashboard.py'
spec = importlib.util.spec_from_file_location('tak_dashboard_i540_test', DASH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def point(uid: str, name: str, mission_id=None):
    row = {
        'uid': uid,
        'callsign': name,
        'name': name,
        'lat': 35.0,
        'lon': -117.0,
        'kind': 'datasync',
        'geometry': 'point',
        'source': 'OpenTAKServer Data Sync mission_uids',
    }
    if mission_id is not None:
        row['mission_id'] = mission_id
    return row

base = {
    'ok': True,
    'missions': [
        {'id': 7, 'name': 'TAKMAP-DATASYNC-TEST'},
        {'id': 8, 'name': 'GROUP-MISSION'},
        {'id': 9, 'name': 'OTHER-MISSION'},
    ],
    'mission_uids': [
        dict(point('UID-ACTIVE', 'Active', 7), mission_id=7),
        point('UID-DELETED', 'Deleted'),
        dict(point('UID-GROUP', 'Group', 8), mission_id=8),
        dict(point('UID-OTHER', 'Other', 9), mission_id=9),
    ],
    'mission_content': [],
    'mission_logs': [],
    'mission_roles': [
        {'mission_id': 7, 'username': 'darktek', 'client_uid': 'TAKMAP-USER-TEST', 'role': 'SUBSCRIBER'},
        {'mission_id': 9, 'username': 'someone-else', 'client_uid': 'OTHER-UID', 'role': 'SUBSCRIBER'},
    ],
    'mission_content_mission': [],
    'packages': [],
    'objects': [
        point('UID-ACTIVE', 'Active'),
        point('UID-DELETED', 'Deleted'),
        point('UID-GROUP', 'Group'),
        point('UID-OTHER', 'Other'),
    ],
}

sess = {
    'auth_mode': 'ots-user',
    'username': 'darktek',
    'tak_uid': 'TAKMAP-USER-TEST',
    'profile': {'username': 'darktek', 'tak_uid': 'TAKMAP-USER-TEST'},
}
cfg = {'marti_url': 'https://ots.example:8089'}

# The remote mission API is deliberately slow and empty. The Data Sync endpoint
# must return immediately and preserve the direct mission role.
mod._I539_SCOPE_CACHE.clear()
mod._I540_SCOPE_INFLIGHT.clear()
api_calls = {'count': 0}

def slow_empty_scope(*args, **kwargs):
    api_calls['count'] += 1
    time.sleep(0.35)
    return {
        'ok': True,
        'status': 200,
        'json': {'data': []},
        'identity_mode': 'per-user-enrolled-marti-certificate',
        'certificate_cn': 'darktek',
        'client_uid': 'TAKMAP-USER-TEST',
    }

mod._ots_mission_api_request = slow_empty_scope
start = time.perf_counter()
out = mod._i512_augment_data_sync(base, cfg, sess)
elapsed = time.perf_counter() - start
assert elapsed < 0.10, elapsed
assert [row['name'] for row in out['missions']] == ['TAKMAP-DATASYNC-TEST'], out['missions']
assert [row['uid'] for row in out['objects']] == ['UID-ACTIVE'], out['objects']
assert out['mission_api_user_scope_i512']['probe_duration_ms'] == 0
assert out['mission_api_user_scope_i512']['probe_blocked_request'] is False
assert out['mission_api_user_scope_i512']['background_refresh_scheduled'] is True
assert out['mission_api_user_scope_i512']['direct_role_missions'] == ['TAKMAP-DATASYNC-TEST']

# Wait for the background probe; its successful empty response still must not
# erase the role-backed mission on the next request.
deadline = time.time() + 2.0
while time.time() < deadline and (api_calls['count'] < 1 or mod._I540_SCOPE_INFLIGHT):
    time.sleep(0.02)
assert api_calls['count'] == 1, api_calls
out_after_empty = mod._i512_augment_data_sync(base, cfg, sess)
assert [row['name'] for row in out_after_empty['missions']] == ['TAKMAP-DATASYNC-TEST']
assert [row['uid'] for row in out_after_empty['objects']] == ['UID-ACTIVE']
assert out_after_empty['mission_api_user_scope_i512']['empty_api_preserves_direct_roles'] is True

# A cached group-visible mission is unioned with direct MissionRole scope.
key = mod._i539_identity_key(sess, cfg)
mod._I539_SCOPE_CACHE[key] = {
    'ok': True,
    'missions': ['GROUP-MISSION'],
    'time': time.time(),
    'status': 200,
    'identity_mode': 'per-user-enrolled-marti-certificate',
}
unioned = mod._i512_augment_data_sync(base, cfg, sess)
assert [row['name'] for row in unioned['missions']] == ['TAKMAP-DATASYNC-TEST', 'GROUP-MISSION']
assert [row['uid'] for row in unioned['objects']] == ['UID-ACTIVE', 'UID-GROUP']
assert unioned['mission_api_user_scope_i512']['effective_missions'] == ['TAKMAP-DATASYNC-TEST', 'GROUP-MISSION']

# Browser startup is non-blocking, single-flight, and uses one startup refresh
# plus the retained five-minute polling interval.
html = mod.TAK_MAP_HTML
assert "if(dataSyncRequestPromise)return dataSyncRequestPromise" in html
assert "setInterval(refreshDataSyncInterval,300000)" in html
assert "refreshDataSync(false,'startup')" in html
assert html.count("refreshDataSync(false,'startup')") == 1
assert "await forceDataSyncSync('initial-load')" not in html
assert "page-load-force" not in html
assert "auto-load-" not in html
assert "followup-1" not in html and "followup-2" not in html and "followup-3" not in html
assert "dataSyncEventTimer=setTimeout(()=>refreshDataSync(false,reason),500)" in html
assert html.index("textContent='Ready'") < html.index("refreshDataSync(false,'startup')")
assert mod.TAK_MAP_ITERATION == 'i540'
control = mod.tak_map_config()['data_sync_control']
assert control['startup_blocks_main_interface'] is False
assert control['automatic_poll_seconds'] == 300
assert control['mission_scope_request_background'] is True
print(f'i540 non-blocking startup and role-backed Data Sync tests passed in {elapsed:.4f}s')
