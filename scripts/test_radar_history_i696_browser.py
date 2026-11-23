"""Headless interactive i696 radar timeline UI, without NOAA network or server data."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json

ROOT=Path(__file__).resolve().parents[1]
js=(ROOT/'assets/tak-map-radar-history-i696.js').read_text()
css=(ROOT/'assets/tak-map-radar-history-i696.css').read_text()
HTML='''<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><style>%s</style></head><body style="max-width:300px;background:#13202b;color:white">
<section id="takNativeWeatherI691"><div class="tak-weather-body-i691"><section id="takWeatherRadarSettingsI691"><small id="takWeatherRadarStatusI691">Radar ready</small></section></div></section>
<script>
const latest=Date.now()-30000;
const frameTimes=Array.from({length:8},(_,i)=>latest-(7-i)*300000);
const frameData=frameTimes.map(t=>({frame_id:'h'+String(t)+'_abcdef0123456789',valid_time_utc:new Date(t).toISOString()}));
window.checks={choices:[],left:0,stopped:0,ready:false,fetches:0};
window.TakMapNativeWeatherI693={state:{radar:true,radarToken:'p123',historyMode:false},
 selectHistory(frame){checks.choices.push(frame.frame_id);this.state.radarToken=frame.frame_id;this.state.historyMode=true;return true},
 leaveHistory(){checks.left++;this.state.radarToken='p123';this.state.historyMode=false},
 historyReady(id){return checks.ready&&this.state.radarToken===id}};
window.fetch=async()=>{checks.fetches++;return {ok:true,json:async()=>({ok:true,historical_supported:true,frames:frameData,window_available_minutes:35})}};
</script><script>%s</script></body></html>'''%(css,js)
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    p=browser.new_page(viewport={'width':390,'height':850})
    errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
    p.set_content(HTML)
    p.wait_for_function("document.getElementById('takRadarHistoryI696') && checks.fetches>0")
    p.wait_for_function('!TakMapRadarHistoryI696.state.catalogPending')
    assert p.locator('#takRadarHistoryI696').is_visible()
    assert p.locator('#takRadarHistoryI696 [data-radar-window]').count()==4
    assert p.locator('[data-radar-action]').count()==6
    assert p.locator('#takRadarTimelineI696').is_enabled()
    p.locator('[data-radar-window="30"]').click()
    p.wait_for_function('!TakMapRadarHistoryI696.state.catalogPending')
    assert p.evaluate('TakMapRadarHistoryI696.state.window')==30
    p.locator('[data-radar-action="play"]').click()
    p.wait_for_function('TakMapRadarHistoryI696.state.playing')
    assert p.evaluate('checks.choices.length')==1
    p.wait_for_timeout(1550)
    # Until tileload completes, the player cannot consume another frame.
    assert p.evaluate('checks.choices.length')==1
    assert 'Buffering' in p.locator('#takRadarHistoryStatusI696').inner_text()
    p.evaluate('checks.ready=true')
    p.wait_for_function('checks.choices.length>=2',timeout=6000)
    p.locator('[data-radar-action="play"]').click()
    assert not p.evaluate('TakMapRadarHistoryI696.state.playing')
    p.locator('#takRadarTimelineI696').fill('3')
    assert p.evaluate('TakMapRadarHistoryI696.state.index')==3
    p.locator('[data-radar-action="prev"]').click()
    assert p.evaluate('TakMapRadarHistoryI696.state.index')==2
    p.locator('[data-radar-action="next"]').click()
    assert p.evaluate('TakMapRadarHistoryI696.state.index')==3
    p.locator('[data-radar-action="first"]').click()
    assert p.evaluate('TakMapRadarHistoryI696.state.index')==0
    p.locator('[data-radar-action="last"]').click()
    assert p.evaluate('TakMapRadarHistoryI696.state.index')==7
    p.locator('#takRadarSpeedI696').select_option('4')
    assert p.evaluate('TakMapRadarHistoryI696.state.speed')==4
    p.locator('#takRadarLoopI696').uncheck()
    assert not p.evaluate('TakMapRadarHistoryI696.state.loop')
    p.locator('[data-radar-action="live"]').click()
    assert p.evaluate('checks.left')==1
    assert p.evaluate('!TakMapNativeWeatherI693.state.historyMode')
    assert 'LIVE' in p.locator('#takRadarSelectedI696').inner_text()
    assert not p.evaluate('document.documentElement.scrollWidth>document.documentElement.clientWidth'),'horizontal overflow'
    # Radar OFF hides the integrated controls without changing settings.
    p.evaluate('TakMapNativeWeatherI693.state.radar=false')
    p.wait_for_timeout(1900)
    assert p.locator('#takRadarHistoryI696').is_hidden()
    assert errors==[],errors
    print(json.dumps({'result':'PASS','browser':'Chromium','checks':['compact controls','30 minute window','Play/Pause','buffering blocks premature advance','next/prev/first/last','scrub','speed 4x','loop toggle','LIVE return','no mobile overflow','radar OFF hides controls'],'page_errors':errors},indent=2))
    browser.close()
