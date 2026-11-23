/* TAK Map i683 elevation profile: floating compact / extended route view, lifecycle and real NDM slopes.
 * Original i681 full-path terrain elevation profile. No synthetic elevations.
 * Existing NDM terrain sample endpoint is read-only to terrain storage. The
 * route editor dispatches geometry changes; saved routes use canonical coords.
 */
(function(W,D){'use strict';
const ID='takRouteElevationI681', MILE=1609.344, FT=3.280839895;
const S={map:null,panel:null,canvas:null,source:null,mode:'',routeKey:'',full:[],samples:[],elev:[],cache:new Map(),seq:0,controller:null,timer:0,retry:0,collapsed:false,hover:-1,marker:null,cesiumMarker:null,lastDraw:0,working:false,sourceName:'NDM terrain',dismissedLive:false,wasRouteActive:false,gradeWindowM:90,gradeGeneration:0,gradeCache:null,view:'compact',detailRun:-1,selectedRouteKey:'',selectedPopupSource:null,dismissedSavedKey:'',positionReady:false,position:null,drag:null,markerSignature:'',selectedProfileContext:'',refreshing:false};
const $=id=>D.getElementById(id);
const valid=p=>p&&Number.isFinite(p.lat)&&Number.isFinite(p.lng)&&Math.abs(p.lat)<=90&&Math.abs(p.lng)<=180;
const fmtMiles=d=>(d/MILE).toFixed(d/MILE>=10?1:2)+' mi';
const fmtFeet=m=>Math.round(m*FT).toLocaleString()+' ft';
function live(){
 // The core toolbar's activeMapTool is a global lexical binding, not a
 // window property. Use it when available instead of stale button classes.
 try{if(typeof activeMapTool!=='undefined')return activeMapTool==='route'}catch(_){}
 return !!($('toolRoute')?.classList.contains('active')&&$('routeMiniToolbar')?.classList.contains('active'));
}
function eq(a,b){return Math.abs(a.lat-b.lat)<1e-10&&Math.abs(a.lng-b.lng)<1e-10}
function liveGeometry(){
 const s=W.takRouteEditorI654;
 if(!s||!live()||typeof s.fullShape!=='function')return [];
 return (s.fullShape()||[]).map(p=>({lat:Number(p.lat),lng:Number(p.lng)})).filter(valid);
}
function featureCoords(feature){
 const original=Array.isArray(feature?.coords)?feature.coords:[];
 const out=original.map(c=>Array.isArray(c)?
  ({lat:Number(c[0]),lng:Number(c[1])}):({lat:Number(c?.lat),lng:Number(c?.lng??c?.lon)}));
 // Legacy truncated routes are NOT repaired by joining across invalid vertices.
 return out.length===original.length&&out.every(valid)?out:[];
}
function signature(path){if(path.length<2)return 'empty';const n=path.length,a=path[0],b=path[n-1];
 // Long paths can change internally without moving endpoints, so include
 // sampled vertices plus source editor revision in the signature.
 let hash=2166136261;for(let i=0;i<n;i+=Math.max(1,Math.floor(n/384))){const p=path[i];
  const s=Math.round(p.lat*1e6)+':'+Math.round(p.lng*1e6);for(let j=0;j<s.length;j++)hash=Math.imul(hash^s.charCodeAt(j),16777619)>>>0;}
 const rev=live()?W.takRouteEditorI654?.dirty||0:0;
 return [n,a.lat,a.lng,b.lat,b.lng,hash,rev].join(':');
}
function setStatus(message){const e=$('takElevStatusI681');if(e)e.textContent=message;}
function stop(){S.seq++;clearTimeout(S.timer);S.timer=0;S.controller?.abort();S.controller=null;S.working=false;}
function hideCompactMileage(){const el=$('takElevHoverMilesI696');if(el)el.hidden=true;}
function updateCompactMileage(distance,ratio){
 const label=$('takElevHoverMilesI696'),canvas=S.canvas;
 if(!label||!canvas||S.view!=='compact'||!Number.isFinite(distance)){hideCompactMileage();return;}
 label.textContent=fmtMiles(distance);
 // Keep the mileage in its own bottom rail, *below* the 82px chart canvas.
 // Use the canvas origin so the readout follows the existing cursor/plot x-axis.
 label.hidden=false;
 const canvasRect=canvas.getBoundingClientRect();
 const areaRect=canvas.parentElement.getBoundingClientRect();
 const width=canvasRect.width||550;
 const plotX=52+Math.max(0,Math.min(1,ratio))*Math.max(1,width-62);
 const centered=(canvasRect.left-areaRect.left)+plotX;
 const halfWidth=(label.getBoundingClientRect().width||48)/2;
 label.style.left=Math.max(halfWidth+4,Math.min((areaRect.width||width)-halfWidth-4,centered))+'px';
}
function discardHover(){S.hover=-1;hideCompactMileage();try{if(S.marker&&S.map?.hasLayer(S.marker))S.map.removeLayer(S.marker)}catch(_){}S.marker=null;
 try{if(S.cesiumMarker){const v=typeof terrain3DViewer!=='undefined'?terrain3DViewer:null;v?.entities.remove(S.cesiumMarker)}}catch(_){}S.cesiumMarker=null;}
function focusMarker(p){discardHover();if(!p||!S.map||!W.L)return;
 // Keep indicator synchronized with the original route's sampled coordinates.
 if(typeof terrain3DActive!=='undefined'&&terrain3DActive&&typeof terrain3DViewer!=='undefined'&&terrain3DViewer&&W.Cesium){
  try{S.cesiumMarker=terrain3DViewer.entities.add({position:Cesium.Cartesian3.fromDegrees(p.lng,p.lat),point:{pixelSize:11,color:Cesium.Color.CYAN,outlineColor:Cesium.Color.BLACK,outlineWidth:2,heightReference:Cesium.HeightReference.CLAMP_TO_GROUND,disableDepthTestDistance:Number.POSITIVE_INFINITY}});terrain3DViewer.scene.requestRender();return}catch(_){}}
 S.marker=W.L.circleMarker([p.lat,p.lng],{radius:6,weight:2,color:'#09161d',fillColor:'#77e7f0',fillOpacity:1,interactive:false}).addTo(S.map);
}
const POSITION_KEY='tak-map-elevation-i683-position';
function limitPosition(x,y){const el=S.panel;if(!el)return{x,y};const w=el.offsetWidth||580,h=el.offsetHeight||210;
 return {x:Math.round(Math.max(8,Math.min(x,Math.max(8,W.innerWidth-w-8)))),y:Math.round(Math.max(8,Math.min(y,Math.max(8,W.innerHeight-h-8))))};}
function place(){if(!S.panel||S.panel.hidden)return;
 let pt=S.position;
 if(!pt){try{const saved=JSON.parse(W.localStorage.getItem(POSITION_KEY)||'null');if(Number.isFinite(saved?.x)&&Number.isFinite(saved?.y))pt=saved}catch(_){}}
 if(!pt){const rect=S.panel.getBoundingClientRect();pt={x:(W.innerWidth-rect.width)/2,y:Math.max(8,W.innerHeight-rect.height-24)}}
 S.position=limitPosition(pt.x,pt.y);S.panel.style.left=S.position.x+'px';S.panel.style.top=S.position.y+'px';S.panel.style.right='auto';S.panel.style.bottom='auto';S.panel.style.transform='none';S.positionReady=true;
}
function savePosition(){if(!S.position)return;try{W.localStorage.setItem(POSITION_KEY,JSON.stringify(S.position))}catch(_){}}
function dockBottomCenter(){
 // Width and height change when switching Compact/Extended. Discard the
 // previous absolute coordinates and dock to viewport bottom with 24px gap.
 if(!S.panel||S.panel.hidden)return;
 const r=S.panel.getBoundingClientRect();
 movePanel((W.innerWidth-r.width)/2,W.innerHeight-r.height-24);
 savePosition();
}
function movePanel(x,y){S.position=limitPosition(x,y);if(!S.panel)return;S.panel.style.left=S.position.x+'px';S.panel.style.top=S.position.y+'px';S.panel.style.bottom='auto';S.panel.style.transform='none';}
function display(on){if(!S.panel)return;
 if(!on){S.panel.hidden=true;dismissRunTip();discardHover();return;}
 if(S.panel.hidden){S.panel.hidden=false;W.requestAnimationFrame(()=>{place();draw()})}else{place();draw()}
}
function setView(view){if(view!=='compact'&&view!=='extended')return;hideCompactMileage();S.view=view;S.detailRun=-1;S.markerSignature='';S.panel?.classList.toggle('compact',view==='compact');S.panel?.classList.toggle('extended',view==='extended');
 const toggle=$('takElevExpandI683');if(toggle){toggle.textContent=view==='compact'?'⤢  Expand':'⤡  Compact';toggle.setAttribute('aria-expanded',String(view==='extended'))}
 const collapse=$('takElevCollapseI681');if(collapse)collapse.hidden=view==='compact';
 W.requestAnimationFrame(()=>{draw();dockBottomCenter()});
}
function dismissRunTip(){const tip=$('takElevRunTipI683');if(tip)tip.hidden=true;}
function showRunTip(run,index,button){const tip=$('takElevRunTipI683');if(!tip||!button)return;
 const data=[['Location',fmtMiles(run.startD)],['Maximum slope',run.max.toFixed(1)+'°'],['Direction',run.up?'Uphill':'Downhill'],['Elevation change',fmtFeet(Math.abs(run.delta))+' '+(run.up?'gain':'loss')]];
 tip.replaceChildren();const label=D.createElement('small');label.textContent='STEEP RUN '+(index+1)+' · ≥35°';tip.appendChild(label);
 const amount=D.createElement('strong');amount.textContent=fmtFeet(run.length);tip.appendChild(amount);
 for(const [k,v] of data){const row=D.createElement('div'),name=D.createElement('span'),value=D.createElement('b');name.textContent=k;value.textContent=v;row.append(name,value);tip.appendChild(row)}
 tip.hidden=false;const r=button.getBoundingClientRect(),w=tip.offsetWidth,h=tip.offsetHeight;
 tip.style.left=Math.round(r.right+12+w+8<=W.innerWidth?r.right+12:Math.max(8,r.left-w-12))+'px';
 tip.style.top=Math.round(Math.max(8,Math.min(W.innerHeight-h-8,r.top+r.height/2-h/2)))+'px';
}
function attachDrag(){const handle=$('takElevDragI683');if(!handle)return;
 handle.addEventListener('pointerdown',e=>{if(e.button!==0)return;const r=S.panel.getBoundingClientRect();S.drag={id:e.pointerId,clientX:e.clientX,clientY:e.clientY,x:r.left,y:r.top};handle.classList.add('dragging');handle.setPointerCapture(e.pointerId);e.preventDefault()});
 handle.addEventListener('pointermove',e=>{if(!S.drag||e.pointerId!==S.drag.id)return;movePanel(S.drag.x+e.clientX-S.drag.clientX,S.drag.y+e.clientY-S.drag.clientY)});
 const finish=e=>{if(!S.drag||e.pointerId!==S.drag.id)return;S.drag=null;handle.classList.remove('dragging');try{if(handle.hasPointerCapture(e.pointerId))handle.releasePointerCapture(e.pointerId)}catch(_){}savePosition()};
 handle.addEventListener('pointerup',finish);handle.addEventListener('pointercancel',finish);
 handle.addEventListener('keydown',e=>{const vector={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,-1],ArrowDown:[0,1]}[e.key];if(!vector)return;e.preventDefault();const r=S.panel.getBoundingClientRect();movePanel(r.left+vector[0]*(e.shiftKey?1:12),r.top+vector[1]*(e.shiftKey?1:12));savePosition()});
}
function clear(message){stop();S.samples=[];S.elev=[];S.gradeGeneration++;S.gradeCache=null;S.routeKey='';discardHover();if(message)setStatus(message);draw();}
function resetStats(){const el=$('takElevStatsI681');if(el)el.textContent='Distance — · Ascent — · Descent —';}
function rangeAndStats(){let low=Infinity,high=-Infinity,asc=0,desc=0,validCount=0;
 for(let i=0;i<S.elev.length;i++){const h=S.elev[i];if(!Number.isFinite(h))continue;
 validCount++;low=Math.min(low,h);high=Math.max(high,h);
 if(i>0&&Number.isFinite(S.elev[i-1])){const d=h-S.elev[i-1];if(d>0)asc+=d;else desc-=d;}}
 return {low,high,asc,desc,validCount};}
// Terrain-derived slope is measured over a distance window rather than a
// single DEM sample. This reduces isolated high-grade artifacts. Angles are
// signed degrees, unlike percentage grade (35 degrees ~= 70 percent grade).
function gradeProfile(){
 const cached=S.gradeCache;
 if(cached&&cached.samples===S.samples&&cached.elev===S.elev&&cached.generation===S.gradeGeneration&&cached.window===S.gradeWindowM)return cached.value;
 const p=S.samples,e=S.elev,n=p.length,angles=new Array(n).fill(null);
 const out={angles,maxAbs:0,steepMeters:0,steepSegments:0,measuredMeters:0,windowMeters:S.gradeWindowM,runs:[]};
 if(n<2||e.length!==n)return out;
 const missing=new Int32Array(n+1);
 for(let i=0;i<n;i++)missing[i+1]=missing[i]+(Number.isFinite(e[i])?0:1);
 let left=0,right=1;
 for(let i=1;i<n;i++){
  const mid=(p[i-1].d+p[i].d)/2,half=S.gradeWindowM/2;
  while(left+1<i&&p[left+1].d<=mid-half)left++;
  right=Math.max(i,right);
  while(right+1<n&&p[right].d<mid+half)right++;
  const a=Math.min(i-1,left),b=Math.max(i,right),run=p[b].d-p[a].d;
  if(run<=2||missing[b+1]-missing[a])continue;
  const angle=Math.atan2(e[b]-e[a],run)*180/Math.PI;
  if(!Number.isFinite(angle))continue;
  angles[i]=angle;const distance=Math.max(0,p[i].d-p[i-1].d);
  out.maxAbs=Math.max(out.maxAbs,Math.abs(angle));out.measuredMeters+=distance;
  if(Math.abs(angle)>=35){out.steepMeters+=distance;out.steepSegments++;
   const up=angle>=0,prev=out.runs[out.runs.length-1];
   if(prev&&prev.endIndex===i-1&&prev.up===up){prev.endIndex=i;prev.endD=p[i].d;prev.length+=distance;prev.max=Math.max(prev.max,Math.abs(angle));prev.delta+=e[i]-e[i-1]}
   else out.runs.push({startIndex:i-1,endIndex:i,startD:p[i-1].d,endD:p[i].d,length:distance,max:Math.abs(angle),up,delta:e[i]-e[i-1]});
  }
 }
 S.gradeCache={samples:S.samples,elev:S.elev,generation:S.gradeGeneration,window:S.gradeWindowM,value:out};
 return out;
}
function gradeColor(angle){if(!Number.isFinite(angle))return '#76c8d2';const a=Math.abs(angle);
 return a>=35?'#f16b78':a>=25?'#f6a65a':a>=15?'#e9cf79':'#76c8d2';}
function updateMetrics(stats,total,grade,partial){
 const updates={
  takElevStatsI681:fmtMiles(total)+' · ↑'+fmtFeet(stats.asc)+' · ↓'+fmtFeet(stats.desc),
  takElevHeaderDistanceI683:fmtMiles(total), takElevSteepCountI683:grade.runs.length+' runs',
  takElevDistanceI681:fmtMiles(total),takElevGainI681:fmtFeet(stats.asc),takElevLossI681:fmtFeet(stats.desc),
  takElevMinI681:fmtFeet(stats.low),takElevMaxI681:fmtFeet(stats.high),
  takElevSlopeI681:grade.measuredMeters?grade.maxAbs.toFixed(1)+'°':'—',
  takElevSteepI681:grade.measuredMeters?fmtFeet(grade.steepMeters):'—'
 };
 for(const [id,value] of Object.entries(updates)){const el=$(id);if(el)el.textContent=value}
 const warning=$('takElevSteepNoticeI681');if(warning){warning.textContent=grade.steepMeters>0
  ?'Steep terrain detected: '+fmtFeet(grade.steepMeters)+' at ≥35°'
  :'No ≥35° terrain slopes detected in sampled segments';
  warning.classList.toggle('danger',grade.steepMeters>0);}
 const quality=$('takElevQualityI681');if(quality)quality.textContent=(partial?'Partial terrain coverage · ':'')+
  'Slope averaged over '+Math.round(S.gradeWindowM)+' m · terrain estimate, not surveyed road grade';
}
function chartView(total){if(S.view==='extended'&&S.detailRun>=0){const run=gradeProfile().runs[S.detailRun];if(run){const edge=Math.max(90,run.length*1.5);return{start:Math.max(0,run.startD-edge),end:Math.min(total,run.endD+edge)}}}return{start:0,end:total};}
function renderRunMarkers(area,view,xOf,yOf,runList,token){const root=$('takElevMarkersI683');if(!root)return;
 const visible=runList.map((r,i)=>({...r,number:i+1})).filter(r=>r.endD>=view.start&&r.startD<=view.end);
 const signature=[token,S.view,S.detailRun,S.canvas?.clientWidth,S.canvas?.clientHeight,visible.map(r=>r.startIndex+':'+r.endIndex).join(',')].join('|');
 if(S.markerSignature===signature)return;S.markerSignature=signature;dismissRunTip();root.replaceChildren();
 const maxMarkers=120; // Guard against extreme noisy DEM coverage.
 for(const run of visible.slice(0,maxMarkers)){const mid=(run.startIndex+run.endIndex)>>1;const v=S.elev[mid];if(!Number.isFinite(v))continue;
  const x=xOf(S.samples[mid]),y=yOf(v),btn=D.createElement('button');btn.type='button';btn.className='tak-elev-run-marker-i683';
  btn.textContent=String(run.number);btn.style.left=x+'px';btn.style.top=Math.max(6,y-11)+'px';btn.setAttribute('aria-label','Steep run '+run.number+': '+fmtFeet(run.length)+' at '+run.max.toFixed(1)+' degrees. Click for detail');
  btn.addEventListener('pointerenter',()=>showRunTip(run,run.number-1,btn));btn.addEventListener('pointerleave',dismissRunTip);
  btn.addEventListener('focus',()=>showRunTip(run,run.number-1,btn));btn.addEventListener('blur',dismissRunTip);
  btn.addEventListener('click',e=>{e.stopPropagation();S.view='extended';setView('extended');S.detailRun=run.number-1;S.markerSignature='';draw()});root.appendChild(btn);
 }
}
function draw(){const c=S.canvas;if(!c||S.panel?.hidden||S.collapsed)return;
 const rect=c.getBoundingClientRect(),compact=S.view==='compact',w=Math.max(205,Math.round(rect.width||550)),h=Math.max(75,Math.round(rect.height||(compact?82:250))),dpr=Math.min(2,W.devicePixelRatio||1);
 c.width=Math.round(w*dpr);c.height=Math.round(h*dpr);const ctx=c.getContext('2d');if(!ctx)return;ctx.setTransform(dpr,0,0,dpr,0,0);ctx.clearRect(0,0,w,h);
 const area={left:compact?52:70,right:w-10,top:compact?15:21,bottom:h-(compact?19:28)};
 const n=S.samples.length,stats=rangeAndStats(),ready=n>=2&&Number.isFinite(stats.low),grade=gradeProfile();
 ctx.font=(compact?'9px':'10px')+' system-ui,sans-serif';ctx.lineWidth=1;
 if(!ready){ctx.strokeStyle='rgba(183,205,217,.18)';const ticks=compact?3:5;for(let i=0;i<ticks;i++){const y=area.top+(area.bottom-area.top)*i/(ticks-1);ctx.beginPath();ctx.moveTo(area.left,y);ctx.lineTo(area.right,y);ctx.stroke()}
  ctx.fillStyle='#97b1bc';ctx.font='11px system-ui,sans-serif';ctx.fillText(n?'Waiting for NDM terrain samples':'Add two waypoints to see terrain',area.left+10,h/2);
  resetStats();for(const id of ['takElevDistanceI681','takElevGainI681','takElevLossI681','takElevMinI681','takElevMaxI681','takElevSlopeI681','takElevSteepI681','takElevHeaderDistanceI683']){const e=$(id);if(e)e.textContent='—'}
  const root=$('takElevMarkersI683');if(root)root.replaceChildren();S.markerSignature='';dismissRunTip();return;
 }
 const total=Math.max(1,S.samples[n-1].d),view=chartView(total),len=Math.max(1,view.end-view.start);
 let vlo=Infinity,vhi=-Infinity;
 for(let i=0;i<n;i++){if(S.samples[i].d<view.start||S.samples[i].d>view.end||!Number.isFinite(S.elev[i]))continue;vlo=Math.min(vlo,S.elev[i]);vhi=Math.max(vhi,S.elev[i])}
 if(!Number.isFinite(vlo)){vlo=stats.low;vhi=stats.high}
 const spread=Math.max(10,vhi-vlo),pad=Math.max(3,spread*.09),lo=vlo-pad,hi=vhi+pad,delta=hi-lo;
 const xOf=p=>area.left+(area.right-area.left)*((p.d-view.start)/len),yOf=v=>area.bottom-(area.bottom-area.top)*(v-lo)/delta;
 const rows=compact?3:5,columns=compact?3:5;
 for(let k=0;k<rows;k++){const value=hi-(hi-lo)*k/(rows-1),y=yOf(value);ctx.strokeStyle='rgba(183,205,217,.19)';ctx.beginPath();ctx.moveTo(area.left,y);ctx.lineTo(area.right,y);ctx.stroke();ctx.textAlign='right';ctx.textBaseline='middle';ctx.fillStyle='#a8c0ca';ctx.fillText(Math.round(value*FT).toLocaleString()+' ft',area.left-7,y)}
 for(let k=0;k<columns;k++){const dist=view.start+len*k/(columns-1),x=area.left+(area.right-area.left)*k/(columns-1);ctx.strokeStyle='rgba(183,205,217,.09)';ctx.beginPath();ctx.moveTo(x,area.top);ctx.lineTo(x,area.bottom);ctx.stroke();ctx.fillStyle='#a6bdc7';ctx.textAlign=k===0?'left':k===columns-1?'right':'center';ctx.textBaseline='bottom';ctx.fillText((dist/MILE).toFixed(total/MILE>=10?1:2)+' mi',x,h-3)}
 ctx.save();ctx.beginPath();ctx.rect(area.left,area.top,area.right-area.left,area.bottom-area.top);ctx.clip();ctx.lineWidth=compact?1.9:2.1;ctx.lineJoin='round';ctx.lineCap='round';let color='',drawing=false;
 for(let i=1;i<n;i++){if(S.samples[i].d<view.start||S.samples[i-1].d>view.end)continue;const v0=S.elev[i-1],v1=S.elev[i];if(!Number.isFinite(v0)||!Number.isFinite(v1)){if(drawing){ctx.stroke();drawing=false}continue}
  const next=gradeColor(grade.angles[i]);if(!drawing||color!==next){if(drawing)ctx.stroke();color=next;ctx.strokeStyle=color;ctx.beginPath();ctx.moveTo(xOf(S.samples[i-1]),yOf(v0));drawing=true}ctx.lineTo(xOf(S.samples[i]),yOf(v1));
 }if(drawing)ctx.stroke();if(S.hover>=0&&S.hover<n&&S.samples[S.hover].d>=view.start&&S.samples[S.hover].d<=view.end){const x=xOf(S.samples[S.hover]);ctx.strokeStyle='#dcecf0';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(x,area.top);ctx.lineTo(x,area.bottom);ctx.stroke()}ctx.restore();
 updateMetrics(stats,total,grade,stats.validCount<n);renderRunMarkers(area,view,xOf,yOf,grade.runs,S.gradeGeneration);
 const range=$('takElevRangeI683');if(range)range.textContent=S.detailRun>=0&&grade.runs[S.detailRun]?'Steep run '+(S.detailRun+1)+' · '+fmtFeet(grade.runs[S.detailRun].length):'Full route · '+fmtMiles(total);
 $('takElevFullI683')?.setAttribute('aria-pressed',String(S.detailRun<0));$('takElevDetailI683')?.setAttribute('aria-pressed',String(S.detailRun>=0));
}
function samplePolyline(path,spacing){
 // Distance-based interpolation along EVERY original routed vertex, never a
 // waypoint-only profile. Actual terrain heights only come from the API.
 if(path.length<2)return [];
 let total=0;const lengths=[0];for(let i=1;i<path.length;i++){total+=S.map.distance([path[i-1].lat,path[i-1].lng],[path[i].lat,path[i].lng]);lengths.push(total)}
 const maxSamples=40000,step=Math.max(spacing,total/Math.max(1,maxSamples-1));const out=[];let j=1;
 const count=Math.max(2,Math.ceil(total/step)+1);
 for(let i=0;i<count;i++){
  const d=(i===count-1?total:Math.min(total,i*step));
  while(j<lengths.length-1&&lengths[j]<d)j++;
  const span=lengths[j]-lengths[j-1],t=span?Math.max(0,Math.min(1,(d-lengths[j-1])/span)):0;
  const a=path[j-1],b=path[j];
  // short route segments are linear geographic interpolations along the
  // detailed road/trail polyline, never direct waypoint-to-waypoint chords.
  out.push({lat:a.lat+(b.lat-a.lat)*t,lng:a.lng+(b.lng-a.lng)*t,d});
 }
 return out;
}
const cacheKey=p=>p.lat.toFixed(6)+','+p.lng.toFixed(6);
function cacheSet(k,v){if(S.cache.has(k))S.cache.delete(k);S.cache.set(k,v);while(S.cache.size>70000)S.cache.delete(S.cache.keys().next().value)}
async function coverageInterval(path,signal){
 let west=Infinity,east=-Infinity,south=Infinity,north=-Infinity;
 for(const p of path){west=Math.min(west,p.lng);east=Math.max(east,p.lng);south=Math.min(south,p.lat);north=Math.max(north,p.lat)}
 // Avoid spread Math.min(...path), which overflows JS argument limits on long routes.
 const query=new URLSearchParams({west:String(west),south:String(south),east:String(east),north:String(north)});
 try{const r=await fetch('/api/tak-map/ndm/elevation/coverage?'+query,{signal,credentials:'same-origin'});
  if(!r.ok)throw Error('Coverage HTTP '+r.status);const data=await r.json();
  if(data.available===false)throw Error('No NDM terrain package covers this route');
  if(data.status==='preparing')throw Error('NDM terrain cache preparing');
  const values=(data.datasets||[]).map(x=>Number(x.resolution_m)).filter(x=>Number.isFinite(x)&&x>0);
  return values.length?Math.max(10,Math.min(90,Math.min(...values))):30;
 }catch(e){if(e.name==='AbortError')throw e;
  if(/preparing|no ndm/i.test(String(e.message)))throw e;
  return 30;
 }
}
async function sampleBatch(chunk,signal){const r=await fetch('/api/tak-map/ndm/elevation/sample',{method:'POST',credentials:'same-origin',signal,
 headers:{'Content-Type':'application/json'},body:JSON.stringify({points:chunk.map(p=>[p.lat,p.lng])})});
 const result=await r.json().catch(()=>({}));
 if(!r.ok||!result.ok)throw Error(String(result.error||'NDM elevation sample failed (HTTP '+r.status+')'));
 if(!Array.isArray(result.elevations)||result.elevations.length!==chunk.length)throw Error('NDM elevation batch length mismatch');
 S.sourceName=String(result.source||'NDM terrain');
 return result.elevations.map(v=>v==null?null:Number.isFinite(Number(v))?Number(v):null);
}
async function sampleCurrent(token){
 if(token!==S.seq||S.full.length<2||S.collapsed)return;
 const ctl=new AbortController();S.controller=ctl;S.working=true;
 try{
  const interval=await coverageInterval(S.full,ctl.signal);
  if(token!==S.seq)return;
  S.gradeWindowM=Math.max(90,3*interval);
  const pts=samplePolyline(S.full,interval);S.samples=pts;S.elev=new Array(pts.length).fill(null);S.gradeGeneration++;S.gradeCache=null;draw();
  let processed=0,missing=[];
  for(let i=0;i<pts.length;i++){
   const k=cacheKey(pts[i]);if(S.cache.has(k)){S.elev[i]=S.cache.get(k);processed++}else missing.push(i);
  }
  S.gradeGeneration++;
  const totalMissing=missing.length;
  for(let n=0;n<totalMissing;n+=512){
   if(token!==S.seq)return;
   const slice=missing.slice(n,n+512),vals=await sampleBatch(slice.map(i=>pts[i]),ctl.signal);
   if(token!==S.seq)return;
   slice.forEach((idx,j)=>{S.elev[idx]=vals[j];cacheSet(cacheKey(pts[idx]),vals[j]);});
   processed+=slice.length;S.gradeGeneration++;
   setStatus(S.sourceName+' · '+Math.round(processed/pts.length*100)+'% sampled');
   if(performance.now()-S.lastDraw>140){S.lastDraw=performance.now();draw();}
  }
  if(token!==S.seq)return;
  const good=S.elev.filter(Number.isFinite).length;
  setStatus(S.sourceName+' · '+good+'/'+pts.length+' ground samples'+(good<pts.length?' · gaps where unavailable':''));
  S.retry=0;draw();
 }catch(err){if(token!==S.seq||err.name==='AbortError')return;
  setStatus('Elevation unavailable: '+String(err.message||err));draw();
  if(/preparing|busy|retry/i.test(String(err.message||err))&&S.retry++<12){S.timer=setTimeout(()=>{if(token===S.seq)sampleCurrent(token)},10000)}
 }finally{if(token===S.seq){S.working=false;S.controller=null}}
}
function setGeometry(path,mode,name,identity){if(!Array.isArray(path)||(mode==='live'&&S.dismissedLive)||(mode==='saved'&&String(identity)===S.dismissedSavedKey))return;
 path=path.filter(valid);const previousMode=S.mode;S.mode=mode;
 if(previousMode!==mode){S.view='compact';S.detailRun=-1;S.panel?.classList.toggle('compact',true);S.panel?.classList.toggle('extended',false);const toggle=$('takElevExpandI683');if(toggle){toggle.textContent='⤢  Expand';toggle.setAttribute('aria-expanded','false')}S.markerSignature=''}
 const routeName=String(name||'').slice(0,70),label=$('takElevRouteNameI683');if(label)label.textContent=mode==='live'?'':(' · '+(routeName||'Saved route'));
 const title=$('takElevTitleI681');if(title)title.textContent='Route Elevation';
 if(path.length<2){S.full=[];clear('Add a second waypoint to see terrain elevation');if(mode==='live')display(live());return}
 const key=mode+':'+(identity||name||'')+':'+signature(path);
 if(key===S.routeKey){if(S.panel?.hidden)display(true);return}
 stop();discardHover();S.routeKey=key;S.full=path.slice();S.samples=[];S.elev=[];S.gradeGeneration++;S.gradeCache=null;S.markerSignature='';S.detailRun=-1;S.retry=0;
 display(true);setStatus('Preparing distance-spaced NDM terrain samples…');const token=S.seq;S.timer=setTimeout(()=>sampleCurrent(token),450);
}
function hideProfile(){S.mode='';S.full=[];S.selectedRouteKey='';S.selectedPopupSource=null;S.selectedProfileContext='';S.detailRun=-1;clear();display(false)}
function updateLive(){if(!S.map)return;if(!live()){if(S.mode==='live')hideProfile();return}if(!S.dismissedLive)setGeometry(liveGeometry(),'live','')}
function syncLifecycle(){const active=live();
 if(active&&!S.wasRouteActive){S.wasRouteActive=true;S.dismissedLive=false;S.dismissedSavedKey='';S.selectedRouteKey='';S.selectedPopupSource=null;S.view='compact';S.markerSignature='';updateLive();return}
 if(!active&&S.wasRouteActive){S.wasRouteActive=false;S.dismissedLive=false;if(S.mode==='live')hideProfile();return}
 if(!active&&S.mode==='saved'&&!S.selectedRouteKey)hideProfile();
}
function savedRoute(id){let feature=null;try{feature=W.localDataFeatureById?.(id)}catch(_){}
 if(!feature){setStatus('Saved route unavailable — reload Local Data');return false}
 const path=featureCoords(feature);if(path.length<2){setStatus('Saved route geometry unavailable');return false}
 const key=String(id);if(S.selectedRouteKey!==key){S.detailRun=-1;S.view='compact'}
 // Explicit Profile action is an intentional request to reopen, even after X.
 S.dismissedSavedKey='';S.selectedRouteKey=key;setGeometry(path,'saved',String(feature.name||'Saved route'),key);return true;
}
// i684: The right-hand Object Details panel does not raise Leaflet popupopen.
// Route geometry is received directly from that panel's authoritative selection.
function fromContextSelectionI684(evt){
 if(live())return;const detail=evt?.detail||{};
 if(!detail.selected){if(S.mode==='saved')hideProfile();S.dismissedSavedKey='';return}
 if(String(detail.kind||'').toLowerCase()!=='route'){
  if(S.mode==='saved')hideProfile();S.dismissedSavedKey='';return;
 }
 const feature=detail.object,key=String(detail.key||feature?._local_id||feature?.object_id||feature?.id||feature?.uid||feature?.name||'');
 const path=featureCoords(feature);
 if(path.length<2){if(S.mode==='saved')hideProfile();console.warn('[TAK Map] selected route has no usable full geometry',key);return}
 // X dismisses the current selection only. A different selection or reselect
 // after deselection starts a new session and is allowed to show the profile.
 if(S.dismissedSavedKey===key)return;
 if(S.selectedRouteKey!==key){S.view='compact';S.detailRun=-1;S.markerSignature=''}
 S.selectedRouteKey=key;S.selectedPopupSource=null;S.selectedProfileContext='sidebar';
 setGeometry(path,'saved',String(feature?.name||feature?.callsign||'Saved route'),key);
}
function fromPopup(evt){if(live())return;
 const src=evt?.popup?._source||evt?.layer;if(!src)return;
 let features=[];try{if(typeof importedFeatures==='function')features=importedFeatures()||[]}catch(_){}
 const feature=features.find(f=>f.__layer===src||f.__hitLayer===src);
 const type=String(feature?.kind||feature?.type||feature?.geometry||'').toLowerCase();
 if(feature&&(type.includes('route')||type.includes('track')||type.includes('linestring'))){const key=String(feature._local_id||feature.object_id||feature.id||feature.uid||feature.name||'');S.selectedPopupSource=src;S.selectedProfileContext='leaflet';S.selectedRouteKey=key;
  if(S.dismissedSavedKey!==key){S.dismissedSavedKey='';setGeometry(featureCoords(feature),'saved',feature.name||'Saved route',key)}return;
 }
 // Selecting a non-route object clears any route-only elevation profile.
 if(S.mode==='saved')hideProfile();
}
function closePopup(evt){if(live()||S.selectedProfileContext!=='leaflet')return;const src=evt?.popup?._source||evt?.layer;if(!src||src!==S.selectedPopupSource)return;hideProfile()}
function hover(e){const rect=S.canvas?.getBoundingClientRect();if(!rect||!S.samples.length)return;
 const total=S.samples[S.samples.length-1].d,view=chartView(total),left=S.view==='compact'?52:70;
 const ratio=Math.max(0,Math.min(1,(e.clientX-rect.left-left)/Math.max(1,rect.width-left-10)));
 const d=view.start+ratio*(view.end-view.start);let lo=0,hi=S.samples.length-1;
 while(lo<hi){const mid=(lo+hi)>>1;if(S.samples[mid].d<d)lo=mid+1;else hi=mid;}
 const idx=Math.max(0,Math.min(S.samples.length-1,lo)),p=S.samples[idx],v=S.elev[idx];
 S.hover=idx;focusMarker(p);S.hover=idx;
 const angle=gradeProfile().angles[Math.max(1,idx)],hasGrade=Number.isFinite(angle);
 const slope=hasGrade?(angle>0?'+':'')+angle.toFixed(1)+'° / '+(Math.tan(angle*Math.PI/180)*100).toFixed(0)+'%':'—';
 const out=$('takElevCursorI681');if(out){out.textContent=fmtMiles(p.d)+' · '+(Number.isFinite(v)?fmtFeet(v):'no terrain sample')+' · Slope '+slope;
  out.style.color=hasGrade?gradeColor(angle):'';}
 draw();updateCompactMileage(p.d,ratio);
}
function mount(){if(S.panel)return true;const map=W.takLeafletMap?.getContainer?W.takLeafletMap:W.map?.getContainer?W.map:null;
 if(!map)return false;S.map=map;
 const el=D.createElement('section');el.id=ID;el.hidden=true;el.className='compact';el.setAttribute('aria-label','Route elevation profile');
 el.innerHTML=`<header class="tak-elev-head-i681"><div id="takElevDragI683" class="tak-elev-drag-i683" tabindex="0" title="Drag to move elevation profile" aria-label="Drag elevation panel"><div class="tak-elev-heading-i682"><strong><span id="takElevTitleI681">Route Elevation</span><span id="takElevRouteNameI683"></span></strong></div><div class="tak-elev-distance-i683"><small>Route distance</small><b id="takElevHeaderDistanceI683">—</b></div></div><div class="tak-elev-controls-i682"><button type="button" id="takElevExpandI683" aria-expanded="false" title="Switch compact / extended view">⤢  Expand</button><button type="button" id="takElevCollapseI681" aria-label="Collapse profile" title="Collapse profile" hidden>−</button><button type="button" id="takElevCloseI681" title="Close elevation profile" aria-label="Close elevation profile">×</button></div></header>
 <div id="takElevBodyI681"><div class="tak-elev-metrics-i682"><div><small>Route distance</small><b id="takElevDistanceI681">—</b></div><div><small>Total ascent</small><b id="takElevGainI681">—</b></div><div><small>Total descent</small><b id="takElevLossI681">—</b></div><div><small>Low / High</small><b><span id="takElevMinI681">—</span> / <span id="takElevMaxI681">—</span></b></div><div><small>Maximum slope</small><b id="takElevSlopeI681">—</b></div><div class="tak-elev-critical-i683"><small>35°+ steep terrain</small><b id="takElevSteepI681">—</b><small id="takElevSteepCountI683">—</small></div></div>
 <div class="tak-elev-chart-i682"><div class="tak-elev-chart-top-i683"><strong>Elevation along route <span id="takElevRangeI683"></span></strong><span class="tak-elev-view-controls-i683"><button type="button" id="takElevFullI683" aria-pressed="true">Full route</button><button type="button" id="takElevDetailI683" aria-pressed="false">Steep detail</button></span></div><div class="tak-elev-legend-i682"><span><i></i>Under 15°</span><span><i class="moderate"></i>15–25°</span><span><i class="steep"></i>25–35°</span><span><i class="danger"></i>35°+</span></div><div class="tak-elev-chart-area-i683"><canvas id="takElevCanvasI681" aria-label="Terrain elevation in feet by route distance in miles"></canvas><div id="takElevMarkersI683" class="tak-elev-markers-i683"></div></div></div>
 <div class="tak-elev-extended-footer-i683"><div id="takElevSteepNoticeI681">35°+ terrain highlighted in red</div><div id="takElevCursorI681">Hover for distance, elevation and slope (° and %)</div><div id="takElevStatusI681" aria-live="polite">Waiting for route</div><div id="takElevQualityI681">Terrain-derived slopes are estimates, not surveyed grades</div></div><span id="takElevStatsI681" hidden>Distance — · Ascent — · Descent —</span></div>`;
 D.body.appendChild(el);S.panel=el;S.canvas=$('takElevCanvasI681');
 const mileage=D.createElement('div');mileage.id='takElevHoverMilesI696';mileage.className='tak-elev-hover-miles-i696';
 mileage.hidden=true;mileage.setAttribute('aria-live','off');
 $('takElevCanvasI681')?.parentElement?.appendChild(mileage);
 const tip=D.createElement('div');tip.id='takElevRunTipI683';tip.hidden=true;tip.setAttribute('role','tooltip');D.body.appendChild(tip);
 attachDrag();
 $('takElevExpandI683').addEventListener('click',e=>{e.stopPropagation();S.collapsed=false;$('takElevBodyI681').hidden=false;setView(S.view==='compact'?'extended':'compact')});
 $('takElevCollapseI681').addEventListener('click',e=>{e.stopPropagation();S.collapsed=!S.collapsed;$('takElevBodyI681').hidden=S.collapsed;e.currentTarget.textContent=S.collapsed?'+':'−';if(!S.collapsed){draw()}place()});
 $('takElevCloseI681').addEventListener('click',e=>{e.preventDefault();e.stopPropagation();if(S.mode==='live')S.dismissedLive=true;else if(S.mode==='saved')S.dismissedSavedKey=S.selectedRouteKey;
  S.mode='';S.full=[];clear();display(false)});
 $('takElevFullI683').addEventListener('click',()=>{S.detailRun=-1;S.markerSignature='';draw()});
 $('takElevDetailI683').addEventListener('click',()=>{const runs=gradeProfile().runs;if(runs.length){S.detailRun=0;S.markerSignature='';draw()}});
 S.canvas.addEventListener('mousemove',hover);S.canvas.addEventListener('mouseleave',()=>{discardHover();const e=$('takElevCursorI681');if(e)e.textContent='Hover for distance, elevation and slope (° and %)';draw()});
 D.addEventListener('click',ev=>{const btn=ev.target.closest?.('[data-tak-elev-route]');if(btn){ev.stopPropagation();savedRoute(btn.getAttribute('data-tak-elev-route'))}},true);
 W.addEventListener('tak-map-route-geometry-i681',()=>{syncLifecycle();if(live())updateLive()});
 W.addEventListener('tak-map-context-selection-i684',fromContextSelectionI684);
 S.map.on?.('popupopen',fromPopup);S.map.on?.('popupclose',closePopup);
 // The sidebar has its own close/deselect event. Do not interpret its map
 // click as a reason to close a freshly selected saved-route profile.
 S.map.on?.('click',()=>W.setTimeout(()=>{if(!live()&&S.mode==='saved'&&S.selectedProfileContext!=='sidebar'&&!S.selectedPopupSource)hideProfile()},80));
 const observeTool=node=>{if(node&&W.MutationObserver)new MutationObserver(syncLifecycle).observe(node,{attributes:true,attributeFilter:['class']})};
 observeTool($('toolRoute'));observeTool($('routeMiniToolbar'));W.setInterval(syncLifecycle,600);
 W.addEventListener('resize',()=>{if(!S.panel.hidden){place();draw()}});
 for(const id of ['map','terrain3dPane']){const target=$(id);if(target&&W.ResizeObserver)new ResizeObserver(()=>{if(!S.panel.hidden){place();draw()}}).observe(target)}
 display(false);syncLifecycle();return true;
}
const style=D.createElement('style');style.id='takElevationStylesI681';style.textContent=`
#${ID}{position:fixed;z-index:1100;left:50%;bottom:24px;transform:translateX(-50%);width:min(580px,calc(100vw - 18px));box-sizing:border-box;color:#dfeaf0;background:rgba(10,23,33,.975);border:1px solid #426576;border-radius:11px;box-shadow:0 18px 46px #000a;font:12px system-ui,sans-serif;pointer-events:auto;overflow:hidden}
#${ID}.extended{width:min(1040px,calc(100vw - 18px));max-height:calc(100dvh - 48px);overflow-y:auto}
#${ID}[hidden],#${ID} [hidden],#takElevRunTipI683[hidden]{display:none!important}
#${ID} .tak-elev-head-i681{display:flex;align-items:center;gap:8px;padding:10px 12px;background:#152b38;border-bottom:1px solid #335161}
#${ID} .tak-elev-drag-i683{display:flex;align-items:center;gap:10px;flex:1;min-width:0;cursor:grab;touch-action:none;user-select:none;-webkit-user-select:none;align-self:stretch}
#${ID} .tak-elev-drag-i683 *{cursor:inherit}
#${ID} .tak-elev-drag-i683.dragging,#${ID} .tak-elev-drag-i683.dragging *{cursor:grabbing}
#${ID} .tak-elev-drag-i683:focus-visible{outline:2px solid #8adaec;outline-offset:-2px;border-radius:4px}
#${ID} .tak-elev-heading-i682{min-width:0;flex:1}
#${ID} .tak-elev-heading-i682 strong{display:block;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#${ID} #takElevRouteNameI683{font-weight:400;color:#a3c4d0}
#${ID} .tak-elev-distance-i683{display:flex;flex-direction:column;align-items:flex-end;text-align:right;gap:1px;white-space:nowrap}
#${ID} .tak-elev-distance-i683 small{font-size:9px;color:#a1c0cc}
#${ID} .tak-elev-distance-i683 b{font-size:13px;font-variant-numeric:tabular-nums}
#${ID} .tak-elev-controls-i682{display:flex;align-items:center;gap:6px;flex:none}
#${ID} button{color:#dcebf0;background:#253d4c;border:1px solid #4c6876;border-radius:6px;cursor:pointer;padding:0 8px;min-height:26px;white-space:nowrap;font-size:11px}
#${ID} button:hover{background:#365667}
#${ID} #takElevCloseI681{min-width:28px;padding:0;color:#ffdbe0;background:#60313c;border-color:#88505a;font-size:17px}
#${ID} #takElevCloseI681:hover{background:#87424e}
#${ID} #takElevCollapseI681{min-width:27px;padding:0;font-size:16px}
#${ID} #takElevBodyI681{padding:8px 9px 9px}
#${ID} .tak-elev-metrics-i682{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:7px;margin-bottom:7px}
#${ID} .tak-elev-metrics-i682>div{min-width:0;padding:6px 8px;border:1px solid #304d5b;background:#112735;border-radius:6px;display:flex;flex-direction:column;gap:2px}
#${ID} .tak-elev-metrics-i682 small{font-size:10px;color:#aac3cd}
#${ID} .tak-elev-metrics-i682 b{font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-variant-numeric:tabular-nums}
#${ID} .tak-elev-metrics-i682 .tak-elev-critical-i683{background:#2b1b29;border-color:#8b4458}
#${ID} .tak-elev-metrics-i682 .tak-elev-critical-i683 b{color:#ff879a}
#${ID} .tak-elev-chart-i682{display:flex;flex-direction:column;background:#0b202b;border:1px solid #304f60;border-radius:7px;overflow:visible}
#${ID} .tak-elev-chart-top-i683{order:0;display:flex;justify-content:space-between;align-items:center;gap:8px;padding:9px 10px 4px}
#${ID} .tak-elev-chart-top-i683 strong{font-size:11px}
#${ID} #takElevRangeI683{font-size:10px;font-weight:400;color:#adbdc6}
#${ID} .tak-elev-view-controls-i683{display:flex;align-items:center}
#${ID} .tak-elev-view-controls-i683 button{font-size:10px;min-height:25px;background:transparent;border-color:#365463}
#${ID} .tak-elev-view-controls-i683 button[aria-pressed=true]{background:#afcbd7;color:#102634}
#${ID} .tak-elev-legend-i682{order:2;display:flex;align-items:center;gap:14px;color:#adc6cf;font-size:10px;padding:7px 11px;border-top:1px solid #284653}
#${ID} .tak-elev-legend-i682 span{display:flex;align-items:center;gap:5px;white-space:nowrap}
#${ID} .tak-elev-legend-i682 i{display:inline-block;width:14px;height:3px;background:#76c8d2;border-radius:3px}
#${ID} .tak-elev-legend-i682 i.moderate{background:#e9cf79}#${ID} .tak-elev-legend-i682 i.steep{background:#f6a65a}#${ID} .tak-elev-legend-i682 i.danger{background:#f16b78}
#${ID} .tak-elev-chart-area-i683{order:1;position:relative;min-width:0;padding:0 4px}
#${ID} #takElevCanvasI681{display:block;width:100%;height:188px;cursor:crosshair}
#${ID} .tak-elev-markers-i683{position:absolute;left:4px;right:4px;top:0;bottom:0;pointer-events:none;overflow:visible}
#${ID} .tak-elev-run-marker-i683{position:absolute;transform:translate(-50%,-50%);display:grid;place-items:center;padding:0;width:21px;height:21px;min-height:0;border:2px solid #ffccd5;border-radius:50%;background:#bd4058;color:white;font-size:10px;font-weight:800;line-height:1;box-shadow:0 0 0 2px #0d1d27,0 3px 8px #0009;pointer-events:auto;cursor:pointer}
#${ID} .tak-elev-run-marker-i683:hover,#${ID} .tak-elev-run-marker-i683:focus-visible{background:#fa526d;box-shadow:0 0 0 4px #ff6b805e;outline:0}
#takElevRunTipI683{position:fixed;z-index:2100;width:235px;box-sizing:border-box;padding:11px 12px;background:#162b39;border:1px solid #d76a7b;border-radius:9px;box-shadow:0 12px 36px #000d;color:#eaf1f5;font:11px/1.5 system-ui,sans-serif;pointer-events:none}
#takElevRunTipI683 small{display:block;color:#ffa2b1;font-size:10px;font-weight:800;letter-spacing:.05em}
#takElevRunTipI683>strong{display:block;font-size:24px;margin:4px 0 6px}
#takElevRunTipI683>div{display:flex;justify-content:space-between;gap:9px;border-top:1px solid #34505c;padding:5px 0}
#takElevRunTipI683>div span{color:#a9c1cc}#takElevRunTipI683>div b{color:#fff;text-align:right}
#${ID} .tak-elev-extended-footer-i683{margin-top:8px;color:#a6bdc7;font-size:10px;line-height:1.5}
#${ID} .tak-elev-extended-footer-i683>div{padding-top:3px}
#${ID} #takElevSteepNoticeI681.danger{color:#ff8b95}
#${ID}.compact .tak-elev-metrics-i682,#${ID}.compact .tak-elev-chart-top-i683,#${ID}.compact .tak-elev-extended-footer-i683{display:none}
#${ID}.compact .tak-elev-legend-i682{order:0;height:23px;box-sizing:border-box;min-height:23px;gap:13px;white-space:nowrap;border-top:0;border-bottom:1px solid #284653;padding:0 9px;font-size:9px}
#${ID}.compact .tak-elev-legend-i682 i{width:12px}
#${ID}.compact .tak-elev-chart-area-i683{order:1;padding:0 4px 20px}
#${ID}.compact #takElevCanvasI681{height:82px}
#${ID} .tak-elev-hover-miles-i696{position:absolute;z-index:5;bottom:1px;transform:translateX(-50%);border:1px solid #638b9d;border-radius:5px;background:rgba(10,28,39,.95);color:#f0f9fb;white-space:nowrap;font:700 10px/1.3 system-ui,sans-serif;font-variant-numeric:tabular-nums;padding:1px 5px;pointer-events:none}
#${ID} .tak-elev-hover-miles-i696[hidden],#${ID}.extended .tak-elev-hover-miles-i696{display:none!important}
#${ID}.compact .tak-elev-run-marker-i683{width:19px;height:19px;font-size:10px}
@media(max-width:700px){#${ID}.extended .tak-elev-metrics-i682{grid-template-columns:repeat(3,minmax(0,1fr))}#${ID}.extended #takElevCanvasI681{height:164px}}
@media(max-width:440px){#${ID} .tak-elev-head-i681{padding:7px 6px;gap:4px}#${ID} .tak-elev-heading-i682 strong{font-size:11px}#${ID} .tak-elev-distance-i683 small{display:none}#${ID} .tak-elev-distance-i683 b{font-size:11px}#${ID} .tak-elev-controls-i682{gap:3px}#${ID} .tak-elev-controls-i682 button{font-size:10px;padding:0 5px}#${ID}.compact .tak-elev-legend-i682{gap:7px;font-size:8px;padding:0 6px}#${ID}.extended .tak-elev-metrics-i682{grid-template-columns:repeat(2,minmax(0,1fr))}}
`;D.head.appendChild(style);
W.TakMapElevationI681={state:S,mount,showSavedRouteById:savedRoute,samplePolyline,featureCoords,liveGeometry,place,redraw:draw,gradeProfile,syncLifecycle,setView,hideProfile};
if(D.readyState==='loading')D.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
function boot(){if(mount())return;let n=0;const t=setInterval(()=>{if(mount()||++n>120)clearInterval(t)},200)}
})(window,document);
