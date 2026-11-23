#!/usr/bin/env python3
"""Headless-browser regression for i626 checkpoint state-at-time absolute seeks."""
from pathlib import Path
import json,re,runpy,shutil
ROOT=Path(__file__).resolve().parents[1]

def cot(uid,lat,lon,time,stale='2026-08-10T06:00:00Z',callsign=None):
    callsign=callsign or uid
    return f'<event version="2.0" uid="{uid}" type="a-f-A" time="{time}" start="{time}" stale="{stale}"><point lat="{lat}" lon="{lon}" hae="1000" ce="10" le="10"/><detail><contact callsign="{callsign}"/><track course="90" speed="100"/><takgateway_adsb hex="{uid}" flight="{callsign}"/></detail></event>'

def main():
    chromium=next((shutil.which(n) for n in ('chromium','chromium-browser','google-chrome','google-chrome-stable') if shutil.which(n)),None)
    if not chromium:
        print('SKIP: Chromium unavailable'); return 0
    ns=runpy.run_path(str(ROOT/'tak_dashboard.py'),run_name='tak_map_i626_state_browser')
    html=str(ns['TAK_MAP_HTML']); m=re.search(r'(<script id="v415ReplayModeIntegrationPatch">[\s\S]*?</script>)',html); assert m
    replay_script=m.group(1)
    start='2026-07-27T20:45:00Z'; end='2026-08-10T20:45:00Z'; target='2026-08-09T21:01:00Z'
    initial=[{'uid':'A1','source':'adsb','recorded_at':start,'cot':cot('A1',34,-118,start,'2026-07-27T21:00:00Z','UAL100')}]
    state_rows=[
      {'uid':'A1','source':'adsb','recorded_at':'2026-08-09T21:00:30Z','cot':cot('A1',34.5,-118.5,'2026-08-09T21:00:30Z','2026-08-09T21:03:00Z','UAL100')},
      {'uid':'B2','source':'adsb','recorded_at':'2026-08-09T21:00:20Z','cot':cot('B2',35,-119,'2026-08-09T21:00:20Z','2026-08-09T21:03:00Z','SWA200')},
      {'uid':'C3','source':'adsb','recorded_at':'2026-08-09T21:00:10Z','cot':cot('C3',36,-120,'2026-08-09T21:00:10Z','2026-08-09T21:03:00Z','DAL300')},
    ]
    future=[{'uid':'A1','source':'adsb','recorded_at':'2026-08-09T21:02:00Z','cot':cot('A1',34.6,-118.6,'2026-08-09T21:02:00Z','2026-08-09T21:05:00Z','UAL100')}]
    fixture=f'''<!doctype html><html><head><meta charset="utf-8"><style>html,body{{margin:0}}#sidebar{{width:396px}}.replay-v415-hidden{{display:none!important}}.replay-confirm-v415{{display:none}}</style></head><body><div id="sidebar"><div class="version-panel"><div class="version-product">TAK Map</div><span class="release-main">1.4.0</span><span class="iteration-chip">i626</span></div></div><div id="mapStatusBanner"></div><script>
    window.__stateCalls=0;window.__eventCalls=0;window.__targetEventServed=false; const initial={json.dumps(initial)}, stateRows={json.dumps(state_rows)}, future={json.dumps(future)};
    window.fetch=async function(input){{const u=String(input&&input.url||input||'');let body={{ok:true}};
      if(u.includes('/api/tak-map/replay/config'))body={{ok:true,configured:true}};
      else if(u.includes('/api/tak-map/config'))body={{ok:true,default_basemap:'test',basemaps:[{{id:'test',type:'xyz',url:'about:blank',options:{{}}}}]}};
      else if(u.includes('/api/tak-map/replay/periods'))body={{ok:true,periods:[{{id:'rp-long',stable_id:'rp-long',start_utc:'{start}',end_utc:'{end}',duration_seconds:1209600}}]}};
      else if(u.includes('/api/tak-map/replay/state')){{window.__stateCalls++;await new Promise(r=>setTimeout(r,700));body={{ok:true,period_id:'rp-long',stable_id:'rp-long',period_start_utc:'{start}',period_end_utc:'{end}',at_utc:'{target}',checkpoint_utc:'2026-08-09T21:00:00Z',checkpoint_age_seconds:60,delta_events_scanned:7,object_count:3,events:stateRows}};}}
      else if(u.includes('/api/tak-map/replay/events')){{window.__eventCalls++;const q=new URLSearchParams(u.split('?')[1]||''),sm=Date.parse(q.get('start')||'');if(sm<Date.parse('2026-07-27T20:50:00Z'))body={{ok:true,events:initial}};else if(sm>=Date.parse('{target}')){{if(!window.__targetEventServed){{window.__targetEventServed=true;body={{ok:true,events:future}};}}else{{await new Promise(r=>setTimeout(r,1200));body={{ok:true,events:[]}};}}}}else{{await new Promise(r=>setTimeout(r,1200));body={{ok:true,events:[]}};}}}}
      return new Response(JSON.stringify(body),{{status:200,headers:{{'Content-Type':'application/json'}}}})}};
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
        label=page.locator('#replayPeriodV415 option').nth(1).inner_text();assert '07/27/2026' in label and '08/10/2026' in label,label
        page.evaluate("() => {const s=document.getElementById('replayPeriodV415');s.value='rp-long';s.dispatchEvent(new Event('change',{bubbles:true}))}")
        page.wait_for_function("window.getTakMapReplayDiagnosticsV415().currentMs===Date.parse('2026-07-27T20:45:00Z')",timeout=7000)
        old=page.evaluate("window.getTakMapReplayDiagnosticsV415().currentMs")
        page.fill('#replayJumpDateI624','2026-08-09');page.fill('#replayJumpTimeI624','21:01:00');page.click('#replayJumpGoI624')
        page.wait_for_timeout(150)
        locked=page.evaluate("() => ({play:document.getElementById('replayPlayV415').disabled,timeline:document.getElementById('replayTimelineV415').disabled,seeking:window.getTakMapReplayDiagnosticsV415().replaySeekI625.seeking,current:window.getTakMapReplayDiagnosticsV415().currentMs,date:document.getElementById('replayJumpDateI624').value,time:document.getElementById('replayJumpTimeI624').value})")
        assert locked['play'] and locked['timeline'] and locked['seeking'],locked
        assert locked['current']==old and locked['date']=='2026-08-09' and locked['time']=='21:01:00',locked
        page.evaluate("document.getElementById('replayPlayV415').click()")
        page.wait_for_timeout(100);assert page.evaluate("window.getTakMapReplayDiagnosticsV415().currentMs")==old
        target_ms=1786309260000
        page.wait_for_function(f"window.getTakMapReplayDiagnosticsV415().currentMs==={target_ms}",timeout=7000)
        after=page.evaluate("() => ({diag:window.getTakMapReplayDiagnosticsV415(),stateCalls:window.__stateCalls,eventCalls:window.__eventCalls,playDisabled:document.getElementById('replayPlayV415').disabled,date:document.getElementById('replayJumpDateI624').value,time:document.getElementById('replayJumpTimeI624').value})")
        assert after['stateCalls']==1,after
        assert after['eventCalls']<15,after
        assert after['diag']['visible']==3,after
        assert not after['playDisabled'] and after['date']=='2026-08-09' and after['time']=='21:01:00',after
        page.click('#replayPlayV415');page.wait_for_timeout(550);playing=page.evaluate("window.getTakMapReplayDiagnosticsV415().currentMs");assert playing>target_ms,playing
        browser.close()
    assert not errors,errors
    print('TAK Map i626 checkpoint state-at-time long-jump/transport-lock browser regression passed')
    return 0
if __name__=='__main__':raise SystemExit(main())
