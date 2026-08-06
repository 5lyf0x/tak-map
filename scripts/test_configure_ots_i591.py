#!/usr/bin/env python3
import importlib.util
import json
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TMP = Path(tempfile.mkdtemp(prefix='tak-map-i589-ots-'))
DATA = TMP / 'data'
DATA.mkdir(parents=True)
legacy_manifest_path = DATA / 'ots_enrollment_manifest_i587.json'
legacy_manifest_path.write_text(json.dumps({'version':'i587','status':'disconnected','origin':'https://legacy.example.test','files':[],'managed_trees':[],'remote_certificates':[],'state_entries':[]}))
os.environ['TAK_DASHBOARD_DATA_DIR'] = str(DATA)
os.environ['TAK_MAP_MIL_ROOT'] = str(ROOT / 'assets' / 'mil2525')

spec = importlib.util.spec_from_file_location('tak_dashboard_i591_ots', ROOT / 'tak_dashboard.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

assert mod.TAK_MAP_ITERATION == 'i600'
migrated_manifest = mod._i589_manifest_load(adopt=False)
assert migrated_manifest['origin'] == 'https://legacy.example.test'
assert mod._I589_ENROLLMENT_MANIFEST_FILE.exists()
assert not legacy_manifest_path.exists()
config = mod.tak_map_config()
assert config['version'] == '1.3.0-i600'
assert config['configure_ots_i589']['minimum_initial_fields'] == [
    'server_address', 'administrator_username', 'administrator_password'
]
assert config['configure_ots_i589']['full_functionality_defaults_checked'] is True
assert config['configure_ots_i589']['browser_autofill_suppressed'] is True
assert config['configure_ots_i589']['password_manager_opt_out_attributes'] is True
assert config['configure_ots_i589']['sensitive_fields_readonly_until_user_interaction'] is True
assert config['configure_ots_i589']['request_secrets_cleared_after_each_request'] is True
assert config['configure_ots_i589']['modal_credentials_cleared_on_close'] is True
assert config['configure_ots_i589']['opaque_field_ids_and_names'] is True
assert config['configure_ots_i589']['opaque_positional_request_transport'] is True
assert config['configure_ots_i589']['semantic_transport_keys_exposed_by_browser'] is False
assert config['configure_ots_i589']['connection_section_header_removed'] is True
assert config['configure_ots_i589']['sentence_case_labels'] is True
assert config['configure_ots_i589']['compact_checkbox_text'] is True
assert config['configure_ots_i589']['two_factor_label'] == '2FA Code (optional)'
assert config['configure_ots_i589']['all_four_checkboxes_checked_for_new_configuration'] is True
assert config['configure_ots_i589']['ots_default_helper_text'] == 'OTS Default: https://opentakserver'
assert config['configure_ots_i589']['protocol_aware_endpoint_classification'] is True
assert config['configure_ots_i589']['certificate_hostname_discovery'] is True
assert config['configure_ots_i589']['disconnect_helper'] == 'Disabled OTS login but keeps connection details.'
assert config['configure_ots_i589']['unenroll_helper'] == 'Disconnects and completely removes OTS enrollment.'

# Browser request keys are opaque. Semantic names are created only at the API boundary.
opaque = {'q': ['https://ots.example.test', 'admin', 'secret', '123456', True, True, True, True, True, '', '', '', '', 8089, '/api/truststore', 'trust-secret', '', 'UNENROLL']}
decoded = mod._i589_decode_opaque_transport(opaque)
assert decoded['server_address'] == 'https://ots.example.test'
assert decoded['username'] == 'admin' and decoded['password'] == 'secret'
assert decoded['otp'] == '123456' and decoded['confirmation'] == 'UNENROLL'
assert list(opaque) == ['q']

# Standard values are derived from only the server address; passwords are not inferred.
candidate = mod._i589_standard_config({'server_address': 'ots.example.test'})
assert candidate['base_url'] == 'https://ots.example.test'
assert candidate['api_url'] == 'https://ots.example.test'
assert candidate['marti_url'] == 'https://ots.example.test:8443'
assert candidate['enrollment_url'] == 'https://ots.example.test:8446'
assert candidate['cot_host'] == 'ots.example.test'
assert candidate['cot_port'] == 8089
assert candidate['truststore_path'] == '/api/truststore'
assert candidate['enabled'] and candidate['login_enabled'] and candidate['data_sync_enabled']
assert candidate['automatic_user_certificate_enrollment'] and candidate['automatic_trust_installation']
for forbidden in ('password', 'otp', 'truststore_password'):
    assert forbidden not in candidate

# Standard protocol responses are accepted and only a genuinely failed endpoint is revealed.
old_probe, old_cert_probe, old_adopt = mod._i589_http_probe, mod._i509_cert_probe, mod._i589_adopt_canonical_certificate_host
try:
    mod._i589_adopt_canonical_certificate_host = lambda cfg: cfg
    def semantic_probe(url, method='GET', **kwargs):
        base = {'url': url, 'final_url': url, 'reachable': True, 'tls_verified': not kwargs.get('unverified', True), 'error': '', 'headers': {}, 'body': b'', 'body_preview': ''}
        if '/api/truststore' in url:
            return {**base, 'status': 200, 'ok': True, 'body': b'PKCS12', 'headers': {'Content-Type':'application/pkcs12'}}
        if ':8443/' in url:
            return {**base, 'status': 400, 'ok': False, 'body_preview': 'No required SSL certificate was sent'}
        if ':8446/' in url:
            return {**base, 'status': 405, 'ok': False, 'headers': {'Allow':'POST, OPTIONS'}}
        return {**base, 'status': 200, 'ok': True, 'body': b'OK'}
    mod._i589_http_probe = semantic_probe
    mod._i509_cert_probe = lambda *a, **k: {'ok': True, 'strict_tls_ok': True, 'hostname_match': True}
    checks = mod._i589_standard_endpoint_checks(candidate)
    assert checks['required_fields'] == [], checks
    assert all(checks['checks'].values()), checks

    def failed_marti(url, method='GET', **kwargs):
        row = semantic_probe(url, method=method, **kwargs)
        if ':8443/' in url:
            row.update({'status':404,'ok':False,'body_preview':'not found'})
        return row
    mod._i589_http_probe = failed_marti
    checks = mod._i589_standard_endpoint_checks(candidate)
    assert checks['required_fields'] == ['marti_url'], checks
finally:
    mod._i589_http_probe, mod._i509_cert_probe, mod._i589_adopt_canonical_certificate_host = old_probe, old_cert_probe, old_adopt

# An IP entry automatically adopts a certificate DNS name only when both resolve to the same server.
old_cert, old_resolve = mod._i589_unverified_certificate, mod._i589_resolve_addresses
try:
    mod._i589_unverified_certificate = lambda host, port=443: {'ok':True,'dns_names':['opentakserver'],'ip_addresses':[],'subject':{'commonName':'opentakserver'},'sans':[{'type':'DNS','value':'opentakserver'}]}
    mod._i589_resolve_addresses = lambda host: ['10.10.10.3'] if str(host).strip('[]').lower() in ('10.10.10.3','opentakserver') else []
    canonical = mod._i589_standard_config({'server_address':'https://10.10.10.3'})
    assert canonical['base_url'] == 'https://opentakserver', canonical
    assert canonical['marti_url'] == 'https://opentakserver:8443'
    assert canonical['enrollment_url'] == 'https://opentakserver:8446'
    assert canonical['cot_host'] == 'opentakserver'
    assert canonical['canonical_discovery']['adopted_certificate_hostname'] is True
finally:
    mod._i589_unverified_certificate, mod._i589_resolve_addresses = old_cert, old_resolve

# Generate a CA and an encrypted PKCS#12 truststore. No password is assumed.
cert = TMP / 'ca.pem'
key = TMP / 'ca.key'
p12 = TMP / 'truststore.p12'
subprocess.run([
    'openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '2',
    '-subj', '/CN=TAK Map i589 Test CA', '-keyout', str(key), '-out', str(cert)
], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run([
    'openssl', 'pkcs12', '-export', '-in', str(cert), '-inkey', str(key),
    '-passout', 'pass:custom-only-password', '-out', str(p12)
], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
assert not mod._i589_extract_trust_certificates(p12.read_bytes(), ''), 'Encrypted truststore opened without a supplied password'
assert mod._i589_extract_trust_certificates(p12.read_bytes(), 'custom-only-password')

# Enrollment response persists no credential or one-time secret.
old_checks = mod._i589_standard_endpoint_checks
old_install = mod._i589_install_trust
old_discover = mod._i509_discover_ots
old_auth = mod._i509_authenticate_remote
old_profile = mod._i511_fetch_profile
old_validate = mod._i509_validate_login_activation
try:
    mod._i589_standard_endpoint_checks = lambda cfg, strict=False: {
        'checks': {'web': True, 'truststore': True, 'marti': True, 'enrollment': True, 'cot': True},
        'probes': {}, 'cot': {'ok': True}, 'required_fields': []
    }
    mod._i589_install_trust = lambda cfg, payload, manifest: {
        'ok': True, 'cfg': {**cfg, 'ca_cert_path': str(cert)}, 'manifest': manifest,
        'path': str(cert), 'certificates': 1, 'certificate_identities': []
    }
    mod._i509_discover_ots = lambda cfg: {'ok': True, 'summary': {
        'web_reachable': True, 'strict_web_tls': True, 'hostname_match': True,
        'cot_tls_reachable': True, 'marti_available': True, 'enrollment_available': True
    }}
    mod._i509_authenticate_remote = lambda cfg, username, password, otp='': {
        'ok': username == 'admin' and password == 'secret', 'token': 'memory-only'
    }
    mod._i509_validate_login_activation = lambda cfg: None
    mod._i511_fetch_profile = lambda cfg, auth, username: {'ok': True, 'profile': {
        'username': username, 'display_identity': 'ADMIN', 'role_names': ['administrator'], 'is_admin': True
    }}
    enrolled = mod._i589_enroll_server({'q': [
        'https://ots.example.test', 'admin', 'secret', '654321',
        True, True, True, True, True, '', '', '', '', 8089,
        '/api/truststore', '', '', ''
    ]})
    assert enrolled['ok'] is True, enrolled
    assert enrolled['password_persisted'] is False and enrolled['otp_persisted'] is False
    persisted = json.loads(mod.TAK_MAP_OTS_CONFIG_FILE.read_text())
    for forbidden in ('password', 'username', 'otp', 'truststore_password', 'token', 'cookies'):
        assert forbidden not in persisted, (forbidden, persisted)
    manifest = json.loads(mod._I589_ENROLLMENT_MANIFEST_FILE.read_text())
    assert manifest['status'] == 'enrolled'
    assert any(row.get('path') == str(mod.TAK_MAP_OTS_CONFIG_FILE) for row in manifest['files'])
finally:
    mod._i589_standard_endpoint_checks = old_checks
    mod._i589_install_trust = old_install
    mod._i509_discover_ots = old_discover
    mod._i509_authenticate_remote = old_auth
    mod._i511_fetch_profile = old_profile
    mod._i509_validate_login_activation = old_validate

# Manifest-scoped Unenroll removes only recorded enrollment artifacts.
managed_tree = DATA / 'ots_user_credentials'
managed_tree.mkdir(parents=True, exist_ok=True)
(managed_tree / 'client-cert.pem').write_text('managed')
managed_file = DATA / 'ots_trust' / 'opentakserver-ca-chain.crt'
managed_file.parent.mkdir(parents=True, exist_ok=True)
managed_file.write_text('managed')
unrelated = DATA / 'unrelated-local-data.json'
unrelated.write_text('preserve-me')
manifest = mod._i589_manifest_default()
manifest.update({'status': 'enrolled', 'origin': 'https://ots.example.test', 'created_at': mod._i589_iso_now()})
mod._i589_record_tree(manifest, managed_tree, 'per-user-certificates')
mod._i589_record_file(manifest, managed_file, 'ots-ca-chain')
manifest['remote_certificates'] = [{'certificate_cn': 'takmap-test', 'client_uid': 'TAKMAP-TEST'}]
mod._i589_manifest_write(manifest)
mod.TAK_MAP_OTS_CONFIG_FILE.write_text(json.dumps({'base_url': 'https://ots.example.test', 'enabled': True, 'login_enabled': True}))
old_ready = mod._i512_local_admin_ready
old_revoke = mod._i589_attempt_remote_revocation
try:
    mod._i512_local_admin_ready = lambda: True
    mod._i589_attempt_remote_revocation = lambda *a, **k: {
        'attempted': True, 'supported': True, 'revoked': [],
        'outstanding': [{'certificate_cn': 'takmap-test', 'error': 'simulated remote failure'}],
        'message': 'simulated'
    }
    result = mod._i589_unenroll_server({'q': ['', '', '', '', True, True, True, True, True, '', '', '', '', 8089, '/api/truststore', '', '', 'UNENROLL']})
    assert result['remote_cleanup_outstanding'] is True
    assert unrelated.read_text() == 'preserve-me'
    assert not managed_tree.exists()
    assert not managed_file.exists()
    assert not mod.TAK_MAP_OTS_CONFIG_FILE.exists()
    assert not mod._I589_ENROLLMENT_MANIFEST_FILE.exists()
    assert 'OTS users' in result['preserved'] and 'map points' in result['preserved']
finally:
    mod._i512_local_admin_ready = old_ready
    mod._i589_attempt_remote_revocation = old_revoke

source = (ROOT / 'tak_dashboard.py').read_text(errors='replace')
assert "Disabled OTS login but keeps connection details." in source
assert "Disconnects and completely removes OTS enrollment." in source
assert "atakatak" not in source[source.index('# --- TAK Map i589 automated Configure OTS'):]
assert "Type UNENROLL" in source
assert 'Connect this TAK Map server' not in source
assert '2FA Code (optional)' in source
assert 'OTS Default: https://opentakserver' in source
assert "function transport(confirmText){return {q:[" in source
assert 'name="takmap_i589' not in source
assert 'id="ots589User' not in source
print('i589 Configure OTS discovery, manifest migration, no-assumed-password trust, secret handling, enrollment manifest, and scoped Unenroll tests passed')
