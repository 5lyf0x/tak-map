#!/usr/bin/env python3
"""Browser regression: actual i697 radar timeline equals basemap Soft Pill slider."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json
root=Path(__file__).resolve().parents[1]
stack=(root/'assets/tak-map-basemap-stack-i673.js').read_text()
canonical=stack.split('.tak-soft-pill-i678{appearance:none!important;',1)[1].split('\n#takBasemapPopoverI678',1)[0]
canonical='.tak-soft-pill-i678{appearance:none!important;'+canonical
css=(root/'assets/tak-map-radar-history-i696.css').read_text()
js=(root/'assets/tak-map-radar-history-i696.js').read_text()
html='''<!doctype html><html><head><style>%s\n%s</style></head>
<body style="max-width:390px;background:#13202b;color:white">
<section id="takNativeWeatherI691"><div id="takWeatherRadarSettingsI691"><small id="takWeatherRadarStatusI691">Radar ready</small></div></section>
<div id="takBasemapBlendI673"><input id="baseline" type="range" class="tak-soft-pill-i678" min="0" max="100" value="50" style="--tak-soft-pill-pct:50%%"></div>
<script>
const latest=Date.now()-30000;
const frameData=Array.from({length:5},(_,i)=>({frame_id:'h'+String(latest-(4-i)*300000)+'_abcdef0123456789',valid_time_utc:new Date(latest-(4-i)*300000).toISOString()}));
window.TakMapNativeWeatherI693={state:{radar:true,radarToken:'p123',historyMode:false},
 selectHistory(frame){this.state.radarToken=frame.frame_id;this.state.historyMode=true;return true},
 leaveHistory(){this.state.radarToken='p123';this.state.historyMode=false},historyReady(){return true}};
window.fetch=async()=>({ok:true,json:async()=>({ok:true,historical_supported:true,frames:frameData,window_available_minutes:20})});
</script><script>%s</script></body></html>'''%(canonical,css,js)
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    p=browser.new_page(viewport={'width':390,'height':850})
    errs=[];p.on('pageerror',lambda e:errs.append(str(e)))
    p.set_content(html)
    p.wait_for_function('document.getElementById("takRadarTimelineI696") && !TakMapRadarHistoryI696.state.catalogPending')
    values=p.evaluate('''() => {
      const a=document.getElementById('takRadarTimelineI696'),b=document.getElementById('baseline');
      const sa=getComputedStyle(a),sb=getComputedStyle(b),
            ta=getComputedStyle(a,'::-webkit-slider-runnable-track'),tb=getComputedStyle(b,'::-webkit-slider-runnable-track');
      return {heightA:sa.height,heightB:sb.height,trackA:ta.backgroundImage,trackB:tb.backgroundImage,appearanceA:sa.appearance,appearanceB:sb.appearance,widthA:a.offsetWidth,enabled:!a.disabled};
    }''')
    assert values['enabled'] and values['widthA']>240,values
    assert values['heightA']==values['heightB']=='24px',values
    assert values['trackA']==values['trackB'],values
    assert values['appearanceA']==values['appearanceB'],values
    p.locator('#takRadarTimelineI696').fill('2')
    assert p.evaluate('TakMapRadarHistoryI696.state.index')==2
    progress=p.evaluate("document.getElementById('takRadarTimelineI696').style.getPropertyValue('--tak-soft-pill-pct')")
    assert progress=='50.00%',progress
    p.locator('#takRadarTimelineI696').fill('4')
    assert p.evaluate('TakMapRadarHistoryI696.state.index')==4
    assert p.evaluate("document.getElementById('takRadarTimelineI696').style.getPropertyValue('--tak-soft-pill-pct')")=='100.00%'
    assert not errs,errs
    print(json.dumps({'status':'PASS','matched_soft_pill_track':True,'matched_height':values['heightA'],'timeline_progress':['50.00%','100.00%'],'page_errors':errs}))
    browser.close()
