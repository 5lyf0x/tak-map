#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(data_dir: Path):
    os.environ['TAK_DASHBOARD_DATA_DIR'] = str(data_dir)
    spec = importlib.util.spec_from_file_location('tak_map_i531_confirmed_test', ROOT / 'tak_dashboard.py')
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
            'cot_type': 'a-f-G-U-C',
        },
    }


def main() -> None:
    with tempfile.TemporaryDirectory(prefix='tak-map-i533-confirmed-') as td:
        m = load_module(Path(td))
        assert m.TAK_MAP_ITERATION == 'i537'

        built = m._i526_point_xml(point_feature(), 'TAKMAP-DATASYNC-TEST', 'TAKMAP-USER-darktek')

        # i532 preserves fail-closed exact ingest confirmation while reusing the persistent user socket.
        native_cfg = m.tak_map_config()['data_sync_native_point_publish']
        assert native_cfg['persistent_authenticated_user_eud'] is True
        assert native_cfg['success_requires_exact_cot_ingest_confirmation'] is True
        assert native_cfg['association_requires_confirmed_ingest'] is True
        assert native_cfg['shared_service_certificate_fallback'] is False

        # Full publish must not associate an unconfirmed CoT UID.
        m._I512_REQUEST_CONTEXT.identity = {
            'username': 'darktek',
            'callsign': 'darktek',
            'tak_uid': 'TAKMAP-USER-darktek',
        }
        m._i528_strict_creator = lambda: {
            'ok': True,
            'uid': 'TAKMAP-USER-darktek',
            'source': 'per-user-enrolled-marti-certificate-i529',
            'certificate_cn': 'darktek',
            'shared_service_fallback': False,
        }
        m._i526_create_mission = lambda *args, **kwargs: {
            'ok': True,
            'json': {'data': [{'token': 'mission-token'}]},
        }
        m._i526_send_native_mission_cot = lambda *args, **kwargs: {
            'ok': False,
            'status': 504,
            'error': 'exact UID not ingested',
            'ingest_confirmed': False,
        }
        association_calls = []
        original_associate_uid = m._i531_associate_uid
        m._i531_associate_uid = lambda *args, **kwargs: association_calls.append(args) or {'ok': True}
        m._write_send_diag = lambda *args, **kwargs: {}
        published = m.tak_map_publish_native_points_to_mission_i526(
            [point_feature()], 'TAKMAP-DATASYNC-TEST', 'opentakserver'
        )
        assert published['ok'] is False
        assert association_calls == []
        assert published['readback_confirmed'] is False

        m._i531_associate_uid = original_associate_uid

        # A duplicate existing UID association can be reused, but remains provisional
        # until the exact UID appears in Mission GET /cot.
        calls = []
        m._ots_mission_api_request = lambda *args, **kwargs: (
            calls.append((args, kwargs)) or {
                'ok': False,
                'status': 409,
                'error': 'already associated',
            }
        )
        assoc = m._i531_associate_uid(
            'TAKMAP-DATASYNC-TEST',
            'TAKMAP-USER-darktek',
            built['uid'],
            'mission-token',
        )
        assert assoc['ok'] is True
        assert assoc['already_associated'] is True
        assert assoc['provisional_until_exact_cot_readback'] is True

        # Read-back uses only GET /cot and requires the exact object UID.
        api_paths = []
        responses = [
            {'ok': True, 'status': 200, 'json': {'data': []}, 'body': ''},
            {'ok': True, 'status': 200, 'json': {'data': [{'uid': built['uid']}]}, 'body': ''},
        ]
        def readback_api(path, method='GET', **kwargs):
            api_paths.append((path, method))
            return responses.pop(0)
        m._ots_mission_api_request = readback_api
        m.time.sleep = lambda seconds: None
        readback = m._i528_confirm_readback(
            'TAKMAP-DATASYNC-TEST', built['uid'], 'TAKMAP-USER-darktek', 'opentakserver'
        )
        assert readback['ok'] is True
        assert readback['source'] == 'mission-api-get-cot-exact-uid'
        assert readback['mission_uid_row_alone_counts_as_readback'] is False
        assert all('/cot?' in path and method == 'GET' for path, method in api_paths)
        assert all('/contents?' not in path for path, _ in api_paths)

        # Orphan raw mission_uids no longer become client suppression authority.
        html = m.TAK_MAP_HTML
        assert 'takMapMissionPointReconcileI532' in html
        assert 'takMapMissionPointReconcileI528' not in html
        runtime = html.split('<script id="takMapMissionPointReconcileI532">', 1)[1].split('</script>', 1)[0]
        assert '(j&&j.objects||[])' in runtime
        assert 'mission_uids' not in runtime
        assert 'querySelectorAll(\'.leaflet-marker-icon\')' not in runtime
        assert 'sweep()' not in runtime

        cfg = m.tak_map_config()['data_sync_native_point_publish']
        assert cfg['success_requires_exact_cot_ingest_confirmation'] is True
        assert cfg['cot_socket_held_open_through_ingest_confirmation'] is True
        assert cfg['mission_readback_requires_exact_uid_from_get_cot'] is True
        assert cfg['mission_uid_row_alone_counts_as_readback'] is False
        assert cfg['orphan_mission_uid_suppresses_local_marker'] is False

    print('i532 confirmed CoT ingest, strict Mission read-back, and orphan suppression tests passed')


if __name__ == '__main__':
    main()
