#!/usr/bin/env python3
"""Browser regression for TAK Map i640 authoritative Shape edit draft and compact controls."""
from __future__ import annotations
from pathlib import Path
import json, shutil, urllib.parse

ROOT=Path(__file__).resolve().parents[1]
CONTEXT=(ROOT/'assets'/'tak-map-context-sidebar-i572.js').read_text()
PACKAGE=(ROOT/'assets'/'tak-map-package-i580.js').read_text()
ORIGIN='http://127.0.0.1'
FIXTURE=f"""<!doctype html><html><head><meta charset='utf-8'><base href='{ORIGIN}/'><style>
html,body{{margin:0;width:100%;height:100%;overflow:hidden;background:#071117;color:#e9f0f5;font-family:Arial,sans-serif}}#map{{position:relative;width:100%;height:100%}}
.tak-v322-title{{font-weight:900}}
</style></head><body><aside class='version-panel'><div class='version-product'>TAK Map</div><span class='release-main'>1.4.0</span><span class='iteration-chip'>i639</span></aside><div id='map'></div>
<script>
window.ResizeObserver=class{{constructor(cb){{this.cb=cb}}observe(){{}}disconnect(){{}}}};
(function(){{
 const handlers={{}}; const mapEl=document.getElementById('map'); window.__i640Markers=[];
 window.map={{_scale:26000,on(names,cb){{String(names).split(/\\s+/).forEach(n=>(handlers[n]||(handlers[n]=[])).push(cb));return this}},fire(name,event={{}}){{(handlers[name]||[]).forEach(cb=>cb(event));}},getContainer(){{return mapEl}},getBounds(){{return {{contains(){{return true}}}}}},getZoom(){{return 14}},panTo(){{}},setView(){{}},removeLayer(layer){{try{{layer.remove()}}catch(_){{}}}},latLngToContainerPoint(ll){{const lat=Array.isArray(ll)?Number(ll[0]):Number(ll.lat),lon=Array.isArray(ll)?Number(ll[1]):Number(ll.lng??ll.lon);return {{x:640+(lon+118.72761)*this._scale,y:380-(lat-34.2060116)*this._scale}};}}}};
 function latlng(v){{return Array.isArray(v)?{{lat:Number(v[0]),lng:Number(v[1])}}:{{lat:Number(v.lat),lng:Number(v.lng??v.lon)}}}}
 window.L={{DomEvent:{{disableClickPropagation(){{}},disableScrollPropagation(){{}},stop(){{}}}},divIcon(opts){{return opts||{{}}}},marker(ll,opts={{}}){{let pos=latlng(ll),node=null,evs={{}};const marker={{options:opts,addTo(m){{if(opts.icon&&opts.icon.html){{node=document.createElement('div');node.className=opts.icon.className||'';node.innerHTML=opts.icon.html;mapEl.appendChild(node)}}return this}},on(name,cb){{evs[name]=cb;return this}},getLatLng(){{return {{lat:pos.lat,lng:pos.lng}}}},setLatLng(v){{pos=latlng(v);return this}},remove(){{if(node&&node.remove)node.remove();node=null;return this}},fire(name,p={{}}){{if(evs[name])evs[name]({{target:this,...p}});return this}}}};window.__i640Markers.push(marker);return marker;}}}};
 window.makeShapeLayer=function(points){{let pts=JSON.parse(JSON.stringify(points)),evs={{}};return {{options:{{}},setCalls:0,on(name,cb){{evs[name]=cb;return this}},off(name){{if(name)delete evs[name];return this}},unbindPopup(){{return this}},getPopup(){{return null}},getLatLngs(){{return JSON.parse(JSON.stringify(pts))}},setLatLngs(v){{pts=JSON.parse(JSON.stringify(v));this.setCalls++;return this}},redraw(){{return this}},getBounds(){{return {{getCenter(){{return {{lat:34.206,lng:-118.727}};}}}};}}}};}};
}})();
window.layerPopupForObject=(o)=>`<div class="tak-v322-popup" data-kind="Shape" data-source="Local Data"><div class="tak-v322-bar"></div><div class="tak-v322-inner"><div class="tak-v322-title">${{o.name}}</div><div class="tak-v322-sub">Shape · Local Data</div><div class="tak-v322-table"><div class="tak-v322-row"><b>Category</b><span>shape</span></div><div class="tak-v322-row"><b>Lat/Lon</b><span>${{o.lat}}, ${{o.lon}}</span></div><div class="tak-v322-row"><b>Points</b><span>${{o.coords.length}}</span></div><div class="tak-v322-row"><b>Width</b><span>old width</span></div><div class="tak-v322-row"><b>Height</b><span>old height</span></div><div class="tak-v322-row"><b>Rotation</b><span>126.1°</span></div><div class="tak-v322-row"><b>Notes</b><span>${{o.notes||''}}</span></div><div class="tak-v322-row"><b>Added</b><span>9/2/2026, 07:06</span></div></div><details class="popup-edit tak-v322-edit" data-key="datasync:${{o.uid}}" data-source="datasync"><summary>Edit</summary><div class="tak-v322-edit-fields"><label>Name<input name="name" value="${{o.name}}"></label><label>Category<input name="category" value="shape"></label><label>Lat/Lon<input name="latlon" value="${{o.lat}}, ${{o.lon}}"><input type="hidden" name="lat" value="${{o.lat}}"><input type="hidden" name="lon" value="${{o.lon}}"></label><label>Notes<textarea name="notes">${{o.notes||''}}</textarea></label></div><div class="tak-v322-actions"><button type="button" data-v322-popup-action="save">Old Save</button><button type="button" data-v322-popup-action="cancel">Old Cancel</button><button type="button" class="danger">Delete</button></div><div class="popup-edit-status"></div></details></div></div>`;
window.dataSyncCategory=(o)=>/u-d-r/.test(o.type||'')?'Shapes / Areas':'Point Markers';
window.lastDataSync={{objects:[]}};
</script>
<script src='/assets/runtime/tak-map-context-sidebar-i572.js?v=1.4.0-i640'></script>
<script src='/assets/runtime/tak-map-package-i580.js?v=1.4.0-i640'></script>
</body></html>"""

ORIGINAL={
    'uid':'rect-i640','name':'Rectangle 3','notes':'test note','type':'u-d-r','cot_type':'u-d-r','kind':'shape','geometry':'shape',
    'is_mission_object':True,'mission_memberships':['1-40TH RECON'],'mission_name':'1-40TH RECON',
    'lat':34.2060116,'lon':-118.72761,'shape_kind_i636':'rectangle','shape_closed_i636':True,'delete_supported':True,
    'raw_cot_i636':'<event uid="rect-i640" type="u-d-r"><point lat="34.2060116" lon="-118.72761"/><detail><contact callsign="Rectangle 3"/><link point="34.2102879,-118.7583232,0"/><link point="34.1830578,-118.7132411,0"/><link point="34.2017311,-118.6968958,0"/><link point="34.2289671,-118.7419826,0"/></detail></event>',
    'coords':[[34.21028794604995,-118.75832320362926],[34.18305784557117,-118.71324111471124],[34.201731109450755,-118.69689581442177],[34.22896713330185,-118.74198259098516]],
}

def main()->int:
    chromium=next((n for n in ('chromium','chromium-browser','google-chrome','google-chrome-stable') if shutil.which(n)),None)
    if not chromium: raise SystemExit('Chromium is required')
    from playwright.sync_api import sync_playwright
    errors=[]; posts=[]; save_attempt={'n':0}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=shutil.which(chromium),args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
        context=browser.new_context(locale='en-US',viewport={'width':1280,'height':760})
        page=context.new_page(); page.on('pageerror',lambda exc:errors.append(str(exc)))
        def route(route):
            path=urllib.parse.urlsplit(route.request.url).path
            if path.endswith('tak-map-context-sidebar-i572.js'): route.fulfill(status=200,content_type='application/javascript',body=CONTEXT)
            elif path.endswith('tak-map-package-i580.js'): route.fulfill(status=200,content_type='application/javascript',body=PACKAGE)
            elif path=='/api/tak-map/popup-edit' and route.request.method=='POST':
                body=json.loads(route.request.post_data or '{}'); posts.append(body); save_attempt['n']+=1
                if save_attempt['n']==1: route.fulfill(status=500,content_type='application/json',body=json.dumps({'ok':False,'error':'simulated save failure'}))
                else: route.fulfill(status=200,content_type='application/json',body=json.dumps({'ok':True,'shape_geometry_i639':body.get('shape_geometry_i639',{})}))
            else: route.fulfill(status=404,body='not found')
        page.route('**/*',route)
        page.set_content(FIXTURE,wait_until='domcontentloaded',timeout=20000)
        page.wait_for_function('window.TakMapContextSidebarI572 && window.TakMapContextPanelSizingI620')
        page.evaluate('(o)=>{const x=JSON.parse(JSON.stringify(o));x.__layer=window.makeShapeLayer(x.coords);window.__baseObj=x;window.__baseLayer=x.__layer;window.lastDataSync={objects:[x]};TakMapContextSidebarI572.showObject(x,"datasync",x.__layer,false)}',ORIGINAL)
        page.wait_for_timeout(150)
        normal=page.evaluate("""() => {const b=document.getElementById('takMapContextSidebarBodyI572'),rows=[...b.querySelectorAll('.tak-v322-row')].map(r=>(r.querySelector('b')?.textContent||'').trim());const title=b.querySelector('.tak-v322-title');return {rows,title:title?.textContent||'',weight:Number(getComputedStyle(title).fontWeight)||0,edit:b.querySelector('.tak-shape-edit-toggle-i639')?.textContent||'',diag:TakMapContextSidebarI572.diagnostics()};}""")
        assert normal['title']=='Rectangle 3' and normal['weight']<=500,normal
        assert normal['edit']=='Edit',normal
        for absent in ('Category','Rotation','Width','Height'): assert absent not in normal['rows'],normal
        for present in ('Center','Points','Area','Perimeter','Added'): assert present in normal['rows'],normal
        assert normal['diag']['authoritativeDraftI640'] and normal['diag']['closeEditRemovedI640'],normal

        page.click('.tak-shape-edit-toggle-i639'); page.wait_for_timeout(80)
        edit=page.evaluate("""() => {const b=document.getElementById('takMapContextSidebarBodyI572'),toggle=b.querySelector('.tak-shape-edit-toggle-i639'),save=b.querySelector('[data-i640-shape-save]'),cancel=b.querySelector('[data-i640-shape-cancel]'),del=b.querySelector('.tak-context-delete-button-i572'),name=b.querySelector('.tak-shape-name-input-i639'),sr=save.getBoundingClientRect(),cr=cancel.getBoundingClientRect();return {toggleDisplay:getComputedStyle(toggle).display,buttons:[save?.textContent,cancel?.textContent],saveWidth:sr.width,cancelWidth:cr.width,deleteText:del?.textContent||'',nameWeight:Number(getComputedStyle(name).fontWeight)||0,diag:TakMapContextSidebarI572.diagnostics()};}""")
        assert edit['toggleDisplay']=='none' and edit['buttons']==['Save','Cancel'],edit
        assert abs(edit['saveWidth']-edit['cancelWidth'])<1.5 and edit['saveWidth']>100,edit
        assert edit['deleteText']=='Delete Shape' and edit['nameWeight']<=500,edit
        assert edit['diag']['shapeEditActiveI640'] and edit['diag']['shapeEditHandleCountI639']==4,edit

        drag=page.evaluate("""() => {const h=window.__i640Markers.find(m=>m.options&&m.options.draggable===true);const before=window.__baseLayer.getLatLngs();h.setLatLng([34.216,-118.766]).fire('drag');const after=window.__baseLayer.getLatLngs();const hp=h.getLatLng();return {before,after,hp,diag:TakMapContextSidebarI572.diagnostics()};}""")
        assert drag['before']!=drag['after'] and drag['diag']['shapeEditDirtyI640'] and drag['diag']['shapeEditRevisionI640']>0,drag
        edited0=drag['after'][0]

        # Simulate the periodic Data Sync replacement that caused i639 to snap the stroke back.
        page.evaluate('(o)=>{const fresh=JSON.parse(JSON.stringify(o));fresh.__layer=window.makeShapeLayer(fresh.coords);window.__freshObj=fresh;window.__freshLayer=fresh.__layer;window.lastDataSync={objects:[fresh]};}',ORIGINAL)
        page.wait_for_timeout(2750)
        refresh=page.evaluate("""() => {const pts=window.__freshLayer.getLatLngs(),h=window.__i640Markers.find(m=>m.options&&m.options.draggable===true)?.getLatLng(),d=TakMapContextSidebarI572.diagnostics();return {pts,h,baseOriginal:window.__freshObj.coords[0],diag:d,area:[...document.querySelectorAll('.tak-v322-row')].find(r=>(r.querySelector('b')?.textContent||'').trim()==='Area')?.querySelector('span')?.textContent||''};}""")
        assert refresh['pts'][0]!=ORIGINAL['coords'][0],refresh
        assert abs(refresh['pts'][0][0]-edited0[0])<1e-8 and abs(refresh['pts'][0][1]-edited0[1])<1e-8,refresh
        assert abs(refresh['h']['lat']-refresh['pts'][0][0])<1e-8 and abs(refresh['h']['lng']-refresh['pts'][0][1])<1e-8,refresh
        assert refresh['diag']['shapeEditActiveI640'] and refresh['diag']['shapeEditDirtyI640'],refresh

        # A failed save must be visible and must not discard the draft.
        page.click('[data-i640-shape-save]'); page.wait_for_timeout(120)
        failed=page.evaluate("""() => ({diag:TakMapContextSidebarI572.diagnostics(),status:document.querySelector('.popup-edit-status')?.textContent||'',pts:window.__freshLayer.getLatLngs()})""")
        assert failed['diag']['shapeEditActiveI640'] and 'simulated save failure' in failed['status'],failed
        assert abs(failed['pts'][0][0]-edited0[0])<1e-8,failed

        # Second Save succeeds, exits edit mode, and sends exactly the visible draft geometry.
        page.click('[data-i640-shape-save]'); page.wait_for_timeout(180)
        saved=page.evaluate("""() => {const b=document.getElementById('takMapContextSidebarBodyI572'),d=TakMapContextSidebarI572.diagnostics();return {active:d.shapeEditActiveI640,edit:b.querySelector('.tak-shape-edit-toggle-i639')?.textContent||'',close:[...b.querySelectorAll('button')].some(x=>x.textContent.trim()==='Close Edit'),name:b.querySelector('.tak-v322-title')?.textContent||''};}""")
        assert not saved['active'] and saved['edit']=='Edit' and not saved['close'] and saved['name']=='Rectangle 3',saved
        assert len(posts)==2,posts
        payload=posts[-1]['shape_geometry_i639']
        assert abs(payload['coords'][0][0]-edited0[0])<1e-8 and abs(payload['coords'][0][1]-edited0[1])<1e-8,payload
        assert payload['uid']=='rect-i640' and payload['cot_type']=='u-d-r' and payload['mission_names']==['1-40TH RECON'],payload

        # Cancel restores the exact geometry that was current when the new edit session started.
        page.click('.tak-shape-edit-toggle-i639'); page.wait_for_timeout(60)
        baseline=page.evaluate('window.__baseLayer.getLatLngs()')
        page.evaluate("""() => {const h=window.__i640Markers.find(m=>m.options&&m.options.draggable===true);h.setLatLng([34.220,-118.770]).fire('drag')}""")
        page.click('[data-i640-shape-cancel]'); page.wait_for_timeout(100)
        cancelled=page.evaluate('window.__baseLayer.getLatLngs()')
        assert cancelled==baseline,(baseline,cancelled)
        assert not errors,errors
        context.close(); browser.close()
    print('TAK Map i640 authoritative Shape edit browser regression passed')
    return 0
if __name__=='__main__': raise SystemExit(main())
