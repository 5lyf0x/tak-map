#!/usr/bin/env python3
"""TAK Map i647 AIS source/appearance/port-preservation checks."""
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
js=(ROOT/'assets/tak-map-gateway-data-v491.js').read_text()
py=(ROOT/'tak_dashboard.py').read_text()
installer=(ROOT/'install.sh').read_text()
for name in ('ais-civil.png','ais-law.png'):
    path=ROOT/'assets'/name
    assert path.is_file(),name
    with Image.open(path) as asset:
        assert asset.size==(64,64),(name,asset.size)
        assert asset.mode=='RGBA',name
assert "return law?{src:'/assets/ais-law.png',width:12,height:12,variant:'law'}:{src:'/assets/ais-civil.png',width:12,height:12,variant:'civil'}" in js
assert 'iconSize:[icon.width,icon.height]' in js
assert 'iconAnchor:[icon.width/2,icon.height/2]' in js
assert 'width="20" height="20" alt=""' in py
assert 'install -m 0644 assets/ais-civil.png' in installer
assert 'install -m 0644 assets/ais-law.png' in installer
for name in ('tak-map-https-9444.conf','tak-map-https-9444.conf.example'):
    conf=(ROOT/'nginx'/name).read_text()
    assert 'proxy_set_header Host $http_host;' in conf,name
    assert 'proxy_set_header Host $host;' not in conf,name
assert "origin.netloc.lower()==handler.headers.get('Host','').strip().lower()" in py
print('PASS: i647 ship assets (64x64), 12x12 map markers, preserved origin validation and port-aware nginx proxy')
