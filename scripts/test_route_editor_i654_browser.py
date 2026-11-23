"""Headless integration smoke tests for the staged route editor; no live network."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parents[1]
js=(root/'assets/tak-map-route-editor-i654.js').read_text()
harness=r'''
<!doctype html><html><head></head><body>
<div id="map" style="position:relative;width:1000px;height:700px;"></div>
<input id="routeColorInput" value="#ff6f2e"/>
<input id="routeStyleInput" value="solid"/>
<script>
window.activeMapTool='route';
class Layer{
 constructor(pos,opts={}){this.pos=pos;this.options=opts;this.events={};}
 addTo(m){if(!m.layers)m.layers=new Set();m.layers.add(this);return this}
 on(k,f){this.events[k]=f;return this}
 getLatLng(){return this.pos}
 setLatLng(v){this.pos=v;return this}
 trigger(k,originalEvent){return this.events[k]?.({target:this,latlng:Array.isArray(this.pos)?this.pos[Math.floor(this.pos.length/2)]:this.pos,originalEvent:originalEvent||{stopPropagation(){},preventDefault(){}}})}
}
const ll=(a,b)=>({lat:a,lng:b});
const map={layers:new Set(),events:{},
 distance(a,b){return Math.hypot((a.lat-b.lat)*111320,(a.lng-b.lng)*92200)},
 hasLayer(l){return this.layers.has(l)},removeLayer(l){this.layers.delete(l)},
 on(k,fn){(this.events[k]??=[]).push(fn);return this},
 emit(k,p){for(const fn of this.events[k]||[])fn({latlng:p,originalEvent:{stopPropagation(){},preventDefault(){}}})},
 latLngToContainerPoint(p){return {x:(p.lng+118)*1000,y:(34-p.lat)*1000,distanceTo(q){return Math.hypot(this.x-q.x,this.y-q.y)}}},
 latLngToLayerPoint(p){return this.latLngToContainerPoint(p)},
 layerPointToLatLng(p){return ll(34-p.y/1000,p.x/1000-118)},
 getContainer(){return document.getElementById('map')}
};
window.L={latLng:ll,point:(x,y)=>({x,y}),
 layerGroup:()=>new Layer([]),polyline:(p,o)=>new Layer(p,o),marker:(p,o)=>new Layer(p,o),
 circleMarker:(p,o)=>new Layer(p,o),divIcon:o=>o,DomEvent:{stop(){}}};
window.map=map;
window.v233RouteState={points:[],color:'#ff6f2e',style:'solid'};
window.v234RedrawRoute=function(){};
window.v233RouteMapClick=function(point){window.v233RouteState.points.push(point)};
window.savedRoute=[];window.lastSavedFeature=null;window.refreshImports=async()=>{};window.prompt=()=> 'Route Save Regression';
window.v233FinishRoute=async function(){throw Error('Legacy route saving bypassed the resolved geometry')};
window.v233ClearRoute=function(){window.v233RouteState.points=[]};
window.setActiveMapTool=function(tool){window.activeMapTool=tool};
window.toggleMapTool=function(tool){window.activeMapTool=tool};
window.failResolve=false;window.offsetRoutedStart=false;
window.fetch=async function(url,opts){
 if(url.endsWith('/import')){
  const file=opts.body.get('files');const obj=JSON.parse(await file.text());
  window.lastSavedFeature=obj.features[0];window.savedRoute=obj.features[0].geometry.coordinates;
  return {ok:true,json:async()=>({ok:true,imports:[{name:file.name,
   features:[{kind:'route',coords:window.savedRoute.map(p=>[p[1],p[0]])}]}]})};
 }
 if(url.endsWith('/imported'))return {ok:true,json:async()=>({ok:true,imports:[{name:(window.lastSavedFeature?.properties?.name||'Route Save Regression')+'.geojson',features:[{kind:'route',coords:window.savedRoute.map(p=>[p[1],p[0]])}]}]})};
 if(url.endsWith('/ndm/status'))return {ok:true,json:async()=>({ok:true,routing_enabled:true})};
 const req=JSON.parse(opts.body);
 if(url.endsWith('/snap'))return {ok:true,json:async()=>({ok:true,lat:req.lat,lon:req.lon})};
 if(url.endsWith('/resolve')){
  if(window.failResolve)return {ok:false,json:async()=>({ok:false,error:'Disconnected road graph'})};
  const [a,b]=req.locations;const latA=window.offsetRoutedStart?a.lat+.035:a.lat;
  return {ok:true,json:async()=>({ok:true,geometry:{type:'LineString',coordinates:[[a.lon,latA],[(latA+b.lat)/2+.0002,(a.lat+b.lat)/2+.0002],[b.lon,b.lat]]}})};
 }
 throw new Error('Unexpected URL '+url)
}
</script>
</body></html>
'''

def run():
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(headless=True, executable_path="/usr/bin/chromium", args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1200,'height':850})
        errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.set_content(harness,wait_until='load')
        page.add_script_tag(content=js)
        page.wait_for_function('window.takRouteEditorI654 && window.takRouteEditorI654.installed',timeout=3000)
        selector=page.locator('#takRouteSelectorI654')
        assert selector.is_visible(),'Mode selector hidden'
        assert page.evaluate('takRouteEditorI654.mode')=='roads','Roads must be the default'
        assert page.locator('#takRouteNetworkStateI655').is_visible()
        selector.locator('button[data-mode="manual"]').click()
        page.evaluate('''async()=>{
          await window.v233RouteMapClick(L.latLng(34,-118));
          await window.v233RouteMapClick(L.latLng(34.01,-118.01));
        }''')
        r=page.evaluate('''()=>({controls:v233RouteState.points.length,leg:takRouteEditorI654.legs[0].mode,status:takRouteEditorI654.legs[0].status})''')
        assert r=={'controls':2,'leg':'manual','status':'ready'},r
        assert '1 → 2' in page.locator('#takRouteHudI654').inner_text()
        # Switch to Roads, clear, then create two snapped waypoints and resolved geometry.
        selector.locator('button[data-mode="roads"]').click()
        page.evaluate('''async()=>{v233ClearRoute();await v233RouteMapClick(L.latLng(34,-118));await v233RouteMapClick(L.latLng(34.01,-118.01))}''')
        page.wait_for_function('takRouteEditorI654.legs[0] && takRouteEditorI654.legs[0].status==="ready"',timeout=3000)
        assert page.evaluate('takRouteEditorI654.legs[0].shape.length')==3
        # Click route geometry inserts a waypoint between controls.
        page.evaluate('''()=>{
          const h=v233RouteState.hitLayer;
          const first=[...v233RouteState.hitLayer.layers].find(x=>x.options&&x.options.weight===18);
          first.trigger('click');
        }''')
        page.wait_for_function('v233RouteState.points.length===3',timeout=3000)
        page.wait_for_function('takRouteEditorI654.legs.length===2&&takRouteEditorI654.legs.every(l=>l.status==="ready")',timeout=3000)
        # Waypoint popover can manually override a single control point.
        page.evaluate('''()=>takRouteEditorI654.markers[1].trigger('click')''')
        assert 'Copy Coordinates' in page.locator('.tak-route-menu-i654').inner_text()
        page.locator('.tak-route-menu-i654 button[data-op="manual"]').click()
        assert page.evaluate('takRouteEditorI654.pointModes[1]')=='manual'
        assert page.evaluate('takRouteEditorI654.legs.every(l=>l.mode==="roads")'), 'Manual waypoint should not turn whole legs into straight lines'
        # Dragging manual waypoint does not snap and recalculates only affected legs.
        page.evaluate('''()=>{
          const marker=takRouteEditorI654.markers[1];marker.setLatLng(L.latLng(34.006,-118.006));marker.trigger('dragend')
        }''')
        page.wait_for_function('Math.abs(v233RouteState.points[1].lat-34.006)<1e-7',timeout=3000)
        # A manually overridden control can sit well off the road; only its
        # connector is manual, while the graph-based leg remains Roads.
        page.evaluate('''async()=>{
          v233ClearRoute();await v233RouteMapClick(L.latLng(34,-118));await v233RouteMapClick(L.latLng(34.01,-118.01));
        }''')
        page.wait_for_function('takRouteEditorI654.legs[0]&&takRouteEditorI654.legs[0].status==="ready"',timeout=3000)
        page.evaluate('window.offsetRoutedStart=true')
        page.evaluate('''()=>takRouteEditorI654.markers[0].trigger('click')''')
        page.locator('.tak-route-menu-i654 button[data-op="manual"]').click()
        page.wait_for_function('takRouteEditorI654.legs[0]&&takRouteEditorI654.legs[0].status==="ready"',timeout=3000)
        check=page.evaluate('''()=>({manualStart:takRouteEditorI654.legs[0].manualStart,mode:takRouteEditorI654.legs[0].mode,shapeLength:takRouteEditorI654.legs[0].shape.length})''')
        assert check=={'manualStart':True,'mode':'roads','shapeLength':4},check
        page.evaluate('window.offsetRoutedStart=false')
        page.evaluate('v233ClearRoute()')
        # End-to-end save uses full resolved geometry for road segments.
        page.evaluate('''async()=>{
           v233ClearRoute();await v233RouteMapClick(L.latLng(34,-118));await v233RouteMapClick(L.latLng(34.01,-118.01))
        }''')
        page.wait_for_function('takRouteEditorI654.legs[0]&&takRouteEditorI654.legs[0].status==="ready"',timeout=3000)
        page.evaluate('''async()=>{await v233FinishRoute()}''')
        assert page.evaluate('savedRoute.length')==3, 'Saved route lost polyline vertices'
        assert page.evaluate('lastSavedFeature.properties.route_control_point_count')==2, 'Resolved geometry was confused with control points'
        assert page.evaluate('lastSavedFeature.properties.route_resolved_vertex_count')==3, 'Saved vertex count metadata mismatch'
        # Routing failure is visibly marked and cannot be saved.
        page.evaluate('''async()=>{
          window.failResolve=true;setActiveMapTool('route');await v233RouteMapClick(L.latLng(34,-118));await v233RouteMapClick(L.latLng(34.01,-118.01))
        }''')
        page.wait_for_function('takRouteEditorI654.legs[0]&&takRouteEditorI654.legs[0].status==="error"',timeout=3000)
        assert 'No connection' in page.locator('#takRouteHudI654').inner_text()
        page.evaluate('''async()=>{await v233FinishRoute()}''')
        assert page.evaluate('v233RouteState.points.length')==2,'Failed route wrongly saved'
        assert not errors,errors
        browser.close()
        print('PASS: manual/roads modes, 20px snapping, geometry save, click insertion, menu, manual override, dragging, distances, disconnected error')

if __name__=='__main__':run()
