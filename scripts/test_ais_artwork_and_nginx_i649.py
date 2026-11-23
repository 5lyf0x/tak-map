#!/usr/bin/env python3
"""i649: retained AIS assets, authoritative tactical rendering, Nginx origin preservation."""
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1]
js=(R/'assets/tak-map-gateway-data-v491.js').read_text()
py=(R/'tak_dashboard.py').read_text()
installer=(R/'install.sh').read_text()
for name in ('ais-civil.png','ais-law.png'):
    path=R/'assets'/name
    assert path.is_file(),name
    with Image.open(path) as asset:
        assert asset.size==(64,64),(name,asset.size)
        assert asset.mode=='RGBA',name
assert "if(src==='ais_vessels'){const icon=aisIconProfile(feature)" not in js
assert "takmap:milstd-catalog-ready" in js
assert "function resolveAisTacticalSymbol(" in js
assert 'width="20" height="20" alt=""' in py
for n in ('ais-civil.png','ais-law.png'):
    assert f'install -m 0644 assets/{n}' in installer
for name in ('tak-map-https-9444.conf','tak-map-https-9444.conf.example'):
    conf=(R/'nginx'/name).read_text()
    assert 'proxy_set_header Host $http_host;' in conf,name
    assert 'proxy_set_header Host $host;' not in conf,name
assert "origin.netloc.lower()==handler.headers.get('Host','').strip().lower()" in py
print('PASS: i649 retained 64px AIS assets, registry-only Gateway icons, port-aware origin proxy')
