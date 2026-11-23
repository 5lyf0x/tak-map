#!/usr/bin/env python3
"""Real i003 JS snippet browser regression; checks full card decorators and Leaflet options."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json
root=Path(__file__).resolve().parent.parent
core=(root/'assets/tak-map-core-i553.js').read_text()
stack=(root/'assets/tak-map-basemap-stack-i673.js').read_text()
card=(root/'assets/tak-map-offline-maps-i698.js').read_text()
css=(root/'assets/tak-map-offline-maps-i698.css').read_text()

def get(source,beg,end):
 a=source.index(beg);b=source.index(end,a)
 return source[a:b]
refresh=get(core,'function offlineBasemapEntry(m)','async function uploadOfflineMaps()')
render=get(core,'function sortOfflineMapPacksByNameI001(','async function apiJsonResponse(')
card_logic=get(card,'function addRenameControl(','// Startup loader creates')
layer_opts=get(stack,'function isOffline(b)','// Pixel-heavy custom modes')
assert 'updateWhenIdle:off?false:true' in layer_opts
assert 'keepBuffer:off?(custom?2:3):(custom?5:8)' in layer_opts
assert 'generation=' in refresh and 'maxNativeZoom:nativeMax' in refresh
records=[
 {'id':'x','name':'Imported XYZ','path':'/does/not/matter','format':'png','min_zoom':4,'max_zoom':12,'tile_row_scheme':'xyz'},
 {'id':'s','name':'Standard TMS','created_by':'download','download_status':'complete','min_zoom':6,'max_zoom':13},
]
html='<html><head><style>'+css+'</style></head><body><div id="offlineMapRows"></div></body></html>'
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-gpu'])
 page=browser.new_page(viewport={'width':1000,'height':720})
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.set_content(html)
 page.evaluate('''() => {
 window.w=window;window.d=document;window.$=id=>document.getElementById(id);
 window.config={basemaps:[],default_basemap:'esri_topo'};
 window.offlineMaps=[];
 window.renderBasemaps=()=>{};window.esc=v=>String(v||'');
 window.requestStats=[];
 }''')
 page.evaluate('''records => {window.records=records;window.fetch=async (url,opts)=>{
 let data={ok:true};
 if(String(url).includes('/offline-row-scheme-i003')){
   const body=JSON.parse(opts.body);window.requestStats.push(body);
   const m=records.find(x=>x.id===body.id);m.tile_row_scheme=body.tile_row_scheme;
   m.updated='2026-11-22T12:00:00Z';data={ok:true,map:m,maps:records};
 }else if(String(url).includes('/offline-maps'))data={ok:true,maps:records};
 return {ok:true,status:200,headers:{get:()=> 'application/json'},json:async()=>data};
 };}''',records)
 page.add_script_tag(content=refresh+'\n'+render+'\n'+card_logic+'\nwindow.decorateCards=decorateCards;wrapRender();')
 page.evaluate('refreshOfflineMaps(true)')
 page.evaluate('decorateCards()')
 assert page.locator('#offlineMapRows .offline-card').count()==2
 assert page.locator('#offlineMapRows .offline-rename-action').count()==2
 assert page.locator('#offlineMapRows .offline-row-scheme-i003 select').count()==1
 assert page.locator('#offlineMapRows .offline-row-scheme-i003 select').input_value()=='xyz'
 layer=page.evaluate("config.basemaps.find(b=>b.id==='offline_x')")
 assert layer['minZoom']==4 and layer['maxNativeZoom']==12 and layer['maxZoom']==22,layer
 assert 'generation=' in layer['url']
 page.locator('#offlineMapRows .offline-row-scheme-i003 select').select_option('tms')
 page.wait_for_timeout(90)
 assert page.evaluate('requestStats.length')==1
 assert page.locator('#offlineMapRows .offline-row-scheme-i003 select').input_value()=='tms'
 page.evaluate('decorateCards()')
 assert page.locator('#offlineMapRows .offline-row-scheme-i003 select').count()==1
 assert page.locator('#offlineMapRows .offline-rename-action').count()==2
 # Actual i003 layer-options function. Online basemap must retain i002 defaults.
 page.evaluate('''() => {window.W=window;window.W.L={latLngBounds:(a)=>({pad:()=>({area:a})})};}''')
 page.add_script_tag(content=layer_opts+'\nwindow.i003LayerOptions=layerOptions;')
 offline=page.evaluate('i003LayerOptions({type:"mbtiles",id:"offline_x",minZoom:4,maxZoom:22,minNativeZoom:4,maxNativeZoom:12},false)')
 online=page.evaluate('i003LayerOptions({type:"xyz",id:"esri_topo",minZoom:0,maxZoom:19},false)')
 custom=page.evaluate('i003LayerOptions({type:"mbtiles",id:"offline_x",minZoom:4,maxZoom:22,maxNativeZoom:12},true)')
 assert offline['updateWhenIdle'] is False and offline['updateInterval']==200 and offline['keepBuffer']==3 and offline['maxNativeZoom']==12
 assert custom['keepBuffer']==2
 assert online['updateWhenIdle'] is True and online['keepBuffer']==8 and online['maxZoom']==19
 assert not errors,errors
 page.close();browser.close()
 print('PASS i003 Chromium: imported-row selector and save, Rename persistence, native zoom, generation URLs, offline-only continuous pan/buffers, online behavior unchanged')
