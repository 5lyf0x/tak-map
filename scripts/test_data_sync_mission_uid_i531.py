#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(data_dir: Path):
    os.environ['TAK_DASHBOARD_DATA_DIR'] = str(data_dir)
    spec = importlib.util.spec_from_file_location('tak_map_i531_test', ROOT / 'tak_dashboard.py')
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def point_feature():
    return {
        'type': 'Feature',
        'canonical_id': 'local:ds-p04',
        'geometry': {'type': 'Point', 'coordinates': [-118.4, 34.4, 200]},
        'properties': {
            'name': 'DS-P04',
            'callsign': 'DS-P04',
            'sidc': 'SFGPUCA--------',
            'mil2525_name': 'friendly-ground-unit-armor',
            'mil2525_label': 'ARMOR',
            'cot_type': 'a-f-G-U-C',
        },
    }


def main():
    with tempfile.TemporaryDirectory(prefix='tak-map-i533-test-') as td:
        m = load_module(Path(td))
        assert m.TAK_MAP_ITERATION == 'i537'

        # Certificate status is cached and invalidated by file signatures.
        calls = []
        m._I531_STATUS_CACHE.clear()
        m._i531_status_file_signature = lambda username: (('cert', 1, 2), ('key', 3, 4), ('ca', 5, 6), ('meta', 7, 8))
        m._i531_certificate_status_uncached = lambda username, uid='': (
            calls.append((username, uid)) or {
                'ok': True,
                'username': username,
                'client_uid': uid,
                'certificate_cn': username,
            }
        )
        first = m._i529_public_certificate_status('darktek', 'TAKMAP-USER-darktek')
        second = m._i529_public_certificate_status('darktek', 'TAKMAP-USER-darktek')
        assert first['ok'] and second['ok']
        assert first['version'] == 'i534'
        assert len(calls) == 1, calls

        # i532 retains the strict per-user transport and moves object sends onto the persistent user EUD socket.
        built = m._i526_point_xml(point_feature(), 'TAKMAP-DATASYNC-TEST', 'TAKMAP-USER-darktek')
        assert hasattr(m, '_i532_send_per_user_cot')
        assert m.tak_map_config()['data_sync_native_point_publish']['persistent_authenticated_user_eud'] is True
        assert m.tak_map_config()['data_sync_native_point_publish']['shared_service_certificate_fallback'] is False

        # Mission association uses only PUT /contents with the event UID.
        api_calls = []
        def fake_api(path, method='GET', body=None, headers=None, token='', public_host='', timeout=0):
            api_calls.append({'path': path, 'method': method, 'body': body, 'headers': headers or {}, 'token': token})
            return {'ok': True, 'status': 200, 'json': {'data': []}}
        m._ots_mission_api_request = fake_api
        assoc = m._i531_associate_uid('TAKMAP-DATASYNC-TEST', 'TAKMAP-USER-darktek', built['uid'], 'mission-token')
        assert assoc['ok'], assoc
        assert len(api_calls) == 1
        assert api_calls[0]['method'] == 'PUT'
        assert api_calls[0]['path'].startswith('/Marti/api/missions/TAKMAP-DATASYNC-TEST/contents?creatorUid=')
        assert '/cot?' not in api_calls[0]['path']
        assert json.loads(api_calls[0]['body']) == {'uids': [built['uid']]}

        # Full publication requires create/access, per-user CoT ingest, UID association, and read-back.
        sequence = []
        m._I512_REQUEST_CONTEXT.identity = {'username': 'darktek', 'callsign': 'darktek', 'tak_uid': 'TAKMAP-USER-darktek'}
        m._i528_strict_creator = lambda: {
            'ok': True,
            'uid': 'TAKMAP-USER-darktek',
            'source': 'per-user-enrolled-marti-certificate-i529',
            'certificate_cn': 'darktek',
            'shared_service_fallback': False,
        }
        m._i526_create_mission = lambda mission, creator_uid, server_host='': (
            sequence.append('create') or {'ok': True, 'json': {'data': [{'token': 'mission-token'}]}}
        )
        m._i526_send_native_mission_cot = lambda mission, creator_uid, xml, server_host='': (
            sequence.append('cot-ingest') or {'ok': True, 'status': 202, 'shared_service_fallback': False}
        )
        m._i531_associate_uid = lambda mission, creator_uid, uid, token='', server_host='': (
            sequence.append('associate-uid') or {'ok': True, 'status': 200, 'event_uid': uid}
        )
        m._i528_confirm_readback = lambda mission, uid, creator_uid, server_host='': (
            sequence.append('readback') or {'ok': True, 'source': 'fixture'}
        )
        m._write_send_diag = lambda *args, **kwargs: {}
        published = m.tak_map_publish_native_points_to_mission_i526(
            [point_feature()], 'TAKMAP-DATASYNC-TEST', 'opentakserver'
        )
        assert published['ok'], published
        assert sequence == ['create', 'cot-ingest', 'associate-uid', 'readback'], sequence
        assert published['publish_mode'] == 'ots-confirmed-self-configured-persistent-per-user-cot-mission-uid-i534'
        assert published['mission_cot_write_endpoint_disabled'] is True
        assert published['shared_service_fallback'] is False
        assert published['readback_confirmed'] is True
        assert published['zip_package_created'] is False

        # A failed UID association is a failed publish; Local Data must not be promoted.
        m._i531_associate_uid = lambda *args, **kwargs: {'ok': False, 'status': 403, 'error': 'fixture denied'}
        failed = m.tak_map_publish_native_points_to_mission_i526(
            [point_feature()], 'TAKMAP-DATASYNC-TEST', 'opentakserver'
        )
        assert failed['ok'] is False
        assert failed['readback_confirmed'] is False
        assert 'Mission UID association' in failed['error']

        html = m.TAK_MAP_HTML
        assert 'takMapSelfServiceIdentityI534' in html
        assert 'takMapPerUserDataSyncIdentityI529' not in html
        runtime = html.split('<script id="takMapSelfServiceIdentityI534">', 1)[1].split('</script>', 1)[0]
        assert "[500,1500,3500]" not in runtime
        assert runtime.count("load();") >= 1
        assert "new MutationObserver(ensure)" in runtime
        assert "takMapIdentityI534" in runtime

        install = (ROOT / 'install.sh').read_text(encoding='utf-8')
        assert 'Preserving existing TAK Map HTTPS certificate and key on upgrade.' in install
        assert 'No existing TAK Map HTTPS certificate/key found; generating them for this clean installation...' in install
        preserve_pos = install.index('if [[ -s "$SERVER_CRT" && -s "$SERVER_KEY" ]]')
        cert_setup_pos = install.index('$WRAPPER" cert-setup', preserve_pos)
        assert preserve_pos < cert_setup_pos
        assert "observer.observe(d.body,{childList:true,subtree:true})" in runtime

        installer = (ROOT / 'install.sh').read_text()
        assert 'Preserving existing TAK Map HTTPS certificate and key on upgrade.' in installer
        assert 'if [[ -s "$SERVER_CRT" && -s "$SERVER_KEY" ]]' in installer
        assert 'No existing TAK Map HTTPS certificate/key found; generating them for this clean installation...' in installer

        cfg = m.tak_map_config()
        assert cfg['tak_map_iteration'] == 'i537'
        assert cfg['data_sync_native_point_publish']['mission_uid_association_endpoint'].startswith('PUT ')
        assert cfg['data_sync_native_point_publish']['mission_cot_write_endpoint_used'] is False
        assert cfg['browser_https_certificate_upgrade_policy']['preserve_existing_certificate_and_key'] is True

    print('i532 persistent per-user SSL CoT and Mission UID association tests passed')


if __name__ == '__main__':
    main()
