#!/usr/bin/env python3
"""Browser contract for TAK Map i639 in-place native Shape editing."""
from __future__ import annotations
from pathlib import Path
import shutil, urllib.parse

ROOT=Path(__file__).resolve().parents[1]
CONTEXT=(ROOT/'assets'/'tak-map-context-sidebar-i572.js').read_text()
PACKAGE=(ROOT/'assets'/'tak-map-package-i580.js').read_text()
ORIGIN='http://127.0.0.1'
FIXTURE=f"""<!doctype html><html><head><meta charset='utf-8'><base href='{ORIGIN}/'><style>
html,body{{margin:0;width:100%;height:100%;overflow:hidden;background:#071117;color:#e9f0f5;font-family:Arial,sans-serif}}#map{{position:relative;width:100%;height:100%}}
</style></head><body><aside class='version-panel'><div class='version-product'>TAK Map</div><span class='release-main'>1.4.0</span><span class='iteration-chip'>i638</span></aside><div id='map'></div>
<script>
window.ResizeObserver=class{{constructor(cb){{this.cb=cb}}observe(){{}}disconnect(){{}}}};
(function(){{
 const handlers={{}}; const mapEl=document.getElementById('map'); window.__i639Markers=[];
 window.map={{_scale:26000,on(names,cb){{String(names).split(/\\s+/).forEach(n=>(handlers[n]||(handlers[n]=[])).push(cb));return this}},fire(name,event={{}}){{(handlers[name]||[]).forEach(cb=>cb(event));}},getContainer(){{return mapEl}},getBounds(){{return {{contains(){{return true}}}}}},getZoom(){{return 14}},panTo(){{}},setView(){{}},removeLayer(layer){{try{{layer.remove()}}catch(_){{}}}},latLngToContainerPoint(ll){{const lat=Array.isArray(ll)?Number(ll[0]):Number(ll.lat),lon=Array.isArray(ll)?Number(ll[1]):Number(ll.lng??ll.lon);return {{x:640+(lon+118.72761)*this._scale,y:380-(lat-34.2060116)*this._scale}};}}}};
 function latlng(v){{return Array.isArray(v)?{{lat:Number(v[0]),lng:Number(v[1])}}:{{lat:Number(v.lat),lng:Number(v.lng??v.lon)}}}}
 window.L={{DomEvent:{{disableClickPropagation(){{}},disableScrollPropagation(){{}},stop(){{}}}},divIcon(opts){{return opts||{{}}}},marker(ll,opts={{}}){{let pos=latlng(ll),node=null,evs={{}};const marker={{options:opts,addTo(m){{if(opts.icon&&opts.icon.html){{node=document.createElement('div');node.className=opts.icon.className||'';node.innerHTML=opts.icon.html;mapEl.appendChild(node)}}return this}},on(name,cb){{evs[name]=cb;return this}},getLatLng(){{return {{lat:pos.lat,lng:pos.lng}}}},setLatLng(v){{pos=latlng(v);return this}},remove(){{if(node&&node.remove)node.remove();node=null;return this}},fire(name,p={{}}){{if(evs[name])evs[name]({{target:this,...p}});return this}}}};window.__i639Markers.push(marker);return marker;}}}};
}})();
window.layerPopupForObject=(o)=>`<div class="tak-v322-popup" data-kind="Shape" data-source="Local Data"><div class="tak-v322-bar"></div><div class="tak-v322-inner"><div class="tak-v322-title">${{o.name}}</div><div class="tak-v322-sub">Shape · Local Data</div><div class="tak-v322-table"><div class="tak-v322-row"><b>Category</b><span>shape</span></div><div class="tak-v322-row"><b>Lat/Lon</b><span>${{o.lat}}, ${{o.lon}}</span></div><div class="tak-v322-row"><b>Points</b><span>${{o.coords.length}}</span></div><div class="tak-v322-row"><b>Width</b><span>old width</span></div><div class="tak-v322-row"><b>Height</b><span>old height</span></div><div class="tak-v322-row"><b>Notes</b><span>${{o.notes||''}}</span></div><div class="tak-v322-row"><b>Added</b><span>9/2/2026, 07:06</span></div></div><details class="popup-edit tak-v322-edit" data-key="datasync:${{o.uid}}" data-source="datasync"><summary>Edit</summary><div class="tak-v322-edit-fields"><label>Name<input name="name" value="${{o.name}}"></label><label>Category<input name="category" value="shape"></label><label>Lat/Lon<input name="latlon" value="${{o.lat}}, ${{o.lon}}"><input type="hidden" name="lat" value="${{o.lat}}"><input type="hidden" name="lon" value="${{o.lon}}"></label><label>Notes<textarea name="notes">${{o.notes||''}}</textarea></label></div><div class="tak-v322-actions"><button type="button" data-v322-popup-action="save" data-popup-key="datasync:${{o.uid}}" data-popup-source="datasync">Save</button><button type="button" data-v322-popup-action="cancel">Cancel</button><button type="button" class="danger" data-v322-popup-action="delete">Delete</button></div><div class="popup-edit-status"></div></details></div></div>`;
window.dataSyncCategory=(o)=>/u-d-r/.test(o.type||'')?'Shapes / Areas':'Point Markers';
window.lastDataSync={{objects:[]}};
</script>
<script src='/assets/runtime/tak-map-context-sidebar-i572.js?v=1.4.0-i639'></script>
<script src='/assets/runtime/tak-map-package-i580.js?v=1.4.0-i639'></script>
</body></html>"""

OBJ={
    'uid':'rect-i639','name':'Rectangle 3','notes':'test note','type':'u-d-r','cot_type':'u-d-r','kind':'shape','geometry':'shape',
    'is_mission_object':True,'mission_memberships':['1-40TH RECON'],'mission_name':'1-40TH RECON',
    'lat':34.2060116,'lon':-118.72761,'shape_kind_i636':'rectangle','shape_closed_i636':True,
    'delete_supported':True,
    'coords':[[34.21028794604995,-118.75832320362926],[34.18305784557117,-118.71324111471124],[34.201731109450755,-118.69689581442177],[34.22896713330185,-118.74198259098516]],
}

def main()->int:
    chromium=next((n for n in ('chromium','chromium-browser','google-chrome','google-chrome-stable') if shutil.which(n)),None)
    if not chromium: raise SystemExit('Chromium is required')
    from playwright.sync_api import sync_playwright
    errors=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=shutil.which(chromium),args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
        context=browser.new_context(locale='en-US',viewport={'width':1280,'height':760})
        page=context.new_page(); page.on('pageerror',lambda exc:errors.append(str(exc)))
        def route(route):
            path=urllib.parse.urlsplit(route.request.url).path
            if path.endswith('tak-map-context-sidebar-i572.js'): route.fulfill(status=200,content_type='application/javascript',body=CONTEXT)
            elif path.endswith('tak-map-package-i580.js'): route.fulfill(status=200,content_type='application/javascript',body=PACKAGE)
            else: route.fulfill(status=404,body='not found')
        page.route('**/*',route)
        page.set_content(FIXTURE,wait_until='domcontentloaded',timeout=20000)
        page.wait_for_function('window.TakMapContextSidebarI572 && window.TakMapContextPanelSizingI620')
        page.evaluate('(o)=>{window.lastDataSync={objects:[o]};TakMapContextSidebarI572.showObject(o,"datasync",null,false)}',OBJ)
        page.wait_for_timeout(200)
        normal=page.evaluate("""() => {
          const p=document.getElementById('takMapContextSidebarI572'),b=document.getElementById('takMapContextSidebarBodyI572');
          const rows=Object.fromEntries([...b.querySelectorAll('.tak-v322-row')].map(r=>[(r.querySelector('b')?.textContent||'').trim(),(r.querySelector('span')?.textContent||'').trim()]));
          return {rows,headTitle:document.getElementById('takMapContextTitleI572')?.textContent||'',headHidden:document.getElementById('takMapContextTitleI572')?.hidden,bodyTitle:b.querySelector('.tak-v322-title')?.textContent||'',source:b.querySelector('.tak-v322-sub')?.textContent||'',edit:b.querySelector('.tak-shape-edit-toggle-i639')?.textContent||'',deleteBg:getComputedStyle(b.querySelector('.tak-context-delete-button-i572')).backgroundImage,panelWidth:p.getBoundingClientRect().width};
        }""")
        assert normal['headHidden'] and normal['headTitle']=='' and normal['bodyTitle']=='Rectangle 3',normal
        assert normal['rows'].get('Center') and normal['rows'].get('Category')=='shape',normal
        assert 'Width' not in normal['rows'] and 'Height' not in normal['rows'],normal
        for k in ('Area','Perimeter','Rotation'): assert k in normal['rows'],normal
        assert 'Data Sync · 1-40TH RECON' in normal['source'] and normal['edit']=='Edit',normal
        assert 316<=normal['panelWidth']<=321,normal
        # The explicit delete action is gray, not the older red warning fill.
        assert 'rgb(78, 91, 101)' in normal['deleteBg'] or 'rgb(43, 53, 61)' in normal['deleteBg'],normal['deleteBg']

        page.click('.tak-shape-edit-toggle-i639'); page.wait_for_timeout(100)
        edit=page.evaluate("""() => {
          const b=document.getElementById('takMapContextSidebarBodyI572'),d=TakMapContextSidebarI572.diagnostics();
          const title=b.querySelector('.tak-v322-title'),center=[...b.querySelectorAll('.tak-v322-row')].find(r=>(r.querySelector('b')?.textContent||'').trim()==='Center');
          const cat=[...b.querySelectorAll('.tak-v322-row')].find(r=>(r.querySelector('b')?.textContent||'').trim()==='Category');
          const details=b.querySelector('details.popup-edit'),actions=[...details.querySelectorAll('.tak-v322-actions button')].filter(x=>getComputedStyle(x).display!=='none');
          return {diag:d,kicker:document.getElementById('takMapContextKickerI572')?.textContent||'',nameInput:!!title.querySelector('input[name=name]'),centerInput:!!center?.querySelector('input[name=latlon]'),categoryText:cat?.querySelector('span')?.textContent||'',visibleFieldBlock:getComputedStyle(details.querySelector('.tak-v322-edit-fields')).display,visibleActions:actions.map(x=>x.textContent.trim()),buttonBackgrounds:actions.map(x=>getComputedStyle(x).backgroundImage),toggle:b.querySelector('.tak-shape-edit-toggle-i639')?.textContent||'',vectorNodes:document.querySelectorAll('.tak-shape-vector-i639').length,distanceNodes:document.querySelectorAll('.tak-shape-distance-i639').length};
        }""")
        assert edit['kicker']=='Edit Shape' and edit['nameInput'] and edit['centerInput'],edit
        assert edit['categoryText']=='shape' and edit['visibleFieldBlock']=='none',edit
        assert edit['visibleActions']==['Save','Cancel'],edit
        assert edit['toggle']=='Close Edit',edit
        assert edit['diag']['shapeEditActiveI639'] and edit['diag']['shapeEditHandleCountI639']==4,edit
        assert edit['vectorNodes']==4 and edit['diag']['shapeEditLabelCountI639']>0 and edit['distanceNodes']>0,edit
        # Dragging a rectangle corner updates native geometry and live computed measurements.
        drag=page.evaluate("""() => {
          const b=document.getElementById('takMapContextSidebarBodyI572');
          const area=()=>[...b.querySelectorAll('.tak-v322-row')].find(r=>(r.querySelector('b')?.textContent||'').trim()==='Area')?.querySelector('span')?.textContent||'';
          const before=area(),beforePoint=window.lastDataSync.objects[0].coords[0].slice();
          const handle=window.__i639Markers.find(m=>m.options&&m.options.draggable===true);
          handle.setLatLng([34.216,-118.766]).fire('drag');
          return {before,after:area(),beforePoint,afterPoint:window.lastDataSync.objects[0].coords[0].slice(),diag:TakMapContextSidebarI572.diagnostics()};
        }""")
        assert drag['beforePoint']!=drag['afterPoint'] and drag['before']!=drag['after'],drag
        assert drag['diag']['shapeEditHandleCountI639']==4 and drag['diag']['shapeEditLabelCountI639']>0,drag
        # Save and Cancel are both themed gray/silver gradients (no red/orange action fill).
        assert all(('rgb(224, 229, 232)' in bg or 'rgb(77, 90, 100)' in bg) for bg in edit['buttonBackgrounds']),edit['buttonBackgrounds']

        # Zoom/space rule: the exact same shape drops segment labels when too small on screen.
        page.evaluate('map._scale=300; map.fire("zoomend")'); page.wait_for_timeout(50)
        zoomed=page.evaluate('TakMapContextSidebarI572.diagnostics()')
        assert zoomed['shapeEditHandleCountI639']==4 and zoomed['shapeEditLabelCountI639']==0,zoomed
        page.evaluate('map._scale=26000; map.fire("zoomend")'); page.wait_for_timeout(50)
        zoomed_in=page.evaluate('TakMapContextSidebarI572.diagnostics()')
        assert zoomed_in['shapeEditLabelCountI639']>0,zoomed_in

        # Close Edit restores normal panel rather than leaving a second appended form.
        page.click('.tak-shape-edit-toggle-i639'); page.wait_for_timeout(80)
        closed=page.evaluate("""() => {const b=document.getElementById('takMapContextSidebarBodyI572'),d=TakMapContextSidebarI572.diagnostics();return {active:d.shapeEditActiveI639,handles:d.shapeEditHandleCountI639,labels:d.shapeEditLabelCountI639,title:b.querySelector('.tak-v322-title')?.textContent||'',nameInputs:b.querySelectorAll('.tak-v322-title input[name=name]').length,centerLabel:[...b.querySelectorAll('.tak-v322-row b')].some(x=>x.textContent.trim()==='Center')};}""")
        assert closed=={'active':False,'handles':0,'labels':0,'title':'Rectangle 3','nameInputs':0,'centerLabel':True},closed
        assert not errors,errors
        context.close()

        # Same geometry remains metric for metric regional settings.
        metric_context=browser.new_context(locale='de-DE',viewport={'width':1280,'height':760})
        metric=metric_context.new_page(); metric_errors=[]; metric.on('pageerror',lambda exc:metric_errors.append(str(exc)))
        metric.route('**/*',route); metric.set_content(FIXTURE,wait_until='domcontentloaded',timeout=20000)
        metric.wait_for_function('window.TakMapContextSidebarI572 && window.TakMapContextPanelSizingI620')
        metric.evaluate('(o)=>{window.lastDataSync={objects:[o]};TakMapContextSidebarI572.showObject(o,"datasync",null,false)}',OBJ); metric.wait_for_timeout(120)
        metric_area=metric.evaluate("() => [...document.querySelectorAll('.tak-v322-row')].find(r=>(r.querySelector('b')?.textContent||'').trim()==='Area')?.querySelector('span')?.textContent||''")
        assert 'm²' in metric_area and 'sq ft' not in metric_area,metric_area
        metric.click('.tak-shape-edit-toggle-i639'); metric.wait_for_timeout(80)
        metric_labels=metric.evaluate("() => [...document.querySelectorAll('.tak-shape-distance-i639')].map(x=>x.textContent)")
        assert metric_labels and all((' m' in x or ' km' in x) and 'ft' not in x and 'mi' not in x for x in metric_labels),metric_labels
        assert not metric_errors,metric_errors
        metric_context.close(); browser.close()
    print('TAK Map i639 in-place Shape context browser test passed')
    return 0
if __name__=='__main__': raise SystemExit(main())
