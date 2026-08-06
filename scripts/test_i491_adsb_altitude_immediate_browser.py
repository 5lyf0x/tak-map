#!/usr/bin/env python3
from __future__ import annotations
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD = ROOT / 'assets' / 'tak-map-card-controls-v491.js'
ADSB = ROOT / 'assets' / 'tak-map-adsb-v491.js'
ORIGIN = 'http://localhost'

HTML = '''<!doctype html><html><head><meta charset="utf-8"><base href="http://localhost/"><style>
body{background:#080d12;color:#eee}.sidebar{width:390px}.panel{border:1px solid #334;padding:8px}.panel-body{display:block}.adsb-settings-grid{display:grid}.chip{padding:2px 6px}
</style></head><body data-ready="0"><aside class="sidebar">
<div class="panel" data-collapse-key="adsbSettings"><h2>ADS-B <span class="panel-toggle">▾</span></h2><div class="panel-body">
<div id="adsbV270Menu"><div class="adsb-v270-top"><button id="adsbToggleBtn">Disable ADS-B</button></div>
<div class="adsb-settings-grid">
<label>Radius Miles<input id="adsbRadiusMiles" type="number" value="10"></label>
<label>Update Interval (sec)<input id="adsbUpdateInterval" type="number" value="300"></label>
<label>Center Source<select id="adsbCenterSource"><option value="follow_map_center">Follow Map Center</option></select></label>
<label>Center Lat/Lon<input id="adsbCenterLatLon" value="34.1,-118.2"></label>
</div>
<div class="adsb-filter-box">
<label><span>Civil</span><input id="adsbFilterCivil" type="checkbox" checked></label>
<label><span>Military</span><input id="adsbFilterMilitary" type="checkbox" checked></label>
<label><span>Govt</span><input id="adsbFilterGovt" type="checkbox" checked></label>
<label><span>Unknown</span><input id="adsbFilterUnknown" type="checkbox" checked></label>
</div></div>
<div id="bannerAdsb">0 Aircraft</div><div id="adsbStatus"></div><div id="adsbSettingsStatus"></div>
</div></div></aside><div id="statusDropdown"></div>
<script>
window.lastAdsbSettings={update_interval_seconds:300,stale_seconds:90,center_source:'follow_map_center',radius_miles:10};
window.takLeafletMap=window.map={getCenter:()=>({lat:34.1,lng:-118.2}),on:()=>{},distance:()=>1609.344};
window.TakMapControllers={adsb:{version:'v491',markers:new Map(),data:new Map(),layer:{removeLayer(){}}}};
window.__draws=[];window.drawAircraft=rows=>{window.__draws.push(rows.map(r=>r.id));return rows};
</script>
<script src="/assets/runtime/tak-map-card-controls-v491.js"></script>
<script src="/assets/runtime/tak-map-adsb-v491.js"></script>
</body></html>'''

ROWS = [
    {'id':'low','lat':34.10,'lon':-118.20,'alt_ft':5000},
    {'id':'mid','lat':34.11,'lon':-118.21,'alt_ft':15000},
    {'id':'high','lat':34.12,'lon':-118.22,'alt_ft':25000},
    {'id':'unknown','lat':34.13,'lon':-118.23},
]


def main() -> int:
    chromium = next((n for n in ('chromium','chromium-browser','google-chrome','google-chrome-stable') if shutil.which(n)), None)
    if not chromium:
        print('SKIP: Chromium unavailable')
        return 0
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=shutil.which(chromium), args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
        page = browser.new_page()
        errors: list[str] = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        def route(r):
            u = r.request.url
            if u.endswith('/assets/runtime/tak-map-card-controls-v491.js'):
                r.fulfill(status=200, content_type='application/javascript; charset=utf-8', body=CARD.read_text())
            elif u.endswith('/assets/runtime/tak-map-adsb-v491.js'):
                r.fulfill(status=200, content_type='application/javascript; charset=utf-8', body=ADSB.read_text())
            elif '/api/tak-map/adsb' in u:
                r.fulfill(status=200, content_type='application/json', body=json.dumps({'ok':True,'aircraft':ROWS,'settings':{'stale_seconds':90}}))
            else:
                r.fulfill(status=404, body='not found')
        page.route('**/*', route)
        page.evaluate("""(()=>{const s={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>Object.prototype.hasOwnProperty.call(s,k)?s[k]:null,setItem:(k,v)=>{s[k]=String(v)},removeItem:k=>{delete s[k]},clear:()=>{Object.keys(s).forEach(k=>delete s[k])}}});})()""")
        page.set_content(HTML, wait_until='domcontentloaded')
        page.wait_for_function("window.TakMapCardControlsV477 && window.TakMapAdsbWorkerV476")
        page.wait_for_function("Array.isArray(window.lastAircraft) && window.lastAircraft.length===4", timeout=12000)
        page.wait_for_timeout(200)

        initial = page.evaluate("""()=>({
          ids:lastAircraft.map(x=>x.id).sort(),
          secondary:[...document.querySelectorAll('.adsb-type-sub-v491')].map(x=>x.textContent),
          cardTexts:[...document.querySelectorAll('.adsb-type-card-v491')].map(x=>x.textContent.replace(/✓/g,'').trim()),
          diag:TakMapAdsbWorkerV476.diagnostics()
        })""")

        # The default threshold is 10,000 ft. Selecting Above must filter immediately.
        page.select_option('#adsbAltitudeFilterV477', 'above')
        page.wait_for_function("window.lastAircraft.map(x=>x.id).sort().join('|')==='high|mid'", timeout=3000)
        above = page.evaluate("()=>({ids:lastAircraft.map(x=>x.id).sort(),mode:localStorage.getItem('takmap.adsb.altitude.mode'),diag:TakMapAdsbWorkerV476.diagnostics()})")

        # Switching to Below must immediately use the current threshold.
        page.select_option('#adsbAltitudeFilterV477', 'below')
        page.wait_for_function("window.lastAircraft.map(x=>x.id).join('|')==='low'", timeout=3000)
        below = page.evaluate("()=>({ids:lastAircraft.map(x=>x.id),mode:localStorage.getItem('takmap.adsb.altitude.mode'),diag:TakMapAdsbWorkerV476.diagnostics()})")

        # Typing alone, without blur/change/Enter, must update the current Below filter.
        page.fill('#adsbAltitudeThresholdV477', '20000')
        page.wait_for_function("window.lastAircraft.map(x=>x.id).sort().join('|')==='low|mid'", timeout=3000)
        typed = page.evaluate("()=>({ids:lastAircraft.map(x=>x.id).sort(),meters:Number(localStorage.getItem('takmap.adsb.altitude.thresholdMeters')),active:TakMapAdsbWorkerV476.diagnostics().altitudeThresholdActive})")

        # A mode switch after typing must immediately use the typed value.
        page.select_option('#adsbAltitudeFilterV477', 'above')
        page.wait_for_function("window.lastAircraft.map(x=>x.id).join('|')==='high'", timeout=3000)
        switched = page.evaluate("()=>({ids:lastAircraft.map(x=>x.id),mode:TakMapAdsbWorkerV476.diagnostics().altitudeMode})")

        # Clearing the field removes the active threshold immediately while retaining the chosen mode.
        page.fill('#adsbAltitudeThresholdV477', '')
        page.wait_for_function("window.lastAircraft.length===4", timeout=3000)
        cleared = page.evaluate("()=>({ids:lastAircraft.map(x=>x.id).sort(),stored:localStorage.getItem('takmap.adsb.altitude.thresholdMeters'),mode:TakMapAdsbWorkerV476.diagnostics().altitudeMode,active:TakMapAdsbWorkerV476.diagnostics().altitudeThresholdActive})")

        # Typing again reactivates the filter immediately.
        page.fill('#adsbAltitudeThresholdV477', '10000')
        page.wait_for_function("window.lastAircraft.map(x=>x.id).sort().join('|')==='high|mid'", timeout=3000)
        retyped = page.evaluate("()=>({ids:lastAircraft.map(x=>x.id).sort(),active:TakMapAdsbWorkerV476.diagnostics().altitudeThresholdActive,changes:TakMapAdsbWorkerV476.diagnostics().altitudeFilterChanges})")
        browser.close()

    assert not errors, errors
    assert initial['ids'] == ['high','low','mid','unknown'], initial
    assert initial['secondary'] == [], initial
    assert all(x in initial['cardTexts'] for x in ('CIVCivil','GOVGovt','MILMilitary','UNKUnknown')), initial
    assert above['ids'] == ['high','mid'] and above['mode'] == 'above', above
    assert below['ids'] == ['low'] and below['mode'] == 'below', below
    assert typed['ids'] == ['low','mid'] and 6095 < typed['meters'] < 6097 and typed['active'], typed
    assert switched == {'ids':['high'], 'mode':'above'}, switched
    assert cleared['ids'] == ['high','low','mid','unknown'] and cleared['stored'] == '' and cleared['mode'] == 'above' and not cleared['active'], cleared
    assert retyped['ids'] == ['high','mid'] and retyped['active'] and retyped['changes'] >= 6, retyped
    print('ADS-B immediate altitude filter browser test passed')
    print(json.dumps({'initial':initial,'above':above,'below':below,'typed':typed,'switched':switched,'cleared':cleared,'retyped':retyped}, sort_keys=True))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
