#!/usr/bin/env python3
import importlib.util
import os
import tempfile
import threading
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / 'assets' / 'tak-map-gateway-data-v491.js'


def load_dashboard(data_dir: Path):
    os.environ['TAK_DASHBOARD_DATA_DIR'] = str(data_dir)
    os.environ['TAK_DASHBOARD_BIND'] = '127.0.0.1'
    os.environ['TAK_DASHBOARD_PORT'] = '0'
    spec = importlib.util.spec_from_file_location('tak_dashboard_i523_ais_test', ROOT / 'tak_dashboard.py')
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_asset_routes(module) -> None:
    server = ThreadingHTTPServer(('127.0.0.1', 0), module.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{server.server_address[1]}'
    try:
        for name, expected_size in [('ais-civil.png', (20, 22)), ('ais-law.png', (27, 27))]:
            with urlopen(f'{base}/assets/{name}', timeout=10) as response:
                body = response.read()
                assert response.status == 200
                assert response.headers.get_content_type() == 'image/png'
                assert int(response.headers['Content-Length']) == len(body)
                assert body == (ROOT / 'assets' / name).read_bytes()
            request = Request(f'{base}/assets/{name}', method='HEAD')
            with urlopen(request, timeout=10) as response:
                assert response.status == 200
                assert response.headers.get_content_type() == 'image/png'
                assert int(response.headers['Content-Length']) == (ROOT / 'assets' / name).stat().st_size
                assert response.read() == b''
        connection = HTTPConnection('127.0.0.1', server.server_address[1], timeout=10)
        connection.request('GET', '/assets/ais-unknown.png')
        response = connection.getresponse()
        response.read()
        assert response.status in (302, 404)
        assert response.getheader('Content-Type') != 'image/png'
        connection.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=10)


def main() -> None:
    assert (ROOT / 'VERSION').read_text().strip() == '1.3.0-i616'
    text = JS.read_text()
    assert "const V='i616',POLL_MS=300000;" in text
    assert 'function aisIconProfile(feature)' in text
    assert 'icon_variant' in text
    assert '/assets/ais-civil.png' in text
    assert '/assets/ais-law.png' in text
    assert 'gateway-data-ais-native-v523' in text
    assert 'transform:rotate(${course}deg)' not in text
    assert 'course=Number(p.course' not in text
    assert 'iconSize:[icon.width,icon.height]' in text
    assert 'iconAnchor:[icon.width/2,icon.height/2]' in text
    for name, size in [('ais-civil.png', (20, 22)), ('ais-law.png', (27, 27))]:
        path = ROOT / 'assets' / name
        assert path.is_file()
        with Image.open(path) as image:
            assert image.size == size
            assert image.mode == 'RGBA'
        assert path.stat().st_size < 4096
    installer = (ROOT / 'install.sh').read_text()
    assert 'Installing required TAK Map HTTPS dependency: nginx' in installer
    assert 'assets/ais-civil.png' in installer
    assert 'assets/ais-law.png' in installer
    dashboard = (ROOT / 'tak_dashboard.py').read_text()
    assert "r'^/assets/(ais-(?:civil|law)\\.png)$'" in dashboard
    assert "self.send_header('Content-Type','image/png')" in dashboard
    assert "if self.command != 'HEAD':" in dashboard
    sidebar = (ROOT / 'assets' / 'tak-map-sidebar-performance-v491.js').read_text()
    assert "const VERSION='i602';" in sidebar
    with tempfile.TemporaryDirectory(prefix='tak-map-i525-ais-route-') as tmp:
        module = load_dashboard(Path(tmp))
        test_asset_routes(module)
    print('TAK Map i525 preservation of i523 AIS native icon route, five-minute polling, and Nginx tests passed')


if __name__ == '__main__':
    main()
