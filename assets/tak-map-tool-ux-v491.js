(function(w,d){
'use strict';
const VERSION='i491';
const S={map:null,mousemoveBound:false,toolWrappers:false,routePreview:null,measurePreviewHalo:null,measurePreviewLine:null,measurePreviewLabel:null,lastPointer:null,lastTool:'move',boots:0,statusSuppressions:0,cursorUpdates:0,routePreviewUpdates:0,measurePreviewUpdates:0,measureDraftClears:0,routeCancelInstalls:0,basemapSyncs:0,basemapHeaderBound:false,keyBound:false,colorPickerBound:false,colorPickerCloses:0,colorPickerOpens:0,colorPickerInput:null};
function $(id){try{return d.getElementById(id)}catch(_){return null}}
function q(sel,root){try{return (root||d).querySelector(sel)}catch(_){return null}}
function qa(sel,root){try{return Array.from((root||d).querySelectorAll(sel))}catch(_){return []}}
function mapObj(){try{return (w.takLeafletMap&&w.takLeafletMap.on)?w.takLeafletMap:((w.map&&w.map.on)?w.map:null)}catch(_){return null}}
function currentTool(){try{if(typeof activeMapTool!=='undefined')return String(activeMapTool||'move')}catch(_){}try{return String(w.activeMapTool||'move')}catch(_){return'move'}}
function creationTool(tool){tool=String(tool||currentTool()).toLowerCase();return tool==='pointdropper'||tool==='route'||tool==='draw'||tool==='measure'}
function mapContainer(){const m=mapObj();try{return (m&&m.getContainer&&m.getContainer())||$('map')}catch(_){return $('map')}}
function installCss(){
  if($('takMapToolUxStyleV486'))return;
  const st=d.createElement('style');st.id='takMapToolUxStyleV486';st.textContent=`
#mapStatus,#toolStatus{display:none!important;visibility:hidden!important;height:0!important;min-height:0!important;margin:0!important;padding:0!important;border:0!important;overflow:hidden!important}
.leaflet-container.tak-create-crosshair-v491,.leaflet-container.tak-create-crosshair-v491 .leaflet-interactive,.leaflet-container.tak-create-crosshair-v491 .leaflet-marker-icon,.leaflet-container.tak-create-crosshair-v491 .leaflet-marker-shadow{cursor:crosshair!important}
#routeMiniToolbar .tak-route-cancel-v491{border-color:rgba(255,95,87,.92)!important;background:rgba(255,95,87,.17)!important;color:#ffd8d5!important;box-shadow:0 0 0 1px rgba(255,95,87,.18),0 0 12px rgba(255,95,87,.14)!important}
#routeMiniToolbar .tak-route-cancel-v491:hover{background:rgba(255,95,87,.28)!important;color:#fff!important}
#routeMiniToolbar .tak-route-cancel-v491 svg{stroke:currentColor!important;fill:none!important;stroke-width:2.4!important;stroke-linecap:round!important}
#routeMiniToolbar .tak-route-clear-v491{border-color:rgba(255,204,102,.55)!important}
.tak-measure-preview-pane-v491{z-index:625!important;pointer-events:none!important}.tak-measure-preview-halo-v491{stroke:#061019!important;stroke-opacity:.94!important;stroke-width:7px!important;stroke-dasharray:10 8!important;stroke-linecap:round!important;pointer-events:none!important}.tak-measure-live-preview-v491{stroke-dasharray:10 8!important;stroke-linecap:round!important;filter:drop-shadow(0 0 3px rgba(255,255,255,.42));pointer-events:none!important}.measure-preview-seg-label-v491{display:block;width:max-content;padding:3px 6px;border:1px dashed currentColor;border-radius:7px;background:rgba(6,10,14,.94);font-size:.68rem;font-weight:850;line-height:1.1;white-space:nowrap;box-shadow:0 2px 8px rgba(0,0,0,.42);transform:translate(5px,-5px)}
.tak-color-picker-v491{position:fixed;z-index:21040;width:238px;padding:10px;border:1px solid rgba(255,111,46,.45);border-radius:13px;background:linear-gradient(180deg,rgba(17,26,35,.99),rgba(7,12,18,.99));box-shadow:0 20px 55px rgba(0,0,0,.65);color:#dce6ea}.tak-color-picker-grid-v491{display:grid;grid-template-columns:repeat(8,1fr);gap:6px}.tak-color-swatch-v491{width:21px!important;height:21px!important;min-width:21px!important;min-height:21px!important;margin:0!important;padding:0!important;border:1px solid rgba(255,255,255,.32)!important;border-radius:6px!important;background:var(--swatch)!important;box-shadow:inset 0 0 0 1px rgba(0,0,0,.28)!important}.tak-color-swatch-v491:hover,.tak-color-swatch-v491:focus-visible{outline:2px solid #fff!important;outline-offset:1px!important}.tak-color-picker-custom-v491{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:7px;margin-top:9px}.tak-color-picker-custom-v491 input{width:100%;min-width:0;padding:6px 8px;border:1px solid #3b4b57;border-radius:8px;background:#091018;color:#eef5f8;font:700 .72rem ui-monospace,SFMono-Regular,Consolas,monospace;text-transform:uppercase}.tak-color-picker-custom-v491 button{margin:0!important;padding:6px 9px!important;border:1px solid rgba(255,111,46,.55)!important;border-radius:8px!important;background:rgba(255,111,46,.15)!important;color:#ffd8c5!important;font-size:.7rem!important;font-weight:850!important}
.panel.collapsed #basemapCacheControlsV462,.panel.collapsed #basemapCacheControlsV463,.panel.collapsed #basemapCacheControlsV480,.panel.collapsed #basemapCacheControlsV486,.panel.is-collapsed #basemapCacheControlsV462,.panel.is-collapsed #basemapCacheControlsV463,.panel.is-collapsed #basemapCacheControlsV480,.panel.is-collapsed #basemapCacheControlsV486{display:none!important;visibility:hidden!important}
`;
  d.head.appendChild(st)
}
function suppressToolStatus(){
  for(const id of ['mapStatus','toolStatus']){
    const el=$(id);if(!el)continue;
    el.setAttribute('aria-hidden','true');el.hidden=true;el.style.display='none';S.statusSuppressions++
  }
}
function updateCursor(){
  const el=mapContainer();if(!el)return false;
  const on=creationTool();
  el.classList.toggle('tak-create-crosshair-v491',on);
  el.classList.remove('tak-create-crosshair-v480','tak-create-crosshair-v482');
  el.dataset.takCreationCursorV486=on?'crosshair':'default';
  S.cursorUpdates++;
  if(currentTool()!=='route')clearRoutePreview();
  if(currentTool()!=='measure')clearMeasurePreview();
  S.lastTool=currentTool();
  return on
}
function routeState(){try{return w.v233RouteState||null}catch(_){return null}}
function routeColor(){const st=routeState()||{};return String(($('routeColorInput')||{}).value||st.color||'#ff6f2e')}
function routeDashed(){const st=routeState()||{};return String(($('routeStyleInput')||{}).value||st.style||'solid')==='dashed'}
function measurePointsRef(){try{if(typeof measurePoints!=='undefined'&&Array.isArray(measurePoints))return measurePoints}catch(_){}try{return Array.isArray(w.measurePoints)?w.measurePoints:[]}catch(_){return[]}}
function measureLockedNow(){try{if(typeof measureLocked!=='undefined')return Boolean(measureLocked)}catch(_){}try{return Boolean(w.measureLocked)}catch(_){return false}}
function measureLayerObj(){try{if(typeof measureLayer!=='undefined'&&measureLayer)return measureLayer}catch(_){}return w.measureLayer||null}
function measureLineColorNow(){try{if(typeof measureLineColor!=='undefined')return String(measureLineColor||'#b9c4c9')}catch(_){}return String(w.measureLineColor||'#b9c4c9')}
function measureTextColorNow(){try{if(typeof measureTextColor!=='undefined')return String(measureTextColor||'#c6d0d5')}catch(_){}return String(w.measureTextColor||'#c6d0d5')}
function measureUnitsNow(){try{if(typeof measureUnitsMode!=='undefined')return String(measureUnitsMode||'all')}catch(_){}return String(w.measureUnitsMode||'all')}
function removeLayer(layer){if(!layer)return;const m=mapObj(),group=measureLayerObj();try{if(group&&group.removeLayer)group.removeLayer(layer)}catch(_){}try{if(m&&m.removeLayer)m.removeLayer(layer)}catch(_){}try{if(layer.remove)layer.remove()}catch(_){} }
function clearRoutePreview(){if(S.routePreview){removeLayer(S.routePreview);S.routePreview=null}if(currentTool()==='route')S.lastPointer=null}
function clearMeasurePreview(){if(S.measurePreviewHalo){removeLayer(S.measurePreviewHalo);S.measurePreviewHalo=null}if(S.measurePreviewLine){removeLayer(S.measurePreviewLine);S.measurePreviewLine=null}if(S.measurePreviewLabel){removeLayer(S.measurePreviewLabel);S.measurePreviewLabel=null}if(currentTool()==='measure')S.lastPointer=null}
function drawRoutePreview(latlng){
  const m=mapObj(),st=routeState();
  if(!m||!w.L||currentTool()!=='route'||!st||!Array.isArray(st.points)||!st.points.length||!latlng){clearRoutePreview();return false}
  const last=st.points[st.points.length-1];if(!last){clearRoutePreview();return false}
  if(!S.routePreview){
    S.routePreview=w.L.polyline([last,latlng],{color:routeColor(),weight:3,opacity:.76,dashArray:routeDashed()?'8 7':'5 7',interactive:false,className:'tak-route-live-preview-v491'}).addTo(m)
  }else{
    try{S.routePreview.setLatLngs([last,latlng]);S.routePreview.setStyle({color:routeColor(),dashArray:routeDashed()?'8 7':'5 7'})}
    catch(_){clearRoutePreview();return drawRoutePreview(latlng)}
  }
  S.lastPointer=latlng;S.routePreviewUpdates++;return true
}
function formatMeasureDistance(meters){
  const mode=measureUnitsNow();
  try{if(typeof fmtDistance==='function')return String(fmtDistance(meters,mode))}catch(_){}
  try{if(typeof w.fmtDistance==='function')return String(w.fmtDistance(meters,mode))}catch(_){}
  if(mode==='metric')return meters>=1000?(meters/1000).toFixed(2)+' km':Math.round(meters)+' m';
  if(mode==='imperial')return meters>=1609.344?(meters/1609.344).toFixed(2)+' mi':Math.round(meters*3.280839895)+' ft';
  return (meters/1609.344).toFixed(2)+' mi · '+Math.round(meters*3.280839895)+' ft · '+(meters/1000).toFixed(2)+' km · '+Math.round(meters)+' m'
}
function layerAddTarget(layer){const group=measureLayerObj(),m=mapObj();if(group&&layer&&typeof layer.addTo==='function'){try{return layer.addTo(group)}catch(_){}}if(m&&layer&&typeof layer.addTo==='function'){try{return layer.addTo(m)}catch(_){}}return layer}
function ensureMeasurePreviewPane(){
  const m=mapObj();if(!m)return '';
  const name='takMeasurePreviewPaneV486';
  try{let pane=m.getPane&&m.getPane(name);if(!pane&&m.createPane)pane=m.createPane(name);if(pane){pane.classList.add('tak-measure-preview-pane-v491');pane.style.zIndex='625';pane.style.pointerEvents='none'}return pane?name:''}catch(_){return ''}
}
function addPreviewToMap(layer){const m=mapObj();if(!layer||!m)return layer;try{return layer.addTo(m)}catch(_){return layer}}
function drawMeasurePreview(latlng){
  const m=mapObj(),points=measurePointsRef();
  if(!m||!w.L||currentTool()!=='measure'||measureLockedNow()||!points.length||!latlng){clearMeasurePreview();return false}
  const last=points[points.length-1];if(!last){clearMeasurePreview();return false}
  const distance=typeof m.distance==='function'?Number(m.distance(last,latlng)):NaN;
  const pane=ensureMeasurePreviewPane(),common={pane:pane||undefined,interactive:false,dashArray:'10 8',lineCap:'round'};
  if(!S.measurePreviewHalo){
    S.measurePreviewHalo=addPreviewToMap(w.L.polyline([last,latlng],Object.assign({},common,{color:'#061019',weight:7,opacity:.94,className:'tak-measure-preview-halo-v491'})))
  }else{try{S.measurePreviewHalo.setLatLngs([last,latlng]);S.measurePreviewHalo.setStyle({dashArray:'10 8',weight:7,opacity:.94})}catch(_){removeLayer(S.measurePreviewHalo);S.measurePreviewHalo=null}}
  if(!S.measurePreviewLine){
    S.measurePreviewLine=addPreviewToMap(w.L.polyline([last,latlng],Object.assign({},common,{color:measureLineColorNow(),weight:4,opacity:1,className:'tak-measure-live-preview-v491'})))
  }else{
    try{S.measurePreviewLine.setLatLngs([last,latlng]);S.measurePreviewLine.setStyle({color:measureLineColorNow(),dashArray:'10 8',weight:4,opacity:1})}
    catch(_){removeLayer(S.measurePreviewLine);S.measurePreviewLine=null;return drawMeasurePreview(latlng)}
  }
  const mid=w.L.latLng?w.L.latLng((Number(last.lat)+Number(latlng.lat))/2,(Number(last.lng)+Number(latlng.lng))/2):{lat:(Number(last.lat)+Number(latlng.lat))/2,lng:(Number(last.lng)+Number(latlng.lng))/2};
  const text=Number.isFinite(distance)?formatMeasureDistance(distance):'';
  if(S.measurePreviewLabel){removeLayer(S.measurePreviewLabel);S.measurePreviewLabel=null}
  if(text&&w.L.marker&&w.L.divIcon){
    S.measurePreviewLabel=addPreviewToMap(w.L.marker(mid,{pane:pane||undefined,interactive:false,zIndexOffset:10035,icon:w.L.divIcon({className:'',html:'<div class="measure-preview-seg-label-v491" style="color:'+measureTextColorNow()+'">Next · '+text+'</div>',iconAnchor:[0,0]})}))
  }
  S.lastPointer=latlng;S.measurePreviewUpdates++;return true
}
function asMeasureDash(layer){try{return String(layer&&layer.options&&layer.options.dashArray||layer&&layer.opts&&layer.opts.dashArray||'')}catch(_){return ''}}
function measurePreviewPaneName(){try{return String(S.measurePreviewLine&&S.measurePreviewLine.options&&S.measurePreviewLine.options.pane||S.measurePreviewLine&&S.measurePreviewLine.opts&&S.measurePreviewLine.opts.pane||'')}catch(_){return ''}}
function syncRoutePreview(){
  if(currentTool()!=='route'){clearRoutePreview();return}
  const st=routeState();if(!st||!Array.isArray(st.points)||!st.points.length){clearRoutePreview();return}
  if(S.lastPointer)drawRoutePreview(S.lastPointer)
}
function syncMeasurePreview(){
  if(currentTool()!=='measure'||measureLockedNow()||!measurePointsRef().length){clearMeasurePreview();return}
  if(S.lastPointer)drawMeasurePreview(S.lastPointer)
}
function clearMeasureDraft(){
  clearMeasurePreview();
  let cleared=false;
  try{if(typeof w.measureClear==='function'){w.measureClear();cleared=true}else if(typeof measureClear==='function'){measureClear();cleared=true}}catch(_){}
  if(!cleared){
    try{measurePoints=[];measureLocked=false;if(typeof drawMeasure==='function')drawMeasure();cleared=true}catch(_){}
    try{w.measurePoints=[];w.measureLocked=false;if(typeof w.drawMeasure==='function')w.drawMeasure();cleared=true}catch(_){}
  }
  S.measureDraftClears++;return cleared
}
function closeRoutePanel(){try{const p=$('routeEditPanel');if(p)p.classList.remove('active')}catch(_){} }
function cancelRoute(){
  try{
    if(typeof w.v233ClearRoute==='function')w.v233ClearRoute();
    else{const st=routeState();if(st){st.points=[];removeLayer(st.layer);removeLayer(st.hitLayer);st.layer=null;st.hitLayer=null}}
  }catch(_){}
  clearRoutePreview();closeRoutePanel();
  try{if(typeof w.setActiveMapTool==='function')w.setActiveMapTool('move');else if(typeof setActiveMapTool==='function')setActiveMapTool('move')}
  catch(_){try{w.activeMapTool='move'}catch(__){}}
  updateCursor();return false
}
function installRouteButtons(){
  const bar=$('routeMiniToolbar');if(!bar)return false;
  let cancel=bar.querySelector('.tak-route-cancel-v491');
  if(!cancel){
    cancel=Array.from(bar.querySelectorAll('button')).find(btn=>/cancel/i.test(String(btn.title||btn.textContent||''))||/setActiveMapTool\(['"]move/.test(String(btn.getAttribute('onclick')||'')));
    if(cancel){
      cancel.classList.remove('tak-route-cancel-v480','tak-route-cancel-v482');cancel.classList.add('tak-route-cancel-v491');cancel.removeAttribute('onclick');cancel.type='button';
      cancel.title='Cancel Route — discard the draft and exit Route Creation';cancel.setAttribute('aria-label','Cancel Route — discard draft and exit');
      cancel.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg><span class="tool-label">Cancel Route</span>';
      cancel.addEventListener('click',function(ev){try{ev.preventDefault();ev.stopPropagation()}catch(_){}cancelRoute()});S.routeCancelInstalls++
    }
  }
  const clear=Array.from(bar.querySelectorAll('button')).find(btn=>btn!==cancel&&/clear route|clear|start over/i.test(String(btn.title||btn.textContent||'')));
  if(clear){clear.classList.remove('tak-route-clear-v480','tak-route-clear-v482');clear.classList.add('tak-route-clear-v491');clear.title='Start Over — remove all route points and keep Route Creation active';clear.setAttribute('aria-label','Start Over — clear route points but stay in Route Creation')}
  return !!cancel
}
function basemapPanel(){return qa('.panel').find(p=>{const h=q(':scope > h2',p)||q('h2',p);return h&&/^Basemap$/i.test(String(h.textContent||'').replace(/[▸▾]/g,'').trim())})||null}
function basemapControls(){return $('basemapCacheControlsV462')||$('basemapCacheControlsV463')||$('basemapCacheControlsV480')||$('basemapCacheControlsV486')}
function repairBasemapPrecache(){
  const panel=basemapPanel(),controls=basemapControls();if(!panel||!controls)return false;
  const collapsed=panel.classList.contains('collapsed')||panel.classList.contains('is-collapsed')||panel.getAttribute('aria-expanded')==='false';
  controls.hidden=collapsed;controls.setAttribute('aria-hidden',collapsed?'true':'false');
  controls.style.display=collapsed?'none':'';controls.style.visibility=collapsed?'hidden':'';
  S.basemapSyncs++;return true
}
function bindBasemapHeader(){
  if(S.basemapHeaderBound)return;
  S.basemapHeaderBound=true;
  d.addEventListener('click',function(ev){
    try{const header=ev.target&&ev.target.closest&&ev.target.closest('.panel > h2,.tak-card-header-v480,.tak-card-header-v491');if(!header)return;const panel=header.closest('.panel');if(panel!==basemapPanel())return;setTimeout(repairBasemapPrecache,0)}catch(_){}
  },false)
}
function wrapFunction(name,after){
  try{
    const old=w[name];if(typeof old!=='function'||old.__takToolUxV486)return false;
    const wrapped=function(){const out=old.apply(this,arguments);try{after.apply(this,arguments)}catch(_){}return out};
    wrapped.__takToolUxV486=true;wrapped.__takToolUxOriginal=old;w[name]=wrapped;return true
  }catch(_){return false}
}
function wrapToolSwitch(){
  try{
    const old=w.setActiveMapTool;if(typeof old!=='function'||old.__takToolUxV486)return false;
    const wrapped=function(tool){const before=currentTool(),next=String(tool||'move');if(before==='measure'&&next!=='measure')clearMeasureDraft();const out=old.apply(this,arguments);setTimeout(function(){updateCursor();syncRoutePreview();syncMeasurePreview();suppressToolStatus();installRouteButtons()},0);return out};
    wrapped.__takToolUxV486=true;wrapped.__takToolUxOriginal=old;w.setActiveMapTool=wrapped;return true
  }catch(_){return false}
}
function installWrappers(){
  if(S.toolWrappers)return;
  wrapToolSwitch();
  wrapFunction('toggleMapTool',function(){setTimeout(function(){updateCursor();syncRoutePreview();syncMeasurePreview();suppressToolStatus()},0)});
  wrapFunction('v233StartDraw',function(){setTimeout(updateCursor,0)});
  wrapFunction('v233RouteMapClick',function(){setTimeout(syncRoutePreview,0)});
  wrapFunction('v233UndoRoute',function(){setTimeout(syncRoutePreview,0)});
  wrapFunction('v233ClearRoute',function(){clearRoutePreview()});
  wrapFunction('v233FinishRoute',function(){setTimeout(function(){clearRoutePreview();updateCursor()},0)});
  wrapFunction('measureAddPoint',function(){setTimeout(syncMeasurePreview,0)});
  wrapFunction('measureUndo',function(){setTimeout(syncMeasurePreview,0)});
  wrapFunction('measureClear',function(){clearMeasurePreview()});
  wrapFunction('measureLock',function(){clearMeasurePreview()});
  wrapFunction('measureResume',function(){setTimeout(syncMeasurePreview,0)});
  wrapFunction('measureUnitsToggle',function(){setTimeout(syncMeasurePreview,0)});
  wrapFunction('setMeasureLineColor',function(){setTimeout(syncMeasurePreview,0)});
  wrapFunction('setMeasureTextColor',function(){setTimeout(syncMeasurePreview,0)});
  wrapFunction('togglePanelCollapse',function(){setTimeout(repairBasemapPrecache,0)});
  S.toolWrappers=true
}
function bindKeyboard(){
  if(S.keyBound)return;S.keyBound=true;
  d.addEventListener('keydown',function(event){
    if(event.key!=='Escape'||currentTool()!=='measure')return;
    const target=event.target;try{if(target&&target.closest&&target.closest('.tak-delete-dialog-overlay-v491'))return}catch(_){}
    if(measurePointsRef().length||S.measurePreviewLine||S.measurePreviewLabel){try{event.preventDefault();event.stopPropagation();event.stopImmediatePropagation()}catch(_){}clearMeasureDraft();updateCursor()}
  },true)
}
const COLOR_SWATCHES=['#ff6f2e','#ff3b30','#ff9500','#ffcc00','#77d95b','#39d98a','#00c7be','#32ade6','#2386ff','#5856d6','#a979ff','#b56cff','#ff2d55','#ffffff','#d1d8dc','#91a2ad','#606b73','#202a31','#000000','#8b5a2b','#7a4eab','#0f6b3d','#0f4c81','#7a1f1f'];
function closeColorPicker(){const box=$('takMapColorPickerV486');if(box)box.remove();S.colorPickerInput=null}
function applyColor(input,value){value=String(value||'').trim();if(!/^#[0-9a-f]{6}$/i.test(value)||!input)return false;input.value=value;try{input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}))}catch(_){}S.colorPickerCloses++;closeColorPicker();try{input.focus({preventScroll:true})}catch(_){}return true}
function openColorPicker(input){if(!input)return false;closeColorPicker();S.colorPickerInput=input;const box=d.createElement('div');box.id='takMapColorPickerV486';box.className='tak-color-picker-v491';box.setAttribute('role','dialog');box.setAttribute('aria-label','Choose color');box.innerHTML='<div class="tak-color-picker-grid-v491">'+COLOR_SWATCHES.map(color=>'<button type="button" class="tak-color-swatch-v491" data-color="'+color+'" style="--swatch:'+color+'" aria-label="Use '+color+'"></button>').join('')+'</div><div class="tak-color-picker-custom-v491"><input data-color-hex value="'+String(input.value||'#ff6f2e').toUpperCase()+'" maxlength="7" aria-label="Custom hex color"><button type="button" data-color-apply>Apply</button></div>';
  d.body.appendChild(box);const r=input.getBoundingClientRect(),br=box.getBoundingClientRect();let left=Math.min(Math.max(8,r.left),Math.max(8,w.innerWidth-br.width-8)),top=r.bottom+7;if(top+br.height>w.innerHeight-8)top=Math.max(8,r.top-br.height-7);box.style.left=left+'px';box.style.top=top+'px';
  box.addEventListener('click',event=>{const sw=event.target.closest('[data-color]');if(sw){event.preventDefault();applyColor(input,sw.dataset.color);return}if(event.target.closest('[data-color-apply]')){event.preventDefault();applyColor(input,(box.querySelector('[data-color-hex]')||{}).value)}});
  box.addEventListener('keydown',event=>{if(event.key==='Escape'){event.preventDefault();closeColorPicker();input.focus()}else if(event.key==='Enter'&&event.target.matches('[data-color-hex]')){event.preventDefault();applyColor(input,event.target.value)}});
  setTimeout(()=>{const current=box.querySelector('[data-color="'+String(input.value||'').toLowerCase()+'"]')||box.querySelector('[data-color]');current&&current.focus()},0);S.colorPickerOpens++;return true
}
function bindColorPickers(){
  if(S.colorPickerBound)return;S.colorPickerBound=true;
  d.addEventListener('click',event=>{const input=event.target&&event.target.closest&&event.target.closest('input[type="color"]');if(input){try{event.preventDefault();event.stopPropagation();event.stopImmediatePropagation()}catch(_){}openColorPicker(input);return}if(!event.target.closest||!event.target.closest('#takMapColorPickerV486'))closeColorPicker()},true);
  d.addEventListener('keydown',event=>{const input=event.target;if(input&&input.matches&&input.matches('input[type="color"]')&&(event.key==='Enter'||event.key===' ')){event.preventDefault();openColorPicker(input)}else if(event.key==='Escape'&&$('takMapColorPickerV486')){event.preventDefault();closeColorPicker()}},true)
}
function bindMap(){
  const m=mapObj();if(!m||!m.on)return false;S.map=m;
  if(!m.__takToolUxMousemoveV486){
    m.__takToolUxMousemoveV486=true;
    m.on('mousemove',function(ev){if(currentTool()==='route')drawRoutePreview(ev&&ev.latlng);else if(currentTool()==='measure')drawMeasurePreview(ev&&ev.latlng)});
    m.on('click',function(){setTimeout(function(){syncRoutePreview();syncMeasurePreview();updateCursor();suppressToolStatus()},0)});
    m.on('mouseout',function(){if(currentTool()==='route')clearRoutePreview();if(currentTool()==='measure')clearMeasurePreview()});
    S.mousemoveBound=true
  }
  return true
}
function boot(){S.boots++;installCss();suppressToolStatus();installWrappers();bindMap();bindKeyboard();bindColorPickers();installRouteButtons();bindBasemapHeader();repairBasemapPrecache();updateCursor()}
const api=Object.freeze({
  version:VERSION,boot,cancelRoute,updateCursor,drawRoutePreview,clearRoutePreview,drawMeasurePreview,clearMeasurePreview,clearMeasureDraft,repairBasemapPrecache,
  diagnostics:function(){
    const panel=basemapPanel(),controls=basemapControls(),bar=$('routeMiniToolbar'),container=mapContainer();
    return {version:VERSION,tool:currentTool(),crosshairActive:!!(container&&container.classList.contains('tak-create-crosshair-v491')),routeCancelInstalled:!!(bar&&bar.querySelector('.tak-route-cancel-v491')),routeCancelLabel:bar&&bar.querySelector('.tak-route-cancel-v491')&&bar.querySelector('.tak-route-cancel-v491').getAttribute('aria-label')||'',routePreviewActive:!!S.routePreview,measurePreviewActive:!!S.measurePreviewLine,measurePreviewHaloActive:!!S.measurePreviewHalo,measurePreviewLabelActive:!!S.measurePreviewLabel,measurePreviewDashArray:asMeasureDash(S.measurePreviewLine),measurePreviewDirectMap:!!(S.measurePreviewLine&&S.measurePreviewLine.target===mapObj()),measurePreviewInMeasureLayer:!!(S.measurePreviewLine&&S.measurePreviewLine.target===measureLayerObj()),measurePreviewPane:measurePreviewPaneName(),routePointCount:(routeState()&&routeState().points||[]).length,measurePointCount:measurePointsRef().length,mapStatusHidden:!!($('mapStatus')&&($('mapStatus').hidden||getComputedStyle($('mapStatus')).display==='none')),basemapPanelCollapsed:!!(panel&&(panel.classList.contains('collapsed')||panel.classList.contains('is-collapsed'))),basemapPrecacheHidden:!!(controls&&(controls.hidden||getComputedStyle(controls).display==='none')),boots:S.boots,statusSuppressions:S.statusSuppressions,cursorUpdates:S.cursorUpdates,routePreviewUpdates:S.routePreviewUpdates,measurePreviewUpdates:S.measurePreviewUpdates,measureDraftClears:S.measureDraftClears,routeCancelInstalls:S.routeCancelInstalls,basemapSyncs:S.basemapSyncs,colorPickerCloses:S.colorPickerCloses,colorPickerOpens:S.colorPickerOpens,customColorPicker:!!$('takMapColorPickerV486'),documentWideObserver:false,classAttributeObserver:false}
  }
});
w.TakMapToolUxV486=api;w.TakMapToolUxV482=api;w.TakMapToolUxV480=api;
if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',function(){setTimeout(boot,120)},{once:true});else setTimeout(boot,120);
[500,1200,3000,6500,9000].forEach(ms=>setTimeout(boot,ms));
})(window,document);
