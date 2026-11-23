#!/usr/bin/env python3
"""TAK Map i633 inherited OpenTAKServer 1.7.13 Configure OTS regression tests."""
from pathlib import Path
import os, runpy, tempfile

ROOT = Path(__file__).resolve().parents[1]
os.environ['TAK_MAP_DATA_DIR'] = tempfile.mkdtemp(prefix='tak-map-i630-ots-')
os.environ['TAK_MAP_OTS_DEFAULT_SERVER'] = 'https://10.10.10.2'
os.environ['TAK_MAP_OTS_TRUSTSTORE_PASSWORD_FALLBACK'] = 'public-default-test'
ns = runpy.run_path(str(ROOT / 'tak_dashboard.py'), run_name='tak_map_i630_ots_test')
g = ns['_i589_adopt_canonical_certificate_host'].__globals__

assert ns['TAK_MAP_ITERATION'] == 'i635'
cfg = ns['tak_map_config']()
feature = cfg['configure_ots_i630']
assert feature['compatibility_target'] == '1.7.13'
assert feature['deployment_default_server'] == 'https://10.10.10.2'
assert feature['managed_hosts_bootstrap'] is True
assert feature['hosts_file_edit_required_when_certificate_needs_dns_name'] is True
assert feature['managed_hosts_mapping_automatic'] is True
assert feature['manual_hosts_file_edit_required'] is False
assert feature['per_user_certificate_preflight'] is True
assert feature['marti_client_certificate_preflight'] is True
assert feature['ots_login_independent_of_data_sync_certificate_failure'] is True

# Wizard-time bootstrap uses the privileged helper result to discover a standard
# 8443 Web/API deployment without requiring the operator to know that port.
g['_i630_bootstrap_managed_dns'] = lambda ip: {
    'ok': True, 'ip': ip, 'hostname': 'opentakserver', 'mapped': True,
    'mapping_required': True, 'web_port': 8443, 'certificate_port': 8443,
}
g['_i589_unverified_certificate'] = lambda host, port=443: {
    'ok': True, 'host': host, 'port': port,
    'subject': {'commonName': 'opentakserver'}, 'issuer': {},
    'sans': [{'type': 'DNS', 'value': 'opentakserver'}],
    'dns_names': ['opentakserver'], 'ip_addresses': [], 'error': '',
}
g['_i589_resolve_addresses'] = lambda host: ['10.10.10.2'] if str(host).strip('[]') in ('10.10.10.2','opentakserver') else []
standard = g['_i589_standard_config']({'server_address':'https://10.10.10.2'})
assert standard['base_url'] == 'https://opentakserver:8443', standard
assert standard['api_url'] == 'https://opentakserver:8443', standard
assert standard['marti_url'] == 'https://opentakserver:8443', standard
assert standard['enrollment_url'] == 'https://opentakserver:8446', standard
assert standard['cot_host'] == 'opentakserver', standard
assert standard['managed_dns']['mapped'] is True
assert standard['managed_dns']['web_port'] == 8443
normalized = g['_i509_normalize_ots_config'](standard, {})
assert normalized['managed_dns']['hostname'] == 'opentakserver', normalized
assert normalized['managed_dns']['mapped'] is True, normalized
public = g['_i509_public_ots_config'](normalized)
assert public['managed_dns']['hostname'] == 'opentakserver', public
assert public['managed_dns']['web_port'] == 8443, public

# If the privileged managed-host helper is unavailable, the exact in-process
# hostname pin must still make a DNS-only certificate usable without weakening
# certificate validation.
g['_i630_bootstrap_managed_dns'] = lambda ip: {
    'ok': False, 'ip': ip, 'mapped': False, 'mapping_required': True,
    'hostname': '', 'web_port': 0, 'error': 'helper unavailable',
}
g['_i589_resolve_addresses'] = lambda host: ['10.10.10.2'] if str(host).strip('[]') == '10.10.10.2' else []
fallback = g['_i589_standard_config']({'server_address':'https://10.10.10.2'})
assert fallback['base_url'] == 'https://opentakserver', fallback
assert fallback['api_url'] == 'https://opentakserver', fallback
assert fallback['marti_url'] == 'https://opentakserver:8443', fallback
assert fallback['enrollment_url'] == 'https://opentakserver:8446', fallback
assert fallback['cot_host'] == 'opentakserver', fallback
assert fallback['transport_pin_enabled'] is True, fallback
assert fallback['transport_host'] == '10.10.10.2', fallback
assert fallback['tls_server_name'] == 'opentakserver', fallback
assert g['_I630_OTS_HOST_ALIASES'].get('opentakserver') == '10.10.10.2'

# A truststore fallback is attempted only when no password was supplied, and it
# comes from installer configuration rather than persisting a submitted secret.
calls = []
def fake_trust(cfg, payload=None, manifest=None):
    payload = dict(payload or {})
    calls.append(payload.get('truststore_password', ''))
    if payload.get('truststore_password') == 'public-default-test':
        return {'ok': True, 'cfg': dict(cfg), 'manifest': manifest or {}, 'path': '/tmp/ca.pem', 'certificates': 1}
    return {'ok': False, 'required_fields': ['truststore_password'], 'error': 'password required'}
g['_i630_install_trust_before'] = fake_trust
trust = g['_i589_install_trust']({'base_url': 'https://opentakserver'}, {}, {})
assert trust['ok'] is True
assert calls == ['', 'public-default-test'], calls
assert trust['default_truststore_password_used'] is True
assert trust['truststore_password_persisted'] is False

# Valid OTS authentication remains a valid TAK Maps login even when Data Sync
# certificate enrollment is temporarily unavailable.
g['_i509_load_ots_config'] = lambda: {
    'enabled': True, 'login_enabled': True, 'data_sync_enabled': True,
    'automatic_user_certificate_enrollment': True,
}
g['_i509_authenticate_remote'] = lambda cfg, username, password, otp='': {'ok': True, 'auth_method': 'api-auth-token'}
g['_i511_fetch_profile'] = lambda cfg, auth, fallback_username='': {'ok': True, 'profile': {
    'username': fallback_username, 'tak_uid': 'TAKMAP-USER-1', 'is_admin': False,
    'display_identity': fallback_username, 'role_names': [],
}}
g['_i512_apply_ots_identity'] = lambda cfg, profile: dict(profile)
g['_i529_ensure_user_certificate'] = lambda cfg, username, password, client_uid, force=False: {
    'ok': False, 'error': 'simulated enrollment outage', 'client_uid': client_uid,
}
def fake_session(username, password, auth_mode, is_admin, auth, profile):
    token = 'i630-test-session'
    with ns['TAK_MAP_SESSIONS_LOCK']:
        ns['TAK_MAP_SESSIONS'][token] = {
            'username': username, 'auth_mode': auth_mode, 'is_admin': is_admin,
            'profile': dict(profile), 'tak_uid': profile.get('tak_uid'),
        }
    return token
g['_i511_create_profile_session'] = fake_session
g['_i509_session_public'] = lambda sess: dict(sess or {})
class FakeHandler:
    def _is_secure_request(self): return True
    def _read_form(self): return {'mode': 'ots', 'username': 'user1', 'password': 'secret'}
    def _send_json(self, obj, status=200, headers=None): return obj, status, headers or {}
    def _tak_map_session_cookie(self, token): return 'tak-map-session=' + token
reply, status, headers = g['_i630_handle_login'](FakeHandler())
assert status == 200, (status, reply)
assert reply['ok'] is True
assert reply['ots_authentication_succeeded'] is True
assert reply['data_sync_identity_ready'] is False
assert 'simulated enrollment outage' in reply['data_sync_warning']
assert 'Set-Cookie' in headers

# The Configure OTS commit path must perform the certificate and mTLS preflight
# before persisting/activating the OTS connection, and it must never persist
# submitted authentication secrets.
sequence = []
saved_cfg = {}
base_cfg = {
    'base_url': 'https://opentakserver',
    'api_url': 'https://opentakserver',
    'marti_url': 'https://opentakserver:8443',
    'enrollment_url': 'https://opentakserver:8446',
    'cot_host': 'opentakserver', 'cot_port': 8089,
    'enabled': True, 'login_enabled': True, 'data_sync_enabled': True,
    'automatic_trust_installation': True,
    'automatic_user_certificate_enrollment': True,
    'advanced_overrides': {}, 'canonical_discovery': {
        'entered_base_url': 'https://10.10.10.2',
        'adopted_certificate_hostname': True,
    },
    'managed_dns': {'ok': True, 'mapped': True, 'mapping_required': True,
                    'ip': '10.10.10.2', 'hostname': 'opentakserver',
                    'web_port': 443, 'certificate_port': 443},
    'transport_pin_enabled': False, 'transport_host': '', 'tls_server_name': '',
}
g['_i589_decode_opaque_transport'] = lambda payload: dict(payload or {})
g['_i589_standard_config'] = lambda payload=None: dict(base_cfg)
g['_i589_standard_endpoint_checks'] = lambda cfg, strict=False: {
    'required_fields': [],
    'checks': {'web': True, 'truststore': True, 'marti': True, 'enrollment': True, 'cot': True},
}
g['_i589_manifest_load'] = lambda *args, **kwargs: {'files': [], 'managed_trees': []}
def full_trust(cfg, payload=None, manifest=None):
    sequence.append('trust')
    trusted = dict(cfg); trusted['ca_cert_path'] = '/tmp/mock-ots-ca.pem'
    return {'ok': True, 'cfg': trusted, 'manifest': dict(manifest or {}), 'path': '/tmp/mock-ots-ca.pem', 'certificates': 1}
g['_i589_install_trust'] = full_trust
g['_i589_adopt_canonical_certificate_host'] = lambda cfg: dict(cfg)
g['_i509_authenticate_remote'] = lambda cfg, username, password, otp='': (sequence.append('auth') or {'ok': True, 'auth_method': 'api-auth-token'})
g['_i511_fetch_profile'] = lambda cfg, auth, fallback_username='': (sequence.append('profile') or {'ok': True, 'profile': {
    'username': fallback_username, 'tak_uid': 'TAKMAP-ADMIN-1', 'is_admin': True,
    'display_identity': fallback_username, 'role_names': ['administrator'],
}})
g['_i512_apply_ots_identity'] = lambda cfg, profile: dict(profile)
g['_i630_detect_ots_version'] = lambda cfg, auth: (sequence.append('version') or {
    'target': '1.7.13', 'detected': '1.7.13', 'detected_source': '/api/status:version',
    'advertised_match': True, 'endpoint_compatible': True, 'probes': [],
})
g['_i529_ensure_user_certificate'] = lambda cfg, username, password, client_uid, force=False: (sequence.append('certificate') or {
    'ok': True, 'client_uid': client_uid, 'username': username,
})
g['_i630_mtls_probe'] = lambda cfg, username, client_uid: (sequence.append('mtls') or {
    'ok': True, 'status': 200, 'endpoint': cfg['marti_url'] + '/Marti/api/version/config',
})
def full_save(cfg):
    sequence.append('save')
    saved_cfg.clear(); saved_cfg.update(dict(cfg))
    return dict(cfg)
g['_i509_save_ots_config'] = full_save
g['_i589_record_file'] = lambda *args, **kwargs: None
g['_i589_manifest_write'] = lambda manifest: dict(manifest)
g['_i509_discover_ots'] = lambda cfg: {'ok': True, 'summary': {}}
full = g['_i589_enroll_server']({
    'server_address': 'https://10.10.10.2',
    'username': 'administrator', 'password': 'super-secret', 'otp': '654321',
    'truststore_password': 'also-secret',
})
assert full['ok'] is True, full
assert full['preflight']['per_user_certificate'] is True
assert full['preflight']['client_certificate_mtls'] is True
assert sequence.index('certificate') < sequence.index('mtls') < sequence.index('save'), sequence
assert full['password_persisted'] is False
assert full['otp_persisted'] is False
assert full['truststore_password_persisted'] is False
for forbidden in ('password', 'otp', 'truststore_password'):
    assert forbidden not in saved_cfg, (forbidden, saved_cfg)

# Installer contains a bounded /etc/hosts manager, automatic bootstrap, the
# 10.10.10.2 deployment default, and cleanup on uninstall.
install = (ROOT/'install.sh').read_text()
uninstall = (ROOT/'uninstall.sh').read_text()
assert '# BEGIN TAK MAP MANAGED OTS HOSTS' in install
assert 'ots-host-bootstrap' in install and 'ots-host-clear' in install
assert 'STANDARD_WEB_PORTS=(443,8443)' in install
assert 'TAK_MAP_OTS_DEFAULT_SERVER' in install
assert 'DEFAULT_OTS_IP="${TAK_MAP_OTS_IP:-10.10.10.2}"' in install
assert 'ots-host-clear' in uninstall

print('TAK Map i633 inherited OTS 1.7.13 managed-DNS, endpoint discovery, login, and trust regression tests passed')
