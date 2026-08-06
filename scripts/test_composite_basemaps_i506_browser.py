#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import runpy
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    chromium = next((n for n in ('chromium','chromium-browser','google-chrome','google-chrome-stable') if shutil.which(n)), None)
    if not chromium:
        print('SKIP: Chromium unavailable')
        return 0

    with tempfile.TemporaryDirectory(prefix='tak-map-i506-browser-') as td:
        os.environ['TAK_DASHBOARD_DATA_DIR'] = td
        module = runpy.run_path(str(ROOT/'tak_dashboard.py'), run_name='tak_dashboard_i506_browser')
        production = module['TAK_MAP_HTML']
        match = re.search(r'(<style id="takMapBasemapManagementStyleV506">[\s\S]*?<script id="takMapBasemapManagementV506">[\s\S]*?</script>)', production)
        assert match, 'i506 basemap-management client patch not found'
        patch = match.group(1)

        fixture = f'''<!doctype html><html><head><meta charset="utf-8"></head><body>
<div class="basemap-button-row">
  <button>Send Map</button><button>Add Basemap</button>
  <button id="gatewayButton" onclick="importTakGatewayBasemapsV506()">Import Gateway</button>
  <button id="managerButton" onclick="openBasemapManagerV506()">Manage Basemaps</button>
  <input id="basemapXmlInput" type="file" multiple style="display:none">
  <small id="customBasemapStatus"></small>
  <div id="basemapSummaryV506" class="tak-basemap-summary-v506"><div><b id="basemapSummaryMainV506">0 imported basemaps</b><small id="basemapSummarySubV506"></small></div><button type="button" onclick="openBasemapManagerV506()">Manage</button></div>
  <div id="customBasemapRowsV505"><div class="legacy-visible-row">SHOULD NOT DISPLAY</div></div>
</div>
<select id="basemapSelect"></select>
<div class="relief-controls tak-relief-controls-v506">
  <input type="checkbox" id="reliefOverlayToggle" aria-hidden="true">
  <button id="reliefOverlayButtonV506" class="tak-relief-toggle-v506" type="button" aria-pressed="false" onclick="toggleReliefButtonV506()">USGS Shaded Relief</button>
  <div class="tak-relief-slider-row-v442"><input id="reliefOpacity" type="range" min="0" max="100" value="35"><span>35%</span></div>
</div>
<script>
let activeBasemap='esri_topo';
const built={{id:'esri_topo',label:'Esri Topo',group:'Topo / Terrain',url:'https://example/{{z}}/{{x}}/{{y}}.png',minZoom:0,maxZoom:19}};
let config={{default_basemap:'esri_topo',basemaps:[built]}};
window.__active='esri_topo';window.__reliefCalls=[];window.__calls=[];window.__serverBasemaps=[];
const gatewayNames=[
 ['g-noaa-img','TG-ESRI-Img+NOAA','NOAA Radar'],['g-noaa-strt','TG-ESRI-Strt+NOAA','NOAA Radar'],
 ['g-rain-img','TG-ESRI-Img+RainViewer','RainViewer'],['g-rain-strt','TG-ESRI-Strt+RainViewer','RainViewer'],
 ['g-imerg-img','TG-ESRI-Img+IMERG','NASA IMERG'],['g-imerg-strt','TG-ESRI-Strt+IMERG','NASA IMERG'],
 ['g-goes18-img','TG-ESRI-Img+GOES-18','GOES-18 Pacific'],['g-goes18-strt','TG-ESRI-Strt+GOES-18','GOES-18 Pacific'],
 ['g-goes19-img','TG-ESRI-Img+GOES-19','GOES-19 Atlantic'],['g-goes19-strt','TG-ESRI-Strt+GOES-19','GOES-19 Atlantic']
];
const gatewayMaps=gatewayNames.map(x=>({{id:x[0],label:x[1],group:'TAK Gateway Composite',managementType:'gateway',managementSource:x[2],importedBasemap:true,serverPersisted:true,precacheAllowed:false,minZoom:2,maxZoom:22,url:'/api/tak-map/custom-basemap-tile/'+x[0]+'/{{z}}/{{x}}/{{y}}.png'}}));
const customMaps=[
 {{id:'c-topo',label:'County Topographic Overlay',group:'Custom',managementType:'custom',managementSource:'Custom XML',importedBasemap:true,minZoom:4,maxZoom:18,url:'/api/tak-map/custom-basemap-tile/c-topo/{{z}}/{{x}}/{{y}}.png'}},
 {{id:'c-sar',label:'SAR Planning Grid',group:'Custom',managementType:'custom',managementSource:'Custom XML',importedBasemap:true,minZoom:3,maxZoom:19,url:'/api/tak-map/custom-basemap-tile/c-sar/{{z}}/{{x}}/{{y}}.png'}}
];
function setBasemap(id){{activeBasemap=id;window.__active=id;renderBasemaps()}}
function renderBasemaps(){{
 const sel=document.getElementById('basemapSelect');const current=activeBasemap;sel.innerHTML='';
 const order=['Offline Maps','TAK Gateway Composite','Imagery','Topo / Terrain','Street / Reference','Custom','Basemaps'];
 for(const group of order){{const rows=config.basemaps.filter(b=>(b.group||'Basemaps')===group);if(!rows.length)continue;const og=document.createElement('optgroup');og.label=group;for(const b of rows){{const o=document.createElement('option');o.value=b.id;o.textContent=b.label;og.appendChild(o)}}sel.appendChild(og)}}sel.value=current;
}}
function toggleReliefOverlay(on){{window.__reliefCalls.push(!!on)}}
function response(message){{return new Response(JSON.stringify({{ok:true,message,basemaps:[built,...window.__serverBasemaps]}}),{{status:200,headers:{{'Content-Type':'application/json'}}}})}}
window.fetch=async (url,opt={{}})=>{{
 const u=String(url);window.__calls.push({{url:u,method:opt.method||'GET'}});
 if(u.endsWith('import-gateway')){{window.__serverBasemaps=[...gatewayMaps,...customMaps];return response('Imported or refreshed 10 TAK Gateway composite basemap(s).')}}
 if(u.endsWith('custom-basemaps'))return response('Imported basemaps loaded.');
 if(u.endsWith('custom-basemap-delete')){{const body=JSON.parse(opt.body||'{{}}');window.__serverBasemaps=window.__serverBasemaps.filter(x=>x.id!==body.id);return response('Imported basemap removed.')}}
 if(u.endsWith('custom-basemap-bulk-delete')){{const body=JSON.parse(opt.body||'{{}}');window.__serverBasemaps=window.__serverBasemaps.filter(x=>body.scope==='gateway'?x.managementType!=='gateway':x.managementType==='gateway');return response('Imported basemaps removed.')}}
 if(u.endsWith('custom-basemap-upload'))return response('Imported XML.');
 return new Response(JSON.stringify({{ok:false,error:'unexpected '+u}}),{{status:404,headers:{{'Content-Type':'application/json'}}}});
}};
renderBasemaps();
</script>{patch}</body></html>'''

        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, executable_path=shutil.which(chromium), args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
            page = browser.new_page(viewport={'width':1100,'height':850})
            errors=[]
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.set_content(fixture, wait_until='domcontentloaded', timeout=30000)
            page.wait_for_function("window.TakMapBasemapManagementV506 && TakMapBasemapManagementV506.diagnostics().manager", timeout=7000)

            assert page.locator('#customBasemapRowsV505').evaluate("el=>getComputedStyle(el).display") == 'none'
            page.locator('#gatewayButton').click()
            page.wait_for_function("document.getElementById('basemapSummaryMainV506').textContent==='12 imported basemaps'", timeout=7000)
            imported = page.evaluate("""()=>({
              summary:document.getElementById('basemapSummaryMainV506').textContent,
              detail:document.getElementById('basemapSummarySubV506').textContent,
              gatewayOptions:[...document.querySelectorAll('#basemapSelect optgroup')].find(x=>x.label==='TAK Gateway Composite')?.querySelectorAll('option').length||0,
              diag:TakMapBasemapManagementV506.diagnostics()
            })""")
            assert imported['gatewayOptions']==10, imported
            assert imported['detail']=='10 TAK Gateway Composite · 2 Custom XML', imported
            assert imported['diag']['inlineRows'] is False and imported['diag']['clientComposition'] is False, imported

            page.locator('#managerButton').click()
            page.wait_for_selector('#basemapManagerBackdropV506.open')
            manager = page.evaluate("""()=>({gateway:document.querySelectorAll('#basemapGatewayRowsV506 .tak-bm-row-v506').length,custom:document.querySelectorAll('#basemapCustomRowsV506 .tak-bm-row-v506').length,count:document.getElementById('basemapManagerCountV506').textContent})""")
            assert manager=={'gateway':10,'custom':2,'count':'12 IMPORTED'}, manager

            page.locator('#basemapManagerSearchV506').fill('GOES-19')
            search_result = page.evaluate("""()=>[...document.querySelectorAll('.tak-bm-row-v506')].filter(x=>getComputedStyle(x).display!=='none').map(x=>x.textContent)""")
            assert len(search_result)==2 and all('GOES-19' in x for x in search_result), search_result
            page.locator('#basemapManagerSearchV506').fill('')

            page.evaluate("setBasemap('g-noaa-img')")
            page.locator('#basemapGatewayRowsV506 .tak-bm-remove-v506').first.click()
            assert page.locator('#basemapManagerConfirmV506').evaluate("el=>el.classList.contains('open')")
            page.locator('#basemapConfirmApproveV506').click()
            page.wait_for_function("window.__active==='esri_topo' && document.querySelectorAll('#basemapGatewayRowsV506 .tak-bm-row-v506').length===9", timeout=7000)

            page.locator('#basemapManagerBulkV506').click()
            page.locator('#basemapManagerBulkMenuV506 [data-scope="custom"]').click()
            assert page.locator('#basemapManagerConfirmV506').evaluate("el=>el.classList.contains('open')")
            page.locator('#basemapConfirmApproveV506').click()
            page.wait_for_function("document.querySelectorAll('#basemapCustomRowsV506 .tak-bm-row-v506').length===0", timeout=7000)

            page.locator('#basemapManagerDoneV506').click()
            page.wait_for_function("!document.getElementById('basemapManagerBackdropV506').classList.contains('open')")
            relief = page.locator('#reliefOverlayButtonV506')
            assert relief.get_attribute('aria-pressed')=='false'
            off_bg = relief.evaluate("el=>getComputedStyle(el).backgroundImage")
            relief.click()
            assert relief.get_attribute('aria-pressed')=='true'
            assert page.locator('#reliefOverlayToggle').is_checked()
            on_bg = relief.evaluate("el=>getComputedStyle(el).backgroundImage")
            assert off_bg != on_bg and 'rgb(220, 228, 232)' in on_bg, (off_bg,on_bg)
            assert page.evaluate("window.__reliefCalls") == [True]
            assert page.locator('#reliefOpacity').input_value() == '35'
            relief.click()
            assert relief.get_attribute('aria-pressed')=='false'
            assert page.evaluate("window.__reliefCalls") == [True, False]

            final = page.evaluate("""()=>({
              active:window.__active,
              summary:document.getElementById('basemapSummaryMainV506').textContent,
              gateway:document.querySelectorAll('#basemapGatewayRowsV506 .tak-bm-row-v506').length,
              custom:document.querySelectorAll('#basemapCustomRowsV506 .tak-bm-row-v506').length,
              calls:window.__calls
            })""")
            browser.close()

        assert not errors, errors
        assert final['active']=='esri_topo' and final['gateway']==9 and final['custom']==0, final
        assert any(x['url'].endswith('custom-basemap-delete') for x in final['calls']), final
        assert any(x['url'].endswith('custom-basemap-bulk-delete') for x in final['calls']), final
        print('TAK Map i506 composite basemap management/relief browser test passed')
        print(json.dumps({'imported':imported,'manager':manager,'final':final},sort_keys=True))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
