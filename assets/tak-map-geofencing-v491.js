(function(w,d){
'use strict';
const V='i502';
if(w.TakMapGeofencingV491)return;
const $=id=>d.getElementById(id),qa=(s,r)=>Array.from((r||d).querySelectorAll(s));
const FENCES=new Map(),TRACK=new Map(),EVENTS=[],POPUP_TARGETS=new Map();
const CFG={confirmationMs:2000,rearmMs:10000,maxEvents:160,tickMs:500};
const S={loadedAt:Date.now(),master:true,filter:'all',eventsCollapsed:false,dragged:false,lastTick:0,ticks:0,alerts:0,suppressedStale:0,suppressedRearm:0,protectedBlocks:0,popupButtons:0,soundReady:false,soundPlays:0,lastError:'',saveRequests:0,loadRequests:0,reportedCoordinateEvaluations:0,visualCoordinateEvaluations:0,reportedSegmentsEvaluated:0};
let timer=0,audioCtx=null;
function esc(v){return String(v==null?'':v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function text(v){return String(v==null?'':v).trim()}
function num(v){v=Number(v);return Number.isFinite(v)?v:null}
function nowIso(){return new Date().toISOString()}
function mapObj(){try{return w.map||(typeof map!=='undefined'?map:null)||w.takLeafletMap||null}catch(_){return w.map||w.takLeafletMap||null}}
function lifecycle(){return w.TakMapObjectLifecycleV486||w.TakMapObjectLifecycleV482||w.TakMapObjectLifecycleV479||null}
function stateObj(){try{return w.state||(typeof state!=='undefined'?state:null)}catch(_){return w.state||null}}
function currentImports(){try{return Array.isArray(w.lastImports)?w.lastImports:(typeof lastImports!=='undefined'&&Array.isArray(lastImports)?lastImports:[])}catch(_){return []}}
function currentDataSync(){try{return w.lastDataSync||(typeof lastDataSync!=='undefined'?lastDataSync:null)||{}}catch(_){return w.lastDataSync||{}}}
function currentTak(){try{return Array.isArray(w.lastTakMarkers)?w.lastTakMarkers:(typeof lastTakMarkers!=='undefined'&&Array.isArray(lastTakMarkers)?lastTakMarkers:[])}catch(_){return []}}
function currentAircraft(){try{const api=w.TakMapAdsbWorkerV477||w.TakMapAdsbWorkerV476;/* Geofence truth must use reported coordinates, never the interpolated marker pose. */if(api&&typeof api.rawSnapshot==='function')return api.rawSnapshot();if(api&&typeof api.snapshot==='function')return api.snapshot();return Array.isArray(w.lastAircraft)?w.lastAircraft:[]}catch(_){return []}}
function objectKind(o){try{const api=lifecycle(),id=canonicalId(o);const e=api&&id&&api.entryForId&&api.entryForId(id);if(e&&e.kind)return e.kind}catch(_){}const v=text(o&&((o.object_kind)||o.kind||o.geometry_type||(o.geometry&&o.geometry.type)||o.geometry||o.type)).toLowerCase();if(/route|track|line/.test(v))return'route';if(/shape|polygon|area|rectangle|circle|ellipse|freehand/.test(v))return'shape';return'point'}
function canonicalId(o){if(!o||typeof o!=='object')return'';const direct=text(o.canonical_id||o.canonicalId||o._takCanonicalObjectId||o._takSelectionCanonicalId);if(direct)return direct;const local=text(o.object_id||o.local_id||o._local_id||o.source_id);if(local.startsWith('local-'))return'local:'+local;if(local.startsWith('datasync-'))return'datasync:'+local;return''}
function objectName(o){return text(o&& (o.callsign||o.name||o.title||o.label||o.filename||o.uid||o.id))||'Unnamed object'}
function sourceName(o,fallback){return text(o&& (o.mission_name||o.import_name||o.source||o.source_kind))||fallback||'TAK Map'}
function flatten(value,out){out=out||[];if(!Array.isArray(value))return out;if(value.length>=2&&Number.isFinite(Number(value[0]))&&Number.isFinite(Number(value[1]))){out.push([Number(value[0]),Number(value[1])]);return out}for(const c of value)flatten(c,out);return out}
function coordPairs(o){if(!o||typeof o!=='object')return[];const lat=num(o.lat),lon=num(o.lon!=null?o.lon:o.lng);if(lat!=null&&lon!=null)return[[lon,lat]];if(Array.isArray(o.coords)){const out=[];for(const c of o.coords){if(Array.isArray(c)&&c.length>=2){const a=num(c[0]),b=num(c[1]);if(a!=null&&b!=null){if(Math.abs(a)<=90&&Math.abs(b)<=180)out.push([b,a]);else out.push([a,b])}}else if(c&&typeof c==='object'){const la=num(c.lat),lo=num(c.lon!=null?c.lon:c.lng);if(la!=null&&lo!=null)out.push([lo,la])}}if(out.length)return out}const g=o.geometry&&typeof o.geometry==='object'?o.geometry:null;if(g&&Array.isArray(g.coordinates))return flatten(g.coordinates,[]);if(o.feature&&o.feature.geometry)return flatten(o.feature.geometry.coordinates||[],[]);return[]}
function geometryFromObject(o,kind){kind=kind||objectKind(o);let pairs=[];const props=o&&o.properties||{};if(kind==='route'){
 /* A route object may expose a center lat/lon for popup placement. That point is
    metadata, not route geometry. Ignore it and use only the stored line vertices;
    if they are unavailable, targetForLayer falls back to the Leaflet polyline. */
 const routeObject=o&&typeof o==='object'?Object.assign({},o):o;
 if(routeObject){delete routeObject.lat;delete routeObject.lon;delete routeObject.lng;delete routeObject.latitude;delete routeObject.longitude}
 pairs=coordPairs(routeObject);
 return pairs.length>1?{type:'route',coordinates:pairs}:null
 }
 pairs=coordPairs(o);
 if(kind==='shape'){
 const radius=num(o.radius_meters??o.radius_m??props.radius_meters??props.radius_m??o.radius);if(radius!=null&&pairs.length){return {type:'circle',center:pairs[0],radius_m:Math.max(.5,radius)}}
 if(pairs.length>2){const ring=pairs.slice();if(ring[0][0]!==ring[ring.length-1][0]||ring[0][1]!==ring[ring.length-1][1])ring.push(ring[0].slice());return {type:'polygon',coordinates:ring}}
 }
 return null
}
function geometryCenter(g){if(!g)return null;if(g.type==='circle')return {lat:g.center[1],lon:g.center[0]};const pts=g.coordinates||[];if(!pts.length)return null;let minLat=90,maxLat=-90,minLon=180,maxLon=-180;for(const p of pts){minLon=Math.min(minLon,p[0]);maxLon=Math.max(maxLon,p[0]);minLat=Math.min(minLat,p[1]);maxLat=Math.max(maxLat,p[1])}return {lat:(minLat+maxLat)/2,lon:(minLon+maxLon)/2}}
function geometrySummary(g){if(!g)return'No geometry';if(g.type==='circle')return 'Circle · '+Math.round(g.radius_m)+' m radius';if(g.type==='route')return 'Route · '+(g.coordinates||[]).length+' points';return 'Area · '+Math.max(0,(g.coordinates||[]).length-1)+' vertices'}
function haversine(a,b){const R=6371008.8,p1=a.lat*Math.PI/180,p2=b.lat*Math.PI/180,dp=(b.lat-a.lat)*Math.PI/180,dl=(b.lon-a.lon)*Math.PI/180;const q=Math.sin(dp/2)**2+Math.cos(p1)*Math.cos(p2)*Math.sin(dl/2)**2;return 2*R*Math.atan2(Math.sqrt(q),Math.sqrt(1-q))}
const ROUTE_CATEGORIES_V500=['General','Primary','Alternate','Ingress','Egress','Evacuation','Patrol','Search','Medical','Logistics','Restricted / Avoid','Training','Other'];
function routeColorV500(o){const p=o&&o.properties||{},v=text(o&&(o.color||o.stroke_color)||p.color||p.stroke_color).toLowerCase();return /^#[0-9a-f]{6}$/.test(v)?v:'#ff6f2e'}
function routeCategoryV500(o){const p=o&&o.properties||{},v=text(o&&(o.route_category||o.category)||p.route_category||p.category);return ROUTE_CATEGORIES_V500.includes(v)?v:'General'}
function routeNotesV500(o){const p=o&&o.properties||{};return text(o&&(o.notes||o.description)||p.notes||p.description)}
function routeLengthMetersV500(g){const pts=g&&Array.isArray(g.coordinates)?g.coordinates:[];let total=0;for(let i=1;i<pts.length;i++)total+=haversine({lon:Number(pts[i-1][0]),lat:Number(pts[i-1][1])},{lon:Number(pts[i][0]),lat:Number(pts[i][1])});return total}
function routeDualDistanceV500(m){m=Number(m)||0;const mi=m/1609.344,km=m/1000;return mi.toFixed(mi<.1?3:2)+' mi · '+km.toFixed(km<.1?3:2)+' km'}
function routeCoordV500(p){return Array.isArray(p)&&p.length>1&&Number.isFinite(Number(p[0]))&&Number.isFinite(Number(p[1]))?Number(p[1]).toFixed(6)+', '+Number(p[0]).toFixed(6):'—'}
function routeCreatedV500(o){const p=o&&o.properties||{},raw=text(o&&(o.created_at||o.created||o.added||o.uploaded||o.time||o.updated)||p.created_at||p.created||p.added||p.uploaded||p.time||p.updated);if(!raw)return'—';const t=Date.parse(raw);if(!Number.isFinite(t))return raw;try{return new Date(t).toLocaleString([], {year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'})}catch(_){return raw}}
function routeGeofenceStatusV500(target){const f=target&&fenceForTarget(target.id);if(!f)return'Off';const candidates=[f.corridor_distance_m,f.corridor_m,f.buffer_m,f.geometry&&f.geometry.corridor_distance_m,target.object&&target.object.corridor_distance_m,target.object&&target.object.route_corridor_m];const width=candidates.map(num).find(v=>v!=null&&v>0);return 'Configured · Cross route'+(width?' · '+routeDualDistanceV500(width)+' corridor':'')}
function routePopupRowV500(label,value,html){if(value==null||String(value).trim()==='')return'';return '<div class="tak-v322-row tak-route-row-v500"><b>'+esc(label)+'</b><span>'+(html?String(value):esc(value))+'</span></div>'}
function enrichRoutePopupV500(feature,target){if(!feature||!target||target.kind!=='route')return false;const table=popupValueTable(feature);if(!table)return false;const o=target.object||{},pts=target.geometry&&target.geometry.coordinates||[],color=routeColorV500(o),name=objectName(o),notes=routeNotesV500(o),created=routeCreatedV500(o),category=routeCategoryV500(o),length=routeDualDistanceV500(routeLengthMetersV500(target.geometry)),start=routeCoordV500(pts[0]),end=routeCoordV500(pts[pts.length-1]),gf=routeGeofenceStatusV500(target),colorHtml='<span class="tak-route-color-value-v500"><i style="--tak-route-color:'+esc(color)+'"></i><code>'+esc(color.toUpperCase())+'</code></span>';table.innerHTML=routePopupRowV500('Name',name)+routePopupRowV500('Length',length)+routePopupRowV500('Color',colorHtml,true)+routePopupRowV500('Start',start)+routePopupRowV500('End',end)+routePopupRowV500('Category',category)+routePopupRowV500('Notes',notes)+routePopupRowV500('Created',created)+routePopupRowV500('Geofence',gf);const title=feature.querySelector('.tak-v322-title,.tak-v321-title,.tak-v320-title,h3');if(title)title.textContent=name;feature.dataset.takRoutePopupV500='1';return true}
function pointInPolygon(pt,ring){let inside=false;for(let i=0,j=ring.length-1;i<ring.length;j=i++){const xi=ring[i][0],yi=ring[i][1],xj=ring[j][0],yj=ring[j][1];const hit=((yi>pt.lat)!==(yj>pt.lat))&&(pt.lon<(xj-xi)*(pt.lat-yi)/((yj-yi)||1e-12)+xi);if(hit)inside=!inside}return inside}
function insideGeometry(pt,g){if(!g||!pt)return false;if(g.type==='circle')return haversine(pt,{lat:g.center[1],lon:g.center[0]})<=g.radius_m;return pointInPolygon(pt,g.coordinates||[])}
function orient(a,b,c){const v=(b.lon-a.lon)*(c.lat-a.lat)-(b.lat-a.lat)*(c.lon-a.lon);return Math.abs(v)<1e-12?0:(v>0?1:-1)}
function onSeg(a,b,c){return Math.min(a.lon,b.lon)-1e-10<=c.lon&&c.lon<=Math.max(a.lon,b.lon)+1e-10&&Math.min(a.lat,b.lat)-1e-10<=c.lat&&c.lat<=Math.max(a.lat,b.lat)+1e-10}
function intersects(a,b,c,d2){const o1=orient(a,b,c),o2=orient(a,b,d2),o3=orient(c,d2,a),o4=orient(c,d2,b);if(o1!==o2&&o3!==o4)return true;if(o1===0&&onSeg(a,b,c))return true;if(o2===0&&onSeg(a,b,d2))return true;if(o3===0&&onSeg(c,d2,a))return true;if(o4===0&&onSeg(c,d2,b))return true;return false}
function crossesRoute(prev,cur,g){if(!prev||!cur||!g||g.type!=='route')return false;const pts=g.coordinates||[];for(let i=1;i<pts.length;i++){const a={lon:pts[i-1][0],lat:pts[i-1][1]},b={lon:pts[i][0],lat:pts[i][1]};if(intersects(prev,cur,a,b))return true}return false}
function parseTime(v){if(v==null||v==='')return 0;if(typeof v==='number'){if(v<1e12)return v*1000;return v}const n=Date.parse(String(v));return Number.isFinite(n)?n:0}
function objectTime(o,source){const candidates=[o&&o.position_time,o&&o.updated_at,o&&o.updated,o&&o.timestamp,o&&o.time,o&&o.last_seen,o&&o.seen,o&&o.generated_at,o&&o.properties&&o.properties.updated_at,o&&o.properties&&o.properties.updated,o&&o.properties&&o.properties.timestamp];for(const v of candidates){const t=parseTime(v);if(t)return t}if(source==='satellite'||source==='local'||source==='datasync')return Date.now();return 0}
function staleLimit(source,o){if(source==='adsb')return Math.max(30000,Math.min(300000,Number((w.lastAdsbSettings||{}).stale_seconds||90)*1000));if(source==='eud')return 60000;if(source==='gateway'){const at=parseTime(o&&o.properties&&o.properties.stale_at);if(at)return Math.max(0,at-Date.now()+1000);return 300000}if(source==='satellite')return 90000;return Infinity}
function pointFrom(o){const lat=num(o&& (o.lat??o.latitude)),lon=num(o&& (o.lon??o.lng??o.longitude));return lat!=null&&lon!=null?{lat,lon}:null}
function altitudeFt(o){for(const v of [o&&o.altitude_ft,o&&o.altitude,o&&o.alt_ft,o&&o.baro_altitude_ft,o&&o.baro_altitude,o&&o.geo_altitude_ft]){const n=num(v);if(n!=null)return n}const m=num(o&&o.altitude_m);return m!=null?m*3.280839895:null}
function sourceEnabled(source){const st=stateObj();if(source==='adsb'){const api=w.TakMapAdsbWorkerV477||w.TakMapAdsbWorkerV476;try{return api&&api.diagnostics?api.diagnostics().enabled!==false:st&&st.live&&st.live.adsb_aircraft!==false}catch(_){return true}}if(source==='datasync')return !st||st.dataSync!==false;if(source==='local')return !st||st.imported!==false;if(source==='gateway'){try{return !w.TakMapGatewayDataV476||w.TakMapGatewayDataV476.diagnostics().master!==false}catch(_){return true}}if(source==='satellite'){const el=$('satEnableV409');return !!(el&&el.checked)}return true}
function layerForCanonical(id){const api=lifecycle(),e=api&&api.entryForId&&api.entryForId(id);if(e&&e.layers){for(const l of e.layers){if(l&&l.getElement)return l}}return null}
function layerForLive(source,id){
 id=text(id);
 try{
  if(source==='adsb'){
   const ctl=w.TakMapControllers&&w.TakMapControllers.adsb,markers=ctl&&ctl.markers;
   const direct=markers&&markers.get&&(markers.get(id)||markers.get(id.toLowerCase())||markers.get(id.toUpperCase()));
   if(direct)return direct;
  }
 }catch(_){}
 const m=mapObj();let found=null;if(!m||!m.eachLayer)return null;m.eachLayer(l=>{if(found)return;try{if(source==='adsb'&&text(l._takAdsbId)===id)found=l;else if(source==='gateway'&&text(l._takGatewayUid||l._gatewayUid||l.feature&&l.feature.properties&&l.feature.properties.uid)===id)found=l;else if(source==='satellite'&&text(l._takSatelliteId||l._satelliteId||l._takSatKey)===id)found=l;else if(source==='eud'){const o=l._takSelectionObject||l._takObject||l.feature&&l.feature.properties;if(o&&text(o.uid||o.id||o.callsign)===id)found=l}}catch(_){}});return found}
function pulse(layer){if(!layer)return;let el=null;try{el=layer.getElement&&layer.getElement()}catch(_){}if(!el)return;el.classList.remove('tak-geofence-pulse-v491');void el.offsetWidth;el.classList.add('tak-geofence-pulse-v491');setTimeout(()=>{try{el.classList.remove('tak-geofence-pulse-v491')}catch(_){}},9000)}
function monitorObject(source,id,name,point,o,layer){id=text(id);S.reportedCoordinateEvaluations++;return {source,id,textId:id.includes(':')?id:source+':'+id,name:name||id,point,positionSource:'reported-lat-lon',altitudeFt:source==='adsb'?altitudeFt(o):null,time:objectTime(o,source),staleMs:staleLimit(source,o),raw:o,layer:layer||null}}
function collectObjects(){const out=[];const wanted=new Set();for(const f of FENCES.values())if(f.enabled!==false)for(const s of f.monitored||[])wanted.add(s);if(!wanted.size)return out;
 if(wanted.has('adsb')&&sourceEnabled('adsb'))for(const a of currentAircraft()){const p=pointFrom(a),id=text(a.id||a.hex||a.icao||a.uid||a.callsign);if(p&&id)out.push(monitorObject('adsb',id,objectName(a),p,a,layerForLive('adsb',id)))}
 if(wanted.has('eud'))for(const o of currentTak()){if(text(o.kind).toLowerCase()!=='eud')continue;const p=pointFrom(o),id=text(o.uid||o.id||o.callsign);if(p&&id)out.push(monitorObject('eud',id,objectName(o),p,o,layerForLive('eud',id)))}
 const api=lifecycle();if(api&&api.registryById){for(const [id,e] of api.registryById){if(!e||e.kind!=='point'||!wanted.has(e.source)||!sourceEnabled(e.source))continue;const o=e.object||{},pairs=coordPairs(o);if(!pairs.length)continue;const p={lon:pairs[0][0],lat:pairs[0][1]},layer=layerForCanonical(id);out.push(monitorObject(e.source,id,objectName(o),p,o,layer))}}
 if(wanted.has('gateway')&&sourceEnabled('gateway')){try{const apiG=w.TakMapGatewayDataV476,rows=apiG&&apiG.snapshot?apiG.snapshot():[];for(const o of rows){const p=pointFrom(o)||pointFrom(o.properties||{}),id=text(o.uid||o.id||o.properties&&o.properties.uid);if(p&&id)out.push(monitorObject('gateway',id,objectName(o.properties||o),p,o,layerForLive('gateway',id)))}}catch(_){}}
 if(wanted.has('satellite')&&sourceEnabled('satellite')){try{const rows=typeof w.getTakMapSatelliteSnapshotV491==='function'?w.getTakMapSatelliteSnapshotV491():[];for(const o of rows){const p=pointFrom(o),id=text(o.id||o.norad||o.name);if(p&&id)out.push(monitorObject('satellite',id,objectName(o),p,o,layerForLive('satellite',id)))}}catch(_){}}
 return out
}
function altitudeAllowed(f,o){if(o.source!=='adsb')return true;const a=f.altitude||{mode:'none'},mode=text(a.mode||'none');if(mode==='none')return true;const v=o.altitudeFt;if(v==null)return false;const min=num(a.min_ft),max=num(a.max_ft);if(mode==='min')return min==null||v>=min;if(mode==='max')return max==null||v<=max;if(mode==='band')return (min==null||v>=min)&&(max==null||v<=max);return true}
function trackKey(f,o){return f.id+'|'+o.textId}
function fresh(o,now){if(!o.time)return false;if(o.staleMs===Infinity)return true;return now-o.time<=o.staleMs}
function triggerAllowed(st,now){if(st.lastEventAt&&now-st.lastEventAt<CFG.rearmMs){S.suppressedRearm++;return false}return true}
function eventLabel(t){return t==='enter'?'entered':t==='exit'?'exited':t==='cross'?'crossed':'met dwell threshold in'}
function armSound(){try{if(!audioCtx)audioCtx=new (w.AudioContext||w.webkitAudioContext)();if(audioCtx.state==='suspended')audioCtx.resume();S.soundReady=true;return true}catch(e){S.lastError=String(e&&e.message||e);return false}}
function playSound(){try{if(!armSound())return;const start=audioCtx.currentTime;[[0,880],[.16,660],[.32,880]].forEach(([off,freq])=>{const osc=audioCtx.createOscillator(),gain=audioCtx.createGain();osc.type='sine';osc.frequency.value=freq;gain.gain.setValueAtTime(.0001,start+off);gain.gain.exponentialRampToValueAtTime(.16,start+off+.015);gain.gain.exponentialRampToValueAtTime(.0001,start+off+.12);osc.connect(gain).connect(audioCtx.destination);osc.start(start+off);osc.stop(start+off+.14)});S.soundReady=true;S.soundPlays++}catch(e){S.lastError=String(e&&e.message||e)}}
function addEvent(f,o,type,extra){const ev={id:'gfe-'+Date.now().toString(36)+'-'+Math.random().toString(36).slice(2,7),time:Date.now(),type,fence_id:f.id,fence_name:f.name,object_id:o.textId,object_name:o.name,source:o.source,altitude_ft:o.altitudeFt,extra:extra||''};EVENTS.unshift(ev);if(EVENTS.length>CFG.maxEvents)EVENTS.length=CFG.maxEvents;S.alerts++;pulse(o.layer);playSound();renderEvents();return ev}
function processArea(f,o,now){const key=trackKey(f,o),st=TRACK.get(key)||{inside:null,pending:null,pendingSince:0,lastEventAt:0,dwellStart:0,dwellFired:false,lastPoint:null};if(st.lastPoint)S.reportedSegmentsEvaluated++;const isIn=altitudeAllowed(f,o)&&insideGeometry(o.point,f.geometry);if(st.inside===null){st.inside=isIn;st.dwellStart=isIn?now:0;st.dwellFired=false;st.lastPoint=o.point;TRACK.set(key,st);return}
 if(isIn!==st.inside){if(st.pending!==isIn){st.pending=isIn;st.pendingSince=now}else if(now-st.pendingSince>=CFG.confirmationMs){st.inside=isIn;st.pending=null;st.pendingSince=0;st.dwellStart=isIn?now:0;st.dwellFired=false;const type=isIn?'enter':'exit';if(f.triggers&&f.triggers[type]&&triggerAllowed(st,now)){addEvent(f,o,type);st.lastEventAt=now}}}else{st.pending=null;st.pendingSince=0}
 if(st.inside&&f.triggers&&f.triggers.dwell&&!st.dwellFired){if(!st.dwellStart)st.dwellStart=now;const mins=Math.max(1,Number(f.dwell_minutes)||1);if(now-st.dwellStart>=mins*60000&&triggerAllowed(st,now)){addEvent(f,o,'dwell',mins+' min');st.lastEventAt=now;st.dwellFired=true}}
 st.lastPoint=o.point;TRACK.set(key,st)
}
function processRoute(f,o,now){const key=trackKey(f,o),st=TRACK.get(key)||{lastPoint:null,pendingCross:0,lastEventAt:0};if(st.lastPoint)S.reportedSegmentsEvaluated++;if(!altitudeAllowed(f,o)){st.lastPoint=null;st.pendingCross=0;TRACK.set(key,st);return}if(st.pendingCross&&now-st.pendingCross>=CFG.confirmationMs){if(f.triggers&&f.triggers.cross&&triggerAllowed(st,now)){addEvent(f,o,'cross');st.lastEventAt=now}st.pendingCross=0}
 if(st.lastPoint&&crossesRoute(st.lastPoint,o.point,f.geometry)&&!st.pendingCross)st.pendingCross=now;st.lastPoint=o.point;TRACK.set(key,st)
}
function tick(){const now=Date.now();S.lastTick=now;S.ticks++;if(!S.master)return;const objects=collectObjects();for(const f of FENCES.values()){if(f.enabled===false)continue;const allowed=new Set(f.monitored||[]);for(const o of objects){if(!allowed.has(o.source)||o.id===f.target_id)continue;if(!fresh(o,now)){S.suppressedStale++;continue}if(f.kind==='route')processRoute(f,o,now);else processArea(f,o,now)}}}
function ensureTimer(){if(timer)return;timer=setInterval(tick,CFG.tickMs)}
function clearTrackingForFence(id){for(const k of Array.from(TRACK.keys()))if(k.startsWith(id+'|'))TRACK.delete(k)}
function normalizedFence(raw){raw=raw||{};const kind=raw.kind==='route'?'route':'shape',tr=raw.triggers||{};return {id:text(raw.id)||'gf-'+Date.now().toString(36)+'-'+Math.random().toString(36).slice(2,8),name:text(raw.name)||'Geofence',target_id:text(raw.target_id),target_source:text(raw.target_source)||'local',target_name:text(raw.target_name)||'Map object',kind,geometry:raw.geometry||null,monitored:Array.from(new Set((raw.monitored||[]).filter(x=>['eud','adsb','local','datasync','gateway','satellite'].includes(x)))),triggers:{enter:kind==='shape'&&!!tr.enter,exit:kind==='shape'&&!!tr.exit,dwell:kind==='shape'&&!!tr.dwell,cross:kind==='route'},dwell_minutes:Math.max(1,Number(raw.dwell_minutes)||1),altitude:{mode:['none','min','max','band'].includes(text(raw.altitude&&raw.altitude.mode))?text(raw.altitude.mode):'none',min_ft:num(raw.altitude&&raw.altitude.min_ft),max_ft:num(raw.altitude&&raw.altitude.max_ft)},enabled:raw.enabled!==false,created_at:text(raw.created_at)||nowIso(),updated_at:text(raw.updated_at)||nowIso()}}
async function apiJson(url,init){const r=await fetch(url,Object.assign({cache:'no-store',credentials:'same-origin'},init||{}));let j={};try{j=await r.json()}catch(_){}if(!r.ok||j.ok===false)throw new Error(j.error||('HTTP '+r.status));return j}
async function loadFences(){S.loadRequests++;try{const j=await apiJson('/api/tak-map/geofences?_='+Date.now());FENCES.clear();for(const raw of j.fences||[]){const f=normalizedFence(raw);FENCES.set(f.id,f)}renderAll();return j}catch(e){S.lastError=String(e&&e.message||e);renderAll();return {ok:false,error:S.lastError}}}
async function saveFence(f){S.saveRequests++;f=normalizedFence(Object.assign({},f,{updated_at:nowIso()}));const j=await apiJson('/api/tak-map/geofences',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'upsert',fence:f})});FENCES.set(f.id,normalizedFence(j.fence||f));clearTrackingForFence(f.id);renderAll();return FENCES.get(f.id)}
async function removeFence(id){S.saveRequests++;await apiJson('/api/tak-map/geofences',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:'remove',id})});FENCES.delete(id);clearTrackingForFence(id);renderAll();refreshPopupButtons();return true}
async function setFenceEnabled(id,on){const f=FENCES.get(id);if(!f)return false;f.enabled=!!on;await saveFence(f);return true}
function protectedIds(){return new Set(Array.from(FENCES.values()).map(f=>f.target_id).filter(Boolean))}
function fenceForTarget(id){return Array.from(FENCES.values()).find(f=>f.target_id===id)||null}
function showNotice(title,message){const prior=$('takGeofenceNoticeV491');if(prior)prior.remove();const ov=d.createElement('div');ov.id='takGeofenceNoticeV491';ov.className='tak-gf-overlay-v491';ov.innerHTML='<div class="tak-gf-notice-v491" role="dialog" aria-modal="true"><div class="tak-gf-modal-head-v491"><div><b>'+esc(title)+'</b><small>TAK Map Geofencing</small></div><button type="button" data-close>×</button></div><div class="tak-gf-notice-body-v491">'+esc(message)+'</div><div class="tak-gf-modal-actions-v491"><button type="button" data-close>Close</button></div></div>';ov.addEventListener('click',e=>{if(e.target===ov||e.target.closest('[data-close]'))ov.remove()});d.body.appendChild(ov)}
function objectForId(id){const api=lifecycle(),e=api&&api.entryForId&&api.entryForId(id);return e?e.object:null}
function geometryFromLayer(layer,kind){
 if(!layer)return null;
 try{
  if(kind==='shape'&&typeof layer.getLatLng==='function'&&typeof layer.getRadius==='function'){
   const c=layer.getLatLng(),r=num(layer.getRadius());
   if(c&&r!=null)return {type:'circle',center:[Number(c.lng),Number(c.lat)],radius_m:Math.max(.5,r)};
  }
  if(typeof layer.getLatLngs==='function'){
   const raw=layer.getLatLngs(),pairs=[];
   (function walk(v){if(!Array.isArray(v))return;if(v.length&&v[0]&&typeof v[0].lat==='number'){for(const q of v)pairs.push([Number(q.lng),Number(q.lat)]);return}for(const q of v)walk(q)})(raw);
   if(kind==='route'&&pairs.length>1)return {type:'route',coordinates:pairs};
   if(kind==='shape'&&pairs.length>2){const ring=pairs.slice();if(ring[0][0]!==ring[ring.length-1][0]||ring[0][1]!==ring[ring.length-1][1])ring.push(ring[0].slice());return {type:'polygon',coordinates:ring}}
  }
 }catch(_){}
 return null
}
function targetForLayer(layer){
 const api=lifecycle(),e=api&&api.entryForLayer&&api.entryForLayer(layer);
 const o=e&&e.object||layer&&layer._takSelectionObject||layer&&layer._takObject||layer&&layer.feature&&layer.feature.properties||null;
 const id=text(e&&e.objectId||layer&&layer._takCanonicalObjectId||layer&&layer._takSelectionCanonicalId||canonicalId(o));
 const kind=text(e&&e.kind||objectKind(o));
 if(!id||!['shape','route'].includes(kind))return null;
 const objectGeometry=geometryFromObject(o,kind);
 const g=(kind==='route'&&(!objectGeometry||!Array.isArray(objectGeometry.coordinates)||objectGeometry.coordinates.length<2))?geometryFromLayer(layer,kind):(objectGeometry||geometryFromLayer(layer,kind));
 if(!g||(kind==='route'&&(!Array.isArray(g.coordinates)||g.coordinates.length<2)))return null;
 return {id,kind,source:text(e&&e.source)||(id.startsWith('datasync:')?'datasync':'local'),object:o,name:objectName(o),geometry:g}
}
function sourceLabel(s){return {eud:'EUDs / TAK users',adsb:'ADS-B aircraft',local:'Local Data',datasync:'Data Sync',gateway:'Gateway Data',satellite:'Satellite objects'}[s]||s}
function triggerLabel(f){const a=[];if(f.triggers.enter)a.push('Enter');if(f.triggers.exit)a.push('Exit');if(f.triggers.cross)a.push('Cross');if(f.triggers.dwell)a.push('Dwell '+f.dwell_minutes+' min');return a.join(' + ')||'No trigger'}
function monitoredLabel(f){const a=(f.monitored||[]).map(s=>({eud:'EUD',adsb:'ADS-B',local:'Local',datasync:'Data Sync',gateway:'Gateway',satellite:'Satellite'}[s]||s));return a.length===6?'All sources':a.join(' + ')}
function altitudeLabel(f){if(!f.monitored.includes('adsb')||!f.altitude||f.altitude.mode==='none')return'';if(f.altitude.mode==='min')return ' · ≥ '+Math.round(f.altitude.min_ft||0).toLocaleString()+' ft';if(f.altitude.mode==='max')return ' · ≤ '+Math.round(f.altitude.max_ft||0).toLocaleString()+' ft';return ' · '+Math.round(f.altitude.min_ft||0).toLocaleString()+'–'+Math.round(f.altitude.max_ft||0).toLocaleString()+' ft'}
function editorHtml(target,f){const editing=!!f;const cur=f||{id:'',name:target.name,target_id:target.id,target_source:target.source,target_name:target.name,kind:target.kind,geometry:target.geometry,monitored:['eud','adsb'],triggers:{enter:target.kind==='shape',exit:false,dwell:false,cross:target.kind==='route'},dwell_minutes:5,altitude:{mode:'none',min_ft:null,max_ft:null},enabled:true};const checked=s=>cur.monitored.includes(s),tr=k=>cur.triggers&&cur.triggers[k];return '<div class="tak-gf-modal-v491" role="dialog" aria-modal="true"><div class="tak-gf-modal-head-v491"><div><b>'+(editing?'Edit Geofence':'Create Geofence')+'</b><small>'+esc(target.name)+' · '+esc(geometrySummary(target.geometry))+'</small></div><button type="button" data-gf-close>×</button></div><div class="tak-gf-modal-body-v491"><label class="tak-gf-field-v491"><span>Name</span><input id="takGfNameV491" value="'+esc(cur.name)+'" maxlength="80"></label><div class="tak-gf-section-v491"><b>Monitor object classes</b><div class="tak-gf-check-grid-v491">'+['eud','adsb','local','datasync','gateway','satellite'].map(s=>'<label><input type="checkbox" data-gf-source="'+s+'" '+(checked(s)?'checked':'')+'><span class="tak-gf-box-v491">✓</span><em>'+esc(sourceLabel(s))+'</em></label>').join('')+'</div></div><div class="tak-gf-section-v491"><b>Alert triggers</b><div class="tak-gf-trigger-grid-v491">'+(target.kind==='route'?'<label><input type="checkbox" data-gf-trigger="cross" checked disabled><span class="tak-gf-box-v491">✓</span><em>Cross route</em></label>':['enter','exit','dwell'].map(k=>'<label><input type="checkbox" data-gf-trigger="'+k+'" '+(tr(k)?'checked':'')+'><span class="tak-gf-box-v491">✓</span><em>'+({enter:'Enter area',exit:'Exit area',dwell:'Dwell inside'}[k])+'</em></label>').join(''))+'</div>'+(target.kind==='shape'?'<label class="tak-gf-field-v491 tak-gf-dwell-v491"><span>Dwell duration (minutes)</span><input id="takGfDwellV491" type="number" min="1" max="1440" value="'+Math.max(1,cur.dwell_minutes||5)+'"></label>':'')+'</div><div class="tak-gf-section-v491"><b>ADS-B altitude rule</b><div class="tak-gf-alt-grid-v491"><label><span>Mode</span><select id="takGfAltModeV491"><option value="none" '+(cur.altitude.mode==='none'?'selected':'')+'>No altitude limit</option><option value="min" '+(cur.altitude.mode==='min'?'selected':'')+'>Minimum altitude</option><option value="max" '+(cur.altitude.mode==='max'?'selected':'')+'>Maximum altitude</option><option value="band" '+(cur.altitude.mode==='band'?'selected':'')+'>Altitude band</option></select></label><label><span>Minimum ft</span><input id="takGfAltMinV491" type="number" min="-2000" max="100000" step="100" value="'+(cur.altitude.min_ft==null?'':cur.altitude.min_ft)+'"></label><label><span>Maximum ft</span><input id="takGfAltMaxV491" type="number" min="-2000" max="100000" step="100" value="'+(cur.altitude.max_ft==null?'':cur.altitude.max_ft)+'"></label></div><small>Uses the altitude supplied by ADS-B.</small></div><div class="tak-gf-rules-v491"><span>Boundary confirmation: 2 seconds</span><span>Rearm delay: 10 seconds</span><span>One event per crossing</span></div></div><div class="tak-gf-modal-actions-v491">'+(editing?'<button type="button" class="danger" data-gf-remove>Remove Geofence</button>':'')+'<span></span><button type="button" data-gf-close>Cancel</button><button type="button" class="primary" data-gf-save>Save & Activate</button></div></div>'}
function openEditor(targetOrId){
 let target=null;
 let existing=null;
 if(typeof targetOrId==='string'&&FENCES.has(targetOrId)){
  existing=FENCES.get(targetOrId);
  const o=objectForId(existing.target_id);
  target={id:existing.target_id,kind:existing.kind,source:existing.target_source,name:existing.target_name,geometry:existing.geometry,object:o};
 }else if(typeof targetOrId==='string'){
  const o=objectForId(targetOrId);
  if(o)target={id:targetOrId,kind:objectKind(o),source:targetOrId.startsWith('datasync:')?'datasync':'local',name:objectName(o),geometry:geometryFromObject(o)};
 }else{
  target=targetOrId;
 }
 if(!target||!target.geometry){
  showNotice('Geofence unavailable','This shape or route does not expose usable canonical geometry.');
  return false;
 }
 if(!existing)existing=fenceForTarget(target.id);
 const ov=d.createElement('div');
 ov.className='tak-gf-overlay-v491';
 ov.id='takGeofenceEditorV491';
 ov.innerHTML=editorHtml(target,existing);
 const close=()=>ov.remove();
 ov.addEventListener('click',async e=>{
  if(e.target===ov||e.target.closest('[data-gf-close]')){
   close();
   return;
  }
  if(e.target.closest('[data-gf-save]')){
   const name=text($('takGfNameV491')&&$('takGfNameV491').value);
   const monitored=qa('[data-gf-source]:checked',ov).map(x=>x.dataset.gfSource);
   const triggers={};
   qa('[data-gf-trigger]',ov).forEach(x=>{triggers[x.dataset.gfTrigger]=!!x.checked});
   if(!name){showNotice('Name required','Enter a name for this geofence.');return}
   if(!monitored.length){showNotice('Monitoring required','Select at least one object class to monitor.');return}
   if(target.kind==='shape'&&!triggers.enter&&!triggers.exit&&!triggers.dwell){showNotice('Trigger required','Select Enter, Exit, or Dwell.');return}
   const altModeEl=$('takGfAltModeV491');
   const mode=altModeEl?altModeEl.value:'none';
   const minEl=$('takGfAltMinV491'),maxEl=$('takGfAltMaxV491');
   const min=num(minEl&&minEl.value),max=num(maxEl&&maxEl.value);
   if(mode==='band'&&min!=null&&max!=null&&min>max){showNotice('Altitude band invalid','Minimum altitude must not exceed maximum altitude.');return}
   const dwellEl=$('takGfDwellV491');
   const next=normalizedFence(Object.assign({},existing||{}, {
    id:existing&&existing.id,
    name,
    target_id:target.id,
    target_source:target.source,
    target_name:target.name,
    kind:target.kind,
    geometry:target.geometry,
    monitored,
    triggers,
    dwell_minutes:num(dwellEl&&dwellEl.value)||5,
    altitude:{mode,min_ft:min,max_ft:max},
    enabled:true,
    created_at:(existing&&existing.created_at)||nowIso()
   }));
   try{
    await saveFence(next);
    close();
    refreshPopupButtons();
    try{audioCtx=audioCtx||new (w.AudioContext||w.webkitAudioContext)();S.soundReady=true}catch(_){}
   }catch(err){
    showNotice('Save failed',String(err&&err.message||err));
   }
   return;
  }
  if(e.target.closest('[data-gf-remove]')){
   const b=e.target.closest('[data-gf-remove]');
   if(b.dataset.confirmed!=='1'){
    b.dataset.confirmed='1';
    b.textContent='Click Again to Remove';
    return;
   }
   try{
    await removeFence(existing.id);
    close();
   }catch(err){
    showNotice('Remove failed',String(err&&err.message||err));
   }
  }
 });
 d.body.appendChild(ov);
 return true;
}
function targetForPopupLayer(layer){
 let target=targetForLayer(layer);if(target)return target;
 try{const api=lifecycle(),entry=api&&api.entryForLayer&&api.entryForLayer(layer);if(entry&&entry.layers){for(const candidate of entry.layers){target=targetForLayer(candidate);if(target)return target}}}catch(_){}
 return null
}
function popupActionText(el){return text(el&&el.textContent).replace(/\s+/g,' ').toLowerCase()}
function popupEditCandidates(root){
 return qa('button,a,summary',root).filter(el=>{
  if(el.closest&&el.closest('.popup-edit-actions,.tak-popup-inline-edit-actions-v497'))return false;
  if(el.classList&&el.classList.contains('tak-geofence-popup-btn-v491'))return false;
  const label=popupActionText(el);return label==='edit'||label==='edit data'
 })
}
function popupEditorValue(editor,name,fallback){
 try{const el=editor&&editor.querySelector('[name="'+name+'"]');if(el)return text(el.value)}catch(_){}
 return text(fallback)
}
function popupEditMeta(holder,target,editor){
 const feature=holder.querySelector('.feature-popup')||holder;
 const ds=feature.dataset||{};
 const o=target&&target.object||{};
 const center=geometryCenter(target&&target.geometry)||{lat:num(o.lat),lon:num(o.lon!=null?o.lon:o.lng)};
 let key=text(ds.takInlineKey||editor&&editor.dataset&&editor.dataset.key);
 if(!key)try{if(typeof w.popupEditKey==='function')key=text(w.popupEditKey(o))}catch(_){}
 const source=text(ds.takInlineSource||editor&&editor.dataset&&editor.dataset.source||target&&target.source||sourceName(o,'TAK Map'));
 const objectId=text(ds.takInlineObjectId||editor&&editor.dataset&&editor.dataset.objectId||target&&target.id||canonicalId(o));
 const save=editor&&Array.from(editor.querySelectorAll('button')).find(b=>/^save$/i.test(text(b.textContent)));
 const del=editor&&Array.from(editor.querySelectorAll('button')).find(b=>/^delete$/i.test(text(b.textContent)));
 const canEdit=ds.takInlineCanEdit?ds.takInlineCanEdit==='1':!!key&&!(save&&save.disabled);
 const fallbackDelete=!!(objectId&&((target&&target.source)==='local'||o.delete_supported===true));
 const canDelete=ds.takInlineCanDelete?ds.takInlineCanDelete==='1':!!(del?!del.disabled:fallbackDelete);
 let asset='';try{asset=typeof w.assetDescriptor==='function'?w.assetDescriptor(o):text(o.asset)}catch(_){asset=text(o.asset)}
 let notes='';try{notes=typeof w.popupNotes==='function'?w.popupNotes(o):text(o.notes||o.remarks||o.description)}catch(_){notes=text(o.notes||o.remarks||o.description)}
 const kind=text(target&&target.kind||ds.takInlineKind||objectKind(o));
 const route=kind==='route',pts=route&&target&&target.geometry&&target.geometry.coordinates||[];
 if(route)notes=routeNotesV500(o);
 return {
  key,objectId,source,canEdit,canDelete,kind,
  name:popupEditorValue(editor,'name',ds.takInlineName||objectName(o)),
  type:popupEditorValue(editor,'type',ds.takInlineType||(route?(o.type||o.cot_type):(o.type||o.cot_type||o.category))),
  asset:popupEditorValue(editor,'asset',ds.takInlineAsset||asset),
  category:popupEditorValue(editor,'category',ds.takInlineCategory||(route?routeCategoryV500(o):text(o.category))),
  color:popupEditorValue(editor,'color',ds.takInlineColor||(route?routeColorV500(o):text(o.color))),
  lat:popupEditorValue(editor,'lat',ds.takInlineLat||(center&&center.lat!=null?Number(center.lat).toFixed(6):'')),
  lon:popupEditorValue(editor,'lon',ds.takInlineLon||(center&&center.lon!=null?Number(center.lon).toFixed(6):'')),
  notes:popupEditorValue(editor,'notes',ds.takInlineNotes||notes),
  length:route?routeDualDistanceV500(routeLengthMetersV500(target.geometry)):text(ds.takInlineLength),
  start:route?routeCoordV500(pts[0]):text(ds.takInlineStart),
  end:route?routeCoordV500(pts[pts.length-1]):text(ds.takInlineEnd),
  created:route?routeCreatedV500(o):text(ds.takInlineCreated),
  geofence:route?routeGeofenceStatusV500(target):text(ds.takInlineGeofence)
 }
}
function setPopupEditMeta(feature,meta){
 if(!feature||!feature.dataset)return;
 const ds=feature.dataset;
 ds.takInlineEditor='i498';ds.takInlineKey=text(meta.key);ds.takInlineObjectId=text(meta.objectId);ds.takInlineSource=text(meta.source);
 ds.takInlineCanEdit=meta.canEdit?'1':'0';ds.takInlineCanDelete=meta.canDelete?'1':'0';ds.takInlineKind=text(meta.kind);ds.takInlineName=text(meta.name);ds.takInlineType=text(meta.type);ds.takInlineAsset=text(meta.asset);ds.takInlineCategory=text(meta.category);ds.takInlineColor=text(meta.color);ds.takInlineLat=text(meta.lat);ds.takInlineLon=text(meta.lon);ds.takInlineNotes=text(meta.notes);ds.takInlineLength=text(meta.length);ds.takInlineStart=text(meta.start);ds.takInlineEnd=text(meta.end);ds.takInlineCreated=text(meta.created);ds.takInlineGeofence=text(meta.geofence)
}
function popupMetaForFeature(feature){
 const ds=feature&&feature.dataset||{};
 return {key:text(ds.takInlineKey),objectId:text(ds.takInlineObjectId),source:text(ds.takInlineSource),canEdit:ds.takInlineCanEdit==='1',canDelete:ds.takInlineCanDelete==='1',kind:text(ds.takInlineKind),name:text(ds.takInlineName),type:text(ds.takInlineType),asset:text(ds.takInlineAsset),category:text(ds.takInlineCategory),color:text(ds.takInlineColor),lat:text(ds.takInlineLat),lon:text(ds.takInlineLon),notes:text(ds.takInlineNotes),length:text(ds.takInlineLength),start:text(ds.takInlineStart),end:text(ds.takInlineEnd),created:text(ds.takInlineCreated),geofence:text(ds.takInlineGeofence)}
}
function popupFeature(root,content){return root.querySelector('.feature-popup,.tak-v322-popup,.tak-v321-popup,.tak-v320-popup')||content||root}
function popupBody(feature,content){
 if(feature&&feature.matches&&feature.matches('.tak-v322-popup,.tak-v321-popup,.tak-v320-popup'))return feature.querySelector('.tak-v322-inner,.tak-v321-inner,.tak-v320-inner')||feature;
 return feature||content
}
function popupValueTable(feature){return feature&&feature.querySelector('.kvp,.tak-v322-table,.tak-v321-table,.tak-v320-table')}
function normalizePopupPrimaryActions(root,content,feature){
 feature=feature||popupFeature(root,content);const body=popupBody(feature,content);
 let row=root.querySelector('.tak-popup-primary-actions-v492');
 if(!row){row=d.createElement('div');row.className='tak-popup-primary-actions-v492 tak-popup-primary-actions-v493 tak-geofence-popup-actions-v491';body.appendChild(row);S.popupButtons++}
 else{row.classList.add('tak-popup-primary-actions-v493','tak-geofence-popup-actions-v491');if(row.parentElement!==body)body.appendChild(row)}
 const candidates=popupEditCandidates(root);
 let edit=row.querySelector('.tak-popup-edit-toggle-v492,.tak-popup-edit-toggle-v493');
 if(!edit){
  const existing=candidates.find(el=>el.tagName==='BUTTON'&&!el.closest('.popup-edit'))||candidates.find(el=>el.tagName!=='SUMMARY'&&!el.closest('.popup-edit'));
  if(existing&&existing.tagName==='BUTTON')edit=existing;
  else{edit=d.createElement('button');edit.type='button';edit.textContent='Edit'}
  edit.classList.remove('legacy-popup-edit');edit.removeAttribute('style');edit.classList.add('layer-button','tak-popup-edit-toggle-v492','tak-popup-edit-toggle-v493');edit.type='button';edit.removeAttribute('onclick');edit.removeAttribute('href');row.appendChild(edit)
 }
 edit.textContent='Edit';edit.setAttribute('aria-expanded','false');edit.classList.remove('active');
 const meta=popupMetaForFeature(feature);edit.disabled=!meta.canEdit;edit.title=meta.canEdit?'Edit this shape or route.':'Editing is unavailable because this object has no stable source identity.';
 for(const candidate of popupEditCandidates(root)){if(candidate===edit)continue;try{candidate.remove()}catch(_){}}
 for(const extra of qa('.tak-popup-primary-actions-v492',root))if(extra!==row){for(const child of Array.from(extra.children))if(!row.contains(child))row.appendChild(child);extra.remove()}
 return row
}
function canonicalPopupStoredContent(popup,layer){
 const target=targetForPopupLayer(layer);if(!popup||!target)return false;
 POPUP_TARGETS.set(target.id,target);
 let raw=null;try{raw=popup.getContent?popup.getContent():popup._content}catch(_){raw=null}
 try{if(typeof raw==='function')raw=raw.call(layer,layer)}catch(_){return false}
 const holder=d.createElement('div');
 try{if(raw&&raw.nodeType)holder.appendChild(raw.cloneNode(true));else holder.innerHTML=String(raw==null?'':raw)}catch(_){return false}
 const content=holder.querySelector('.leaflet-popup-content')||holder;
 const feature=popupFeature(holder,content);
 if(target.kind==='route')enrichRoutePopupV500(feature,target);
 const editor=holder.querySelector('details.popup-edit,.popup-edit-source-v497,.popup-edit:not(.tak-popup-inline-editing-v497)');
 const meta=popupEditMeta(holder,target,editor);
 for(const oldEditor of qa('details.popup-edit,.popup-edit-source-v497',holder))oldEditor.remove();
 for(const oldEditor of qa('.popup-edit',holder))if(oldEditor!==feature&&!oldEditor.classList.contains('tak-popup-inline-editing-v497'))oldEditor.remove();
 feature.classList.remove('popup-edit','tak-popup-inline-editing-v497');feature.removeAttribute('open');setPopupEditMeta(feature,meta);
 const row=normalizePopupPrimaryActions(holder,content,feature);
 let button=row.querySelector('.tak-geofence-popup-btn-v491');
 if(!button){button=d.createElement('button');button.type='button';button.className='layer-button tak-geofence-popup-btn-v491';row.appendChild(button)}
 const fence=fenceForTarget(target.id);button.dataset.gfPopupTarget=target.id;if(fence)button.dataset.gfPopupFence=fence.id;else delete button.dataset.gfPopupFence;button.textContent=fence?'Edit Geofence':'Geofence';
 for(const obsolete of qa('.tak-geofence-popup-actions-v491',holder))if(obsolete!==row)obsolete.remove();
 if(fence)disablePopupDelete(holder,target.id);
 const html=holder.innerHTML;
 try{
  if(popup.setContent)popup.setContent(html);else popup._content=html;
  popup.__takCanonicalStoredContentV495=true;popup.__takCanonicalStoredContentV496=true;popup.__takCanonicalStoredContentV497=true;popup.__takCanonicalStoredContentV498=true;popup.__takCanonicalStoredContentV500=true;
  popup.__takCanonicalTargetIdV495=target.id;popup.__takCanonicalTargetIdV496=target.id;popup.__takCanonicalTargetIdV497=target.id;popup.__takCanonicalTargetIdV498=target.id;popup.__takCanonicalTargetIdV500=target.id;
  popup.__takCanonicalStoredMarkupV495=html;popup.__takCanonicalStoredMarkupV496=html;popup.__takCanonicalStoredMarkupV497=html;popup.__takCanonicalStoredMarkupV498=html;popup.__takCanonicalStoredMarkupV500=html;
  S.popupButtons++;return true
 }catch(_){return false}
}
function ensurePopupButton(ev){
 const popup=ev&&ev.popup,layer=popup&&popup._source;if(!popup||!layer)return false;
 const prepared=canonicalPopupStoredContent(popup,layer);
 setTimeout(()=>{
  const target=targetForPopupLayer(layer),root=popup.getElement&&popup.getElement();if(!target||!root)return;
  const content=root.querySelector('.leaflet-popup-content')||root,feature=popupFeature(root,content);
  const row=normalizePopupPrimaryActions(root,content,feature);
  let button=row.querySelector('.tak-geofence-popup-btn-v491');if(!button){button=d.createElement('button');button.type='button';button.className='layer-button tak-geofence-popup-btn-v491';row.appendChild(button)}
  const f=fenceForTarget(target.id);button.dataset.gfPopupTarget=target.id;if(f)button.dataset.gfPopupFence=f.id;else delete button.dataset.gfPopupFence;button.textContent=f?'Edit Geofence':'Geofence';if(f)disablePopupDelete(root,target.id)
 },0);
 return prepared
}
function popupRows(kvp){
 const rows=[];if(!kvp)return rows;
 const structured=qa(':scope>.tak-v322-row,:scope>.tak-v321-row,:scope>.tak-v320-row',kvp);
 if(structured.length){for(const item of structured){const children=Array.from(item.children||[]),label=children.find(el=>el.tagName==='B'),value=children.find(el=>el!==label);if(label&&value)rows.push({label:text(label.textContent).replace(/:$/,''),value:text(value.textContent)})}return rows}
 const children=Array.from(kvp.children||[]);
 for(let i=0;i<children.length;i++){const label=children[i];if(label.tagName!=='B')continue;const value=children[i+1];if(!value||value.tagName==='B')continue;rows.push({label:text(label.textContent).replace(/:$/,''),value:text(value.textContent)});i++}
 return rows
}
function inlineValue(label,value,meta,seen){
 const low=label.toLowerCase();
 if(low==='name'){seen.name=true;return '<b>Name</b><label class="tak-popup-inline-value-v497"><input name="name" value="'+esc(meta.name||value)+'"></label>'}
 if(low==='coordinates'||low==='center point'||low==='lat/lon'||low==='lat lon'){seen.coords=true;return '<b>'+esc(label)+'</b><div class="popup-edit-grid tak-popup-inline-coordinates-v497"><label><span>Lat</span><input name="lat" value="'+esc(meta.lat)+'"></label><label><span>Lon</span><input name="lon" value="'+esc(meta.lon)+'"></label></div>'}
 if(low==='notes'){seen.notes=true;return '<b>Notes</b><label class="tak-popup-inline-value-v497"><textarea name="notes" rows="2">'+esc(meta.notes||value)+'</textarea></label>'}
 if(low==='asset'){seen.asset=true;return '<b>Asset</b><label class="tak-popup-inline-value-v497"><input name="asset" value="'+esc(meta.asset||value)+'"></label>'}
 if(low==='type'){seen.type=true;return '<b>Type</b><label class="tak-popup-inline-value-v497"><input name="type" value="'+esc(meta.type||value)+'"></label>'}
 return '<b>'+esc(label)+'</b><label class="tak-popup-inline-value-v497 readonly"><input value="'+esc(value)+'" readonly></label>'
}
function routeOptionsV500(selected){return ROUTE_CATEGORIES_V500.map(c=>'<option value="'+esc(c)+'" '+(c===selected?'selected':'')+'>'+esc(c)+'</option>').join('')}
function routeInlineEditorHtmlV500(meta){const color=routeColorV500({color:meta.color});return '<b>Name</b><label class="tak-popup-inline-value-v497"><input name="name" value="'+esc(meta.name)+'"></label><b>Color</b><label class="tak-popup-inline-value-v497 tak-route-edit-color-v500"><span><input type="color" name="color" value="'+esc(color)+'"><code data-route-color-hex-v500>'+esc(color.toUpperCase())+'</code></span></label><b>Category</b><label class="tak-popup-inline-value-v497"><select name="category">'+routeOptionsV500(meta.category||'General')+'</select></label><b>Notes</b><label class="tak-popup-inline-value-v497"><textarea name="notes" rows="3">'+esc(meta.notes)+'</textarea></label><b>Length</b><label class="tak-popup-inline-value-v497 readonly"><input value="'+esc(meta.length)+'" readonly></label><b>Start</b><label class="tak-popup-inline-value-v497 readonly"><input value="'+esc(meta.start)+'" readonly></label><b>End</b><label class="tak-popup-inline-value-v497 readonly"><input value="'+esc(meta.end)+'" readonly></label><b>Created</b><label class="tak-popup-inline-value-v497 readonly"><input value="'+esc(meta.created)+'" readonly></label><b>Geofence</b><label class="tak-popup-inline-value-v497 readonly"><input value="'+esc(meta.geofence)+'" readonly></label><div class="tak-popup-inline-hidden-v497" hidden><input name="type" readonly value="'+esc(meta.type)+'"><input name="asset" readonly value="'+esc(meta.asset)+'"></div>'}
function inlineEditorHtml(kvp,meta){
 if(meta.kind==='route')return routeInlineEditorHtmlV500(meta);
 const seen={name:false,coords:false,notes:false,type:false,asset:false};let html='';for(const row of popupRows(kvp))html+=inlineValue(row.label,row.value,meta,seen);
 if(!seen.name)html='<b>Name</b><label class="tak-popup-inline-value-v497"><input name="name" value="'+esc(meta.name)+'"></label>'+html;
 if(!seen.coords&&(meta.lat||meta.lon))html+='<b>Coordinates</b><div class="popup-edit-grid tak-popup-inline-coordinates-v497"><label><span>Lat</span><input name="lat" value="'+esc(meta.lat)+'"></label><label><span>Lon</span><input name="lon" value="'+esc(meta.lon)+'"></label></div>';
 if(!seen.notes)html+='<b>Notes</b><label class="tak-popup-inline-value-v497"><textarea name="notes" rows="2">'+esc(meta.notes)+'</textarea></label>';
 html+='<div class="tak-popup-inline-hidden-v497" hidden>'+(seen.type?'':'<input name="type" value="'+esc(meta.type)+'">')+(seen.asset?'':'<input name="asset" value="'+esc(meta.asset)+'">')+'</div>';
 return html
}
function popupForRenderedRoot(root){try{const m=mapObj(),p=m&&m._popup;if(p&&p.getElement&&p.getElement()===root)return p}catch(_){}return null}
function restoreInlinePopup(feature){
 if(!feature)return false;const root=feature.closest('.leaflet-popup'),popup=popupForRenderedRoot(root);if(root)root.classList.remove('editing');
 if(popup){const html=popup.__takCanonicalStoredMarkupV500||popup.__takCanonicalStoredMarkupV498||popup.__takCanonicalStoredMarkupV497||popup.getContent&&popup.getContent();if(popup.setContent)popup.setContent(html);setTimeout(()=>ensurePopupButton({popup}),0);return true}
 return false
}
function startInlinePopupEdit(edit){
 const root=edit&&edit.closest&&edit.closest('.leaflet-popup');if(!root)return false;const content=root.querySelector('.leaflet-popup-content')||root,feature=popupFeature(root,content),kvp=popupValueTable(feature),row=feature&&feature.querySelector('.tak-popup-primary-actions-v492');if(!feature||!kvp||!row)return false;
 const meta=popupMetaForFeature(feature);if(!meta.canEdit)return false;const box=popupBody(feature,content);
 box.classList.add('popup-edit','tak-popup-inline-editing-v497');box.setAttribute('open','');box.dataset.key=meta.key;box.dataset.objectId=meta.objectId;box.dataset.source=meta.source;box.dataset.dirty='0';root.classList.add('editing');
 kvp.classList.add('tak-popup-inline-fields-v497');kvp.innerHTML=inlineEditorHtml(kvp,meta);
 row.classList.add('tak-popup-inline-edit-actions-v497');row.innerHTML='<button type="button" class="layer-button primary" data-tak-inline-action="save">Save</button><button type="button" class="layer-button" data-tak-inline-action="cancel">Cancel</button><button type="button" class="layer-button danger-action" data-tak-inline-action="delete">Delete</button><span class="popup-edit-status"></span>';
 const del=row.querySelector('[data-tak-inline-action="delete"]');del.disabled=!meta.canDelete;del.title=meta.canDelete?'Delete this shape or route.':'Deletion is unavailable because this object has no source-owned identity.';const targetId=text(root.querySelector('.tak-geofence-popup-btn-v491')&&root.querySelector('.tak-geofence-popup-btn-v491').dataset.gfPopupTarget||feature.dataset.takInlineObjectId);if(targetId)disablePopupDelete(root,targetId);
 const first=kvp.querySelector('[name="name"]');if(first&&first.focus)setTimeout(()=>{try{first.focus();first.select()}catch(_){}},0);return true
}
async function saveInlinePopup(button){
 const box=button&&button.closest&&button.closest('.tak-popup-inline-editing-v497');if(!box)return false;
 try{if(typeof w.savePopupEdit==='function')return await w.savePopupEdit(button)}catch(err){const status=box.querySelector('.popup-edit-status');if(status)status.textContent='Save failed: '+String(err&&err.message||err);return false}
 return false
}
async function deleteInlinePopup(button){
 const box=button&&button.closest&&button.closest('.tak-popup-inline-editing-v497');if(!box)return false;
 try{const api=lifecycle();if(api&&typeof api.deletePopupEdit==='function')return await api.deletePopupEdit(button);if(typeof w.deletePopupEdit==='function')return await w.deletePopupEdit(button)}catch(err){const status=box.querySelector('.popup-edit-status');if(status)status.textContent='Delete failed: '+String(err&&err.message||err)}return false
}
function bindPopupActionDelegation(){
 if(w.__takGeofencePopupDelegationV492)return;w.__takGeofencePopupDelegationV492=true;
 for(const type of ['pointerdown','mousedown','touchstart'])d.addEventListener(type,e=>{const b=e.target&&e.target.closest&&e.target.closest('.tak-geofence-popup-btn-v491,.tak-popup-edit-toggle-v492,.tak-popup-edit-toggle-v493,[data-tak-inline-action]');if(!b)return;e.preventDefault();e.stopPropagation();try{e.stopImmediatePropagation()}catch(_){}},true);
 d.addEventListener('input',e=>{const box=e.target&&e.target.closest&&e.target.closest('.tak-popup-inline-editing-v497');if(box)box.dataset.dirty='1';if(e.target&&e.target.matches&&e.target.matches('.tak-route-edit-color-v500 input[type="color"]')){const code=e.target.closest('.tak-route-edit-color-v500').querySelector('[data-route-color-hex-v500]');if(code)code.textContent=String(e.target.value||'').toUpperCase()}},true);d.addEventListener('change',e=>{if(e.target&&e.target.matches&&e.target.matches('.tak-route-edit-color-v500 input[type="color"]'))try{e.target.blur()}catch(_){}},true);
 d.addEventListener('keydown',e=>{const box=e.target&&e.target.closest&&e.target.closest('.tak-popup-inline-editing-v497');if(!box)return;if(e.key==='Escape'){e.preventDefault();restoreInlinePopup(box);return}if(e.key==='Enter'&&!e.shiftKey&&e.target&&e.target.tagName!=='TEXTAREA'){e.preventDefault();const focusable=qa('input:not([readonly]):not([disabled]),textarea:not([disabled]),button:not([disabled])',box);const i=focusable.indexOf(e.target),next=focusable[i+1];if(next&&next.focus)next.focus()}},true);
 d.addEventListener('click',e=>{
  const action=e.target&&e.target.closest&&e.target.closest('[data-tak-inline-action]');if(action){e.preventDefault();e.stopPropagation();try{e.stopImmediatePropagation()}catch(_){}const which=action.dataset.takInlineAction;if(which==='cancel'){restoreInlinePopup(action.closest('.tak-popup-inline-editing-v497'));return}if(which==='save'){saveInlinePopup(action);return}if(which==='delete'){deleteInlinePopup(action);return}}
  const edit=e.target&&e.target.closest&&e.target.closest('.tak-popup-edit-toggle-v492,.tak-popup-edit-toggle-v493');if(edit){e.preventDefault();e.stopPropagation();try{e.stopImmediatePropagation()}catch(_){}startInlinePopupEdit(edit);return}
  const b=e.target&&e.target.closest&&e.target.closest('.tak-geofence-popup-btn-v491');if(!b)return;e.preventDefault();e.stopPropagation();try{e.stopImmediatePropagation()}catch(_){};armSound();const fenceId=text(b.dataset.gfPopupFence),targetId=text(b.dataset.gfPopupTarget);let target=fenceId||POPUP_TARGETS.get(targetId)||targetId;try{if(!openEditor(target))showNotice('Geofence unavailable','This shape or route is not currently connected to a canonical map object.')}catch(err){S.lastError=String(err&&err.message||err);showNotice('Geofence unavailable',S.lastError)}
 },true)
}
function disablePopupDelete(root,id){
 const locked=protectedIds().has(id);
 for(const b of qa('button',root)){
  const deleteLike=/^delete$/i.test(text(b.textContent))||/delete/i.test(text(b.getAttribute('onclick')))||b.dataset.takGfProtectedDelete==='1';
  if(!deleteLike)continue;
  if(locked){if(b.dataset.takGfProtectedDelete!=='1')b.dataset.takGfOriginalText=text(b.textContent)||'Delete';b.dataset.takGfProtectedDelete='1';b.disabled=true;b.title='Remove the geofence before deleting this shape or route.';b.textContent='Delete unavailable'}
  else if(b.dataset.takGfProtectedDelete==='1'){b.disabled=false;b.title='';b.textContent=b.dataset.takGfOriginalText||'Delete';delete b.dataset.takGfProtectedDelete;delete b.dataset.takGfOriginalText}
 }
}
function refreshPopupButtons(){try{const m=mapObj(),p=m&&m._popup;if(p)ensurePopupButton({popup:p})}catch(_){}renderSidebar()}
function centerFence(id){const f=FENCES.get(id);if(!f)return;const m=mapObj(),g=f.geometry;if(!m||!g)return;if(g.type==='circle'){const c=[g.center[1],g.center[0]];m.setView(c,Math.max(m.getZoom(),13));return}const L=w.L;if(L&&g.coordinates&&g.coordinates.length){const b=L.latLngBounds(g.coordinates.map(p=>[p[1],p[0]]));if(b.isValid())m.fitBounds(b,{padding:[40,40]})}}
function placeSidebarPanel(panel){
 const sidebar=$('sidebar');if(!sidebar||!panel)return panel;
 const titleOf=p=>text(p&&p.querySelector&&p.querySelector('h2')&&p.querySelector('h2').textContent);
 const panels=qa('.panel',sidebar),basemap=panels.find(p=>/^Basemap\b/i.test(titleOf(p))),adsb=panels.find(p=>/^ADS-B\b/i.test(titleOf(p)));
 panel.dataset.manualCollapse='true';panel.dataset.skipAutoCollapsible='true';panel.dataset.collapsibleReady='1';
 if(basemap&&adsb&&basemap!==panel&&adsb!==panel){if(basemap.nextElementSibling!==panel)basemap.insertAdjacentElement('afterend',panel);if(panel.nextElementSibling!==adsb)panel.insertAdjacentElement('afterend',adsb)}
 else if(adsb&&adsb!==panel){if(adsb.previousElementSibling!==panel)adsb.insertAdjacentElement('beforebegin',panel)}
 else if(basemap&&basemap!==panel){if(basemap.nextElementSibling!==panel)basemap.insertAdjacentElement('afterend',panel)}
 else if(panel.parentElement!==sidebar)sidebar.appendChild(panel);
 return panel
}
function ensureSidebar(){
 let panel=$('geofencePanelV491');if(panel)return placeSidebarPanel(panel);
 const sidebar=$('sidebar');if(!sidebar)return null;
 panel=d.createElement('div');panel.id='geofencePanelV491';panel.className='panel tak-gf-panel-v491';panel.innerHTML='<div class="tak-gf-card-head-v491"><h2>Geofences</h2><div class="tak-gf-head-actions-v491"><span id="takGfCountV491" class="chip tak-header-count-v491">0 ACTIVE, 0 TOTAL</span><label class="tak-gf-switch-v491" title="Enable Geofencing"><input id="takGfMasterV491" type="checkbox" checked><span><i></i></span></label><button id="takGfCollapseV491" class="tak-gf-collapse-v491" type="button">▾</button></div></div><div id="takGfBodyV491" class="tak-gf-card-body-v491"><div class="tak-gf-toolbar-v491"><div class="tak-gf-segmented-v491"><button data-gf-filter="all" class="active">All</button><button data-gf-filter="area">Area</button><button data-gf-filter="route">Route</button></div><span id="takGfLiveV491">Monitoring live</span></div><div id="takGfRowsV491" class="tak-gf-list-v491"></div></div>';
 placeSidebarPanel(panel);
 const head=panel.querySelector('.tak-gf-card-head-v491'),body=$('takGfBodyV491'),collapse=$('takGfCollapseV491'),master=$('takGfMasterV491');
 const applyCollapsed=(closed,persist)=>{closed=!!closed;panel.classList.toggle('collapsed',closed);if(head){head.setAttribute('role','button');head.setAttribute('tabindex','0');head.setAttribute('aria-expanded',closed?'false':'true');head.setAttribute('aria-label',closed?'Expand Geofences card':'Collapse Geofences card')}if(body)body.setAttribute('aria-hidden',closed?'true':'false');if(collapse){if(collapse.textContent!==(closed?'▸':'▾'))collapse.textContent=closed?'▸':'▾';collapse.setAttribute('aria-expanded',closed?'false':'true');collapse.setAttribute('aria-label',closed?'Expand Geofences':'Collapse Geofences');collapse.title=closed?'Expand Geofences':'Collapse Geofences'}if(persist){try{localStorage.setItem('takMapPanelCollapsed:geofences',closed?'1':'0')}catch(_){}}setTimeout(()=>{try{const m=mapObj();if(m&&typeof m.invalidateSize==='function')m.invalidateSize({pan:false})}catch(_){}},50)};
 let collapsed=false;try{collapsed=localStorage.getItem('takMapPanelCollapsed:geofences')==='1'}catch(_){}applyCollapsed(collapsed,false);
 const switchTarget=target=>!!(target&&target.closest&&target.closest('.tak-gf-switch-v491,#takGfMasterV491'));
 const toggleCollapsed=()=>applyCollapsed(!panel.classList.contains('collapsed'),true);
 if(head){head.addEventListener('click',e=>{if(switchTarget(e.target))return;e.preventDefault();toggleCollapsed()});head.addEventListener('keydown',e=>{if(e.target!==head||(e.key!=='Enter'&&e.key!==' '))return;e.preventDefault();toggleCollapsed()})}
 master.addEventListener('change',e=>{S.master=!!e.target.checked;try{sessionStorage.setItem('takmap.geofence.master',S.master?'1':'0')}catch(_){}renderSidebar()});
 panel.addEventListener('click',e=>{const fb=e.target.closest('[data-gf-filter]');if(fb){S.filter=fb.dataset.gfFilter;renderSidebar();return}const b=e.target.closest('[data-gf-action]');if(!b)return;const id=b.dataset.gfId,action=b.dataset.gfAction;if(action==='center')centerFence(id);if(action==='edit')openEditor(id);if(action==='pause')setFenceEnabled(id,false);if(action==='enable')setFenceEnabled(id,true)});
 return panel
}
function renderSidebar(){ensureSidebar();const rows=$('takGfRowsV491'),count=$('takGfCountV491'),live=$('takGfLiveV491');if(!rows)return;const all=Array.from(FENCES.values()),active=all.filter(f=>f.enabled!==false).length;if(count)count.textContent=active+' ACTIVE, '+all.length+' TOTAL';if(live)live.textContent=S.master?'Monitoring live':'Monitoring paused';for(const b of qa('[data-gf-filter]',$('geofencePanelV491')))b.classList.toggle('active',b.dataset.gfFilter===S.filter);const shown=all.filter(f=>S.filter==='all'||(S.filter==='area'&&f.kind==='shape')||(S.filter==='route'&&f.kind==='route'));rows.innerHTML=shown.length?shown.map(f=>'<div class="tak-gf-row-v491 '+(f.enabled!==false?'armed':'paused')+'"><div class="tak-gf-row-main-v491"><div class="tak-gf-geom-v491 '+f.kind+'">'+(f.kind==='route'?'↗':'◇')+'</div><div class="tak-gf-row-copy-v491"><b>'+esc(f.name)+'</b><small>'+esc(monitoredLabel(f)+' · '+triggerLabel(f)+altitudeLabel(f))+'</small></div><span class="tak-gf-state-v491 '+(f.enabled!==false?'':'paused')+'">'+(f.enabled!==false?'Armed':'Paused')+'</span></div><div class="tak-gf-row-actions-v491"><button data-gf-action="center" data-gf-id="'+esc(f.id)+'">Center</button><button data-gf-action="edit" data-gf-id="'+esc(f.id)+'">Edit</button><button data-gf-action="'+(f.enabled!==false?'pause':'enable')+'" data-gf-id="'+esc(f.id)+'">'+(f.enabled!==false?'Pause':'Enable')+'</button></div></div>').join(''):'<div class="tak-gf-empty-v491">No geofences configured. Open a shape or route popup and select Geofence.</div>';placeSidebarPanel($('geofencePanelV491'))}
function eventWindowLimits(win,top){const min=132,safeTop=92,t=Number.isFinite(top)?Math.max(safeTop,top):Math.max(safeTop,win.getBoundingClientRect().top);return {min,max:Math.max(min,w.innerHeight-t-6)}}
function saveEventWindowState(win){if(!win)return;const r=win.getBoundingClientRect();try{sessionStorage.setItem('takmap.geofence.events.pos',JSON.stringify({left:Math.round(r.left),top:Math.round(r.top)}));if(win.classList.contains('tak-gf-resized-v492'))sessionStorage.setItem('takmap.geofence.events.height',String(Math.round(r.height)));sessionStorage.setItem('takmap.geofence.events.collapsed',S.eventsCollapsed?'1':'0')}catch(_){}}
function ensureEventWindow(){
 if(!FENCES.size)return null;let existing=$('takGeofenceEventsV491');if(existing)return existing;
 const win=d.createElement('section');win.id='takGeofenceEventsV491';win.className='tak-gf-events-v491';win.innerHTML='<div class="tak-gf-resize-v492 top" data-gf-resize="top" title="Resize height"></div><div class="tak-gf-events-head-v491"><div class="tak-gf-events-title-v491"><span></span><b>Geofence Alerts</b></div><span id="takGfEventCountV491" class="tak-gf-event-count-v491">0 EVENTS</span><button id="takGfEventMinV491" type="button" title="Minimize"><i></i></button></div><div id="takGfEventsBodyV491" class="tak-gf-events-body-v491"><div id="takGfEventRowsV491"></div><div class="tak-gf-events-foot-v491"><span>Newest first · sound enabled</span><button id="takGfClearEventsV491" type="button">Clear</button></div></div><div class="tak-gf-resize-v492 bottom" data-gf-resize="bottom" title="Resize height"></div>';
 d.body.appendChild(win);
 const pos=(()=>{try{return JSON.parse(sessionStorage.getItem('takmap.geofence.events.pos')||'null')}catch(_){return null}})();if(pos&&Number.isFinite(pos.left)&&Number.isFinite(pos.top)){win.style.left=pos.left+'px';win.style.top=pos.top+'px';win.style.right='auto';win.style.bottom='auto';S.dragged=true}
 let savedHeight=0;try{savedHeight=Number(sessionStorage.getItem('takmap.geofence.events.height')||0);S.eventsCollapsed=sessionStorage.getItem('takmap.geofence.events.collapsed')==='1'}catch(_){}if(Number.isFinite(savedHeight)&&savedHeight>0){const r=win.getBoundingClientRect(),lim=eventWindowLimits(win,r.top);win.style.height=Math.max(lim.min,Math.min(lim.max,savedHeight))+'px';win.classList.add('tak-gf-resized-v492')}win.classList.toggle('collapsed',S.eventsCollapsed);
 const minBtn=$('takGfEventMinV491');minBtn.classList.toggle('restore',S.eventsCollapsed);minBtn.title=S.eventsCollapsed?'Restore':'Minimize';
 const head=win.querySelector('.tak-gf-events-head-v491');let drag=null;head.addEventListener('pointerdown',e=>{if(e.target.closest('button'))return;const r=win.getBoundingClientRect();drag={x:e.clientX,y:e.clientY,left:r.left,top:r.top};head.setPointerCapture(e.pointerId);e.preventDefault()});head.addEventListener('pointermove',e=>{if(!drag)return;const left=Math.max(6,Math.min(w.innerWidth-win.offsetWidth-6,drag.left+e.clientX-drag.x)),top=Math.max(92,Math.min(w.innerHeight-win.offsetHeight-6,drag.top+e.clientY-drag.y));win.style.left=left+'px';win.style.top=top+'px';win.style.right='auto';win.style.bottom='auto';S.dragged=true});head.addEventListener('pointerup',e=>{if(!drag)return;drag=null;try{head.releasePointerCapture(e.pointerId)}catch(_){}saveEventWindowState(win)});
 let resize=null;for(const grip of qa('[data-gf-resize]',win)){grip.addEventListener('pointerdown',e=>{if(S.eventsCollapsed)return;const r=win.getBoundingClientRect();win.style.left=r.left+'px';win.style.top=r.top+'px';win.style.right='auto';win.style.bottom='auto';win.style.height=r.height+'px';win.classList.add('tak-gf-resized-v492');resize={edge:grip.dataset.gfResize,y:e.clientY,top:r.top,bottom:r.bottom,height:r.height};grip.setPointerCapture(e.pointerId);e.preventDefault();e.stopPropagation()});grip.addEventListener('pointermove',e=>{if(!resize)return;const lim=eventWindowLimits(win,resize.edge==='top'?Math.max(92,resize.bottom-(resize.height+resize.y-e.clientY)):resize.top);if(resize.edge==='top'){const max=Math.max(lim.min,resize.bottom-92),height=Math.max(lim.min,Math.min(max,resize.height+resize.y-e.clientY));win.style.top=(resize.bottom-height)+'px';win.style.height=height+'px'}else{const max=Math.max(lim.min,w.innerHeight-resize.top-6),height=Math.max(lim.min,Math.min(max,resize.height+e.clientY-resize.y));win.style.top=resize.top+'px';win.style.height=height+'px'}e.preventDefault()});grip.addEventListener('pointerup',e=>{if(!resize)return;resize=null;try{grip.releasePointerCapture(e.pointerId)}catch(_){}saveEventWindowState(win)})}
 minBtn.addEventListener('click',()=>{S.eventsCollapsed=!S.eventsCollapsed;win.classList.toggle('collapsed',S.eventsCollapsed);minBtn.classList.toggle('restore',S.eventsCollapsed);minBtn.title=S.eventsCollapsed?'Restore':'Minimize';saveEventWindowState(win)});$('takGfClearEventsV491').addEventListener('click',()=>{EVENTS.length=0;renderEvents()});
 w.addEventListener('resize',()=>{if(!win.isConnected||S.eventsCollapsed)return;const r=win.getBoundingClientRect(),lim=eventWindowLimits(win,r.top),height=Math.max(lim.min,Math.min(lim.max,r.height)),left=Math.max(6,Math.min(w.innerWidth-r.width-6,r.left)),top=Math.max(92,Math.min(w.innerHeight-height-6,r.top));win.style.left=left+'px';win.style.top=top+'px';win.style.right='auto';win.style.bottom='auto';if(win.classList.contains('tak-gf-resized-v492'))win.style.height=height+'px';saveEventWindowState(win)});
 return win
}
function renderEvents(){if(!FENCES.size){const old=$('takGeofenceEventsV491');if(old)old.remove();return}ensureEventWindow();const rows=$('takGfEventRowsV491'),count=$('takGfEventCountV491');if(!rows)return;if(count)count.textContent=EVENTS.length+' EVENT'+(EVENTS.length===1?'':'S');rows.innerHTML=EVENTS.length?EVENTS.map(ev=>'<div class="tak-gf-event-v491"><div class="tak-gf-event-copy-v491"><span class="tak-gf-trigger-v491 '+ev.type+'">'+esc(ev.type)+'</span><div><div><strong>'+esc(ev.object_name)+'</strong> · '+esc(ev.fence_name)+'</div><small>'+esc(sourceLabel(ev.source)+(ev.altitude_ft!=null?' · '+Math.round(ev.altitude_ft).toLocaleString()+' ft':'')+(ev.extra?' · '+ev.extra:''))+'</small></div></div><time>'+new Date(ev.time).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'})+'</time></div>').join(''):'<div class="tak-gf-events-empty-v491">No geofence events.</div>'}
function renderAll(){renderSidebar();renderEvents();applyProtectionUi()}
function applyProtectionUi(){const ids=protectedIds(),api=lifecycle();if(api&&api.registryById){for(const [id,e] of api.registryById){const locked=ids.has(id);if(e&&e.object){if(locked)e.object._takGeofenceProtected=true;else delete e.object._takGeofenceProtected}for(const l of e&&e.layers||[]){if(locked)l._takGeofenceProtected=true;else delete l._takGeofenceProtected}}}try{const m=mapObj(),p=m&&m._popup,root=p&&p.getElement&&p.getElement(),layer=p&&p._source,id=layer&&text(layer._takCanonicalObjectId||layer._takSelectionCanonicalId);if(root&&id)disablePopupDelete(root,id)}catch(_){} }
function selectedProtected(){const ids=protectedIds(),out=[];try{const st=w.__takSelectionStateV477;for(const item of st&&st.selected||[]){const layer=(item.layers&&item.layers[0])||item.layer,id=layer&&layer._takCanonicalObjectId;if(id&&ids.has(id))out.push(id)}}catch(_){}return out}
function localSelectedProtected(kind){const ids=protectedIds(),out=[];try{const st=stateObj();for(const id of Object.keys(st.local&&st.local[kind]||{})){if(!st.local[kind][id])continue;const o=(typeof w.localDataFeatureById==='function'?w.localDataFeatureById(id):null),cid=canonicalId(o);if(cid&&ids.has(cid))out.push(cid)}}catch(_){}return out}
function captureProtection(){if(w.__takGeofenceProtectionCaptureV491)return;w.__takGeofenceProtectionCaptureV491=true;d.addEventListener('click',e=>{const b=e.target&&e.target.closest&&e.target.closest('button');if(!b)return;let blocked=[];if(b.id==='selectionDeleteBtn')blocked=selectedProtected();const src=text(b.dataset&&b.dataset.takDeleteSource);if(src==='local')blocked=localSelectedProtected(text(b.dataset.takDeleteKind));if(src==='datasync'){const idx=Number(b.dataset.takDeleteIndex),o=(currentDataSync().objects||[])[idx],id=canonicalId(o);if(id&&protectedIds().has(id))blocked=[id]}if(!blocked.length&&/^delete$/i.test(text(b.textContent))){try{const p=b.closest('.leaflet-popup'),m=mapObj(),layer=m&&m._popup&&m._popup._source,id=layer&&layer._takCanonicalObjectId;if(p&&id&&protectedIds().has(id))blocked=[id]}catch(_){}}if(!blocked.length)return;e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();S.protectedBlocks++;showNotice('Object protected by geofence','Remove the geofence rule before deleting this shape or route.')},true)}
function installCss(){if($('takMapGeofencingStyleV491'))return;const st=d.createElement('style');st.id='takMapGeofencingStyleV491';st.textContent=`
.adsb-type-card-v491 input:checked+.adsb-type-card-label-v491,.adsb-type-card-v491:has(input:checked){border-color:rgba(215,223,228,.72)!important;background:rgba(215,223,228,.10)!important;box-shadow:inset 0 0 0 1px rgba(255,255,255,.06)!important}.adsb-type-card-v491 input:checked~.adsb-type-check-v491,.adsb-type-checkbox-v491:checked~.adsb-type-check-v491{border-color:#d7dfe4!important;background:#d7dfe4!important;color:#12181d!important}
.tak-geofence-pulse-v491{animation:takGfPulseV491 1s ease-in-out 9!important;filter:drop-shadow(0 0 4px #ff342e) drop-shadow(0 0 12px #ff342e)!important}@keyframes takGfPulseV491{0%,100%{filter:drop-shadow(0 0 2px rgba(255,52,46,.55)) drop-shadow(0 0 7px rgba(255,52,46,.5))}50%{filter:drop-shadow(0 0 7px #ff342e) drop-shadow(0 0 20px #ff342e)}}
.tak-gf-panel-v491{padding:0!important;overflow:hidden}.tak-gf-card-head-v491{min-height:46px;cursor:pointer;display:grid;grid-template-columns:minmax(0,1fr) auto;align-items:center;gap:8px;padding:8px 10px 8px 12px;border-bottom:1px solid rgba(255,255,255,.08)}.tak-gf-card-head-v491 h2{margin:0!important}.tak-gf-head-actions-v491{display:grid;grid-template-columns:max-content 40px 14px;align-items:center;gap:8px}.tak-gf-switch-v491{position:relative;display:inline-flex}.tak-gf-switch-v491 input{position:absolute;opacity:0}.tak-gf-switch-v491>span{display:block;width:38px;height:20px;border:1px solid #455561;border-radius:999px;background:#17212a;position:relative}.tak-gf-switch-v491 i{position:absolute;left:2px;top:2px;width:14px;height:14px;border-radius:50%;background:#91a2ad;transition:.15s}.tak-gf-switch-v491 input:checked+span{border-color:rgba(57,217,138,.65);background:rgba(57,217,138,.18)}.tak-gf-switch-v491 input:checked+span i{transform:translateX(18px);background:#39d98a;box-shadow:0 0 8px rgba(57,217,138,.65)}.tak-gf-collapse-v491{border:0;background:transparent;color:#b8c3cb;font-weight:1000;padding:0}.tak-gf-panel-v491.collapsed .tak-gf-card-body-v491{display:none}.tak-gf-card-body-v491{padding:10px}.tak-gf-toolbar-v491{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:8px}.tak-gf-segmented-v491{display:inline-flex;padding:2px;border:1px solid rgba(255,255,255,.1);border-radius:8px;background:#0a1016}.tak-gf-segmented-v491 button{border:0;border-radius:6px;padding:5px 8px;color:#82949e;background:transparent;font-size:.61rem;font-weight:900;text-transform:uppercase}.tak-gf-segmented-v491 button.active{color:#eef4f6;background:#24303a}.tak-gf-toolbar-v491>span{color:#758791;font-size:.62rem;font-weight:800}.tak-gf-list-v491{display:grid;gap:7px}.tak-gf-row-v491{border:1px solid rgba(255,255,255,.1);border-radius:9px;background:linear-gradient(180deg,rgba(255,255,255,.026),rgba(255,255,255,.012))}.tak-gf-row-v491.armed{border-color:rgba(255,111,46,.29);box-shadow:inset 2px 0 0 #ff6f2e}.tak-gf-row-main-v491{display:grid;grid-template-columns:34px minmax(0,1fr) auto;gap:9px;align-items:center;min-height:52px;padding:7px 8px}.tak-gf-geom-v491{width:32px;height:32px;display:grid;place-items:center;border:1px solid rgba(255,255,255,.15);border-radius:8px;background:#131c24;font-weight:950}.tak-gf-geom-v491.route{color:#ffd166}.tak-gf-geom-v491.shape{color:#b475ff}.tak-gf-row-copy-v491{min-width:0}.tak-gf-row-copy-v491 b,.tak-gf-row-copy-v491 small{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.tak-gf-row-copy-v491 b{font-size:.73rem;color:#edf4f7}.tak-gf-row-copy-v491 small{margin-top:3px;color:#7f919c;font-size:.59rem}.tak-gf-state-v491{border:1px solid rgba(92,219,145,.35);border-radius:999px;padding:2px 6px;color:#a9f1c8;background:rgba(92,219,145,.08);font-size:.54rem;font-weight:950;text-transform:uppercase}.tak-gf-state-v491.paused{border-color:rgba(162,173,181,.27);color:#a7b3bb;background:rgba(162,173,181,.06)}.tak-gf-row-actions-v491{display:grid;grid-template-columns:repeat(3,1fr);gap:5px;padding:0 8px 8px 51px}.tak-gf-row-actions-v491 button{border:1px solid rgba(255,255,255,.12);border-radius:7px;padding:5px 6px;color:#cbd6db;background:#111920;font-size:.58rem;font-weight:900;text-transform:uppercase}.tak-gf-empty-v491{padding:12px;color:#83949e;font-size:.7rem;line-height:1.45}
.tak-popup-primary-actions-v492{display:flex!important;align-items:center!important;justify-content:flex-start!important;gap:7px!important;flex-wrap:nowrap!important;margin:9px 0 0!important;padding-top:8px!important;border-top:1px solid rgba(255,255,255,.08)!important}.tak-popup-primary-actions-v492 .layer-button{width:auto!important;min-width:0!important;margin:0!important;white-space:nowrap!important}.tak-popup-summary-hidden-v492,.tak-popup-summary-hidden-v493{display:none!important}.leaflet-popup details.popup-edit.tak-popup-edit-managed-v492, .leaflet-popup details.popup-edit.tak-popup-edit-managed-v493{display:block!important;width:100%!important;max-width:none!important;margin:0!important;padding:0!important}.leaflet-popup details.popup-edit.tak-popup-edit-managed-v492[open], .leaflet-popup details.popup-edit.tak-popup-edit-managed-v493[open]{margin-top:8px!important}.tak-popup-edit-toggle-v492.active,.tak-popup-edit-toggle-v492[aria-expanded="true"]{border-color:rgba(255,111,46,.52)!important;background:rgba(255,111,46,.12)!important;color:#ffe0d1!important}.tak-gf-popup-actions-v491:not(.tak-popup-primary-actions-v492){display:none!important}
.tak-gf-overlay-v491{position:fixed;inset:0;z-index:22000;display:grid;place-items:center;padding:18px;background:rgba(0,0,0,.7);backdrop-filter:blur(3px)}.tak-gf-modal-v491,.tak-gf-notice-v491{width:min(580px,calc(100vw - 36px));max-height:calc(100vh - 36px);overflow:hidden;border:1px solid rgba(255,111,46,.42);border-radius:16px;background:linear-gradient(180deg,rgba(16,25,34,.99),rgba(7,13,19,.99));box-shadow:0 28px 80px rgba(0,0,0,.68);color:#dce6ea}.tak-gf-modal-head-v491{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:14px 16px 11px;border-bottom:1px solid rgba(255,255,255,.075)}.tak-gf-modal-head-v491 b,.tak-gf-modal-head-v491 small{display:block}.tak-gf-modal-head-v491 b{font-size:.93rem;color:#f1f6f8}.tak-gf-modal-head-v491 small{margin-top:2px;color:#8396a0;font-size:.67rem}.tak-gf-modal-head-v491 button{width:30px;height:30px;border:1px solid rgba(255,255,255,.13);border-radius:8px;background:#15212a;color:#dce6ea}.tak-gf-modal-body-v491{max-height:calc(100vh - 170px);overflow:auto;padding:14px 16px}.tak-gf-field-v491,.tak-gf-alt-grid-v491 label{display:grid;gap:4px;color:#91a2ad;font-size:.66rem;font-weight:850;text-transform:uppercase}.tak-gf-field-v491 input,.tak-gf-alt-grid-v491 input,.tak-gf-alt-grid-v491 select{width:100%;border:1px solid #334553;border-radius:9px;background:#091018;color:#edf4f7;padding:8px 9px;font-size:.78rem}.tak-gf-section-v491{margin-top:13px;padding-top:11px;border-top:1px solid rgba(255,255,255,.07)}.tak-gf-section-v491>b{display:block;margin-bottom:8px;font-size:.7rem;text-transform:uppercase;letter-spacing:.07em}.tak-gf-section-v491>small{display:block;margin-top:6px;color:#758791;font-size:.63rem}.tak-gf-check-grid-v491,.tak-gf-trigger-grid-v491{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px}.tak-gf-check-grid-v491 label,.tak-gf-trigger-grid-v491 label{display:grid;grid-template-columns:18px minmax(0,1fr);gap:7px;align-items:center;padding:7px 8px;border:1px solid rgba(255,255,255,.09);border-radius:8px;background:rgba(255,255,255,.02);cursor:pointer}.tak-gf-check-grid-v491 input,.tak-gf-trigger-grid-v491 input{position:absolute;opacity:0}.tak-gf-box-v491{width:17px;height:17px;display:grid;place-items:center;border:1px solid rgba(255,255,255,.25);border-radius:5px;color:transparent;background:rgba(0,0,0,.25);font-size:.68rem;font-weight:950}.tak-gf-check-grid-v491 input:checked+.tak-gf-box-v491,.tak-gf-trigger-grid-v491 input:checked+.tak-gf-box-v491{border-color:#d7dfe4;background:#d7dfe4;color:#12181d}.tak-gf-check-grid-v491 em,.tak-gf-trigger-grid-v491 em{font-style:normal;color:#dbe5e9;font-size:.7rem;font-weight:800}.tak-gf-dwell-v491{margin-top:8px}.tak-gf-alt-grid-v491{display:grid;grid-template-columns:1.1fr 1fr 1fr;gap:7px}.tak-gf-rules-v491{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px}.tak-gf-rules-v491 span{border:1px solid rgba(255,111,46,.22);border-radius:999px;padding:3px 7px;color:#d3dde2;background:rgba(255,111,46,.065);font-size:.59rem;font-weight:800}.tak-gf-modal-actions-v491{display:grid;grid-template-columns:auto 1fr auto auto;gap:8px;align-items:center;padding:11px 16px 15px;border-top:1px solid rgba(255,255,255,.065)}.tak-gf-modal-actions-v491 button{padding:8px 12px;border:1px solid #3b4b57;border-radius:10px;background:#15212a;color:#dbe5e9;font-size:.74rem;font-weight:850}.tak-gf-modal-actions-v491 button.primary{border-color:rgba(255,111,46,.6);background:rgba(255,111,46,.17);color:#ffe1d3}.tak-gf-modal-actions-v491 button.danger{border-color:rgba(255,95,87,.55);background:rgba(255,95,87,.12);color:#ffd1ce}.tak-gf-notice-v491{width:min(420px,calc(100vw - 36px))}.tak-gf-notice-body-v491{padding:17px;color:#d7e1e6;font-size:.8rem;line-height:1.5}
.feature-popup.tak-popup-inline-editing-v497.popup-edit{margin:0!important;padding:0!important;border:0!important;border-radius:0!important;background:transparent!important;box-shadow:none!important;overflow:visible!important;width:auto!important;max-width:none!important}.tak-v322-inner.tak-popup-inline-editing-v497.popup-edit,.tak-v321-inner.tak-popup-inline-editing-v497.popup-edit,.tak-v320-inner.tak-popup-inline-editing-v497.popup-edit{margin:0!important;padding:14px 15px 13px!important;border:0!important;border-radius:0!important;background:transparent!important;box-shadow:none!important;overflow:visible!important;width:auto!important;max-width:none!important}.tak-popup-inline-fields-v497{display:grid!important;grid-template-columns:104px minmax(0,1fr)!important;gap:0!important;align-items:start!important;width:100%!important}.tak-popup-inline-fields-v497>b{padding:7px 13px 7px 0!important;border-top:1px solid rgba(255,255,255,.075)!important;font-size:.66rem!important;text-transform:uppercase!important;letter-spacing:.065em!important;color:#91a8b3!important;font-weight:900!important;white-space:nowrap!important}.tak-popup-inline-fields-v497>.tak-popup-inline-value-v497,.tak-popup-inline-fields-v497>.tak-popup-inline-coordinates-v497{padding:5px 0!important;border-top:1px solid rgba(255,255,255,.075)!important}.tak-popup-inline-value-v497{display:block!important;margin:0!important;padding:0!important;text-transform:none!important;letter-spacing:normal!important}.tak-popup-inline-value-v497 input,.tak-popup-inline-value-v497 textarea,.tak-popup-inline-coordinates-v497 input{width:100%!important;margin:0!important;background:#0b151e!important;color:#f3f8fb!important;border:1px solid rgba(255,255,255,.22)!important;border-radius:7px!important;padding:6px 7px!important;font-size:.76rem!important;font-weight:650!important;box-sizing:border-box!important}.tak-popup-inline-value-v497 textarea{min-height:56px!important;resize:vertical!important}.tak-popup-inline-value-v497.readonly input{color:#a9bac4!important;background:rgba(255,255,255,.035)!important;border-color:rgba(255,255,255,.1)!important}.tak-popup-inline-coordinates-v497{display:grid!important;grid-template-columns:1fr 1fr!important;gap:6px!important}.tak-popup-inline-coordinates-v497 label{display:flex!important;flex-direction:column!important;gap:3px!important;margin:0!important;padding:0!important;color:#91a5b1!important;font-size:.6rem!important;text-transform:uppercase!important;letter-spacing:.055em!important}.tak-popup-inline-edit-actions-v497{flex-wrap:wrap!important}.tak-popup-inline-edit-actions-v497 .popup-edit-status{flex:1 1 100%!important;min-height:1em!important}.tak-popup-inline-edit-actions-v497 [data-tak-inline-action="save"]{border-color:rgba(57,217,138,.52)!important;color:#c8f7dc!important}.tak-popup-inline-edit-actions-v497 [data-tak-inline-action="delete"]{border-color:rgba(255,95,87,.48)!important;color:#ffc2be!important}.tak-popup-inline-edit-actions-v497 button:disabled{opacity:.42!important;cursor:not-allowed!important}
.tak-route-color-value-v500{display:inline-flex!important;align-items:center!important;gap:8px!important}.tak-route-color-value-v500 i{width:17px!important;height:17px!important;flex:0 0 17px!important;border:1px solid rgba(255,255,255,.45)!important;border-radius:4px!important;background:var(--tak-route-color)!important;box-shadow:0 0 0 2px rgba(0,0,0,.22)!important}.tak-route-color-value-v500 code,.tak-route-edit-color-v500 code{color:#dce9ee!important;font-family:ui-monospace,SFMono-Regular,Consolas,monospace!important;font-size:.75rem!important}.tak-popup-inline-value-v497 select{width:100%!important;margin:0!important;background:#0b151e!important;color:#f3f8fb!important;border:1px solid rgba(255,255,255,.22)!important;border-radius:7px!important;padding:6px 7px!important;font-size:.76rem!important;font-weight:650!important;box-sizing:border-box!important}.tak-route-edit-color-v500>span{display:grid!important;grid-template-columns:52px 1fr!important;align-items:center!important;gap:8px!important}.tak-route-edit-color-v500 input[type=color]{width:52px!important;height:34px!important;padding:3px!important;cursor:pointer!important}
.tak-gf-events-v491{position:fixed;right:16px;bottom:44px;z-index:970;width:330px;max-height:calc(100vh - 98px);overflow:hidden;border:1px solid rgba(255,255,255,.15);border-radius:12px;background:rgba(8,13,18,.96);box-shadow:0 18px 48px rgba(0,0,0,.52);display:flex;flex-direction:column}.tak-gf-events-v491.collapsed{height:auto!important;max-height:none!important}.tak-gf-events-v491.collapsed .tak-gf-events-body-v491,.tak-gf-events-v491.collapsed .tak-gf-resize-v492{display:none}.tak-gf-resize-v492{position:relative;flex:0 0 6px;height:6px;cursor:ns-resize;touch-action:none;background:rgba(255,255,255,.012)}.tak-gf-resize-v492::after{content:"";position:absolute;left:50%;top:2px;width:42px;height:2px;transform:translateX(-50%);border-radius:99px;background:rgba(174,188,195,.38)}.tak-gf-resize-v492:hover::after,.tak-gf-resize-v492:active::after{background:rgba(255,111,46,.72)}.tak-gf-events-head-v491{min-height:44px;flex:0 0 44px;display:grid;grid-template-columns:minmax(0,1fr) auto auto;gap:8px;align-items:center;padding:7px 8px 7px 11px;border-bottom:1px solid rgba(255,255,255,.1);background:linear-gradient(180deg,rgba(255,255,255,.035),rgba(255,255,255,.01));cursor:move;user-select:none}.tak-gf-events-title-v491{display:flex;align-items:center;gap:8px;min-width:0}.tak-gf-events-title-v491>span{width:9px;height:9px;border-radius:50%;background:#ff615b;box-shadow:0 0 0 4px rgba(255,97,91,.1),0 0 11px rgba(255,97,91,.6)}.tak-gf-events-title-v491 b{display:block;font-size:.71rem;text-transform:uppercase;letter-spacing:.075em}.tak-gf-event-count-v491{border:1px solid rgba(255,97,91,.3);border-radius:999px;padding:2px 6px;color:#ffb7b3;background:rgba(255,97,91,.08);font-size:.54rem;font-weight:950;white-space:nowrap}.tak-gf-events-head-v491 button{width:27px;height:27px;display:grid;place-items:center;border:1px solid rgba(255,255,255,.12);border-radius:7px;background:#111920;color:#d0dbe0}.tak-gf-events-head-v491 button i{width:12px;height:2px;border-radius:99px;background:currentColor}.tak-gf-events-head-v491 button.restore i{height:12px;background:linear-gradient(currentColor,currentColor) center/12px 2px no-repeat,linear-gradient(currentColor,currentColor) center/2px 12px no-repeat}.tak-gf-events-body-v491{max-height:274px;overflow:auto}.tak-gf-events-v491.tak-gf-resized-v492 .tak-gf-events-body-v491{display:flex;flex:1 1 auto;min-height:0;max-height:none;overflow:hidden;flex-direction:column}.tak-gf-events-v491.tak-gf-resized-v492 #takGfEventRowsV491{flex:1 1 auto;min-height:0;overflow:auto}.tak-gf-event-v491{display:grid;grid-template-columns:minmax(0,1fr) auto;min-height:43px;padding:6px 9px;border-bottom:1px solid rgba(255,255,255,.075)}.tak-gf-event-copy-v491{display:grid;grid-template-columns:auto minmax(0,1fr);align-items:center;gap:7px;min-width:0}.tak-gf-trigger-v491{border-radius:999px;padding:2px 6px;font-size:.5rem;font-weight:950;text-transform:uppercase}.tak-gf-trigger-v491.enter{color:#aef1c9;background:rgba(88,220,141,.1);border:1px solid rgba(88,220,141,.25)}.tak-gf-trigger-v491.exit{color:#ffb5b1;background:rgba(255,97,91,.1);border:1px solid rgba(255,97,91,.25)}.tak-gf-trigger-v491.cross{color:#ffe3a4;background:rgba(255,209,102,.09);border:1px solid rgba(255,209,102,.23)}.tak-gf-trigger-v491.dwell{color:#d8baff;background:rgba(180,117,255,.1);border:1px solid rgba(180,117,255,.25)}.tak-gf-event-copy-v491>div>div{overflow:hidden;color:#d9e4e8;font-size:.64rem;text-overflow:ellipsis;white-space:nowrap}.tak-gf-event-copy-v491 strong{color:#fff}.tak-gf-event-copy-v491 small{display:block;overflow:hidden;margin-top:2px;color:#748690;font-size:.55rem;text-overflow:ellipsis;white-space:nowrap}.tak-gf-event-v491 time{padding-top:2px;color:#899aa4;font-size:.53rem;font-weight:850;white-space:nowrap}.tak-gf-events-foot-v491{display:flex;flex:0 0 auto;justify-content:space-between;align-items:center;gap:8px;padding:7px 9px;border-top:1px solid rgba(255,255,255,.1);color:#71838d;background:rgba(255,255,255,.018);font-size:.54rem;font-weight:800}.tak-gf-events-foot-v491 button{border:1px solid rgba(255,255,255,.12);border-radius:7px;padding:4px 7px;color:#aebcc3;background:#111920;font-size:.54rem;font-weight:900;text-transform:uppercase}.tak-gf-events-empty-v491{padding:12px;color:#758791;font-size:.66rem}
.adsb-type-card-v491.tak-gf-light-selected-v491.is-checked-v491{border-color:rgba(218,225,230,.62)!important;background:rgba(218,225,230,.10)!important}.adsb-type-card-v491.tak-gf-light-selected-v491.is-checked-v491 .adsb-type-check-v491{border-color:#d9e0e4!important;background:#d9e0e4!important;color:#111820!important}
@media(max-width:700px){.tak-gf-events-v491{width:min(330px,calc(100vw - 24px));right:12px}.tak-gf-alt-grid-v491{grid-template-columns:1fr}.tak-gf-check-grid-v491,.tak-gf-trigger-grid-v491{grid-template-columns:1fr}}
`;d.head.appendChild(st)}
function patchAdsbSelected(){for(const card of qa('.adsb-type-card-v491'))card.classList.add('tak-gf-light-selected-v491')}
function bindMap(){const m=mapObj();if(!m||typeof m.on!=='function'||m.__takGeofenceBoundV491)return false;m.__takGeofenceBoundV491=true;m.on('popupopen',ensurePopupButton);return true}
function boot(){installCss();try{S.master=sessionStorage.getItem('takmap.geofence.master')!=='0'}catch(_){}ensureSidebar();captureProtection();bindPopupActionDelegation();bindMap();patchAdsbSelected();loadFences();ensureTimer();renderAll()}
const api={version:V,openEditor,preparePopup:(popup,layer)=>canonicalPopupStoredContent(popup,layer||popup&&popup._source),attachPopup:popup=>ensurePopupButton({popup}),targetForLayer,load:loadFences,save:saveFence,remove:removeFence,fences:()=>Array.from(FENCES.values()).map(x=>JSON.parse(JSON.stringify(x))),events:()=>EVENTS.map(x=>Object.assign({},x)),protectedIds:()=>Array.from(protectedIds()),tick,diagnostics:()=>({version:V,loadedAt:S.loadedAt,fences:FENCES.size,active:Array.from(FENCES.values()).filter(f=>f.enabled!==false).length,master:S.master,events:EVENTS.length,ticks:S.ticks,lastTick:S.lastTick,alerts:S.alerts,suppressedStale:S.suppressedStale,suppressedRearm:S.suppressedRearm,protectedBlocks:S.protectedBlocks,popupButtons:S.popupButtons,soundReady:S.soundReady,soundPlays:S.soundPlays,boundaryConfirmationSeconds:2,rearmSeconds:10,oneEventPerCrossing:true,sidebarDesign:'Option A Operational Rows',eventDesign:'Option C Dense Trigger Chips',collapseDesign:'Option 1 Minimize/Restore',eventWindowConditional:true,eventWindowSubtitle:false,heightResizeOnly:true,topBottomResizeGrips:true,sidebarPlacement:'Basemap > Geofences > ADS-B',nativeBrowserControls:false,unifiedPopupActions:true,duplicateEditControls:false,legacyEditSummaryRemoved:true,legacyDetailsEditorRemoved:true,productionPopupMarkupEditWiring:true,primaryActionsInsidePaddedPopupBody:true,inlineReadOnlyToEditFields:true,inlineEditActions:['Save','Cancel','Delete'],routeSaveViewEditV500:true,routePointCountShown:false,routeEditableFields:['Name','Color','Category','Notes'],routeReadOnlyFields:['Length','Start','End','Created','Geofence'],routeLengthUnits:['miles','kilometers'],coordinateTruth:'reported-lat-lon',adsbCoordinateSnapshot:'rawSnapshot',visualMarkerGeometryIgnored:true,iconBoundsIgnored:true,labelBoundsIgnored:true,rotationIgnored:true,interpolationAffectsGeofence:false,reportedCoordinateEvaluations:S.reportedCoordinateEvaluations,visualCoordinateEvaluations:S.visualCoordinateEvaluations,reportedSegmentsEvaluated:S.reportedSegmentsEvaluated,hoverClickSamePopupDesign:true,shapePopupAnchor:'geometry-center',storedPopupContentCanonical:true,reopenWithoutPopupopenSafe:true,singleGeometryPopupEventOwner:true,lastError:S.lastError})};
w.TakMapGeofencingV491=Object.freeze(api);
const oldDiag=w.TakMapDiagnostics;w.TakMapDiagnostics=function(){let out={};try{out=typeof oldDiag==='function'?oldDiag():{}}catch(e){out={diagnosticError:String(e&&e.message||e)}}out.version=V;out.geofencing=api.diagnostics();return out};
if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',()=>setTimeout(boot,240),{once:true});else setTimeout(boot,240);[900,2200,5000,9000].forEach(ms=>setTimeout(()=>{ensureSidebar();bindPopupActionDelegation();bindMap();patchAdsbSelected();refreshPopupButtons();renderAll()},ms));
console.info('[TAK Map] geofencing-v491: loaded');
})(window,document);
