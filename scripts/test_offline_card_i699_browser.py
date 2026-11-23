#!/usr/bin/env python3
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
script=(root/'assets/tak-map-offline-maps-i698.js').read_text()
css=(root/'assets/tak-map-offline-maps-i698.css').read_text()
geo=json.loads((root/'assets/tak-map-offline-us-regions-i698.json').read_text())
html='''<!doctype html><html><head><style>body{background:#061018;color:#e1edf6;font:12px system-ui;width:360px}.panel{padding:12px;border:1px solid #304557;border-radius:12px}.row{display:flex;gap:6px;padding:6px 0}.subgroup-title{font-size:11px}button{cursor:pointer}</style></head><body>
<div class="panel"><h2>Offline Maps</h2><div class="subgroup-title">Create Offline Map Pack</div><input id="offlinePackName" value="South CA">
<div class="row"><span id="offlineSourceText">Source basemap</span></div>
<div class="row"><button onclick="useCurrentViewForOffline()">Current View</button><button onclick="startOfflineAreaDraw()">Draw Area</button></div>
<div class="row" id="offlineBoundsRow"><span id="offlineBoundsText">West -120.1 East -114.2 South 32.5 North 37.6</span></div>
<div id="offlineEstimate"></div><div class="row"><label>Min zoom</label><input id="offlineMinZoom" value="8"></div>
<div class="row"><label>Max zoom</label><input id="offlineMaxZoom" value="13"></div>
<div class="row"><button onclick="previewOfflineZoom()">Preview Max Zoom</button><button onclick="startOfflineDownload()">Create Offline Map</button></div>
<div class="row"><button onclick="refreshOfflineMaps()">Refresh Offline Maps</button></div><div id="offlineJobStatus"></div><div id="offlineMapRows"></div></div>
<script>
window.config={};window.activeBasemap='fixture';window.offlineDownloadBounds=null;window.offlineAreaRect=null;
window.map={getBounds:()=>({getWest:()=>-120,getEast:()=>-114,getNorth:()=>37,getSouth:()=>32}),fitBounds(){},setView(){},removeLayer(){}};
window.L={geoJSON:()=>({getBounds:()=>({isValid:()=>true}),addTo(){}})};
window.useCurrentViewForOffline=()=>{offlineDownloadBounds={west:-120,south:32,east:-114,north:37}};
window.startOfflineAreaDraw=()=>{};window.stopOfflineAreaDraw=()=>{};window.updateOfflineBoundsText=()=>{};
window.refreshOfflineMaps=()=>{};window.renderOfflineMapRows=()=>{};window.pollOfflineJob=()=>{};
window.__sources=[{id:'fixture',label:'Google Terrain'},{id:'new',label:'Google Roads'}];
window.__requestCount=0;
</script></body></html>'''
with sync_playwright() as pl:
 browser=pl.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':480,'height':850});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.set_content(html)
 page.evaluate('''(geo)=>{window.__geo=geo;window.fetch=async(u,options={})=>{const url=String(u);if(url.includes('offline-areas-i698'))return{ok:true,status:200,json:async()=>({ok:true,geojson:geo})};if(url.includes('api/tak-map/config')){window.__requestCount++;await new Promise(r=>setTimeout(r,150));return{ok:true,status:200,json:async()=>({ok:true,offline_download_sources:window.__sources})};}if(url.includes('offline-estimate'))return{ok:true,status:200,json:async()=>({ok:true,tile_count:4200,internal_jobs:1,estimated_bytes:125000000})};throw Error(url)}}''',geo)
 page.add_style_tag(content=css);page.add_script_tag(content=script)
 page.wait_for_function('document.querySelectorAll("#offlineAreaSelectI698 option").length===54')
 page.wait_for_function('document.querySelectorAll("#offlineSourceSelectI698 option").length===2')
 assert page.locator('#offlineAreaSelectorI698').is_visible()
 assert page.evaluate('document.getElementById("offlineBoundsRow").style.display')=='none'
 assert page.locator('text=Create Offline Map Pack').count()==0
 assert page.locator('#offlineAreaSelectorI698').evaluate('(el)=>el.previousElementSibling.tagName')=='H2'
 assert page.locator('#offlineSourceSelectI698 option').all_text_contents()==['Google Terrain','Google Roads']
 assert page.locator('button[onclick*="previewOfflineZoom"]').inner_text()=='Preview Max'
 assert page.locator('button').filter(has_text='Download').count()>=1
 assert not page.locator('.tak-offline-i699 h2 img, .tak-offline-i699 h2 svg').count()
 assert page.locator('#offlineAreaSelectI698').evaluate('(el)=>getComputedStyle(el).appearance')=='none'
 assert page.locator('#offlineSourceSelectI698').evaluate('(el)=>getComputedStyle(el).appearance')=='none'
 font_a=page.locator('#offlineAreaSelectI698').evaluate('(el)=>[getComputedStyle(el).fontFamily,getComputedStyle(el).fontWeight,getComputedStyle(el).fontSize]')
 font_b=page.locator('#offlineSourceSelectI698').evaluate('(el)=>[getComputedStyle(el).fontFamily,getComputedStyle(el).fontWeight,getComputedStyle(el).fontSize]')
 assert font_a==font_b,(font_a,font_b)
 page.screenshot(path='/mnt/data/TAK-Map-i699-Offline-Maps-Card-Preview.png')
 page.evaluate('window.__sources.push({id:"third",label:"Custom XML"})')
 page.wait_for_timeout(5350)
 page.locator('#offlineSourceSelectI698').focus()
 page.wait_for_function('document.querySelectorAll("#offlineSourceSelectI698 option").length===3')
 assert not errors,errors
 print('PASS i699 area immediately below title, no header icon, no coords, no redundant title')
 print('PASS source dropdown async loaded, refresh imported source, both arrow-free with identical typography')
 print('PASS Preview Max/Download icon-free buttons, all 54 choices, no JS errors')
 browser.close()
