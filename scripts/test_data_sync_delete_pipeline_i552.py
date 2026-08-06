#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tak_dashboard_i552_delete_pipeline_test', ROOT / 'tak_dashboard.py')
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

content_uid = 'c2b7d3b6-d884-4d05-ac54-afb565be257'
event_uid = 'ATAK-DS-P12-EVENT-UID'
mission = 'TAKMAP-DATASYNC-TEST'
xml = f'''<event version="2.0" uid="{event_uid}" type="a-f-G-U-C-I" time="2026-07-25T22:05:00Z" start="2026-07-25T22:05:00Z" stale="2026-07-25T22:15:00Z">
  <point lat="34.5901786" lon="-117.014907" hae="0" ce="10" le="10"/>
  <detail><contact callsign="DS-P12 RENAMED"/></detail>
</event>'''
event = mod._i545_extract_events({}, xml)[event_uid.casefold()]
content_row = {
    'uid': content_uid,
    'id': content_uid,
    'name': content_uid,
    'callsign': content_uid,
    'lat': 34.5901786,
    'lon': -117.014907,
    'xml': xml,
    'updated': '2026-07-25T23:00:00Z',
    'source': 'OpenTAKServer Data Sync mission_uids',
    'mission_id': 7,
}
payload = {
    'ok': True,
    'missions': [{'id': 7, 'name': mission}],
    'mission_uids': [{'mission_id': 7, 'uid': event_uid}],
    'mission_content': [],
    'mission_logs': [],
    'mission_roles': [],
    'mission_content_mission': [],
    'packages': [],
    'objects': [content_row],
    'data_sync_deleted_uid_tombstones_i546': {'version': 'i546', 'count': 0, 'tombstones': []},
}
cfg = {'marti_url': 'https://ots.example:8089'}
sess = {'username': 'operator', 'auth_mode': 'ots-user', 'profile': {'username': 'operator'}}
mod._I512_REQUEST_CONTEXT.identity = {'username': 'operator'}
mod._I537_REQUEST_CONTEXT.identity_key = 'operator'
key = mod._i545_cache_key(cfg, sess)
mod._I545_ENRICH_CACHE.clear()
mod._I545_ENRICH_CACHE[key] = {
    'ok': True,
    'time': time.time(),
    'requested': (mission.casefold(),),
    'events': {event_uid.casefold(): dict(event, mission_name=mission)},
    'missions': [{'mission': mission, 'ok': True, 'status': 200, 'event_count': 1}],
    'event_count': 1,
    'error': '',
}

# Replace the earlier wrapper only inside this test so the final i552 function
# receives a deterministic, already user-scoped base payload.
original_before = mod._i552_augment_before
def visible_pipeline(base, _cfg, _sess):
    out = mod._i545_apply_cached_enrichment(dict(base), cfg, sess, [mission])
    rows = [mod._i546_normalize_row_identity(row) for row in out.get('objects') or []]
    rows, _ = mod._i546_dedupe_rows(rows)
    out['objects'] = rows
    return mod._tak_enrich_data_sync_result(out)
mod._i552_augment_before = visible_pipeline

original_data_sync = mod.tak_map_data_sync
original_session = mod._i529_current_session
original_config = mod._i509_load_ots_config
mod.tak_map_data_sync = lambda: dict(payload)
mod._i529_current_session = lambda: dict(sess)
mod._i509_load_ots_config = lambda: dict(cfg)
try:
    snapshot = mod._tak_fresh_data_sync_result()
finally:
    mod._i552_augment_before = original_before

assert snapshot['data_sync_delete_snapshot_i552']['same_as_visible_data_sync_pipeline'] is True
assert len(snapshot['objects']) == 1
point = snapshot['objects'][0]
expected_object_id = 'datasync-' + hashlib.sha256(('uid:' + event_uid).encode()).hexdigest()[:24]
expected_canonical = 'datasync:' + expected_object_id
assert point['uid'] == event_uid
assert point['mission_content_uid'] == content_uid
assert point['object_id'] == expected_object_id
assert point['canonical_id'] == expected_canonical
assert point['mission_delete_target'] == 'uid'
assert point['mission_delete_value'] == event_uid

captured = {}
original_delete_record = mod._tak_data_sync_delete_record
def fake_delete_record(obj, server_host=''):
    captured.update(obj)
    return {
        'object_id': obj['canonical_id'],
        'status': 'deleted',
        'mission': obj['mission_name'],
        'target': obj['mission_delete_target'],
        'value': obj['mission_delete_value'],
        'http_status': 200,
    }
mod._tak_data_sync_delete_record = fake_delete_record
mod._i552_augment_before = visible_pipeline
try:
    result = mod.tak_map_object_delete([expected_canonical])
finally:
    mod._tak_data_sync_delete_record = original_delete_record
    mod._i552_augment_before = original_before
    mod.tak_map_data_sync = original_data_sync
    mod._i529_current_session = original_session
    mod._i509_load_ots_config = original_config

assert result['ok'] is True, result
assert result['deleted_ids'] == [expected_canonical], result
assert not result['not_found_ids'], result
assert captured['uid'] == event_uid
assert captured['mission_content_uid'] == content_uid
assert captured['mission_delete_value'] == event_uid
print('i552 Data Sync deletion lookup uses the visible canonical Mission-CoT pipeline')
