#!/usr/bin/env python3
from __future__ import annotations
import json, os, shutil, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LIFECYCLE=(ROOT/'assets'/'tak-map-object-lifecycle-v491.js').read_text()
GEOFENCE=(ROOT/'assets'/'tak-map-geofencing-v491.js').read_text()

HTML='''<!doctype html><html><head><meta charset="utf-8"><style>.leaflet-popup details.popup-edit>summary{display:inline-flex!important;width:auto!important}.tak-v322-popup{width:360px}.tak-v322-inner{padding:14px 15px 13px}.tak-v322-table{display:table;width:100%}.tak-v322-row{display:table-row}.tak-v322-row b,.tak-v322-row span{display:table-cell;padding:7px 0}</style></head><body>
<div id="sidebar"><div class="panel"><h2>Basemap</h2></div><div class="panel"><h2>ADS-B</h2></div></div>
<div id="map"></div><div id="localDataRows"></div><div id="dataSyncRows"></div>
<div id="selectionReviewPanel"><button id="selectionDeleteBtn">Delete</button><div id="selectionDeleteNote"></div></div>
</body></html>'''

STUB=r'''(()=>{
let nextId=1;
class Evented{
 constructor(){this._events={}}
 on(names,fn,ctx){for(const name of String(names).split(/\s+/)){if(!name)continue;(this._events[name]||(this._events[name]=[])).push({fn,ctx})}return this}
 off(name,fn,ctx){if(!name){this._events={};return this}const list=this._events[name]||[];this._events[name]=fn?list.filter(x=>x.fn!==fn||(ctx&&x.ctx!==ctx)):[];return this}
 fire(name,data={}){data.target=data.target||this;for(const x of (this._events[name]||[]).slice())x.fn.call(x.ctx||this,data);return this}
}
function ll(a,b){if(Array.isArray(a))return {lat:Number(a[0]),lng:Number(a[1])};if(a&&typeof a==='object')return {lat:Number(a.lat),lng:Number(a.lng??a.lon)};return {lat:Number(a),lng:Number(b)}}
function flatten(v,out=[]){if(Array.isArray(v)&&v.length&&typeof v[0]==='number'){out.push(ll(v));return out}if(Array.isArray(v))for(const x of v)flatten(x,out);return out}
class Popup{
 constructor(content,options,source){this._content=content;this.options=Object.assign({},options);this._source=source;this._open=false;this._root=null}
 getContent(){return this._content} setContent(v){this._content=v;if(this._root){const c=this._root.querySelector('.leaflet-popup-content');if(c)c.innerHTML=String(v||'')}return this} setLatLng(v){this._latlng=v;return this}
 getElement(){return this._root} isOpen(){return this._open}
 remove(){if(this._source)this._source.closePopup();return this}
}
class Layer extends Evented{
 constructor(kind,coords,options={}){super();this._leaflet_id=nextId++;this.kind=kind;this.coords=coords;this.options=Object.assign({},options);this._popup=null;this._group=null;this._element=document.createElement('div');this._element.dataset.layer=String(this._leaflet_id);document.getElementById('map').appendChild(this._element)}
 addTo(group){this._group=group;group.addLayer(this);return this} remove(){if(this._group)this._group.removeLayer(this);this.closePopup();return this}
 bindPopup(content,options={}){this._popup=content instanceof Popup?content:new Popup(content,options,this);this._popup._source=this;if(!this._openPopup){this._openPopup=(ev)=>{this.openPopup(ev&&ev.latlng)};this.on('click',this._openPopup,this)}return this}
 unbindPopup(){if(this._openPopup)this.off('click',this._openPopup,this);this._popup=null;return this}
 getPopup(){return this._popup} setPopupContent(v){if(this._popup)this._popup.setContent(v);return this}
 openPopup(at){if(!this._popup)return this;if(map._popup&&map._popup!==this._popup){const old=map._popup,src=old._source;if(src)src.closePopup()}
  const p=this._popup,already=!!(p._open&&map._popup===p);p._source=this;p._open=true;p._latlng=at||p._latlng;if(!p._root){const root=document.createElement('div');root.className='leaflet-popup';root.innerHTML='<div class="leaflet-popup-content">'+String(p.getContent()||'')+'</div>';document.body.appendChild(root);p._root=root}
  map._popup=p;if(!already){this.fire('popupopen',{popup:p});map.fire('popupopen',{popup:p})}return this}
 closePopup(){const p=this._popup;if(!p||!p._open)return this;p._open=false;if(p._root){p._root.remove();p._root=null}if(map._popup===p)map._popup=null;this.fire('popupclose',{popup:p});map.fire('popupclose',{popup:p});return this}
 isPopupOpen(){return !!(this._popup&&this._popup._open)} getElement(){return this._element}
 getLatLng(){const pts=flatten(this.coords);return pts[0]||ll(34,-118)} getLatLngs(){return this.coords}
 getBounds(){const pts=flatten(this.coords);return {getCenter(){if(!pts.length)return {lat:0,lng:0};const lats=pts.map(p=>p.lat),lngs=pts.map(p=>p.lng);return {lat:(Math.min(...lats)+Math.max(...lats))/2,lng:(Math.min(...lngs)+Math.max(...lngs))/2}},isValid(){return !!pts.length}}}
}
class Group extends Evented{constructor(){super();this.layers=[]}addLayer(x){if(!this.layers.includes(x))this.layers.push(x);return this}removeLayer(x){this.layers=this.layers.filter(v=>v!==x);x.closePopup();return this}clearLayers(){for(const x of this.layers.slice())this.removeLayer(x);return this}eachLayer(fn){this.layers.slice().forEach(fn)}hasLayer(x){return this.layers.includes(x)}}
class MapX extends Group{constructor(){super();this._popup=null}getContainer(){return document.getElementById('map')}hasLayer(x){return this.layers.includes(x)}removeLayer(x){super.removeLayer(x);return this}setView(){return this}fitBounds(){return this}getZoom(){return 12}eachLayer(fn){super.eachLayer(fn)}}
window.map=new MapX();window.takLeafletMap=map;
window.L={polyline:(c,o)=>new Layer('route',c,o),polygon:(c,o)=>new Layer('shape',c,o),marker:(c,o)=>new Layer('point',c,o),latLng:ll,latLngBounds(c){const pts=flatten(c);return {getCenter(){if(!pts.length)return {lat:0,lng:0};const lats=pts.map(p=>p.lat),lngs=pts.map(p=>p.lng);return {lat:(Math.min(...lats)+Math.max(...lats))/2,lng:(Math.min(...lngs)+Math.max(...lngs))/2}},isValid(){return !!pts.length}}},DomEvent:{stopPropagation(e){if(e)e._stopped=true},preventDefault(e){if(e)e.defaultPrevented=true},stop(e){if(e){e._stopped=true;e.defaultPrevented=true}}}};
window.importedLayer=new Group();window.dataSyncLayer=new Group();map.addLayer(importedLayer);map.addLayer(dataSyncLayer);
window.state={dataSync:true,imported:true,local:{routes:{},points:{},shapes:{},hidden:{}},live:{adsb_aircraft:true}};window.lastImports=[];window.lastDataSync={missions:[],packages:[],objects:[]};window.lastTakMarkers=[];window.lastAircraft=[];
window.fetch=async(url,init={})=>{const u=String(url);if(u.includes('/api/tak-map/geofences'))return new Response(JSON.stringify({ok:true,fences:[]}),{status:200,headers:{'Content-Type':'application/json'}});return new Response(JSON.stringify({ok:true}),{status:200,headers:{'Content-Type':'application/json'}})};
window.AudioContext=class{constructor(){this.state='running';this.currentTime=0;this.destination={}}resume(){}createOscillator(){return {type:'sine',frequency:{value:0},connect(){return this},start(){},stop(){}}}createGain(){return {gain:{setValueAtTime(){},exponentialRampToValueAtTime(){}},connect(){return this}}}};
window.esc=x=>String(x);window.formatCoords=(a,b)=>a+','+b;window.assetDescriptor=o=>o&&o.kind==='route'?'Route':'Shape';window.popupNotes=o=>String(o&&o.notes||'');window.popupEditToggle=()=>{};window.markPopupEditDirty=()=>{};window.popupEditKeyNav=()=>{};window.savePopupEdit=async btn=>{const box=btn.closest('.popup-edit');const get=n=>(box.querySelector('[name="'+n+'"]')||{}).value||'';window.__inlineSave={key:box.dataset.key,source:box.dataset.source,name:get('name'),type:get('type'),asset:get('asset'),category:get('category'),color:get('color'),lat:get('lat'),lon:get('lon'),notes:get('notes')};return {ok:true}};window.cancelPopupEdit=()=>{};window.popupEditForm=o=>'<details class="popup-edit" data-key="local:'+o.object_id+'" data-object-id="local:'+o.object_id+'" data-source="local" onclick="event.stopPropagation()"><summary>Edit Data</summary><label>Name<input name="name" value="'+o.name+'"></label><label>Type<input name="type" value="'+o.kind+'"></label><label>Asset<input name="asset" value="'+(o.kind==='route'?'Route':'Shape')+'"></label><div class="popup-edit-grid"><label>Lat<input name="lat" value="34.005000"></label><label>Lon<input name="lon" value="-117.995000"></label></div><label>Notes<textarea name="notes">'+(o.notes||'')+'</textarea></label><div class="popup-edit-actions"><button type="button">Save</button><button type="button">Cancel</button><button type="button">Delete</button></div></details>';
window.dataSyncCategory=o=>o.kind==='route'?'Routes':o.kind==='shape'?'Shapes / Areas':'Point Markers';window.objectCenter=o=>{const pts=flatten(o.coords||[]);return pts.length?[pts.reduce((a,p)=>a+p.lat,0)/pts.length,pts.reduce((a,p)=>a+p.lng,0)/pts.length]:null};window.routeCoords=o=>o.coords;window.shapeCoords=o=>o.coords;
window.layerPopupForObject=(o,cat)=>{const row=(k,v)=>'<div class="tak-v322-row"><b>'+k+'</b><span>'+v+'</span></div>';const rows=row('Category',cat)+row('Lat/Lon','34.005000, -117.995000')+row('Points',o.kind==='shape'?'5':'3')+row(o.kind==='route'?'Distance':'Area',o.kind==='route'?'1.2 mi':'1,234 sq ft')+row('Added','2026-07-20')+row('Notes',o.notes||'');return '<div class="tak-v322-popup" data-kind="'+(o.kind==='route'?'Route':'Shape')+'" data-source="'+cat+'"><div class="tak-v322-bar"></div><div class="tak-v322-inner"><div class="tak-v322-title">'+o.name+'</div><div class="tak-v322-sub">'+(o.kind==='route'?'Route':'Shape')+' · '+cat+'</div><div class="tak-v322-table">'+rows+'</div>'+popupEditForm(o,cat)+'<button class="layer-button legacy-popup-edit">EDIT</button></div></div>'};
window.addSearchItem=()=>{};window.takMapStampSelectionIdentityV478=()=>{};
window.stabilizeLayerPopup=layer=>{if(!layer||layer.__baseStable)return layer;layer.__baseStable=true;let anchor=null;const open=ev=>{anchor=anchor||(layer.getBounds?layer.getBounds().getCenter():layer.getLatLng());layer.openPopup(ev&&ev.latlng||anchor)};layer.on('mouseover',()=>open());layer.on('mouseout',()=>setTimeout(()=>{if(!layer._takPopupPinned&&!layer._takPopupHover)layer.closePopup()},120));layer.on('click',ev=>{layer._takPopupPinned=true;window._takPinnedPopupLayer=layer;open(ev);if(ev&&ev.originalEvent)L.DomEvent.stop(ev.originalEvent)});layer.on('popupopen',ev=>{const root=ev.popup.getElement();if(root){root.addEventListener('mouseenter',()=>layer._takPopupHover=true);root.addEventListener('mouseleave',()=>layer._takPopupHover=false)}});return layer};
window.addObjectLayer=(group,o,sourceKey)=>{const cat=dataSyncCategory(o);let layer=null;if(cat==='Routes'){const popup=layerPopupForObject(o,cat);layer=L.polyline(o.coords,{interactive:true,bubblingMouseEvents:false}).bindPopup(popup,{autoClose:false,closeOnClick:false}).addTo(group);const hit=L.polyline(o.coords,{interactive:true,bubblingMouseEvents:false,weight:16,opacity:0}).bindPopup(popup,{autoClose:false,closeOnClick:false}).addTo(group);stabilizeLayerPopup(hit);o.__hitLayer=hit}else if(cat==='Shapes / Areas'){layer=L.polygon(o.coords,{interactive:true,bubblingMouseEvents:false}).bindPopup(layerPopupForObject(o,cat),{autoClose:false,closeOnClick:false}).addTo(group)};if(layer){stabilizeLayerPopup(layer);o.__layer=layer}return layer};
window.importedFeatures=()=>[];window.drawImportedObjects=()=>{};window.drawDataSyncObjects=()=>{};window.renderLocalDataRows=()=>{};window.renderDataSyncRows=()=>{};window.localDataSets=()=>({routes:[],points:[],shapes:[]});window.renderLocalActions=()=>'';window.renderLocalSection=()=>'';window.localDataAction=()=>{};window.deleteDataSyncItem=()=>{};window.deletePopupEdit=()=>{};window.popupEditKey=()=>'';window.terrain3DDataHash=()=>'';window.refreshTerrain3DObjects=()=>{};
window.__takSelectionStateV477={selected:[],selectedIds:new Set()};window.TakMapSelectionV478={refreshReview(){}};window.TakMapSelectionV477=window.TakMapSelectionV478;
window.clearPinnedPopup=()=>{const lyr=window._takPinnedPopupLayer;if(lyr){lyr._takPopupPinned=false;lyr.closePopup()}window._takPinnedPopupLayer=null};map.on('click',()=>clearPinnedPopup());
})();'''

def main():
    chromium=next((x for x in ('chromium','chromium-browser','google-chrome','google-chrome-stable') if shutil.which(x)),None)
    if not chromium:
        print('SKIP: Chromium unavailable');return 0
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b=pw.chromium.launch(headless=True,executable_path=shutil.which(chromium),args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
        p=b.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)));p.set_content(HTML,wait_until='domcontentloaded');p.add_script_tag(content=STUB);p.add_script_tag(content=LIFECYCLE);p.add_script_tag(content=GEOFENCE)
        p.wait_for_function("window.TakMapObjectLifecycleV486 && window.TakMapGeofencingV491 && document.getElementById('geofencePanelV491')",timeout=8000);p.wait_for_timeout(600)
        setup=p.evaluate("""()=>{
          const shape={name:'Shape Alpha',notes:'Shape note',kind:'shape',coords:[[34,-118],[34,-117.99],[34.01,-117.99],[34.01,-118],[34,-118]],object_id:'local-shape-alpha',local_id:'local-shape-alpha',_local_id:'local-shape-alpha',source_id:'local-shape-alpha',source_kind:'local',canonical_id:'local:local-shape-alpha'};
          const route={name:'Route Bravo',notes:'Route note',category:'Evacuation',color:'#3366cc',created_at:'2026-07-20T12:30:00Z',kind:'route',lat:34.025,lon:-117.99,coords:[[34.02,-118],[34.025,-117.99],[34.03,-117.98]],object_id:'local-route-bravo',local_id:'local-route-bravo',_local_id:'local-route-bravo',source_id:'local-route-bravo',source_kind:'local',canonical_id:'local:local-route-bravo'};
          addObjectLayer(importedLayer,shape,'imported');addObjectLayer(importedLayer,route,'imported');TakMapObjectLifecycleV486.syncCanonicalPopups();window.__popupObjects={shape,route};
          return {shapePopup:!!shape.__layer.getPopup(),routePopup:!!route.__layer.getPopup(),hitPopup:!!route.__hitLayer.getPopup(),independent:route.__layer.getPopup()!==route.__hitLayer.getPopup(),shapeOwner:!!shape.__layer.__takCanonicalPopupOwnerV492,routeOwner:!!route.__hitLayer.__takCanonicalPopupOwnerV492,shapeMouseover:(shape.__layer._events.mouseover||[]).length,shapeMouseout:(shape.__layer._events.mouseout||[]).length,shapeClick:(shape.__layer._events.click||[]).length,legacyRetired:!!shape.__layer.__takLegacyPopupInteractionRetiredV494};
        }""")
        assert setup=={'shapePopup':True,'routePopup':True,'hitPopup':True,'independent':True,'shapeOwner':True,'routeOwner':True,'shapeMouseover':1,'shapeMouseout':1,'shapeClick':1,'legacyRetired':True},setup

        # Hover shape, enter popup, and verify it remains open; leave and verify temporary close.
        p.evaluate("()=>window.__popupObjects.shape.__layer.fire('mouseover',{latlng:L.latLng(34.001,-117.999)})");p.wait_for_timeout(80)
        hover=p.evaluate("""()=>{const row=document.querySelector('.tak-popup-primary-actions-v492');const buttons=row?Array.from(row.querySelectorAll('button')).map(b=>b.textContent.trim()):[];const rects=row?Array.from(row.querySelectorAll('button')).map(b=>b.getBoundingClientRect().top):[];const visibleEdits=Array.from(document.querySelectorAll('.leaflet-popup button,.leaflet-popup summary')).filter(el=>/^(edit|edit data)$/i.test((el.textContent||'').trim())&&getComputedStyle(el).display!=='none');const a=__popupObjects.shape.__layer.getPopup()._latlng||{};const actions=document.querySelector('.tak-popup-primary-actions-v492'),inner=document.querySelector('.tak-v322-inner'),ar=actions.getBoundingClientRect(),ir=inner.getBoundingClientRect();return {open:__popupObjects.shape.__layer.isPopupOpen(),button:document.querySelectorAll('.tak-geofence-popup-btn-v491').length,row:document.querySelectorAll('.tak-popup-primary-actions-v492').length,buttons,separate:document.querySelectorAll('.tak-geofence-popup-actions-v491:not(.tak-popup-primary-actions-v492)').length,summaryRemoved:document.querySelector('.popup-edit>summary')===null,sameRow:rects.length===2&&Math.abs(rects[0]-rects[1])<1,insidePaddedBody:actions.parentElement===inner,leftSpace:Math.round(ar.left-ir.left),rightSpace:Math.round(ir.right-ar.right),bottomSpace:Math.round(ir.bottom-ar.bottom),visibleEdits:visibleEdits.length,anchor:[Number(a.lat.toFixed(3)),Number(a.lng.toFixed(3))]}}""")
        assert hover=={'open':True,'button':1,'row':1,'buttons':['Edit','Geofence'],'separate':0,'summaryRemoved':True,'sameRow':True,'insidePaddedBody':True,'leftSpace':15,'rightSpace':15,'bottomSpace':13,'visibleEdits':1,'anchor':[34.005,-117.995]},hover
        stored=p.evaluate("""()=>{const pop=__popupObjects.shape.__layer.getPopup(),html=String(pop.getContent()||'');const t=document.createElement('template');t.innerHTML=html;return {canonical:pop.__takCanonicalStoredContentV498===true,rows:t.content.querySelectorAll('.tak-popup-primary-actions-v492').length,buttons:Array.from(t.content.querySelectorAll('.tak-popup-primary-actions-v492 button')).map(b=>b.textContent.trim()),legacy:t.content.querySelectorAll('.legacy-popup-edit:not(.tak-popup-edit-toggle-v492)').length,details:t.content.querySelectorAll('details.popup-edit').length,legacyFields:t.content.querySelectorAll('details.popup-edit input,details.popup-edit textarea').length}}""")
        assert stored=={'canonical':True,'rows':1,'buttons':['Edit','Geofence'],'legacy':0,'details':0,'legacyFields':0},stored
        # Repeat hover and click while already open. Real Leaflet emits no
        # second popupopen in this state; stored content must remain canonical.
        p.evaluate("""()=>{const l=__popupObjects.shape.__layer;l.__popupOpenCount=0;l.on('popupopen',()=>l.__popupOpenCount++);l.fire('mouseover',{latlng:L.latLng(34.002,-117.998)});const oe={};l.fire('click',{latlng:L.latLng(34.002,-117.998),originalEvent:oe})}""")
        p.wait_for_timeout(80)
        repeat=p.evaluate("""()=>{const l=__popupObjects.shape.__layer,pop=l.getPopup(),html=String(pop.getContent()||''),t=document.createElement('template');t.innerHTML=html;return {popupopen:l.__popupOpenCount,open:l.isPopupOpen(),stored:pop.__takCanonicalStoredContentV498===true,buttons:Array.from(t.content.querySelectorAll('.tak-popup-primary-actions-v492 button')).map(b=>b.textContent.trim()),rendered:Array.from(document.querySelectorAll('.tak-popup-primary-actions-v492 button')).map(b=>b.textContent.trim()),legacy:t.content.querySelectorAll('.legacy-popup-edit:not(.tak-popup-edit-toggle-v492)').length}}""")
        assert repeat=={'popupopen':0,'open':True,'stored':True,'buttons':['Edit','Geofence'],'rendered':['Edit','Geofence'],'legacy':0},repeat
        p.evaluate("""()=>{const l=__popupObjects.shape.__layer,e=TakMapObjectLifecycleV486.entryForLayer(l);l._takPopupPinned=false;l.__v462PopupPinned=false;l.__v461PopupPinned=false;l.__v353PopupPinned=false;if(e&&e.popupState)e.popupState.pinnedLayer=null;window.__takCanonicalPinnedEntryV492=null;window._takPinnedPopupLayer=null}""")
        p.locator('.tak-popup-edit-toggle-v492').click()
        inline=p.evaluate("""()=>{const f=document.querySelector('.tak-v322-popup'),row=f.querySelector('.tak-popup-primary-actions-v492');return {editing:!!f.querySelector('.tak-v322-inner.tak-popup-inline-editing-v497'),details:document.querySelectorAll('details.popup-edit').length,legacyFields:document.querySelectorAll('details.popup-edit input,details.popup-edit textarea').length,actions:Array.from(row.querySelectorAll('button')).map(b=>b.textContent.trim()),name:f.querySelector('[name="name"]')?.value||'',categoryReadonly:!!f.querySelector('.tak-popup-inline-value-v497.readonly input[readonly]'),notes:f.querySelector('[name="notes"]')?.value||''}}""")
        assert inline=={'editing':True,'details':0,'legacyFields':0,'actions':['Save','Cancel','Delete'],'name':'Shape Alpha','categoryReadonly':True,'notes':'Shape note'},inline
        p.locator('[name="name"]').fill('Changed but canceled');p.locator('[data-tak-inline-action="cancel"]').click();p.wait_for_timeout(40)
        canceled=p.evaluate("""()=>({editing:!!document.querySelector('.tak-popup-inline-editing-v497'),details:document.querySelectorAll('details.popup-edit').length,actions:Array.from(document.querySelectorAll('.tak-popup-primary-actions-v492 button')).map(b=>b.textContent.trim()),name:document.querySelector('.tak-v322-title')?.textContent.trim()||''})""")
        assert canceled=={'editing':False,'details':0,'actions':['Edit','Geofence'],'name':'Shape Alpha'},canceled
        p.locator('.tak-popup-edit-toggle-v492').click();p.locator('[name="name"]').fill('Shape Alpha Edited');p.locator('[data-tak-inline-action="save"]').click();p.wait_for_timeout(40)
        saved=p.evaluate("()=>window.__inlineSave")
        assert saved=={'key':'local:local-shape-alpha','source':'local','name':'Shape Alpha Edited','type':'','asset':'Shape','category':'','color':'','lat':'34.005000','lon':'-117.995000','notes':'Shape note'},saved
        p.locator('[data-tak-inline-action="cancel"]').click();p.wait_for_timeout(40)
        p.evaluate("()=>{const l=__popupObjects.shape.__layer;l.fire('mouseout',{});l.getPopup().getElement().dispatchEvent(new MouseEvent('mouseenter',{bubbles:false}))}");p.wait_for_timeout(450)
        assert p.evaluate("()=>__popupObjects.shape.__layer.isPopupOpen()") is True
        hover_markup=p.evaluate("()=>document.querySelector('.leaflet-popup-content').innerHTML")
        p.evaluate("()=>__popupObjects.shape.__layer.getPopup().getElement().dispatchEvent(new MouseEvent('mouseleave',{bubbles:false}))");p.wait_for_timeout(800)
        assert p.evaluate("()=>__popupObjects.shape.__layer.isPopupOpen()") is False
        # Exact video regression: after leaving the canonical hover popup, no
        # delayed legacy handler may reopen the old EDIT-only popup.
        p.wait_for_timeout(700)
        assert p.evaluate("()=>({open:__popupObjects.shape.__layer.isPopupOpen(),popupCount:document.querySelectorAll('.leaflet-popup').length,legacy:document.querySelectorAll('.legacy-popup-edit:not(.tak-popup-edit-toggle-v492)').length})") == {'open':False,'popupCount':0,'legacy':0}

        # Click shape: synthetic map click is fired only if propagation was not stopped.
        click_shape=p.evaluate("""()=>{const l=__popupObjects.shape.__layer,oe={};l.fire('click',{latlng:L.latLng(34.001,-117.999),originalEvent:oe});if(!oe._stopped)map.fire('click',{});const a=l.getPopup()._latlng||{};return {stopped:!!oe._stopped,open:l.isPopupOpen(),pinned:l._takPopupPinned===true,anchor:[Number(a.lat.toFixed(3)),Number(a.lng.toFixed(3))]}}""")
        p.wait_for_timeout(500);click_shape['openAfter']=p.evaluate("()=>__popupObjects.shape.__layer.isPopupOpen()")
        assert click_shape=={'stopped':True,'open':True,'pinned':True,'anchor':[34.005,-117.995],'openAfter':True},click_shape
        click_markup=p.evaluate("()=>document.querySelector('.leaflet-popup-content').innerHTML")
        assert click_markup==hover_markup,(hover_markup,click_markup)
        assert p.evaluate("()=>({buttons:Array.from(document.querySelectorAll('.tak-popup-primary-actions-v492 button')).map(b=>b.textContent.trim()),legacy:document.querySelectorAll('.legacy-popup-edit:not(.tak-popup-edit-toggle-v492)').length})") == {'buttons':['Edit','Geofence'],'legacy':0}
        # Replace button node to prove delegated Geofence action survives popup DOM refresh.
        p.evaluate("()=>{const b=document.querySelector('.tak-geofence-popup-btn-v491');b.outerHTML=b.outerHTML}")
        p.locator('.tak-geofence-popup-btn-v491').click();p.wait_for_selector('#takGeofenceEditorV491');assert p.locator('#takGfNameV491').input_value()=='Shape Alpha';p.locator('[data-gf-close]').first.click()

        # The visible route representation uses the same normalized popup design.
        p.evaluate("()=>{clearPinnedPopup();__popupObjects.route.__layer.fire('mouseover',{latlng:L.latLng(34.024,-117.992)})}");p.wait_for_timeout(120)
        visible_route=p.evaluate("""()=>{const row=document.querySelector('.tak-popup-primary-actions-v492');const buttons=row?Array.from(row.querySelectorAll('button')).map(b=>(b.textContent||'').trim()):[];const visibleEdits=Array.from(document.querySelectorAll('.leaflet-popup button,.leaflet-popup summary')).filter(el=>/^(edit|edit data)$/i.test((el.textContent||'').trim())&&getComputedStyle(el).display!=='none');const info={};document.querySelectorAll('.tak-v322-row').forEach(r=>{const b=r.querySelector('b'),v=r.querySelector('span');if(b&&v)info[b.textContent.trim()]=v.textContent.trim()});return {buttons,rows:document.querySelectorAll('.tak-popup-primary-actions-v492').length,geofence:document.querySelectorAll('.tak-geofence-popup-btn-v491').length,visibleEdits:visibleEdits.length,open:__popupObjects.route.__layer.isPopupOpen(),labels:Object.keys(info),name:info.Name,category:info.Category,color:info.Color,geofenceStatus:info.Geofence,hasPointCount:Object.prototype.hasOwnProperty.call(info,'Points')}}""")
        assert visible_route['buttons']==['Edit','Geofence'] and visible_route['rows']==1 and visible_route['geofence']==1 and visible_route['visibleEdits']==1 and visible_route['open'] is True,visible_route
        assert visible_route['labels']==['Name','Length','Color','Start','End','Category','Notes','Created','Geofence'],visible_route
        assert visible_route['name']=='Route Bravo' and visible_route['category']=='Evacuation' and visible_route['color']=='#3366CC' and visible_route['geofenceStatus']=='Off' and visible_route['hasPointCount'] is False,visible_route
        p.evaluate("()=>__popupObjects.route.__layer.fire('mouseout',{})");p.wait_for_timeout(430)
        assert p.evaluate("()=>__popupObjects.route.__layer.isPopupOpen()") is False

        # Route hit layer click must stay open instead of being closed by map or visible-layer timers.
        click_route=p.evaluate("""()=>{clearPinnedPopup();const l=__popupObjects.route.__hitLayer,oe={};l.fire('mouseover',{latlng:L.latLng(34.025,-117.99)});l.fire('click',{latlng:L.latLng(34.025,-117.99),originalEvent:oe});l.fire('mouseout',{});if(!oe._stopped)map.fire('click',{});return {stopped:!!oe._stopped,open:l.isPopupOpen(),pinned:l._takPopupPinned===true,shared:l.getPopup()===__popupObjects.route.__layer.getPopup()}}""")
        p.wait_for_timeout(600);click_route['openAfter']=p.evaluate("()=>__popupObjects.route.__hitLayer.isPopupOpen()")
        assert click_route=={'stopped':True,'open':True,'pinned':True,'shared':False,'openAfter':True},click_route
        p.wait_for_function("document.querySelectorAll('.tak-geofence-popup-btn-v491').length===1")
        route_design=p.evaluate("""()=>{const row=document.querySelector('.tak-popup-primary-actions-v492');const buttons=row?Array.from(row.querySelectorAll('button')).map(b=>(b.textContent||'').trim()):[];const visibleEdits=Array.from(document.querySelectorAll('.leaflet-popup button,.leaflet-popup summary')).filter(el=>/^(edit|edit data)$/i.test((el.textContent||'').trim())&&getComputedStyle(el).display!=='none');return {buttons,rows:document.querySelectorAll('.tak-popup-primary-actions-v492').length,geofence:document.querySelectorAll('.tak-geofence-popup-btn-v491').length,visibleEdits:visibleEdits.length}}""")
        assert route_design=={'buttons':['Edit','Geofence'],'rows':1,'geofence':1,'visibleEdits':1},route_design
        p.locator('.tak-popup-edit-toggle-v492').click();p.wait_for_timeout(40)
        route_edit=p.evaluate("""()=>{const box=document.querySelector('.tak-v322-inner.tak-popup-inline-editing-v497'),row=document.querySelector('.tak-popup-primary-actions-v492');return {editing:!!box,name:box?.querySelector('[name=\"name\"]')?.value||'',category:box?.querySelector('[name=\"category\"]')?.value||'',color:box?.querySelector('[name=\"color\"]')?.value||'',editable:Array.from(box?.querySelectorAll('input:not([readonly]),select:not([disabled]),textarea:not([readonly])')||[]).map(e=>e.name).filter(Boolean),lat:!!box?.querySelector('[name=\"lat\"]'),lon:!!box?.querySelector('[name=\"lon\"]'),readonly:Array.from(box?.querySelectorAll('.tak-popup-inline-value-v497.readonly input[readonly]')||[]).map(e=>e.value),actions:Array.from(row.querySelectorAll('button')).map(b=>b.textContent.trim())}}""")
        assert route_edit['editing'] is True and route_edit['name']=='Route Bravo' and route_edit['category']=='Evacuation' and route_edit['color']=='#3366cc',route_edit
        assert route_edit['editable']==['name','color','category','notes'] and route_edit['lat'] is False and route_edit['lon'] is False,route_edit
        assert len(route_edit['readonly'])==5 and route_edit['readonly'][-1]=='Off' and route_edit['actions']==['Save','Cancel','Delete'],route_edit
        p.locator('[name=\"category\"]').select_option('Medical');p.locator('[name=\"color\"]').evaluate("e=>{e.focus();e.value='#aa22cc';e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}))}");p.locator('[data-tak-inline-action=\"save\"]').click();p.wait_for_timeout(40)
        route_saved=p.evaluate("()=>window.__inlineSave")
        assert route_saved=={'key':'local:local-route-bravo','source':'local','name':'Route Bravo','type':'','asset':'Route','category':'Medical','color':'#aa22cc','lat':'','lon':'','notes':'Route note'},route_saved
        p.locator('[data-tak-inline-action="cancel"]').click();p.wait_for_timeout(40)
        p.locator('.tak-geofence-popup-btn-v491').click();p.wait_for_selector('#takGeofenceEditorV491');assert p.locator('#takGfNameV491').input_value()=='Route Bravo';assert 'Route · 3 points' in p.locator('.tak-gf-modal-head-v491 small').inner_text()
        diag=p.evaluate("()=>({life:TakMapObjectLifecycleV486.diagnostics(),gf:TakMapGeofencingV491.diagnostics()})")
        b.close()
    if errors:raise AssertionError(errors)
    assert diag['life']['canonicalShapePopupOwner'] is True and diag['life']['popupPropagation'] is True,diag
    print('TAK Map i502 production shape/route popup and route-geofence browser test passed')
    print(json.dumps(diag,sort_keys=True))
    return 0

if __name__=='__main__':
    code=main()
    try:
        sys.stdout.flush(); sys.stderr.flush()
    except Exception:
        pass
    os._exit(int(code or 0))
