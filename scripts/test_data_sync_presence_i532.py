#!/usr/bin/env python3
import runpy
import time
import xml.etree.ElementTree as ET
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = (root / 'tak_dashboard.py').read_text(encoding='utf-8')
assert '# --- TAK Map i532 persistent per-user EUD session + confirmed Local Data reconciliation ---' in source
assert source.rstrip().endswith("if __name__=='__main__':\n    main()")
assert source.rfind('# --- TAK Map i532') < source.rfind("if __name__=='__main__':")
assert "_I532_HEARTBEAT_SECONDS = 30.0" in source
assert "'endpoint': '*:-1:stcp'" in source
assert "ET.SubElement(detail, 'uid', {'Droid': callsign})" in source
assert "persistent-per-user-cot-mission-uid-i532" in source
assert "stable_source_ids" in source and "verified_absent" in source
assert "shared_service_fallback': False" in source
assert "_i532_stop_all_presence('ots-disconnect')" in source

ns = runpy.run_path(str(root / 'tak_dashboard.py'), run_name='tak_map_i532_test')
g = ns['_i532_ensure_presence'].__globals__
cfg = g['tak_map_config']()
assert cfg['tak_map_iteration'] == 'i537'
assert cfg['version'] == '1.3.0-i537'
assert cfg['ots_integration']['version'] == 'i534'
assert cfg['ots_integration']['persistent_per_user_eud_connection'] is True
assert cfg['ots_integration']['presence_heartbeat_seconds'] == 30
assert cfg['ots_integration']['shared_service_certificate_fallback'] is False
native = cfg['data_sync_native_point_publish']
assert native['version'] == 'i534'
assert native['publish_mode'] == 'ots-confirmed-self-configured-persistent-per-user-cot-mission-uid-i534'
assert native['persistent_authenticated_user_eud'] is True
assert native['mission_object_uid_independent'] is True
assert native['stable_source_id_reconciliation'] is True

sess = {
    'username': 'darktek',
    'auth_mode': 'ots-user',
    'tak_uid': 'TAKMAP-USER-TEST',
    'profile': {
        'username': 'darktek',
        'selected_callsign': 'DARKTEK-OPS',
        'callsign': 'OTS-DARKTEK',
        'suggested_callsign': 'OTS-DARKTEK',
        'tak_uid': 'TAKMAP-USER-TEST',
    },
}
presence = g['_i532_presence_xml'](sess, {'client_uid': 'TAKMAP-USER-TEST', 'certificate_cn': 'darktek'})
assert presence['ok'] and presence['callsign'] == 'DARKTEK-OPS'
root_xml = ET.fromstring(presence['xml'].encode())
assert root_xml.attrib['uid'] == 'TAKMAP-USER-TEST'
detail = root_xml.find('detail')
contact = detail.find('contact')
assert contact.attrib['callsign'] == 'DARKTEK-OPS'
assert contact.attrib['endpoint'] == '*:-1:stcp'
assert detail.find('uid').attrib['Droid'] == 'DARKTEK-OPS'
assert detail.find('takmap_user_presence').attrib['missionObject'] == 'false'

# One persistent connection is shared by multiple browser sessions for the same user UID.
g['_i532_presence_worker'] = lambda key, state: state['stop'].wait(2.0)
now = time.time()
for token in ('tok-a', 'tok-b'):
    g['TAK_MAP_SESSIONS'][token] = {
        **sess,
        'created': now,
        'expires': now + 300,
        'profile': dict(sess['profile']),
    }
first = g['_i532_ensure_presence']('tok-a', g['TAK_MAP_SESSIONS']['tok-a'])
second = g['_i532_ensure_presence']('tok-b', g['TAK_MAP_SESSIONS']['tok-b'])
key_a = g['_I532_TOKEN_KEYS']['tok-a']
key_b = g['_I532_TOKEN_KEYS']['tok-b']
assert key_a == key_b
state = g['_I532_PRESENCE'][key_a]
assert state['tokens'] == {'tok-a', 'tok-b'}
g['_i532_remove_session_token']('tok-a', 'test-logout')
assert not state['stop'].is_set()
g['TAK_MAP_SESSIONS'].pop('tok-a', None)
g['_i532_remove_session_token']('tok-b', 'test-logout')
assert state['stop'].is_set()
g['TAK_MAP_SESSIONS'].pop('tok-b', None)
g['_i532_stop_all_presence']('test-end')


# Mission objects reuse the already-connected per-user socket and keep their UID separate.
class FakeTLS:
    def __init__(self):
        self.payloads = []
        self.closed = False
    def sendall(self, payload):
        assert not self.closed
        self.payloads.append(payload)
    def shutdown(self, how):
        self.closed = True
    def close(self):
        self.closed = True

send_token = 'tok-send'
send_now = time.time()
g['TAK_MAP_SESSIONS'][send_token] = {
    **sess,
    'created': send_now,
    'expires': send_now + 300,
    'profile': dict(sess['profile']),
}
send_key = g['_i532_presence_key'](g['TAK_MAP_SESSIONS'][send_token])
fake_tls = FakeTLS()
send_state = {
    'key': send_key,
    'tokens': {send_token},
    'stop': __import__('threading').Event(),
    'wake': __import__('threading').Event(),
    'io_lock': __import__('threading').RLock(),
    'tls': fake_tls,
    'connected': True,
    'socket_connected': True,
    'ots_eud_confirmed': True,
    'ots_confirmation_state': 'confirmed',
    'state': 'connected',
    'host': 'opentakserver',
    'port': 8089,
    'certificate_cn': 'darktek',
    'client_uid': 'TAKMAP-USER-TEST',
    'callsign': 'DARKTEK-OPS',
    'username': 'darktek',
    'team_color': 'Cyan',
    'team_role': 'Team Member',
    'tak_identity_configured': False,
    'last_heartbeat_monotonic': time.monotonic(),
    'last_error': '',
}
g['_I532_PRESENCE'][send_key] = send_state
g['_I532_TOKEN_KEYS'][send_token] = send_key
g['_I529_REQUEST_CONTEXT'].session_token = send_token
g['_i531_wait_for_cot_ingest'] = lambda uid, timeout_seconds=15.0: {
    'ok': True,
    'event_uid': uid,
    'source': 'fixture-exact-uid',
}
point_uid = 'TAKMAP-MISSION-POINT-TEST'
point_xml = '<?xml version="1.0" encoding="UTF-8"?><event version="2.0" uid="'+point_uid+'" type="a-f-G-U-C"><point lat="34" lon="-117" hae="0" ce="5" le="5"/><detail><contact callsign="DS-P04"/></detail></event>'
sent = g['_i532_send_per_user_cot'](point_xml, point_uid)
assert sent['ok'] is True, sent
assert sent['persistent_user_eud'] is True
assert sent['persistent_connection_reused'] is True
assert sent['connection_identity_uid'] == 'TAKMAP-USER-TEST'
assert sent['mission_object_uid'] == point_uid
assert sent['point_uid_used_as_eud_identity'] is False
assert sent['shared_service_fallback'] is False
assert len(fake_tls.payloads) == 1
assert point_uid.encode() in fake_tls.payloads[0]
g['_i532_remove_session_token'](send_token, 'test-send-end')
g['TAK_MAP_SESSIONS'].pop(send_token, None)

# Confirmed read-back removes the exact stable Local Data source and verifies absence.
# runpy returns a namespace copy; patch the callable's actual globals for behavioral tests.
publish_fn = g['tak_map_local_data_mission_publish']
feature = {
    'object_id': 'local-1234567890abcdef',
    'source_id': 'local-1234567890abcdef',
    'local_id': 'local-1234567890abcdef',
    '_local_id': 'local-1234567890abcdef',
    'canonical_id': 'local:local-1234567890abcdef',
    'kind': 'point',
    'geometry': {'type': 'Point', 'coordinates': [-117.1, 34.1]},
}
store = {'present': True}
delete_calls = []
g['_selected_local_data_features'] = lambda ids: [dict(feature)] if store['present'] else []
g['_i526_point_features'] = lambda features, kind='': list(features)
g['_i528_identity'] = lambda: {'tak_uid': 'TAKMAP-USER-TEST'}
g['tak_map_publish_native_points_to_mission_i526'] = lambda *args, **kwargs: {
    'ok': True,
    'readback_confirmed': True,
    'message': 'Published point to Data Sync Mission: TEST.',
}
def delete(ids):
    delete_calls.append(list(ids))
    assert 'local-1234567890abcdef' in ids
    store['present'] = False
    return {
        'ok': True,
        'deleted': True,
        'deleted_count': 1,
        'deleted_ids': ['local:local-1234567890abcdef'],
        'imports': [],
    }
g['tak_map_local_data_delete'] = delete
result = publish_fn(
    ['local:local-1234567890abcdef'], 'points', 'TEST', 'localhost'
)
assert result['ok'] is True
assert result['local_reconcile']['attempted'] is True
assert result['local_reconcile']['deleted'] is True
assert result['local_reconcile']['verified_absent'] is True
assert result['local_data_removed_after_readback'] is True
assert delete_calls

print('i532 persistent per-user EUD and Local Data reconciliation assertions passed')
