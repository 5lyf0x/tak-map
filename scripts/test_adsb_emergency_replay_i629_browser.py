#!/usr/bin/env python3
from pathlib import Path
import json, runpy, shutil
ROOT=Path(__file__).resolve().parents[1]

def extract_function(src,name):
    start=src.index('function '+name+'(')
    brace=src.index('{',start); depth=0; quote=None; esc=False; template=False
    i=brace
    while i<len(src):
        c=src[i]
        if quote:
            if esc: esc=False
            elif c=='\\': esc=True
            elif c==quote: quote=None
        elif template:
            if esc: esc=False
            elif c=='\\': esc=True
            elif c=='`': template=False
        else:
            if c in ('\"',"'"): quote=c
            elif c=='`': template=True
            elif c=='{': depth+=1
            elif c=='}':
                depth-=1
                if depth==0: return src[start:i+1]
        i+=1
    raise ValueError(name)

def main():
    chromium=next((shutil.which(n) for n in ('chromium','chromium-browser','google-chrome','google-chrome-stable') if shutil.which(n)),None)
    if not chromium:
        print('SKIP: Chromium unavailable'); return 0
    manifest=json.loads((ROOT/'assets/tak-map-deferred-i553.json').read_text())
    owner=next(x['code'] for x in manifest['scripts'] if x.get('id')=='v320AdsbSingleOwnerPatch')
    ns=runpy.run_path(str(ROOT/'tak_dashboard.py'),run_name='i629_replay_emergency_browser_source')
    rs=ns['_I629_REPLAY_SCRIPT']
    funcs='\n'.join(extract_function(rs,n) for n in ('parseRecord','replayAircraftData','replayIconSignature'))
    html='''<!doctype html><html><head><meta charset="utf-8"></head><body><div id="statusDropdown"></div>
<input id="adsbFilterCivil" type="checkbox" checked><input id="adsbFilterMilitary" type="checkbox" checked><input id="adsbFilterGovt" type="checkbox" checked><input id="adsbFilterUnknown" type="checkbox" checked>
<script>try{localStorage.setItem('takmap.adsb.localDisabled','1')}catch(_){};window.state={live:{adsb_aircraft:false}};window.L={divIcon:o=>({options:o}),layerGroup:()=>({addTo(){return this}})};</script>
<script>'''+owner+'''</script><script>'''+funcs+'''\nwindow.__i629ParseRecord=parseRecord;window.__i629ReplayAircraftData=replayAircraftData;window.__i629ReplayIconSignature=replayIconSignature;</script></body></html>'''
    emergency_cot='''<event version="2.0" uid="TAKGATE-ADSB-V31-A0A8DE" type="a-f-A" time="2026-08-09T05:55:57.184Z" start="2026-08-09T05:55:57.184Z" stale="2026-08-09T05:57:07.184Z"><point lat="33.941446" lon="-118.390875" hae="1623" ce="10" le="10"/><detail><contact callsign="UAL3926"/><track course="263" speed="121.5"/><takgateway_adsb hex="A0A8DE" flight="UAL3926" registration="N14106" emergency="true"/><color argb="-65536" value="#FF0000"/><strokeColor value="#FF0000"/><fillColor value="#FF0000"/></detail></event>'''
    normal_cot=emergency_cot.replace(' emergency="true"',' emergency="false"').replace('<color argb="-65536" value="#FF0000"/><strokeColor value="#FF0000"/><fillColor value="#FF0000"/>','')
    from playwright.sync_api import sync_playwright
    errors=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=chromium,args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
        page=browser.new_page(); page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content(html,wait_until='domcontentloaded',timeout=15000)
        page.wait_for_function("typeof window.aircraftIcon==='function' && typeof window.__i629ParseRecord==='function'",timeout=8000)
        out=page.evaluate("""({ec,nc})=>{
          const er=window.__i629ParseRecord({uid:'TAKGATE-ADSB-V31-A0A8DE',source:'adsb',recorded_at:'2026-08-09T05:55:57.184Z',cot:ec});
          const nr=window.__i629ParseRecord({uid:'TAKGATE-ADSB-V31-A0A8DE',source:'adsb',recorded_at:'2026-08-09T05:55:47.184Z',cot:nc});
          const ed=window.__i629ReplayAircraftData(er), nd=window.__i629ReplayAircraftData(nr);
          return {er:{emergency:er.emergency,color:er.emergencyColor,squawk:er.squawk},nr:{emergency:nr.emergency,color:nr.emergencyColor},ed:ed,nd:nd,emergencyHtml:window.aircraftIcon(ed).options.html,normalHtml:window.aircraftIcon(nd).options.html,esig:window.__i629ReplayIconSignature(er),nsig:window.__i629ReplayIconSignature(nr)};
        }""",{'ec':emergency_cot,'nc':normal_cot})
        browser.close()
    assert out['er']['emergency'] is True and out['er']['color']=='#FF0000',out
    assert out['nr']['emergency'] is False,out
    assert out['ed']['emergency'] is True and out['ed']['emergency_color']=='#FF0000',out
    assert '/assets/adsb/adsb_emergency_' in out['emergencyHtml'],out
    assert '/assets/adsb/adsb_' in out['normalHtml'] and 'adsb_emergency_' not in out['normalHtml'],out
    assert out['esig']!=out['nsig'] and 'emergency' in out['esig'] and 'normal' in out['nsig'],out
    fatal=[e for e in errors if any(x in e.lower() for x in ('syntaxerror','maximum call stack','too much recursion'))]
    assert not fatal,fatal
    print('TAK Map i629 Replay UAL3926 emergency metadata -> red icon browser regression passed')
    return 0
if __name__=='__main__': raise SystemExit(main())
