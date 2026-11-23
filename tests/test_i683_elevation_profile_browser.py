"""TAK Map i683: real component mounted against a mocked Leaflet map; no terrain API writes.
Run: python tests/test_i683_elevation_profile_browser.py
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
HTML='''<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:0;background:#10232f;color:white;font:12px system-ui}
#map{position:fixed;inset:0;background:linear-gradient(140deg,#142b35,#304652)}
#toolRoute{position:fixed;right:18px;top:15px}
#routeMiniToolbar{position:fixed;right:18px;top:65px}
</style></head><body><div id="map"></div><button id="toolRoute">Route Creation</button><div id="routeMiniToolbar">Route tools</div></body></html>'''
INIT='''() => {
 window.map={_handlers:{},getContainer:()=>document.getElementById('map'),distance:(a,b)=>Math.hypot((a[0]-b[0])*111000,(a[1]-b[1])*111000),
  hasLayer:()=>false,on:function(e,fn){(this._handlers[e]??=[]).push(fn)},fire:function(e,p){(this._handlers[e]||[]).forEach(fn=>fn(p))}};
 window.takLeafletMap=window.map;
 window.L={circleMarker:()=>({addTo:()=>({})})};
 window.sourceRoute={};window.sourcePoint={};
 window.savedRoute={name:'Anza - Fish Creek',kind:'route',_local_id:'route1',coords:[[33.03,-116.10],[33.04,-116.09]],__layer:window.sourceRoute};
 window.importedFeatures=()=>[window.savedRoute,{name:'Point',kind:'point',__layer:window.sourcePoint}];
 window.localDataFeatureById=id=>id==='route1'?window.savedRoute:null;
}'''
SAMPLES='''() => {
 let a=TakMapElevationI681,s=a.state;
 s.samples=Array.from({length:101},(_,i)=>({d:i*30,lat:33.03+i*.00005,lng:-116.10+i*.00005}));
 s.elev=Array.from({length:101},(_,i)=>{
  let height=1100+i*.13;
  if(i>=18&&i<=26)height+=(i-18)*39;
  if(i>26)height+=8*39;
  if(i>=63&&i<=68)height-=(i-63)*40;
  if(i>68)height-=5*40;
  return height;
 });
 s.gradeWindowM=60;s.gradeGeneration++;a.redraw();
}'''

def main():
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  try:
   page=browser.new_page(viewport={'width':1280,'height':850})
   errors=[]
   page.on('pageerror',lambda error:errors.append(str(error)))
   page.set_content(HTML)
   page.evaluate("() => {const data={};Object.defineProperty(window,'localStorage',{configurable:true,value:{setItem:(k,v)=>data[k]=v,getItem:(k)=>data[k]||null}})}")
   page.add_script_tag(content="let activeMapTool='move';")
   page.evaluate(INIT)
   page.add_script_tag(path=str(ROOT/'assets/tak-map-route-elevation-i681.js'))
   panel=page.locator('#takRouteElevationI681')
   assert panel.is_hidden(), 'must be hidden with no route active/selected'
   page.evaluate("activeMapTool='route';TakMapElevationI681.syncLifecycle()")
   assert panel.is_visible() and 'compact' in panel.get_attribute('class')
   page.evaluate(SAMPLES)
   assert page.locator('#takElevHeaderDistanceI683').text_content().endswith(' mi')
   assert page.locator('#takElevSteepI681').text_content().endswith(' ft')
   assert page.locator('#takElevMarkersI683 button').count()>=2, 'marker for each steep run'
   page.screenshot(path='/mnt/data/_tak_i683_qa_compact.png')
   marker=page.locator('#takElevMarkersI683 button').first
   assert marker.evaluate('(el)=>getComputedStyle(el).cursor')=='pointer'
   marker.hover(force=True)
   assert page.locator('#takElevRunTipI683').is_visible()
   assert 'ft' in page.locator('#takElevRunTipI683').inner_text()
   marker.click(force=True)
   assert 'extended' in panel.get_attribute('class')
   page.screenshot(path='/mnt/data/_tak_i683_qa_extended.png')
   assert page.locator('#takElevCanvasI681').evaluate('(el)=>el.clientHeight')>=180
   assert page.locator('#takElevRunTipI683').is_hidden()
   page.locator('#takElevExpandI683').click()
   assert 'compact' in panel.get_attribute('class')
   assert page.locator('#takElevCanvasI681').evaluate('(el)=>el.clientHeight')==82
   assert page.locator('.tak-elev-chart-top-i683').is_hidden()
   assert page.locator('.tak-elev-metrics-i682').is_hidden()
   assert page.locator('.tak-elev-legend-i682').is_visible()
   print('PASS compact default, 82px chart, slim legend, 35° markers, hover feet, click-to-extended')
   handle=page.locator('#takElevDragI683')
   assert handle.evaluate('(e)=>getComputedStyle(e).cursor')=='grab'
   r=handle.bounding_box();old=panel.bounding_box()
   page.mouse.move(r['x']+50,r['y']+r['height']/2)
   page.mouse.down();page.mouse.move(r['x']+140,r['y']-60,steps=6)
   assert handle.evaluate('(e)=>getComputedStyle(e).cursor')=='grabbing'
   page.mouse.up()
   new=panel.bounding_box()
   assert abs(new['x']-old['x'])>50 and abs(new['y']-old['y'])>40,(old,new)
   stored=page.evaluate("localStorage.getItem('tak-map-elevation-i683-position')")
   assert stored is not None and 'x' in stored
   print('PASS floating header drag, grab/grabbing, persistent position')
   # Profile should hide when leaving route creation and no selection, even when X never clicked.
   page.evaluate("activeMapTool='move';TakMapElevationI681.syncLifecycle()")
   assert panel.is_hidden()
   page.evaluate("window.map.fire('popupopen',{popup:{_source:window.sourceRoute}})")
   assert panel.is_visible()
   page.evaluate(SAMPLES)
   assert page.locator('#takElevRouteNameI683').text_content().find('Anza')>=0
   page.evaluate("window.map.fire('popupopen',{popup:{_source:window.sourcePoint}})")
   assert panel.is_hidden(), 'point selection must hide elevation'
   page.evaluate("window.map.fire('popupopen',{popup:{_source:window.sourceRoute}})")
   assert panel.is_visible()
   page.evaluate("window.map.fire('popupclose',{popup:{_source:window.sourceRoute}})")
   assert panel.is_hidden(), 'deselect saved route must close'
   print('PASS visibility: no route -> hidden, live route -> shown, selected route -> shown, point/deselect -> hidden')
   page.evaluate("window.map.fire('popupopen',{popup:{_source:window.sourceRoute}})")
   assert panel.is_visible()
   page.locator('#takElevCloseI681').click()
   assert panel.is_hidden()
   page.evaluate("TakMapElevationI681.syncLifecycle()")
   assert panel.is_hidden()
   page.evaluate("TakMapElevationI681.showSavedRouteById('route1')")
   assert panel.is_visible(), 'explicit profile action can reopen after dismissal'
   print('PASS X fully closes, no spontaneous reopen, explicit route Profile reopens')
   if errors:raise AssertionError(errors)
   print('PASS no browser JavaScript exceptions')
   # Check narrow view constraints.
   page.set_viewport_size({'width':390,'height':630})
   page.wait_for_timeout(120)
   b=panel.bounding_box()
   assert b['x']>=-0.1 and b['y']>=-0.1 and b['x']+b['width']<=391 and b['y']+b['height']<=631,b
   assert page.locator('#takElevHeaderDistanceI683').is_visible()
   print('PASS viewport clamping and compact header at 390px')
   out=Path('/mnt/data/TAK-Map-i683-Elevation-Profile-Compact-Implementation.png')
   page.screenshot(path=str(out))
  finally:
   browser.close()

if __name__=='__main__':main()
