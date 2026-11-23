#!/usr/bin/env python3
"""Headless-browser regression for i625 Replay Search/Jump reconstruction and Play."""
from pathlib import Path
import json, re, runpy, shutil
ROOT=Path(__file__).resolve().parents[1]

def cot(uid,lat,lon,time='2026-08-10T12:00:00Z',stale='2026-08-10T12:30:00Z',callsign=None):
    callsign=callsign or uid
    return f'<event version="2.0" uid="{uid}" type="a-f-A" time="{time}" start="{time}" stale="{stale}"><point lat="{lat}" lon="{lon}" hae="1000" ce="10" le="10"/><detail><contact callsign="{callsign}"/><track course="90" speed="100"/><takgateway_adsb icao="{uid}" flight="{callsign}"/></detail></event>'

def main():
    chromium=next((shutil.which(n) for n in ('chromium','chromium-browser','google-chrome','google-chrome-stable') if shutil.which(n)),None)
    if not chromium:
        print('SKIP: Chromium unavailable'); return 0
    ns=runpy.run_path(str(ROOT/'tak_dashboard.py'),run_name='tak_map_i625_seek_browser')
    html=str(ns['TAK_MAP_HTML'])
    m=re.search(r'(<script id="v415ReplayModeIntegrationPatch">[\s\S]*?</script>)',html)
    assert m
    replay_script=m.group(1)
    rows0=[
      {'uid':'AAA111','source':'adsb','recorded_at':'2026-08-10T12:00:00Z','cot':cot('AAA111',34.0,-118.0,callsign='UAL100')},
      {'uid':'BBB222','source':'adsb','recorded_at':'2026-08-10T12:00:00Z','cot':cot('BBB222',34.1,-118.1,callsign='SWA200')},
      {'uid':'CCC333','source':'adsb','recorded_at':'2026-08-10T12:00:00Z','cot':cot('CCC333',34.2,-118.2,callsign='DAL300')},
    ]
    row10={'uid':'AAA111','source':'adsb','recorded_at':'2026-08-10T12:10:00Z','cot':cot('AAA111',34.5,-118.5,time='2026-08-10T12:10:00Z',callsign='UAL100')}
    fixture=f'''<!doctype html><html><head><meta charset="utf-8"><style>html,body{{margin:0}}#sidebar{{width:396px}}.replay-v415-hidden{{display:none!important}}.replay-confirm-v415{{display:none}}</style></head><body><div id="sidebar"><div class="version-panel"><div class="version-product">TAK Map</div><span class="release-main">1.4.0</span><span class="iteration-chip">i625</span></div></div><div id="mapStatusBanner"></div><script>
    window.__eventCalls={{}}; window.__searchUrl='';
    const rows0={json.dumps(rows0)}; const row10={json.dumps(row10)};
    window.fetch=async function(input){{
      const u=String(input&&input.url||input||''); let body={{ok:true}};
      if(u.includes('/api/tak-map/replay/config')) body={{ok:true,configured:true}};
      else if(u.includes('/api/tak-map/config')) body={{ok:true,default_basemap:'test',basemaps:[{{id:'test',type:'xyz',url:'about:blank',options:{{}}}}]}};
      else if(u.includes('/api/tak-map/replay/periods')) body={{ok:true,periods:[{{id:'rp1',stable_id:'rp1',start_utc:'2026-08-10T12:00:00Z',end_utc:'2026-08-10T12:20:00Z',duration_seconds:1200}}]}};
      else if(u.includes('/api/tak-map/replay/search')){{window.__searchUrl=u;body={{ok:true,period_id:'rp1',stable_id:'rp1',period_start_utc:'2026-08-10T12:00:00Z',period_end_utc:'2026-08-10T12:20:00Z',results:[{{uid:'AAA111',source:'adsb',display_identity:'UAL100',matched_field:'flight',matched_field_label:'Flight',matched_value:'UAL100',first_seen_utc:'2026-08-10T12:10:00Z',last_seen_utc:'2026-08-10T12:10:00Z',appearance_count:1,occurrences:[{{seek_utc:'2026-08-10T12:10:00Z'}}],identifiers:{{flight:['UAL100'],icao:['AAA111']}}}}]}};}}
      else if(u.includes('/api/tak-map/replay/events')){{
        const q=new URLSearchParams((u.split('?')[1]||'')),s=q.get('start')||'',sm=Date.parse(s); window.__eventCalls[s]=(window.__eventCalls[s]||0)+1;
        if(sm<Date.parse('2026-08-10T12:05:00Z')) body={{ok:true,events:rows0}};
        else {{if(sm===Date.parse('2026-08-10T12:05:00Z')&&window.__eventCalls[s]===1) await new Promise(r=>setTimeout(r,900)); body={{ok:true,events:sm<=Date.parse('2026-08-10T12:10:00Z')?[row10]:[]}};}}
      }}
      return new Response(JSON.stringify(body),{{status:200,headers:{{'Content-Type':'application/json'}}}});
    }};
    function chain(){{return {{on(){{return this}},off(){{return this}},addTo(){{return this}},setView(){{return this}},invalidateSize(){{}},remove(){{}},removeLayer(){{}},addLayer(){{}},hasLayer(){{return false}},panTo(){{}},getCenter(){{return {{lat:34,lng:-118}}}},getZoom(){{return 9}},clearLayers(){{}},setLatLng(){{return this}},getLatLng(){{return {{lat:34,lng:-118}}}},bindPopup(){{return this}},unbindPopup(){{return this}},getPopup(){{return null}},setPopupContent(){{return this}},openPopup(){{return this}},closePopup(){{return this}},getElement(){{return null}},setIcon(){{return this}},setStyle(){{return this}},addLatLng(){{return this}}}}}}
    window.L={{map:()=>chain(),control:{{scale:()=>chain()}},layerGroup:()=>chain(),tileLayer:function(){{return chain()}},divIcon:()=>({{}}),marker:()=>chain(),polyline:()=>chain(),DomEvent:{{stopPropagation(){{}},preventDefault(){{}}}}}}; window.L.tileLayer.wms=()=>chain();
    </script>{replay_script}</body></html>'''
    from playwright.sync_api import sync_playwright
    errors=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=chromium,args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
        context=browser.new_context(viewport={'width':1280,'height':760},timezone_id='UTC')
        page=context.new_page(); page.on('pageerror',lambda exc:errors.append(str(exc)))
        page.set_content(fixture,wait_until='domcontentloaded',timeout=20000)
        page.wait_for_selector('#replayJumpGoI624',state='attached',timeout=7000)
        page.evaluate("() => document.getElementById('replayModeToggleV415').dispatchEvent(new Event('change',{bubbles:true}))")
        page.wait_for_function("document.getElementById('replayConfirmV415').style.display === 'grid'",timeout=5000); page.click('#replayConfirmOkV415')
        page.wait_for_function("document.querySelectorAll('#replayPeriodV415 option').length>=2",timeout=7000)
        page.evaluate("() => {const s=document.getElementById('replayPeriodV415');s.value='rp1';s.dispatchEvent(new Event('change',{bubbles:true}))}")
        page.wait_for_function("window.getTakMapReplayDiagnosticsV415().visible===3",timeout=7000)
        before=page.evaluate("window.getTakMapReplayDiagnosticsV415()")
        assert before['visible']==3,before

        # Search while the ordinary background request is deliberately still in flight.
        page.fill('#replaySearchInputI621','UAL100'); page.click('#replaySearchButtonI621')
        page.wait_for_selector('.replay-search-result-i621',timeout=7000); page.click('.replay-search-result-i621')
        page.wait_for_timeout(150)
        mid=page.evaluate("window.getTakMapReplayDiagnosticsV415()")
        assert mid['visible']==3,mid
        page.wait_for_function("window.getTakMapReplayDiagnosticsV415().currentMs>=Date.parse('2026-08-10T12:10:00Z')",timeout=7000)
        after=page.evaluate("window.getTakMapReplayDiagnosticsV415()")
        assert after['visible']==3,after
        assert after['replaySeekI625']['searchUnified'] and after['replaySeekI625']['backgroundSerialized'],after

        # Sparse date/time jump: no event follows the exact target, but Play must still advance toward the actual period end.
        page.fill('#replayJumpDateI624','2026-08-10'); page.fill('#replayJumpTimeI624','12:10:30'); page.click('#replayJumpGoI624')
        target=1786363830000
        page.wait_for_function(f"window.getTakMapReplayDiagnosticsV415().currentMs==={target}",timeout=7000)
        jumped=page.evaluate("window.getTakMapReplayDiagnosticsV415()")
        assert jumped['visible']==3,jumped
        assert jumped['replaySeekI625']['logicalEndMs']==1786364400000,jumped
        assert jumped['replaySeekI625']['eventEndMs']<=target,jumped
        page.click('#replayPlayV415'); page.wait_for_timeout(700)
        playing=page.evaluate("window.getTakMapReplayDiagnosticsV415()")
        assert playing['currentMs']>target,playing
        assert playing['currentMs']<playing['replaySeekI625']['logicalEndMs'],playing
        page.click('#replayPlayV415')
        browser.close()
    assert not errors,errors
    print('TAK Map i625 Replay Search/Jump state persistence and Play-after-Jump browser regression passed')
    return 0
if __name__=='__main__': raise SystemExit(main())
