#!/usr/bin/env python3
from __future__ import annotations
import json, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ASSET=(ROOT/'assets'/'tak-map-adsb-v491.js').read_text()

HTML_PREFIX=r'''<!doctype html><html><head><meta charset="utf-8"><style>
#map{position:relative;width:900px;height:600px;background:#ddd}.leaflet-marker-icon{position:absolute;left:300px;top:240px;width:52px;height:52px;z-index:20}.leaflet-popup{position:absolute;left:365px;top:220px;z-index:30;background:#111;color:#fff;padding:12px}
</style></head><body>
<div id="map"></div><div id="adsbStatus"></div><div id="adsbSettingsStatus"></div><div id="bannerAdsb"></div><div id="bannerAdsbDot"></div><div id="adsbHeaderCountV486"></div><div id="statusDropdown"></div>
<input id="adsbFilterCivil" type="checkbox" checked><input id="adsbFilterMilitary" type="checkbox" checked><input id="adsbFilterGovt" type="checkbox" checked><input id="adsbFilterUnknown" type="checkbox" checked>
<input id="adsbUpdateInterval" value="5"><input id="adsbRadiusMiles" value="50"><select id="adsbCenterSource"><option value="manual">manual</option></select><input id="adsbCenterLatLon" value="34,-118"><button id="adsbToggleBtn"></button><input id="adsbHeaderEnableV476" type="checkbox" checked>
<script>
try{localStorage.setItem('takmap.adsb.localDisabled','1')}catch(_){}
(function(){
 let seq=1;
 function Evented(){this._events={}}
 Evented.prototype.on=function(name,fn,ctx){(this._events[name]||(this._events[name]=[])).push({fn,ctx:ctx||this});return this};
 Evented.prototype.off=function(name,fn,ctx){if(!name){this._events={};return this}const a=this._events[name]||[];this._events[name]=a.filter(x=>!((!fn||x.fn===fn)&&(!ctx||x.ctx===ctx)));return this};
 Evented.prototype.fire=function(name,data){for(const x of (this._events[name]||[]).slice())x.fn.call(x.ctx||this,data||{});return this};
 const map=new Evented();map._layers=[];map.getCenter=()=>({lat:34,lng:-118});map.distance=()=>0;map.addLayer=x=>{if(!map._layers.includes(x))map._layers.push(x);return map};map.removeLayer=x=>{map._layers=map._layers.filter(v=>v!==x);return map};map.hasLayer=x=>map._layers.includes(x);map.eachLayer=fn=>{map._layers.slice().forEach(fn);return map};map.getContainer=()=>document.getElementById('map');window.map=window.takLeafletMap=map;
 function layerGroup(){const g=new Evented();g._layers=[];g.addTo=m=>{g._map=m;m.addLayer(g);return g};g.addLayer=x=>{if(!g._layers.includes(x))g._layers.push(x);x._map=map;return g};g.removeLayer=x=>{g._layers=g._layers.filter(v=>v!==x);try{x.getElement()?.remove()}catch(_){}return g};g.clearLayers=()=>{g._layers.slice().forEach(x=>g.removeLayer(x));return g};g.eachLayer=fn=>{g._layers.slice().forEach(fn);return g};return g}
 function marker(coords,opts){const mk=new Evented();mk._leaflet_id=seq++;mk.options=opts||{};mk._latlng={lat:Number(coords[0]),lng:Number(coords[1])};mk._popup=null;mk._opened=false;const el=document.createElement('button');el.type='button';el.className='leaflet-marker-icon adsb-test-marker';el.innerHTML='<img data-adsb-img alt="Aircraft" style="width:38px;height:38px"><span class="aircraft-label"></span>';document.getElementById('map').appendChild(el);
  mk.addTo=g=>{g.addLayer(mk);return mk};mk.getElement=()=>el;mk.getLatLng=()=>mk._latlng;mk.setLatLng=v=>{mk._latlng={lat:Number(v[0]??v.lat),lng:Number(v[1]??v.lng)};return mk};mk.setZIndexOffset=()=>mk;mk.setIcon=()=>mk;
  mk.bindPopup=function(content,options){const p={content,options:Object.assign({},options||{}),_source:mk,_open:false,_el:null,getContent(){return this.content},setContent(v){this.content=v;return this},getElement(){return this._el},isOpen(){return this._open}};mk._popup=p;mk._openPopup=function(ev){if(mk._opened)mk.closePopup();else mk.openPopup(ev&&ev.latlng)};mk.on('click',mk._openPopup,mk);try{TakMapPopupLifecycleV463.registerPopupLayer(mk)}catch(_){}return mk};
  mk.getPopup=()=>mk._popup;mk.setPopupContent=v=>{if(mk._popup)mk._popup.content=v;return mk};mk.isPopupOpen=()=>mk._opened;
  mk.openPopup=function(at){const p=mk._popup;if(!p)return mk;mk._opened=true;p._open=true;if(!p._el){p._el=document.createElement('div');p._el.className='leaflet-popup adsb-object-popup adsb-test-popup';document.getElementById('map').appendChild(p._el)}p._el.innerHTML=String(p.content||'');p._el.style.display='block';map._popup=p;mk.fire('popupopen',{popup:p,latlng:at});map.fire('popupopen',{popup:p});return mk};
  mk.closePopup=function(){const p=mk._popup;if(!p||!mk._opened)return mk;mk._opened=false;p._open=false;if(p._el)p._el.style.display='none';mk.fire('popupclose',{popup:p});map.fire('popupclose',{popup:p});if(map._popup===p)map._popup=null;return mk};return mk}
 window.L={marker,layerGroup,latLng:(a,b)=>({lat:Number(a?.lat??a?.[0]??a),lng:Number(a?.lng??a?.lon??a?.[1]??b)}),divIcon:o=>o||{},DomEvent:{stopPropagation:e=>{if(e){e._stopped=true;e.stopPropagation&&e.stopPropagation()}},preventDefault:e=>e&&e.preventDefault&&e.preventDefault(),stop:e=>{if(e){e._stopped=true;e.preventDefault&&e.preventDefault();e.stopPropagation&&e.stopPropagation()}}},Layer:{prototype:{}}};
 const layer=L.layerGroup().addTo(map),ctl={version:'v491',layer,markers:new Map(),data:new Map(),lastList:[],tracking:{id:null,layer:null,label:null,points:[]}};window.TakMapControllers={adsb:ctl};window.aircraftLayer=layer;
 window.TakMapPopupLifecycleV463={registerPopupLayer(mk){if(mk.__v463LifecycleBound)return mk;mk.__v463LifecycleBound=true;mk.on('click',ev=>{const oe=ev&&ev.originalEvent;if(oe){oe.__takMapObjectPopupClick=true;oe._stopped=true}mk._takPopupPinned=true;window._takPinnedPopupLayer=mk;setTimeout(()=>{if(!mk.isPopupOpen())mk.openPopup(ev&&ev.latlng)},0)});return mk}};
 window.drawAircraft=function(input){const rows=Array.isArray(input)?input:[],seen=new Set();rows.forEach(a=>{const id=String(a.id).toLowerCase();seen.add(id);let mk=ctl.markers.get(id);if(!mk){mk=L.marker([a.lat,a.lon],{interactive:true}).addTo(layer);ctl.markers.set(id,mk)}else mk.setLatLng([a.lat,a.lon]);mk._takAdsbAircraft=a;mk._takAdsbId=id;if(!mk.isPopupOpen()){mk.bindPopup('<div class="aircraft-info">'+String(a.callsign||id)+'</div>',{className:'adsb-object-popup',autoPan:false,closeButton:false,autoClose:false,closeOnClick:false});try{if(mk.__v463LifecycleBound&&mk._openPopup)mk.off('click',mk._openPopup,mk)}catch(_){}}else mk.setPopupContent('<div class="aircraft-info">'+String(a.callsign||id)+'</div>')});for(const [id,mk] of [...ctl.markers])if(!seen.has(id)){layer.removeLayer(mk);ctl.markers.delete(id)}return rows};
 window.__adsbBubbleClicks=0;document.addEventListener('click',()=>window.__adsbBubbleClicks++);
})();
</script><script>'''
HTML_SUFFIX='''</script></body></html>'''

def main()->int:
    chromium=next((n for n in ('chromium','chromium-browser','google-chrome','google-chrome-stable') if shutil.which(n)),None)
    if not chromium:
        print('SKIP: Chromium unavailable');return 0
    html=HTML_PREFIX+ASSET+HTML_SUFFIX
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=shutil.which(chromium),args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
        page=browser.new_page(viewport={'width':1000,'height':700});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content(html,wait_until='domcontentloaded',timeout=15000)
        page.wait_for_function("window.TakMapAdsbWorkerV477 && typeof window.TakMapAdsbWorkerV477.renderForTest==='function'",timeout=10000)
        rows=[{'id':'dom-click-aircraft','lat':34.0,'lon':-118.0,'alt_ft':7500,'category_class':'civil','description':'CIVIL','callsign':'DOM502'}]
        first=page.evaluate("""rows=>{const api=TakMapAdsbWorkerV477;api.renderForTest(rows);api.bindPopupOwners();const mk=TakMapControllers.adsb.markers.get('dom-click-aircraft');return {marker:!!mk,owner:!!(mk&&mk.__takAdsbPopupOwnerHandlerV502),open:!!(mk&&mk.isPopupOpen()),diag:api.diagnostics()}}""",rows)
        page.locator('.adsb-test-marker').click(force=True,timeout=5000);page.wait_for_timeout(80)
        after=page.evaluate("""()=>{const api=TakMapAdsbWorkerV477,mk=TakMapControllers.adsb.markers.get('dom-click-aircraft'),p=mk&&mk.getPopup();return {open:!!(mk&&mk.isPopupOpen()),pinned:!!(mk&&mk._takPopupPinned),popupPinned:!!(p&&p.__v463Pinned),popupVisible:!!document.querySelector('.adsb-test-popup')&&getComputedStyle(document.querySelector('.adsb-test-popup')).display!=='none',bubbleClicks:window.__adsbBubbleClicks,diag:api.diagnostics()}}""")
        rerender=page.evaluate("""rows=>{const api=TakMapAdsbWorkerV477,mk=TakMapControllers.adsb.markers.get('dom-click-aircraft'),before=mk.__takAdsbPopupOwnerHandlerV502;api.renderForTest(rows);api.bindPopupOwners();return {same:before===mk.__takAdsbPopupOwnerHandlerV502,diag:api.diagnostics()}}""",rows)
        page.locator('.adsb-test-marker').click(force=True,timeout=5000);page.wait_for_timeout(80)
        second=page.evaluate("""()=>{const mk=TakMapControllers.adsb.markers.get('dom-click-aircraft');return {open:mk.isPopupOpen(),bubbleClicks:window.__adsbBubbleClicks}}""")
        browser.close()
    assert first['marker'] and first['owner'] and not first['open'],first
    assert after['open'] and after['pinned'] and after['popupPinned'] and after['popupVisible'],after
    assert after['bubbleClicks']==0,after
    assert rerender['same'] and rerender['diag']['popupOwnerBinds']==1 and rerender['diag']['popupOpenFailures']==0,rerender
    assert second['open'] and second['bubbleClicks']==0,second
    fatal=[e for e in errors if any(t in e.lower() for t in ('maximum call stack','too much recursion','out of memory'))];assert not fatal,fatal
    print('TAK Map i502 ADS-B real DOM first-click popup owner test passed')
    print(json.dumps({'first':first,'after':after,'rerender':rerender,'second':second},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
