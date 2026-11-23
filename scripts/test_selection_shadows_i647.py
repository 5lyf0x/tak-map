#!/usr/bin/env python3
from pathlib import Path
import json
from PIL import Image
R=Path(__file__).resolve().parents[1]
J=(R/'assets/tak-map-gateway-data-v491.js').read_text()
S=(R/'assets/tak-map-adsb-sidebar-i610.js').read_text()
D=json.loads((R/'assets/tak-map-deferred-i553.json').read_text())
assert D['version']=='1.4.0-i647'
assert next(r['code'] for r in D['scripts'] if r['id']=='TakMapAdsbSidebarI610')==S
assert next(r['code'] for r in D['scripts'] if r['id']=='takMapGatewayDataLoaderV476')==J
assert '.gateway-data-selected-i614.gateway-data-ais-native-v523 img{filter:drop-shadow(0 0 3px rgba(255,48,48,.98))' in J
assert '.gateway-data-marker-v491.gateway-data-ais-native-v523 .gdm{filter:none!important}' in J
assert "el.classList.toggle('tak-adsb-selected-i647',selected.has(markerId))" in S
assert 'filter:drop-shadow(0 0 3px rgba(255,255,255,.98))' in S
assert "ownerOp||'Not reported'" in S
for n in ('ais-civil.png','ais-law.png'):
    with Image.open(R/'assets'/n) as im:
        assert im.size==(64,64) and im.mode=='RGBA'
        assert im.getpixel((0,0))[3]==0
        assert im.getpixel((32,32))[3]==255
print('PASS: i647 asset, no unselected AIS shadow, selected red AIS / white ADS-B, owner row')
