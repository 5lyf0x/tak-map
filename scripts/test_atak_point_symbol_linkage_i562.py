#!/usr/bin/env python3
import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tak_dashboard_i562_symbol_test', ROOT / 'tak_dashboard.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

uid = 'ATAK-SYMBOL-LINKAGE-UID'
feature = {
    'type': 'Feature', 'uid': uid, 'cot_uid': uid, 'event_uid': uid,
    'geometry': {'type': 'Point', 'coordinates': [-117.0, 34.5]},
    'properties': {
        'uid': uid, 'cot_uid': uid, 'event_uid': uid,
        'preserve_event_uid_i555': True,
        'name': 'SYMBOL-LINKAGE', 'callsign': 'SYMBOL-LINKAGE',
        'mission_name': 'SYMBOL-LINKAGE-MISSION',
        'icon_mode': 'milstd2525c',
        'sidc': 'SFGPUCA--------',
        'cot_type': 'a-f-G-U-C-A',
        'iconsetpath': '', 'iconset_path': '',
    },
}

built = mod._i526_point_xml(feature, 'SYMBOL-LINKAGE-MISSION', 'USER-UID')
assert built['ok'] is True
root = ET.fromstring(built['xml'].split('\n', 1)[1])
assert root.attrib['type'] == 'a-f-G-U-C-A'
usericon = root.find('./detail/usericon')
assert usericon is not None
assert usericon.attrib['iconsetpath'] == 'COT_MAPPING_2525C/a-f/a-f-G-U-C-A'
assert built['iconset_path'] == usericon.attrib['iconsetpath']
meta = root.find('./detail/takmap_point')
assert meta is not None
assert meta.attrib['atakSymbolLinkage'] == 'event-type-plus-usericon'

payload = {
    'name': 'SYMBOL-LINKAGE', 'lat': 34.5, 'lon': -117.0,
    'symbol': {'kind': 'milstd2525c', 'sidc': 'SFGPUCA--------', 'cot_type': 'a-f-G-U-C-A'},
}
confirmed = {
    'uid': uid, 'cot_uid': uid, 'event_uid': uid,
    'mission_name': 'SYMBOL-LINKAGE-MISSION',
    'name': 'SYMBOL-LINKAGE', 'callsign': 'SYMBOL-LINKAGE',
    'lat': 34.5, 'lon': -117.0,
    'type': 'a-f-G-U-C-A', 'cot_type': 'a-f-G-U-C-A',
    'iconsetpath': 'COT_MAPPING_2525C/a-f/a-f-G-U-C-A',
}
matched, detail = mod._i562_point_update_match(confirmed, payload)
assert matched is True, detail

stale = dict(confirmed)
stale['iconsetpath'] = 'COT_MAPPING_2525C/a-f/a-f-G-U-C-D'
matched, detail = mod._i562_point_update_match(stale, payload)
assert matched is False
assert 'iconsetpath' in detail['mismatches']

wrong_type = dict(confirmed)
wrong_type['type'] = wrong_type['cot_type'] = 'a-f-G-U-C-D'
matched, detail = mod._i562_point_update_match(wrong_type, payload)
assert matched is False
assert 'cot_type' in detail['mismatches']

custom_feature = {
    'type': 'Feature', 'uid': uid + '-CUSTOM',
    'geometry': {'type': 'Point', 'coordinates': [-117.1, 34.6]},
    'properties': {
        'uid': uid + '-CUSTOM', 'preserve_event_uid_i555': True,
        'name': 'CUSTOM', 'icon_mode': 'custom-registry',
        'cot_type': 'a-f-G', 'iconsetpath': 'sample-set/group/icon.png',
    },
}
custom_built = mod._i526_point_xml(custom_feature, 'SYMBOL-LINKAGE-MISSION', 'USER-UID')
custom_root = ET.fromstring(custom_built['xml'].split('\n', 1)[1])
custom_usericon = custom_root.find('./detail/usericon')
assert custom_usericon is not None
assert custom_usericon.attrib['iconsetpath'] == 'sample-set/group/icon.png'

cfg = mod.tak_map_config()
policy = cfg['data_sync_point_symbol_update']
assert policy['atak_event_type_and_usericon_emitted'] is True
assert policy['semantic_readback_required'] is True
assert policy['uid_only_readback_is_not_success'] is True

# Exercise the final save wrapper: UID presence alone is not sufficient.
original_before = mod._i562_save_point_before
original_find = mod._i555_find_point
original_sleep = mod.time.sleep
try:
    base_reply = {'ok': True, 'version': 'i555', 'point': confirmed, 'publish': {'ok': True}, 'redraw_allowed': True}
    mod._i562_save_point_before = lambda value: (dict(base_reply), 200)
    mod.time.sleep = lambda seconds: None
    save_payload = dict(payload, uid=uid, mission_name='SYMBOL-LINKAGE-MISSION')

    mod._i555_find_point = lambda point_uid, mission, force=False: dict(confirmed)
    save_reply, save_status = mod._i555_save_point(save_payload)
    assert save_status == 200, save_reply
    assert save_reply['symbol_readback_confirmed'] is True
    assert save_reply['redraw_allowed'] is True

    mod._i555_find_point = lambda point_uid, mission, force=False: dict(stale)
    stale_reply, stale_status = mod._i555_save_point(save_payload)
    assert stale_status == 502, stale_reply
    assert stale_reply['symbol_readback_confirmed'] is False
    assert stale_reply['redraw_allowed'] is False
    assert 'previous icon' in stale_reply['error']
    assert 'iconsetpath' in stale_reply['readback']['mismatches']
finally:
    mod._i562_save_point_before = original_before
    mod._i555_find_point = original_find
    mod.time.sleep = original_sleep

print('i562 ATAK event-type + usericon publication and semantic symbol read-back checks passed')
