#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tak_dashboard_i552_upgrade_test', ROOT / 'tak_dashboard.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def stale_i550_row(name: str, cot_type: str, iconset: str, stale_sidc: str, stale_file: str, authority: str) -> dict:
    return {
        'uid': name.lower(),
        'name': name,
        'callsign': name,
        'type': cot_type,
        'cot_type': cot_type,
        'atak_cot_type': cot_type,
        'mission_cot_raw_type_i550': cot_type,
        'data_sync_current_cot_type_i550': cot_type,
        'mission_cot_raw_iconset_path_i550': iconset,
        'data_sync_current_iconset_path_i550': iconset,
        'iconsetPath': iconset,
        'iconsetpath': iconset,
        'usericon_path': iconset,
        'sidc': stale_sidc,
        'SIDC': stale_sidc,
        'mil2525_file': stale_file,
        'mil2525_name': stale_file.removesuffix('.svg'),
        'symbol_resolution_i550': {'version': 'i550', 'source': 'stale-regression'},
        'data_sync_symbol_decision_i550': {
            'version': 'i550',
            'authority': authority,
            'selected_cot_type': cot_type if authority == 'event-type' else '',
            'selected_iconset_path': iconset if authority == 'usericon-iconsetpath' else '',
        },
        'properties': {
            'type': cot_type,
            'cot_type': cot_type,
            'mission_cot_raw_type_i550': cot_type,
            'mission_cot_raw_iconset_path_i550': iconset,
            'iconsetPath': iconset,
            'sidc': stale_sidc,
            'SIDC': stale_sidc,
            'mil2525_file': stale_file,
            'mil2525_name': stale_file.removesuffix('.svg'),
            'symbol_resolution_i550': {'version': 'i550', 'source': 'stale-regression'},
            'data_sync_symbol_decision_i550': {'version': 'i550', 'authority': authority},
        },
    }


construction = stale_i550_row(
    'DS-P13',
    'a-f-G-U-C-E-N',
    'COT_MAPPING_2525C/a-f/a-f-G-U-C-D',
    'SFGPUCE--------',
    'friendly-ground-unit-engineer.svg',
    'event-type',
)
howitzer = stale_i550_row(
    'DS-P10',
    'a-f-G-E-W-H',
    'COT_MAPPING_2525C/a-f/a-f-G-E-V-U-S',
    'SFGPEVUS-------',
    'friendly-ground-equipment-semi.svg',
    'usericon-iconsetpath',
)

normalized_construction = mod._i552_normalize_visible_row(construction)
assert normalized_construction['mil2525_file'] == 'friendly-emergency-construction.svg', normalized_construction
assert normalized_construction['sidc'] == 'SFGPUCEN-------', normalized_construction
assert normalized_construction['data_sync_symbol_decision_i552']['authority'] == 'event-type'
assert normalized_construction['data_sync_symbol_decision_i552']['upgrade_normalized'] is True
assert normalized_construction['data_sync_symbol_decision_i552']['previous_decision_version'] == 'i550'
assert normalized_construction['properties']['mil2525_file'] == 'friendly-emergency-construction.svg'
assert normalized_construction['properties']['data_sync_symbol_decision_i552']['version'] == 'i552'
assert normalized_construction['symbol_resolution_i552']['reviewed_alias_selected'] is True
assert 'symbol_resolution_i550' not in normalized_construction
assert 'symbol_resolution_i550' not in normalized_construction['properties']

normalized_howitzer = mod._i552_normalize_visible_row(howitzer)
assert normalized_howitzer['mil2525_file'] == 'friendly-ground-equipment-self-propelled-howitzer.svg', normalized_howitzer
assert normalized_howitzer['data_sync_symbol_decision_i552']['authority'] == 'event-type'
assert normalized_howitzer['data_sync_symbol_decision_i552']['previous_decision_authority'] == 'usericon-iconsetpath'
assert normalized_howitzer['properties']['mil2525_file'] == 'friendly-ground-equipment-self-propelled-howitzer.svg'

# Idempotence: a second response normalization keeps the current visual and decision.
again = mod._i552_normalize_visible_row(normalized_howitzer)
assert again['mil2525_file'] == 'friendly-ground-equipment-self-propelled-howitzer.svg'
assert again['data_sync_symbol_decision_i552']['version'] == 'i552'
assert again['data_sync_upgrade_normalized_i552'] is True

# Custom user-icon packages remain deterministic browser fallbacks rather than
# being overwritten by a derived generic symbol during the upgrade pass.
custom = {
    'uid': 'custom-1',
    'name': 'CUSTOM',
    'type': 'a-f-G-U-C',
    'mission_cot_raw_type_i550': 'a-f-G-U-C',
    'mission_cot_raw_iconset_path_i550': 'MyCustomIcons/incident/custom.png',
    'iconsetPath': 'MyCustomIcons/incident/custom.png',
    'data_sync_symbol_decision_i550': {'version': 'i550', 'authority': 'usericon-iconsetpath'},
    'properties': {},
}
normalized_custom = mod._i552_normalize_visible_row(custom)
custom_decision = normalized_custom['data_sync_symbol_decision_i552']
assert custom_decision['authority'] == 'usericon-iconsetpath', custom_decision
assert custom_decision['custom_usericon_fallback'] is True
assert normalized_custom.get('mil2525_file', '') == ''
assert normalized_custom['iconsetPath'] == 'MyCustomIcons/incident/custom.png'

# Exercise the final response wrapper. The older rows are unchanged Mission
# objects; no merge hook is called, yet both must be upgraded in the response.
original_before = mod._i552_augment_before
try:
    mod._i552_augment_before = lambda base, cfg, sess: {
        'version': 'i551',
        'objects': [construction, howitzer],
        'missions': ['TAKMAP-DATASYNC-TEST'],
        'mission_cot_symbol_enrichment_i551': {'version': 'i551'},
    }
    payload = mod._i512_augment_data_sync({}, {}, {})
finally:
    mod._i552_augment_before = original_before

assert payload['version'] == 'i552'
files = {row['name']: row.get('mil2525_file') for row in payload['objects']}
assert files == {
    'DS-P13': 'friendly-emergency-construction.svg',
    'DS-P10': 'friendly-ground-equipment-self-propelled-howitzer.svg',
}, files
diag = payload['mission_cot_symbol_enrichment_i552']
assert diag['final_visible_response_normalization'] is True
assert diag['unchanged_older_events_reprocessed'] is True
assert diag['objects_upgrade_normalized_i552'] == 2
assert diag['objects_visual_file_changed_during_upgrade_i552'] == 2

print('i552 unchanged i550/i551 Data Sync upgrade normalization regression passed')
