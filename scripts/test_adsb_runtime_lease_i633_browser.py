#!/usr/bin/env python3
from __future__ import annotations
import json, shutil
from pathlib import Path
from urllib.parse import urlparse, parse_qs
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'assets/tak-map-deferred-i553.json').read_text())
ADSB=next(x['code'] for x in manifest['scripts'] if x.get('id')=='takMapAdsbWorkerI463')
HTML='''<!doctype html><html><head><base href="http://localhost/"></head><body>
<div class="panel" data-collapse-key="adsbSettings"><div class="panel-body">
<input id="adsbRadiusMiles" value="10"><input id="adsbUpdateInterval" value="300">
<select id="adsbCenterSource"><option value="follow_map_center" selected>Follow Map Center</option></select>
<input id="adsbCenterLatLon" value="34.100000, -118.200000">
<input id="adsbFilterCivil" type="checkbox" checked><input id="adsbFilterMilitary" type="checkbox" checked>
<input id="adsbFilterGovt" type="checkbox" checked><input id="adsbFilterUnknown" type="checkbox" checked>
</div></div>
<div id="adsbStatus"></div><div id="adsbSettingsStatus"></div><div id="bannerAdsb">0 Aircraft</div><div id="statusDropdown"></div>
<script>
window.lastAdsbSettings={update_interval_seconds:300,stale_seconds:90,center_source:'follow_map_center',radius_miles:10};
window.takLeafletMap=window.map={getCenter:()=>({lat:34.1,lng:-118.2}),on:()=>{},distance:()=>1609.344,hasLayer:()=>true};
window.TakMapControllers={adsb:{version:'v491',markers:new Map(),data:new Map(),layer:{removeLayer(){},addTo(){}}}};
window.lastAircraft=[];window.drawAircraft=rows=>{window.lastAircraft=rows;return rows};
</script><script src="/runtime/adsb.js"></script></body></html>'''

def main():
    chromium=next((n for n in ('chromium','chromium-browser','google-chrome','google-chrome-stable') if shutil.which(n)),None)
    if not chromium:
        print('SKIP: Chromium unavailable'); return 0
    from playwright.sync_api import sync_playwright
    seen=[]; errors=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=shutil.which(chromium),args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
        page=browser.new_page()
        page.on('pageerror',lambda e: errors.append(str(e)))
        def route(r):
            u=r.request.url; p=urlparse(u)
            if p.path=='/':
                return r.fulfill(status=200,content_type='text/html; charset=utf-8',body=HTML)
            if p.path=='/runtime/adsb.js':
                return r.fulfill(status=200,content_type='application/javascript; charset=utf-8',body=ADSB)
            if p.path=='/api/tak-map/adsb':
                q=parse_qs(p.query); seen.append({k:(v[-1] if v else '') for k,v in q.items()})
                return r.fulfill(status=200,content_type='application/json',body=json.dumps({'ok':True,'aircraft':[{'id':'a1b2c3','lat':34.1,'lon':-118.2,'alt_ft':12000}],'settings':{'stale_seconds':90},'snapshot_ready':True}))
            return r.fulfill(status=204,body='')
        page.route('**/*',route)
        # Stable storage stub for deterministic per-tab client ID persistence.
        storage="""(()=>{const a=new Map(),b=new Map();const mk=m=>({getItem:k=>m.has(String(k))?m.get(String(k)):null,setItem:(k,v)=>m.set(String(k),String(v)),removeItem:k=>m.delete(String(k)),clear:()=>m.clear()});Object.defineProperty(window,'localStorage',{configurable:true,value:mk(a)});Object.defineProperty(window,'sessionStorage',{configurable:true,value:mk(b)});})();"""
        page.evaluate(storage)
        page.set_content(HTML,wait_until='domcontentloaded')
        page.wait_for_function("window.TakMapAdsbWorkerV476 && window.TakMapAdsbWorkerV476.diagnostics().completedPollCount>=1",timeout=12000)
        page.wait_for_timeout(200)
        active=[x for x in seen if x.get('active')=='1']
        assert active,seen
        cid=active[0].get('client_id','')
        assert cid and all(x.get('client_id')==cid for x in active),active
        assert active[0].get('center_lat')=='34.100000' and active[0].get('center_lon')=='-118.200000',active[0]
        before=len(active)
        page.evaluate("window.TakMapAdsbWorkerV476.disable()")
        page.wait_for_function("localStorage.getItem('takmap.adsb.localDisabled')==='1'",timeout=3000)
        page.wait_for_timeout(600)
        inactive=[x for x in seen if x.get('active')=='0']
        assert inactive and inactive[-1].get('client_id')==cid,(inactive,cid)
        page.wait_for_timeout(1200)
        active_after=[x for x in seen if x.get('active')=='1']
        assert len(active_after)==before,(active_after,seen)
        browser.close()
    assert not errors,errors
    print('TAK Map i633 deferred ADS-B runtime active lease + OFF revocation browser regression passed')
    print(json.dumps({'active_requests':len(active_after),'inactive_requests':len(inactive),'client_id_present':bool(cid)},sort_keys=True))
    return 0
if __name__=='__main__': raise SystemExit(main())
