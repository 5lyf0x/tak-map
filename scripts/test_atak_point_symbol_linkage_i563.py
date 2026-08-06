#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tak_dashboard_i563_symbol_test', ROOT / 'tak_dashboard.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader
spec.loader.exec_module(mod)

uid = 'ATAK-SYMBOL-LINKAGE-UID'
mission = 'SYMBOL-LINKAGE-MISSION'
feature = {
    'type': 'Feature', 'uid': uid, 'cot_uid': uid, 'event_uid': uid,
    'geometry': {'type': 'Point', 'coordinates': [-117.0, 34.5]},
    'properties': {
        'uid': uid, 'cot_uid': uid, 'event_uid': uid,
        'preserve_event_uid_i555': True,
        'name': 'SYMBOL-LINKAGE', 'callsign': 'SYMBOL-LINKAGE',
        'mission_name': mission,
        'icon_mode': 'milstd2525c',
        'sidc': 'SFGPUCA--------',
        'cot_type': 'a-f-G-U-C-A',
        'iconsetpath': '', 'iconset_path': '',
    },
}

built = mod._i526_point_xml(feature, mission, 'USER-UID')
assert built['ok'] is True
assert built['version'] == 'i563'
root = ET.fromstring(built['xml'].split('\n', 1)[1])
assert root.attrib['type'] == 'a-f-G-U-C-A'
usericon = root.find('./detail/usericon')
assert usericon is not None
assert usericon.attrib['iconsetpath'] == 'COT_MAPPING_2525C/a-f/a-f-G-U-C-A'
assert built['iconset_path'] == usericon.attrib['iconsetpath']
meta = root.find('./detail/takmap_point')
assert meta is not None
assert meta.attrib['atakSymbolLinkage'] == 'event-type-plus-usericon'
assert meta.attrib['boundedLiveStale'] == '10-minutes'

payload = {
    'uid': uid, 'mission_name': mission, 'expected_fingerprint': 'current-fingerprint',
    'name': 'SYMBOL-LINKAGE', 'lat': 34.5, 'lon': -117.0,
    'symbol': {'kind': 'milstd2525c', 'sidc': 'SFGPUCA--------', 'cot_type': 'a-f-G-U-C-A'},
}
confirmed = {
    'uid': uid, 'cot_uid': uid, 'event_uid': uid,
    'mission_name': mission,
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
custom_built = mod._i526_point_xml(custom_feature, mission, 'USER-UID')
custom_root = ET.fromstring(custom_built['xml'].split('\n', 1)[1])
custom_usericon = custom_root.find('./detail/usericon')
assert custom_usericon is not None
assert custom_usericon.attrib['iconsetpath'] == 'sample-set/group/icon.png'

cfg = mod.tak_map_config()
policy = cfg['data_sync_point_symbol_update']
assert policy['atak_event_type_and_usericon_emitted'] is True
assert policy['semantic_readback_required'] is True
assert policy['uid_only_readback_is_not_success'] is True
assert policy['atak_refresh_sequence'] == 't-x-d-d then updated event'

# Exercise the final i563 save wrapper while replacing only the underlying i555
# publisher. UID presence alone remains insufficient; the exact symbol and
# fields must match after Mission read-back.
with tempfile.TemporaryDirectory(prefix='tak-map-i563-symbol-fence-') as td:
    mod._I563_FENCE_FILE = Path(td) / 'fences.json'
    original_before = mod._i562_save_point_before
    original_find = mod._i555_find_point
    original_sleep = mod.time.sleep
    try:
        base_reply = {'ok': True, 'version': 'i555', 'point': confirmed, 'publish': {'ok': True}, 'redraw_allowed': True}
        mod._i562_save_point_before = lambda value: (dict(base_reply), 200)
        mod.time.sleep = lambda seconds: None

        mod._i555_find_point = lambda point_uid, point_mission, force=False: dict(confirmed)
        save_reply, save_status = mod._i555_save_point(dict(payload))
        assert save_status == 200, save_reply
        assert save_reply['version'] == 'i563'
        assert save_reply['symbol_readback_confirmed'] is True
        assert save_reply['redraw_allowed'] is True

        mod._i555_find_point = lambda point_uid, point_mission, force=False: dict(stale)
        stale_reply, stale_status = mod._i555_save_point(dict(payload))
        assert stale_status == 502, stale_reply
        assert stale_reply['version'] == 'i563'
        assert stale_reply['symbol_readback_confirmed'] is False
        assert stale_reply['redraw_allowed'] is False
        assert 'previous icon' in stale_reply['error']
        assert 'iconsetpath' in stale_reply['readback']['mismatches']
    finally:
        mod._i562_save_point_before = original_before
        mod._i555_find_point = original_find
        mod.time.sleep = original_sleep

print('i563 ATAK event-type + usericon publication, bounded stale, refresh policy, and semantic read-back checks passed')
