#!/usr/bin/env python3
from pathlib import Path
import json, shutil
ROOT=Path(__file__).resolve().parents[1]

def main():
    chromium=next((shutil.which(n) for n in ('chromium','chromium-browser','google-chrome','google-chrome-stable') if shutil.which(n)),None)
    if not chromium:
        print('SKIP: Chromium unavailable'); return 0
    manifest=json.loads((ROOT/'assets/tak-map-deferred-i553.json').read_text())
    code=next(x['code'] for x in manifest['scripts'] if x.get('id')=='v320AdsbSingleOwnerPatch')
    html='''<!doctype html><html><head><meta charset="utf-8"></head><body>
<div id="statusDropdown"></div><input id="adsbFilterCivil" type="checkbox" checked><input id="adsbFilterMilitary" type="checkbox" checked><input id="adsbFilterGovt" type="checkbox" checked><input id="adsbFilterUnknown" type="checkbox" checked>
<script>
try{localStorage.setItem('takmap.adsb.localDisabled','1')}catch(_){};window.state={live:{adsb_aircraft:false}};
window.L={divIcon:o=>({options:o}),layerGroup:()=>({addTo(){return this}})};
</script><script>'''+code+'''</script></body></html>'''
    from playwright.sync_api import sync_playwright
    errors=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=chromium,args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
        page=browser.new_page(); page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content(html,wait_until='domcontentloaded',timeout=15000)
        page.wait_for_function("typeof window.aircraftIcon==='function'",timeout=8000)
        out=page.evaluate("""()=>{
          const base={id:'A0A8DE',lat:33.9,lon:-118.3,callsign:'UAL3926',category:'civil'};
          const html=x=>window.aircraftIcon(Object.assign({},base,x)).options.html;
          return {
            normal:html({emergency:false}),
            emergency:html({emergency:true}),
            cleared:html({emergency:false}),
            squawk7700:html({emergency:false,squawk:'7700'}),
            gatewayRed:html({emergency:false,emergency_color:'#FF0000'}),
          };
        }""")
        browser.close()
    assert 'adsb_civ_fixed.png' in out['normal'] and 'adsb_emergency_' not in out['normal'],out
    assert 'adsb_emergency_civ_fixed.png' in out['emergency'],out
    assert 'adsb_civ_fixed.png' in out['cleared'] and 'adsb_emergency_' not in out['cleared'],out
    assert 'adsb_emergency_civ_fixed.png' in out['squawk7700'],out
    assert 'adsb_emergency_civ_fixed.png' in out['gatewayRed'],out
    fatal=[e for e in errors if any(x in e.lower() for x in ('syntaxerror','maximum call stack','too much recursion'))]
    assert not fatal,fatal
    print('TAK Map i629 live ADS-B emergency normal -> red -> normal browser regression passed')
    return 0
if __name__=='__main__': raise SystemExit(main())
