import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
asset = (ROOT / 'assets' / 'tak-map-context-sidebar-i564.js').read_text(encoding='utf-8')

bootstrap = r'''
class Bounds { contains(){return true} getCenter(){return {lat:34,lng:-118}} }
class MapStub {
  constructor(node){this.node=node;this.events={};this.bounds=new Bounds();this.panCalls=[];this.zoom=10}
  on(names,fn){String(names).split(/\s+/).forEach(n=>(this.events[n]=this.events[n]||[]).push(fn));return this}
  fire(name,data={}){(this.events[name]||[]).slice().forEach(fn=>fn(data));return this}
  getContainer(){return this.node} getBounds(){return this.bounds} getZoom(){return this.zoom}
  panTo(center,opts){this.panCalls.push({center,opts});return this} setView(center,zoom,opts){this.panCalls.push({center,zoom,opts});return this}
  removeLayer(layer){layer.removed=true}
}
class LayerStub {
  constructor(lat,lng,html){this.lat=lat;this.lng=lng;this.events={};this.options={};this.removed=false;this.popup={_content:html,getContent(){return this._content}}}
  on(name,fn){(this.events[name]=this.events[name]||[]).push(fn);return this}
  off(name){if(name)this.events[name]=[];return this}
  getLatLng(){return {lat:this.lat,lng:this.lng}} getPopup(){return this.popup} unbindPopup(){this.popup=null;return this}
  remove(){this.removed=true}
}
window.L={DomEvent:{stop(){}}};
window.map=new MapStub(document.getElementById('map'));
window.__nativeDialogs=[];
window.alert=(...args)=>{window.__nativeDialogs.push(['alert',...args]);throw new Error('native alert invoked')};
window.confirm=(...args)=>{window.__nativeDialogs.push(['confirm',...args]);throw new Error('native confirm invoked')};
window.prompt=(...args)=>{window.__nativeDialogs.push(['prompt',...args]);throw new Error('native prompt invoked')};
const make=(kind,id,name,lat,lon)=>({
  uid:id,object_id:id,canonical_id:'datasync:'+id,mission_name:'Mission Alpha',mission_delete_target:'uid',mission_delete_value:id,
  delete_supported:true,name,callsign:name,kind,lat,lon
});
const point=make('', 'POINT-1','Point One',34.20,-118.40);
const route=make('route','ROUTE-1','Route One',34.30,-118.50);
const shape=make('shape','SHAPE-1','Shape One',34.40,-118.60);
for(const o of [point,route,shape]) o.__layer=new LayerStub(o.lat,o.lon,`<div class="feature-popup"><h3>${o.name}</h3><div class="kvp"><b>Name</b><span>${o.name}</span></div></div>`);
window.lastDataSync={objects:[point,route,shape]};
window.__objects={point,route,shape};
window.dataSyncCategory=o=>o.kind==='route'?'Routes':(o.kind==='shape'?'Shapes / Areas':'Point Markers');
window.layerPopupForObject=(o,cat)=>`<div class="feature-popup"><h3>${o.name}</h3><div class="kvp"><b>Category</b><span>${cat}</span></div></div>`;
window.importedFeatures=()=>[];
window.addObjectLayer=(group,o)=>o.__layer;
window.drawDataSyncObjects=()=>{};window.drawImportedObjects=()=>{};window.centerDataSyncIndex=()=>{};window.centerLocalItem=()=>{};window.chooseSearchItem=()=>{};
window.renderDataSyncRows=()=>{};
window.TakMapObjectLifecycleV486={canonicalId:(o,source)=>o.canonical_id||''};
window.TakMapIconRegistryI564={
  isPoint:o=>!o.kind, isLocalPoint:()=>false, pointUid:o=>o.uid, pointMission:o=>o.mission_name, pointLocalId:()=>'',
  pointInfoHtml:o=>`<div class="point-info-popup-i556"><div class="point-popup-body-i556"><div class="point-popup-grid-i556"><div class="point-popup-label-i556">Mission</div><div class="point-popup-value-i556">${o.mission_name}</div></div><div class="point-popup-actions-i556"><button class="point-popup-edit-i556">Edit Point</button></div></div></div>`
};
window.__fetchQueue=[];window.__deleteRequests=[];window.__refreshCalls=[];
window.fetch=async (url,options={})=>{
  if(url!=='/api/tak-map/object-delete') throw new Error('unexpected fetch '+url);
  const payload=JSON.parse(options.body||'{}');window.__deleteRequests.push({url,options,payload});
  const next=window.__fetchQueue.shift()||{status:200,body:{ok:true,deleted_ids:payload.object_ids,results:[]}};
  return new Response(JSON.stringify(next.body),{status:next.status,headers:{'content-type':'application/json'}});
};
window.refreshDataSync=async (...args)=>{window.__refreshCalls.push(args)};
'''

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
    page = browser.new_page(viewport={'width': 1400, 'height': 900})
    errors=[]
    page.on('pageerror', lambda exc: errors.append(str(exc)))
    page.set_content('''<!doctype html><html><head><style>body{margin:0;background:#111;color:#eee}#map{position:relative;width:1200px;height:880px;background:#26323b;overflow:hidden}.leaflet-control-scale{position:absolute;right:10px;bottom:10px;width:120px;height:25px;background:#eee}#dataSyncRows{position:absolute;left:10px;top:10px;background:#101923;padding:10px;z-index:4}</style></head><body><div id="map"><div class="leaflet-control-scale"></div><div id="dataSyncRows"><button id="legacyDelete" data-tak-delete-source="datasync" data-tak-delete-index="0" onclick="deleteDataSyncItem(0,event)">Delete</button></div></div></body></html>''')
    page.add_script_tag(content=bootstrap)
    page.add_script_tag(content=asset)
    page.wait_for_function("window.TakMapContextSidebarI564 && TakMapContextSidebarI564.diagnostics().installed")
    page.wait_for_function("TakMapContextSidebarI564.diagnostics().boundLayers===3")
    page.wait_for_function("document.getElementById('legacyDelete').dataset.takI564DeleteIndex==='0' && !document.getElementById('legacyDelete').hasAttribute('onclick')")

    print('step card open', flush=True)
    # The old Data Sync card button opens the same themed sidebar controller.
    page.click('#legacyDelete')
    page.wait_for_function("TakMapContextSidebarI564.diagnostics().mode==='delete-confirm'")
    first = page.evaluate('''() => ({
      title:document.getElementById('takMapContextTitleI564').textContent,
      text:document.getElementById('takMapContextSidebarBodyI564').textContent,
      open:!document.getElementById('takMapContextSidebarI564').classList.contains('collapsed'),
      native:window.__nativeDialogs.length,
      same:window.TakMapDeleteControllerI564===window.TakMapContextSidebarI564
    })''')
    assert first['title']=='Point One' and 'Delete Point One?' in first['text'], first
    assert first['open'] and first['native']==0 and first['same'], first

    print('step failure', flush=True)
    # A server failure is themed and inline; object/sidebar remain present/open.
    page.evaluate("window.__fetchQueue.push({status:403,body:{ok:false,failed_ids:['datasync:POINT-1'],results:[{object_id:'datasync:POINT-1',status:'failed',http_status:403,error:'Mission role does not permit deletion'}]}})")
    page.click('[data-i564-delete-confirm]')
    page.wait_for_function("TakMapContextSidebarI564.diagnostics().mode==='delete-error'")
    failed = page.evaluate('''() => ({
      text:document.getElementById('takMapContextSidebarBodyI564').textContent,
      open:!document.getElementById('takMapContextSidebarI564').classList.contains('collapsed'),
      removed:__objects.point.__layer.removed,
      native:__nativeDialogs.length,
      requests:__deleteRequests.length
    })''')
    assert failed['open'] and not failed['removed'] and failed['native']==0 and failed['requests']==1, failed
    assert 'OpenTAKServer HTTP 403' in failed['text'] and 'Mission role does not permit deletion' in failed['text'], failed

    print('step retry', flush=True)
    # Retry succeeds, removes the layer, refreshes Data Sync, and hides the sidebar.
    page.evaluate("window.__fetchQueue.push({status:200,body:{ok:true,deleted_ids:['datasync:POINT-1'],results:[{object_id:'datasync:POINT-1',status:'deleted'}]}})")
    page.click('[data-i564-delete-confirm]')
    page.wait_for_function("document.getElementById('takMapContextSidebarI564').classList.contains('collapsed')")
    success = page.evaluate("() => ({removed:__objects.point.__layer.removed,refresh:__refreshCalls.length,native:__nativeDialogs.length,requests:__deleteRequests.map(x=>x.payload.object_ids[0])})")
    assert success['removed'] and success['refresh']==1 and success['native']==0, success
    assert success['requests']==['datasync:POINT-1','datasync:POINT-1'], success

    print('step route shape', flush=True)
    # Route and shape information views expose their matching Delete controls.
    for name, label, canonical in [('route','Delete Route','datasync:ROUTE-1'),('shape','Delete Shape','datasync:SHAPE-1')]:
        page.evaluate(f"TakMapContextSidebarI564.showObject(__objects.{name},'datasync',__objects.{name}.__layer,false)")
        page.wait_for_function(f"document.getElementById('takMapContextTitleI564').textContent==='{name.title()} One'")
        button = page.locator('[data-tak-i564-delete-current]')
        assert button.text_content().strip() == label
        page.click('[data-tak-i564-delete-current]')
        page.wait_for_function("TakMapContextSidebarI564.diagnostics().mode==='delete-confirm'")
        page.evaluate(f"window.__fetchQueue.push({{status:200,body:{{ok:true,deleted_ids:['{canonical}'],results:[{{object_id:'{canonical}',status:'deleted'}}]}}}})")
        page.click('[data-i564-delete-confirm]')
        page.wait_for_function("document.getElementById('takMapContextSidebarI564').classList.contains('collapsed')")
        assert page.evaluate(f"__objects.{name}.__layer.removed") is True

    print('step final', flush=True)
    final = page.evaluate("() => ({native:__nativeDialogs.length,diag:TakMapContextSidebarI564.diagnostics(),requests:__deleteRequests.map(x=>x.payload.object_ids[0])})")
    assert final['native']==0, final
    assert final['diag']['contextualDelete'] and final['diag']['nativeDeleteDialogs'] is False and final['diag']['sharedDeleteController'], final
    assert final['requests'][-2:]==['datasync:ROUTE-1','datasync:SHAPE-1'], final
    assert not errors, errors
    browser.close()

print('i564 shared Data Sync/sidebar point, route, and shape deletion; themed failure; and no native-dialog checks passed')
sys.stdout.flush()
os._exit(0)
