#!/usr/bin/env python3
from __future__ import annotations
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / 'assets' / 'tak-map-card-controls-v491.js'
COMBINED = ROOT / 'combined_scripts_v287.js'
ORIGIN = 'http://localhost'


def v414_block() -> str:
    src = COMBINED.read_text()
    start = src.index("(function(){\n  'use strict';\n  const V='v414'")
    end = src.index("\n})();", start) + len("\n})();")
    block = src[start:end]
    assert "panel.dataset.manualCollapse==='true'||panel.dataset.skipAutoCollapsible==='true'" in block
    assert "__takMapAdsbCollapseObserverV414" in block
    assert "11500" in block
    return block


def main() -> int:
    chromium = next((n for n in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable') if shutil.which(n)), None)
    if not chromium:
        print('SKIP: Chromium unavailable')
        return 0

    html = f'''<!doctype html><html><head><meta charset="utf-8"><base href="{ORIGIN}/"><style>
    body{{background:#06090d;color:#e9f0f5}}.panel{{border:1px solid #273642;padding:12px}}.panel-body{{display:block}}.panel.collapsed .panel-body{{display:none}}.chip{{border:1px solid #555}}
    </style></head><body data-result="pending"><aside id="sidebar" class="sidebar">
    <div class="panel" data-collapse-key="localData"><h2 onclick="togglePanelCollapse(this)">Local Data <span class="panel-toggle">▾</span></h2><div class="panel-body"><div class="row"><span class="chip" id="localDataCount">4</span></div><div id="localDataRows"></div></div></div>
    <div class="panel" data-collapse-key="adsbSettings"><h2 onclick="togglePanelCollapse(this)">ADS-B <span class="panel-toggle">▾</span></h2><div class="panel-body"><div id="bannerAdsb">7 Aircraft</div><div id="adsbV270Menu"><div class="adsb-v270-top"><button id="adsbToggleBtn">Disable ADS-B</button></div><div class="adsb-settings-grid"><label>Radius Miles<input id="adsbRadiusMiles" type="number" value="10"></label><label>Update Interval (sec)<input id="adsbUpdateInterval" type="number" value="5"></label><label>Center Source<select id="adsbCenterSource"><option value="follow_map_center">Follow Map Center</option></select></label><label>Center Lat/Lon<input id="adsbCenterLatLon" value="34.1,-118.2"></label></div><div class="adsb-filter-box"><label class="legacy-filter"><span>Civil</span><input id="adsbFilterCivil" type="checkbox" checked></label><label class="legacy-filter"><span>Military</span><input id="adsbFilterMilitary" type="checkbox" checked></label><label class="legacy-filter"><span>Govt</span><input id="adsbFilterGovt" type="checkbox" checked></label><label class="legacy-filter"><span>Unknown</span><input id="adsbFilterUnknown" type="checkbox" checked></label></div></div></div></div>
    <div id="satelliteTrackingPanelV409" class="panel"><h2>Satellite Tracking</h2><div class="row"><label><input id="satEnableV409" type="checkbox" checked><span>Enable Satellite Tracking</span></label><span class="chip" id="satVisibleCountV409">4 visible</span></div><div class="sat-grid"><label>Update sec<input id="satUpdateSecV409" type="number" min="5" max="600" step="5" value="30"></label></div></div>
    <div id="dataSyncPanelV476" class="panel"><h2>Data Sync</h2><div class="row"><button id="dsAction">Refresh Data Sync</button><span class="chip" id="missionCount">2 missions</span><span class="chip" id="dataSyncObjectCount">5 objects</span></div><div id="dataSyncRows"></div></div>
    </aside><pre id="result"></pre>
    <script>
    window.togglePanelCollapse=function(h){{const p=h.closest('.panel');p.classList.toggle('collapsed')}};
    window.state={{imported:true}};window.__localToggleCalls=[];window.toggleImportedObjects=on=>{{window.state.imported=!!on;window.__localToggleCalls.push(!!on)}};window.localDataSets=()=>({{points:[1,2],routes:[3],shapes:[4]}});window.lastDataSync={{missions:[{{}},{{}}],objects:[{{}},{{}},{{}},{{}},{{}}],packages:[]}};
    window.__adsbCalls=[];window.TakMapAdsbWorkerV476={{snapshot(){{return Array.from({{length:7}},(_,i)=>({{id:i}}))}},enable(){{window.__adsbCalls.push('enable');localStorage.setItem('takmap.adsb.localDisabled','0')}},disable(){{window.__adsbCalls.push('disable');localStorage.setItem('takmap.adsb.localDisabled','1')}}}};
    window.__dsCalls=[];window.TakMapDataSyncControlV476={{_on:true,isEnabled(){{return this._on}},setEnabled(on,reason){{this._on=!!on;window.__dsCalls.push([!!on,reason]);localStorage.setItem('takmap.dataSync.disabled',on?'0':'1');return Promise.resolve({{ok:true}})}}}};
    {v414_block()}
    setTimeout(()=>{{const s=document.createElement('script');s.src='{ORIGIN}/assets/runtime/tak-map-card-controls-v491.js';document.head.appendChild(s)}},180);
    setTimeout(()=>{{try{{
      const api=TakMapCardControlsV477,d=api.diagnostics();
      const adsbPanel=document.querySelector('[data-collapse-key="adsbSettings"]'),adsbHeader=adsbPanel.querySelector(':scope>h2'),adsbButton=adsbHeader.querySelector('.tak-header-switch-button-v491'),adsbInput=document.getElementById('adsbHeaderEnableV476');
      const legacyBefore=getTakMapAdsbCollapseDiagnosticsV414();const before=adsbPanel.classList.contains('tak-card-collapsed-v491');adsbButton.click();
      const adsbOff=!adsbInput.checked&&localStorage.getItem('takmap.adsb.localDisabled')==='1'&&window.__adsbCalls.at(-1)==='disable';
      const toggleIndependent=adsbPanel.classList.contains('tak-card-collapsed-v491')===before&&!adsbPanel.classList.contains('collapsed');
      adsbButton.click();const adsbOn=adsbInput.checked&&localStorage.getItem('takmap.adsb.localDisabled')==='0'&&window.__adsbCalls.at(-1)==='enable';
      adsbHeader.querySelector('.tak-card-title-v491').click();const headerCollapses=adsbPanel.classList.contains('tak-card-collapsed-v491');adsbHeader.querySelector('.tak-card-chevron-v491').click();const headerReopens=!adsbPanel.classList.contains('tak-card-collapsed-v491');
      const filterRows=[...document.querySelectorAll('.adsb-type-grid-v491 > .adsb-type-card-v491')];const filterLabels=filterRows.map(x=>x.querySelector('.type-name,.adsb-type-name-v491')?.childNodes?.[0]?.textContent?.trim()||x.querySelector('.adsb-type-name-v491')?.textContent?.trim());const filterOrder=filterRows.map(x=>x.dataset.type).join('|')==='civil|govt|military|unknown';const filterThemed=filterRows.length===4&&filterRows.every(r=>r.querySelector('input.adsb-type-checkbox-v491')&&r.querySelector('.adsb-type-badge-v491')&&r.querySelector('.adsb-type-check-v491'))&&document.querySelectorAll('.legacy-filter').length===0;
      const govt=document.getElementById('adsbFilterGovt');let govtChanges=0;govt.addEventListener('change',()=>govtChanges++);govt.click();const filterFunctional=govtChanges===1&&!govt.checked;
      const altMode=document.getElementById('adsbAltitudeFilterV477'),altInput=document.getElementById('adsbAltitudeThresholdV477'),altUnit=document.getElementById('adsbAltitudeUnitV477'),filterLabel=altMode.closest('label'),altLabel=altInput.closest('label'),sourceLabel=document.getElementById('adsbCenterSource').closest('label'),centerLabel=document.getElementById('adsbCenterLatLon').closest('label');const altitudeOrder=Math.abs(filterLabel.getBoundingClientRect().top-altLabel.getBoundingClientRect().top)<2&&Math.abs(sourceLabel.getBoundingClientRect().top-centerLabel.getBoundingClientRect().top)<2;const allDisabled=altMode.value==='all'&&altInput.disabled&&altUnit.disabled;altMode.value='above';altMode.dispatchEvent(new Event('change',{{bubbles:true}}));const aboveEnabled=!altInput.disabled&&!altUnit.disabled;altInput.value='10000';altInput.dispatchEvent(new Event('change',{{bubbles:true}}));const beforeUnit=altUnit.textContent;altUnit.click();const unitSwitched=beforeUnit==='ft'&&altUnit.textContent==='m'&&localStorage.getItem('takmap.adsb.altitude.unit')==='m'&&Number(localStorage.getItem('takmap.adsb.altitude.thresholdMeters'))>3047&&Number(localStorage.getItem('takmap.adsb.altitude.thresholdMeters'))<3049;const unitWhite=getComputedStyle(altUnit).color==='rgb(255, 255, 255)';
      const sat=document.getElementById('satelliteTrackingPanelV409'),satInput=document.getElementById('satEnableV409'),satButton=sat.querySelector('.tak-header-switch-button-v491'),satBefore=sat.classList.contains('tak-card-collapsed-v491');satButton.click();const satIndependent=!satInput.checked&&sat.classList.contains('tak-card-collapsed-v491')===satBefore;sat.querySelector('.tak-card-title-v491').click();const satHeaderCollapses=sat.classList.contains('tak-card-collapsed-v491');sat.querySelector('.tak-card-title-v491').click();const satHeaderReopens=!sat.classList.contains('tak-card-collapsed-v491');
      const step=document.getElementById('satUpdateSecV409'),up=document.querySelector('.tak-sat-step-buttons-v491 [data-dir="1"]');up.click();const stepperWorks=step.value==='35';
      const ds=document.getElementById('dataSyncPanelV476'),dsInput=document.getElementById('dataSyncHeaderEnableV476'),dsButton=ds.querySelector('.tak-header-switch-button-v491'),dsBefore=ds.classList.contains('tak-card-collapsed-v491');dsButton.click();const dsOff=!dsInput.checked&&window.__dsCalls.at(-1)?.[0]===false&&ds.classList.contains('tak-card-collapsed-v491')===dsBefore;dsButton.click();const dsOn=dsInput.checked&&window.__dsCalls.at(-1)?.[0]===true;
      const localPanel=document.querySelector('[data-collapse-key="localData"]'),localHeader=localPanel.querySelector(':scope>h2'),localChip=document.getElementById('localDataCount'),localInput=document.getElementById('localDataHeaderEnableV486'),localButton=localHeader.querySelector('.tak-header-switch-button-v491');const localHeaderText=localChip.textContent,localInHeader=localChip.closest('h2')===localHeader,localToggleInHeader=!!localInput&&!!localButton&&localButton.closest('h2')===localHeader;const localCollapsedBefore=localPanel.classList.contains('collapsed');localButton.click();const localOff=!localInput.checked&&window.state.imported===false&&window.__localToggleCalls.at(-1)===false&&localPanel.classList.contains('collapsed')===localCollapsedBefore;localButton.click();const localOn=localInput.checked&&window.state.imported===true&&window.__localToggleCalls.at(-1)===true;localHeader.querySelector('.tak-card-title-v491')?.click();const localVisibleCollapsed=getComputedStyle(localChip).display!=='none'&&!localChip.hidden&&getComputedStyle(localButton).display!=='none';localHeader.querySelector('.tak-card-title-v491')?.click();
      const adsbChip=document.getElementById('adsbHeaderCountV486'),dataSyncChip=document.getElementById('dataSyncHeaderCountV486'),satChip=document.getElementById('satVisibleCountV409');const adsbCountText=adsbChip?.textContent||'';const dataSyncCountText=dataSyncChip?.textContent||'';const dataSyncObjectHidden=document.getElementById('dataSyncObjectCount')?.hidden===true;
      const chipStyle=el=>{{const x=getComputedStyle(el);return [x.fontFamily,x.fontSize,x.fontWeight,x.letterSpacing,x.lineHeight,x.paddingTop,x.paddingRight,x.borderRadius,x.backgroundColor,x.color].join('|')}};const countChipStylesMatch=[adsbChip,dataSyncChip,satChip].every(el=>el&&el.classList.contains('tak-header-count-v491')&&chipStyle(el)===chipStyle(localChip));
      const legacyAfter=getTakMapAdsbCollapseDiagnosticsV414(),d2=api.diagnostics();
      const pass=d.captureSwitchOwner&&d.legacyAdsbObserverDisconnected&&d.adsbHeader&&d.adsbHeaderToggle&&d.adsbManualCollapseOwner&&d.adsbInternalButtonHidden&&d.adsbFilters&&d.adsbFilterRows===4&&d.adsbFilterInputsThemed===4&&d2.adsbAltitude&&d2.adsbAltitudeMode==='above'&&d2.adsbAltitudeUnit==='m'&&d2.adsbAltitudeUnitWhite&&altitudeOrder&&allDisabled&&aboveEnabled&&unitSwitched&&unitWhite&&d.satelliteHeader&&d.satelliteHeaderToggle&&d.satelliteManualCollapseOwner&&d.satelliteInternalEnableRowRemoved&&d.satelliteStepper&&d.dataSyncHeader&&d.dataSyncHeaderToggle&&d.dataSyncManualCollapseOwner&&localHeaderText==='4 ITEMS'&&localInHeader&&localToggleInHeader&&localOff&&localOn&&localVisibleCollapsed&&adsbCountText==='7 AIRCRAFT'&&dataSyncCountText==='2 MIS, 5 ITEMS'&&dataSyncObjectHidden&&countChipStylesMatch&&adsbOff&&adsbOn&&toggleIndependent&&headerCollapses&&headerReopens&&filterOrder&&filterThemed&&filterFunctional&&satIndependent&&satHeaderCollapses&&satHeaderReopens&&stepperWorks&&dsOff&&dsOn&&!legacyAfter.patched&&!adsbPanel.classList.contains('collapsed');
      document.body.dataset.result=pass?'pass':'fail';document.getElementById('result').textContent=JSON.stringify({{d,legacyBefore,legacyAfter,adsbOff,adsbOn,toggleIndependent,headerCollapses,headerReopens,filterLabels,filterThemed,filterFunctional,altitudeOrder,allDisabled,aboveEnabled,unitSwitched,unitWhite,altitudeMode:d2.adsbAltitudeMode,altitudeUnit:d2.adsbAltitudeUnit,d2,satIndependent,satHeaderCollapses,satHeaderReopens,stepperWorks,dsOff,dsOn,adsbCalls:window.__adsbCalls,dsCalls:window.__dsCalls,localHeaderText,localInHeader,localToggleInHeader,localOff,localOn,localToggleCalls:window.__localToggleCalls,localVisibleCollapsed,adsbCountText,dataSyncCountText,dataSyncObjectHidden,countChipStylesMatch,localChipStyle:chipStyle(localChip),adsbChipStyle:chipStyle(adsbChip),satChipStyle:chipStyle(satChip),dataSyncChipStyle:chipStyle(dataSyncChip)}});
    }}catch(e){{document.body.dataset.result='error';document.getElementById('result').textContent=String(e&&e.stack||e)}}}},12450)
    </script></body></html>'''

    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=shutil.which(chromium), args=['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'])
        page = browser.new_page()
        errors: list[str] = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        def route(r):
            if r.request.url.startswith(ORIGIN + '/assets/runtime/tak-map-card-controls-v491.js'):
                r.fulfill(status=200, content_type='application/javascript; charset=utf-8', body=ASSET.read_text())
            else:
                r.fulfill(status=404, body='not found')
        page.route('**/*', route)
        page.evaluate("(()=>{const s={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>Object.prototype.hasOwnProperty.call(s,k)?s[k]:null,setItem:(k,v)=>{s[k]=String(v)},removeItem:k=>{delete s[k]},clear:()=>{Object.keys(s).forEach(k=>delete s[k])}}})})()")
        page.set_content(html, wait_until='domcontentloaded')
        page.wait_for_function("document.body.dataset.result !== 'pending'", timeout=18000)
        result = page.get_attribute('body', 'data-result')
        detail = page.text_content('#result') or ''
        browser.close()
    if result != 'pass' or errors:
        raise AssertionError(f'{result}: {detail}; errors={errors}')
    parsed = json.loads(detail)
    print('Card controls visible-track/legacy-v414 browser test passed')
    print(json.dumps({k: parsed[k] for k in ('adsbOff','adsbOn','toggleIndependent','filterLabels','altitudeOrder','unitSwitched','unitWhite','satIndependent','dsOff','dsOn','localHeaderText','localInHeader','localToggleInHeader','localOff','localOn','localVisibleCollapsed','adsbCountText','dataSyncCountText','dataSyncObjectHidden','countChipStylesMatch')}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
