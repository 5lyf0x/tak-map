/* TAK Map i669 Range Rings: independent geodesic sets, Leaflet + Cesium terrain.
 * All coordinates stored as WGS84 latitude/longitude. Circles are computed in metres.
 * Toolbar creates a set; ONLY its center marker reopens that set's modal. */
(()=>{'use strict';
const VERSION='1.4.0-i671', KEY='takMap.rangeRings.i669.v1', R=6371008.8;
const UNIT={mi:1609.344,km:1000,nmi:1852,m:1,ft:0.3048};
const $=id=>document.getElementById(id);
const sets=new Map(), groups=new Map();
let current=null, draft=null, chooser=false, choiceCleanup=null, leaflet=null, viewer=null, cesiumSource=null, cesiumHandler=null, lastTerrainType='', lastRenderKey='', started=false, refreshTimer=null;
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function validLatLon(p){return p&&Number.isFinite(Number(p.lat))&&Number.isFinite(Number(p.lon))&&Math.abs(Number(p.lat))<=90&&Math.abs(Number(p.lon))<=180}
function normalize(x,id){
 if(!x||!validLatLon(x.center))return null;
 const interval=Number(x.interval),count=Number(x.count),u=String(x.units||'mi');
 if(!(u in UNIT)||!Number.isFinite(interval)||interval<=0||!Number.isInteger(count)||count<1||count>20||interval*count*UNIT[u]>2000000)return null;
 return {id:String(id||x.id||''),name:String(x.name||'Range Rings').trim().slice(0,65),center:{lat:Number(x.center.lat),lon:Number(x.center.lon)},interval,
 units:u,count,style:x.style==='dashed'?'dashed':'solid',color:/^#[a-f0-9]{6}$/i.test(String(x.color))?String(x.color):'#85cefa',
 opacity:Math.max(.15,Math.min(1,Number(x.opacity)||.85)),width:Math.max(1,Math.min(5,Number(x.width)||1.7)),
 labels:x.labels!==false,labelPositions:(Array.isArray(x.labelPositions)?[...new Set(x.labelPositions.filter(v=>['N','NE','E','SE','S','SW','W','NW'].includes(v)))]:[['N','E','S','W'].includes(x.labelPosition)?x.labelPosition:'N']),remember:!!x.remember};
}
function persist(){try{const arr=[...sets.values()].filter(x=>x.remember);if(arr.length)localStorage.setItem(KEY,JSON.stringify(arr));else localStorage.removeItem(KEY)}catch(_){}}
function restore(){try{const data=JSON.parse(localStorage.getItem(KEY)||'[]');if(Array.isArray(data))for(const raw of data.slice(0,20)){const s=normalize(raw,raw.id);if(s&&s.id&&!sets.has(s.id)){s.remember=true;sets.set(s.id,s)}}}catch(_){}}
function freshId(){let i=1;while(sets.has('ring-'+i))i++;return 'ring-'+i}
function nextName(){let i=1;const used=new Set([...sets.values()].map(x=>x.name));while(used.has('Range Rings '+i))i++;return 'Range Rings '+i}
function centerFromMap(){try{const v=active3D(),C=window.Cesium;if(v&&C){const canvas=v.scene.canvas,ray=v.camera.getPickRay(new C.Cartesian2(canvas.clientWidth/2,canvas.clientHeight/2)),p=ray&&v.scene.globe.pick(ray,v.scene);if(p){const c=C.Cartographic.fromCartesian(p);return {lat:C.Math.toDegrees(c.latitude),lon:C.Math.toDegrees(c.longitude)}}}}catch(_){}try{const m=window.map;if(m&&m.getCenter){const p=m.getCenter();return {lat:p.lat,lon:p.lng}}}catch(_){}try{const s=window.TakMapVeilSceneI668?.();const C=window.Cesium;if(s?.active&&s.viewer&&C){const p=C.Ellipsoid.WGS84.cartesianToCartographic(s.viewer.camera.positionWC);return {lat:C.Math.toDegrees(p.latitude),lon:C.Math.toDegrees(p.longitude)}}}catch(_){}return {lat:34.05,lon:-118.25}}
function destination(center,meters,bearing){const lat=center.lat*Math.PI/180,lon=center.lon*Math.PI/180,b=bearing*Math.PI/180,delta=meters/R;
 const lat2=Math.asin(Math.sin(lat)*Math.cos(delta)+Math.cos(lat)*Math.sin(delta)*Math.cos(b));
 const lon2=lon+Math.atan2(Math.sin(b)*Math.sin(delta)*Math.cos(lat),Math.cos(delta)-Math.sin(lat)*Math.sin(lat2));
 return {lat:lat2*180/Math.PI,lon:((lon2*180/Math.PI+540)%360)-180};}
function ringPoints(s,n){const dist=s.interval*UNIT[s.units]*n,steps=Math.max(96,Math.min(160,Math.ceil(dist/9000)));const arr=[];for(let i=0;i<=steps;i++)arr.push(destination(s.center,dist,i*360/steps));return arr}
function distanceLabel(s,n){return Number((s.interval*n).toFixed(4)).toLocaleString(undefined,{maximumFractionDigits:4})+' '+s.units}
function layerMap(){const m=window.map;return m&&typeof m.getContainer==='function'&&window.L?m:null}
function clear2D(){for(const g of groups.values())try{leaflet&&leaflet.removeLayer(g)}catch(_){}groups.clear();leaflet=null}
function centerHtml(s){return '<div class="tak-range-center-hit-i669"><div class="tak-range-center-title-i669">'+esc(s.name)+'</div><div class="tak-range-cross-i669">+</div></div>'}
function redraw2D(){const m=layerMap(),L=window.L;if(!m||!L)return;
 if(leaflet!==m){clear2D();leaflet=m}
 for(const [id,g] of groups){if(!sets.has(id)){m.removeLayer(g);groups.delete(id)}}
 for(const s of sets.values()){
  const old=groups.get(s.id);if(old){m.removeLayer(old);groups.delete(s.id)}
  const g=L.layerGroup();
  for(let n=1;n<=s.count;n++){
    const pts=ringPoints(s,n).map(p=>[p.lat,p.lon]);
    L.polyline(pts,{color:s.color,weight:s.width,opacity:s.opacity,dashArray:s.style==='dashed'?'7 6':null,interactive:false,noClip:false}).addTo(g);
    if(s.labels)for(const direction of s.labelPositions){const az={N:0,NE:45,E:90,SE:135,S:180,SW:225,W:270,NW:315}[direction];const p=destination(s.center,s.interval*UNIT[s.units]*n,az);
      L.marker([p.lat,p.lon],{interactive:false,keyboard:false,icon:L.divIcon({className:'tak-range-dist-container-i669',html:'<span class="tak-range-dist-i669">'+esc(distanceLabel(s,n))+'</span>',iconSize:[1,1],iconAnchor:[0,0]}),zIndexOffset:290}).addTo(g)}
  }
  const center=L.marker([s.center.lat,s.center.lon],{icon:L.divIcon({className:'tak-range-center-container-i669',html:centerHtml(s),iconSize:[18,18],iconAnchor:[9,9]}),title:s.name,zIndexOffset:920,interactive:true});
  center.on('click',e=>{L.DomEvent.stopPropagation(e);openEdit(s.id)});center.addTo(g);g.addTo(m);groups.set(s.id,g);
 }
}
function active3D(){const info=window.TakMapVeilSceneI668?.();return info?.active&&info.viewer&&window.Cesium?info.viewer:null}
function terrainSample(point){try{const h=window.TakMapTerrainOverlayHooksI669;if(h?.local&&typeof h.sampleLocal==='function'){const m=h.sampleLocal(point.lat,point.lon);return Number.isFinite(m)?m+2:null}}catch(_){}return null}
function localTerrain(){try{return !!window.TakMapTerrainOverlayHooksI669?.local}catch(_){return false}}
function clear3D(){if(cesiumHandler){try{cesiumHandler.destroy()}catch(_){}cesiumHandler=null}if(viewer&&cesiumSource){try{viewer.dataSources.remove(cesiumSource,true)}catch(_){} }viewer=null;cesiumSource=null;lastRenderKey=''}
function build3D(){const v=active3D(),C=window.Cesium;if(!v||!C){clear3D();return}const isLocal=localTerrain();
 if(viewer!==v){clear3D();viewer=v;cesiumSource=new C.CustomDataSource('TAK Map Range Rings i669');void viewer.dataSources.add(cesiumSource);
  cesiumHandler=new C.ScreenSpaceEventHandler(viewer.scene.canvas);
  cesiumHandler.setInputAction(event=>{const hit=viewer.scene.pick(event.position),entity=hit&&hit.id;
   if(entity&&typeof entity.__takRangeIdI669==='string')openEdit(entity.__takRangeIdI669)
  },C.ScreenSpaceEventType.LEFT_CLICK);
 }
 const key=(isLocal?'local':'streamed')+':'+[...sets.values()].map(s=>JSON.stringify(s)).join('|');if(key===lastRenderKey)return;lastRenderKey=key;
 cesiumSource.entities.removeAll();
 for(const s of sets.values()){
  const color=C.Color.fromCssColorString(s.color).withAlpha(s.opacity);
  const material=s.style==='dashed'?new C.PolylineDashMaterialProperty({color,dashLength:16}):color;
  for(let n=1;n<=s.count;n++){
   const coords=ringPoints(s,n),sampled=isLocal?coords.map(terrainSample):null;
   const drape=!!(!isLocal||sampled&&sampled.every(x=>x!==null));
   const positions=coords.map((p,i)=>C.Cartesian3.fromDegrees(p.lon,p.lat,isLocal&&sampled?.[i]!=null?sampled[i]:0));
   const polyline={positions,width:s.width,material,clampToGround:!isLocal||!drape,arcType:C.ArcType.GEODESIC};
   if(isLocal&&drape)polyline.clampToGround=false;
   cesiumSource.entities.add({id:s.id+':ring:'+n,polyline});
   if(s.labels)for(const direction of s.labelPositions){const az={N:0,NE:45,E:90,SE:135,S:180,SW:225,W:270,NW:315}[direction],p=destination(s.center,s.interval*UNIT[s.units]*n,az),h=terrainSample(p);
    cesiumSource.entities.add({id:s.id+':label:'+n+':'+direction,position:C.Cartesian3.fromDegrees(p.lon,p.lat,h??0),
      label:{text:distanceLabel(s,n),font:'600 12px sans-serif',fillColor:C.Color.WHITE,
      outlineColor:C.Color.fromCssColorString('#11212c'),outlineWidth:3,style:C.LabelStyle.FILL_AND_OUTLINE,
      showBackground:true,backgroundColor:C.Color.fromCssColorString('#10202b').withAlpha(.9),backgroundPadding:new C.Cartesian2(6,3),
      pixelOffset:new C.Cartesian2(0,-9),heightReference:h!=null?C.HeightReference.NONE:C.HeightReference.CLAMP_TO_GROUND,
      disableDepthTestDistance:Number.POSITIVE_INFINITY}});
   }
  }
  const h=terrainSample(s.center),mark=cesiumSource.entities.add({id:s.id+':center',name:s.name,
    position:C.Cartesian3.fromDegrees(s.center.lon,s.center.lat,h??0),
    billboard:{image:'data:image/svg+xml,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 28 28"><circle cx="14" cy="14" r="9" fill="#11202d" stroke="'+s.color+'" stroke-width="2"/><path d="M9 14h10M14 9v10" stroke="white" stroke-width="1.5"/></svg>'),width:28,height:28,verticalOrigin:C.VerticalOrigin.CENTER,
      heightReference:h!=null?C.HeightReference.NONE:C.HeightReference.CLAMP_TO_GROUND,disableDepthTestDistance:Number.POSITIVE_INFINITY},
    label:{text:s.name,font:'600 12px sans-serif',showBackground:true,backgroundColor:C.Color.fromCssColorString('#10202b').withAlpha(.95),
      backgroundPadding:new C.Cartesian2(6,3),fillColor:C.Color.WHITE,verticalOrigin:C.VerticalOrigin.BOTTOM,pixelOffset:new C.Cartesian2(0,-16),
      heightReference:h!=null?C.HeightReference.NONE:C.HeightReference.CLAMP_TO_GROUND,disableDepthTestDistance:Number.POSITIVE_INFINITY}});
  mark.__takRangeIdI669=s.id;
 }
 viewer.scene.requestRender();
}
function render(){if(active3D()){clear2D();build3D()}else{clear3D();redraw2D()}}
function css(){if($('takRangeCssI669'))return;const el=document.createElement('style');el.id='takRangeCssI669';el.textContent=`
#toolRangeRingsI669 img{display:block;width:21px;height:21px;object-fit:contain}
.tak-range-center-container-i669,.tak-range-dist-container-i669{background:none!important;border:0!important}
.tak-range-center-hit-i669{position:relative;width:18px;height:18px;cursor:pointer}
.tak-range-cross-i669{border:1.6px solid #b5d7ed;border-radius:50%;width:18px;height:18px;display:grid;place-items:center;background:#10202ceb;color:white;font-size:14px;line-height:1;box-shadow:0 1px 6px #0008;font-weight:700}
.tak-range-center-title-i669{position:absolute;left:50%;bottom:22px;transform:translateX(-50%);white-space:nowrap;font-size:11px;font-weight:700;color:#f1f6f8;background:#10212beF;border:1px solid #456073;padding:3px 6px;border-radius:5px;pointer-events:none;max-width:170px;overflow:hidden;text-overflow:ellipsis;line-height:1.2}
.tak-range-dist-i669{display:inline-block;transform:translate(-50%,-50%);white-space:nowrap;padding:2px 5px;border-radius:5px;color:#edf6fa;background:#10212bef;border:1px solid #46657c;font-size:11px;font-weight:650;pointer-events:none}
#takRangeModalI669{position:fixed;inset:0;background:#030910a8;z-index:2147483200;display:none;justify-content:center;align-items:center;padding:12px}
#takRangeModalI669.open{display:flex}
#takRangeModalI669 .tr-dialog{width:min(365px,96vw);max-height:92vh;overflow-y:auto;display:grid;gap:11px;padding:14px;background:#101e28;color:#edf4f8;border:1px solid #395769;border-radius:12px;box-shadow:0 14px 46px #000b;font:12px system-ui,sans-serif}
#takRangeModalI669 .tr-head{display:flex;align-items:center;gap:9px}#takRangeModalI669 .tr-head img{width:23px;height:23px}
#takRangeModalI669 .tr-head b{flex:1;font-size:15px}#takRangeModalI669 button{cursor:pointer;font:inherit;border:1px solid #415a6a;border-radius:7px;background:#1a3040;color:#eef6fb;padding:7px 9px}
#takRangeModalI669 button:hover{background:#24465b}#takRangeModalI669 input:not([type=checkbox]):not([type=color]),#takRangeModalI669 select{width:100%;min-width:0;box-sizing:border-box;border:1px solid #415b6d;background:#0b1923;color:#edf5f9;border-radius:7px;padding:8px;font:inherit}
#takRangeModalI669 .tr-field{display:grid;gap:4px;color:#b3c8d6;font-size:11px}#takRangeModalI669 .tr-two{display:grid;grid-template-columns:1fr 1fr;gap:8px}
#takRangeModalI669 .tr-center{display:flex;gap:6px}#takRangeModalI669 .tr-center button{flex:1;padding:8px 4px;font-size:11px}#takRangeModalI669 .tr-center button.active{border-color:#8ac8ea;color:white;background:#23506a}
#takRangeModalI669 .tr-check{display:flex;align-items:center;gap:7px;color:#d8e5ec;font-size:11px}#takRangeModalI669 input[type=checkbox]{accent-color:#4ca5d5}
#takRangeModalI669 input[type=color]{width:42px;height:30px;cursor:pointer;appearance:auto;background:#0e1b24;border:1px solid #405a69;border-radius:5px}#takRangeModalI669 .tr-palette{display:flex;align-items:center;gap:7px}#takRangeModalI669 .tr-palette button{padding:5px 8px}#takRangeModalI669 .tr-directions{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px}#takRangeModalI669 .tr-directions label{display:flex;gap:4px;align-items:center;cursor:pointer}
#takRangeModalI669 .tr-footer{display:flex;justify-content:flex-end;gap:7px}#takRangeModalI669 .tr-footer .primary{background:#b9c8d1;color:#10212b;font-weight:800;border-color:#b9c8d1}
#takRangeModalI669 .tr-footer .danger{margin-right:auto;color:#ffb3ad;border-color:#9b484a;background:#28191e}#takRangeModalI669 .tr-note{font-size:10px;color:#9bb6c5}
#takRangeModalI669 .tr-message{color:#ffc19d;font-size:11px;min-height:12px}
`;document.head.append(el)}
function modal(){if($('takRangeModalI669'))return;const host=document.createElement('section');host.id='takRangeModalI669';host.role='dialog';host.setAttribute('aria-modal','true');host.innerHTML=`<div class="tr-dialog">
 <header class="tr-head"><img src="/assets/runtime/tak-map-range-rings-icon-i669.svg" alt=""><b>Range Rings</b><button type="button" id="trCloseI669" aria-label="Close">×</button></header>
 <label class="tr-field">Name<input id="trNameI669" maxlength="65" placeholder="Range Rings 1"></label>
 <div class="tr-field">Ring center<div class="tr-center"><button data-center="map" type="button">Map Center</button><button data-center="select" type="button">Select on Map</button><button data-center="location" type="button">My Location</button></div></div>
 <div class="tr-note" id="trCenterNoteI669">Center remains fixed as the map moves.</div>
 <div class="tr-two"><label class="tr-field">Interval<input type="number" min="0.01" step="any" id="trIntervalI669"></label><label class="tr-field">Units<select id="trUnitsI669"><option value="mi">Miles</option><option value="km">Kilometers</option><option value="nmi">Nautical miles</option><option value="m">Meters</option><option value="ft">Feet</option></select></label></div>
 <div class="tr-two"><label class="tr-field">Number of rings<input id="trCountI669" type="number" min="1" max="20" step="1"></label><label class="tr-field">Line style<select id="trStyleI669"><option value="solid">Solid</option><option value="dashed">Dashed</option></select></label></div>
 <div class="tr-two"><label class="tr-field">Ring color<div class="tr-palette"><input id="trColorI669" type="color" aria-label="Ring color"><button type="button" id="trOpenColorI671">Choose</button></div></label><label class="tr-field">Opacity<input id="trOpacityI669" type="range" min="15" max="100" step="5"></label></div>
 <div class="tr-two"><label class="tr-field">Line width<select id="trWidthI669"><option value="1">Thin</option><option value="1.7">Normal</option><option value="2.5">Bold</option></select></label><div class="tr-field">Label directions<div class="tr-directions" id="trPositionsI671"><label><input type="checkbox" value="N">N</label><label><input type="checkbox" value="NE">NE</label><label><input type="checkbox" value="E">E</label><label><input type="checkbox" value="SE">SE</label><label><input type="checkbox" value="S">S</label><label><input type="checkbox" value="SW">SW</label><label><input type="checkbox" value="W">W</label><label><input type="checkbox" value="NW">NW</label></div></div></div>
 <label class="tr-check"><input id="trLabelsI669" type="checkbox" checked> Show distance labels</label>
 <label class="tr-check"><input id="trRememberI669" type="checkbox"> Remember rings after reload</label>
 <div class="tr-note" id="trSummaryI669"></div><div class="tr-message" id="trErrorI669" role="status"></div>
 <footer class="tr-footer"><button class="danger" type="button" id="trClearI669">Clear Rings</button><button id="trCancelI669" type="button">Cancel</button><button class="primary" id="trApplyI669" type="button">Apply</button></footer>
 </div>`;document.body.append(host);
 $('trCloseI669').onclick=closeModal;$('trCancelI669').onclick=closeModal;
 $('trClearI669').onclick=()=>{if(current&&sets.has(current)){sets.delete(current);persist();render();closeModal()}};
 $('trApplyI669').onclick=apply;
 document.querySelectorAll('#takRangeModalI669 [data-center]').forEach(btn=>{btn.onclick=()=>chooseCenter(btn.dataset.center)});
 ['trIntervalI669','trUnitsI669','trCountI669'].forEach(x=>$(x).addEventListener('input',summary));
 $('trLabelsI669').addEventListener('change',()=>{document.querySelectorAll('#trPositionsI671 input').forEach(el=>el.disabled=!$('trLabelsI669').checked)});
 $('trOpenColorI671').addEventListener('click',()=>{const color=$('trColorI669');if(typeof color.showPicker==='function'){try{color.showPicker();return}catch(_){}}color.click()});
 host.addEventListener('click',e=>{if(e.target===host)closeModal()});
}
function summary(){const u=$('trUnitsI669').value,n=Number($('trCountI669').value),v=Number($('trIntervalI669').value);$('trSummaryI669').textContent=(n&&v)?n+' rings · '+v+' '+u+' intervals · '+Number((v*n).toFixed(3))+' '+u+' outer radius':''}
function chooseCenter(mode){
 if(!draft)return;
 document.querySelectorAll('#takRangeModalI669 [data-center]').forEach(b=>b.classList.toggle('active',b.dataset.center===mode));
 if(mode==='map'){
   draft.center=centerFromMap();
   $('trCenterNoteI669').textContent='Centered on current map view · '+draft.center.lat.toFixed(5)+', '+draft.center.lon.toFixed(5);
  }else if(mode==='select'){
   $('trCenterNoteI669').textContent='Click the map once to choose center. Press Escape to cancel.';
   chooser=true;$('takRangeModalI669').classList.remove('open');
   const m=layerMap(),v=m?null:active3D(),C=window.Cesium;
   const canvas=m?m.getContainer():v?.scene?.canvas;
   if(!canvas){chooser=false;$('takRangeModalI669').classList.add('open');$('trErrorI669').textContent='Map is not ready for center selection.';return}
   const previous=canvas.style.cursor;
   const crosshair='url("data:image/svg+xml,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32"><path d="M16 2v28M2 16h28" stroke="white" stroke-width="4"/><path d="M16 2v28M2 16h28" stroke="black" stroke-width="2"/></svg>')+'") 16 16, crosshair';
   canvas.style.setProperty('cursor',crosshair,'important');
   let callback=null,handler=null;
   choiceCleanup=()=>{canvas.style.cursor=previous;canvas.style.removeProperty('cursor');if(previous)canvas.style.cursor=previous;canvas.removeEventListener('mousemove',enforceCursor,true);window.removeEventListener('keydown',escapeChoice,true);if(m&&callback)m.off('click',callback);if(handler){handler.destroy();handler=null}choiceCleanup=null};
   function enforceCursor(){if(chooser)canvas.style.setProperty('cursor',crosshair,'important')}
   function cancelChoice(){if(!chooser)return;chooser=false;choiceCleanup?.();$('takRangeModalI669').classList.add('open');$('trCenterNoteI669').textContent='Center selection canceled.'}
   function escapeChoice(e){if(e.key==='Escape'){e.preventDefault();e.stopPropagation();cancelChoice()}}
   const selected=p=>{if(!chooser||!draft)return;draft.center=p;chooser=false;choiceCleanup?.();$('takRangeModalI669').classList.add('open');$('trCenterNoteI669').textContent='Center selected · '+p.lat.toFixed(5)+', '+p.lon.toFixed(5)};
   canvas.addEventListener('mousemove',enforceCursor,true);window.addEventListener('keydown',escapeChoice,true);
   if(m){callback=e=>selected({lat:e.latlng.lat,lon:e.latlng.lng});m.on('click',callback)}
   else if(v&&C){handler=new C.ScreenSpaceEventHandler(canvas);handler.setInputAction(e=>{const ray=v.camera.getPickRay(e.position),p=ray&&v.scene.globe.pick(ray,v.scene);if(p){const c=C.Cartographic.fromCartesian(p);selected({lat:C.Math.toDegrees(c.latitude),lon:C.Math.toDegrees(c.longitude)})}},C.ScreenSpaceEventType.LEFT_CLICK)}
 }else if(mode==='location'){
   if(!navigator.geolocation){$('trErrorI669').textContent='Location access unavailable.';return}
   navigator.geolocation.getCurrentPosition(p=>{if(!draft)return;draft.center={lat:p.coords.latitude,lon:p.coords.longitude};
     $('trCenterNoteI669').textContent='Location selected · '+draft.center.lat.toFixed(5)+', '+draft.center.lon.toFixed(5)
   },()=>{$('trErrorI669').textContent='Location unavailable. Use Map Center or Select on Map.'},{enableHighAccuracy:false,timeout:8000,maximumAge:60000});
 }
}
function fill(s){$('trNameI669').value=s.name;$('trIntervalI669').value=s.interval;$('trUnitsI669').value=s.units;$('trCountI669').value=s.count;
 $('trStyleI669').value=s.style;$('trColorI669').value=s.color;$('trOpacityI669').value=Math.round(s.opacity*100);
 $('trWidthI669').value=String(s.width);$('trLabelsI669').checked=s.labels;document.querySelectorAll('#trPositionsI671 input').forEach(el=>{el.checked=s.labelPositions.includes(el.value);el.disabled=!s.labels});
 $('trRememberI669').checked=s.remember;$('trErrorI669').textContent='';
 $('trClearI669').hidden=current===null;$('trCenterNoteI669').textContent='Center · '+s.center.lat.toFixed(5)+', '+s.center.lon.toFixed(5);
 document.querySelectorAll('#takRangeModalI669 [data-center]').forEach(b=>b.classList.remove('active'));summary()}
function openNew(){if(!started)return;current=null;draft={id:freshId(),name:nextName(),center:centerFromMap(),interval:5,units:'mi',count:5,style:'solid',color:'#85cefa',opacity:.85,width:1.7,labels:true,labelPositions:['N'],remember:false};fill(draft);$('takRangeModalI669').classList.add('open');$('trNameI669').focus()}
function openEdit(id){if(!sets.has(id))return;current=id;draft={...sets.get(id),center:{...sets.get(id).center}};fill(draft);$('takRangeModalI669').classList.add('open')}
function closeModal(){chooser=false;choiceCleanup?.();current=null;draft=null;$('takRangeModalI669')?.classList.remove('open')}
function apply(){if(!draft)return;const item=normalize({...draft,name:$('trNameI669').value||draft.name,interval:Number($('trIntervalI669').value),units:$('trUnitsI669').value,count:Number($('trCountI669').value),style:$('trStyleI669').value,
 color:$('trColorI669').value,opacity:Number($('trOpacityI669').value)/100,width:Number($('trWidthI669').value),labels:$('trLabelsI669').checked,labelPositions:[...document.querySelectorAll('#trPositionsI671 input:checked')].map(el=>el.value),remember:$('trRememberI669').checked},draft.id);
 if(!item){$('trErrorI669').textContent='Choose 1–20 rings with valid intervals (outer radius 2,000 km maximum).';return}
 if(sets.size>=20&&!sets.has(item.id)){$('trErrorI669').textContent='The maximum is 20 independent sets.';return}
 sets.set(item.id,item);persist();render();closeModal();}
function toolbar(){const bar=$('floatingMapToolbar'),move=$('toolMove');if(!bar||!move)return false;
 if($('toolRangeRingsI669'))return true;const b=document.createElement('button');b.id='toolRangeRingsI669';b.className='tool-btn';b.type='button';b.title='Range Rings';b.setAttribute('aria-label','Create range rings');
 b.innerHTML='<img src="/assets/runtime/tak-map-range-rings-icon-i669.svg" alt=""><span class="tool-label">Range Rings</span>';move.insertAdjacentElement('afterend',b);b.addEventListener('click',e=>{e.stopPropagation();openNew()});return true}
function boot(){if(started)return;if(!document.body||!document.head||!toolbar())return;started=true;css();modal();restore();render();
 refreshTimer=setInterval(()=>{const type=localTerrain()?'local':'streamed';if(type!==lastTerrainType){lastRenderKey='';lastTerrainType=type}renderMode()},1700);
 window.addEventListener('keydown',e=>{if(e.key==='Escape'&&$('takRangeModalI669')?.classList.contains('open'))closeModal()});
 window.addEventListener('takmap:runtime-ready-i553',renderMode);
}
function renderMode(){const v=active3D();if(v){clear2D();build3D()}else{if(viewer)clear3D();if(sets.size&&(groups.size!==sets.size||leaflet!==layerMap()))redraw2D()}}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>{boot();setTimeout(boot,1000)},{once:true});else{boot();setTimeout(boot,1000)}
window.TakMapRangeRingsI669={version:VERSION,destination,normalize,ringPoints,get sets(){return [...sets.values()].map(s=>({...s}))},openNew,openEdit,render,diagnostics:()=>({count:sets.size,leaflet:groups.size,terrain:!!viewer})};
})();
