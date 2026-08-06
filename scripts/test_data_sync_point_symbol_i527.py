#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module():
    spec = importlib.util.spec_from_file_location('tak_map_i527_test', ROOT / 'tak_dashboard.py')
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def point_feature(name: str = 'DS-P03'):
    return {
        'type': 'Feature',
        'canonical_id': 'local:local-ds-p03-friendly-armor',
        'geometry': {'type': 'Point', 'coordinates': [-118.2234567, 34.2234567, 155.5]},
        'properties': {
            'name': name,
            'callsign': name,
            'remarks': 'Exact friendly armor symbol validation',
            'icon_mode': 'milstd2525c',
            'mil2525_name': 'friendly-ground-unit-armor',
            'mil2525_label': 'ARMOR',
            'sidc': 'SFGPUCA--------',
            # Deliberately include the old generic fallback. The selected SIDC must win.
            'cot_type': 'a-f-G-U-C',
            'color': '#2386ff',
        },
    }


def cot_type_to_sidc(cot_type: str) -> str:
    parts = [p for p in re.split(r'-+', cot_type.lower()) if p]
    assert len(parts) >= 3 and parts[0] == 'a'
    aff = {'f': 'F', 'h': 'H', 'n': 'N', 'u': 'U'}[parts[1]]
    dim = {'g': 'G', 'a': 'A', 's': 'S', 'u': 'U', 'p': 'P'}[parts[2]]
    rest = ''.join(parts[3:]).upper()
    return ('S' + aff + dim + 'P' + rest + '---------------')[:15]


def main():
    m = load_module()
    assert m.TAK_MAP_ITERATION == 'i537'
    cfg = m.tak_map_config()
    policy = cfg['data_sync_native_point_publish']
    assert policy['version'] == 'i534'
    assert policy['exact_mil2525_symbol_mapping'] is True
    assert policy['sidc_to_cot_type'] is True

    assert m._i527_cot_type_from_sidc('SFGPUCA--------') == 'a-f-G-U-C-A'
    assert m._i527_cot_type_from_sidc('SHGPEVATH------') == 'a-h-G-E-V-A-T-H'
    assert m._i527_cot_type_from_sidc('GFGPUCA--------') == ''
    assert cot_type_to_sidc('a-f-G-U-C-A') == 'SFGPUCA--------'

    feature = point_feature()
    assert m._i527_selected_sidc(feature) == 'SFGPUCA--------'
    assert m._i526_point_type(feature) == 'a-f-G-U-C-A'
    built = m._i526_point_xml(feature, 'TAKMAP-DATASYNC-TEST', 'ANDROID-darktek')
    assert built['ok'], built
    assert built['cot_type'] == 'a-f-G-U-C-A'
    assert built['sidc'] == 'SFGPUCA--------'
    assert built['mil2525_name'] == 'friendly-ground-unit-armor'
    assert built['symbol_mapping_source'] == 'selected-sidc'

    root = ET.fromstring(built['xml'])
    assert root.attrib['type'] == 'a-f-G-U-C-A'
    detail = root.find('detail')
    assert detail is not None
    meta = detail.find('takmap_point')
    assert meta is not None
    assert meta.attrib['version'] == 'i534'
    assert meta.attrib['symbolMode'] == 'milstd2525c-exact'
    assert meta.attrib['sidc'] == 'SFGPUCA--------'
    assert meta.attrib['mil2525Name'] == 'friendly-ground-unit-armor'
    assert meta.attrib['mil2525Label'] == 'ARMOR'

    # Verify exact icon exists and the browser-side reverse mapping has a matching file.
    icons = json.loads((ROOT / 'assets' / 'mil2525' / 'icons.json').read_text())
    exact = [x for x in icons if x.get('sidc') == 'SFGPUCA--------']
    assert exact and exact[0]['name'] == 'friendly-ground-unit-armor'
    assert (ROOT / 'assets' / 'mil2525' / 'svg' / 'friendly-ground-unit-armor.svg').is_file()
    js = (ROOT / 'takmap.js').read_text(errors='replace')
    assert 'function cotTypeToSidc' in js
    assert '"SFGPUCA--------":"friendly-ground-unit-armor.svg"' in js

    m._I512_REQUEST_CONTEXT.identity = {'tak_uid':'ANDROID-darktek','callsign':'darktek','username':'darktek'}
    m._i528_strict_creator = lambda: {'ok':True,'uid':'ANDROID-darktek','source':'fixture-i529','identity':m._I512_REQUEST_CONTEXT.identity,'shared_service_fallback':False}
    calls = []
    m._i526_create_mission = lambda mission, creator_uid, server_host='': {'ok': True, 'json': {'data': [{'token': 't'}]}}
    def send(mission, creator_uid, xml, server_host=''):
        calls.append(('cot', creator_uid, ET.fromstring(xml).attrib['type']))
        return {'ok': True, 'status': 200}
    def associate(mission, creator_uid, uid, token='', server_host=''):
        calls.append(('associate', creator_uid, uid))
        return {'ok': True, 'status': 200}
    m._i526_send_native_mission_cot = send
    m._i531_associate_uid = associate
    m._i528_confirm_readback = lambda mission, uid, creator_uid, server_host='': {'ok':True,'source':'fixture'}
    m._write_send_diag = lambda *args, **kwargs: {}
    result = m.tak_map_publish_native_points_to_mission_i526(
        [feature], 'TAKMAP-DATASYNC-TEST', 'ots.test', 'ANDROID-darktek'
    )
    assert result['ok'], result
    assert result['publish_mode'] == 'ots-confirmed-self-configured-persistent-per-user-cot-mission-uid-i534'
    assert result['zip_package_created'] is False
    assert result['symbol_mapping']['version'] == 'i527'
    assert calls[0] == ('cot', 'ANDROID-darktek', 'a-f-G-U-C-A')
    assert calls[1][0] == 'associate'

    print('i527 exact MIL-STD native point symbol tests passed')


if __name__ == '__main__':
    main()
