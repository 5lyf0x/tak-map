#!/usr/bin/env python3
"""Offline regression checks for TAK Gateway transport modes and Replay payload parity.

Uses the full staged TAK Map runtime with mocked Gateway API responses;
never requires a live Gateway or sends network traffic.
"""
import contextlib
import email.message
import gzip
import io
import json
import os
from pathlib import Path
import runpy
import ssl
import subprocess
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
NS = runpy.run_path(str(ROOT / 'tak_dashboard.py'), run_name='test_gateway_optional_certificate')
G = NS['_tak_gateway_connection_profile'].__globals__


class FakeResponse:
    status = 200

    def __init__(self, data, *, headers=None):
        self.body = data
        self.headers = email.message.Message()
        for k, v in (headers or {'Content-Type': 'application/json'}).items():
            self.headers[k] = v

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self, n=-1):
        return self.body[:n] if n >= 0 else self.body


class FakeHandler:
    def __init__(self):
        self.json = None
        self.status = None
        self.headers = {}
        self.wfile = io.BytesIO()

    def _send_json(self, value, status=200):
        self.json = value
        self.status = status

    def send_response(self, status):
        self.status = status

    def send_header(self, name, value):
        self.headers[name] = value

    def end_headers(self):
        pass


class GatewayOptionalCertificateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        base = Path(cls.tmp.name)
        cls.cert, cls.key = base/'client.crt', base/'client.key'
        subprocess.run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
                        '-keyout', str(cls.key), '-out', str(cls.cert), '-days', '2',
                        '-subj', '/CN=tak-map-auth-mode-test'],
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, check=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.env = mock.patch.dict(os.environ, {
            'TAK_MAP_ENROLLMENT_MANIFEST': '/nonexistent/optional-auth-test.json',
            'TAK_MAP_REPLAY_CLIENT_CERT': '/missing/replay-cert',
            'TAK_MAP_REPLAY_CLIENT_KEY': '/missing/replay-key',
            'TAK_MAP_REPLAY_CA_CERT': '/missing/replay-ca',
            'TAK_MAP_REPLAY_AUTH_MODE': 'certificate',
            'TAK_MAP_GATEWAY_DATA_AUTH_MODE': 'none',
            'TAK_MAP_GATEWAY_DATA_VERIFY_TLS': 'true',
        }, clear=False)
        self.env.start()
        self.orig = {k:G.get(k) for k in ('TAK_MAP_REPLAY_API_URL', 'TAK_MAP_GATEWAY_DATA_API_URL',
                                          'TAK_MAP_REPLAY_CLIENT_CERT','TAK_MAP_REPLAY_CLIENT_KEY',
                                          'TAK_MAP_REPLAY_CA_CERT','TAK_MAP_REPLAY_VERIFY_TLS')}
        G['TAK_MAP_REPLAY_API_URL'] = 'https://127.0.0.1:9443/api/replay/v1'
        G['TAK_MAP_GATEWAY_DATA_API_URL'] = 'https://127.0.0.1:9443/api/external-sources/v1'
        G['TAK_MAP_REPLAY_CLIENT_CERT'] = '/missing/replay-cert'
        G['TAK_MAP_REPLAY_CLIENT_KEY'] = '/missing/replay-key'
        G['TAK_MAP_REPLAY_CA_CERT'] = '/missing/replay-ca'
        G['TAK_MAP_REPLAY_VERIFY_TLS'] = True
        G['_i475_gateway_ssl_cache'].update({'initialized':False,'key':None,'ctx':None})

    def tearDown(self):
        for k,v in self.orig.items():G[k]=v
        self.env.stop()

    def test_gateway_data_no_cert_https_requires_server_tls_verification(self):
        p = G['_tak_gateway_connection_profile']('gateway_data')
        self.assertTrue(p['configured'])
        self.assertEqual(p['auth_mode'], 'none')
        ctx, reused = G['_i475_gateway_ssl_context']()
        self.assertFalse(reused)
        self.assertIsInstance(ctx, ssl.SSLContext)
        self.assertEqual(ctx.verify_mode, ssl.CERT_REQUIRED)
        self.assertTrue(ctx.check_hostname)
        self.assertTrue(G['_i475_gateway_ssl_context']()[1])
        self.assertEqual(G['_i475_gateway_data_config']()['auth'], 'none')

    def test_gateway_data_no_cert_http_and_cert_over_http_denied(self):
        G['TAK_MAP_GATEWAY_DATA_API_URL'] = 'http://10.10.10.101:8090/api/external-sources/v1'
        self.assertTrue(G['_tak_gateway_connection_profile']('gateway_data')['configured'])
        self.assertEqual(G['_i475_gateway_ssl_context']()[0], None)
        os.environ['TAK_MAP_GATEWAY_DATA_AUTH_MODE'] = 'certificate'
        self.assertFalse(G['_tak_gateway_connection_profile']('gateway_data')['configured'])

    def test_gateway_data_cert_mode_is_separate_from_replay(self):
        os.environ['TAK_MAP_GATEWAY_DATA_AUTH_MODE'] = 'certificate'
        os.environ['TAK_MAP_GATEWAY_DATA_CLIENT_CERT'] = str(self.cert)
        os.environ['TAK_MAP_GATEWAY_DATA_CLIENT_KEY'] = str(self.key)
        os.environ['TAK_MAP_GATEWAY_DATA_CA_CERT'] = str(self.cert)
        self.assertTrue(G['_tak_gateway_connection_profile']('gateway_data')['configured'])
        self.assertEqual(G['_tak_gateway_connection_profile']('gateway_data')['auth_mode'],'certificate')
        ctx, _ = G['_i475_gateway_ssl_context']()
        self.assertIsInstance(ctx, ssl.SSLContext)
        self.assertFalse(G['_tak_gateway_connection_profile']('replay')['configured'])
        self.assertTrue(G['_i475_gateway_data_config']()['client_certificate_required'])

    def test_gateway_data_auto_preserves_existing_and_fails_closed_if_partial(self):
        os.environ['TAK_MAP_GATEWAY_DATA_AUTH_MODE'] = 'auto'
        self.assertEqual(G['_tak_gateway_connection_profile']('gateway_data')['auth_mode'], 'none')
        os.environ['TAK_MAP_GATEWAY_DATA_CLIENT_CERT'] = str(self.cert)
        os.environ['TAK_MAP_GATEWAY_DATA_CLIENT_KEY'] = str(self.key)
        self.assertEqual(G['_tak_gateway_connection_profile']('gateway_data')['auth_mode'], 'certificate')
        os.environ['TAK_MAP_GATEWAY_DATA_CLIENT_KEY'] = '/missing/key'
        self.assertFalse(G['_tak_gateway_connection_profile']('gateway_data')['configured'])
        os.environ['TAK_MAP_GATEWAY_DATA_AUTH_MODE'] = 'none'
        self.assertTrue(G['_tak_gateway_connection_profile']('gateway_data')['configured'])

    def test_invalid_mode_and_missing_enrollment_fails_closed(self):
        os.environ['TAK_MAP_GATEWAY_DATA_AUTH_MODE'] = 'anonymous-please'
        self.assertFalse(G['_tak_gateway_connection_profile']('gateway_data')['configured'])
        os.environ['TAK_MAP_GATEWAY_DATA_AUTH_MODE'] = 'auto'
        with tempfile.NamedTemporaryFile() as f:
            os.environ['TAK_MAP_ENROLLMENT_MANIFEST'] = f.name
            self.assertFalse(G['_tak_gateway_connection_profile']('gateway_data')['configured'])

    def test_replay_backward_compat_default_requires_cert(self):
        status = G['_tak_v415_replay_config_status']()
        self.assertFalse(status['configured'])
        self.assertEqual(status['auth_mode'], 'certificate')
        self.assertEqual(status['version'], 'v415')
        os.environ['TAK_MAP_REPLAY_CLIENT_CERT'] = str(self.cert)
        os.environ['TAK_MAP_REPLAY_CLIENT_KEY'] = str(self.key)
        G['TAK_MAP_REPLAY_CLIENT_CERT'] = str(self.cert)
        G['TAK_MAP_REPLAY_CLIENT_KEY'] = str(self.key)
        os.environ['TAK_MAP_REPLAY_CA_CERT'] = str(self.cert)
        G['TAK_MAP_REPLAY_CA_CERT'] = str(self.cert)
        status = G['_tak_v415_replay_config_status']()
        self.assertTrue(status['configured'])
        self.assertEqual(status['auth_mode'], 'certificate')
        self.assertIsInstance(G['_tak_v415_replay_ssl_context'](), ssl.SSLContext)

    def test_replay_no_cert_https_only_not_unverified(self):
        os.environ['TAK_MAP_REPLAY_AUTH_MODE'] = 'none'
        self.assertTrue(G['_tak_v415_replay_config_status']()['configured'])
        ctx = G['_tak_v415_replay_ssl_context']()
        self.assertTrue(ctx.check_hostname)
        self.assertEqual(ctx.verify_mode, ssl.CERT_REQUIRED)
        G['TAK_MAP_REPLAY_API_URL'] = 'http://10.10.10.101:8090/api/replay/v1'
        self.assertFalse(G['_tak_v415_replay_config_status']()['configured'])
        G['TAK_MAP_REPLAY_API_URL'] = 'https://127.0.0.1:9443/api/replay/v1'
        G['TAK_MAP_REPLAY_VERIFY_TLS'] = False
        self.assertFalse(G['_tak_v415_replay_config_status']()['configured'])

    def test_gateway_data_health_snapshot_capabilities_unmodified(self):
        paths = []
        def fake_open(req, *, context, timeout):
            paths.append(req.full_url)
            return FakeResponse(json.dumps({'ok':True,'revision':7,'objects':[],'deleted_uids':[]}).encode())
        with mock.patch.object(G['_urlreq_v415'], 'urlopen', side_effect=fake_open):
            for endpoint in ('health', 'capabilities', 'snapshot'):
                h = FakeHandler()
                G['_i475_gateway_data_proxy'](h, endpoint, 'since_revision=7' if endpoint=='snapshot' else '')
                self.assertEqual(h.status, 200)
                self.assertTrue(h.json['ok'])
                self.assertEqual(h.json['revision'], 7)
                self.assertEqual(h.json['deleted_uids'], [])
            self.assertEqual(paths[-1], G['TAK_MAP_GATEWAY_DATA_API_URL']+'/snapshot?since_revision=7')
            self.assertEqual(len(paths), 3)

    def test_replay_json_endpoints_and_query_contract_in_both_modes(self):
        for mode in ('none', 'certificate'):
            with self.subTest(mode=mode):
                os.environ['TAK_MAP_REPLAY_AUTH_MODE'] = mode
                if mode == 'certificate':
                    G['TAK_MAP_REPLAY_CLIENT_CERT'] = str(self.cert)
                    G['TAK_MAP_REPLAY_CLIENT_KEY'] = str(self.key)
                    G['TAK_MAP_REPLAY_CA_CERT'] = str(self.cert)
                    os.environ['TAK_MAP_REPLAY_CLIENT_CERT'] = str(self.cert)
                    os.environ['TAK_MAP_REPLAY_CLIENT_KEY'] = str(self.key)
                    os.environ['TAK_MAP_REPLAY_CA_CERT'] = str(self.cert)
                captured=[]
                def fake_open(req, *, context, timeout):
                    captured.append((req.full_url,context,timeout))
                    return FakeResponse(json.dumps({'ok':True,'periods':[{'id':'period-1'}], 'results':[], 'state':{'uid':'x'}}).encode())
                with mock.patch.object(G['_urlreq_v415'], 'urlopen', side_effect=fake_open):
                    for endpoint in ('health','capabilities','periods','manifest','events','search','state'):
                        h=FakeHandler()
                        G['_tak_v415_replay_proxy'](h, endpoint, 'period_id=period-1&limit=25')
                        self.assertEqual(h.status,200,endpoint)
                        self.assertEqual(h.json['periods'][0]['id'],'period-1')
                        self.assertEqual(captured[-1][0],G['TAK_MAP_REPLAY_API_URL']+'/'+endpoint+'?period_id=period-1&limit=25')
                        self.assertEqual(captured[-1][2],G['TAK_MAP_REPLAY_TIMEOUT'])
                self.assertEqual(len(captured),7)

    def test_replay_chunk_gzip_binary_and_headers_passthrough_both_modes(self):
        blob = gzip.compress(b'{"uid":"u1","time":"2026-11-03T19:00:00Z"}\n')
        hdrs={'Content-Type':'application/x-ndjson', 'Content-Encoding':'gzip',
              'X-TAKGW-Chunk-ID':'chunk-100', 'X-TAKGW-Chunk-Start':'start',
              'X-TAKGW-Chunk-End':'end','X-TAKGW-Sources':'adsb,pli'}
        for mode in ('none','certificate'):
            with self.subTest(mode=mode):
                os.environ['TAK_MAP_REPLAY_AUTH_MODE']=mode
                if mode=='certificate':
                    G['TAK_MAP_REPLAY_CLIENT_CERT'] = str(self.cert)
                    G['TAK_MAP_REPLAY_CLIENT_KEY'] = str(self.key)
                    G['TAK_MAP_REPLAY_CA_CERT'] = str(self.cert)
                    os.environ['TAK_MAP_REPLAY_CLIENT_CERT'] = str(self.cert)
                    os.environ['TAK_MAP_REPLAY_CLIENT_KEY'] = str(self.key)
                    os.environ['TAK_MAP_REPLAY_CA_CERT'] = str(self.cert)
                    os.environ['TAK_MAP_REPLAY_CLIENT_CERT'] = str(self.cert)
                    os.environ['TAK_MAP_REPLAY_CLIENT_KEY'] = str(self.key)
                    os.environ['TAK_MAP_REPLAY_CA_CERT'] = str(self.cert)
                with mock.patch.object(G['_urlreq_v415'], 'urlopen', return_value=FakeResponse(blob, headers=hdrs)):
                    h=FakeHandler()
                    G['_tak_v415_replay_proxy'](h,'chunk','id=chunk-100')
                    self.assertEqual(h.status,200)
                    self.assertEqual(h.wfile.getvalue(),blob)
                    self.assertEqual(h.headers['Content-Encoding'],'gzip')
                    self.assertEqual(h.headers['Content-Length'],str(len(blob)))
                    for key in ('X-TAKGW-Chunk-ID','X-TAKGW-Chunk-Start','X-TAKGW-Chunk-End','X-TAKGW-Sources'):
                        self.assertEqual(h.headers[key],hdrs[key])

    def test_replay_access_denial_no_fallback(self):
        os.environ['TAK_MAP_REPLAY_AUTH_MODE'] = 'none'
        import urllib.error
        def denied(req, *, context, timeout):
            raise urllib.error.HTTPError(req.full_url,403,'Forbidden',{},io.BytesIO(b'{"ok":false,"error":"Replay API read access denied."}'))
        with mock.patch.object(G['_urlreq_v415'], 'urlopen', side_effect=denied) as f:
            h=FakeHandler()
            G['_tak_v415_replay_proxy'](h,'periods')
            self.assertEqual(h.status,403)
            self.assertEqual(h.json['error'],'Replay API read access denied.')
            self.assertEqual(f.call_count,1)

    def test_browser_session_gate_still_protects_both_proxy_routes(self):
        import inspect
        replay_get=inspect.getsource(G['_v415_get'])
        gateway_get=inspect.getsource(G['_i475_resilience_get'])
        for src in (replay_get,gateway_get):
            self.assertIn('self._tak_map_auth_ok()', src)
            self.assertIn('self._require_tak_map_login()', src)


if __name__=='__main__':
    unittest.main(verbosity=2)
