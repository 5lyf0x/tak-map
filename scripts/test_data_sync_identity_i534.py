#!/usr/bin/env python3
import json
import runpy
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path

root = Path(__file__).resolve().parents[1]
source = (root / 'tak_dashboard.py').read_text(encoding='utf-8')
assert '# --- TAK Map i534 self-service TAK identity + valid OTS EUD team registration ---' in source
assert source.rstrip().endswith("if __name__=='__main__':\n    main()")
assert source.count("if __name__=='__main__':") == 1
assert source.rfind('# --- TAK Map i534') < source.rfind("if __name__=='__main__':")
assert "'valid_cot_group_required': True" in source
assert "'administrator_identity_override': False" in source
assert "ET.Element('__group'" in source

ns = runpy.run_path(str(root / 'tak_dashboard.py'), run_name='tak_map_i534_test')
g = ns['_i532_presence_xml'].__globals__

cfg = g['tak_map_config']()
assert cfg['tak_map_iteration'] == 'i537'
assert cfg['version'] == '1.3.0-i537'
ots = cfg['ots_integration']
assert ots['version'] == 'i534'
assert ots['valid_cot_group_required'] is True
assert ots['self_service_tak_identity'] is True
assert ots['per_user_callsign_team_color_role'] is True
assert ots['administrator_identity_override'] is False
assert 'Cyan' in ots['team_colors'] and 'Team Member' in ots['team_roles']
native = cfg['data_sync_native_point_publish']
assert native['version'] == 'i534'
assert native['valid_user_group_identity'] is True
assert native['mission_object_uid_independent'] is True
assert native['local_data_removed_after_exact_readback'] is True
assert native['shared_service_certificate_fallback'] is False

sess = {
    'username': 'darktek',
    'auth_mode': 'ots-user',
    'tak_uid': 'TAKMAP-USER-TEST',
    'profile': {
        'username': 'darktek',
        'identity_key': 'fixture-darktek',
        'selected_callsign': 'DARKTEK-OPS',
        'suggested_callsign': 'darktek',
        'callsign': 'DARKTEK-OPS',
        'selected_team_color': 'Dark Blue',
        'selected_team_role': 'Team Lead',
        'team_color': 'Dark Blue',
        'team': 'Dark Blue',
        'team_role': 'Team Lead',
        'tak_identity_configured': True,
        'tak_uid': 'TAKMAP-USER-TEST',
    },
}
presence = g['_i532_presence_xml'](sess, {'client_uid': 'TAKMAP-USER-TEST', 'certificate_cn': 'darktek'})
assert presence['ok'] is True
assert presence['version'] == 'i537'
assert presence['callsign'] == 'DARKTEK-OPS'
assert presence['team_color'] == 'Dark Blue'
assert presence['team_role'] == 'Team Lead'
root_xml = ET.fromstring(presence['wire_xml'].strip().encode())
detail = root_xml.find('detail')
assert detail.find('contact').attrib['callsign'] == 'DARKTEK-OPS'
assert detail.find('__group').attrib == {'name': 'Dark Blue', 'role': 'Team Lead'}
assert detail.find('takv').attrib == {
    'device': 'Web Browser',
    'platform': 'TAK Map',
    'os': 'Web',
    'version': '1.3.0-i537',
}
meta = detail.find('takmap_user_presence').attrib
assert meta['version'] == 'i537'
assert meta['teamColor'] == 'Dark Blue'
assert meta['teamRole'] == 'Team Lead'
assert meta['selfConfigured'] == 'true'
assert meta['timestamps'] == 'timezone-aware-utc'
assert meta['serviceCredentialFallback'] == 'false'

# Missing user configuration uses provider/default values but still emits the
# valid OTS-required group element.
fallback = {
    'username': 'alice',
    'auth_mode': 'ots-user',
    'tak_uid': 'TAKMAP-USER-ALICE',
    'profile': {
        'username': 'alice',
        'suggested_callsign': 'ALICE',
        'callsign': 'ALICE',
        'team': 'Green',
        'team_role': 'Medic',
        'tak_uid': 'TAKMAP-USER-ALICE',
    },
}
fallback_presence = g['_i532_presence_xml'](fallback, {'client_uid': 'TAKMAP-USER-ALICE', 'certificate_cn': 'alice'})
fallback_detail = ET.fromstring(fallback_presence['wire_xml'].strip().encode()).find('detail')
assert fallback_detail.find('__group').attrib == {'name': 'Green', 'role': 'Medic'}
assert fallback_presence['tak_identity_configured'] is False

defaults = {
    'username': 'bob',
    'auth_mode': 'ots-user',
    'tak_uid': 'TAKMAP-USER-BOB',
    'profile': {'username': 'bob', 'callsign': 'BOB', 'tak_uid': 'TAKMAP-USER-BOB'},
}
default_detail = ET.fromstring(g['_i532_presence_xml'](defaults, {'client_uid': 'TAKMAP-USER-BOB'})['wire_xml'].strip().encode()).find('detail')
assert default_detail.find('__group').attrib == {'name': 'Cyan', 'role': 'Team Member'}

for bad in ('Chartreuse', 'cyan team', '<Cyan>'):
    try:
        g['_i534_team_color'](bad)
        raise AssertionError('bad team color accepted: ' + bad)
    except ValueError:
        pass
for bad in ('Commander', 'Observer', '<Medic>'):
    try:
        g['_i534_team_role'](bad)
        raise AssertionError('bad team role accepted: ' + bad)
    except ValueError:
        pass

# Exercise per-user persistence and verify that one user cannot update another
# user's normal account-menu identity settings.
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    g['TAK_MAP_USER_IDENTITIES_FILE'] = tmp / 'user_identities.json'
    g['TAK_MAP_LOCAL_ACCOUNTS_FILE'] = tmp / 'local_accounts.json'
    g['_i509_load_ots_config'] = lambda: {'base_url': 'https://ots.example.test'}
    g['_i534_restart_user_presence'] = lambda current: 1
    now = time.time()
    darktek = {
        'username': 'darktek', 'auth_mode': 'ots-user', 'tak_uid': 'TAKMAP-USER-DARK',
        'created': now, 'expires': now + 600,
        'profile': {
            'username': 'darktek', 'user_id': 7, 'identity_key': 'dark-key',
            'suggested_callsign': 'darktek', 'callsign': 'darktek',
            'tak_uid': 'TAKMAP-USER-DARK',
        },
    }
    other = {
        'username': 'other', 'auth_mode': 'ots-user', 'tak_uid': 'TAKMAP-USER-OTHER',
        'created': now, 'expires': now + 600,
        'profile': {
            'username': 'other', 'user_id': 8, 'identity_key': 'other-key',
            'suggested_callsign': 'OTHER', 'callsign': 'OTHER',
            'tak_uid': 'TAKMAP-USER-OTHER',
        },
    }
    g['TAK_MAP_SESSIONS'].clear()
    g['TAK_MAP_SESSIONS']['dark-token'] = darktek
    g['TAK_MAP_SESSIONS']['other-token'] = other
    result = g['_i534_update_tak_identity'](darktek, {
        'callsign': 'DARKTEK-WEB',
        'team_color': 'Cyan',
        'team_role': 'RTO',
        # A supplied username is intentionally ignored; updates are bound to
        # the authenticated session.
        'username': 'other',
    })
    assert result['ok'] and result['self_service'] is True
    assert result['administrator_override'] is False
    assert result['identity']['callsign'] == 'DARKTEK-WEB'
    assert result['identity']['team_color'] == 'Cyan'
    assert result['identity']['team_role'] == 'RTO'
    assert g['TAK_MAP_SESSIONS']['dark-token']['profile']['selected_callsign'] == 'DARKTEK-WEB'
    assert g['TAK_MAP_SESSIONS']['dark-token']['profile']['selected_team_role'] == 'RTO'
    assert g['TAK_MAP_SESSIONS']['other-token']['profile']['callsign'] == 'OTHER'
    stored = json.loads(g['TAK_MAP_USER_IDENTITIES_FILE'].read_text())['identities']
    assert set(stored) == {'dark-key'}
    assert stored['dark-key']['username'] == 'darktek'
    assert stored['dark-key']['callsign'] == 'DARKTEK-WEB'
    assert stored['dark-key']['team_color'] == 'Cyan'
    assert stored['dark-key']['team_role'] == 'RTO'

assert 'takMapSelfServiceIdentityI534' in g['TAK_MAP_HTML']
assert 'Save My TAK Identity' in g['TAK_MAP_HTML']
assert '/api/tak-map/account/tak-identity' in g['TAK_MAP_HTML']
assert 'takMapPerUserDataSyncIdentityI533' not in g['TAK_MAP_HTML']

print('i534 self-service TAK identity and OTS EUD group assertions passed')
