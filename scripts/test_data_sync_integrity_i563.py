#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tak_dashboard_i563_integrity_test', ROOT / 'tak_dashboard.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader
spec.loader.exec_module(mod)

uid = 'I563-DELETE-INTEGRITY-UID'
mission = 'I563-INTEGRITY-MISSION'

with tempfile.TemporaryDirectory(prefix='tak-map-i563-fences-') as td:
    mod._I563_FENCE_FILE = Path(td) / 'fences.json'
    try:
        mod._I512_REQUEST_CONTEXT.identity = {'username': 'integrity-user'}
    except Exception:
        pass

    # A CoT delete is control state, never a display object. It creates a
    # persistent fence before later live/EUD copies are considered.
    payload = {
        'objects': [{
            'uid': uid, 'cot_uid': uid, 'event_uid': uid,
            'mission_name': mission, 'type': 't-x-d-d',
            'time': '2026-07-27T20:00:00Z', 'lat': 34.2, 'lon': -118.4,
        }],
        'markers': [{
            'uid': uid, 'cot_uid': uid, 'event_uid': uid,
            'mission_name': mission, 'type': 'a-f-G',
            'name': 'Generic stale marker', 'lat': 34.2, 'lon': -118.4,
        }],
        'euds': [{
            'uid': uid, 'mission_name': mission, 'type': 'a-f-G',
            'callsign': 'Generic stale EUD', 'lat': 34.2, 'lon': -118.4,
        }],
    }
    filtered = mod._i563_filter_payload(payload, True)
    assert filtered['objects'] == [], filtered
    assert filtered['markers'] == [], filtered
    assert filtered['euds'] == [], filtered
    assert mod._i563_fenced(uid, mission) is True
    persisted = json.loads(mod._I563_FENCE_FILE.read_text())
    assert len(persisted['fences']) == 1
    fence = next(iter(persisted['fences'].values()))
    assert fence['uid'] == uid and fence['mission'] == mission
    assert fence['reason'] == 'cot-delete-event'

    # Reloading from disk retains suppression; a non-delete event alone cannot
    # release the fence.
    later = mod._i563_filter_payload({
        'objects': [],
        'markers': [{'uid': uid, 'mission_name': mission, 'type': 'a-f-G-U-C-A', 'lat': 34.3, 'lon': -118.5}],
    }, False)
    assert later['markers'] == []
    assert mod._i563_load_fences()['fences']

    # Fences are scoped to the authenticated identity; one user's deletion
    # cannot hide another user's same-UID object.
    try:
        mod._I512_REQUEST_CONTEXT.identity = {'username': 'other-user'}
    except Exception:
        pass
    assert mod._i563_fenced(uid, mission) is False
    other_view = mod._i563_filter_payload({'markers':[{'uid':uid,'mission_name':mission,'type':'a-f-G','lat':34.2,'lon':-118.4}]}, False)
    assert len(other_view['markers']) == 1
    try:
        mod._I512_REQUEST_CONTEXT.identity = {'username': 'integrity-user'}
    except Exception:
        pass
    assert mod._i563_fenced(uid, mission) is True

    # A genuinely newer non-delete event plus an explicit current Mission UID
    # association is the only inbound recreation that releases the fence.
    recreated_time = '2026-07-28T20:00:00Z'
    recreated_view = mod._i563_filter_payload({
        'mission_uids':[{'event_uid':uid,'mission_name':mission}],
        'objects':[{'uid':uid,'mission_name':mission,'type':'a-f-G-U-C-A','time':recreated_time,'lat':34.4,'lon':-118.6}],
    }, True)
    assert len(recreated_view['objects']) == 1, recreated_view
    assert mod._i563_fenced(uid, mission) is False

    # TAK Map's own symbol-refresh tombstone is never promoted into a user
    # deletion fence, even if it is observed after the publish call returns.
    refresh_xml = mod._i563_delete_xml(uid, 'Refresh', 34.4, -118.6, 'symbol-refresh')
    refresh_view = mod._i563_filter_payload({'objects':[{'uid':uid,'mission_name':mission,'type':'t-x-d-d','raw_xml':refresh_xml,'time':'2026-07-28T20:01:00Z'}]}, True)
    assert refresh_view['objects'] == []
    assert mod._i563_fenced(uid, mission) is False

    # Restore a real user-delete fence for the deletion workflow checks below.
    mod._i563_add_fence(uid, mission, 'cot-delete-event', '2026-07-28T20:02:00Z')

    # Terminal deletion uses the same UID, a deletion CoT type, and a short
    # stale interval rather than creating a visible generic point.
    terminal_xml = mod._i563_delete_xml(uid, 'Deleted Point', 34.2, -118.4, 'mission-delete')
    terminal = ET.fromstring(terminal_xml.split('\n', 1)[1])
    assert terminal.attrib['uid'] == uid
    assert terminal.attrib['type'] == 't-x-d-d'
    start = datetime.fromisoformat(terminal.attrib['time'].replace('Z', '+00:00'))
    stale = datetime.fromisoformat(terminal.attrib['stale'].replace('Z', '+00:00'))
    assert 8 <= (stale - start).total_seconds() <= 15
    assert terminal.find('./detail/usericon') is None

    # Normal point publication has bounded live lifetime and keeps matching
    # event type + ATAK MIL usericon linkage.
    feature = {
        'type': 'Feature', 'uid': uid, 'cot_uid': uid, 'event_uid': uid,
        'geometry': {'type': 'Point', 'coordinates': [-118.4, 34.2]},
        'properties': {
            'uid': uid, 'cot_uid': uid, 'event_uid': uid,
            'preserve_event_uid_i555': True,
            'name': 'Integrity Point', 'mission_name': mission,
            'icon_mode': 'milstd2525c', 'sidc': 'SFGPUCA--------',
            'cot_type': 'a-f-G-U-C-A', 'iconsetpath': '',
        },
    }
    built = mod._i526_point_xml(feature, mission, 'USER-UID')
    assert built['ok'] and built['version'] == 'i563', built
    event = ET.fromstring(built['xml'].split('\n', 1)[1])
    event_start = datetime.fromisoformat(event.attrib['time'].replace('Z', '+00:00'))
    event_stale = datetime.fromisoformat(event.attrib['stale'].replace('Z', '+00:00'))
    assert 595 <= (event_stale - event_start).total_seconds() <= 605
    assert event.attrib['type'] == 'a-f-G-U-C-A'
    assert event.find('./detail/usericon').attrib['iconsetpath'] == 'COT_MAPPING_2525C/a-f/a-f-G-U-C-A'
    meta = event.find('./detail/takmap_point')
    assert meta is not None and meta.attrib['boundedLiveStale'] == '10-minutes'

    # Existing edits retire the previous live symbol and publish the replacement
    # without issuing another Mission association PUT.
    old_publish = mod._i563_publish_before
    old_raw_active = mod._i563_raw_active
    old_fenced = mod._i563_fenced
    old_terminal = mod._i563_send_terminal
    old_sleep = mod.time.sleep
    calls = []
    try:
        mod._i563_raw_active = lambda point_uid, point_mission='': True
        mod._i563_fenced = lambda point_uid, point_mission='': False
        mod._i563_send_terminal = lambda *args, **kwargs: calls.append(('terminal', args, kwargs)) or {'ok': True, 'terminal_type': 't-x-d-d'}
        mod.time.sleep = lambda seconds: calls.append(('sleep', seconds))
        def fake_publish(points, mission_name='', server_host='', creator_uid=''):
            calls.append(('publish', bool(getattr(mod._I563_PUBLISH_CONTEXT, 'skip_association', False))))
            association = mod._i531_associate_uid(mission_name, creator_uid, uid, '', server_host)
            calls.append(('association', association))
            return {'ok': True, 'version': 'base', 'readback_confirmed': True, 'redraw_allowed': True}
        mod._i563_publish_before = fake_publish
        mod._I563_PUBLISH_CONTEXT.payload = {
            'uid': uid, 'mission_name': mission, 'expected_fingerprint': 'fingerprint',
            'name': 'Integrity Point', 'lat': 34.2, 'lon': -118.4,
        }
        result = mod.tak_map_publish_native_points_to_mission_i526([feature], mission, 'ots.example.test', 'USER-UID')
        assert result['ok'] is True, result
        assert result['existing_edit_reassociated'] is False
        assert result['atak_symbol_refresh_sequence'] == 't-x-d-d-then-new-event'
        assert [row[0] for row in calls].count('terminal') == 1
        assert ('publish', True) in calls
        association = next(row[1] for row in calls if row[0] == 'association')
        assert association['skipped'] is True
        assert association['reason'] == 'existing-point-edit-does-not-reassociate'
    finally:
        mod._i563_publish_before = old_publish
        mod._i563_raw_active = old_raw_active
        mod._i563_fenced = old_fenced
        mod._i563_send_terminal = old_terminal
        mod.time.sleep = old_sleep
        mod._I563_PUBLISH_CONTEXT.payload = None
        mod._I563_PUBLISH_CONTEXT.skip_association = False

    # A TAK Map delete adds a fence first, removes Mission membership, emits a
    # terminal same-UID delete, and confirms absence before success.
    mod._i563_remove_fence(uid, mission)
    old_delete = mod._i563_delete_before
    old_terminal = mod._i563_send_terminal
    old_raw_active = mod._i563_raw_active
    try:
        mod._i563_delete_before = lambda obj, server_host='': {'status': 'deleted', 'target': 'uid'}
        mod._i563_send_terminal = lambda *args, **kwargs: {'ok': True, 'terminal_type': 't-x-d-d', 'reason': 'mission-delete'}
        mod._i563_raw_active = lambda point_uid, point_mission='': False
        obj = {
            'uid': uid, 'cot_uid': uid, 'event_uid': uid, 'mission_name': mission,
            'mission_delete_target': 'uid', 'mission_delete_value': uid,
            'name': 'Integrity Point', 'lat': 34.2, 'lon': -118.4,
        }
        deleted = mod._tak_data_sync_delete_record(obj, 'ots.example.test')
        assert deleted['status'] == 'deleted', deleted
        assert deleted['mission_absence_confirmed'] is True
        assert deleted['terminal_cot']['terminal_type'] == 't-x-d-d'
        assert deleted['stale_marker_suppressed'] is True
        assert deleted['resurrection_blocked'] is True
        assert mod._i563_fenced(uid, mission) is True
    finally:
        mod._i563_delete_before = old_delete
        mod._i563_send_terminal = old_terminal
        mod._i563_raw_active = old_raw_active

    # A stale editor cannot recreate or re-associate the fenced UID.
    blocked, status = mod._i555_save_point({
        'uid': uid, 'mission_name': mission, 'expected_fingerprint': 'old',
        'name': 'Must Not Return', 'lat': 34.2, 'lon': -118.4,
        'symbol': {'kind': 'milstd2525c', 'cot_type': 'a-f-G-U-C-A'},
    })
    assert status == 410 and blocked['deleted'] is True, blocked
    assert blocked['redraw_allowed'] is False

    # Only an explicit successful new publication can clear the fence.
    old_publish = mod._i563_publish_before
    try:
        mod._i563_publish_before = lambda *args, **kwargs: {'ok': True, 'readback_confirmed': True, 'redraw_allowed': True}
        mod._I563_PUBLISH_CONTEXT.payload = {'mission_name': mission, 'name': 'Explicit Recreation'}
        recreated = mod.tak_map_publish_native_points_to_mission_i526([feature], mission, '', 'USER-UID')
        assert recreated['ok'] is True
        assert mod._i563_fenced(uid, mission) is False
    finally:
        mod._i563_publish_before = old_publish
        mod._I563_PUBLISH_CONTEXT.payload = None

cfg = mod.tak_map_config()
policy = cfg['data_sync_deletion_integrity']
assert policy['persistent_fences'] is True
assert policy['delete_event_rendering'] is False
assert policy['terminal_same_uid_delete'] is True
assert policy['existing_edits_reassociate'] is False
assert policy['bounded_live_stale_seconds'] == 600
assert policy['per_uid_publication_lock'] is True

print('i563 persistent deletion fence, terminal delete, no-reassociation, bounded stale, and resurrection blocking checks passed')
