#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tak_dashboard_i551_symbol_conflict_test', ROOT / 'tak_dashboard.py')
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

uid = 'a1121512-4c56-4038-bca1-b82c602d3f96'
old_row = {
    'uid': uid,
    'name': 'DS-P12',
    'callsign': 'DS-P12',
    'type': 'a-f-G-U-C-D',
    'cot_type': 'a-f-G-U-C-D',
    'iconsetPath': 'COT_MAPPING_2525C/a-f/a-f-G-U-C-D',
    'usericon_path': 'COT_MAPPING_2525C/a-f/a-f-G-U-C-D',
    'sidc': 'SFGPUCD--------',
    'SIDC': 'SFGPUCD--------',
    'mil2525_name': 'friendly-ground-unit-air-defense',
    'mil2525_file': 'friendly-ground-unit-air-defense.svg',
    'properties': {
        'type': 'a-f-G-U-C-D',
        'cot_type': 'a-f-G-U-C-D',
        'iconsetPath': 'COT_MAPPING_2525C/a-f/a-f-G-U-C-D',
        'usericon_path': 'COT_MAPPING_2525C/a-f/a-f-G-U-C-D',
        'sidc': 'SFGPUCD--------',
        'mil2525_file': 'friendly-ground-unit-air-defense.svg',
    },
}

# Exact DS-P13 capture: ATAK changed the specific CoT type to Anti-Armor but
# retained the older Air Defense usericon path.
xml = f'''<event access="Undefined" how="h-g-i-g-o" stale="2026-07-26T04:49:39.129Z" start="2026-07-26T04:44:39.129Z" time="2026-07-26T04:44:39.129Z" type="a-f-G-U-C-A-A" uid="{uid}" version="2.0">
  <point lat="34.5901786" lon="-117.014907" hae="0" ce="10" le="10"/>
  <detail><contact callsign="DS-P13"/><usericon iconsetpath="COT_MAPPING_2525C/a-f/a-f-G-U-C-D"/></detail>
</event>'''
event = mod._i545_extract_events({}, xml)[uid.casefold()]
merged, applied, reason = mod._i545_merge_event(old_row, event)
assert applied is True
assert reason == 'merged-reviewed-atak-alias-i551', reason
assert merged['name'] == 'DS-P13'
assert merged['callsign'] == 'DS-P13'
assert merged['type'] == 'a-f-G-U-C-A-A'
assert merged['iconsetPath'] == 'COT_MAPPING_2525C/a-f/a-f-G-U-C-D'
assert merged['sidc'] == 'SFGPUCAA-------', merged.get('sidc')
assert merged['mil2525_file'] == 'friendly-ground-unit-tank-destroyer.svg', merged.get('mil2525_file')
assert merged['properties']['sidc'] == 'SFGPUCAA-------'
assert merged['properties']['mil2525_file'] == 'friendly-ground-unit-tank-destroyer.svg'
decision = merged['data_sync_symbol_decision_i551']
assert decision['conflict'] is True
assert decision['authority'] == 'event-type'
assert decision['reason'] == 'specific-type-changed-iconset-unchanged'
assert decision['type_changed'] is True
assert decision['iconset_changed'] is False
assert decision['type_candidate_file'] == 'friendly-ground-unit-tank-destroyer.svg'
assert decision['iconset_candidate_file'] == 'friendly-ground-unit-air-defense.svg'
assert decision['selected_file'] == 'friendly-ground-unit-tank-destroyer.svg'

# Even without usable historical fields, a conflicting specific current type is
# the safe default authority unless only the iconset is known to have changed.
minimal_row = {'uid': uid, 'name': 'DS-P13'}
minimal, applied, _ = mod._i545_merge_event(minimal_row, event)
assert applied is True
assert minimal['mil2525_file'] == 'friendly-ground-unit-tank-destroyer.svg'
assert minimal['data_sync_symbol_decision_i551']['authority'] == 'event-type'
assert minimal['data_sync_symbol_decision_i551']['reason'] == 'specific-current-type-conflict-default'

cfg = mod.tak_map_config()
assert cfg['version'] == '1.3.0-i551'
assert cfg['data_sync_control']['change_aware_symbol_conflict_resolution'] is True
assert cfg['data_sync_control']['specific_changed_cot_type_overrides_unchanged_iconset'] is True
assert cfg['data_sync_control']['changed_iconset_overrides_unchanged_generic_cot_type'] is True
assert cfg['milstd2525c']['decision_metadata'] == 'data_sync_symbol_decision_i551'
assert mod.TAK_MAP_ITERATION == 'i551'
print('i551 DS-P13 reviewed changed-type/stale-iconset conflict regression passed')
