#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
alias_path = ROOT / 'assets' / 'mil2525' / 'atak-compatibility-aliases-i552.json'
alias = json.loads(alias_path.read_text(encoding='utf-8'))
assert alias['version'] == 'i552'
assert alias['summary']['sidc_aliases'] >= 800
assert alias['summary']['cot_type_aliases'] >= 900
assert alias['summary']['missing_reviewed_svg_files'] == 0
assert alias['policy']['exact_reviewed_alias_before_catalog_parent_fallback'] is True
assert alias['policy']['prefix_alias_requires_identical_reviewed_svg_bytes'] is True

construction = alias['by_cot_type']['a-f-g-u-c-e-n']
assert construction['file'] == 'friendly-emergency-construction.svg'
assert construction['alias_kinds'] == ['review-candidate']

howitzer = alias['by_cot_type']['a-f-g-e-w-h']
assert howitzer['file'] == 'friendly-ground-equipment-self-propelled-howitzer.svg'
assert sorted(howitzer['equivalent_files']) == [
    'friendly-ground-equipment-self-propelled-artillery.svg',
    'friendly-ground-equipment-self-propelled-howitzer.svg',
]
assert 'review-candidate-prefix-identical-artwork' in howitzer['alias_kinds']

spec = importlib.util.spec_from_file_location('tak_dashboard_i552_alias_test', ROOT / 'tak_dashboard.py')
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

r = mod._i552_resolve_type('a-f-G-U-C-E-N')
assert r and r['file'] == 'friendly-emergency-construction.svg', r
assert r['sidc'] == 'SFGPUCEN-------'
assert r['reviewed_alias'] is True

r = mod._i552_resolve_type('a-f-G-E-W-H')
assert r and r['file'] == 'friendly-ground-equipment-self-propelled-howitzer.svg', r
assert r['sidc'] == 'SFGPEWH--------'
assert r['reviewed_alias'] is True

# DS-P13: current Construction type must override the stale Air Defense icon path.
prior = {
    'uid': 'a1121512-4c56-4038-bca1-b82c602d3f96',
    'name': 'DS-P13',
    'cot_type': 'a-f-G-U-C-E-N',
    'type': 'a-f-G-U-C-E-N',
    'iconsetPath': '',
}
xml = '''<event access="Undefined" how="h-g-i-g-o" stale="2026-07-26T05:00:00Z" start="2026-07-26T04:55:00Z" time="2026-07-26T04:55:00Z" type="a-f-G-U-C-E-N" uid="a1121512-4c56-4038-bca1-b82c602d3f96" version="2.0"><point lat="34.5" lon="-117" hae="0" ce="10" le="10"/><detail><contact callsign="DS-P13"/><usericon iconsetpath="COT_MAPPING_2525C/a-f/a-f-G-U-C-D"/></detail></event>'''
event = mod._i545_extract_events({}, xml)['a1121512-4c56-4038-bca1-b82c602d3f96']
merged, applied, reason = mod._i545_merge_event(prior, event)
assert applied and reason == 'merged-reviewed-atak-alias-i552', (applied, reason)
assert merged['mil2525_file'] == 'friendly-emergency-construction.svg', merged
assert merged['data_sync_symbol_decision_i552']['authority'] == 'event-type'
assert merged['data_sync_symbol_decision_i552']['reviewed_alias_selected'] is True

# DS-P10: exact reviewed Howitzer type overrides the stale Semi iconset path.
prior = {
    'uid': '28a3a6b9-8c6e-4619-bddc-0f5e188bb944',
    'name': 'DS-P10',
    'cot_type': 'a-f-G-E-W-H',
    'type': 'a-f-G-E-W-H',
    'iconsetPath': 'COT_MAPPING_2525C/a-f/a-f-G-E-V-U-S',
}
xml = '''<event access="Undefined" how="h-g-i-g-o" stale="2026-07-26T05:00:00Z" start="2026-07-26T04:55:00Z" time="2026-07-26T04:55:00Z" type="a-f-G-E-W-H" uid="28a3a6b9-8c6e-4619-bddc-0f5e188bb944" version="2.0"><point lat="34.6" lon="-117.1" hae="0" ce="10" le="10"/><detail><contact callsign="DS-P10"/><usericon iconsetpath="COT_MAPPING_2525C/a-f/a-f-G-E-V-U-S"/></detail></event>'''
event = mod._i545_extract_events({}, xml)['28a3a6b9-8c6e-4619-bddc-0f5e188bb944']
merged, applied, reason = mod._i545_merge_event(prior, event)
assert applied and reason == 'merged-reviewed-atak-alias-i552', (applied, reason)
assert merged['mil2525_file'] == 'friendly-ground-equipment-self-propelled-howitzer.svg', merged
assert merged['data_sync_symbol_decision_i552']['authority'] == 'event-type'
assert merged['data_sync_symbol_decision_i552']['type_candidate_file'] == 'friendly-ground-equipment-self-propelled-howitzer.svg'
assert merged['data_sync_symbol_decision_i552']['iconset_candidate_file'] == 'friendly-ground-equipment-semi.svg'

cfg = mod.tak_map_config()
assert cfg['version'] == '1.3.0-i552'
assert cfg['data_sync_control']['reviewed_alias_before_parent_fallback'] is True
assert cfg['milstd2525c']['reviewed_sidc_aliases'] == len(alias['by_sidc'])
assert cfg['milstd2525c']['reviewed_cot_type_aliases'] == len(alias['by_cot_type'])
print('i552 systematic reviewed ATAK alias catalog regressions passed')
