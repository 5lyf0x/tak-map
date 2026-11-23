"""i676 live Chromium: complete mixed route save and draggable routing HUD."""
import json, ast, re
from pathlib import Path
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parents[1]
editor=(root/'assets/tak-map-route-editor-i654.js').read_text()
hud=(root/'assets/tak-map-routing-dropdown-i675.js').read_text()
main=(root/'tak_dashboard.py').read_text()
m=re.search(r"    _I500_ROUTE_UI = ('.*')\n\n    def _i500_patch_html", main,re.S)
assert m
modal=ast.literal_eval(m.group(1)).replace('<script id="takMapRouteUiV500">','').replace('</script>','')
AZ='a'*64
html='''<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:0;background:#172a33;color:white}
#header{position:absolute;left:0;right:0;top:0;height:55px;background:#030b12;z-index:9999}
#map{position:absolute;left:269px;right:0;top:55px;bottom:0;background:#d2e6e8}
#zoom{position:absolute;top:59px;right:7px;width:155px;height:26px;background:#081824;z-index:5000}
#toolbar{position:absolute;top:146px;right:7px;width:37px;height:380px;background:#09222e;z-index:900}
</style></head><body>
<div id="header">TAK MAP HEADER</div><div id="map"></div><div id="zoom">Zoom coordinates</div><div id="toolbar"></div>
<button id="toolRoute" class="active" style="display:none">Route</button>
<input id="routeNameInput" value="Demo Trail"/><input id="routeColorInput" value="#ff6f2e"/>
</body></html>'''
init_js=r'''
window.__fakeStore={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>window.__fakeStore[k]??null,setItem:(k,v)=>window.__fakeStore[k]=String(v),removeItem:k=>delete window.__fakeStore[k]}});
window.activeMapTool='route'; window.v233RouteState={points:[],name:'',notes:'',category:'General'};
window.setActiveMapTool=function(tool){window.activeMapTool=tool};
window.v234RedrawRoute=function(){};
window.v233RouteMapClick=function(){};
window.v233FinishRoute=function(){};
window.__savedImports=[];window.__truncate=false;
window.fetch=async function(url,opts={}){
 const name=String(url);
 if(name.includes('/api/tak-map/ndm/status'))return {ok:true,json:async()=>({routing_enabled:true})};
 if(name.includes('/api/tak-map/routing/datasets-i675'))return {ok:true,json:async()=>({ok:true,active_dataset_id:'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',datasets:[{dataset_id:'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',label:'Arizona',active:true}],switch:{status:'idle'}})};
 if(name.includes('/api/tak-map/imported'))return {ok:true,json:async()=>({imports:window.__savedImports.map(i=>({...i,features:i.features.map(f=>({...f,coords:window.__truncate?f.coords.slice(0,4):f.coords}))}))})};
 if(name.includes('/api/tak-map/import')&&opts.method==='POST'){
   const file=opts.body.get('files');const json=JSON.parse(await file.text());const f=json.features[0];
   const imported={id:'import-one',name:file.name,features:[{...f.properties,properties:f.properties,kind:'route',coords:f.geometry.coordinates.map(p=>[p[1],p[0]]),object_id:'r-one',route_revision_i659:'rev-1'}]};
   window.__savedImports=[imported];return {ok:true,json:async()=>({ok:true,added:[imported],imports:window.__savedImports})};
 }
 if(name.includes('/api/tak-map/route-update-i659')&&opts.method==='POST'){
   const payload=JSON.parse(opts.body);const f=payload.feature;
   const imported={id:'import-one',name:'Demo Trail.geojson',features:[{...f.properties,properties:f.properties,kind:'route',coords:f.geometry.coordinates.map(p=>[p[1],p[0]]),object_id:'r-one',route_revision_i659:'rev-2'}]};
   window.__savedImports=[imported];return {ok:true,json:async()=>({ok:true,imports:window.__savedImports})};
 }
 throw Error('unexpected '+name);
};
const on=()=>({options:{},on(){return this},addTo(){return this},getLatLng(){return {lat:34,lng:-118}},getPopup(){return null}});
window.L={latLng:(lat,lng)=>({lat,lng}),point:(x,y)=>({x,y,distanceTo(q){return Math.hypot(x-q.x,y-q.y)}}),layerGroup:on,marker:on,polyline:on,circleMarker:on,divIcon:()=>({})};
window.map={on(){},getContainer:()=>document.getElementById('map'),hasLayer(){return false},distance(a,b){return Math.hypot(a.lat-b.lat,a.lng-b.lng)*111000},getZoom(){return 9},latLngToContainerPoint(p){return {x:p.lng*10,y:p.lat*10,distanceTo(q){return Math.hypot(this.x-q.x,this.y-q.y)}}},getSize(){return {x:1473,y:809}}};
window.refreshImports=async()=>{};
window.refreshLocalData=async()=>{};
window.drawImportedObjects=function(){};
window.lastImports=[];
window.confirm=()=>true;
'''

def seed(page):
 return page.evaluate('''() => {
   window.activeMapTool='route';
   const state=window.takRouteEditorI654;
   const pts=Array.from({length:13},(_,i)=>window.L.latLng(34.03+(i*.07),-118.6+(i*.095)));
   window.v233RouteState.points=pts;
   state.pointModes=pts.map((_,i)=>i===6?'manual':'roads');
   state.segmentModes=Array(12).fill('roads');state.segmentModes[5]='manual';
   state.legs=Array.from({length:12},(_,i)=>{
       const a=pts[i],b=pts[i+1],fail=[3,7,10].includes(i);
       return {status:fail?'error':'ready',mode:state.segmentModes[i],shape:fail?[a,b]:[a,window.L.latLng((a.lat+b.lat)/2+.002,(a.lng+b.lng)/2+.003),b]};
   });
   const result=state.getResolvedSaveState();return result;
 }''')
with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  page=browser.new_page(viewport={'width':1742,'height':864})
  page.set_content(html)
  page.evaluate(init_js)
  page.evaluate(modal)
  page.evaluate(editor)
  page.wait_for_timeout(500)
  assert page.evaluate('window.takRouteEditorI654.installed'), 'route editor failed to install'
  state=seed(page);assert state['ready'] and state['controlCount']==13 and state['fallbackCount']==3,state
  page.evaluate('window.TakMapRouteUiV500.open()')
  note=page.locator('.tak-route-connector-note-i676');assert note.is_visible()
  assert '3 segment(s)' in note.inner_text()
  page.locator('#takRouteSaveButtonV500').click()
  page.wait_for_timeout(150)
  result=page.evaluate('''() => {
    const saved=window.__savedImports[0].features[0];return {
      vertices:saved.coords.length,controlCount:saved.properties.route_control_point_count,
      last:saved.coords.at(-1),sourceLast:window.L.latLng(34.03+12*.07,-118.6+12*.095),
      fallback:saved.properties.route_fallback_leg_indices,
      allLegEnds:Array.from({length:12},(_,i)=>saved.properties['route_leg_end_'+i]),
      routeCleared:window.v233RouteState.points.length===0
    };
  }''')
  assert result['controlCount']==13 and result['routeCleared'], result
  assert result['fallback']=='3,7,10' and result['vertices']>=22,result
  assert abs(result['last'][0]-result['sourceLast']['lat'])<1e-6,result
  assert all(int(a)<int(b) for a,b in zip(result['allLegEnds'][:-1],result['allLegEnds'][1:])),result
  # Verify storage truncation does not clear 13-point editable route.
  page.evaluate('window.__truncate=true')
  state=seed(page); assert state['ready'];
  saved=page.evaluate('window.takRouteEditorI654.saveResolvedRoute({name:"Should fail storage check"})')
  assert saved is False,'truncated server geometry incorrectly marked successful'
  assert page.evaluate('window.v233RouteState.points.length')==13,'failed verification erased full route'
  page.evaluate('window.__truncate=false')
  edit=page.evaluate('''() => {
    const imp=window.__savedImports[0],feature=imp.features[0];
    const opened=window.takRouteEditorI654.startEditingSavedRoute(feature,imp);
    return {opened,controls:window.v233RouteState.points.length,
      fallback:window.takRouteEditorI654.legs.filter(l=>l.status==='error').length, warning:window.takRouteEditorI654.warning};
  }''')
  assert edit['opened'] and edit['controls']==13 and edit['fallback']==3,edit
  updated=page.evaluate('window.takRouteEditorI654.saveResolvedRoute({name:"Edited Full Trail"})')
  assert updated is True,'in-place edit did not preserve full route'
  assert page.evaluate('window.__savedImports[0].features[0].coords.length')>=22

  # Route selector visibility / map header placement
  page.evaluate(hud)
  page.wait_for_timeout(650)
  selector=page.locator('#takRouteSelectorI654');bounds=selector.bounding_box()
  assert bounds and bounds['y']>=100 and bounds['x']>=270, bounds
  mode=page.locator('#takRouteDataI675');grip=page.locator('#takRouteDataGripI676')
  assert grip.is_visible()
  b=mode.bounding_box();assert b and b['width']==155 and b['height']==25, b
  start=(b['x']+8,b['y']+12)
  page.mouse.move(*start);page.mouse.down();page.mouse.move(start[0]-150,start[1]+125,steps=5);page.mouse.up()
  page.wait_for_timeout(150)
  moved=mode.bounding_box();assert moved and moved['x']<b['x']-80 and moved['y']>b['y']+70,(b,moved)
  pos=page.evaluate('localStorage.getItem("tak-map.routing-data.position.i676")');assert pos and 'right' in pos,pos
  page.evaluate('document.getElementById("takRouteDataButtonI675").click()')
  assert page.locator('#takRouteDataMenuI675').is_visible()
  page.get_by_text('Reset Position',exact=True).click()
  reset=mode.bounding_box();assert reset and abs(reset['x']-b['x'])<=2,(b,reset)
  assert page.evaluate('localStorage.getItem("tak-map.routing-data.position.i676")') is None
  page.evaluate('window.activeMapTool="move";document.getElementById("toolRoute").classList.remove("active")');page.wait_for_timeout(620)
  assert mode.is_hidden()
  page.set_viewport_size({'width':900,'height':620});page.evaluate('window.activeMapTool="route"');page.wait_for_timeout(650)
  small=mode.bounding_box();assert small and small['x']>=269 and small['x']+155<=900,small
  print('PASS i676: 13 points / 12 legs / 3 disconnects saved, truncated readback refused, mode below header, HUD drag / reset / route-only',result,small)
  browser.close()
