#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / 'tak_dashboard.py'
spec = importlib.util.spec_from_file_location('tak_dashboard_i542_test', DASH)
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
        dict(point('ATAK-UID-ACTIVE', 'Active', 7), mission_id=7),
        point('ATAK-UID-DELETED', 'Deleted'),
        dict(point('UID-GROUP', 'Group', 8), mission_id=8),
        dict(point('UID-OTHER', 'Other', 9), mission_id=9),
    ],
    'mission_content': [],
    'mission_logs': [],
    # This is the live failure shape: the mission role belongs to ATAK's EUD UID,
    # not TAK Map's own persistent browser EUD UID, and username is blank.
    'mission_roles': [
        {'mission_id': 7, 'mission_name': 'TAKMAP-DATASYNC-TEST', 'username': '', 'clientUid': 'ATAK-DEVICE-UID', 'role_type': 'MISSION_SUBSCRIBER'},
        {'mission_id': 9, 'mission_name': 'OTHER-MISSION', 'username': 'someone-else', 'clientUid': 'OTHER-UID', 'role_type': 'MISSION_SUBSCRIBER'},
    ],
    'mission_content_mission': [],
    'packages': [],
    'objects': [
        point('ATAK-UID-ACTIVE', 'Active'),
        point('ATAK-UID-DELETED', 'Deleted'),
        point('UID-GROUP', 'Group'),
        point('UID-OTHER', 'Other'),
    ],
}

sess = {
    'auth_mode': 'ots-user',
    'username': 'darktek',
    'tak_uid': 'TAKMAP-USER-BROWSER-UID',
    'profile': {'username': 'darktek', 'tak_uid': 'TAKMAP-USER-BROWSER-UID'},
}
cfg = {'marti_url': 'https://ots.example:8089'}

# Simulate current OTS tables. The account owns ATAK-DEVICE-UID through the EUD
# user relationship. The remote Marti mission list is empty and must not erase it.
queries = []
mod._candidate_ots_pg_uris = lambda: (['postgresql://test'], [])

def fake_rows(_uri, sql):
    queries.append(sql)
    if 'from public.euds e' in sql:
        return ([{'uid': 'ATAK-DEVICE-UID'}], '')
    if 'from public.certificates c' in sql:
        return ([], '')
    if 'from public.mission_roles mr' in sql:
        assert 'lower(coalesce(mr."clientUid"' in sql
        assert 'atak-device-uid' in sql.lower()
        return ([{'mission_name': 'TAKMAP-DATASYNC-TEST'}], '')
    if 'from public.groups_missions gm' in sql:
        return ([], '')
    if 'from public.missions m' in sql:
        return ([], '')
    raise AssertionError(sql)

mod._pg_rows_json = fake_rows
mod._I542_DB_SCOPE_CACHE.clear()
scope = mod._i542_database_mission_scope(cfg, sess)
assert scope['ok'] is True, scope
assert scope['direct'] == ['TAKMAP-DATASYNC-TEST'], scope
assert 'atak-device-uid' in scope['owned_eud_uids'], scope
assert len(queries) == 5, len(queries)

# Empty successful API cache must be additive only and cannot erase database scope.
key = mod._i539_identity_key(sess, cfg)
mod._I539_SCOPE_CACHE.clear()
mod._I539_SCOPE_CACHE[key] = {
    'ok': True,
    'missions': [],
    'time': time.time(),
    'status': 200,
    'identity_mode': 'per-user-enrolled-marti-certificate',
}
mod._i540_schedule_scope_refresh = lambda *_: {'scheduled': False, 'reason': 'fresh-cache'}
out = mod._i512_augment_data_sync(base, cfg, sess)
assert [row['name'] for row in out['missions']] == ['TAKMAP-DATASYNC-TEST'], out['missions']
assert [row['uid'] for row in out['objects']] == ['ATAK-UID-ACTIVE'], out['objects']
diag = out['mission_api_user_scope_i512']
assert diag['version'] == 'i542'
assert diag['database_direct_role_missions'] == ['TAKMAP-DATASYNC-TEST']
assert diag['effective_missions'] == ['TAKMAP-DATASYNC-TEST']
assert diag['empty_api_preserves_database_scope'] is True

# A failure in optional group/certificate relationships cannot erase a proven
# direct MissionRole relationship.
mod._I542_DB_SCOPE_CACHE.clear()
def partial_rows(_uri, sql):
    if 'from public.euds e' in sql:
        return ([{'uid': 'ATAK-DEVICE-UID'}], '')
    if 'from public.certificates c' in sql:
        return ([], 'missing optional table')
    if 'from public.mission_roles mr' in sql:
        return ([{'mission_name': 'TAKMAP-DATASYNC-TEST'}], '')
    if 'from public.groups_missions gm' in sql:
        return ([], 'group relation unavailable')
    if 'from public.missions m' in sql:
        return ([], '')
    return ([], 'unexpected')
mod._pg_rows_json = partial_rows
partial = mod._i542_database_mission_scope(cfg, sess)
assert partial['ok'] is True, partial
assert partial['partial'] is True
assert partial['direct'] == ['TAKMAP-DATASYNC-TEST']

# Static startup contracts: one dedicated post-shell owner, no duplicate deferred
# controller, immediate control installation, five-minute polling, and render proof.
startup = (ROOT / 'assets/tak-map-startup-i542.js').read_text()
core = (ROOT / 'assets/tak-map-core-i542.js').read_text()
control = (ROOT / 'assets/tak-map-data-sync-i542.js').read_text()
import json
manifest = json.loads((ROOT / 'assets/tak-map-deferred-i542.json').read_text())
ids = [row.get('id') for row in manifest.get('scripts', [])]
assert 'takMapDataSyncLoaderV476' not in ids
assert startup.count("__takMapStartDataSyncI542()") == 1
assert "tak-map-data-sync-i542.js" in startup
assert "__takMapDataSyncControlReadyI542" in startup
assert "refreshDataSync(false,'startup')" in core
assert core.count("refreshDataSync(false,'startup')") == 1
assert "setInterval(refreshDataSyncInterval,300000)" in core
assert "dataSyncRendered={missions,objects" in core
assert "boot();" in control and "setTimeout(boot,10)" not in control
assert mod.TAK_MAP_ITERATION == 'i542'
print('i542 account-aware Data Sync and single startup owner tests passed')
