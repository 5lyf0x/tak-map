#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import io
import json
import os
import tempfile
from pathlib import Path
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / 'tak_dashboard.py'
ASSET = ROOT / 'assets' / 'tak-map-nrt-satellite-i535.js'
CATALOG_SEARCH = 'https://sh.dataspace.copernicus.eu/catalog/v1/search'


def load_dashboard(data_dir: Path):
    os.environ['TAK_DASHBOARD_DATA_DIR'] = str(data_dir)
    os.environ['TAK_DASHBOARD_BIND'] = '127.0.0.1'
    os.environ['TAK_DASHBOARD_PORT'] = '0'
    spec = importlib.util.spec_from_file_location('tak_dashboard_i536_sentinel_test', DASHBOARD)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def http_error(code: int, body: bytes = b'{"code":406,"description":"HTTP 406 Not Acceptable"}') -> HTTPError:
    return HTTPError(CATALOG_SEARCH, code, 'fixture', {}, io.BytesIO(body))


def main() -> int:
    source = DASHBOARD.read_text(encoding='utf-8')
    js = ASSET.read_text(encoding='utf-8')

    assert (ROOT / 'VERSION').read_text().strip() == '1.3.0-i537'
    assert source.count("if __name__=='__main__':") == 1
    assert source.rstrip().endswith("if __name__=='__main__':\n    main()")
    assert source.rfind('# --- TAK Map i536 Sentinel Hub Catalog response negotiation ---') < source.rfind("if __name__=='__main__':")
    assert "const VERSION = 'i536'" in js
    assert "const VERSION='i537';" in (ROOT / 'assets' / 'tak-map-sidebar-performance-v491.js').read_text(encoding='utf-8')

    for token in (
        "'application/geo+json, application/json'",
        "'application/geo+json'",
        "'*/*'",
        'request_content_type',
        'response_accept_attempts',
        'Sentinel Hub Catalog API request failed',
    ):
        assert token in source, token

    with tempfile.TemporaryDirectory(prefix='tak-map-i536-sentinel-') as tmp:
        module = load_dashboard(Path(tmp))
        g = module._i535_json_with_refresh.__globals__
        assert module.TAK_MAP_ITERATION == 'i537'
        cfg = module.tak_map_config()
        assert cfg['tak_map_iteration'] == 'i537'
        assert cfg['version'] == '1.3.0-i537'
        assert cfg['nrt_satellite_imagery']['version'] == 'i536'
        assert cfg['nrt_satellite_imagery']['sentinel_catalog_response_negotiation'] == [
            'application/geo+json, application/json',
            'application/geo+json',
            '*/*',
        ]

        session = {'auth_mode': 'ots-user', 'username': 'raptor', 'profile': {'identity_key': 'ots:raptor'}}
        g['_i535_user_token'] = lambda sess, force=False: 'fixture-token-refresh' if force else 'fixture-token'

        # Preferred Catalog search response negotiation succeeds on the first request.
        calls = []
        def preferred_api(url, token, method='GET', payload=None, accept='application/json'):
            calls.append((url, token, method, payload, accept))
            return 200, {'Content-Type': 'application/geo+json'}, json.dumps({'type': 'FeatureCollection', 'features': []}).encode()
        g['_i535_api_request'] = preferred_api
        value = g['_i535_json_with_refresh'](session, CATALOG_SEARCH, 'POST', {'collections': ['sentinel-2-l2a']})
        assert value['type'] == 'FeatureCollection'
        assert calls == [(CATALOG_SEARCH, 'fixture-token', 'POST', {'collections': ['sentinel-2-l2a']}, 'application/geo+json, application/json')]

        # HTTP 406 on the preferred header retries with GeoJSON-only and then succeeds.
        calls.clear()
        def fallback_api(url, token, method='GET', payload=None, accept='application/json'):
            calls.append(accept)
            if len(calls) == 1:
                raise http_error(406)
            return 200, {'Content-Type': 'application/geo+json'}, b'{"type":"FeatureCollection","features":[]}'
        g['_i535_api_request'] = fallback_api
        value = g['_i535_json_with_refresh'](session, CATALOG_SEARCH, 'POST', {'collections': ['sentinel-2-l2a']})
        assert value['features'] == []
        assert calls == ['application/geo+json, application/json', 'application/geo+json']

        # A JSON endpoint outside Catalog search preserves the i535 JSON request path.
        delegated = []
        g['_i536_json_with_refresh_before'] = lambda sess, url, method='GET', payload=None: delegated.append((url, method, payload)) or {'ok': True}
        result = g['_i535_json_with_refresh'](session, 'https://sh.dataspace.copernicus.eu/catalog/v1/collections/sentinel-2-l2a')
        assert result == {'ok': True}
        assert delegated == [('https://sh.dataspace.copernicus.eu/catalog/v1/collections/sentinel-2-l2a', 'GET', None)]

        # Exhausted content negotiation produces actionable diagnostics.
        attempts = []
        def rejected_api(url, token, method='GET', payload=None, accept='application/json'):
            attempts.append(accept)
            raise http_error(406)
        g['_i535_api_request'] = rejected_api
        try:
            g['_i535_json_with_refresh'](session, CATALOG_SEARCH, 'POST', {'collections': ['sentinel-2-l2a']})
            raise AssertionError('expected Catalog 406 failure')
        except RuntimeError as exc:
            message = str(exc)
            assert 'HTTP 406' in message
            assert 'endpoint=' + CATALOG_SEARCH in message
            assert 'method=POST' in message
            assert 'request_content_type=application/json' in message
            assert 'application/geo+json, application/json' in message
            assert '*/*' in message
        assert attempts == ['application/geo+json, application/json', 'application/geo+json', '*/*']

    print('i536 Sentinel Hub Catalog response negotiation and diagnostics assertions passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
