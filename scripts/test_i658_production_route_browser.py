#!/usr/bin/env python3
"""Production deferred+inline Save Route source, real editor preview, HUD and readback."""
from __future__ import annotations
import ast,json,runpy,shutil
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'assets/tak-map-deferred-i553.json').read_text())
rows={r['id']:r['code'] for r in manifest['scripts']}
inline={}
for n in ast.parse((ROOT/'tak_dashboard.py').read_text()).body:
 if isinstance(n,ast.Try):
  for x in n.body:
   if isinstance(x,ast.Assign):
    for target in x.targets:
     if isinstance(target,ast.Name) and target.id in ('_I500_ROUTE_UI','_I501_ROUTE_SAVE_FIX'):
      inline[target.id]=ast.literal_eval(x.value).split('>',1)[1].rsplit('</script>',1)[0]
assert rows['takMapRouteUiV500']==inline['_I500_ROUTE_UI'], 'CRITICAL: deferred save UI differs from inline save UI'
assert rows['takMapRouteSaveFixV501']==inline['_I501_ROUTE_SAVE_FIX']
assert manifest['version']=='1.4.0-i659'
harness=runpy.run_path(str(ROOT/'scripts/test_route_editor_i654_browser.py'))['harness']
editor=(ROOT/'assets/tak-map-route-editor-i654.js').read_text()
chromium=shutil.which('chromium') or shutil.which('chromium-browser')
assert chromium
SETUP=r'''(()=>{
 document.body.insertAdjacentHTML('beforeend',`<input id="routeNameInput" value=""><input id="routeMethodInput" value="Driving">
 <input id="routeDirectionInput" value="Infil"><input id="routeTypeInput" value="Primary">
 <input id="routeOrderInput" value="Ascending Check Points"><input id="routePrefixInput" value="CP">
 <textarea id="routeNotesInput"></textarea><div id="routeEditPanel"></div>`);
 window.lastImports=[];
 window.drawImportedObjects=()=>{window.drawn=(window.drawn||0)+1};
 window.refreshImports=async()=>{window.lastImports=window.latestImports||[];window.drawImportedObjects()};
 const oldFetch=window.fetch;
 window.fetch=async function(url,opts){
   if(url.endsWith('/import')){
      const file=opts.body.get('files'),obj=JSON.parse(await file.text()),feature=obj.features[0];
      window.lastSavedFeature=feature;window.savedRoute=feature.geometry.coordinates;
      const props={};for(const [k,v] of Object.entries(feature.properties))props[k]=String(v).slice(0,500);
      window.latestImports=[{name:file.name,features:[{kind:'route',name:feature.properties.name,
        coords:feature.geometry.coordinates.map(p=>[p[1],p[0]]),properties:props}]}];
      return {ok:true,json:async()=>({ok:true,imports:window.latestImports})};
   }
   if(url.endsWith('/imported'))return {ok:true,json:async()=>({ok:true,imports:window.latestImports||[]})};
   if(url.endsWith('/resolve')){
      const req=JSON.parse(opts.body),[a,b]=req.locations;
      const coordinates=Array.from({length:253},(_,i)=>{
        const t=i/252,wiggle=(i===0||i===252)?0:.0001*Math.sin(Math.PI*4*t);
        return [a.lon+(b.lon-a.lon)*t+wiggle,a.lat+(b.lat-a.lat)*t+wiggle];
      });
      return {ok:true,json:async()=>({ok:true,geometry:{type:'LineString',coordinates}})};
   }
   return oldFetch(url,opts);
 };
})();'''

def run_case(browser,deferred_first):
 page=browser.new_page(viewport={'width':1280,'height':820})
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.set_content(harness,wait_until='domcontentloaded')
 page.add_script_tag(content=SETUP)
 if deferred_first:
  page.add_script_tag(content=rows['takMapRouteUiV500'])
  page.add_script_tag(content=inline['_I500_ROUTE_UI'])
 else:
  page.add_script_tag(content=inline['_I500_ROUTE_UI'])
  page.add_script_tag(content=rows['takMapRouteUiV500'])
 page.add_script_tag(content=rows['takMapRouteSaveFixV501'])
 page.add_script_tag(content=editor)
 page.wait_for_function('window.takRouteEditorI654?.installed && window.TakMapRouteUiV500')
 page.wait_for_timeout(4200) # legacy timers overwrite Finish; real user clicks Save after this
 assert page.evaluate('v233FinishRoute.__takRouteSaveV500===true')
 selector=page.locator('#takRouteSelectorI654')
 assert selector.is_visible() and selector.locator('button.active').inner_text()=='Roads'
 # The first waypoint must preview the routed leg to the cursor, not just a snap marker.
 page.evaluate('''async()=>{await v233RouteMapClick(L.latLng(34,-118));map.emit('mousemove',L.latLng(34.01,-118.01))}''')
 page.wait_for_function("takRouteEditorI654.preview&&takRouteEditorI654.preview.pos.length===253",timeout=2500)
 preview=page.evaluate('''()=>({vertices:takRouteEditorI654.preview.pos.length,
  dashed:takRouteEditorI654.preview.options.dashArray,
  first:takRouteEditorI654.preview.pos[0],last:takRouteEditorI654.preview.pos.at(-1)})''')
 assert preview['vertices']==253 and preview['dashed'],preview
 page.evaluate('''async()=>{await v233RouteMapClick(L.latLng(34.01,-118.01))}''')
 page.wait_for_function('takRouteEditorI654.getResolvedSaveState().ready')
 assert page.evaluate('takRouteEditorI654.getResolvedSaveState().vertexCount')==253
 labels=page.evaluate('''()=>takRouteEditorI654.labels.filter(l=>l.options.icon?.className==='tak-route-distance-icon-i658')
   .map(l=>({pos:l.pos,html:l.options.icon.html}))''')
 assert len(labels)==1 and 'mi' in labels[0]['html'],labels
 # The HUD grows upward (no per-leg 125px scrollbar).
 css=page.evaluate('''()=>({legs:getComputedStyle(document.querySelector('.tak-route-hud-legs-i654')).overflowY,
  maxHeight:getComputedStyle(document.querySelector('.tak-route-hud-legs-i654')).maxHeight,
  hudBottom:getComputedStyle(document.getElementById('takRouteHudI654')).bottom})''')
 assert css['legs']!='auto' and css['maxHeight']=='none' and css['hudBottom']=='72px',css
 # If another startup owner removes the selector, it is recreated and re-shown.
 page.evaluate("document.getElementById('takRouteSelectorI654').remove()")
 page.wait_for_function("document.getElementById('takRouteSelectorI654') && !document.getElementById('takRouteSelectorI654').hidden",timeout=3400)
 assert page.locator('#takRouteSelectorI654').is_visible()
 page.evaluate('v233FinishRoute()')
 page.wait_for_selector('#takRouteSaveV500')
 page.locator('#takRouteNameV500').fill('Arizona Snapped 253 Check')
 page.locator('#takRouteCategoryV500').select_option('Patrol')
 page.locator('#takRouteSaveButtonV500').click()
 page.wait_for_function('window.savedRoute?.length===253 && window.takRouteEditorI654.savedLabels.length===1',timeout=4000)
 saved=page.evaluate('''()=>({coords:window.savedRoute,props:window.lastSavedFeature.properties,
  imported:window.lastImports[0].features[0],labels:takRouteEditorI654.savedLabels.length,
  originalWaypoints:window.v233RouteState.points.length})''')
 assert len(saved['coords'])==253 and saved['props']['route_control_point_count']==2
 assert saved['props']['route_resolved_vertex_count']==253
 assert saved['props']['route_leg_label_count']==1 and saved['props']['route_leg_label_0']
 assert saved['labels']==1 and saved['originalWaypoints']==0,saved
 assert not errors,errors
 page.close()
 return saved

with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,executable_path=chromium,args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
 for deferred_first in (True,False):run_case(browser,deferred_first)
 browser.close()
print('PASS: i658 production deferred/inline owner precedence, Roads preview, selector recovery, HUD, per-leg distance, full GeoJSON save and imported labels')
