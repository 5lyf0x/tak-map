#!/usr/bin/env python3
"""Actual i659 editor + deferred Save Route dialog: edit, copy, cancel, waypoint interactions."""
import json, runpy, shutil
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
harness=runpy.run_path(str(ROOT/'scripts/test_route_editor_i654_browser.py'))['harness']
editor=(ROOT/'assets/tak-map-route-editor-i654.js').read_text()
manifest=json.loads((ROOT/'assets/tak-map-deferred-i553.json').read_text())
dialog=next(x['code'] for x in manifest['scripts'] if x['id']=='takMapRouteUiV500')
setup=r'''(()=>{
 document.body.insertAdjacentHTML('beforeend',`<input id="routeNameInput"><textarea id="routeNotesInput"></textarea><div id="routeEditPanel"></div>`);
 const original=fetch;
 const pts=Array.from({length:253},(_,i)=>{const t=i/252;
   return [34+.02*t+.0002*Math.sin(4*Math.PI*t),-118-.025*t];});
 const feature={kind:'route',name:'Original Saved Route',object_id:'local-sample-001',local_id:'local-sample-001',
  route_revision_i659:'f'.repeat(64),coords:pts,properties:{name:'Original Saved Route',color:'#ff6f2e',
    category:'Patrol',notes:'Original notes',route_control_point_count:'2',route_segment_modes:'roads',
    route_cp_0:'34.0000000,-118.0000000,roads',route_cp_1:'34.0200000,-118.0250000,roads',
    route_leg_end_0:'252',route_editor_version:'i659'}};
 const record={id:'file-111',name:'Original Saved Route.geojson',features:[feature]};
 window.originalRecord=record;window.lastImports=[record];window.allImports=[record];
 window.refreshImports=async()=>{window.lastImports=window.allImports;window.drawImportedObjects()};
 window.drawImportedObjects=()=>{window.drawCount=(window.drawCount||0)+1};
 window.confirm=()=>true;window.prompt=()=> 'New Route Copy';
 window.updated=0;window.copied=0;window.lastUpdate=null;
 fetch=async function(url,opts){
  if(url.endsWith('/imported'))return {ok:true,json:async()=>({ok:true,imports:window.allImports})};
  if(url.endsWith('/route-update-i659')){
   const j=JSON.parse(opts.body);window.lastUpdate=j;
   if(j.expected_revision!==feature.route_revision_i659) return {ok:false,json:async()=>({ok:false,error:'Stale revision'})};
   feature.coords=j.feature.geometry.coordinates.map(c=>[c[1],c[0]]);
   feature.properties={...j.feature.properties};feature.name=feature.properties.name;
   window.updated++;return {ok:true,json:async()=>({ok:true,imports:window.allImports})};
  }
  if(url.endsWith('/import')){
   const file=opts.body.get('files'),obj=JSON.parse(await file.text()),saved=obj.features[0];
   const copy={kind:'route',name:saved.properties.name,object_id:'local-copy-002',local_id:'local-copy-002',
    coords:saved.geometry.coordinates.map(c=>[c[1],c[0]]),properties:saved.properties};
   const incoming={id:'file-222',name:file.name,features:[copy]};
   window.allImports=[record,incoming];window.copied++;window.copyRecord=incoming;
   return {ok:true,json:async()=>({ok:true,imports:window.allImports})};
  }
  if(url.endsWith('/resolve')){
    const j=JSON.parse(opts.body),[a,b]=j.locations;
    const coordinates=Array.from({length:253},(_,i)=>{const t=i/252;
      return [a.lon+(b.lon-a.lon)*t+.0001*Math.sin(Math.PI*2*t),a.lat+(b.lat-a.lat)*t];});
    return {ok:true,json:async()=>({ok:true,geometry:{type:'LineString',coordinates}})};
  }
  return original(url,opts);
 };
})();'''

def test(page):
 errors=[];page.on('pageerror',lambda err:errors.append(str(err)))
 page.set_content(harness,wait_until='load')
 page.add_script_tag(content=setup)
 page.add_script_tag(content=dialog)
 page.add_script_tag(content=editor)
 page.wait_for_function('takRouteEditorI654?.installed && TakMapRouteUiV500')
 # Production imported-route popup owns the Edit Route button.
 page.evaluate('''()=>{
   const root=document.createElement('div');root.innerHTML='<div class="feature-popup"><h3>Original Saved Route</h3></div>';
   document.body.appendChild(root);
   const layer=new Layer([],{});layer.getPopup=()=>({getElement:()=>root});
   originalRecord.features[0].__layer=layer;
   window.testPopupLayer=layer;
   drawImportedObjects();
 }''')
 page.wait_for_function('!!window.testPopupLayer.events.popupopen',timeout=3000)
 page.evaluate("window.testPopupLayer.trigger('popupopen')")
 assert page.locator('button[data-tak-edit-route-i659]').is_visible()
 page.locator('button[data-tak-edit-route-i659]').click()
 # Existing imported route opens with only its 2 user-defined controls, preserving 253 road vertices.
 values=page.evaluate('''()=>({points:v233RouteState.points.length,shape:takRouteEditorI654.getResolvedSaveState().vertexCount,
      ready:takRouteEditorI654.getResolvedSaveState().ready,editing:!!takRouteEditorI654.editing})''')
 assert values=={'points':2,'shape':253,'ready':True,'editing':True},values
 assert page.locator('[data-route-edit-action="save"]').is_visible()
 assert page.locator('[data-route-edit-action="copy"]').is_visible()
 assert page.locator('[data-route-edit-action="cancel"]').is_visible()
 # Existing route segment click inserts in the middle, then the inserted control can be moved.
 page.evaluate('''()=>[...v233RouteState.hitLayer.layers].find(l=>l.options.weight===18).trigger('click')''')
 page.wait_for_function('v233RouteState.points.length===3')
 page.wait_for_function('takRouteEditorI654.getResolvedSaveState().ready',timeout=5000)
 page.evaluate('''()=>takRouteEditorI654.markers[1].trigger('click')''')
 assert page.locator('.tak-route-menu-i654 button[data-op="delete"]').is_visible()
 css=page.evaluate('''()=>({pad:getComputedStyle(document.querySelector('.tak-route-menu-i654')).padding,
  weight:getComputedStyle(document.querySelector('.tak-route-menu-i654 button')).fontWeight})''')
 assert css['pad']=='4px' and int(css['weight'])>=700,css
 page.locator('.tak-route-menu-i654 button[data-op="manual"]').click()
 assert page.evaluate('takRouteEditorI654.pointModes[1]')=='manual'
 page.evaluate('''()=>{const marker=takRouteEditorI654.markers[1];marker.setLatLng(L.latLng(34.008,-118.009));marker.trigger('dragend')}''')
 page.wait_for_function('takRouteEditorI654.getResolvedSaveState().ready',timeout=5000)
 page.evaluate('''()=>takRouteEditorI654.markers[1].trigger('click')''')
 page.locator('.tak-route-menu-i654 button[data-op="delete"]').click()
 assert page.evaluate('v233RouteState.points.length')==2
 page.wait_for_function('takRouteEditorI654.getResolvedSaveState().ready',timeout=5000)
 # Save Changes invokes route-only atomic update, not the import uploader.
 page.locator('[data-route-edit-action="save"]').click()
 page.wait_for_function('window.updated===1',timeout=5000)
 update=page.evaluate('''()=>({id:lastUpdate.object_id,importId:lastUpdate.import_id,
  coordinates:lastUpdate.feature.geometry.coordinates.length,
  controls:lastUpdate.feature.properties.route_control_point_count,
  originals:allImports.length,editor:!!takRouteEditorI654.editing})''')
 assert update['id']=='local-sample-001' and update['importId']=='file-111' and update['coordinates']>=3,update
 assert update['controls']==2 and update['originals']==1,update
 page.wait_for_function('takRouteEditorI654.editing===null')
 # Reopen the updated saved route and choose Save as New Route: existing Save dialog collects metadata.
 page.evaluate('''()=>{originalRecord.features[0].route_revision_i659='e'.repeat(64);
   takRouteEditorI654.startEditingSavedRoute(originalRecord.features[0],originalRecord)}''')
 page.locator('[data-route-edit-action="copy"]').click()
 assert page.locator('#takRouteSaveV500').is_visible()
 page.locator('#takRouteNameV500').fill('Route Edited Copy')
 page.locator('#takRouteColorV500').fill('#00aabb')
 page.locator('#takRouteCategoryV500').select_option('Patrol')
 page.locator('#takRouteNotesV500').fill('Independent copy')
 page.locator('#takRouteSaveButtonV500').click()
 page.wait_for_function('window.copied===1',timeout=5000)
 copy=page.evaluate('''()=>({length:copyRecord.features[0].coords.length,
  name:copyRecord.features[0].properties.name,notes:copyRecord.features[0].properties.notes,
  original:originalRecord.features[0].name,files:allImports.length})''')
 assert copy['length']>=3 and copy['name']=='Route Edited Copy' and copy['notes']=='Independent copy',copy
 assert copy['files']==2 and copy['original']=='Original Saved Route',copy
 # Cancel must not call either save endpoint.
 page.evaluate('''()=>{originalRecord.features[0].route_revision_i659='d'.repeat(64);
    takRouteEditorI654.startEditingSavedRoute(originalRecord.features[0],originalRecord)}''')
 page.locator('[data-route-edit-action="cancel"]').click()
 assert page.evaluate('''()=>!takRouteEditorI654.editing && updated===1 && copied===1''')
 assert not errors,errors

with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,executable_path=shutil.which('chromium') or '/usr/bin/chromium',
    args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
 page=browser.new_page(viewport={'width':1280,'height':820})
 test(page)
 page.close();browser.close()
print('PASS: i659 reopen 253-vertex route, move/insert/delete/manual, compact menu, in-place save, Save as New dialog, cancel')
