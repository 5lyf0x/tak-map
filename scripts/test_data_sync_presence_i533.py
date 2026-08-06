#!/usr/bin/env python3
import re
import runpy
import threading
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = (root / 'tak_dashboard.py').read_text(encoding='utf-8')
assert '# --- TAK Map i533 OTS-confirmed persistent per-user EUD presence ---' in source
assert source.rstrip().endswith("if __name__=='__main__':\n    main()")
assert source.count("if __name__=='__main__':") == 1
assert source.rfind('# --- TAK Map i533') < source.rfind("if __name__=='__main__':")
assert 'timezone-aware-utc' in source
assert "'wire_xml': bare_xml + '\\n'" in source
assert 'ots_eud_row_confirmation_required' in source
assert 'socket_reader_enabled' in source
assert 'initial_identity_group_side_effects_removed' in source
assert 'shared_service_certificate_fallback' in source

ns = runpy.run_path(str(root / 'tak_dashboard.py'), run_name='tak_map_i533_test')
g = ns['_i532_presence_xml'].__globals__

cfg = g['tak_map_config']()
assert cfg['tak_map_iteration'] == 'i537'
assert cfg['version'] == '1.3.0-i537'
ots = cfg['ots_integration']
assert ots['version'] == 'i534'
assert ots['persistent_per_user_eud_connection'] is True
assert ots['ots_eud_row_confirmation_required'] is True
assert ots['timezone_aware_utc_presence_timestamps'] is True
assert ots['socket_reader_enabled'] is True
assert ots['initial_identity_group_side_effects_removed'] is False
assert ots['initial_identity_valid_group_restored'] is True
assert ots['valid_cot_group_required'] is True
assert ots['shared_service_certificate_fallback'] is False
native = cfg['data_sync_native_point_publish']
assert native['version'] == 'i534'
assert native['publish_mode'] == 'ots-confirmed-self-configured-persistent-per-user-cot-mission-uid-i534'
assert native['ots_eud_confirmation_required'] is True
assert native['mission_object_uid_independent'] is True
assert native['local_data_removed_after_exact_readback'] is True
assert native['shared_service_certificate_fallback'] is False

sess = {
    'username': 'darktek',
    'auth_mode': 'ots-user',
    'tak_uid': 'TAKMAP-USER-TEST',
    'profile': {
        'username': 'darktek',
        'selected_callsign': 'DARKTEK-OPS',
        'callsign': 'OTS-DARKTEK',
        'tak_uid': 'TAKMAP-USER-TEST',
    },
}
presence = g['_i532_presence_xml'](sess, {'client_uid': 'TAKMAP-USER-TEST', 'certificate_cn': 'darktek'})
assert presence['ok'] is True
assert presence['callsign'] == 'DARKTEK-OPS'
for field in ('time', 'start', 'stale'):
    assert re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z', presence[field]), presence[field]
start = datetime.fromisoformat(presence['start'].replace('Z', '+00:00'))
stale = datetime.fromisoformat(presence['stale'].replace('Z', '+00:00'))
assert start.tzinfo == timezone.utc
assert 179 <= (stale - start).total_seconds() <= 181
assert presence['wire_xml'].startswith('<event ')
assert '<?xml' not in presence['wire_xml']
assert presence['wire_xml'].endswith('</event>\n')
root_xml = ET.fromstring(presence['wire_xml'].strip().encode())
assert root_xml.attrib['uid'] == 'TAKMAP-USER-TEST'
assert root_xml.attrib['start'] == presence['start']
detail = root_xml.find('detail')
assert detail.find('contact').attrib['callsign'] == 'DARKTEK-OPS'
assert detail.find('contact').attrib['endpoint'] == '*:-1:stcp'
assert detail.find('uid').attrib['Droid'] == 'DARKTEK-OPS'
takv = detail.find('takv')
assert takv.attrib == {
    'device': 'Web Browser',
    'platform': 'TAK Map',
    'os': 'Web',
    'version': '1.3.0-i537',
}
group = detail.find('__group')
assert group is not None
assert group.attrib == {'name': 'Cyan', 'role': 'Team Member'}
assert detail.find('takmap_user_presence').attrib['timestamps'] == 'timezone-aware-utc'

valid_row = {
    'uid': 'TAKMAP-USER-TEST',
    'callsign': 'DARKTEK-OPS',
    'device': 'Web Browser',
    'os': 'Web',
    'platform': 'TAK Map',
    'version': '1.3.0-i537',
    'last_status': 'Connected',
    'last_event_time': presence['start'],
    'age_seconds': 1.25,
    'confirmation_source': 'fixture',
}
verdict = g['_i533_eud_row_status'](valid_row, presence['uid'], presence['callsign'])
assert verdict['confirmed'] is True
assert verdict['callsign_ok'] and verdict['status_ok'] and verdict['current_ok']
for bad in (
    {**valid_row, 'callsign': ''},
    {**valid_row, 'last_status': 'Disconnected'},
    {**valid_row, 'age_seconds': 500},
    {**valid_row, 'uid': 'OTHER'},
):
    assert g['_i533_eud_row_status'](bad, presence['uid'], presence['callsign'])['confirmed'] is False

# Public status must not call an open socket "Connected" until OTS confirms
# the exact current EUD row.
base_state = {
    'tls': object(),
    'socket_connected': True,
    'connected': True,
    'ots_eud_confirmed': False,
    'state': 'awaiting-ots-confirmation',
    'client_uid': presence['uid'],
    'callsign': presence['callsign'],
}
unconfirmed = g['_i532_presence_public']('', base_state)
assert unconfirmed['socket_connected'] is True
assert unconfirmed['connected'] is False
assert unconfirmed['ots_eud_confirmed'] is False
confirmed_state = {
    **base_state,
    'ots_eud_confirmed': True,
    'ots_eud_row': valid_row,
    'ots_eud_verdict': verdict,
    'state': 'connected',
}
confirmed = g['_i532_presence_public']('', confirmed_state)
assert confirmed['connected'] is True
assert confirmed['ots_eud_confirmed'] is True
assert confirmed['ots_callsign'] == 'DARKTEK-OPS'
assert confirmed['ots_device'] == 'Web Browser'
assert confirmed['ots_platform'] == 'TAK Map'
assert confirmed['ots_version'] == '1.3.0-i537'
assert confirmed['timezone_aware_utc'] is True
assert confirmed['shared_service_fallback'] is False

# Exercise the connection handshake with a fake TLS transport and an
# authoritative OTS EUD-row confirmation.
class FakeRaw:
    def setsockopt(self, *args):
        pass
    def settimeout(self, value):
        self.timeout = value
    def close(self):
        pass

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

class FakeContext:
    def __init__(self, tls):
        self.tls = tls
    def load_cert_chain(self, *args, **kwargs):
        pass
    def wrap_socket(self, raw, server_hostname=None):
        return self.tls

fake_tls = FakeTLS()
g['_i532_session_credential'] = lambda s: {
    'ok': True,
    'certificate_cn': 'darktek',
    'certificate_path': '/fixture/cert.pem',
    'private_key_path': '/fixture/key.pem',
    'key_password': 'not-real',
    'ca_chain_path': '/fixture/ca.pem',
    'client_uid': 'TAKMAP-USER-TEST',
}
g['_i509_load_ots_config'] = lambda: {'fixture': True}
g['_i531_cot_endpoint'] = lambda cfg: ('opentakserver', 8089)
g['_i529_strict_tls_context'] = lambda cfg, ca: FakeContext(fake_tls)
g['socket'].create_connection = lambda addr, timeout=8: FakeRaw()
g['_I533_FIRST_IDENTITY_DELAY_SECONDS'] = 0.0
g['_i533_wait_for_ots_eud'] = lambda s, p, timeout=None: {
    'ok': True,
    'row': dict(valid_row),
    'verdict': dict(verdict),
}
state = {
    'key': 'takmap-user-test',
    'tokens': set(),
    'stop': threading.Event(),
    'wake': threading.Event(),
    'io_lock': threading.RLock(),
    'tls': None,
    'connected': False,
    'state': 'starting',
}
connected_presence = g['_i532_connect_locked'](state, sess)
assert connected_presence['uid'] == 'TAKMAP-USER-TEST'
assert state['connected'] is True
assert state['ots_eud_confirmed'] is True
assert state['socket_connected'] is True
assert len(fake_tls.payloads) == 1
assert fake_tls.payloads[0].startswith(b'<event ')
assert b'<contact callsign="DARKTEK-OPS"' in fake_tls.payloads[0]
assert b'<takv device="Web Browser" platform="TAK Map" os="Web" version="1.3.0-i537"' in fake_tls.payloads[0]
assert b'<__group name="Cyan" role="Team Member"' in fake_tls.payloads[0]
state['stop'].set()
with state['io_lock']:
    g['_i532_close_locked'](state, 'test-end')

assert 'takMapSelfServiceIdentityI534' in g['TAK_MAP_HTML']
assert 'Socket connected · awaiting OTS confirmation' in g['TAK_MAP_HTML']
assert 'Connected · OTS confirmed' in g['TAK_MAP_HTML']
assert 'takMapPerUserDataSyncIdentityI532' not in g['TAK_MAP_HTML']

print('i533 OTS-confirmed persistent EUD presence assertions passed')
