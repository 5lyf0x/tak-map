#!/usr/bin/env python3
"""TAK Map i627 real backend Replay /state proxy forwarding regression."""
from pathlib import Path
import json, runpy

ROOT = Path(__file__).resolve().parents[1]

class FakeHeaders(dict):
    def get(self, key, default=None):
        return super().get(key, default)

class FakeResponse:
    status = 200
    headers = FakeHeaders({'Content-Type': 'application/json'})
    def __init__(self, payload):
        self.payload = payload
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self):
        return json.dumps(self.payload).encode('utf-8')

class DummyHandlerBase:
    def _tak_map_auth_ok(self):
        return True
    def _require_tak_map_login(self):
        raise AssertionError('unexpected login challenge')
    def _tak_map_session(self):
        return {'user':'test'}
    def _send_json(self, data, code=200):
        self.response = (int(code), data)
        return self.response


def main():
    ns = runpy.run_path(str(ROOT / 'tak_dashboard.py'), run_name='tak_map_i627_proxy_test')
    source = (ROOT / 'tak_dashboard.py').read_text()
    assert "allowed={'health','capabilities','periods','manifest','events','chunk','search','state'}" in source
    assert 'replay/(health|capabilities|periods|manifest|events|chunk|search|state)' in source

    proxy = ns['_tak_v415_replay_proxy']
    g = proxy.__globals__
    calls = []
    g['_tak_v415_replay_config_status'] = lambda: {'ok': True, 'configured': True}
    g['_tak_v415_replay_ssl_context'] = lambda: object()
    def fake_urlopen(req, context=None, timeout=None):
        calls.append({'url': req.full_url, 'timeout': timeout})
        return FakeResponse({
            'ok': True,
            'period_id': 'rp-long',
            'at_utc': '2026-08-09T21:01:00Z',
            'object_count': 3,
            'events': [],
        })
    g['_urlreq_v415'].urlopen = fake_urlopen

    Handler = ns['Handler']
    class ReplayProxyHandler(DummyHandlerBase, Handler):
        pass
    handler = ReplayProxyHandler.__new__(ReplayProxyHandler)
    handler.path = '/api/tak-map/replay/state?period_id=rp-long&at=2026-08-09T21%3A01%3A00Z'
    handler.response = None
    handler.headers = {}
    ReplayProxyHandler.do_GET(handler)
    assert handler.response is not None, 'HTTP handler returned no response'
    code, payload = handler.response
    assert code == 200, handler.response
    assert payload.get('ok') is True and payload.get('period_id') == 'rp-long', payload
    assert len(calls) == 1, calls
    assert calls[0]['url'].startswith('https://127.0.0.1:9443/api/replay/v1/state?'), calls
    assert 'period_id=rp-long' in calls[0]['url'] and 'at=2026-08-09T21%3A01%3A00Z' in calls[0]['url'], calls

    cfg = ns['tak_map_config']()
    feature = cfg.get('replay_proxy_i627') or {}
    assert feature.get('state_endpoint_forwarded') is True
    assert feature.get('real_backend_proxy_regression') is True
    print('TAK Map i627 real backend Replay /state proxy forwarding regression passed')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
