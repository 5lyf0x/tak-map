#!/usr/bin/env python3
from __future__ import annotations

import html as htmlmod
import json
import re
import runpy
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    chromium = next((n for n in ('chromium','chromium-browser','google-chrome','google-chrome-stable') if shutil.which(n)), None)
    if not chromium:
        print('SKIP: Chromium unavailable'); return 0

    with tempfile.TemporaryDirectory(prefix='tak-map-i505-browser-') as td:
        import os
        os.environ['TAK_DASHBOARD_DATA_DIR'] = td
        module = runpy.run_path(str(ROOT/'tak_dashboard.py'), run_name='tak_dashboard_i505_browser')
        production = module['TAK_MAP_HTML']
        match = re.search(r'(<style id="takMapCompositeBasemapStyleV505">[\s\S]*?<script id="takMapCompositeBasemapsV505">[\s\S]*?</script>)', production)
        assert match, 'i505 client patch not found in generated HTML'
        patch = match.group(1)
        assert "const order=['Offline Maps','TAK Gateway Composite','Imagery'" in production

        fixture = f'''<!doctype html><html><head><meta charset="utf-8"></head><body>
<div class="basemap-button-row">
<button id="send">Send Map</button><button id="add">Add Basemap</button>
<button id="gateway" onclick="importTakGatewayBasemapsV505()">Import Gateway</button>
<button id="clear" onclick="clearCustomBasemaps()">Clear Custom</button>
<input id="basemapXmlInput" type="file" multiple style="display:none">
<small id="customBasemapStatus"></small><div id="customBasemapRowsV505"></div>
</div><select id="basemapSelect"></select>
<script>
let config={{default_basemap:'esri_topo',basemaps:[{{id:'esri_topo',label:'Esri Topo',group:'Topo / Terrain',url:'https://example/{{z}}/{{x}}/{{y}}.png'}}]}};
let activeBasemap='esri_topo';
function setBasemap(id){{activeBasemap=id;window.__active=id}}
function renderBasemaps(){{
 const sel=document.getElementById('basemapSelect'); const current=activeBasemap; sel.innerHTML='';
 const order=['Offline Maps','TAK Gateway Composite','Imagery','Topo / Terrain','Street / Reference','Custom','Basemaps'];
 for(const group of order){{const rows=config.basemaps.filter(b=>(b.group||'Basemaps')===group);if(!rows.length)continue;const og=document.createElement('optgroup');og.label=group;for(const b of rows){{const o=document.createElement('option');o.value=b.id;o.textContent=b.label;og.appendChild(o)}}sel.appendChild(og)}}
 sel.value=current;
}}
function loadCustomBasemaps(){{return [{{id:'legacy'}}]}} function saveCustomBasemaps(){{}} function applyCustomBasemaps(){{}} function importBasemapXmlFiles(){{}} function clearCustomBasemaps(){{}}
window.__calls=[]; window.__serverBasemaps=[];
const built={{id:'esri_topo',label:'Esri Topo',group:'Topo / Terrain',url:'https://example/{{z}}/{{x}}/{{y}}.png'}};
const gatewayMaps=[
 {{id:'custom_xml_img',label:'TG-ESRI-Img+Radar',group:'TAK Gateway Composite',url:'/api/tak-map/custom-basemap-tile/custom_xml_img/{{z}}/{{x}}/{{y}}.png',minZoom:3,maxZoom:23,importedBasemap:true,serverPersisted:true,precacheAllowed:false}},
 {{id:'custom_xml_street',label:'TG-ESRI-Strt+Radar',group:'TAK Gateway Composite',url:'/api/tak-map/custom-basemap-tile/custom_xml_street/{{z}}/{{x}}/{{y}}.png',minZoom:3,maxZoom:23,importedBasemap:true,serverPersisted:true,precacheAllowed:false}}
];
function response(message){{return new Response(JSON.stringify({{ok:true,message,basemaps:[built,...window.__serverBasemaps]}}),{{status:200,headers:{{'Content-Type':'application/json'}}}})}}
window.fetch=async (url,opt={{}})=>{{
 window.__calls.push({{url:String(url),method:opt.method||'GET',isForm:opt.body instanceof FormData}});
 if(String(url).endsWith('import-gateway')){{window.__serverBasemaps=[...gatewayMaps];return response('Imported 2 TAK Gateway composite basemap(s).')}}
 if(String(url).endsWith('upload')){{window.__serverBasemaps=[...window.__serverBasemaps,{{id:'custom_xml_manual',label:'Manual XML',group:'Custom',url:'/api/tak-map/custom-basemap-tile/custom_xml_manual/{{z}}/{{x}}/{{y}}.png',minZoom:1,maxZoom:18,importedBasemap:true}}];return response('Imported 1 basemap XML file(s).')}}
 if(String(url).endsWith('delete')){{const body=JSON.parse(opt.body||'{{}}');window.__serverBasemaps=window.__serverBasemaps.filter(x=>x.id!==body.id);return response('Imported basemap removed.')}}
 if(String(url).endsWith('clear')){{window.__serverBasemaps=[];return response('All imported basemaps removed.')}}
 return new Response(JSON.stringify({{ok:false,error:'unexpected '+url}}),{{status:404,headers:{{'Content-Type':'application/json'}}}});
}};
renderBasemaps();
</script>{patch}</body></html>'''

        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, executable_path=shutil.which(chromium), args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
            page = browser.new_page(viewport={'width':1000,'height':800})
            errors=[]; page.on('pageerror', lambda e: errors.append(str(e)))
            page.set_content(fixture, wait_until='domcontentloaded', timeout=30000)
            page.wait_for_function("window.TakMapCompositeBasemapsV505 && TakMapCompositeBasemapsV505.diagnostics().serverPersisted", timeout=7000)

            page.evaluate("window.importTakGatewayBasemapsV505()")
            page.wait_for_function("document.querySelectorAll('#customBasemapRowsV505 .tak-custom-basemap-row-v505').length===2", timeout=7000)
            imported = page.evaluate("""()=>({
              rows:document.querySelectorAll('#customBasemapRowsV505 .tak-custom-basemap-row-v505').length,
              names:[...document.querySelectorAll('.tak-custom-basemap-name-v505')].map(x=>x.firstChild.textContent),
              gatewayGroup:[...document.querySelectorAll('#basemapSelect optgroup')].find(x=>x.label==='TAK Gateway Composite')?.querySelectorAll('option').length||0,
              status:document.getElementById('customBasemapStatus').textContent,
              diag:TakMapCompositeBasemapsV505.diagnostics(),
              calls:window.__calls
            })""")
            assert imported['rows']==2 and imported['gatewayGroup']==2, imported
            assert 'Imported 2' in imported['status'], imported
            assert imported['diag']['imported']==2 and imported['diag']['clientComposition'] is False, imported
            assert imported['diag']['localTileCache'] is False and imported['diag']['precache'] is False, imported
            assert any(x['url'].endswith('import-gateway') for x in imported['calls']), imported

            # Real input selection exercises the multipart FormData path.
            page.set_input_files('#basemapXmlInput', {'name':'manual.xml','mimeType':'application/xml','buffer':b'<customMapSource />'})
            page.wait_for_function("document.querySelectorAll('#customBasemapRowsV505 .tak-custom-basemap-row-v505').length===3", timeout=7000)
            manual = page.evaluate("""()=>({rows:document.querySelectorAll('#customBasemapRowsV505 .tak-custom-basemap-row-v505').length,custom:[...document.querySelectorAll('#basemapSelect optgroup')].find(x=>x.label==='Custom')?.querySelectorAll('option').length||0,calls:window.__calls})""")
            assert manual['rows']==3 and manual['custom']==1, manual
            assert any(x['url'].endswith('upload') and x['isForm'] for x in manual['calls']), manual

            page.evaluate("setBasemap('custom_xml_img')")
            page.locator('.tak-custom-basemap-delete-v505').first.click()
            page.wait_for_function("document.querySelectorAll('#customBasemapRowsV505 .tak-custom-basemap-row-v505').length===2", timeout=7000)
            deleted = page.evaluate("""()=>({rows:document.querySelectorAll('#customBasemapRowsV505 .tak-custom-basemap-row-v505').length,active:window.__active,calls:window.__calls})""")
            assert deleted['active']=='esri_topo', deleted
            assert any(x['url'].endswith('delete') for x in deleted['calls']), deleted

            browser.close()
        assert not errors, errors
        print('TAK Map i505 composite basemap browser UI test passed')
        print(json.dumps({'imported':imported,'manual':manual,'deleted':deleted}, sort_keys=True))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
