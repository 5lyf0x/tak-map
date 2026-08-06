#!/usr/bin/env python3
from __future__ import annotations
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DS_ASSET=ROOT/'assets'/'tak-map-data-sync-v491.js'
CARD_ASSET=ROOT/'assets'/'tak-map-card-controls-v491.js'
ORIGIN='http://localhost'


def main()->int:
    chromium=next((n for n in ('chromium','chromium-browser','google-chrome','google-chrome-stable') if shutil.which(n)),None)
    if not chromium:
        print('SKIP: Chromium unavailable')
        return 0
    html=f'''<!doctype html><html><head><meta charset="utf-8"><base href="{ORIGIN}/"><style>.panel{{padding:8px}}.panel-body{{display:block}}</style></head><body data-result="pending">
    <aside class="sidebar"><div id="dataSyncPanelV476" class="panel" data-collapse-key="dataSync" data-manual-collapse="true" data-skip-auto-collapsible="true"><h2>Data Sync</h2><div class="panel-body"><div class="row"><button id="dsAction">Refresh Data Sync</button><span id="missionCount">0 missions</span></div><div id="dataSyncRows"><div class="muted">Loading missions...</div></div></div></div></aside><pre id="result"></pre>
    <script>
    window.__refreshCalls=[];
    window.refreshDataSync=async function(force,reason){{window.__refreshCalls.push([!!force,reason||'']);const u='{ORIGIN}/api/tak-map/data-sync'+(force?'?force=1&reason='+encodeURIComponent(reason||'force'):'?reason='+(reason||'interval'));const r=await fetch(u);return r.json()}};
    window.forceDataSyncSync=async function(reason){{const out=await window.refreshDataSync(true,reason||'force');setTimeout(()=>window.refreshDataSync(true,(reason||'force')+'-followup-1'),25);setTimeout(()=>window.refreshDataSync(true,(reason||'force')+'-followup-2'),50);setTimeout(()=>window.refreshDataSync(true,(reason||'force')+'-followup-3'),75);return out}};
    window.sweepTakMapOrphanMissionLayersV391=()=>fetch('{ORIGIN}/api/tak-map/data-sync?force=1&reason=v391-orphan-sweep').then(r=>r.json());
    window.sweepTakMapOrphanMissionLayersV392=()=>fetch('{ORIGIN}/api/tak-map/data-sync?force=1&reason=v392-sweep').then(r=>r.json());
    window.map={{hasLayer:()=>false,addLayer(){{}},removeLayer(){{}}}};window.dataSyncLayer={{}};
    </script>
    <script src="{ORIGIN}/assets/runtime/tak-map-data-sync-v491.js"></script><script src="{ORIGIN}/assets/runtime/tak-map-card-controls-v491.js"></script>
    <script>
    setTimeout(async()=>{{try{{
      // Simulate the old fan-out: many sweeps and concurrent normal refreshes.
      const burst=[];for(let i=0;i<24;i++){{burst.push(fetch('{ORIGIN}/api/tak-map/data-sync?force=1&reason='+(i%2?'v391-orphan-sweep':'v392-sweep')).then(r=>r.json()))}}
      for(let i=0;i<8;i++)burst.push(fetch('{ORIGIN}/api/tak-map/data-sync?reason=interval').then(r=>r.json()));
      await Promise.all(burst);await new Promise(r=>setTimeout(r,550));
      const beforeOff=TakMapDataSyncControlV476.diagnostics();const panel=document.getElementById('dataSyncPanelV476'),button=panel.querySelector('.tak-header-switch-button-v491'),input=document.getElementById('dataSyncHeaderEnableV476'),collapsedBefore=panel.classList.contains('tak-card-collapsed-v491');
      button.click();await new Promise(r=>setTimeout(r,40));const disabled=!input.checked&&!TakMapDataSyncControlV476.isEnabled()&&localStorage.getItem('takmap.dataSync.disabled')==='1'&&panel.classList.contains('tak-card-collapsed-v491')===collapsedBefore;
      const netBeforeDisabled=beforeOff.networkRequests;const disabledResponse=await fetch('{ORIGIN}/api/tak-map/data-sync?reason=interval').then(r=>r.json());await window.forceDataSyncSync('disabled-force');await new Promise(r=>setTimeout(r,80));const disabledDiag=TakMapDataSyncControlV476.diagnostics();const noNetworkWhileDisabled=disabledDiag.networkRequests===netBeforeDisabled&&disabledResponse.data_sync_control?.kind==='disabled';
      document.getElementById('dsAction').click();const actionBlocked=panel.dataset.dataSyncStatus==='Enable Data Sync to use this action.'||document.getElementById('dataSyncRows').textContent.includes('Enable Data Sync');
      button.click();await new Promise(r=>setTimeout(r,500));const afterOn=TakMapDataSyncControlV476.diagnostics();const enabled=input.checked&&TakMapDataSyncControlV476.isEnabled()&&localStorage.getItem('takmap.dataSync.disabled')==='0';
      const networkBounded=afterOn.networkRequests<=2&&beforeOff.networkRequests<=1&&(beforeOff.coalesced>=1||beforeOff.suppressedMinInterval>=8)&&beforeOff.suppressedLegacy>=24;
      const apiOwned=afterOn.apiOwnersInstalled&&afterOn.legacySweepsNeutralized&&typeof window.forceDataSyncSync==='function';
      const pass=disabled&&noNetworkWhileDisabled&&actionBlocked&&enabled&&networkBounded&&apiOwned&&!panel.classList.contains('tak-card-collapsed-v491');
      document.body.dataset.result=pass?'pass':'fail';document.getElementById('result').textContent=JSON.stringify({{beforeOff,afterOn,disabled,noNetworkWhileDisabled,actionBlocked,enabled,networkBounded,apiOwned,networkCount:afterOn.networkRequests,refreshCalls:window.__refreshCalls}})
    }}catch(e){{document.body.dataset.result='error';document.getElementById('result').textContent=String(e&&e.stack||e)}}}},350)
    </script></body></html>'''
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=shutil.which(chromium),args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
        page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        def route(r):
            url=r.request.url
            if url.startswith(ORIGIN+'/assets/runtime/tak-map-data-sync-v491.js'):
                r.fulfill(status=200,content_type='application/javascript; charset=utf-8',body=DS_ASSET.read_text())
            elif url.startswith(ORIGIN+'/assets/runtime/tak-map-card-controls-v491.js'):
                r.fulfill(status=200,content_type='application/javascript; charset=utf-8',body=CARD_ASSET.read_text())
            elif '/api/tak-map/data-sync' in url:
                r.fulfill(status=200,content_type='application/json',body=json.dumps({'ok':True,'objects':[{'uid':'A'}],'missions':[{'name':'M'}]}))
            else:r.fulfill(status=404,body='not found')
        page.route('**/*',route);page.evaluate("(()=>{const s={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>Object.prototype.hasOwnProperty.call(s,k)?s[k]:null,setItem:(k,v)=>{s[k]=String(v)},removeItem:k=>{delete s[k]},clear:()=>{Object.keys(s).forEach(k=>delete s[k])}}})})()");page.set_content(html,wait_until='domcontentloaded');page.wait_for_function("document.body.dataset.result !== 'pending'",timeout=10000)
        result=page.get_attribute('body','data-result');detail=page.text_content('#result') or '';browser.close()
    if result!='pass' or errors:raise AssertionError(f'{result}: {detail}; errors={errors}')
    parsed=json.loads(detail);print('Data Sync toggle/single-flight browser test passed');print(json.dumps({k:parsed[k] for k in ('networkCount','disabled','noNetworkWhileDisabled','actionBlocked','enabled','networkBounded','apiOwned')},sort_keys=True));return 0

if __name__=='__main__':raise SystemExit(main())
