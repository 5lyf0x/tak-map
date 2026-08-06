#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tak_dashboard_i547_live_refresh_test', ROOT / 'tak_dashboard.py')
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

mission = 'TAKMAP-DATASYNC-TEST'
uid = 'ATAK-DS-P12-UID'
old_xml = f'''<event version="2.0" uid="{uid}" type="a-f-G-E-V-A" time="2026-07-25T20:00:00Z" start="2026-07-25T20:00:00Z" stale="2026-07-25T20:10:00Z">
  <point lat="34.5901786" lon="-117.014907" hae="0" ce="10" le="10"/>
  <detail><contact callsign="DS-P12"/><usericon iconsetpath="COT_MAPPING_2525C/a-f-G-E-V-A"/></detail>
</event>'''
new_xml = f'''<event version="2.0" uid="{uid}" type="a-f-G-U-C-I" time="2026-07-25T20:05:00Z" start="2026-07-25T20:05:00Z" stale="2026-07-25T20:15:00Z">
  <point lat="34.5901786" lon="-117.014907" hae="0" ce="10" le="10"/>
  <detail><contact callsign="DS-P12 RENAMED"/></detail>
</event>'''

row = {
    'uid': uid,
    'name': 'DS-P12',
    'callsign': 'DS-P12',
    'title': 'DS-P12',
    'label': 'DS-P12',
    'lat': 34.5901786,
    'lon': -117.014907,
    # Deliberately newer than the current Mission CoT event. This is a database
    # bookkeeping timestamp and must no longer reject the event.
    'updated': '2026-07-25T22:00:00Z',
    'xml': old_xml,
    'type': 'a-f-G-E-V-A',
    'cot_type': 'a-f-G-E-V-A',
    'iconsetPath': 'COT_MAPPING_2525C/a-f-G-E-V-A',
    'mil2525_file': 'friendly-ground-equipment-armored-vehicle.svg',
    'symbol_resolution_i537': {'version': 'i537'},
    'properties': {
        'name': 'DS-P12',
        'callsign': 'DS-P12',
        'title': 'DS-P12',
        'type': 'a-f-G-E-V-A',
        'iconsetPath': 'COT_MAPPING_2525C/a-f-G-E-V-A',
        'mil2525_file': 'friendly-ground-equipment-armored-vehicle.svg',
        'symbol_resolution_i537': {'version': 'i537'},
    },
    'source': 'OpenTAKServer Data Sync mission_uids',
    'mission_id': 7,
}

event = mod._i545_extract_events({}, new_xml)[uid.casefold()]
merged, applied, reason = mod._i545_merge_event(row, event)
assert applied is True
assert reason == 'merged-current-mission-cot-event', reason
assert merged['callsign'] == 'DS-P12 RENAMED'
assert merged['name'] == 'DS-P12 RENAMED'
assert merged['title'] == 'DS-P12 RENAMED'
assert merged['label'] == 'DS-P12 RENAMED'
assert merged['type'] == 'a-f-G-U-C-I'
assert merged['cot_type'] == 'a-f-G-U-C-I'
assert not merged.get('iconsetPath'), merged.get('iconsetPath')
assert merged['sidc'] == 'SFGPUCI--------'
assert merged['mil2525_file'] == 'friendly-ground-unit-infantry.svg'
assert merged['properties']['name'] == 'DS-P12 RENAMED'
assert merged['properties']['title'] == 'DS-P12 RENAMED'
assert merged['properties']['type'] == 'a-f-G-U-C-I'
assert not merged['properties'].get('iconsetPath')
assert merged['data_sync_symbol_changed_i547'] is True
live = merged['data_sync_live_event_i547']
assert live['database_row_timestamp_gate_disabled'] is True
assert live['callsign'] == 'DS-P12 RENAMED'
assert live['cot_type'] == 'a-f-G-U-C-I'
assert live['selected_event_uid'] == uid

# The primary Mission /cot read must not use creatorUid. The authenticated user
# certificate is the scope; ATAK may have edited the point using another EUD UID.
paths: list[str] = []
def request(path, method='GET', **kwargs):
    paths.append(path)
    return {'ok': True, 'status': 200, 'json': {}, 'body': new_xml, 'attempts': []}

mod._ots_mission_api_request = request
fetched = mod._i545_fetch_mission_events('Mission A')
assert paths == ['/Marti/api/missions/Mission%20A/cot'], paths
assert fetched['query_strategy'] == 'authenticated-user-scope-no-creatorUid'
assert fetched['creator_uid_filter_primary'] is False
assert fetched['creator_uid_fallback_used'] is False
assert fetched['event_count'] == 1

# A forced Data Sync refresh synchronously refreshes Mission CoT and applies the
# new callsign/icon in the same response rather than waiting another poll cycle.
payload = {
    'ok': True,
    'missions': [{'id': 7, 'name': mission}],
    'mission_uids': [{'mission_id': 7, 'uid': uid}],
    'mission_content': [],
    'mission_logs': [],
    'mission_roles': [],
    'mission_content_mission': [],
    'packages': [],
    'objects': [row],
    'data_sync_deleted_uid_tombstones_i546': {'version': 'i546', 'count': 0, 'tombstones': []},
}
cfg = {'marti_url': 'https://ots.example:8089'}
sess = {'username': 'operator', 'auth_mode': 'ots-user', 'profile': {'username': 'operator'}}
mod._I512_REQUEST_CONTEXT.identity = {'username': 'operator'}
mod._I537_REQUEST_CONTEXT.identity_key = 'operator'
mod._I545_ENRICH_CACHE.clear()
mod._I545_ENRICH_INFLIGHT.clear()

original_before = mod._i547_augment_before
original_fetch = mod._i545_fetch_mission_events
mod._i547_augment_before = lambda base, _cfg, _sess: dict(base)
mod._i545_fetch_mission_events = lambda name: {
    'mission': name,
    'path': '/Marti/api/missions/test/cot',
    'ok': True,
    'status': 200,
    'error': '',
    'events': {uid.casefold(): dict(event)},
    'event_count': 1,
    'query_strategy': 'authenticated-user-scope-no-creatorUid',
    'creator_uid_filter_primary': False,
    'creator_uid_fallback_used': False,
    'request_attempts_i547': [],
}
mod._I547_REQUEST_CONTEXT.force = True
mod._I547_REQUEST_CONTEXT.reason = 'manual-data-sync-refresh'
try:
    forced = mod._i512_augment_data_sync(payload, cfg, sess)
finally:
    mod._i547_augment_before = original_before
    mod._i545_fetch_mission_events = original_fetch
    mod._I547_REQUEST_CONTEXT.force = False
    mod._I547_REQUEST_CONTEXT.reason = ''

assert len(forced['objects']) == 1
point = forced['objects'][0]
assert point['name'] == 'DS-P12 RENAMED'
assert point['mil2525_file'] == 'friendly-ground-unit-infantry.svg'
diag = forced['mission_cot_symbol_enrichment_i547']
assert diag['force_requested'] is True
assert diag['forced_refresh_completed'] is True
assert diag['forced_refresh_ok'] is True
assert diag['forced_refresh_event_count'] == 1
assert diag['database_row_timestamp_gate_disabled'] is True
assert diag['creator_uid_filter_primary'] is False
assert forced['data_sync_deleted_uid_tombstones_i547']['version'] == 'i547'

cfg_public = mod.tak_map_config()
assert cfg_public['version'] == '1.3.0-i547'
assert cfg_public['data_sync_control']['same_uid_name_updates'] is True
assert cfg_public['data_sync_control']['same_uid_icon_updates'] is True
assert cfg_public['data_sync_control']['delete_lookup_uses_visible_canonical_pipeline'] is True
assert mod.TAK_MAP_ITERATION == 'i547'
print('i547 live same-UID callsign/icon refresh and unfiltered Mission /cot tests passed')
