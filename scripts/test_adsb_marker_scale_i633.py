#!/usr/bin/env python3
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]

def main():
    m=json.loads((ROOT/'assets/tak-map-deferred-i553.json').read_text())
    rows={x.get('id'):x.get('code','') for x in m['scripts']}
    owner=rows['v320AdsbSingleOwnerPatch']
    sidebar=rows['TakMapAdsbSidebarI610']
    sidebar_src=(ROOT/'assets/tak-map-adsb-sidebar-i610.js').read_text()
    interp=(ROOT/'assets/tak-map-live-interpolation-v491.js').read_text()
    source=(ROOT/'takmap.js').read_text()
    assert sidebar==sidebar_src, 'served sidebar drifted from source asset'
    # Initial marker and both v320 live refresh writers must preserve scale + origin.
    assert 'scale(.75);transform-origin:50% 50%' in owner
    assert owner.count("scale(.75)") >= 3, owner.count("scale(.75)")
    assert owner.count("transformOrigin='50% 50%'") >= 2
    assert "img.style.transform=`rotate(${p.heading}deg) scale(.75)`;img.style.transformOrigin='50% 50%'" in sidebar
    assert "el.style.transform='rotate('+deg+'deg) scale(.75)'" in interp
    assert "style=\"transform:rotate('+deg+'deg) scale(.75);transform-origin:50% 50%\"" in source
    # Reject known rotate-only aircraft image writers in served runtime.
    for sid in ('v320AdsbSingleOwnerPatch','TakMapAdsbSidebarI610','takMapLiveInterpolationLoaderV476'):
        code=rows[sid]
        for line in code.splitlines():
            if '.style.transform' in line and 'rotate' in line and 'match(/rotate' not in line:
                assert 'scale(.75)' in line, (sid,line)
                assert ('transformOrigin' in line or 'transform-origin' in line or sid=='takMapLiveInterpolationLoaderV476'), (sid,line)
    print('TAK Map i633 served ADS-B marker scale/origin regression passed')
    return 0
if __name__=='__main__': raise SystemExit(main())
