#!/usr/bin/env python3
"""Browser regression for TAK Map i643 native Mission Shape save + center translation."""
from __future__ import annotations
from pathlib import Path
import json, shutil, urllib.parse, math
ROOT=Path(__file__).resolve().parents[1]
CONTEXT=(ROOT/'assets'/'tak-map-context-sidebar-i572.js').read_text()
PACKAGE=(ROOT/'assets'/'tak-map-package-i580.js').read_text()
ORIGIN='http://127.0.0.1'
FIXTURE=f"""<!doctype html><html><head><meta charset='utf-8'><base href='{ORIGIN}/'><style>
html,body{{margin:0;width:100%;height:100%;overflow:hidden;background:#071117;color:#e9f0f5;font-family:Arial,sans-serif}}#map{{position:relative;width:100%;height:100%}}
</style></head><body><aside class='version-panel'><div class='version-product'>TAK Map</div><span class='release-main'>1.4.0</span><span class='iteration-chip'>i643</span></aside><div id='map'></div>
<script>
window.ResizeObserver=class{{constructor(cb){{this.cb=cb}}observe(){{}}disconnect(){{}}}};
(function(){{
 const handlers={{}}; const mapEl=document.getElementById('map'); window.__markers=[];
 window.map={{_scale:26000,on(names,cb){{String(names).split(/\\s+/).forEach(n=>(handlers[n]||(handlers[n]=[])).push(cb));return this}},fire(name,event={{}}){{(handlers[name]||[]).forEach(cb=>cb(event));}},getContainer(){{return mapEl}},getBounds(){{return {{contains(){{return true}}}}}},getZoom(){{return 14}},panTo(){{}},setView(){{}},removeLayer(layer){{try{{layer.remove()}}catch(_){{}}}},latLngToContainerPoint(ll){{const lat=Array.isArray(ll)?Number(ll[0]):Number(ll.lat),lon=Array.isArray(ll)?Number(ll[1]):Number(ll.lng??ll.lon);return {{x:640+(lon+118.72761)*this._scale,y:380-(lat-34.2060116)*this._scale}};}}}};
 function latlng(v){{return Array.isArray(v)?{{lat:Number(v[0]),lng:Number(v[1])}}:{{lat:Number(v.lat),lng:Number(v.lng??v.lon)}}}}
 window.L={{DomEvent:{{disableClickPropagation(){{}},disableScrollPropagation(){{}},stop(){{}}}},divIcon(opts){{return opts||{{}}}},marker(ll,opts={{}}){{let pos=latlng(ll),node=null,evs={{}};const marker={{options:opts,addTo(m){{if(opts.icon&&opts.icon.html){{node=document.createElement('div');node.className=opts.icon.className||'';node.innerHTML=opts.icon.html;mapEl.appendChild(node)}}return this}},on(name,cb){{evs[name]=cb;return this}},getLatLng(){{return {{lat:pos.lat,lng:pos.lng}}}},setLatLng(v){{pos=latlng(v);return this}},remove(){{if(node&&node.remove)node.remove();node=null;return this}},fire(name,p={{}}){{if(evs[name])evs[name]({{target:this,...p}});return this}}}};window.__markers.push(marker);return marker;}}}};
 window.makeShapeLayer=function(points){{let pts=JSON.parse(JSON.stringify(points)),evs={{}};return {{options:{{}},setCalls:0,on(name,cb){{evs[name]=cb;return this}},off(name){{if(name)delete evs[name];return this}},unbindPopup(){{return this}},getPopup(){{return null}},getLatLngs(){{return JSON.parse(JSON.stringify(pts))}},setLatLngs(v){{pts=JSON.parse(JSON.stringify(v));this.setCalls++;return this}},redraw(){{return this}},getBounds(){{return {{getCenter(){{return {{lat:34.206,lng:-118.727}};}}}};}}}};}};
}})();
window.layerPopupForObject=(o)=>`<div class="tak-v322-popup" data-kind="Shape" data-source="Data Sync"><div class="tak-v322-bar"></div><div class="tak-v322-inner"><div class="tak-v322-title">${{o.name}}</div><div class="tak-v322-sub">Shape · Data Sync</div><div class="tak-v322-table"><div class="tak-v322-row"><b>Category</b><span>shape</span></div><div class="tak-v322-row"><b>Lat/Lon</b><span>${{o.lat}}, ${{o.lon}}</span></div><div class="tak-v322-row"><b>Points</b><span>${{o.coords.length}}</span></div><div class="tak-v322-row"><b>Rotation</b><span>126.1°</span></div><div class="tak-v322-row"><b>Notes</b><span>${{o.notes||''}}</span></div><div class="tak-v322-row"><b>Added</b><span>9/2/2026, 07:06</span></div></div><details class="popup-edit tak-v322-edit" data-key="datasync:${{o.uid}}" data-source="datasync"><summary>Edit</summary><div class="tak-v322-edit-fields"><label>Name<input name="name" value="${{o.name}}"></label><label>Category<input name="category" value="shape"></label><label>Lat/Lon<input name="latlon" value="${{o.lat}}, ${{o.lon}}"><input type="hidden" name="lat" value="${{o.lat}}"><input type="hidden" name="lon" value="${{o.lon}}"></label><label>Notes<textarea name="notes">${{o.notes||''}}</textarea></label></div><div class="tak-v322-actions"><button type="button">Old Save</button><button type="button">Old Cancel</button></div><div class="popup-edit-status"></div></details></div></div>`;
window.dataSyncCategory=(o)=>/u-d-r/.test(o.type||'')?'Shapes / Areas':'Point Markers'; window.lastDataSync={{objects:[]}};
</script>
<script src='/assets/runtime/tak-map-context-sidebar-i572.js?v=1.4.0-i643'></script><script src='/assets/runtime/tak-map-package-i580.js?v=1.4.0-i643'></script></body></html>"""
ORIGINAL={'uid':'rect-i643','name':'Rectangle 3','notes':'test note','type':'u-d-r','cot_type':'u-d-r','kind':'shape','geometry':'shape','is_mission_object':True,'mission_memberships':['1-40TH RECON'],'mission_name':'1-40TH RECON','lat':34.2060116,'lon':-118.72761,'shape_kind_i636':'rectangle','shape_closed_i636':True,'delete_supported':True,'raw_cot_i636':'<event uid="rect-i643" type="u-d-r"><point lat="34.2060116" lon="-118.72761"/><detail><contact callsign="Rectangle 3"/><link point="34.2102879,-118.7583232,0"/><link point="34.1830578,-118.7132411,0"/><link point="34.2017311,-118.6968958,0"/><link point="34.2289671,-118.7419826,0"/></detail></event>','coords':[[34.21028794604995,-118.75832320362926],[34.18305784557117,-118.71324111471124],[34.201731109450755,-118.69689581442177],[34.22896713330185,-118.74198259098516]]}
def dist(a,b): return math.hypot((a[0]-b[0])*111000,(a[1]-b[1])*92000)
def main():
    chromium=next((n for n in ('chromium','chromium-browser','google-chrome','google-chrome-stable') if shutil.which(n)),None)
    if not chromium: raise SystemExit('Chromium is required')
    from playwright.sync_api import sync_playwright
    errors=[]; posts=[]; saved_geom={'value':None}; readbacks={'n':0}
    with sync_playwright() as pw:
      browser=pw.chromium.launch(headless=True,executable_path=shutil.which(chromium),args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage']); page=browser.new_page(viewport={'width':1280,'height':760});page.on('pageerror',lambda exc:errors.append(str(exc)))
      def route(route):
        path=urllib.parse.urlsplit(route.request.url).path
        if path.endswith('tak-map-context-sidebar-i572.js'): route.fulfill(status=200,content_type='application/javascript',body=CONTEXT)
        elif path.endswith('tak-map-package-i580.js'): route.fulfill(status=200,content_type='application/javascript',body=PACKAGE)
        elif path=='/api/tak-map/popup-edit' and route.request.method=='POST':
          body=json.loads(route.request.post_data or '{}');posts.append(body); saved_geom['value']=body['shape_geometry_i639'];route.fulfill(status=200,content_type='application/json',body=json.dumps({'ok':True,'shape_geometry_i639':saved_geom['value'],'shape_edit_i639':{'persisted_overlay':True,'server_cot_updated':True,'readback_contract':'native-shape-global-ingest-contents-association-mission-readback-i643'},'shape_edit_i643':{'version':'i643','mission_backed':True,'authoritative_global_readback_confirmed':True,'authoritative_mission_readback_confirmed':True,'native_shape_contract':True,'commit_gate':'native-shape-global-ingest-then-mission-contents-and-cot-get-readback','missions':['1-40TH RECON']} }))
        elif path=='/api/tak-map/data-sync':
          readbacks['n']+=1; route.fulfill(status=200,content_type='application/json',body=json.dumps({'ok':True,'objects':[ORIGINAL]}))
        else: route.fulfill(status=404,body='not found')
      page.route('**/*',route);page.set_content(FIXTURE,wait_until='domcontentloaded');page.wait_for_function('window.TakMapContextSidebarI572')
      page.evaluate('(o)=>{const x=JSON.parse(JSON.stringify(o));x.__layer=window.makeShapeLayer(x.coords);window.__obj=x;window.__layer=x.__layer;window.lastDataSync={objects:[x]};TakMapContextSidebarI572.showObject(x,"datasync",x.__layer,false)}',ORIGINAL);page.wait_for_timeout(100)
      rows=page.evaluate("() => [...document.querySelectorAll('.tak-v322-row')].map(r=>(r.querySelector('b')?.textContent||'').trim())")
      assert 'Category' not in rows and 'Rotation' not in rows and rows[-1]=='Notes',rows
      page.click('.tak-shape-edit-toggle-i639');page.wait_for_timeout(80)
      ui=page.evaluate("""() => {const s=document.querySelector('[data-i640-shape-save]'),c=document.querySelector('[data-i640-shape-cancel]'),rows=[...document.querySelectorAll('.tak-v322-row')].map(r=>(r.querySelector('b')?.textContent||'').trim()),d=TakMapContextSidebarI572.diagnostics();return {sw:s.getBoundingClientRect().width,cw:c.getBoundingClientRect().width,sf:parseFloat(getComputedStyle(s).fontSize),cf:parseFloat(getComputedStyle(c).fontSize),rows,handles:d.shapeEditHandleCountI639,diag:d}}""")
      assert abs(ui['sw']-ui['cw'])<1.5 and ui['sf']>=11 and ui['cf']>=11,ui
      assert ui['rows'][-1]=='Notes' and ui['handles']==5 and ui['diag']['centerTranslationHandleI641'],ui
      # resize via first vertex (center is marker 0, corner marker 1)
      page.evaluate("() => {const hs=window.__markers.filter(m=>m.options&&m.options.draggable);hs[1].setLatLng([34.214,-118.764]).fire('drag')}");page.wait_for_timeout(50)
      resized=page.evaluate('window.__layer.getLatLngs()'); before_lengths=[dist(resized[i],resized[(i+1)%4]) for i in range(4)]
      # empty map click must not cancel
      page.evaluate("() => map.fire('click',{originalEvent:{target:document.getElementById('map')}})");page.wait_for_timeout(40)
      assert page.evaluate('TakMapContextSidebarI572.diagnostics().shapeEditActiveI640') is True
      # center translation: drag center marker, dimensions remain unchanged, Center field follows
      center_before=page.evaluate("document.querySelector('.tak-shape-center-input-i639').value")
      page.evaluate("() => {const hs=window.__markers.filter(m=>m.options&&m.options.draggable);const c=hs[0].getLatLng();hs[0].setLatLng([c.lat+0.006,c.lng+0.008]).fire('drag')}");page.wait_for_timeout(60)
      moved=page.evaluate('window.__layer.getLatLngs()'); after_lengths=[dist(moved[i],moved[(i+1)%4]) for i in range(4)];center_after=page.evaluate("document.querySelector('.tak-shape-center-input-i639').value")
      assert center_before!=center_after,(center_before,center_after)
      for a,b in zip(before_lengths,after_lengths): assert abs(a-b)<1.0,(before_lengths,after_lengths)
      # Save must trust only the backend's authoritative Mission /cot confirmation and never poll aggregate Data Sync.
      page.click('[data-i640-shape-save]');page.wait_for_timeout(180)
      final=page.evaluate("() => ({active:TakMapContextSidebarI572.diagnostics().shapeEditActiveI640,confirm:TakMapContextSidebarI572.diagnostics().shapeEditSaveConfirmationI641,diag:TakMapContextSidebarI572.diagnostics(),pts:window.__layer.getLatLngs(),center:[window.__obj.lat,window.__obj.lon]})")
      assert final['active'] is False and final['confirm']=='native-shape-global-mission-readback-i643',final
      assert final['diag']['nativeShapeSaveI643'] is True and final['diag']['globalNativeShapeReadbackI643'] is True and final['diag']['missionContentsUidAssociationI643'] is True and final['diag']['missionCotGetOnlyI643'] is True and final['diag']['aggregateDataSyncCommitGateI642'] is False,final
      assert readbacks['n']==0 and len(posts)==1,(readbacks,posts)
      for got,want in zip(final['pts'],saved_geom['value']['coords']): assert abs(got[0]-want[0])<2e-6 and abs(got[1]-want[1])<2e-6,(got,want)
      assert not errors,errors
      browser.close()
    print('TAK Map i643 native Mission Shape save and center translation browser regression passed')
if __name__=='__main__': main()
