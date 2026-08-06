#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tak_dashboard_i613_source_extension_filter_test', ROOT / 'tak_dashboard.py')
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

polygon = {
    'uid': 'tkgw-ext:faa-socal-moa:OBJECTID-100',
    'id': 'tkgw-ext:faa-socal-moa:OBJECTID-100',
    'callsign': 'LEMOORE A MOA',
    'type': 'u-d-f',
    'kind': 'eud',
    'lat': 36.1,
    'lon': -120.2,
    'source': 'OpenTAKServer cot',
}
line_part = {
    'uid': 'tkgw-ext:faa-socal-moa:OBJECTID-101:part:2',
    'callsign': 'MOA BOUNDARY',
    'cot_type': 'u-d-f',
    'kind': 'cot',
    'lat': 35.8,
    'lon': -118.7,
}
metadata_polygon = {
    'uid': 'legacy-source-key-1',
    'callsign': 'Metadata Drawing',
    'type': 'u-d-f',
    'lat': 34.1,
    'lon': -117.2,
    'xml': '<event uid="legacy-source-key-1" type="u-d-f"><detail><takgateway_source_extension source_id="legacy"/></detail></event>',
}
source_point = {
    'uid': 'tkgw-ext:weather-stations:station-1',
    'callsign': 'Station 1',
    'type': 'a-f-G-U-C',
    'kind': 'cot',
    'lat': 34.0,
    'lon': -118.0,
}
normal_eud = {
    'uid': 'ANDROID-ATAK-001',
    'callsign': 'EUD-01',
    'type': 'a-f-G-U-C',
    'kind': 'eud',
    'lat': 34.2,
    'lon': -118.1,
}
non_extension_drawing = {
    'uid': 'operator-drawing-1',
    'callsign': 'Operator Drawing',
    'type': 'u-d-f',
    'kind': 'cot',
    'lat': 34.3,
    'lon': -118.2,
}

assert mod._i613_source_extension_drawing(polygon)
assert mod._i613_source_extension_drawing(line_part)
assert mod._i613_source_extension_drawing(metadata_polygon)
assert not mod._i613_source_extension_drawing(source_point)
assert not mod._i613_source_extension_drawing(normal_eud)
assert not mod._i613_source_extension_drawing(non_extension_drawing)

cot = mod._i613_filter_source_extension_live_payload({
    'ok': True,
    'markers': [polygon, line_part, metadata_polygon, source_point, normal_eud, non_extension_drawing],
}, 'cot')
assert [row['uid'] for row in cot['markers']] == [
    source_point['uid'], normal_eud['uid'], non_extension_drawing['uid']
]
diag = cot['source_extension_live_filter_i613']
assert diag['version'] == 'i613'
assert diag['endpoint'] == 'cot'
assert diag['rows_before'] == 6
assert diag['rows_after'] == 3
assert diag['removed_count'] == 3
assert diag['legitimate_point_source_extensions_preserved'] is True

# Source Extension objects are not physical EUD devices. This excludes both
# drawing and point records from the EUD device list while the point remains in
# the live CoT marker path above.
euds = mod._i613_filter_source_extension_live_payload({
    'ok': True,
    'euds': [polygon, source_point, normal_eud],
}, 'euds')
assert [row['uid'] for row in euds['euds']] == [normal_eud['uid']]
assert euds['source_extension_live_filter_i613']['removed_count'] == 2

# Raw normalization is also protected, so a representative point never enters
# the live marker collection before endpoint filtering.
raw_polygon = {
    'xml': '<event uid="tkgw-ext:faa-socal-moa:raw-1" type="u-d-f" time="2099-01-01T00:00:00Z"><point lat="34.1" lon="-117.2"/><detail><contact callsign="RAW MOA"/><takgateway_source_extension source_id="faa-socal-moa"/></detail></event>'
}
assert mod._normalize_tak_marker(raw_polygon, 'cot', 'cot') is None

raw_point = {
    'xml': '<event uid="tkgw-ext:weather-stations:raw-point" type="a-f-G-U-C" time="2099-01-01T00:00:00Z"><point lat="34.1" lon="-117.2"/><detail><contact callsign="Station"/><takgateway_source_extension source_id="weather-stations"/></detail></event>'
}
normalized_point = mod._normalize_tak_marker(raw_point, 'cot', 'cot')
assert normalized_point is not None
assert normalized_point['uid'] == 'tkgw-ext:weather-stations:raw-point'

# Verify the final public endpoint wrappers, not only the helper.
old_cot = mod._i613_cot_before
old_euds = mod._i613_euds_before
try:
    mod._i613_cot_before = lambda *a, **k: {'ok': True, 'markers': [polygon, source_point, normal_eud]}
    mod._i613_euds_before = lambda *a, **k: {'ok': True, 'euds': [polygon, source_point, normal_eud]}
    assert [x['uid'] for x in mod.tak_map_cot_markers()['markers']] == [source_point['uid'], normal_eud['uid']]
    assert [x['uid'] for x in mod.tak_map_euds()['euds']] == [normal_eud['uid']]
finally:
    mod._i613_cot_before = old_cot
    mod._i613_euds_before = old_euds

cfg = mod.tak_map_config()
cap = cfg['source_extension_live_drawing_suppression_i613']
assert cap['gateway_data_authoritative_for_drawings'] is True
assert cap['live_u_d_f_representative_points_suppressed'] is True
assert cap['source_extension_points_preserved'] is True

print('i613 Source Extension drawing representative-point and EUD suppression checks passed')
