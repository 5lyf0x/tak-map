#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / 'tak_dashboard.py'
ASSET = ROOT / 'assets' / 'tak-map-nrt-satellite-i535.js'
ROUTE = '/assets/runtime/tak-map-nrt-satellite-i535.js'
PRODUCTS = {
    'true_color', 'false_color', 'swir', 'ndvi', 'ndre', 'ndmi', 'ndwi', 'mndwi',
    'nbr', 'ndsi', 'ndbi', 'bare_soil', 'scl', 'cloud_mask', 'cloud_probability',
}


def load_dashboard(data_dir: Path):
    os.environ['TAK_DASHBOARD_DATA_DIR'] = str(data_dir)
    os.environ['TAK_DASHBOARD_BIND'] = '127.0.0.1'
    os.environ['TAK_DASHBOARD_PORT'] = '0'
    spec = importlib.util.spec_from_file_location('tak_dashboard_i535_sentinel_test', DASHBOARD)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_asset_route(module) -> None:
    server = ThreadingHTTPServer(('127.0.0.1', 0), module.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{server.server_address[1]}'
    try:
        expected = ASSET.read_bytes()
        with urlopen(base + ROUTE, timeout=10) as response:
            assert response.status == 200
            assert response.headers.get_content_type() == 'application/javascript'
            assert response.headers['X-TAK-Map-Module'] == 'i535-sentinel-hub'
            assert response.read() == expected
        with urlopen(Request(base + ROUTE, method='HEAD'), timeout=10) as response:
            assert response.status == 200
            assert response.read() == b''
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=10)


def main() -> int:
    source = DASHBOARD.read_text(encoding='utf-8')
    js = ASSET.read_text(encoding='utf-8')
    installer = (ROOT / 'install.sh').read_text(encoding='utf-8')
    sidebar = (ROOT / 'assets' / 'tak-map-sidebar-performance-v491.js').read_text(encoding='utf-8')

    assert (ROOT / 'VERSION').read_text().strip() == '1.3.0-i537'
    assert source.count("if __name__=='__main__':") == 1
    assert source.rstrip().endswith("if __name__=='__main__':\n    main()")
    assert source.rfind('# --- TAK Map i535') < source.rfind("if __name__=='__main__':")
    assert "const VERSION='i537';" in sidebar

    assert ASSET.is_file()
    assert "const VERSION = 'i536'" in js
    assert "sentinel2_cdse" in js
    assert "Copernicus Sentinel-2 L2A" in js
    assert "/api/tak-map/sentinel-hub/search" in js
    assert "/api/tak-map/sentinel-hub/tile/" in js
    assert "requiresPerUserCredentials: true" in js
    assert 'takSentinelClientIdI535' not in js and 'takSentinelClientSecretI535' not in js
    for product in PRODUCTS:
        assert product + ':' in js or product == 'scl', product
    for label in ('True Color', 'False Color · Vegetation', 'SWIR Composite', 'NDVI', 'NDRE',
                  'NDMI / NDII', 'NDWI', 'MNDWI', 'NBR / Burn Scar', 'NDSI', 'NDBI',
                  'Bare Soil', 'Scene Classification', 'Cloud Mask', 'Cloud Probability'):
        assert label in js, label

    assert 'assets/tak-map-nrt-satellite-i535.js' in installer
    assert '$APP_DIR/assets/tak-map-nrt-satellite-i535.js' in installer
    assert '"$DATA_DIR/sentinel_hub_users"' in installer
    assert '"$DATA_DIR/sentinel_hub_cache"' in installer
    assert 'chmod 0700 "$DATA_DIR/ots_user_credentials" "$DATA_DIR/sentinel_hub_users"' in installer
    assert 'chmod 0750 "$DATA_DIR/sentinel_hub_cache"' in installer

    for token in (
        "_I535_TOKEN_ENDPOINT = 'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'",
        "_I535_CATALOG_BASE = 'https://sh.dataspace.copernicus.eu/catalog/v1'",
        "_I535_PROCESS_ENDPOINT = 'https://sh.dataspace.copernicus.eu/api/v1/process'",
        "'credential_scope': 'current-authenticated-user-only'",
        "'shared_credential_fallback': False",
        "'secret_returned_to_browser': False",
        "tak-sentinel-modal-i535{position:fixed;inset:0;z-index:50000",
        ".tak-account-menu-v511{z-index:30020!important}",
        "Configure Sentinel Hub",
        "Test Connection",
        "Replace Credentials",
        "Remove Credentials",
    ):
        assert token in source, token

    with tempfile.TemporaryDirectory(prefix='tak-map-i535-sentinel-') as tmp:
        module = load_dashboard(Path(tmp))
        g = module._i535_public_status.__globals__
        assert module.TAK_MAP_ITERATION == 'i537'
        cfg = module.tak_map_config()
        assert cfg['tak_map_iteration'] == 'i537'
        assert cfg['version'] == '1.3.0-i537'
        nrt = cfg['nrt_satellite_imagery']
        assert nrt['version'] == 'i536'
        assert nrt['sources'][0] == 'sentinel2_cdse'
        assert nrt['sentinel_2_l2a'] is True
        assert nrt['sentinel_hub_catalog_api'] is True
        assert nrt['sentinel_hub_process_api'] is True
        assert nrt['per_user_oauth_credentials'] is True
        assert nrt['shared_credential_fallback'] is False
        assert nrt['server_side_secret_only'] is True
        assert {row['id'] for row in nrt['sentinel_products']} == PRODUCTS
        assert cfg['account_menu']['renders_above_toolbar'] is True
        assert cfg['account_menu']['sentinel_hub_button'] is True
        assert cfg['account_menu']['sentinel_hub_modal'] is True
        assert module.TAK_MAP_HTML.count('takMapNrtSatelliteLoaderI535') == 1
        assert module.TAK_MAP_HTML.count('takMapSentinelHubI535') == 1
        assert ROUTE in module.TAK_MAP_HTML
        assert 'Configure Sentinel Hub' in module.TAK_MAP_HTML
        assert 'tak-sentinel-modal-i535' in module.TAK_MAP_HTML
        assert 'client_secret_encrypted' not in module.TAK_MAP_HTML
        assert 'takMapNrtSatelliteLoaderI535' not in module.TAK_MAP_LOGIN_HTML
        test_asset_route(module)

        user_a = {
            'auth_mode': 'ots-user', 'username': 'darktek',
            'profile': {'identity_key': 'ots:darktek', 'username': 'darktek'},
        }
        user_b = {
            'auth_mode': 'ots-user', 'username': 'slyfox',
            'profile': {'identity_key': 'ots:slyfox', 'username': 'slyfox'},
        }
        status = g['_i535_public_status'](user_a)
        assert status['ok'] is True
        assert status['configured'] is False
        assert status['credential_valid'] is False
        assert status['shared_credential_fallback'] is False
        assert status['secret_returned_to_browser'] is False

        g['_i535_test_credentials'] = lambda client_id, client_secret, cache_key='': {
            'ok': True, 'collection': 'sentinel-2-l2a', 'title': 'Sentinel-2 L2A'
        }
        client_id = 'fixture-client-id-123456'
        client_secret = 'fixture-client-secret-not-real-123456'
        saved = g['_i535_save_credentials'](user_a, client_id, client_secret)
        assert saved['ok'] and saved['configured'] and saved['verified']
        assert client_secret not in json.dumps(saved)
        assert client_id not in json.dumps(saved)
        loaded = g['_i535_load_credentials'](user_a)
        assert loaded['client_id'] == client_id
        assert loaded['client_secret'] == client_secret
        assert not g['_i535_load_credentials'](user_b)['configured']
        path_a = g['_i535_user_paths'](user_a)['credential']
        path_b = g['_i535_user_paths'](user_b)['credential']
        assert path_a != path_b and path_a.is_file() and not path_b.exists()
        raw = path_a.read_text(encoding='utf-8')
        assert client_id not in raw and client_secret not in raw
        assert path_a.stat().st_mode & 0o777 == 0o600

        # Catalog aggregation is current-area and per-user without calling the network.
        g['_i535_catalog_features'] = lambda sess, bbox, start, end, cloud: [
            {'id': 'A', 'properties': {'datetime': '2026-07-24T18:00:00Z', 'eo:cloud_cover': 12, 'platform': 'sentinel-2a'}},
            {'id': 'B', 'properties': {'datetime': '2026-07-24T20:00:00Z', 'eo:cloud_cover': 8, 'platform': 'sentinel-2b'}},
            {'id': 'C', 'properties': {'datetime': '2026-07-19T19:00:00Z', 'eo:cloud_cover': 20, 'platform': 'sentinel-2a'}},
        ]
        searched = g['_i535_search_scenes'](user_a, {'bbox': [-118.5, 33.5, -117.5, 34.5], 'days': 30, 'max_cloud': 35})
        assert searched['ok'] and searched['collection'] == 'sentinel-2-l2a'
        assert searched['scenes'][0]['date'] == '2026-07-24'
        assert searched['scenes'][0]['latest_acquisition'].startswith('2026-07-24T20:00:00')
        assert searched['scenes'][0]['cloud_cover'] == 8
        assert searched['shared_credential_fallback'] is False
        assert len(g['_i535_search_bbox']([170, -10, -170, 10])) == 2

        # Process request uses the selected product and current tile bounds; no user secret is placed in the request.
        captured = {}
        g['_i535_user_token'] = lambda sess, force=False: 'fixture-token'
        def fake_api(url, token, method='GET', payload=None, accept='application/json'):
            captured.update({'url': url, 'token': token, 'method': method, 'payload': payload, 'accept': accept})
            return 200, {}, b'\x89PNG\r\n\x1a\nfixture'
        g['_i535_api_request'] = fake_api
        tile, cached = g['_i535_process_tile'](user_a, 5, 5, 12, '2026-07-24', 'ndvi', 35)
        assert tile.startswith(b'\x89PNG') and cached is False
        assert captured['url'].endswith('/api/v1/process')
        assert captured['method'] == 'POST' and captured['accept'] == 'image/png'
        assert captured['payload']['input']['data'][0]['type'] == 'sentinel-2-l2a'
        assert captured['payload']['input']['data'][0]['dataFilter']['maxCloudCoverage'] == 35
        assert captured['payload']['evalscript'] == g['_I535_EVALSCRIPTS']['ndvi']
        assert client_secret not in json.dumps(captured['payload'])

        removed = g['_i535_remove_credentials'](user_a)
        assert removed['ok'] and removed['configured'] is False
        assert not path_a.exists()

    print('i536 preserved Sentinel Hub per-user credentials, products, NRT rendering, and account-layer assertions passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
