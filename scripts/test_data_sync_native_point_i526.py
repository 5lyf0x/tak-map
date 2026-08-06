#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module():
    spec = importlib.util.spec_from_file_location('tak_map_i526_test', ROOT / 'tak_dashboard.py')
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def point_feature():
    return {
        'type': 'Feature',
        'canonical_id': 'local:local-ds-p02-stable',
        'geometry': {'type': 'Point', 'coordinates': [-118.1234567, 34.1234567, 125.5]},
        'properties': {
            'name': 'DS-P02',
            'callsign': 'DS-P02',
            'atak_cot_type': 'a-f-G-U-C-I',
            'remarks': 'Native point validation',
            'iconset_path': 'COT_MAPPING_2525C/a-f-G-U-C-I',
            'sidc': 'SFGPUCI----K---',
            'color': '-16776961',
            'altitude': 125.5,
        },
    }


def main():
    m = load_module()
    assert m.TAK_MAP_ITERATION == 'i537'
    cfg = m.tak_map_config()
    native = cfg['data_sync_native_point_publish']
    assert native['zip_for_points'] is False
    assert native['mission_uid_association'] is True

    m._I512_REQUEST_CONTEXT.identity = {'tak_uid':'ANDROID-test-owner','callsign':'test-owner','username':'test-owner'}
    m._i528_strict_creator = lambda: {'ok':True,'uid':'ANDROID-test-owner','source':'fixture-i529','identity':m._I512_REQUEST_CONTEXT.identity,'shared_service_fallback':False}
    feature = point_feature()
    built1 = m._i526_point_xml(feature, 'TAKMAP-DATASYNC-TEST', 'ANDROID-test-owner')
    built2 = m._i526_point_xml(feature, 'TAKMAP-DATASYNC-TEST', 'ANDROID-test-owner')
    assert built1['ok'] and built2['ok']
    assert built1['uid'] == built2['uid']
    assert built1['uid'].startswith('TAKMAP-MISSION-POINT-')
    xml = built1['xml']
    for token in (
        'DS-P02', 'TAKMAP-DATASYNC-TEST', 'relation="p-m"',
        'type="a-f-G-U-C-I-K"', 'native-mission-cot',
        'iconsetpath="COT_MAPPING_2525C/a-f-G-U-C-I"',
        'sidc="SFGPUCI----K---"', 'argb="-16776961"',
    ):
        assert token in xml, token
    assert 'mission-package-only' not in xml

    transport_calls = []
    def fake_per_user_transport(xml_text, event_uid=''):
        transport_calls.append({'xml': xml_text, 'event_uid': event_uid})
        return {
            'ok': True,
            'status': 202,
            'event_uid': event_uid,
            'identity_mode': 'per-user-enrolled-marti-certificate',
            'shared_service_fallback': False,
            'mission_cot_write_endpoint_used': False,
        }
    m._i532_send_per_user_cot = fake_per_user_transport
    endpoint = m._i526_send_native_mission_cot('TAKMAP-DATASYNC-TEST', 'ANDROID-test-owner', xml, 'ots.test')
    assert endpoint['ok'], endpoint
    assert len(transport_calls) == 1, transport_calls
    assert transport_calls[0]['event_uid'] == built1['uid']
    assert '<event ' in transport_calls[0]['xml']
    assert 'PK\x03\x04' not in transport_calls[0]['xml']
    assert endpoint['mission_cot_endpoint'] == 'GET-only; not used for publication'
    assert endpoint['shared_service_fallback'] is False

    calls = []

    def fake_create(mission, creator_uid, server_host=''):
        calls.append(('create', mission, creator_uid))
        return {'ok': True, 'json': {'data': [{'token': 'mission-token'}]}}

    def fake_native(mission, creator_uid, xml_text, server_host=''):
        calls.append(('native-cot', mission, creator_uid, xml_text))
        return {'ok': True, 'status': 200, 'path': '/Marti/api/missions/x/cot'}

    def fake_assoc(mission, creator_uid, uid, token='', server_host=''):
        calls.append(('associate', mission, creator_uid, uid, token))
        return {'ok': True, 'status': 200, 'event_uid': uid}

    m._i526_create_mission = fake_create
    m._i526_send_native_mission_cot = fake_native
    m._i531_associate_uid = fake_assoc
    m._i528_confirm_readback = lambda mission, uid, creator_uid, server_host='': {'ok':True,'source':'fixture'}
    m._write_send_diag = lambda *args, **kwargs: {}

    result = m.tak_map_publish_native_points_to_mission_i526(
        [feature], 'TAKMAP-DATASYNC-TEST', 'ots.test', 'ANDROID-test-owner'
    )
    assert result['ok'], result
    assert result['publish_mode'] == 'ots-confirmed-self-configured-persistent-per-user-cot-mission-uid-i534'
    assert result['native_mission_object'] is True
    assert result['zip_package_created'] is False
    assert result['zip_upload_skipped'] is True
    assert result['event_uids'] == [built1['uid']]
    assert [row[0] for row in calls] == ['create', 'native-cot', 'associate']
    assert not any('/sync/upload' in str(row) for row in calls)

    routed = []
    m._selected_local_data_features = lambda ids: [feature]
    m.tak_map_publish_native_points_to_mission_i526 = lambda features, mission_name='', server_host='', preferred_creator_uid='': (
        routed.append((features, mission_name, server_host, preferred_creator_uid)) or
        {'ok': True, 'publish_mode': 'ots-confirmed-self-configured-persistent-per-user-cot-mission-uid-i534', 'zip_package_created': False, 'readback_confirmed': False}
    )
    routed_result = m.tak_map_local_data_mission_publish(['local-ds-p02-stable'], 'points', 'TAKMAP-DATASYNC-TEST', 'ots.test')
    assert routed_result['ok'] and routed_result['publish_mode'] == 'ots-confirmed-self-configured-persistent-per-user-cot-mission-uid-i534'
    assert len(routed) == 1 and routed[0][0][0]['properties']['name'] == 'DS-P02'

    html = m.TAK_MAP_HTML
    assert not re.search(r'<(?:a|button)\b[^>]*>\s*Dashboard\s*</(?:a|button)>', html, re.I)
    assert 'takMapNativeDataSyncI526' in html
    assert "btn.dataset.i526Bound='1'" in html
    print('i532-preserved native Data Sync point and header cleanup tests passed')


if __name__ == '__main__':
    main()
