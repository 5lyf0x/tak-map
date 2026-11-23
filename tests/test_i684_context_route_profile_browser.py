"""Regression: real context sidebar selection -> real elevation panel. No live TAK server."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
HTML='''<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:0;background:#10232f;color:white;font:12px system-ui}
#map{position:fixed;inset:0;background:#142b35}
#toolRoute{position:fixed;right:18px;top:15px}
#routeMiniToolbar{position:fixed;right:18px;top:65px}
#sidebar{position:fixed;top:70px;left:0;bottom:0;width:200px;background:#111e2c}
</style></head><body><div id="map"></div><div id="sidebar"></div>
<button id="toolRoute">Route Creation</button><div id="routeMiniToolbar">Route tools</div></body></html>'''
INIT='''() => {
 window.map={_handlers:{},getContainer:()=>document.getElementById('map'),getZoom:()=>13,
 distance:(a,b)=>Math.hypot((a[0]-b[0])*111000,(a[1]-b[1])*111000),
 getBounds:()=>({contains:()=>true}),panTo:()=>{},getSize:()=>({x:1280,y:800}),hasLayer:()=>false,
 on:function(e,fn){e.split(' ').forEach(k=>(this._handlers[k]??=[]).push(fn))},
 fire:function(e,p){(this._handlers[e]||[]).forEach(fn=>fn(p))}};
 window.takLeafletMap=window.map;
 window.L={circleMarker:()=>({addTo:()=>({})})};
 window.sourceRoute={};window.sourcePoint={};
 window.savedRoute={name:'Anza - Fish Creek',kind:'route',_local_id:'route1',
  coords:Array.from({length:1625},(_,i)=>[33.03+i*.00001,-116.10+i*.00001]),__layer:window.sourceRoute};
 window.point={name:'Point',kind:'point',lat:33.04,lon:-116.09,__layer:window.sourcePoint};
 window.shape={name:'Shape',kind:'polygon',coords:[[33,-116],[33.01,-116],[33.01,-116.01]],__layer:{}};
 window.importedFeatures=()=>[window.savedRoute,window.point,window.shape];
 window.localDataFeatureById=id=>id==='route1'?window.savedRoute:null;
 window.__events=[];
 window.addEventListener('tak-map-context-selection-i684',ev=>window.__events.push({selected:ev.detail?.selected,kind:ev.detail?.kind,key:ev.detail?.key}));
}'''

def main():
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  try:
   page=browser.new_page(viewport={'width':1280,'height':800})
   errors=[]
   page.on('pageerror',lambda err:errors.append(str(err)))
   page.set_content(HTML)
   page.add_script_tag(content="let activeMapTool='move';")
   page.evaluate(INIT)
   page.add_script_tag(path=str(ROOT/'assets/tak-map-route-elevation-i681.js'))
   page.add_script_tag(path=str(ROOT/'assets/tak-map-context-sidebar-i572.js'))
   panel=page.locator('#takRouteElevationI681')
   assert panel.is_hidden()
   page.evaluate('TakMapContextSidebarI572.showObject(window.savedRoute,"local",window.sourceRoute,false)')
   assert panel.is_visible(),'route selected via real Context Sidebar must open elevation'
   assert 'Anza' in page.locator('#takElevRouteNameI683').inner_text()
   assert page.evaluate('TakMapElevationI681.state.full.length')==1625
   print('PASS actual saved-route sidebar selection opens elevation with 1625 original points')
   page.evaluate("window.map.fire('click',{originalEvent:{target:document.getElementById('map')}})")
   page.wait_for_timeout(220)
   assert panel.is_visible(),'map click queued by route selection must not hide it'
   print('PASS map-click race does not dismiss selected route')
   page.evaluate('TakMapContextSidebarI572.showObject(window.point,"local",window.sourcePoint,false)')
   assert panel.is_hidden(),'point selection hides profile'
   page.evaluate('TakMapContextSidebarI572.showObject(window.savedRoute,"local",window.sourceRoute,false)')
   assert panel.is_visible()
   page.locator('#takElevCloseI681').click()
   assert panel.is_hidden(),'X must fully close the panel'
   page.evaluate('TakMapContextSidebarI572.showObject(window.savedRoute,"local",window.sourceRoute,false)')
   assert panel.is_hidden(),'same selection stays dismissed'
   page.evaluate('TakMapContextSidebarI572.hide("button")')
   page.evaluate('TakMapContextSidebarI572.showObject(window.savedRoute,"local",window.sourceRoute,false)')
   assert panel.is_visible(),'new selection after deselect reopens'
   print('PASS point selection, X dismissal, and reselect after deselection')
   page.evaluate('TakMapContextSidebarI572.hide("button")')
   assert panel.is_hidden(),'hide detail panel hides profile'
   page.evaluate('TakMapContextSidebarI572.showObject(window.shape,"local",window.shape.__layer,false)')
   assert panel.is_hidden(),'shape never opens profile'
   print('PASS route deselection and shape selection hide profile')
   assert page.evaluate('window.__events.length')>=6
   assert not errors,errors
   print('PASS no browser page errors, context selection events emitted')
  finally:browser.close()
if __name__=='__main__':main()
