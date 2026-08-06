/* TAK Map i491 presentation-only live movement interpolation */
(function(w,d){
'use strict';
const V='v491',NAME='TakMapLiveInterpolationV476';
if(w[NAME]&&w[NAME].stop)try{w[NAME].stop()}catch(_){ }
const C={enabled:true,adsbDurationMs:4500,cotDurationMs:15000,minDurationMs:500,maxAircraftJumpMeters:80000,maxCotJumpMeters:20000};
const A=new Map(),cotOld=new Map(),cotLastAt=new Map();
let raf=0,stopped=false,cotGroup=null,origClear=null,cotBound=false,currentRows=[],used=new Set();
const S={version:V,installedAt:Date.now(),frames:0,adsbMoves:0,cotMoves:0,snaps:0,completed:0,removed:0,active:0,lastError:''};
function mapObj(){try{return w.takLeafletMap&&w.takLeafletMap.distance?w.takLeafletMap:w.map}catch(_){return null}}
function replay(){try{return !!(d.body&&d.body.classList.contains('replay-mode-v415'))}catch(_){return false}}
function n(v){v=Number(v);return Number.isFinite(v)?v:null}
function point(v){if(!v)return null;const lat=n(Array.isArray(v)?v[0]:v.lat),lng=n(Array.isArray(v)?v[1]:(v.lng??v.lon));return lat==null||lng==null?null:{lat,lng}}
function dist(a,b){const m=mapObj();try{return m.distance([a.lat,a.lng],[b.lat,b.lng])}catch(_){const r=Math.PI/180,x=(b.lng-a.lng)*r*Math.cos((a.lat+b.lat)*r/2),y=(b.lat-a.lat)*r;return Math.hypot(x,y)*6371000}}
function hdelta(a,b){let x=b-a;while(x>180)x-=360;while(x<-180)x+=360;return x}
function ldelta(a,b){let x=b-a;while(x>180)x-=360;while(x<-180)x+=360;return x}
function img(marker){try{return marker&&marker.getElement&&marker.getElement()?.querySelector('[data-adsb-img]')}catch(_){return null}}
function heading(marker){const el=img(marker),m=String(el&&el.style.transform||'').match(/rotate\((-?\d+(?:\.\d+)?)deg\)/i);return m?Number(m[1]):null}
function setHeading(marker,deg){if(!Number.isFinite(deg))return;const el=img(marker);if(!el)return;el.style.transform='rotate('+deg+'deg) scale(.75)';el.style.transformOrigin='50% 50%'}
function snap(marker,target,targetHeading){try{marker.setLatLng([target.lat,target.lng]);if(Number.isFinite(targetHeading))setHeading(marker,targetHeading)}catch(_){ }S.snaps++}
function move(marker,target,opts){opts=opts||{};target=point(target);const start=point(marker&&marker.getLatLng&&marker.getLatLng());if(!marker||!target||!start)return false;const kind=opts.kind||'cot',max=Number(opts.maxJumpMeters)||(kind==='adsb'?C.maxAircraftJumpMeters:C.maxCotJumpMeters),duration=Math.max(C.minDurationMs,Number(opts.durationMs)||(kind==='adsb'?C.adsbDurationMs:C.cotDurationMs));
  if(!C.enabled||stopped||d.hidden||replay()||dist(start,target)>max){snap(marker,target,opts.targetHeading);return false}
  const sh=Number.isFinite(opts.startHeading)?opts.startHeading:heading(marker),th=Number.isFinite(opts.targetHeading)?opts.targetHeading:null;
  A.set(marker,{marker,start,target,started:performance.now(),duration,sh,th,kind});S.active=A.size;if(kind==='adsb')S.adsbMoves++;else S.cotMoves++;if(!raf)raf=requestAnimationFrame(tick);return true
}
function tick(now){raf=0;S.frames++;for(const [marker,a] of A){try{const m=mapObj();if(!marker._map||!m||!m.hasLayer(marker)){A.delete(marker);S.removed++;continue}const p=Math.max(0,Math.min(1,(now-a.started)/a.duration)),lng=a.start.lng+ldelta(a.start.lng,a.target.lng)*p,lat=a.start.lat+(a.target.lat-a.start.lat)*p;marker.setLatLng([lat,lng]);if(Number.isFinite(a.sh)&&Number.isFinite(a.th))setHeading(marker,a.sh+hdelta(a.sh,a.th)*p);if(p>=1){A.delete(marker);snap(marker,a.target,a.th);S.completed++}}catch(e){A.delete(marker);S.lastError=String(e&&e.message||e)}}S.active=A.size;if(A.size)raf=requestAnimationFrame(tick)}
function rows(){try{return Array.isArray(lastTakMarkers)?lastTakMarkers:(Array.isArray(w.lastTakMarkers)?w.lastTakMarkers:[])}catch(_){return Array.isArray(w.lastTakMarkers)?w.lastTakMarkers:[]}}
function key(o){const id=String(o&& (o.uid||o.id||o.callsign||o.name)||'').trim();if(!id)return'';return String(o.kind||o.type||'cot').toLowerCase()+'|'+id}
function prepareRows(){currentRows=[];used.clear();for(const o of rows()){const p=point(o),k=key(o);if(p&&k)currentRows.push({o,p,k})}}
function matchMarker(marker){const p=point(marker&&marker.getLatLng&&marker.getLatLng());if(!p)return null;let best=null,bd=Infinity;for(const r of currentRows){if(used.has(r.k))continue;const x=dist(p,r.p);if(x<bd){bd=x;best=r}}if(!best||bd>5)return null;used.add(best.k);return best}
function rememberExisting(){if(!cotGroup||!cotGroup.eachLayer)return;cotGroup.eachLayer(m=>{const k=m&&m.__takLiveInterpolationKey,p=point(m&&m.getLatLng&&m.getLatLng());if(k&&p)cotOld.set(k,p);A.delete(m)})}
function cotDuration(k){const now=Date.now(),prev=cotLastAt.get(k);cotLastAt.set(k,now);if(!prev)return C.cotDurationMs;return Math.max(1000,Math.min(C.cotDurationMs,(now-prev)*.9))}
function onCotAdd(ev){const m=ev&&ev.layer,r=matchMarker(m);if(!m||!r)return;m.__takLiveInterpolationKey=r.k;const old=cotOld.get(r.k);if(!old)return;const target=point(m.getLatLng());if(!target||dist(old,target)<.5)return;m.setLatLng([old.lat,old.lng]);move(m,target,{kind:'cot',durationMs:cotDuration(r.k),maxJumpMeters:C.maxCotJumpMeters})}
function onCotRemove(ev){if(ev&&ev.layer)A.delete(ev.layer)}
function bindCot(){try{cotGroup=(typeof takMarkerLayer!=='undefined'&&takMarkerLayer)||w.takMarkerLayer}catch(_){cotGroup=w.takMarkerLayer||null}if(!cotGroup||!cotGroup.on||cotBound)return false;origClear=cotGroup.clearLayers;prepareRows();cotGroup.eachLayer(m=>{const r=matchMarker(m);if(r)m.__takLiveInterpolationKey=r.k});cotGroup.clearLayers=function(){rememberExisting();prepareRows();return origClear.apply(this,arguments)};cotGroup.on('layeradd',onCotAdd);cotGroup.on('layerremove',onCotRemove);cotBound=true;return true}
function cancel(marker){if(!marker)return false;const had=A.delete(marker);S.active=A.size;return had}
function cancelKind(kind){let n=0;for(const [marker,a] of Array.from(A.entries()))if(!kind||a.kind===kind){A.delete(marker);n++}S.active=A.size;return n}
function stop(){if(stopped)return;stopped=true;C.enabled=false;if(raf)cancelAnimationFrame(raf);raf=0;for(const [,a] of A)snap(a.marker,a.target,a.th);A.clear();if(cotBound&&cotGroup){try{cotGroup.off('layeradd',onCotAdd);cotGroup.off('layerremove',onCotRemove);if(origClear)cotGroup.clearLayers=origClear}catch(_){ }}S.active=0}
function diagnostics(){return Object.assign({},S,{enabled:C.enabled&&!stopped,activeAnimations:A.size,cotHookBound:cotBound,replaySuppressed:replay(),pageHidden:d.hidden,config:Object.assign({},C)})}
const api={version:V,get enabled(){return C.enabled&&!stopped},config:C,move,setHeading,heading,cancel,cancelKind,stop,start(){stopped=false;C.enabled=true;bindCot();return diagnostics()},diagnostics};
w[NAME]=api;w.__takMapAdsbSingleOwner='v491';try{const ctl=w.TakMapControllers&&w.TakMapControllers.adsb;if(ctl)ctl.version='v491'}catch(_){ }
function boot(){bindCot();try{console.info('[TAK Map] live-interpolation-v491: loaded')}catch(_){ }}
if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',()=>setTimeout(boot,900),{once:true});else setTimeout(boot,900);[2200,5000].forEach(ms=>setTimeout(bindCot,ms));
})(window,document);
