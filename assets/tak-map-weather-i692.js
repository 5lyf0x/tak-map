/* TAK Map i692: same-origin NWS radar, independent NWS alerts. Preserves i691 settings/UI. */
(()=>{'use strict';
const W=window,D=document,KEY='tak-map-native-weather-i691';
const STATUS='/api/tak-map/weather/radar/status-i692';
const TILES='/api/tak-map/weather/radar/tile-i692';
const state={radar:false,alerts:false,opacity:55,radarLayer:null,alertLayer:null,cesRadar:null,cesAlerts:null,viewer:null,map:null,
 lastAlerts:0,lastRadar:0,alertPending:false,radarPending:false,alertSeq:0,radarSeq:0,mode3d:false,
 radarStatus:'Off',alertStatus:'Off',alertsData:[],radarValid:null,radarProvider:null,radarToken:null,
 radarTileLoaded:0,radarTileErrors:0,radarNativeMaxZoom:10};
try{const saved=JSON.parse(localStorage.getItem(KEY)||'{}');state.radar=saved.radar===true;state.alerts=saved.alerts===true;state.opacity=Math.max(0,Math.min(100,Number(saved.opacity??55)||0))}catch(_){}
function save(){try{localStorage.setItem(KEY,JSON.stringify({radar:state.radar,alerts:state.alerts,opacity:state.opacity}))}catch(_){}}
const $=id=>D.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function status(id,msg){const el=$(id);if(el)el.textContent=msg}
function mount(){if($('takNativeWeatherI691'))return true;const stack=$('takBasemapBlendI673'),sel=$('basemapSelect');if(!stack&&!sel)return false;
 const panel=D.createElement('section');panel.id='takNativeWeatherI691';panel.className='tak-weather-i691';
 panel.innerHTML=`<button class="tak-weather-head-i691" type="button" aria-expanded="true">WEATHER OVERLAYS <span>⌃</span></button><div class="tak-weather-body-i691"><label class="tak-weather-row-i691"><span>Radar Reflectivity<small>NOAA/NWS · MRMS</small></span><input id="takWeatherRadarI691" type="checkbox"></label><div id="takWeatherRadarSettingsI691" class="tak-weather-sub-i691"><label>Opacity <output id="takWeatherOpacityOutI691">55%</output></label><input id="takWeatherOpacityI691" type="range" min="0" max="100" step="1" value="55"><small id="takWeatherRadarStatusI691" role="status">Off</small></div><label class="tak-weather-row-i691"><span>Weather Alerts<small>NWS watches · warnings · advisories</small></span><input id="takWeatherAlertsI691" type="checkbox"></label><div id="takWeatherAlertSettingsI691" class="tak-weather-sub-i691"><div class="tak-weather-legend-i691"><i style="background:#ed5b58"></i>Extreme <i style="background:#ed9a54"></i>Severe <i style="background:#e8cf66"></i>Moderate</div><small id="takWeatherAlertStatusI691" role="status">Off</small></div><small class="tak-weather-credit-i691">Weather data © NOAA / National Weather Service</small></div>`;
 (stack||sel).insertAdjacentElement('afterend',panel);
 const radar=$('takWeatherRadarI691'),alerts=$('takWeatherAlertsI691'),opacity=$('takWeatherOpacityI691');radar.checked=state.radar;alerts.checked=state.alerts;opacity.value=state.opacity;
 radar.addEventListener('change',()=>{state.radar=radar.checked;state.radarSeq++;if(!state.radar){state.radarToken=null;state.radarStatus='Off';state.lastRadar=0;}save();apply()});
 alerts.addEventListener('change',()=>{state.alerts=alerts.checked;state.alertSeq++;save();apply()});
 opacity.addEventListener('input',()=>{state.opacity=Number(opacity.value);$('takWeatherOpacityOutI691').textContent=state.opacity+'%';opacity.style.setProperty('--tak-weather-pct',state.opacity+'%');save();if(state.radarLayer)state.radarLayer.setOpacity(state.opacity/100);if(state.cesRadar)state.cesRadar.alpha=state.opacity/100});opacity.dispatchEvent(new Event('input'));
 panel.querySelector('.tak-weather-head-i691').addEventListener('click',e=>{const body=panel.querySelector('.tak-weather-body-i691');const hidden=body.hidden=!body.hidden;e.currentTarget.setAttribute('aria-expanded',String(!hidden));e.currentTarget.querySelector('span').textContent=hidden?'⌄':'⌃'});
 return true}
function mapRef(){return W.takLeafletMap||W.map||null}
function in3D(){try{return typeof terrain3DActive!=='undefined'&&!!terrain3DActive&&typeof terrain3DViewer!=='undefined'&&!!terrain3DViewer&&!!W.Cesium}catch(_){return false}}
function viewer3D(){try{return typeof terrain3DViewer!=='undefined'?terrain3DViewer:null}catch(_){return null}}
function panes(m){if(!m.getPane('takWeatherRadarI691'))m.createPane('takWeatherRadarI691');const rp=m.getPane('takWeatherRadarI691');rp.style.zIndex='270';rp.style.pointerEvents='none';if(!m.getPane('takWeatherAlertI691'))m.createPane('takWeatherAlertI691');const ap=m.getPane('takWeatherAlertI691');ap.style.zIndex='430'}
function radarURL(){return TILES+'/{z}/{x}/{y}.png?frame='+encodeURIComponent(state.radarToken)}
function clearRadar2D(){const m=state.map;if(m&&state.radarLayer&&m.hasLayer(state.radarLayer))m.removeLayer(state.radarLayer);state.radarLayer=null}
function clearRadar3D(){if(state.viewer&&state.cesRadar)try{state.viewer.imageryLayers.remove(state.cesRadar,true)}catch(_){}state.cesRadar=null}
function clear2D(){clearRadar2D();if(state.map&&state.alertLayer&&state.map.hasLayer(state.alertLayer))state.map.removeLayer(state.alertLayer);state.alertLayer=null}
function clear3D(){clearRadar3D();if(state.viewer&&state.cesAlerts)try{state.viewer.dataSources.remove(state.cesAlerts,true)}catch(_){}state.cesAlerts=null}
function hasRouteInteraction(){try{return !!(W.TakMapRouteCreationActive||D.body.classList.contains('route-creation-active')||(typeof activeMapTool!=='undefined'&&activeMapTool==='route')||$('toolRoute')?.classList.contains('active'))}catch(_){return false}}
function eventHtml(f){const p=f.properties||{};const when=s=>s?new Date(s).toLocaleString():'Not reported';const url=String(p['@id']||p.id||f.id||'');const safeUrl=/^https:\/\/(api\.weather\.gov|www\.weather\.gov)\//.test(url)?`<a href="${esc(url)}" target="_blank" rel="noopener noreferrer">Original NWS alert</a>`:'';return `<div class="tak-weather-popup-i691"><b>${esc(p.event||'Weather alert')}</b><p>${esc(p.headline||p.areaDesc||'')}</p><small>Severity: ${esc(p.severity||'Unknown')} · Ends: ${esc(when(p.ends||p.expires))}</small><p>${esc((p.description||'').slice(0,2400))}</p>${safeUrl}</div>`}
function alertStyle(f){const sev=String(f.properties?.severity||'').toLowerCase();const c=sev==='extreme'?'#ed5b58':sev==='severe'?'#ed9a54':sev==='moderate'?'#e8cf66':sev==='minor'?'#66b7ef':'#a2abb5';return {color:c,weight:2,opacity:.92,fillColor:c,fillOpacity:.14,interactive:true}}
function frameLabel(){return state.radarValid?'frame '+new Date(state.radarValid).toLocaleTimeString():'observation time not provided'}
function radarMessage(loaded){const provider=state.radarProvider==='nws-latest'?' · fallback source':'';return (loaded?'Radar ready · ':'Loading radar · ')+frameLabel()+provider}
function loadRadar2D(){const m=state.map;if(!m||in3D()||!state.radar||!state.radarToken||!W.L)return;
 if(!state.radarLayer){
  state.radarTileLoaded=0;state.radarTileErrors=0;
  const layer=W.L.tileLayer(radarURL(),{opacity:state.opacity/100,pane:'takWeatherRadarI691',maxNativeZoom:state.radarNativeMaxZoom,maxZoom:24,updateWhenIdle:true,keepBuffer:2,attribution:'NOAA / NWS MRMS',crossOrigin:false});
  layer.on('tileload',()=>{if(state.radarLayer!==layer)return;state.radarTileLoaded++;if(state.radarTileLoaded===1){state.radarStatus=radarMessage(true);updateLabels()}});
  layer.on('tileerror',()=>{if(state.radarLayer!==layer)return;state.radarTileErrors++;if(state.radarTileErrors>=2){state.radarStatus='Radar tiles unavailable · checking provider';state.lastRadar=Math.min(state.lastRadar,Date.now()-115000);updateLabels()}});
  state.radarLayer=layer;
 }
 if(!m.hasLayer(state.radarLayer))state.radarLayer.addTo(m)
}
function draw2D(){const m=state.map;if(!m||in3D())return;panes(m);
 if(state.radar)loadRadar2D();else clearRadar2D();
 if(state.alerts&&state.alertsData.length){if(state.alertLayer&&m.hasLayer(state.alertLayer))m.removeLayer(state.alertLayer);const features=state.alertsData.filter(f=>f&&f.geometry);state.alertLayer=W.L.geoJSON({type:'FeatureCollection',features},{pane:'takWeatherAlertI691',style:alertStyle,onEachFeature:(f,l)=>l.on('click',e=>{if(hasRouteInteraction())return;W.L.DomEvent.stopPropagation(e);l.bindPopup(eventHtml(f),{maxWidth:360,maxHeight:360,autoPan:true}).openPopup(e.latlng)})});state.alertLayer.addTo(m)}else if(state.alertLayer&&m.hasLayer(state.alertLayer))m.removeLayer(state.alertLayer)
}
function loadRadar3D(){const v=state.viewer,C=W.Cesium;if(!v||!C||!in3D()||!state.radar||!state.radarToken||state.cesRadar)return;
 try{const imagery=new C.UrlTemplateImageryProvider({url:radarURL(),tilingScheme:new C.WebMercatorTilingScheme(),tileWidth:256,tileHeight:256,maximumLevel:state.radarNativeMaxZoom,credit:'NOAA / NWS MRMS'});
  state.cesRadar=v.imageryLayers.addImageryProvider(imagery);state.cesRadar.alpha=state.opacity/100;
 }catch(e){state.radarStatus='3D radar unavailable';updateLabels()}
}
async function draw3D(){const v=viewer3D(),C=W.Cesium;if(!in3D()||!v||!C)return;state.viewer=v;
 if(state.radar)loadRadar3D();else clearRadar3D();
 if(state.cesAlerts)try{v.dataSources.remove(state.cesAlerts,true)}catch(_){}state.cesAlerts=null;
 if(state.alerts&&state.alertsData.some(f=>f.geometry)){try{const source=await C.GeoJsonDataSource.load({type:'FeatureCollection',features:state.alertsData.filter(f=>f.geometry)},{clampToGround:true,stroke:C.Color.ORANGE,fill:C.Color.ORANGE.withAlpha(.12),strokeWidth:2});if(!in3D()||!state.alerts||v!==state.viewer)return;state.cesAlerts=await v.dataSources.add(source)}catch(e){state.alertStatus='3D alerts unavailable: '+String(e.message||e)}}updateLabels()
}
function updateLabels(){if($('takWeatherRadarSettingsI691'))$('takWeatherRadarSettingsI691').hidden=!state.radar;if($('takWeatherAlertSettingsI691'))$('takWeatherAlertSettingsI691').hidden=!state.alerts;status('takWeatherRadarStatusI691',state.radar?state.radarStatus:'Off');status('takWeatherAlertStatusI691',state.alerts?state.alertStatus:'Off')}
function changeRadarToken(token){if(state.radarToken===token)return;state.radarToken=token;clearRadar2D();clearRadar3D();if(!token)return;if(in3D())loadRadar3D();else loadRadar2D()}
async function refreshRadar(){if(!state.radar||state.radarPending)return;state.radarPending=true;const seq=state.radarSeq;state.lastRadar=Date.now();
 try{const r=await fetch(STATUS,{credentials:'same-origin',cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);const d=await r.json();if(!state.radar||seq!==state.radarSeq)return;
  if(!d.ok||!d.frame_token){state.radarStatus='Radar unavailable · '+String(d.error_code||'provider error');changeRadarToken(null);updateLabels();return}
  if(!/^[puf][0-9]{1,16}$/.test(d.frame_token))throw Error('Invalid frame token');
  state.radarProvider=d.provider_id;state.radarValid=d.valid_time_utc||null;state.radarNativeMaxZoom=Number.isInteger(d.native_max_zoom)?d.native_max_zoom:10;
  const changed=d.frame_token!==state.radarToken;
  if(changed){state.radarStatus=radarMessage(false);changeRadarToken(d.frame_token)}
  else if(state.radarTileLoaded>0){state.radarStatus=radarMessage(true)}
  else if(d.service_state==='unavailable'){state.radarStatus='Radar unavailable · '+String(d.error_code||'provider error')}
  else if(d.last_successful_fetch_utc){state.radarStatus=radarMessage(true)}
  else state.radarStatus=radarMessage(false);
  updateLabels()
 }catch(e){if(state.radar&&seq===state.radarSeq){state.radarStatus='Radar metadata unavailable · '+String(e.message||e);updateLabels()}}
 finally{state.radarPending=false}
}
async function refreshAlerts(){if(!state.alerts||state.alertPending)return;state.alertPending=true;const seq=++state.alertSeq;state.lastAlerts=Date.now();state.alertStatus='Updating NWS alerts…';updateLabels();
 try{const r=await fetch('/api/tak-map/weather/alerts-i691',{credentials:'same-origin',cache:'no-store'});if(!r.ok)throw Error('HTTP '+r.status);const data=await r.json();if(!state.alerts||seq!==state.alertSeq)return;if(data.type!=='FeatureCollection'||!Array.isArray(data.features))throw Error('Invalid NWS format');state.alertsData=data.features;const drawable=state.alertsData.filter(f=>f?.geometry).length;const unmapped=state.alertsData.length-drawable;state.alertStatus=`${drawable} mapped · ${unmapped} without geometry · updated ${new Date().toLocaleTimeString()}`;if(in3D())await draw3D();else draw2D()}catch(e){if(state.alerts)state.alertStatus='NWS unavailable · '+String(e.message||e)}finally{state.alertPending=false;updateLabels()}
}
function apply(){updateLabels();if(!state.map)return;if(in3D()){clear2D();draw3D()}else{clear3D();draw2D()}if(state.radar&&(!state.radarToken||Date.now()-state.lastRadar>120000))refreshRadar();if(state.alerts&&Date.now()-state.lastAlerts>90000)refreshAlerts()}
function tick(){if(!mount())return;const m=mapRef();if(!m||!W.L)return;if(m.getPane('takWeatherAlertI691'))m.getPane('takWeatherAlertI691').style.pointerEvents=hasRouteInteraction()?'none':'';
 if(m!==state.map){clear2D();state.map=m;state.mode3d=in3D();apply();return}
 const mode=in3D();if(mode!==state.mode3d){state.mode3d=mode;apply()}
 if(mode&&state.cesRadar&&state.viewer&&!state.viewer.imageryLayers.contains(state.cesRadar))state.cesRadar=null;
 if(mode&&state.radar&&!state.cesRadar)loadRadar3D();if(!mode&&state.radar&&!state.radarLayer)loadRadar2D();
 if(state.radar&&Date.now()-state.lastRadar>120000)refreshRadar();if(state.alerts&&Date.now()-state.lastAlerts>90000)refreshAlerts()
}
W.TakMapNativeWeatherI692={state,apply,refreshAlerts,refreshRadar};
if(D.readyState==='loading')D.addEventListener('DOMContentLoaded',tick,{once:true});else tick();setInterval(tick,2000);
})();
