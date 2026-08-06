#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(data_dir: Path):
    os.environ['TAK_DASHBOARD_DATA_DIR'] = str(data_dir)
    spec = importlib.util.spec_from_file_location('tak_map_i529_test', ROOT / 'tak_dashboard.py')
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def provision_fixture(m, username='darktek', client_uid='TAKMAP-USER-darktek'):
    paths = m._i529_paths(username)
    paths['root'].mkdir(parents=True, exist_ok=True)
    password = m._i529_key_password(username)
    env = os.environ.copy()
    env['TAKMAP_I529_KEY_PASSWORD'] = password
    subprocess.run([
        'openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-sha256', '-days', '30',
        '-keyout', str(paths['key']), '-out', str(paths['cert']),
        '-subj', '/CN=' + username,
        '-passout', 'env:TAKMAP_I529_KEY_PASSWORD',
    ], env=env, capture_output=True, check=True, timeout=45)
    paths['ca'].write_bytes(paths['cert'].read_bytes())
    paths['csr'].write_text('fixture\n')
    paths['meta'].write_text(json.dumps({
        'version': 'i534',
        'username': username,
        'client_uid': client_uid,
        'identity_mode': 'per-user-enrolled-marti-certificate',
        'shared_service_fallback': False,
    }))
    for key in ('root',):
        os.chmod(paths[key], 0o700)
    for key in ('key', 'meta', 'csr'):
        os.chmod(paths[key], 0o600)
    for key in ('cert', 'ca'):
        os.chmod(paths[key], 0o640)
    return paths


def point_feature():
    return {
        'type': 'Feature',
        'canonical_id': 'local:ds-p05',
        'geometry': {'type': 'Point', 'coordinates': [-118.4, 34.4, 200]},
        'properties': {
            'name': 'DS-P05',
            'callsign': 'DS-P05',
            'sidc': 'SFGPUCA--------',
            'mil2525_name': 'friendly-ground-unit-armor',
            'mil2525_label': 'ARMOR',
            'cot_type': 'a-f-G-U-C',
        },
    }


def main():
    with tempfile.TemporaryDirectory(prefix='tak-map-i529-test-') as td:
        m = load_module(Path(td))
        assert m.TAK_MAP_ITERATION == 'i537'
        assert m._i529_pem('QUJD', 'CERTIFICATE').startswith('-----BEGIN CERTIFICATE-----\nQUJD')
        paths = provision_fixture(m)
        status = m._i529_public_certificate_status('darktek', 'TAKMAP-USER-darktek')
        assert status['ok'], status
        assert status['certificate_cn'] == 'darktek'
        assert status['client_uid'] == 'TAKMAP-USER-darktek'
        assert status['shared_service_fallback'] is False
        assert status['renewal_required'] is False

        # Exercise the complete key/CSR/enrollment/storage path with a local signing fixture.
        ca_root = Path(td) / 'fixture-ca'
        ca_root.mkdir()
        ca_key = ca_root / 'ca.key'
        ca_cert = ca_root / 'ca.crt'
        subprocess.run([
            'openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-sha256', '-days', '60',
            '-keyout', str(ca_key), '-out', str(ca_cert), '-subj', '/CN=Fixture OTS CA',
        ], capture_output=True, check=True, timeout=45)
        original_enroll = m._i529_enrollment_request
        def fake_enroll(cfg, username, password, client_uid, csr_pem):
            work = ca_root / username
            work.mkdir(exist_ok=True)
            csr = work / 'client.csr'
            cert = work / 'client.crt'
            csr.write_bytes(csr_pem)
            subprocess.run([
                'openssl', 'x509', '-req', '-in', str(csr), '-CA', str(ca_cert), '-CAkey', str(ca_key),
                '-CAcreateserial', '-out', str(cert), '-days', '30', '-sha256',
            ], capture_output=True, check=True, timeout=45)
            return {'signed_cert': cert.read_text(), 'ca_chain': ca_cert.read_text(), 'endpoint': 'fixture://enrollment', 'status': 200}
        m._i529_enrollment_request = fake_enroll
        enrolled = m._i529_ensure_user_certificate({'ca_cert_path': str(ca_cert)}, 'enrolluser', 'secret', 'TAKMAP-USER-enrolluser', True)
        m._i529_enrollment_request = original_enroll
        assert enrolled['ok'], enrolled
        assert enrolled['certificate_cn'] == 'enrolluser'
        encrypted_key = m._i529_paths('enrolluser')['key'].read_text(errors='ignore')
        assert 'ENCRYPTED PRIVATE KEY' in encrypted_key
        assert 'BEGIN PRIVATE KEY' not in encrypted_key.replace('BEGIN ENCRYPTED PRIVATE KEY', '')

        token = 'fixture-session'
        m.TAK_MAP_SESSIONS[token] = {
            'username': 'darktek',
            'auth_mode': 'ots-user',
            'tak_uid': 'TAKMAP-USER-darktek',
            'callsign': 'darktek',
            'profile': {'username': 'darktek', 'tak_uid': 'TAKMAP-USER-darktek', 'callsign': 'darktek'},
        }
        m._I529_REQUEST_CONTEXT.session_token = token
        m._I529_REQUEST_CONTEXT.auth_mode = 'ots-user'
        m._I512_REQUEST_CONTEXT.identity = {'username': 'darktek', 'callsign': 'darktek', 'tak_uid': 'TAKMAP-USER-darktek'}

        user_calls = []
        service_calls = []
        def user_request(*args, **kwargs):
            user_calls.append((args, kwargs))
            return {'ok': False, 'error': 'fixture user failure', 'shared_service_fallback': False}
        def service_request(*args, **kwargs):
            service_calls.append((args, kwargs))
            return {'ok': True, 'source': 'service'}
        m._i529_user_mission_api_request = user_request
        m._i529_service_mission_request = service_request
        result = m._ots_mission_api_request('/Marti/api/missions/test')
        assert result['ok'] is False
        assert len(user_calls) == 1
        assert not service_calls, 'User request must never fall back to the shared service identity.'

        m._I529_REQUEST_CONTEXT.auth_mode = ''
        background = m._ots_mission_api_request('/background')
        assert background['ok'] is True and len(service_calls) == 1

        m._I529_REQUEST_CONTEXT.auth_mode = 'ots-user'
        creator = m._i528_strict_creator()
        assert creator['ok'], creator
        assert creator['uid'] == 'TAKMAP-USER-darktek'
        assert creator['certificate_cn'] == 'darktek'
        assert creator['shared_service_fallback'] is False

        built = m._i526_point_xml(point_feature(), 'TAKMAP-DATASYNC-TEST', creator['uid'])
        assert built['ok'], built
        root = ET.fromstring(built['xml'])
        detail = root.find('detail')
        assert detail is not None
        identity = detail.find('takmap')
        assert identity is not None
        assert identity.attrib['version'] == 'i534'
        assert identity.attrib['transportIdentity'] == 'per-user-enrolled-marti-certificate'
        assert identity.attrib['serviceCredentialFallback'] == 'false'
        assert root.attrib['uid'].startswith('TAKMAP-MISSION-POINT-')
        assert root.attrib['type'] == 'a-f-G-U-C-A'

        cfg = m.tak_map_config()
        assert cfg['tak_map_iteration'] == 'i537'
        assert cfg['ots_integration']['per_user_marti_certificate_required'] is True
        assert cfg['ots_integration']['shared_service_certificate_fallback'] is False
        assert cfg['data_sync_native_point_publish']['identity_mode'] == 'per-user-enrolled-marti-certificate'
        assert cfg['data_sync_native_point_publish']['shared_service_certificate_fallback'] is False
        assert 'takMapSelfServiceIdentityI534' in m.TAK_MAP_HTML
        assert 'ots_user_credentials' in (ROOT / 'install.sh').read_text()
        assert 'chmod 0700 "$DATA_DIR/ots_user_credentials"' in (ROOT / 'install.sh').read_text()

        public = m._i509_session_public(m.TAK_MAP_SESSIONS[token])
        assert public['data_sync_identity_ready'] is True
        assert public['data_sync_identity']['certificate_cn'] == 'darktek'
        assert 'private_key_path' not in public['data_sync_identity']
        assert 'key_password' not in public['data_sync_identity']

    print('i532 preserved per-user OpenTAKServer certificate-only Data Sync identity tests passed')


if __name__ == '__main__':
    main()
