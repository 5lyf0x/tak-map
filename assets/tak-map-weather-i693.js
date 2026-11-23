/* TAK Map i693: same-origin NWS radar, independent NWS alerts. Preserves i691 settings/UI. */
(()=>{'use strict';
const W=window,D=document,KEY='tak-map-native-weather-i691';
const STATUS='/api/tak-map/weather/radar/status-i693';
const TILES='/api/tak-map/weather/radar/tile-i693';
const state={radar:false,alerts:false,opacity:55,radarLayer:null,alertLayer:null,cesRadar:null,cesAlerts:null,viewer:null,map:null,
 radarPendingLayer:null,radarActiveToken:null,radarStaleAt:0,radarFrameSource:null,radarNativeReady:false,cesRadarRetiring:null,
 lastAlerts:0,lastRadar:0,alertPending:false,radarPending:false,alertSeq:0,radarSeq:0,mode3d:false,
 radarStatus:'Off',alertStatus:'Off',alertsData:[],radarValid:null,radarProvider:null,radarToken:null,
 radarTileLoaded:0,radarTileErrors:0,radarNativeMaxZoom:10,historyMode:false};
try{const saved=JSON.parse(localStorage.getItem(KEY)||'{}');state.radar=saved.radar===true;state.alerts=saved.alerts===true;state.opacity=Math.max(0,Math.min(100,Number(saved.opacity??55)||0))}catch(_){}
function save(){try{localStorage.setItem(KEY,JSON.stringify({radar:state.radar,alerts:state.alerts,opacity:state.opacity}))}catch(_){}}
const $=id=>D.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function status(id,msg){const el=$(id);if(el)el.textContent=msg}
// Reuse the BASEMAP Soft Pill track/thumb and percentage behavior; no weather-only range styling.
function syncOpacitySlider(slider){
 if(!slider)return;
 slider.value=String(state.opacity);
 slider.style.setProperty('--tak-soft-pill-pct',state.opacity+'%');
 const output=$('takWeatherOpacityOutI694');if(output)output.textContent=state.opacity+'%';
}
function setRadarOpacity(value){
 const n=Number(value);if(!Number.isFinite(n))return;
 state.opacity=Math.min(100,Math.max(0,Math.round(n)));
 syncOpacitySlider($('takWeatherOpacitySoftPillI694'));
 const alpha=state.opacity/100;
 // Direct alpha changes on both active and staging frames; never recreate or refetch tiles.
 for(const layer of [state.radarLayer,state.radarPendingLayer])if(layer)layer.setOpacity(alpha);
 for(const layer of [state.cesRadar,state.cesRadarRetiring])if(layer)layer.alpha=alpha;
 // Cesium may use request-render mode. This requests a scene render, not new imagery.
 try{state.viewer?.scene?.requestRender?.()}catch(_){}
}
// Upgrade weather panels already present after an in-place update. An i691/i692/i693
// panel uses the old flat range slider, and the previous mount() early return left it
// untouched. Reconcile in place, preserving weather settings and alert DOM.
function ensureRadarOpacityControl(panel){
 const settings=panel.querySelector('#takWeatherRadarSettingsI691');if(!settings)return null;
 let slider=settings.querySelector('#takWeatherOpacitySoftPillI694');
 let label=settings.querySelector('label');
 let row=settings.querySelector('.tak-weather-opacity-row-i694');
 let output=settings.querySelector('#takWeatherOpacityOutI694')||settings.querySelector('#takWeatherOpacityOutI691');
 const legacy=settings.querySelector('#takWeatherOpacityI691');
 if(!row){row=D.createElement('div');row.className='tak-weather-opacity-row-i694';
  if(label)label.insertAdjacentElement('afterend',row);else settings.insertBefore(row,settings.firstChild)}
 if(!slider){slider=D.createElement('input');slider.id='takWeatherOpacitySoftPillI694';slider.type='range';
  slider.min='0';slider.max='100';slider.step='1';slider.setAttribute('aria-label','Radar opacity')}
 slider.classList.add('tak-soft-pill-i678');
 if(slider.parentElement!==row)row.prepend(slider);
 if(legacy&&legacy!==slider)legacy.remove();
 if(!output){output=D.createElement('output')}
 output.id='takWeatherOpacityOutI694';output.setAttribute('for',slider.id);
 if(output.parentElement!==row)row.append(output);
 if(!label){label=D.createElement('label');row.insertAdjacentElement('beforebegin',label)}
 label.htmlFor=slider.id;
 if(label.textContent.trim()!=='Opacity')label.textContent='Opacity';
 syncOpacitySlider(slider);
 if(slider.dataset.takWeatherOpacityBoundI695!=='1'){
  slider.dataset.takWeatherOpacityBoundI695='1';
  slider.addEventListener('input',()=>setRadarOpacity(slider.value));
  slider.addEventListener('change',save);
 }
 return slider;
}
function mount(){let panel=$('takNativeWeatherI691');
 if(!panel){const stack=$('takBasemapBlendI673'),sel=$('basemapSelect');if(!stack&&!sel)return false;
  panel=D.createElement('section');panel.id='takNativeWeatherI691';panel.className='tak-weather-i691';
 panel.innerHTML=`<button class="tak-weather-head-i691" type="button" aria-expanded="true">WEATHER OVERLAYS <span>⌃</span></button><div class="tak-weather-body-i691"><label class="tak-weather-row-i691"><span>Radar Reflectivity<small>NOAA/NWS · MRMS</small></span><input id="takWeatherRadarI691" type="checkbox"></label><div id="takWeatherRadarSettingsI691" class="tak-weather-sub-i691"><label for="takWeatherOpacitySoftPillI694">Opacity</label><div class="tak-weather-opacity-row-i694"><input id="takWeatherOpacitySoftPillI694" class="tak-soft-pill-i678" type="range" min="0" max="100" step="1" value="55" style="--tak-soft-pill-pct:55%" aria-label="Radar opacity"><output id="takWeatherOpacityOutI694" for="takWeatherOpacitySoftPillI694">55%</output></div><small id="takWeatherRadarStatusI691" role="status">Off</small></div><label class="tak-weather-row-i691"><span>Weather Alerts<small>NWS watches · warnings · advisories</small></span><input id="takWeatherAlertsI691" type="checkbox"></label><div id="takWeatherAlertSettingsI691" class="tak-weather-sub-i691"><div class="tak-weather-legend-i691"><i style="background:#ed5b58"></i>Extreme <i style="background:#ed9a54"></i>Severe <i style="background:#e8cf66"></i>Moderate</div><small id="takWeatherAlertStatusI691" role="status">Off</small></div><small class="tak-weather-credit-i691">Weather data © NOAA / National Weather Service</small></div>`;
  (stack||sel).insertAdjacentElement('afterend',panel);
 }
 const radar=panel.querySelector('#takWeatherRadarI691'),alerts=panel.querySelector('#takWeatherAlertsI691');
 if(!radar||!alerts)return false;
 ensureRadarOpacityControl(panel);
 if(panel.dataset.takWeatherControlsBoundI695!=='1'){
  panel.dataset.takWeatherControlsBoundI695='1';
  radar.checked=state.radar;alerts.checked=state.alerts;
  radar.addEventListener('change',()=>{state.radar=radar.checked;state.radarSeq++;if(!state.radar){state.historyMode=false;W.TakMapRadarHistoryI696?.stop?.();state.radarToken=null;state.radarStatus='Off';state.lastRadar=0;clearRadar2D();clearRadar3D()}save();apply()});
  alerts.addEventListener('change',()=>{state.alerts=alerts.checked;state.alertSeq++;save();apply()});
  const head=panel.querySelector('.tak-weather-head-i691');
  if(head)head.addEventListener('click',e=>{const body=panel.querySelector('.tak-weather-body-i691');const hidden=body.hidden=!body.hidden;e.currentTarget.setAttribute('aria-expanded',String(!hidden));e.currentTarget.querySelector('span').textContent=hidden?'⌄':'⌃'});
 }
 return true;
}
function mapRef(){return W.takLeafletMap||W.map||null}
function in3D(){try{return typeof terrain3DActive!=='undefined'&&!!terrain3DActive&&typeof terrain3DViewer!=='undefined'&&!!terrain3DViewer&&!!W.Cesium}catch(_){return false}}
function viewer3D(){try{return typeof terrain3DViewer!=='undefined'?terrain3DViewer:null}catch(_){return null}}
function panes(m){if(!m.getPane('takWeatherRadarI691'))m.createPane('takWeatherRadarI691');const rp=m.getPane('takWeatherRadarI691');rp.style.zIndex='270';rp.style.pointerEvents='none';if(!m.getPane('takWeatherAlertI691'))m.createPane('takWeatherAlertI691');const ap=m.getPane('takWeatherAlertI691');ap.style.zIndex='430'}
function radarURL(token){const historical=/^h\d{13}_[a-f0-9]{16}$/.test(token);return (historical?'/api/tak-map/weather/radar/history-tile-i696':TILES)+'/{z}/{x}/{y}.png?frame='+encodeURIComponent(token)}
function frameSuffix(){return state.radarFrameSource==='time_range_provisional'?' · time unverified':''}
function cancelLayer(layer){if(!layer)return;const ledger=layer._takLedger;if(ledger)for(const item of ledger.values())if(item.timer)clearTimeout(item.timer);if(ledger)ledger.clear()}
function clearRadar2D(){const m=state.map;for(const l of [state.radarLayer,state.radarPendingLayer]){cancelLayer(l);if(m&&l&&m.hasLayer(l))m.removeLayer(l)}state.radarLayer=null;state.radarPendingLayer=null;state.radarActiveToken=null}
function clearRadar3D(){if(state.viewer)for(const layer of [state.cesRadar,state.cesRadarRetiring])if(layer)try{state.viewer.imageryLayers.remove(layer,true)}catch(_){}state.cesRadar=null;state.cesRadarRetiring=null;state.cesRadarToken=null}
function clear2D(){clearRadar2D();if(state.map&&state.alertLayer&&state.map.hasLayer(state.alertLayer))state.map.removeLayer(state.alertLayer);state.alertLayer=null}
function clear3D(){clearRadar3D();if(state.viewer&&state.cesAlerts)try{state.viewer.dataSources.remove(state.cesAlerts,true)}catch(_){}state.cesAlerts=null}
function hasRouteInteraction(){try{return !!(W.TakMapRouteCreationActive||D.body.classList.contains('route-creation-active')||(typeof activeMapTool!=='undefined'&&activeMapTool==='route')||$('toolRoute')?.classList.contains('active'))}catch(_){return false}}
function eventHtml(f){const p=f.properties||{};const when=s=>s?new Date(s).toLocaleString():'Not reported';const url=String(p['@id']||p.id||f.id||'');const safeUrl=/^https:\/\/(api\.weather\.gov|www\.weather\.gov)\//.test(url)?`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">Original NWS alert</a>`:'';return `<div class="tak-weather-popup-i691"><b>${esc(p.event||'Weather alert')}</b><p>${esc(p.headline||p.areaDesc||'')}</p><small>Severity: ${esc(p.severity||'Unknown')} · Ends: ${esc(when(p.ends||p.expires))}</small><p>${esc((p.description||'').slice(0,2400))}</p>${safeUrl}</div>`}
function alertStyle(f){const sev=String(f.properties?.severity||'').toLowerCase();const c=sev==='extreme'?'#ed5b58':sev==='severe'?'#ed9a54':sev==='moderate'?'#e8cf66':sev==='minor'?'#66b7ef':'#a2abb5';return {color:c,weight:2,opacity:.92,fillColor:c,fillOpacity:.14,interactive:true}}
function frameLabel(){return state.radarValid?'frame '+new Date(state.radarValid).toLocaleTimeString():'observation time not provided'}
function radarMessage(loaded){const provider=state.radarProvider==='nws-latest'?' · fallback source':'';return (loaded?'Radar ready · ':'Loading radar · ')+frameLabel()+provider+frameSuffix()}
function layerCounts(layer){
 const rows=layer?Array.from(layer._takLedger?.values()||[]):[];
 const tally={total:rows.length,loaded:0,failed:0,retrying:0,pending:0};
 for(const row of rows){if(row.state==='loaded')tally.loaded++;else if(row.state==='failed')tally.failed++;else if(row.state==='retrying')tally.retrying++;else tally.pending++}
 return tally;
}
function radarCoverageStatus(layer){const n=layerCounts(layer);if(!n.total)return 'Loading radar · '+frameLabel()+frameSuffix();
 if(n.failed)return `Radar partial · ${n.loaded}/${n.total} tiles · ${n.failed} failed`+frameSuffix();
 if(n.retrying)return `Radar recovering · ${n.loaded}/${n.total} tiles`+frameSuffix();
 if(n.pending)return `Loading radar · ${n.loaded}/${n.total} tiles`+frameSuffix();
 return `Radar ready · ${n.loaded}/${n.total} tiles · ${frameLabel()}`+frameSuffix();
}
function updateRadarFromLayer(layer){if(!state.radar||!layer)return;
 if(layer===state.radarPendingLayer){
  const n=layerCounts(layer),elapsed=Date.now()-(layer._takStarted||Date.now());
  // A few early-loaded tiles are not a complete radar frame. Leaflet 'load'
  // signals the viewport batch settled, including errors; keep old imagery
  // until most tiles actually succeeded and previously covered areas remain covered.
  const old=state.radarLayer,oldLedger=old?._takLedger;
  let oldCovered=0,newCovered=0;
  if(oldLedger)for(const [key,oldTile] of oldLedger){
   if(oldTile.state!=='loaded'||!layer._takLedger.has(key))continue;
   oldCovered++;if(layer._takLedger.get(key)?.state==='loaded')newCovered++;
  }
  const ratio=n.total?n.loaded/n.total:0;
  const coverage=oldCovered?newCovered/oldCovered:1;
  // An early one-tile batch cannot displace a previously covered viewport.
  // Cap the historical sample so panning with keepBuffer does not block refresh.
  const oldSample=oldLedger?Math.min(12,Array.from(oldLedger.values()).filter(t=>t.state==='loaded').length):0;
  const enoughSamples=!oldSample||n.loaded>=Math.ceil(oldSample*.90);
  const threshold=elapsed>26000?.85:.92;
  if(layer._takBatchReady&&n.total&&enoughSamples&&ratio>=threshold&&coverage>=.90&&elapsed>=1400){promoteRadarLayer(layer)}
  else {state.radarStatus='Radar loading next frame · '+n.loaded+'/'+n.total+' tiles · retaining previous frame'+frameSuffix();updateLabels()}
  return;
 }
 if(layer!==state.radarLayer)return;
 state.radarStatus=radarCoverageStatus(layer);updateLabels();
}
function promoteRadarLayer(layer){if(layer!==state.radarPendingLayer)return;
 const old=state.radarLayer;
 state.radarLayer=layer;state.radarActiveToken=layer._takToken;
 state.radarPendingLayer=null;state.radarStaleAt=0;
 try{layer.setZIndex?.(2)}catch(_){}
 if(old&&old!==layer){cancelLayer(old);if(state.map?.hasLayer(old))state.map.removeLayer(old)}
 updateRadarFromLayer(layer);
}
function createRadarLayer(token){const m=state.map;if(!m||!W.L||!token)return null;
 const layer=W.L.tileLayer(radarURL(token),{opacity:state.opacity/100,pane:'takWeatherRadarI691',maxNativeZoom:state.radarNativeMaxZoom,maxZoom:24,updateWhenIdle:true,keepBuffer:2,attribution:'NOAA / NWS MRMS',crossOrigin:false});
 layer._takToken=token;layer._takStarted=Date.now();layer._takLedger=new Map();layer._takBatchReady=false;
 const id=(e)=>e?.coords?`${e.coords.z}/${e.coords.x}/${e.coords.y}`:null;
 layer.on('tileloadstart',e=>{const k=id(e);if(k){layer._takBatchReady=false;layer._takLedger.set(k,{state:'pending',tile:e.tile,attempt:0,timer:null});updateRadarFromLayer(layer)}});
 layer.on('tileload',e=>{const k=id(e);if(!k)return;const item=layer._takLedger.get(k);if(item){if(item.timer)clearTimeout(item.timer);item.state='loaded';state.radarTileLoaded++;updateRadarFromLayer(layer)}});
 layer.on('tileerror',e=>{const k=id(e);if(!k)return;const item=layer._takLedger.get(k);if(!item||item.state==='loaded'||item.state==='failed')return;
   if(layer._takToken!==state.radarToken){item.state='failed';return}
   if(item.attempt>=3){item.state='failed';state.radarTileErrors++;updateRadarFromLayer(layer);return}
   const delay=[1250,3400,8000][item.attempt++];item.state='retrying';updateRadarFromLayer(layer);
   item.timer=setTimeout(()=>{if(!layer._takLedger.has(k)||!state.radar)return;
     item.state='pending';updateRadarFromLayer(layer);
     // Retrying the same XYZ/frame only; attempt cannot alter the upstream URL.
     const url=layer.getTileUrl?layer.getTileUrl(e.coords):radarURL(token).replace('{z}',e.coords.z).replace('{x}',e.coords.x).replace('{y}',e.coords.y);
     e.tile.src=url+(url.includes('?')?'&':'?')+'attempt='+item.attempt;
   },delay);
 });
 layer.on('tileunload',e=>{const k=id(e);if(k){const item=layer._takLedger.get(k);if(item?.timer)clearTimeout(item.timer);layer._takLedger.delete(k);updateRadarFromLayer(layer)}});
 layer.on('load',()=>{layer._takBatchReady=true;setTimeout(()=>updateRadarFromLayer(layer),0)});
 return layer;
}
function loadRadar2D(){const m=state.map;if(!m||in3D()||!state.radar||!W.L||(!state.radarToken&&!state.radarLayer))return;
 if(!state.radarLayer){if(!state.radarToken)return;const layer=createRadarLayer(state.radarToken);if(!layer)return;state.radarLayer=layer;state.radarActiveToken=state.radarToken;layer.setZIndex?.(2);layer.addTo(m);return}
 if(!m.hasLayer(state.radarLayer))state.radarLayer.addTo(m);
 if(state.radarPendingLayer&&!m.hasLayer(state.radarPendingLayer))state.radarPendingLayer.addTo(m);
 if(state.radarToken&&state.radarActiveToken!==state.radarToken&&(!state.radarPendingLayer||state.radarPendingLayer._takToken!==state.radarToken)){
   if(state.radarPendingLayer){cancelLayer(state.radarPendingLayer);if(m.hasLayer(state.radarPendingLayer))m.removeLayer(state.radarPendingLayer)}
   const candidate=createRadarLayer(state.radarToken);if(!candidate)return;
   state.radarPendingLayer=candidate;candidate.setZIndex?.(1);candidate.addTo(m);
   state.radarStaleAt=Date.now();
 }
}
function draw2D(){const m=state.map;if(!m||in3D())return;panes(m);
 if(state.radar)loadRadar2D();else clearRadar2D();
 if(state.alerts&&state.alertsData.length){if(state.alertLayer&&m.hasLayer(state.alertLayer))m.removeLayer(state.alertLayer);const features=state.alertsData.filter(f=>f&&f.geometry);state.alertLayer=W.L.geoJSON({type:'FeatureCollection',features},{pane:'takWeatherAlertI691',style:alertStyle,onEachFeature:(f,l)=>l.on('click',e=>{if(hasRouteInteraction())return;W.L.DomEvent.stopPropagation(e);l.bindPopup(eventHtml(f),{maxWidth:360,maxHeight:360,autoPan:true}).openPopup(e.latlng)})});state.alertLayer.addTo(m)}else if(state.alertLayer&&m.hasLayer(state.alertLayer))m.removeLayer(state.alertLayer)
}
function loadRadar3D(){const v=state.viewer,C=W.Cesium;if(!v||!C||!in3D()||!state.radar||!state.radarToken)return;
 if(state.cesRadar&&state.cesRadarToken===state.radarToken)return;
 try{const token=state.radarToken;
  const imagery=new C.UrlTemplateImageryProvider({url:radarURL(token),tilingScheme:new C.WebMercatorTilingScheme(),tileWidth:256,tileHeight:256,maximumLevel:state.radarNativeMaxZoom,credit:'NOAA / NWS MRMS'});
  const old=state.cesRadar;
  const current=v.imageryLayers.addImageryProvider(imagery);current.alpha=state.opacity/100;
  state.cesRadar=current;state.cesRadarToken=token;
  // Retiring imagery remains visible temporarily during frame swaps and must share opacity.
  if(state.cesRadarRetiring&&state.cesRadarRetiring!==old){try{v.imageryLayers.remove(state.cesRadarRetiring,true)}catch(_){}}
  state.cesRadarRetiring=old||null;
  if(old){let checks=0;const retire=()=>{
    if(state.cesRadarRetiring!==old||state.viewer!==v||!state.radar)return;
    checks++;
    // Never remove a previously visible Cesium frame solely on a wall-clock
    // timer: an imagery request may be delayed or temporarily unavailable.
    if(checks>=3&&v.scene?.globe?.tilesLoaded){
      try{v.imageryLayers.remove(old,true)}catch(_){}state.cesRadarRetiring=null;
      return;
    }
    if(checks<90)setTimeout(retire,700);
  };setTimeout(retire,900)}
  state.radarStatus='3D radar loading · '+frameLabel()+frameSuffix();updateLabels();
 }catch(e){state.radarStatus='3D radar unavailable';updateLabels()}
}
async function draw3D(){const v=viewer3D(),C=W.Cesium;if(!in3D()||!v||!C)return;state.viewer=v;
 if(state.radar)loadRadar3D();else clearRadar3D();
 if(state.cesAlerts)try{v.dataSources.remove(state.cesAlerts,true)}catch(_){}state.cesAlerts=null;
 if(state.alerts&&state.alertsData.some(f=>f.geometry)){try{const source=await C.GeoJsonDataSource.load({type:'FeatureCollection',features:state.alertsData.filter(f=>f.geometry)},{clampToGround:true,stroke:C.Color.ORANGE,fill:C.Color.ORANGE.withAlpha(.12),strokeWidth:2});if(!in3D()||!state.alerts||v!==state.viewer)return;state.cesAlerts=await v.dataSources.add(source)}catch(e){state.alertStatus='3D alerts unavailable: '+String(e.message||e)}}updateLabels()
}
function updateLabels(){if($('takWeatherRadarSettingsI691'))$('takWeatherRadarSettingsI691').hidden=!state.radar;if($('takWeatherAlertSettingsI691'))$('takWeatherAlertSettingsI691').hidden=!state.alerts;status('takWeatherRadarStatusI691',state.radar?state.radarStatus:'Off');status('takWeatherAlertStatusI691',state.alerts?state.alertStatus:'Off')}
function changeRadarToken(token){if(state.radarToken===token)return;
 state.radarToken=token;
 if(!token){state.radarStatus=state.radarLayer?'Radar stale · provider unavailable':'Radar unavailable';if(!state.radarStaleAt)state.radarStaleAt=Date.now();return}
 if(in3D())loadRadar3D();else loadRadar2D();
}
async function refreshRadar(){if(!state.radar||state.radarPending||state.historyMode)return;state.radarPending=true;const seq=state.radarSeq;state.lastRadar=Date.now();
 try{const r=await fetch(STATUS,{credentials:'same-origin',cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);const d=await r.json();if(!state.radar||seq!==state.radarSeq)return;
  if(!d.ok||!d.frame_token){changeRadarToken(null);state.radarStatus=state.radarLayer?'Radar stale · provider unavailable':'Radar unavailable · '+String(d.error_code||'provider error');updateLabels();return}
  if(!/^[puf][0-9]{1,16}$/.test(d.frame_token))throw Error('Invalid frame token');
  state.radarProvider=d.provider_id;state.radarValid=d.valid_time_utc||null;state.radarFrameSource=d.frame_source||null;
  state.radarNativeMaxZoom=Number.isInteger(d.native_max_zoom)?d.native_max_zoom:10;
  const changed=d.frame_token!==state.radarToken;
  if(changed){state.radarStatus=radarMessage(false);changeRadarToken(d.frame_token)}
  else if(in3D()){state.radarStatus='3D radar · '+frameLabel()+frameSuffix()}
  else if(state.radarPendingLayer){updateRadarFromLayer(state.radarPendingLayer)}
  else if(state.radarLayer){state.radarStatus=radarCoverageStatus(state.radarLayer)}
  else {state.radarStatus=radarMessage(false);loadRadar2D()}
  updateLabels();
 }catch(e){if(state.radar&&seq===state.radarSeq){state.radarStatus='Radar metadata unavailable · '+String(e.message||e);updateLabels()}}
 finally{state.radarPending=false}
}
async function refreshAlerts(){if(!state.alerts||state.alertPending)return;state.alertPending=true;const seq=++state.alertSeq;state.lastAlerts=Date.now();state.alertStatus='Updating NWS alerts…';updateLabels();
 try{const r=await fetch('/api/tak-map/weather/alerts-i691',{credentials:'same-origin',cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);const data=await r.json();if(!state.alerts||seq!==state.alertSeq)return;if(data.type!=='FeatureCollection'||!Array.isArray(data.features))throw Error('Invalid NWS format');state.alertsData=data.features;const drawable=state.alertsData.filter(f=>f?.geometry).length;const unmapped=state.alertsData.length-drawable;state.alertStatus=`${drawable} mapped · ${unmapped} without geometry · updated ${new Date().toLocaleTimeString()}`;if(in3D())await draw3D();else draw2D()}catch(e){if(state.alerts)state.alertStatus='NWS unavailable · '+String(e.message||e)}finally{state.alertPending=false;updateLabels()}
}
function apply(){updateLabels();if(!state.map)return;if(in3D()){clear2D();draw3D()}else{clear3D();draw2D()}if(state.radar&&!state.historyMode&&(!state.radarToken||Date.now()-state.lastRadar>120000))refreshRadar();if(state.alerts&&Date.now()-state.lastAlerts>90000)refreshAlerts()}
function tick(){if(!mount())return;const m=mapRef();if(!m||!W.L)return;if(m.getPane('takWeatherAlertI691'))m.getPane('takWeatherAlertI691').style.pointerEvents=hasRouteInteraction()?'none':'';
 if(m!==state.map){clear2D();state.map=m;state.mode3d=in3D();apply();return}
 const mode=in3D();if(mode!==state.mode3d){state.mode3d=mode;apply()}
 if(mode&&state.cesRadar&&state.viewer&&!state.viewer.imageryLayers.contains(state.cesRadar)){state.cesRadar=null;state.cesRadarToken=null}
 if(mode&&state.radar&&!state.cesRadar)loadRadar3D();if(!mode&&state.radar&&(!state.radarLayer||state.radarActiveToken!==state.radarToken||!m.hasLayer(state.radarLayer)||(state.radarPendingLayer&&!m.hasLayer(state.radarPendingLayer))))loadRadar2D();
 if(state.radarPendingLayer)updateRadarFromLayer(state.radarPendingLayer);
 if(state.radarStaleAt&&Date.now()-state.radarStaleAt>600000){
   // Never replace a visible frame with one that failed to load, or erase
   // already-rendered tiles solely because NOAA metadata is temporarily down.
   if(state.radarPendingLayer)state.radarStatus='Radar update delayed · previous frame retained';
   else if(state.radarToken===null)state.radarStatus='Radar source unavailable · previous frame retained (stale)';
   updateLabels();
 }
 if(state.radar&&!state.historyMode&&Date.now()-state.lastRadar>120000)refreshRadar();if(state.alerts&&Date.now()-state.lastAlerts>90000)refreshAlerts()
}
function selectHistory(frame){
 if(!state.radar||!frame||!/^h\d{13}_[a-f0-9]{16}$/.test(frame.frame_id)||!Number.isFinite(Date.parse(frame.valid_time_utc)))return false;
 state.historyMode=true;state.radarProvider='nws-time';state.radarFrameSource='catalog_observation';
 state.radarValid=frame.valid_time_utc;state.radarStatus='Historical radar · '+new Date(frame.valid_time_utc).toLocaleTimeString()+' · loading';
 changeRadarToken(frame.frame_id);
 if(state.radarToken===frame.frame_id){if(in3D())loadRadar3D();else loadRadar2D()}
 updateLabels();return true;
}
function leaveHistory(){state.historyMode=false;state.radarToken=null;state.radarSeq++;
 // Render the most recent VERIFIED live frame instead of repurposing an historical token.
 state.lastRadar=0;refreshRadar();updateLabels();
}
function historyReady(frameId){
 if(!state.historyMode||state.radarToken!==frameId)return false;
 if(in3D())return state.cesRadarToken===frameId&&!!state.viewer?.scene?.globe?.tilesLoaded;
 const layer=state.radarLayer;
 if(!layer||layer._takToken!==frameId)return false;
 const n=layerCounts(layer);
 return !!layer._takBatchReady&&n.total>0&&n.loaded>0&&n.pending===0&&n.retrying===0&&n.failed===0;
}
W.TakMapNativeWeatherI693={state,apply,refreshAlerts,refreshRadar,selectHistory,leaveHistory,historyReady};
if(D.readyState==='loading')D.addEventListener('DOMContentLoaded',tick,{once:true});else tick();setInterval(tick,2000);
})();
