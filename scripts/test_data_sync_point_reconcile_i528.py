#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module():
    spec = importlib.util.spec_from_file_location('tak_map_i528_test', ROOT / 'tak_dashboard.py')
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def point_feature(name='DS-P04'):
    return {
        'type': 'Feature',
        'canonical_id': 'local:local-ds-p04-friendly-armor',
        'geometry': {'type': 'Point', 'coordinates': [-118.3, 34.3, 150]},
        'properties': {
            'name': name,
            'callsign': name,
            'sidc': 'SFGPUCA--------',
            'mil2525_name': 'friendly-ground-unit-armor',
            'mil2525_label': 'ARMOR',
            'cot_type': 'a-f-G-U-C',
            'remarks': 'i528 ownership/reconcile validation',
        },
    }


def main():
    m = load_module()
    assert m.TAK_MAP_ITERATION == 'i537'
    m._I512_REQUEST_CONTEXT.identity = {'tak_uid': 'TAKMAP-USER-darktek', 'callsign': 'darktek', 'username': 'darktek'}
    m._i528_strict_creator = lambda: {'ok':True,'uid':'TAKMAP-USER-darktek','source':'fixture-i529','identity':m._I512_REQUEST_CONTEXT.identity,'shared_service_fallback':False}

    feature = point_feature()
    built = m._i526_point_xml(feature, 'TAKMAP-DATASYNC-TEST', 'TAKMAP-USER-darktek')
    assert built['ok'], built
    root = ET.fromstring(built['xml'])
    assert root.attrib['uid'].startswith('TAKMAP-MISSION-POINT-')
    assert root.attrib['type'] == 'a-f-G-U-C-A'
    detail = root.find('detail')
    assert detail is not None
    creator = detail.find('creator')
    assert creator is not None
    assert creator.attrib['uid'] == 'TAKMAP-USER-darktek'
    assert creator.attrib['callsign'] == 'darktek'
    assert creator.attrib['username'] == 'darktek'
    dest = detail.find('dest')
    assert dest is not None and dest.attrib['mission'] == 'TAKMAP-DATASYNC-TEST'
    meta = detail.find('takmap_point')
    assert meta is not None
    assert meta.attrib['version'] == 'i534'
    assert meta.attrib['eudPresence'] == 'false'
    assert meta.attrib['canonicalSource'] == 'datasync'
    assert detail.find('takv') is None

    calls = []
    m._i526_create_mission = lambda mission, creator_uid, server_host='': {'ok': True, 'json': {'data': [{'token': 't'}]}}
    def send(mission, creator_uid, xml, server_host=''):
        calls.append(('native', creator_uid, xml))
        return {'ok': True, 'status': 200}
    m._i526_send_native_mission_cot = send
    m._i531_associate_uid = lambda mission, creator_uid, uid, token='', server_host='': {'ok': True, 'event_uid': uid}
    m._i528_confirm_readback = lambda mission, uid, creator_uid, server_host='': {'ok': True, 'source': 'fixture'}
    m._write_send_diag = lambda *args, **kwargs: {}

    result = m.tak_map_publish_native_points_to_mission_i526([feature], 'TAKMAP-DATASYNC-TEST', 'ots.test')
    assert result['ok'], result
    assert result['publish_mode'] == 'ots-confirmed-self-configured-persistent-per-user-cot-mission-uid-i534'
    assert result['creator_uid'] == 'TAKMAP-USER-darktek'
    assert result['readback_confirmed'] is True
    assert result['live_cot_fallback_disabled'] is True
    assert result['eud_creator_fallback_disabled'] is True
    assert result['zip_package_created'] is False
    assert len(calls) == 1 and calls[0][0] == 'native'

    deleted = []
    local_store = {'present': True}
    m._selected_local_data_features = lambda ids: [feature] if local_store['present'] else []
    def delete_local(ids):
        deleted.extend(ids)
        local_store['present'] = False
        return {'ok': True, 'deleted': True, 'deleted_count': 1, 'deleted_ids': ['local:local-ds-p04-friendly-armor'], 'imports': []}
    m.tak_map_local_data_delete = delete_local
    routed = m.tak_map_local_data_mission_publish(['local:local-ds-p04-friendly-armor'], 'points', 'TAKMAP-DATASYNC-TEST', 'ots.test')
    assert routed['ok'], routed
    assert routed['local_reconcile']['deleted'] is True
    assert routed['local_reconcile']['verified_absent'] is True
    assert routed['local_data_removed_after_readback'] is True
    assert 'local:local-ds-p04-friendly-armor' in deleted

    mission_uid = built['uid']
    # i537 no longer suppresses objects merely because their UID uses a TAK Map
    # prefix.  It learns exact mission-backed point UIDs for the current user.
    m._I537_REQUEST_CONTEXT.identity_key = 'darktek'
    m._i537_update_mission_uid_cache({
        'objects': [{'uid': mission_uid, 'geometry': {'type': 'Point'}}],
    }, 'darktek')
    rows = [
        {'uid': mission_uid, 'callsign': 'DS-P04'},
        {'uid': 'TAKMAP-USER-darktek', 'callsign': 'DS-P04'},
        {'uid': 'ANDROID-real', 'callsign': 'REAL-EUD'},
    ]
    kept, removed = m._i528_filter_live_rows(rows)
    assert kept == [rows[1], rows[2]], kept
    assert len(removed) == 1

    cfg = m.tak_map_config()['data_sync_native_point_publish']
    assert cfg['version'] == 'i534'
    assert cfg['live_cot_fallback_disabled'] is True
    assert cfg['eud_creator_fallback_disabled'] is True
    assert cfg['readback_required_before_local_reconcile'] is True
    assert 'takMapMissionPointReconcileI532' in m.TAK_MAP_HTML
    assert 'takMapMissionPointReconcileI528' not in m.TAK_MAP_HTML
    print('i532 mission-point ownership, verified Local Data reconciliation, and UID-only EUD isolation tests passed')


if __name__ == '__main__':
    main()
