#!/usr/bin/env python3
"""Headless-browser gate for i624 Replay Jump to Date / Time."""
from __future__ import annotations
from pathlib import Path
import re, runpy, shutil

ROOT=Path(__file__).resolve().parents[1]


def main()->int:
    chromium=next((shutil.which(n) for n in ('chromium','chromium-browser','google-chrome','google-chrome-stable') if shutil.which(n)),None)
    if not chromium:
        print('SKIP: Chromium unavailable')
        return 0
    ns=runpy.run_path(str(ROOT/'tak_dashboard.py'),run_name='tak_map_i624_jump_browser')
    html=str(ns['TAK_MAP_HTML'])
    m=re.search(r'(<script id="v415ReplayModeIntegrationPatch">[\s\S]*?</script>)',html)
    assert m
    replay_script=m.group(1)
    for marker in ('replayJumpI624','replayJumpDateI624','replayJumpTimeI624','replayJumpGoI624'):
        assert marker in replay_script

    fixture=f'''<!doctype html><html><head><meta charset="utf-8"><style>
    html,body{{margin:0;background:#071018;color:#eee;font-family:Arial,sans-serif}}#sidebar{{width:396px;padding:8px}}.replay-v415-hidden{{display:none!important}}.replay-confirm-v415{{display:none}}
    </style></head><body><div id="sidebar"><div class="version-panel"><div class="version-product">TAK Map</div><span class="release-main">1.4.0</span><span class="iteration-chip">i624</span></div></div><div id="mapStatusBanner"></div>
    <script>
    window.__replayEventUrls=[];
    window.fetch=async function(input){{
      const u=String(input&&input.url||input||''); let body={{ok:true}};
      if(u.includes('/api/tak-map/replay/config')) body={{ok:true,configured:true}};
      else if(u.includes('/api/tak-map/config')) body={{ok:true,default_basemap:'test',basemaps:[{{id:'test',type:'xyz',url:'about:blank',options:{{}}}}]}};
      else if(u.includes('/api/tak-map/replay/periods')) body={{ok:true,periods:[{{id:'rp-stable-1',stable_id:'rp-stable-1',legacy_id:'legacy-1',start_utc:'2026-08-10T12:00:00Z',end_utc:'2026-08-10T12:20:00Z',duration_seconds:1200}}]}};
      else if(u.includes('/api/tak-map/replay/events')) {{window.__replayEventUrls.push(u);body={{ok:true,events:[]}};}}
      else if(u.includes('/api/tak-map/replay/search')) body={{ok:true,period_id:'rp-stable-1',stable_id:'rp-stable-1',period_start_utc:'2026-08-10T12:00:00Z',period_end_utc:'2026-08-10T12:20:00Z',results:[]}};
      return new Response(JSON.stringify(body),{{status:200,headers:{{'Content-Type':'application/json'}}}});
    }};
    function chain(){{return {{on(){{return this}},off(){{return this}},addTo(){{return this}},setView(){{return this}},invalidateSize(){{}},remove(){{}},removeLayer(){{}},addLayer(){{}},hasLayer(){{return false}},panTo(){{}},getCenter(){{return {{lat:34,lng:-118}}}},getZoom(){{return 9}},clearLayers(){{}},setLatLng(){{return this}},getLatLng(){{return {{lat:34,lng:-118}}}},bindPopup(){{return this}},getPopup(){{return null}},setPopupContent(){{return this}},openPopup(){{return this}},getElement(){{return null}}}}}}
    window.L={{map:()=>chain(),control:{{scale:()=>chain()}},layerGroup:()=>chain(),tileLayer:function(){{return chain()}},divIcon:()=>({{}}),marker:()=>chain(),polyline:()=>chain(),DomEvent:{{stopPropagation(){{}},preventDefault(){{}}}}}};
    window.L.tileLayer.wms=()=>chain();
    </script>{replay_script}</body></html>'''

    from playwright.sync_api import sync_playwright
    errors=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=chromium,args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
        context=browser.new_context(viewport={'width':1280,'height':760},timezone_id='UTC')
        page=context.new_page(); page.on('pageerror',lambda exc: errors.append(str(exc)))
        page.set_content(fixture,wait_until='domcontentloaded',timeout=20_000)
        page.wait_for_selector('#replayJumpDateI624',state='attached',timeout=7_000)
        initial=page.evaluate('''() => {const p=document.getElementById('replayPeriodV415').closest('.replay-select-field-v433'),j=document.getElementById('replayJumpI624'),s=document.getElementById('replaySearchI621');return {jumpAfterPeriod:p.nextElementSibling===j,searchAfterJump:j.nextElementSibling===s,dateDisabled:document.getElementById('replayJumpDateI624').disabled,timeDisabled:document.getElementById('replayJumpTimeI624').disabled,timeStep:document.getElementById('replayJumpTimeI624').step};}''')
        assert initial['jumpAfterPeriod'] and initial['searchAfterJump'],initial
        assert initial['dateDisabled'] and initial['timeDisabled'] and initial['timeStep']=='1',initial

        page.evaluate("() => document.getElementById('replayModeToggleV415').dispatchEvent(new Event('change',{bubbles:true}))")
        page.wait_for_function("document.getElementById('replayConfirmV415').style.display === 'grid'",timeout=5_000)
        page.click('#replayConfirmOkV415')
        page.wait_for_function("document.querySelectorAll('#replayPeriodV415 option').length >= 2",timeout=7_000)
        page.evaluate("() => {const s=document.getElementById('replayPeriodV415');s.value='rp-stable-1';s.dispatchEvent(new Event('change',{bubbles:true}))}")
        page.wait_for_function("document.getElementById('replayJumpGoI624').disabled === false",timeout=7_000)
        page.wait_for_timeout(250)
        state=page.evaluate('''() => ({date:document.getElementById('replayJumpDateI624').value,time:document.getElementById('replayJumpTimeI624').value,min:document.getElementById('replayJumpDateI624').min,max:document.getElementById('replayJumpDateI624').max,status:document.getElementById('replayJumpStatusI624').textContent,iteration:document.documentElement.dataset.takMapIteration})''')
        assert state['date']=='2026-08-10' and state['min']=='2026-08-10' and state['max']=='2026-08-10',state
        assert state['iteration']=='i624',state
        assert 'Ready to jump' in state['status'],state

        page.fill('#replayJumpDateI624','2026-08-10'); page.fill('#replayJumpTimeI624','12:10:30'); page.click('#replayJumpGoI624')
        target=1786363830000
        page.wait_for_function(f"window.getTakMapReplayDiagnosticsV415().currentMs === {target}",timeout=7_000)
        jumped=page.evaluate('''() => ({time:document.getElementById('replayJumpTimeI624').value,status:document.getElementById('replayJumpStatusI624').textContent,diag:window.getTakMapReplayDiagnosticsV415().replayJumpI624})''')
        assert jumped['time']=='12:10:30' and 'Replay remains paused' in jumped['status'],jumped
        assert jumped['diag']['secondsPrecision'] and jumped['diag']['outsideCurrentBuffer'],jumped

        page.click('#replayJumpForwardI624'); page.wait_for_function("document.getElementById('replayJumpTimeI624').value === '12:11:30'",timeout=5_000)
        page.click('#replayJumpBackI624'); page.wait_for_function("document.getElementById('replayJumpTimeI624').value === '12:10:30'",timeout=5_000)

        # Timeline scrubbing must keep date/time controls synchronized.
        page.evaluate("() => {const t=document.getElementById('replayTimelineV415');t.value='250';t.dispatchEvent(new Event('input',{bubbles:true}))}")
        page.wait_for_function("document.getElementById('replayJumpTimeI624').value === '12:05:00'",timeout=5_000)
        browser.close()
    assert not errors,errors
    print('TAK Map i624 Replay Jump DOM/browser contract passed')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
