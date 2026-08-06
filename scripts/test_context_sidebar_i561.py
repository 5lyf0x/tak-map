import sys
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
asset = (ROOT / 'assets' / 'tak-map-context-sidebar-i561.js').read_text()

bootstrap = r'''
class Bounds {
  constructor(minLat=-90,minLng=-180,maxLat=90,maxLng=180){this.minLat=minLat;this.minLng=minLng;this.maxLat=maxLat;this.maxLng=maxLng}
  contains(value){const lat=Array.isArray(value)?value[0]:value.lat;const lng=Array.isArray(value)?value[1]:(value.lng??value.lon);return lat>=this.minLat&&lat<=this.maxLat&&lng>=this.minLng&&lng<=this.maxLng}
  getCenter(){return {lat:(this.minLat+this.maxLat)/2,lng:(this.minLng+this.maxLng)/2}}
}
class MapStub {
  constructor(node){this.node=node;this.events={};this.bounds=new Bounds();this.panCalls=[];this.zoom=9}
  on(names,fn){String(names).split(/\s+/).forEach(n=>(this.events[n]=this.events[n]||[]).push(fn));return this}
  fire(name,data={}){(this.events[name]||[]).slice().forEach(fn=>fn(data));return this}
  getContainer(){return this.node}
  getBounds(){return this.bounds}
  panTo(center,opts){this.panCalls.push({center,opts});this.center=center;return this}
  setView(center,zoom,opts){this.panCalls.push({center,zoom,opts,setView:true});this.center=center;this.zoom=zoom;return this}
  getZoom(){return this.zoom}
}
class LayerStub {
  constructor(lat,lng,html){this.lat=lat;this.lng=lng;this.events={};this.popup={_content:html,getContent(){return this._content}};this.options={};this.unbound=0}
  on(name,fn){(this.events[name]=this.events[name]||[]).push(fn);return this}
  off(name){if(name)this.events[name]=[];else this.events={};return this}
  fire(name,data={}){(this.events[name]||[]).slice().forEach(fn=>fn.call(this,Object.assign({target:this},data)));return this}
  getLatLng(){return {lat:this.lat,lng:this.lng}}
  getPopup(){return this.popup}
  unbindPopup(){this.popup=null;this.unbound++;return this}
}
window.L={DomEvent:{stop(){}}};
window.map=new MapStub(document.getElementById('map'));
const point={uid:'P-1',mission_name:'Mission Alpha',name:'Point One',callsign:'Point One',lat:34.2,lon:-118.4};
const route={uid:'R-1',name:'Route One',kind:'route',lat:34.3,lon:-118.5};
const shape={uid:'S-1',name:'Shape One',kind:'shape',lat:34.4,lon:-118.6};
point.__layer=new LayerStub(point.lat,point.lon,'<div>legacy point popup</div>');
route.__layer=new LayerStub(route.lat,route.lon,'<div class="feature-popup"><h3>Route One</h3><div class="kvp"><b>Name</b><span>Route One</span></div><details class="popup-edit"><summary>Edit Data</summary><label>Name<input value="Route One"></label><div class="popup-edit-actions"><button>Save</button><button>Cancel</button></div></details></div>');
shape.__layer=new LayerStub(shape.lat,shape.lon,'<div class="feature-popup"><h3>Shape One</h3><div class="kvp"><b>Name</b><span>Shape One</span></div></div>');
window.lastDataSync={objects:[point,route,shape]};
window.dataSyncCategory=o=>o.kind==='route'?'Routes':(o.kind==='shape'?'Shapes / Areas':'Point Markers');
window.layerPopupForObject=(o,cat)=>o.__layer.__takMapI561InfoHtml || `<div class="feature-popup"><h3>${o.name}</h3><div class="kvp"><b>Category</b><span>${cat}</span></div></div>`;
window.importedFeatures=()=>[];
window.addObjectLayer=(group,o,source)=>o.__layer;
window.drawDataSyncObjects=()=>{};
window.drawImportedObjects=()=>{};
window.centerDataSyncIndex=()=>{};
window.centerLocalItem=()=>{};
window.chooseSearchItem=()=>{};
window.TakMapIconRegistryI561={
 version:'i561',
 isPoint:o=>Number.isFinite(Number(o&&o.lat))&&Number.isFinite(Number(o&&o.lon))&&!o.kind,
 isLocalPoint:()=>false,
 pointUid:o=>o.uid,
 pointMission:o=>o.mission_name,
 pointLocalId:()=>'',
 pointInfoHtml:o=>`<div class="point-info-popup-i556"><header class="point-popup-head-i556"><div class="point-popup-stage-i556"></div><div><div class="point-popup-title-i556">${o.name}</div><div class="point-popup-path-i556">Long symbol hierarchy</div></div></header><div class="point-popup-body-i556"><div class="point-popup-grid-i556"><div class="point-popup-label-i556">Mission</div><div class="point-popup-value-i556">${o.mission_name}</div><div class="point-popup-label-i556">Location</div><div class="point-popup-value-i556 point-popup-location-i561"><span class="point-popup-location-text-i561">34.200000, -118.400000</span><button class="point-popup-copy-i561" data-point-copy-location="1">Copy</button></div><div class="point-popup-label-i556">Added</div><div class="point-popup-value-i556 point-popup-time-i561">07/24/2026 02:50 3days 2h 19m</div><div class="point-popup-label-i556">Sync State</div><div class="point-popup-value-i556"><span class="point-popup-sync-i561 state-synced"><span class="point-popup-sync-dot-i561"></span>Synced</span></div></div><div class="point-popup-actions-i556"><button class="point-popup-edit-i556" data-i561-point-edit="1" data-point-source="datasync" data-point-uid="${o.uid}" data-point-mission="${o.mission_name}">Edit Point</button></div></div></div>`,
 openPointEditor(source,reference,mission){
   let modal=document.getElementById('takMapPointEditorI556');
   if(!modal){modal=document.createElement('div');modal.id='takMapPointEditorI556';modal.innerHTML='<section class="point-editor-card-i556"><header class="point-head-i556"><div class="point-title-i556">Edit Point</div><button id="pointEditorCloseI556">×</button></header><div class="point-body-i556"><section class="point-source-strip-i556"><span class="point-source-icon-i556"></span><div><div class="point-source-title-i556">Mission Alpha Mission</div><div class="point-source-meta-i556">UID: P-1 · source-owned</div></div><span class="point-source-state-i556">Synced</span></section><div class="point-field-i556"><label>Name</label><input class="point-control-i556" value="Point One"></div><div class="point-status-i556">Ready</div></div><footer class="point-actions-i556"><button id="pointEditorCancelI556">Cancel</button><button id="pointEditorSaveI556">Save</button></footer></section>';document.body.appendChild(modal)}
   modal.classList.add('active');
   TakMapContextSidebarI561.onPointEditorOpening(source,reference,mission);
   modal.querySelector('#pointEditorCancelI556').onclick=()=>{modal.classList.remove('active');TakMapContextSidebarI561.onPointEditorClosed('cancel',point,'datasync')};
 }
};
window.__objects={point,route,shape};
'''

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    errors=[]
    page.on('pageerror', lambda exc: errors.append(str(exc)))
    page.set_content('''<!doctype html><html><head><style>
      body{margin:0;background:#111;color:#eee}#sidebar{position:absolute;left:0;top:0;width:390px;height:900px;background:#101923}.panel{border:1px solid #333}.panel h2{color:#ff7a1a}.chip{color:#ff7a1a}.panel-toggle{color:#ff7a1a}#map{position:absolute;left:390px;top:0;width:1050px;height:900px;overflow:hidden;background:#28333d}.leaflet-control-scale{position:absolute;right:10px;bottom:10px;width:120px;height:28px;background:#eee}.leaflet-popup{display:none}</style></head><body><aside id="sidebar"><div class="panel"><h2>Basemap <span class="panel-toggle">▾</span></h2><span class="chip">12</span><input id="reliefOpacity" type="range"></div></aside><div id="map"><div class="leaflet-control-scale"></div></div></body></html>''')
    page.evaluate("Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async v=>{window.__copiedLocation=v;}}})")
    page.add_script_tag(content=bootstrap)
    page.add_script_tag(content=asset)
    page.wait_for_function("window.TakMapContextSidebarI561 && TakMapContextSidebarI561.diagnostics().installed")
    page.wait_for_function("TakMapContextSidebarI561.diagnostics().boundLayers===3")

    # Point click opens the right sidebar, unbinds Leaflet popup, and centers map once.
    page.evaluate("__objects.point.__layer.fire('click',{originalEvent:{target:document.getElementById('map')}})")
    page.wait_for_function("!document.getElementById('takMapContextSidebarI561').classList.contains('collapsed')")
    page.wait_for_timeout(280)
    result=page.evaluate('''() => {const p=document.getElementById('takMapContextSidebarI561'),r=p.getBoundingClientRect(),m=document.getElementById('map').getBoundingClientRect(),s=document.querySelector('.leaflet-control-scale').getBoundingClientRect();return {right:Math.round(m.right-r.right),above:r.bottom<=s.top-8,title:document.getElementById('takMapContextTitleI561').textContent,point:!!p.querySelector('.point-info-popup-i556'),popup:__objects.point.__layer.getPopup(),pan:map.panCalls.length,overflow:getComputedStyle(document.getElementById('takMapContextSidebarBodyI561')).overflowY}}''')
    assert 8 <= result['right'] <= 20, result
    assert result['above'] and result['point'] and result['popup'] is None, result
    assert result['title']=='Point One' and result['pan']==1, result
    assert result['overflow']=='visible', result

    typography=page.evaluate('''() => ({panel:Math.round(document.getElementById('takMapContextSidebarI561').getBoundingClientRect().width),label:getComputedStyle(document.querySelector('.point-popup-label-i556')).fontSize,value:getComputedStyle(document.querySelector('.point-popup-value-i556')).fontSize,edit:getComputedStyle(document.querySelector('.point-popup-edit-i556')).fontSize,sync:document.querySelector('.point-popup-sync-i561')?.textContent.trim(),iconPath:document.body.textContent.includes('Icon Path')})''')
    assert typography['panel']==400 and typography['label']=='9.5px' and typography['value']=='11px', typography
    assert typography['edit']=='12.5px' and typography['sync']=='Synced' and typography['iconPath'] is False, typography
    page.click('[data-point-copy-location]')
    page.wait_for_function("window.__copiedLocation==='34.200000, -118.400000'")
    page.wait_for_function("document.querySelector('[data-point-copy-location]').textContent==='Copied'")

    # Edit changes content in the same open sidebar without a hide/show cycle.
    page.click('[data-i561-point-edit]')
    page.wait_for_function("document.querySelector('#takMapContextSidebarBodyI561>#takMapPointEditorI556.active')")
    edit=page.evaluate('''() => {const p=document.getElementById('takMapContextSidebarI561');return {open:!p.classList.contains('collapsed'),mode:TakMapContextSidebarI561.diagnostics().mode,editor:!!p.querySelector('.point-editor-card-i556'),meta:getComputedStyle(p.querySelector('.point-source-meta-i556')).whiteSpace}}''')
    assert edit['open'] and edit['mode']=='edit' and edit['editor'] and edit['meta']=='normal', edit
    page.click('#pointEditorCancelI556')
    page.wait_for_function("document.querySelector('#takMapContextSidebarBodyI561 .point-info-popup-i556')")
    assert page.evaluate("!document.getElementById('takMapContextSidebarI561').classList.contains('collapsed')") is True

    # Route click replaces content; its editor transforms in place.
    page.evaluate("__objects.route.__layer.fire('click',{originalEvent:{target:document.getElementById('map')}})")
    page.wait_for_function("document.getElementById('takMapContextTitleI561').textContent==='Route One'")
    page.click('details.popup-edit summary')
    page.wait_for_function("document.getElementById('takMapContextSidebarI561').classList.contains('generic-edit')")
    assert page.evaluate("getComputedStyle(document.querySelector('#takMapContextSidebarI561 .feature-popup>h3')).display")=='none'
    page.evaluate("document.querySelector('details.popup-edit').open=false")
    page.wait_for_function("!document.getElementById('takMapContextSidebarI561').classList.contains('generic-edit')")

    # Empty map click hides; object click reopens; hide button hides.
    page.wait_for_timeout(420)
    page.evaluate("map.fire('click',{originalEvent:{target:document.getElementById('map')}})")
    page.wait_for_function("document.getElementById('takMapContextSidebarI561').classList.contains('collapsed')")
    page.evaluate("__objects.shape.__layer.fire('click',{originalEvent:{target:document.getElementById('map')}})")
    page.wait_for_function("!document.getElementById('takMapContextSidebarI561').classList.contains('collapsed')")
    page.click('#takMapContextHideI561')
    page.wait_for_function("document.getElementById('takMapContextSidebarI561').classList.contains('collapsed')")

    # Off-screen movement hides the open sidebar.
    page.evaluate("__objects.point.__layer.fire('click',{originalEvent:{target:document.getElementById('map')}})")
    page.wait_for_function("!document.getElementById('takMapContextSidebarI561').classList.contains('collapsed')")
    page.evaluate("map.bounds=new Bounds(0,0,1,1);map.fire('moveend')")
    page.wait_for_function("document.getElementById('takMapContextSidebarI561').classList.contains('collapsed')")

    # Silver theme is applied to the existing left sidebar controls.
    theme=page.evaluate('''() => ({h:getComputedStyle(document.querySelector('#sidebar h2')).color,arrow:getComputedStyle(document.querySelector('#sidebar .panel-toggle')).color,chip:getComputedStyle(document.querySelector('#sidebar .chip')).color,accent:getComputedStyle(document.getElementById('reliefOpacity')).accentColor})''')
    assert theme['h']!='rgb(255, 122, 26)' and theme['arrow']!='rgb(255, 122, 26)' and theme['chip']!='rgb(255, 122, 26)', theme
    assert '203' in theme['accent'] or 'rgb(203' in theme['accent'], theme

    audit=page.evaluate('TakMapContextSidebarI561.diagnostics()')
    assert audit['leafletPopupLifecycleUsed'] is False and audit['silverTheme'] is True, audit
    assert not errors, errors
    browser.close()

print('i561 contextual right sidebar interaction and silver theme validation passed')
sys.stdout.flush()
os._exit(0)
