#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tak_dashboard_i546_test', ROOT / 'tak_dashboard.py')
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

mod._I543_TOMBSTONES.clear()
mod._I512_REQUEST_CONTEXT.identity = {'username': 'darktek'}
mod._I537_REQUEST_CONTEXT.identity_key = 'darktek'


def point(uid: str, name: str, mission_id=None, updated='2026-07-25T04:00:00Z'):
    row = {
        'uid': uid,
        'callsign': name,
        'name': name,
        'lat': 35.0,
        'lon': -117.0,
        'kind': 'datasync',
        'geometry': 'point',
        'source': 'OpenTAKServer Data Sync mission_uids',
        'updated': updated,
    }
    if mission_id is not None:
        row['mission_id'] = mission_id
    return row

base = {
    'ok': True,
    'missions': [{'id': 7, 'name': 'TEST'}],
    'mission_uids': [
        dict(point('UID-ACTIVE', 'Active', 7), mission_id=7),
        point('UID-DELETED', 'Deleted'),
    ],
    'mission_content': [], 'mission_logs': [], 'mission_roles': [],
    'mission_content_mission': [], 'packages': [],
    'objects': [point('UID-ACTIVE', 'Active'), point('UID-DELETED', 'Deleted')],
}
filtered = mod._i539_filter_deleted_orphans(base)
assert [r['uid'] for r in filtered['objects']] == ['UID-ACTIVE'], filtered['objects']
tomb = filtered['data_sync_deleted_uid_tombstones_i543']
assert tomb['count'] == 1, tomb
assert tomb['uids'] == ['uid-deleted'], tomb
assert tomb['survives_browser_reload'] is True

# The retained live copy from the same/older event is removed immediately.
live = {'ok': True, 'markers': [{'uid': 'UID-DELETED', 'updated': '2026-07-25T04:00:00Z'}, {'uid': 'OTHER', 'updated': '2026-07-25T04:00:00Z'}]}
live_filtered = mod._i543_filter_live_payload(live, 'markers')
assert [r['uid'] for r in live_filtered['markers']] == ['OTHER'], live_filtered
assert live_filtered['data_sync_deleted_uid_live_filter_i543']['removed_uids'] == ['uid-deleted']

# A genuinely newer CoT event releases the tombstone and is allowed through.
newer = {'ok': True, 'markers': [{'uid': 'UID-DELETED', 'updated': '2026-07-25T04:00:05Z'}]}
newer_filtered = mod._i543_filter_live_payload(newer, 'markers')
assert [r['uid'] for r in newer_filtered['markers']] == ['UID-DELETED'], newer_filtered
assert newer_filtered['data_sync_deleted_uid_live_filter_i543']['released_uids'] == ['uid-deleted']
assert not mod._i543_tombstones('darktek')

# Recreate tombstone, then re-associate the same UID with the mission; ownership
# must clear the tombstone rather than hiding the newly active mission object.
mod._i539_filter_deleted_orphans(base)
reassociated = dict(base)
reassociated['mission_uids'] = [dict(point('UID-ACTIVE', 'Active', 7), mission_id=7), dict(point('UID-DELETED', 'Deleted', 7, '2026-07-25T04:01:00Z'), mission_id=7)]
reassociated['objects'] = [point('UID-ACTIVE', 'Active'), point('UID-DELETED', 'Deleted', 7, '2026-07-25T04:01:00Z')]
again = mod._i539_filter_deleted_orphans(reassociated)
assert {r['uid'] for r in again['objects']} == {'UID-ACTIVE', 'UID-DELETED'}
assert again['data_sync_deleted_uid_tombstones_i543']['count'] == 0

core = (ROOT / 'assets/tak-map-core-i546.js').read_text()
control = (ROOT / 'assets/tak-map-data-sync-i546.js').read_text()
startup = (ROOT / 'assets/tak-map-startup-i546.js').read_text()
assert 'setInterval(refreshDataSyncInterval,10000)' in core
assert 'setInterval(refreshDataSyncInterval,300000)' not in core
assert core.count("refreshDataSync(false,'startup')") == 1
assert 'minIntervalMs:10000' in control
assert 'automaticPollMs:10000' in control
assert 'tak-map-data-sync-i546.js' in startup
assert mod.TAK_MAP_ITERATION == 'i546'
cfg = mod.tak_map_config()
assert cfg['data_sync_control']['automatic_poll_seconds'] == 10
assert cfg['data_sync_control']['deleted_uid_tombstones'] is True
print('i546 10-second Data Sync polling and exact-UID deletion tombstone tests passed')
