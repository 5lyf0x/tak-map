#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
os.environ['TAK_MAP_DATA_DIR'] = tempfile.mkdtemp(prefix='tak-map-i598-cot-xml-')
os.environ['TAK_MAP_MIL_ROOT'] = str(ROOT / 'assets/mil2525')
os.environ['TAK_MAP_TEST_SKIP_ADSB_WARMUP'] = '1'

spec = importlib.util.spec_from_file_location('tak_dashboard_i598_cot_xml', ROOT / 'tak_dashboard.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader
spec.loader.exec_module(mod)

assert mod.TAK_MAP_ITERATION == 'i598'
assert mod.tak_map_config()['version'] == '1.3.0-i598'

mission = 'PROTECTED-XML-MISSION'
uid = 'XML-ONLY-POINT-1'
event = (
    f'<event version="2.0" uid="{uid}" type="a-f-G-U-C" how="h-e" '
    'time="2026-07-30T12:00:00Z" start="2026-07-30T12:00:00Z" '
    'stale="2026-07-30T12:10:00Z">'
    '<point lat="34.1234" lon="-117.4321" hae="125.5" ce="10" le="10"/>'
    '<detail><contact callsign="XML ONLY POINT"/></detail></event>'
)

for xml in (event, '<events>' + event + '</events>'):
    raw = {'ok': True, 'status': 200, 'json': {}, 'body': xml, 'error': ''}
    parsed = mod._i569_parsed_result(raw)
    assert parsed.get('cot_xml_body_i598') is True, parsed
    assert parsed.get('body') == xml, parsed
    assert mod._i568_result_body(parsed) == xml, parsed

    rows = mod._i512_mission_api_objects(xml, mission)
    point = next((row for row in rows if str(row.get('uid') or row.get('event_uid')) == uid), None)
    assert point, rows
    assert abs(float(point.get('lat')) - 34.1234) < 0.000001, point
    assert abs(float(point.get('lon')) + 117.4321) < 0.000001, point
    assert str(point.get('callsign') or point.get('name')) == 'XML ONLY POINT', point
    assert point.get('cot_xml_projected_i598') is True, point

# Reproduce the full remote seed failure: discovery exposes only the UID, while
# the authoritative coordinates/name are present solely in /cot XML. The empty
# JSON adapter value must not prevent that XML object from entering the snapshot.
cfg = {'api_url': 'https://ots', 'base_url': 'https://ots', 'marti_url': 'https://ots:8443'}
sess = {'auth_mode': 'ots-user', 'username': 'alice', 'callsign': 'ALICE', 'tak_uid': 'alice-uid'}
cot_url = 'https://ots:8443/Marti/api/missions/PROTECTED-XML-MISSION/cot'
normalized = mod._i569_parsed_result({'ok': True, 'status': 200, 'json': {}, 'body': '<events>' + event + '</events>', 'error': ''})
acquired = {
    'mission_names': [mission],
    'mission_rows': [{
        'name': mission,
        'passwordProtected': True,
        'uids': [{'data': uid}],
        'contents': [],
    }],
    'responses': {cot_url: normalized},
    'timings': [],
    'summary': {'discovery_ok': True, 'mission_count': 1},
}

seeded = mod._i568_seed_remote_mission_data({}, cfg, acquired)
objects = list(seeded.get('objects') or [])
point = next((row for row in objects if str(row.get('uid') or row.get('event_uid')) == uid), None)
assert point, objects
assert abs(float(point.get('lat')) - 34.1234) < 0.000001, point
assert abs(float(point.get('lon')) + 117.4321) < 0.000001, point
assert str(point.get('callsign') or point.get('name')) == 'XML ONLY POINT', point

# Confirm the normal snapshot builder receives the same projected object.
mod._candidate_ots_pg_uris = lambda: ([], [])
mod._I591_CONTEXT.locked_missions = []
snapshot = mod._i570_build_from_acquired(cfg, sess, acquired, previous=None, phase='i598-cot-xml-regression')
objects = list(snapshot.get('objects') or [])
point = next((row for row in objects if str(row.get('uid') or row.get('event_uid')) == uid), None)
assert point, objects
assert abs(float(point.get('lat')) - 34.1234) < 0.000001, point
assert abs(float(point.get('lon')) + 117.4321) < 0.000001, point
assert str(point.get('callsign') or point.get('name')) == 'XML ONLY POINT', point

print('i598 Mission /cot XML response regression passed')
