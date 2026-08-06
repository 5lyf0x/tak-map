#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tak_dashboard_i552_usericon_test', ROOT / 'tak_dashboard.py')
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

uid = 'ATAK-DS-P12-UID'
old_row = {
    'uid': uid, 'name': 'DS-P12', 'callsign': 'DS-P12',
    'type': 'a-f-G-U-C', 'cot_type': 'a-f-G-U-C',
    'sidc': 'SFGPEVA--------', 'SIDC': 'SFGPEVA--------',
    'iconsetPath': 'COT_MAPPING_2525C/a-f-G-E-V-A',
    'mil2525_name': 'friendly-ground-equipment-armored-vehicle',
    'mil2525_file': 'friendly-ground-equipment-armored-vehicle.svg',
    'properties': {'type': 'a-f-G-U-C', 'iconsetPath': 'COT_MAPPING_2525C/a-f-G-E-V-A'},
}
xml = f'''<event version="2.0" uid="{uid}" type="a-f-G-U-C" time="2026-07-26T01:00:00Z" start="2026-07-26T01:00:00Z" stale="2026-07-26T01:10:00Z">
  <point lat="34.5901786" lon="-117.014907" hae="0" ce="10" le="10"/>
  <detail><contact callsign="DS-P12 UPDATED"/><usericon iconsetpath="COT_MAPPING_2525C/a-f-G-U-C-I"/></detail>
</event>'''
event = mod._i545_extract_events({}, xml)[uid.casefold()]
merged, applied, reason = mod._i545_merge_event(old_row, event)
assert applied is True
assert reason == 'merged-reviewed-atak-alias-i552'
assert merged['name'] == 'DS-P12 UPDATED'
assert merged['sidc'] == 'SFGPUCI--------'
assert merged['mil2525_file'] == 'friendly-ground-unit-infantry.svg'
decision = merged['data_sync_symbol_decision_i552']
assert decision['authority'] == 'usericon-iconsetpath'
assert decision['reason'] == 'iconset-changed-type-unchanged'
assert decision['iconset_changed'] is True
assert decision['type_changed'] is False

custom_xml = f'''<event version="2.0" uid="{uid}" type="b-m-p-s-m" time="2026-07-26T01:05:00Z" start="2026-07-26T01:05:00Z" stale="2026-07-26T01:15:00Z">
  <point lat="34.5901786" lon="-117.014907" hae="0" ce="10" le="10"/>
  <detail><contact callsign="DS-P12 CUSTOM"/><usericon iconsetpath="COT_MAPPING_SPOTMAP/red-x.png"/></detail>
</event>'''
custom_event = mod._i545_extract_events({}, custom_xml)[uid.casefold()]
custom, applied, _ = mod._i545_merge_event(merged, custom_event)
assert applied is True
assert custom['iconsetPath'] == 'COT_MAPPING_SPOTMAP/red-x.png'
assert not custom.get('mil2525_file')
assert not custom.get('sidc')
assert custom['data_sync_symbol_decision_i552']['authority'] == 'usericon-iconsetpath'
assert custom['data_sync_symbol_decision_i552']['custom_usericon_fallback'] is True
print('i552 iconset-only update and custom usericon fallback regressions passed')
