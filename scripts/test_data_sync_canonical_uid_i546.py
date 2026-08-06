#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tak_dashboard_i546_test', ROOT / 'tak_dashboard.py')
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

content_uid = 'c2b7d3b6-d884-4d05-ac54-afb565be257'
event_uid = 'ATAK-DS-P07-EVENT-UID'
mission = 'TAKMAP-DATASYNC-TEST'
xml = f'''<event version="2.0" uid="{event_uid}" type="a-f-G-E-V-A" time="2026-07-25T22:00:00Z" start="2026-07-25T22:00:00Z" stale="2026-07-25T22:10:00Z">
  <point lat="34.5901786" lon="-117.014907" hae="0" ce="10" le="10"/>
  <detail><contact callsign="DS-P07"/><usericon iconsetpath="COT_MAPPING_2525C/a-f-G-E-V-A"/></detail>
</event>'''

content_row = {
    'uid': content_uid,
    'id': content_uid,
    'name': content_uid,
    'callsign': content_uid,
    'lat': 34.5901786,
    'lon': -117.014907,
    'xml': xml,
    'updated': '2026-07-25T21:59:00Z',
    'source': 'OpenTAKServer Data Sync mission_uids',
    'mission_id': 7,
}

# Canonical CoT/event identity outranks the generic Mission content UUID.
assert mod._i537_object_uid(content_row) == event_uid.casefold()
normalized = mod._i546_normalize_row_identity(content_row)
assert normalized['uid'] == event_uid
assert normalized['cot_uid'] == event_uid
assert normalized['event_uid'] == event_uid
assert normalized['mission_content_uid'] == content_uid
assert normalized['content_uid'] == content_uid
assert normalized['mission_content_id'] == content_uid
assert normalized['data_sync_uid_aliases_i546'] == [event_uid, content_uid]
assert mod._i537_object_uid({'uid': content_uid, 'event_uid': event_uid}) == event_uid.casefold()

# The Mission /cot event supplies the authoritative callsign and armored vehicle symbol.
events = mod._i545_extract_events({}, xml)
assert list(events) == [event_uid.casefold()], events
event = events[event_uid.casefold()]
merged, applied, reason = mod._i545_merge_event(content_row, event)
assert applied and reason == 'merged', (applied, reason, merged)
assert merged['uid'] == event_uid
assert merged['mission_content_uid'] == content_uid
assert merged['callsign'] == 'DS-P07'
assert merged['name'] == 'DS-P07'
assert merged['display_name'] == 'DS-P07'
assert merged['label'] == 'DS-P07'
assert merged['type'] == 'a-f-G-E-V-A'
assert merged['sidc'] == 'SFGPEVA--------'
assert merged['mil2525_file'] == 'friendly-ground-equipment-armored-vehicle.svg'
assert merged['data_sync_display_name_source_i546'] == 'mission-cot-contact-callsign'

# Exact cached enrichment works when the database row and event use different IDs.
mod._I545_ENRICH_CACHE.clear()
mod._I545_ENRICH_INFLIGHT.clear()
mod._I512_REQUEST_CONTEXT.identity = {'username': 'darktek'}
mod._I537_REQUEST_CONTEXT.identity_key = 'darktek'
cfg = {'marti_url': 'https://ots.example:8089'}
sess = {'username': 'darktek', 'auth_mode': 'ots-user', 'profile': {'username': 'darktek'}}
key = mod._i545_cache_key(cfg, sess)
mod._I545_ENRICH_CACHE[key] = {
    'ok': True,
    'time': time.time(),
    'requested': (mission.casefold(),),
    'events': {event_uid.casefold(): dict(event, mission_name=mission)},
    'missions': [{'mission': mission, 'ok': True, 'status': 200, 'event_count': 1}],
    'event_count': 1,
    'error': '',
}

# Include duplicate content-row and event-row representations. i546 must emit one point.
event_row = {
    'uid': event_uid,
    'name': event_uid,
    'callsign': event_uid,
    'lat': 34.5901786,
    'lon': -117.014907,
    'updated': '2026-07-25T21:59:00Z',
    'source': 'OpenTAKServer Data Sync mission_uids',
    'mission_id': 7,
}
payload = {
    'ok': True,
    'missions': [{'id': 7, 'name': mission}],
    'mission_uids': [{'mission_id': 7, 'uid': event_uid}],
    'mission_content': [], 'mission_logs': [], 'mission_roles': [],
    'mission_content_mission': [], 'packages': [],
    'objects': [content_row, event_row],
    'data_sync_deleted_uid_tombstones_i543': {'version': 'i543', 'count': 0, 'tombstones': []},
}

enriched = mod._i545_apply_cached_enrichment(payload, cfg, sess, [mission])
assert enriched['mission_cot_symbol_enrichment_i546']['objects_matched'] == 2, enriched

# Exercise the final i546 augmentation/recanonicalization without remote scope probes.
original_before = mod._i546_augment_before
mod._i546_augment_before = lambda base, _cfg, _sess: mod._i545_apply_cached_enrichment(dict(base), cfg, sess, [mission])
try:
    final = mod._i512_augment_data_sync(payload, cfg, sess)
finally:
    mod._i546_augment_before = original_before

assert len(final['objects']) == 1, final['objects']
point = final['objects'][0]
assert point['uid'] == event_uid
assert point['callsign'] == 'DS-P07'
assert point['name'] == 'DS-P07'
assert point['mil2525_file'] == 'friendly-ground-equipment-armored-vehicle.svg'
assert point['mission_content_uid'] == content_uid
assert point['mission_delete_target'] == 'uid'
assert point['mission_delete_value'] == event_uid
expected_object_id = 'datasync-' + hashlib.sha256(('uid:' + event_uid).encode()).hexdigest()[:24]
assert point['object_id'] == expected_object_id, point
assert final['mission_cot_symbol_enrichment_i546']['duplicate_canonical_point_rows_removed'] == 1

# Mission ownership and exact UID filtering use the event UID, preventing a duplicate live marker.
mod._i537_update_mission_uid_cache(final, 'darktek')
assert mod._i537_is_exact_mission_uid({'uid': event_uid}) is True
assert mod._i537_is_exact_mission_uid({'uid': content_uid}) is False

# Same-UID symbol changes still replace the prior symbol fingerprint.
xml2 = f'''<event version="2.0" uid="{event_uid}" type="a-f-G-U-C-F" time="2026-07-25T22:05:00Z" start="2026-07-25T22:05:00Z" stale="2026-07-25T22:15:00Z"><point lat="34.5901786" lon="-117.014907" hae="0" ce="10" le="10"/><detail><contact callsign="DS-P07"/><usericon iconsetpath="COT_MAPPING_2525C/a-f-G-U-C-F"/></detail></event>'''
event2 = mod._i545_extract_events({}, xml2)[event_uid.casefold()]
changed, applied, reason = mod._i545_merge_event(point, event2)
assert applied and reason == 'merged'
assert changed['type'] == 'a-f-G-U-C-F'
assert changed['callsign'] == 'DS-P07'
assert changed['data_sync_symbol_changed_i546'] is True

# A removed Mission UID association creates the exact event-UID tombstone even
# when the retained object row still exposes the generic content UUID.
mod._I543_TOMBSTONES.clear()
active = dict(payload)
active['objects'] = [content_row]
kept = mod._i539_filter_deleted_orphans(active)
assert len(kept['objects']) == 1, kept
removed_payload = dict(active)
removed_payload['mission_uids'] = []
removed = mod._i539_filter_deleted_orphans(removed_payload)
assert removed['objects'] == [], removed['objects']
tomb = removed['data_sync_deleted_uid_tombstones_i543']
assert tomb['uids'] == [event_uid.casefold()], tomb

cfg_public = mod.tak_map_config()
assert cfg_public['version'] == '1.3.0-i546'
assert cfg_public['data_sync_control']['canonical_cot_uid_priority'] is True
assert cfg_public['data_sync_control']['mission_cot_callsign_merge'] is True
assert cfg_public['milstd2525c']['friendly_armored_vehicle_resolution'] == 'friendly-ground-equipment-armored-vehicle.svg'
assert mod.TAK_MAP_ITERATION == 'i546'
print('i546 canonical Mission CoT UID, callsign, symbol, dedupe, and tombstone tests passed')
