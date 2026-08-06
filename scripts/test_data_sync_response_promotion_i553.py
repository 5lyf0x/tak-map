#!/usr/bin/env python3
from pathlib import Path
import importlib.util, sys
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('tak_dashboard_i553_promotion',ROOT/'tak_dashboard.py')
mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;assert spec.loader;spec.loader.exec_module(mod)
row={
 'uid':'ATAK-UPGRADE','callsign':'DS-P13','cot_type':'a-f-G-U-C-E-N',
 'mission_cot_raw_type_i552':'a-f-G-U-C-E-N',
 'data_sync_current_cot_type_i552':'a-f-G-U-C-E-N',
 'data_sync_symbol_decision_i552':{'version':'i552','authority':'event-type','selected_cot_type':'a-f-G-U-C-E-N','selected_file':'friendly-emergency-construction.svg'},
 'symbol_resolution_i552':{'version':'i552','source':'upgrade-normalized-reviewed-cot-type-i552'},
 'properties':{'data_sync_symbol_decision_i552':{'version':'i552','authority':'event-type','selected_cot_type':'a-f-G-U-C-E-N'}}
}
out=mod._i553_promote_symbol_fields(row)
assert out['mission_cot_raw_type_i553']=='a-f-G-U-C-E-N'
assert out['data_sync_symbol_decision_i553']['version']=='i553'
assert out['data_sync_symbol_decision_i553']['selected_file']=='friendly-emergency-construction.svg'
assert out['symbol_resolution_i553']['version']=='i553'
assert 'i553' in out['symbol_resolution_i553']['source']
assert out['properties']['data_sync_symbol_decision_i553']['version']=='i553'
print('i553 final-response promotion of existing i552 symbol decisions passed')
