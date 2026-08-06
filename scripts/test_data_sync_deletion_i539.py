#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / 'tak_dashboard.py'
spec = importlib.util.spec_from_file_location('tak_dashboard_i539_test', DASH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def point(uid: str, name: str, mission_id=None, mission_name=''):
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
    if mission_name:
        row['mission_name'] = mission_name
    return row

base = {
    'ok': True,
    'missions': [
        {'id': 7, 'name': 'TAKMAP-DATASYNC-TEST'},
        {'id': 8, 'name': 'OTHER-MISSION'},
    ],
    'mission_uids': [
        dict(point('UID-ACTIVE', 'Active', 7), mission_id=7),
        # OTS historical row retained after ATAK removes the mission association.
        point('UID-DELETED', 'Deleted'),
        dict(point('UID-OTHER', 'Other', 8), mission_id=8),
    ],
    'mission_content': [],
    'mission_logs': [],
    'mission_roles': [],
    'mission_content_mission': [],
    'packages': [],
    'objects': [
        point('UID-ACTIVE', 'Active'),
        point('UID-DELETED', 'Deleted'),
        point('UID-OTHER', 'Other'),
    ],
}

filtered = mod._i539_filter_deleted_orphans(base)
assert [row['uid'] for row in filtered['objects']] == ['UID-ACTIVE', 'UID-OTHER'], filtered['objects']
assert filtered['data_sync_deleted_orphan_filter_i539']['removed_count'] == 1
assert filtered['data_sync_deleted_orphan_filter_i539']['removed_sample'][0]['uid'] == 'uid-deleted'
assert filtered['objects'][0]['delete_supported'] is True
assert filtered['objects'][0]['mission_name'] == 'TAKMAP-DATASYNC-TEST'
assert all(row.get('uid') != 'UID-DELETED' for row in filtered['objects'])

# A successful per-user Marti mission list scopes the database view and is cached.
mod._I539_SCOPE_CACHE.clear()
api_calls = {'count': 0}

def ok_scope(*args, **kwargs):
    api_calls['count'] += 1
    return {
        'ok': True,
        'status': 200,
        'json': {'data': [{'name': 'TAKMAP-DATASYNC-TEST'}]},
        'identity_mode': 'per-user-enrolled-marti-certificate',
        'certificate_cn': 'darktek',
        'client_uid': 'TAKMAP-USER-TEST',
    }

mod._ots_mission_api_request = ok_scope
# The i539 path must not call the old shared-credential probes.
mod._i512_request_json = lambda *a, **k: (_ for _ in ()).throw(AssertionError('legacy shared-credential mission probe executed'))
sess = {'auth_mode': 'ots-user', 'username': 'darktek', 'profile': {'username': 'darktek'}}
cfg = {'marti_url': 'https://ots.example:8089'}
scoped = mod._i512_augment_data_sync(base, cfg, sess)
assert api_calls['count'] == 1
assert [row['name'] for row in scoped['missions']] == ['TAKMAP-DATASYNC-TEST']
assert [row['uid'] for row in scoped['objects']] == ['UID-ACTIVE']
assert scoped['mission_api_user_scope_i512']['state'] == 'ok'
assert scoped['mission_api_user_scope_i512']['invalid_contents_get_removed'] is True
assert scoped['mission_api_user_scope_i512']['shared_service_probe_removed'] is True
scoped_again = mod._i512_augment_data_sync(base, cfg, sess)
assert api_calls['count'] == 1, api_calls
assert scoped_again['mission_api_user_scope_i512']['cached'] is True

# Failed scope discovery is cooled down instead of blocking every refresh; DB
# fallback remains available and the deleted orphan is still suppressed.
mod._I539_SCOPE_CACHE.clear()
fail_calls = {'count': 0}

def fail_scope(*args, **kwargs):
    fail_calls['count'] += 1
    return {
        'ok': False,
        'status': 401,
        'error': 'The per-user OpenTAKServer Mission API request failed.',
        'attempts': [{'status': 401}],
    }

mod._ots_mission_api_request = fail_scope
fallback = mod._i512_augment_data_sync(base, cfg, sess)
fallback_again = mod._i512_augment_data_sync(base, cfg, sess)
assert fail_calls['count'] == 1, fail_calls
assert fallback['mission_api_user_scope_i512']['state'] == 'unavailable'
assert fallback_again['mission_api_user_scope_i512']['cached'] is True
assert [row['uid'] for row in fallback['objects']] == ['UID-ACTIVE', 'UID-OTHER']
assert all(row.get('uid') != 'UID-DELETED' for row in fallback['objects'])

assert mod.TAK_MAP_ITERATION == 'i539'
assert mod.tak_map_config()['data_sync_control']['deleted_uid_association_removal'] is True
print('i539 Data Sync deletion reconciliation, per-user scope, and probe cooldown tests passed')
