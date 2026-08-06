#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tak_dashboard_i545_test', ROOT / 'tak_dashboard.py')
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

uid = '9a28f404-23b5-460b-adb5-12ebe39ef5c9'
xml = f'''<events>
<event version="2.0" uid="{uid}" type="a-f-G-U-C-F" time="2026-07-25T06:50:00Z" start="2026-07-25T06:50:00Z" stale="2026-07-25T07:00:00Z">
  <point lat="34.5901786" lon="-117.014907" hae="0" ce="10" le="10"/>
  <detail><contact callsign="DS-P09"/><usericon iconsetpath="COT_MAPPING_2525C/a-f-G-U-C-F"/></detail>
</event>
<event version="2.0" uid="{uid}" type="a-f-G-U-C-C" time="2026-07-25T06:55:00Z" start="2026-07-25T06:55:00Z" stale="2026-07-25T07:05:00Z">
  <point lat="34.5901786" lon="-117.014907" hae="0" ce="10" le="10"/>
  <detail><contact callsign="DS-P09"/><usericon iconsetpath="COT_MAPPING_2525C/a-f-G-U-C-C"/></detail>
</event>
</events>'''

events = mod._i545_extract_events({}, xml)
assert list(events) == [uid.casefold()], events
newest = events[uid.casefold()]
assert newest['type'] == 'a-f-G-U-C-C', newest
assert newest['iconsetPath'].endswith('a-f-G-U-C-C'), newest
assert newest['mission_cot_event_epoch'] > 0

# The newest mission event replaces the generic database type and creates a new
# exact symbol fingerprint for the same UID. The incoming type/usericon remains
# preserved even when the bundled SVG library resolves only to a parent fallback.
db_row = {
    'uid': uid,
    'callsign': 'DS-P09',
    'lat': 34.5901786,
    'lon': -117.014907,
    'type': 'a-f-G-U-S',
    'updated': '2026-07-25T06:51:42.006Z',
    'source': 'OpenTAKServer Data Sync mission_uids',
}
old_fingerprint = mod._i545_symbol_fingerprint(db_row)
merged, applied, reason = mod._i545_merge_event(db_row, newest)
assert applied and reason == 'merged', (applied, reason, merged)
assert merged['type'] == 'a-f-G-U-C-C', merged
assert merged['cot_type'] == 'a-f-G-U-C-C', merged
assert merged['iconsetPath'].endswith('a-f-G-U-C-C'), merged
assert merged['mission_cot_xml'].startswith('<event'), merged
assert merged['data_sync_symbol_fingerprint_i545'] != old_fingerprint, merged
assert merged['data_sync_symbol_changed_i545'] is True, merged
assert merged['data_sync_symbol_enrichment_i545']['metadata_preserved_even_when_svg_missing'] is True

# An older detailed event must never overwrite a newer database update.
newer_db = dict(db_row, updated='2026-07-25T07:00:00Z', type='a-f-G-U-S')
old_event = dict(newest, mission_cot_event_epoch=mod._i545_parse_epoch('2026-07-25T06:55:00Z'))
skipped, applied, reason = mod._i545_merge_event(newer_db, old_event)
assert not applied and reason == 'mission-cot-event-older-than-database-row', (applied, reason, skipped)
assert skipped['type'] == 'a-f-G-U-S'

# Cached exact-UID enrichment is merged without blocking the Data Sync request.
mod._I545_ENRICH_CACHE.clear()
mod._I545_ENRICH_INFLIGHT.clear()
mod._I529_REQUEST_CONTEXT.session_token = 'test-session'
mod._I529_REQUEST_CONTEXT.auth_mode = 'ots-user'
mod._I512_REQUEST_CONTEXT.identity = {'username': 'darktek'}
cfg = {'marti_url': 'https://ots.example:8089'}
sess = {'username': 'darktek', 'auth_mode': 'ots-user', 'profile': {'username': 'darktek'}}
key = mod._i545_cache_key(cfg, sess)
mod._I545_ENRICH_CACHE[key] = {
    'ok': True,
    'time': time.time(),
    'requested': ('takmap-datasync-test',),
    'events': {uid.casefold(): dict(newest, mission_name='TAKMAP-DATASYNC-TEST')},
    'missions': [{'mission': 'TAKMAP-DATASYNC-TEST', 'ok': True, 'status': 200, 'event_count': 1}],
    'event_count': 1,
    'error': '',
}
payload = {
    'ok': True,
    'missions': [{'id': 7, 'name': 'TAKMAP-DATASYNC-TEST'}],
    'objects': [db_row],
    'data_sync_deleted_uid_tombstones_i543': {'version': 'i543', 'count': 0, 'tombstones': []},
}
enriched = mod._i545_apply_cached_enrichment(payload, cfg, sess, ['TAKMAP-DATASYNC-TEST'])
assert enriched['objects'][0]['type'] == 'a-f-G-U-C-C', enriched
assert enriched['mission_cot_symbol_enrichment_i545']['objects_matched'] == 1

# The remote mission /cot request runs in a daemon thread and returns control
# immediately. Its result becomes available for the next 10-second poll.
mod._I545_ENRICH_CACHE.clear()
mod._I545_ENRICH_INFLIGHT.clear()
original_fetch = mod._i545_fetch_mission_events

def slow_fetch(mission: str):
    time.sleep(0.25)
    return {
        'mission': mission,
        'path': '/Marti/api/missions/test/cot',
        'ok': True,
        'status': 200,
        'error': '',
        'events': {uid.casefold(): newest},
        'event_count': 1,
    }

mod._i545_fetch_mission_events = slow_fetch
started = time.monotonic()
scheduled = mod._i545_schedule_enrichment(cfg, sess, ['TAKMAP-DATASYNC-TEST'])
elapsed = time.monotonic() - started
assert scheduled['scheduled'] is True, scheduled
assert elapsed < 0.08, elapsed
for _ in range(80):
    with mod._I545_ENRICH_LOCK:
        record = dict(mod._I545_ENRICH_CACHE.get(key) or {})
    if record.get('event_count') == 1:
        break
    time.sleep(0.01)
else:
    raise AssertionError('background mission CoT enrichment did not complete')
mod._i545_fetch_mission_events = original_fetch

cfg_public = mod.tak_map_config()
assert cfg_public['version'] == '1.3.0-i545'
assert cfg_public['data_sync_control']['automatic_poll_seconds'] == 10
assert cfg_public['data_sync_control']['mission_cot_symbol_enrichment_async'] is True
assert cfg_public['data_sync_control']['same_uid_symbol_updates'] is True
assert cfg_public['milstd2525c']['catalog_expansion_pending'] is True
assert mod.TAK_MAP_ITERATION == 'i545'
print('i545 asynchronous Mission GET /cot exact-UID symbol enrichment tests passed')
