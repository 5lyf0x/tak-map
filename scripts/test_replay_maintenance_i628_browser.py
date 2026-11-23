#!/usr/bin/env python3
"""Browser regression for i628 Replay maintenance 503 + period-ID refresh/remap."""
from pathlib import Path
import json, re, runpy, shutil
ROOT=Path(__file__).resolve().parents[1]

def cot(uid,lat,lon,time,stale='2026-08-09T22:30:00Z',callsign=None):
    callsign=callsign or uid
    return f'<event version="2.0" uid="{uid}" type="a-f-A" time="{time}" start="{time}" stale="{stale}"><point lat="{lat}" lon="{lon}" hae="1000" ce="10" le="10"/><detail><contact callsign="{callsign}"/><track course="90" speed="100"/><takgateway_adsb hex="{uid}" flight="{callsign}"/></detail></event>'

def main():
    chromium=next((shutil.which(n) for n in ('chromium','chromium-browser','google-chrome','google-chrome-stable') if shutil.which(n)),None)
    if not chromium:
        print('SKIP: Chromium unavailable'); return 0
    ns=runpy.run_path(str(ROOT/'tak_dashboard.py'),run_name='tak_map_i628_maintenance_browser')
    html=str(ns['TAK_MAP_HTML']); m=re.search(r'(<script id="v415ReplayModeIntegrationPatch">[\s\S]*?</script>)',html); assert m
    replay_script=m.group(1)
    old_start='2026-08-09T20:00:00Z'; new_start='2026-08-09T20:05:00Z'; end='2026-08-09T22:00:00Z'; target='2026-08-09T21:01:00Z'
    initial=[{'uid':'A1','source':'adsb','recorded_at':new_start,'cot':cot('A1',34,-118,new_start,'2026-08-09T22:30:00Z','UAL100')}]
    state_rows=[
      {'uid':'A1','source':'adsb','recorded_at':'2026-08-09T21:00:30Z','cot':cot('A1',34.5,-118.5,'2026-08-09T21:00:30Z','2026-08-09T22:30:00Z','UAL100')},
      {'uid':'B2','source':'adsb','recorded_at':'2026-08-09T21:00:40Z','cot':cot('B2',35,-119,'2026-08-09T21:00:40Z','2026-08-09T22:30:00Z','SWA200')},
    ]
    fixture=f'''<!doctype html><html><head><meta charset="utf-8"><style>html,body{{margin:0}}#sidebar{{width:396px}}.replay-v415-hidden{{display:none!important}}.replay-confirm-v415{{display:none}}</style></head><body><div id="sidebar"><div class="version-panel"><div class="version-product">TAK Map</div><span class="release-main">1.4.0</span><span class="iteration-chip">i628</span></div></div><div id="mapStatusBanner"></div><script>
    window.__periodCalls=0;window.__stateCalls=0;window.__stateUrls=[]; const initial={json.dumps(initial)}, stateRows={json.dumps(state_rows)};
    window.fetch=async function(input){{const u=String(input&&input.url||input||'');let body={{ok:true}},status=200;
      if(u.includes('/api/tak-map/replay/config'))body={{ok:true,configured:true}};
      else if(u.includes('/api/tak-map/config'))body={{ok:true,default_basemap:'test',basemaps:[{{id:'test',type:'xyz',url:'about:blank',options:{{}}}}]}};
      else if(u.includes('/api/tak-map/replay/periods')){{window.__periodCalls++; if(window.__periodCalls===1)body={{ok:true,periods:[{{id:'rp-old',stable_id:'rp-old',legacy_id:'legacy-old',aliases:['legacy-old'],name:'Long investigation',start_utc:'{old_start}',end_utc:'{end}',duration_seconds:7200}}],maintenance:{{state_checkpoints:{{state:'rebuilding',ready:false}}}}}};else body={{ok:true,periods:[{{id:'rp-new',stable_id:'rp-new',legacy_id:'legacy-new',aliases:['rp-old','legacy-old'],name:'Long investigation',start_utc:'{new_start}',end_utc:'{end}',duration_seconds:6900}}],maintenance:{{state_checkpoints:{{state:'ready',ready:true}}}}}};}}
      else if(u.includes('/api/tak-map/replay/state')){{window.__stateCalls++;window.__stateUrls.push(u);if(window.__stateCalls===1){{status=503;body={{ok:false,rebuilding:true,reason:'state_checkpoints_rebuilding',error:'Replay state index preparing. Try again shortly.'}};}}else if(window.__stateCalls===2){{status=400;body={{ok:false,reason:'period_not_found',error:'Replay period not found.',period_id:'rp-old'}};}}else{{body={{ok:true,period_id:'rp-new',stable_id:'rp-new',aliases:['rp-old'],period_start_utc:'{new_start}',period_end_utc:'{end}',at_utc:'{target}',checkpoint_utc:'2026-08-09T21:00:00Z',events:stateRows}};}}}}
      else if(u.includes('/api/tak-map/replay/events'))body={{ok:true,events:initial}};
      return new Response(JSON.stringify(body),{{status:status,headers:{{'Content-Type':'application/json'}}}})}};
    function chain(){{return {{on(){{return this}},off(){{return this}},addTo(){{return this}},setView(){{return this}},invalidateSize(){{}},remove(){{}},removeLayer(){{}},addLayer(){{}},hasLayer(){{return false}},panTo(){{}},getCenter(){{return {{lat:34,lng:-118}}}},getZoom(){{return 9}},clearLayers(){{}},setLatLng(){{return this}},getLatLng(){{return {{lat:34,lng:-118}}}},bindPopup(){{return this}},unbindPopup(){{return this}},getPopup(){{return null}},setPopupContent(){{return this}},openPopup(){{return this}},closePopup(){{return this}},getElement(){{return null}},setIcon(){{return this}},setStyle(){{return this}},addLatLng(){{return this}}}}}}
    window.L={{map:()=>chain(),control:{{scale:()=>chain()}},layerGroup:()=>chain(),tileLayer:function(){{return chain()}},divIcon:()=>({{}}),marker:()=>chain(),polyline:()=>chain(),DomEvent:{{stopPropagation(){{}},preventDefault(){{}}}}}};window.L.tileLayer.wms=()=>chain();
    </script>{replay_script}</body></html>'''
    from playwright.sync_api import sync_playwright
    errors=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=chromium,args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
        page=browser.new_page(viewport={'width':1280,'height':760},timezone_id='UTC');page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content(fixture,wait_until='domcontentloaded',timeout=20000);page.wait_for_selector('#replayJumpGoI624',state='attached',timeout=7000)
        page.evaluate("() => document.getElementById('replayModeToggleV415').dispatchEvent(new Event('change',{bubbles:true}))");page.wait_for_function("document.getElementById('replayConfirmV415').style.display==='grid'");page.click('#replayConfirmOkV415')
        page.wait_for_function("document.querySelectorAll('#replayPeriodV415 option').length>=2",timeout=7000)
        page.evaluate("() => {const s=document.getElementById('replayPeriodV415');s.value='rp-old';s.dispatchEvent(new Event('change',{bubbles:true}))}")
        page.wait_for_function("window.getTakMapReplayDiagnosticsV415().currentMs===Date.parse('2026-08-09T20:00:00Z')",timeout=7000)
        old_ms=page.evaluate("window.getTakMapReplayDiagnosticsV415().currentMs")
        page.fill('#replayJumpDateI624','2026-08-09');page.fill('#replayJumpTimeI624','21:01:00');page.click('#replayJumpGoI624')
        page.wait_for_function("document.getElementById('replayJumpStatusI624').textContent.includes('Replay state index preparing')",timeout=7000)
        after_503=page.evaluate("() => ({date:document.getElementById('replayJumpDateI624').value,time:document.getElementById('replayJumpTimeI624').value,current:window.getTakMapReplayDiagnosticsV415().currentMs,bad:document.getElementById('replayJumpStatusI624').classList.contains('bad'),calls:window.__stateCalls})")
        assert after_503=={'date':'2026-08-09','time':'21:01:00','current':old_ms,'bad':False,'calls':1},after_503
        page.click('#replayJumpGoI624')
        target_ms=1786309260000
        page.wait_for_function(f"window.getTakMapReplayDiagnosticsV415().currentMs==={target_ms}",timeout=7000)
        final=page.evaluate("() => ({stateCalls:window.__stateCalls,periodCalls:window.__periodCalls,urls:window.__stateUrls,period:window.getTakMapReplayDiagnosticsV415().period,date:document.getElementById('replayJumpDateI624').value,time:document.getElementById('replayJumpTimeI624').value,visible:window.getTakMapReplayDiagnosticsV415().visible})")
        assert final['stateCalls']==3 and final['periodCalls']==2,final
        assert 'period_id=rp-old' in final['urls'][1] and 'period_id=rp-new' in final['urls'][2],final
        assert final['period']['stable_id']=='rp-new',final
        assert final['date']=='2026-08-09' and final['time']=='21:01:00' and final['visible']==2,final
        browser.close()
    assert not errors,errors
    print('TAK Map i628 Replay maintenance 503 + stable period refresh/remap browser regression passed')
    return 0
if __name__=='__main__':raise SystemExit(main())
