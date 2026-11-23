"""i684 regression: cancel removes editor overlays and pending redraws without saving."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
HTML='<html><head></head><body><div id="map" style="width:900px;height:600px"></div><button id="toolRoute" class="active">Route</button></body></html>'
INIT=r'''() => {
  window.activeMapTool='route';window.__writes=0;
  window.v233RouteState={points:[{lat:33,lng:-116},{lat:33.01,lng:-116.02}],color:'#f80'};
  window.v234RedrawRoute=()=>{}; window.v233RouteMapClick=()=>{};window.v233FinishRoute=()=>{};
  window.setActiveMapTool=v=>{window.activeMapTool=v;document.getElementById('toolRoute').classList.toggle('active',v==='route');};
  window.v233ClosePanel=()=>{};
  const layers=new Set();const latLng=(a,b)=>typeof a==='object'?a:{lat:a,lng:b};
  function createLayer(opts={}){return {options:opts, _handlers:{},addTo(map){layers.add(this);return this},on(name,fn){this._handlers[name]=fn;return this},getLatLng(){return this.ll||{lat:33,lng:-116}},setLatLng(ll){this.ll=ll;return this},bindPopup(){return this}}}
  window.map={layers,getContainer:()=>document.getElementById('map'),latLngToContainerPoint:()=>({x:50,y:50}),latLngToLayerPoint:()=>({x:50,y:50}),
    getZoom:()=>10,getSize:()=>({x:900,y:600}),getCenter:()=>({lat:33,lng:-116}),distance:(a,b)=>Math.hypot((a.lat-b.lat)*111000,(a.lng-b.lng)*89000),
    on:()=>{},closePopup:()=>{},hasLayer:l=>layers.has(l),removeLayer:l=>layers.delete(l),eachLayer:fn=>[...layers].forEach(fn)};
  window.L={latLng,point:(x,y)=>({x,y,distanceTo(q){return Math.hypot(x-q.x,y-q.y)}}),layerGroup:()=>createLayer(),polyline:()=>createLayer(),
    marker:(p,opts)=>{let l=createLayer(opts);l.ll=p;return l},circleMarker:()=>createLayer(),divIcon:opts=>({options:opts}),DomEvent:{stop:()=>{}}};
  window.fetch=async url=>({ok:true,json:async()=>({routing_enabled:false})});
  window.lastImports=[];window.drawImportedObjects=()=>{};
  window.__layerTypes=()=>[...layers].map(l=>l.options?.icon?.options?.className||'other');
}'''
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 try:
  page=b.new_page()
  errors=[];page.on('pageerror',lambda e: errors.append(str(e)))
  page.set_content(HTML);page.evaluate(INIT);page.add_script_tag(path=str(ROOT/'assets/tak-map-route-editor-i654.js'))
  assert page.evaluate('!!window.takRouteEditorI654.installed'),'route editor should initialize'
  for cycle in range(2):
   page.evaluate('''() => {let s=window.takRouteEditorI654;window.setActiveMapTool('route');
     window.v233RouteState.points=[L.latLng(33,-116),L.latLng(33.01,-116.02)];
     s.legs=[{status:'ready',mode:'manual',shape:window.v233RouteState.points.slice()}];
     s.pointModes=['manual','manual'];s.segmentModes=['manual'];s.editing={objectId:'saved1',importId:'file1',revision:'1',name:'Saved'};
     v234RedrawRoute();}''')
   assert page.evaluate("window.__layerTypes().filter(x=>x.includes('tak-route-point-i654')).length") == 2
   (page.locator('[data-route-edit-action=cancel]').click() if cycle==0 else page.evaluate('window.takRouteEditorI654.cancelSavedEdit()'))
   assert page.evaluate('window.takRouteEditorI654.editing===null')
   assert page.evaluate('window.v233RouteState.points.length') == 0
   assert page.evaluate("window.__layerTypes().filter(x=>x.includes('tak-route-point-i654')||x.includes('tak-route-distance-icon-i658')).length") == 0
   assert page.evaluate("window.activeMapTool==='move'")
   page.evaluate('v234RedrawRoute()') # race: late route redraw after Cancel must stay empty
   assert page.evaluate("window.__layerTypes().filter(x=>x.includes('tak-route-point-i654')).length") == 0
   print('PASS cancel edit cycle',cycle+1,'without residual draft layers')
  assert not errors,errors
  print('PASS no browser errors')
 finally:b.close()
