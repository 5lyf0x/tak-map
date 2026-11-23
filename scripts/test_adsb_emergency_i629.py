#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import json, runpy
ROOT=Path(__file__).resolve().parents[1]
def main():
    m=json.loads((ROOT/'assets/tak-map-deferred-i553.json').read_text())
    owner=next(x['code'] for x in m['scripts'] if x.get('id')=='v320AdsbSingleOwnerPatch')
    for marker in ('function emergencyState(a)',"['7500','7600','7700']",'adsb_emergency_',"path=iconPath(a)","popupField('Emergency','YES')",'const path=iconPath(a)'):
        assert marker in owner,marker
    for cls in ('civ','gov','mil'):
        for shape in ('fixed','helo'):
            p=ROOT/'assets'/'adsb'/f'adsb_emergency_{cls}_{shape}.png'
            assert p.is_file(),p
            im=Image.open(p).convert('RGBA')
            visible=[px for px in im.getdata() if px[3]>0]
            assert visible and max(px[0] for px in visible)>150,p
            assert max(px[1] for px in visible)==0 and max(px[2] for px in visible)==0,p
    ns=runpy.run_path(str(ROOT/'tak_dashboard.py'),run_name='i629_emergency_contract')
    s=ns['_I629_REPLAY_SCRIPT']
    for marker in ("meta('emergency')","meta('squawk')",'#FF0000',"emergency:!!e.emergency", "e?.emergency?'emergency':'normal'",'Emergency</b><span style="color:#FF0000'):
        assert marker in s,marker
    print('TAK Map i629 ADS-B emergency live/Replay contract passed')
    return 0
if __name__=='__main__': raise SystemExit(main())
