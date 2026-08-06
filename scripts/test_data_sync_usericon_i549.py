#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tak_dashboard_i549_usericon_test', ROOT / 'tak_dashboard.py')
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

uid = 'ATAK-DS-P12-UID'
old_row = {
    'uid': uid,
    'name': 'DS-P12',
    'callsign': 'DS-P12',
    'title': 'DS-P12',
    'label': 'DS-P12',
    'lat': 34.5901786,
    'lon': -117.014907,
    # The CoT type deliberately stays generic while ATAK changes only usericon.
    'type': 'a-f-G-U-C',
    'cot_type': 'a-f-G-U-C',
    'sidc': 'SFGPEVA--------',
    'SIDC': 'SFGPEVA--------',
    'iconsetPath': 'COT_MAPPING_2525C/a-f-G-E-V-A',
    'mil2525_name': 'friendly-ground-equipment-armored-vehicle',
    'mil2525_file': 'friendly-ground-equipment-armored-vehicle.svg',
    'properties': {
        'type': 'a-f-G-U-C',
        'sidc': 'SFGPEVA--------',
        'iconsetPath': 'COT_MAPPING_2525C/a-f-G-E-V-A',
        'mil2525_name': 'friendly-ground-equipment-armored-vehicle',
        'mil2525_file': 'friendly-ground-equipment-armored-vehicle.svg',
    },
    'source': 'OpenTAKServer Data Sync mission_uids',
}

new_xml = f'''<event version="2.0" uid="{uid}" type="a-f-G-U-C" time="2026-07-26T01:00:00Z" start="2026-07-26T01:00:00Z" stale="2026-07-26T01:10:00Z">
  <point lat="34.5901786" lon="-117.014907" hae="0" ce="10" le="10"/>
  <detail><contact callsign="DS-P12 UPDATED"/><usericon iconsetpath="COT_MAPPING_2525C/a-f-G-U-C-I"/></detail>
</event>'''
event = mod._i545_extract_events({}, new_xml)[uid.casefold()]
assert event['mission_cot_raw_iconset_path_i549'] == 'COT_MAPPING_2525C/a-f-G-U-C-I'
assert event['mission_cot_raw_type_i549'] == 'a-f-G-U-C'
merged, applied, reason = mod._i545_merge_event(old_row, event)
assert applied is True
assert reason == 'merged-current-mission-cot-usericon-i549', reason
assert merged['name'] == 'DS-P12 UPDATED'
assert merged['callsign'] == 'DS-P12 UPDATED'
assert merged['type'] == 'a-f-G-U-C'
assert merged['iconsetPath'] == 'COT_MAPPING_2525C/a-f-G-U-C-I'
assert merged['mission_cot_raw_iconset_path_i549'] == 'COT_MAPPING_2525C/a-f-G-U-C-I'
assert merged['sidc'] == 'SFGPUCI--------', merged.get('sidc')
assert merged['mil2525_file'] == 'friendly-ground-unit-infantry.svg', merged.get('mil2525_file')
assert merged['properties']['sidc'] == 'SFGPUCI--------'
assert merged['properties']['mil2525_file'] == 'friendly-ground-unit-infantry.svg'
diag = merged['data_sync_icon_authority_i549']
assert diag['authority'] == 'usericon-iconsetpath'
assert diag['stale_derived_sidc_blocked'] is True
assert diag['custom_usericon_fallback'] is False

# A custom/Spot Map path that is not in TAK Map's MIL catalog must clear the old
# derived icon and preserve the current path for the browser fallback renderer.
custom_xml = f'''<event version="2.0" uid="{uid}" type="b-m-p-s-m" time="2026-07-26T01:05:00Z" start="2026-07-26T01:05:00Z" stale="2026-07-26T01:15:00Z">
  <point lat="34.5901786" lon="-117.014907" hae="0" ce="10" le="10"/>
  <detail><contact callsign="DS-P12 CUSTOM"/><usericon iconsetpath="COT_MAPPING_SPOTMAP/red-x.png"/></detail>
</event>'''
custom_event = mod._i545_extract_events({}, custom_xml)[uid.casefold()]
custom, applied, reason = mod._i545_merge_event(merged, custom_event)
assert applied is True
assert custom['name'] == 'DS-P12 CUSTOM'
assert custom['iconsetPath'] == 'COT_MAPPING_SPOTMAP/red-x.png'
assert custom['mission_cot_raw_iconset_path_i549'] == 'COT_MAPPING_SPOTMAP/red-x.png'
assert not custom.get('mil2525_file'), custom.get('mil2525_file')
assert not custom.get('sidc'), custom.get('sidc')
assert custom['data_sync_icon_authority_i549']['custom_usericon_fallback'] is True

cfg = mod.tak_map_config()
assert cfg['version'] == '1.3.0-i549'
assert cfg['data_sync_control']['atak_usericon_path_authoritative'] is True
assert cfg['data_sync_control']['usericon_only_update_supported'] is True
assert mod.TAK_MAP_ITERATION == 'i549'
print('i549 ATAK usericon-only refresh, stale SIDC suppression, and custom fallback tests passed')
