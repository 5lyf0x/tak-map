/* TAK Map i659 Route Editor — persistent editable routes and verified in-place updates.
 * Editable control points, snapped per-leg geometry, and 20 SCREEN-pixel snap limit.
 * No application-level road category/access filters; Valhalla graph/costing still applies.
 */
(function(){
'use strict';
const W=window,D=document, RADIUS=20, METERS_PER_MILE=1609.344;
const ID='tak-route-editor-i654';
const S={editEpoch:0,mode:'roads',routerState:'preparing',routerReady:false,lastRouterCheck:0,wasActive:false,legs:[],pointModes:[],segmentModes:[],pending:new Set(),snap:null,snapRequest:0,
  snapTimer:null,preview:null,previewAbort:null,previewSeq:0,previewPending:false,dirty:0,menu:null,hover:null,markers:[],labels:[],savedLabels:[],pointLayer:null,
  warning:'',installed:false,saveBusy:false,operationBusy:false,undoTransaction:null,suppressClickUntil:0,editing:null,saveAsNew:false};
W.takRouteEditorI654=S;W.takRouteEditorI655=S;
const el=id=>D.getElementById(id),st=()=>W.v233RouteState;
const coords=ll=>[ll.lng,ll.lat];
const asLL=c=>W.L.latLng(c[1],c[0]);
const llObj=ll=>({lat:ll.lat,lon:ll.lng});
const valid=c=>Array.isArray(c)&&c.length===2&&c.every(Number.isFinite)&&Math.abs(c[1])<=90&&Math.abs(c[0])<=180;
function active(){try{return (typeof activeMapTool!=='undefined'&&activeMapTool==='route')||W.activeMapTool==='route'||(el('toolRoute')?.classList.contains('active')===true)}catch(_){return false}}
function distance(a,b){return W.map.distance(a,b)}
function milesText(m){const miles=m/METERS_PER_MILE;return miles>=10?miles.toFixed(1)+' mi':miles.toFixed(2)+' mi'}
function pathDistance(path){let m=0;for(let j=1;j<path.length;j++)m+=distance(path[j-1],path[j]);return m}
function normalizedPoints(){return (st()?.points||[]).map(p=>W.L.latLng(p.lat,p.lng))}
function dropSnap(){S.snapRequest++;S.previewSeq++;clearTimeout(S.snapTimer);try{S.previewAbort?.abort()}catch(_){}S.previewAbort=null;S.snap=null;S.previewPending=false;
  try{if(S.hover){layerRemove(S.hover);S.hover=null}if(S.preview){layerRemove(S.preview);S.preview=null}}catch(_){} }
function setWarning(text){S.warning=String(text||'');drawHud()}
function message(text){setWarning(text);if(el('takRouteWarningI654'))el('takRouteWarningI654').textContent=text}
function layerRemove(layer){if(layer&&W.map.hasLayer(layer))W.map.removeLayer(layer)}
function clearLayers(){const s=st();if(!s)return;['layer','hitLayer'].forEach(k=>{layerRemove(s[k]);s[k]=null});S.markers.forEach(layerRemove);S.labels.forEach(layerRemove);S.markers=[];S.labels=[];layerRemove(S.hover);S.hover=null}
function currentLineColor(){return el('routeColorInput')?.value||st()?.color||'#ff6f2e'}
function segmentShape(i){const p=normalizedPoints();const l=S.legs[i];return l?.shape?.length>=2?l.shape:[p[i],p[i+1]].filter(Boolean)}
function legDistance(i){const l=S.legs[i];if(l&&l.status==='ready')return pathDistance(l.shape);return null}
// Center markers by DISTANCE ALONG the snapped route, never by coordinate midpoint.
function distanceMidpoint(shape){if(!Array.isArray(shape)||shape.length<2)return null;
  const total=pathDistance(shape);if(total<=0)return shape[0];let used=0;
  for(let i=1;i<shape.length;i++){const segment=distance(shape[i-1],shape[i]);
    if(used+segment>=total/2){const t=segment?(total/2-used)/segment:0;
      return W.L.latLng(shape[i-1].lat+(shape[i].lat-shape[i-1].lat)*t,shape[i-1].lng+(shape[i].lng-shape[i-1].lng)*t)}used+=segment}
  return shape[shape.length-1];
}
function legLabel(latlng,meters,index,saved=false){if(!latlng||!Number.isFinite(meters)||meters<=0)return null;
  const marker=W.L.marker(latlng,{interactive:false,keyboard:false,
    icon:W.L.divIcon({className:'tak-route-distance-icon-i658',
      html:'<span class="tak-route-distance-chip-i658">'+escapeHtml(milesText(meters))+'</span>',iconSize:[82,24],iconAnchor:[41,12]})}).addTo(W.map);
  marker.options.title='Leg '+(index+1)+': '+milesText(meters);
  (saved?S.savedLabels:S.labels).push(marker);return marker;
}
function allReady(){const n=normalizedPoints().length;return n>=2&&S.legs.length===n-1&&S.legs.every(l=>l&&l.status==='ready')}
// i676: A save MUST include every control waypoint. An unresolved Valhalla leg is
// an explicitly identified direct/manual connector, not an excuse to discard a
// section of trail or falsely claim that the connector follows mapped roads.
function buildSaveGeometry(){
  const points=normalizedPoints();
  if(points.length<2||points.some(p=>!Number.isFinite(p.lat)||!Number.isFinite(p.lng)||Math.abs(p.lat)>90||Math.abs(p.lng)>180))return null;
  const shape=[],legShapes=[],legEnds=[],fallbackIndices=[];
  const push=p=>{if(!shape.length||Math.abs(shape.at(-1).lat-p.lat)>1e-11||Math.abs(shape.at(-1).lng-p.lng)>1e-11)shape.push(p)};
  for(let i=0;i<points.length-1;i++){
    const leg=S.legs[i],routed=leg?.status==='ready'&&Array.isArray(leg.shape)&&leg.shape.length>=2&&
      leg.shape.every(p=>p&&Number.isFinite(p.lat)&&Number.isFinite(p.lng)&&Math.abs(p.lat)<=90&&Math.abs(p.lng)<=180);
    const part=routed?[points[i],...leg.shape,points[i+1]]:[points[i],points[i+1]];
    if(!routed)fallbackIndices.push(i);
    part.forEach(push);
    legShapes.push(part);
    legEnds.push(shape.length-1);
  }
  // Every original route anchor, including the final endpoint, must survive.
  if(shape.length<2||legEnds.at(-1)!==shape.length-1)return null;
  return {shape,legShapes,legEnds,fallbackIndices,controlCount:points.length,
    distanceM:pathDistance(shape),vertexCount:shape.length};
}
function fullShape(){return buildSaveGeometry()?.shape||null;}
function lineMode(i){return S.segmentModes[i]||'manual'}
function lineSignature(a,b,mode,i){return mode+':'+S.pointModes[i]+':'+S.pointModes[i+1]+':'+a.lat.toFixed(7)+','+a.lng.toFixed(7)+':'+b.lat.toFixed(7)+','+b.lng.toFixed(7)}
function renderLine(){
  const s=st();if(!s||!W.map)return;clearLayers();
  // i684: Never resurrect draft handles after leaving Route Creation.
  if(!active()&&!S.editing)return;
  const pts=normalizedPoints();
  s.layer=W.L.layerGroup().addTo(W.map);s.hitLayer=W.L.layerGroup().addTo(W.map);
  const c=currentLineColor();
  S.legs.forEach((leg,i)=>{
    if(!pts[i+1])return;
    const shape=segmentShape(i),ready=leg?.status==='ready',failed=leg?.status==='error',pending=leg?.status==='pending';
    const color=failed?'#ff5d64':pending?'#f8bb54':c;
    const style={color,weight:ready?4:3,opacity:ready?.95:.92,dashArray:failed?'5 8':pending?'3 7':(el('routeStyleInput')?.value==='dashed'?'8 7':null)};
    W.L.polyline(shape,style).addTo(s.layer);
    if(ready&&leg?.manualStart)W.L.polyline(shape.slice(0,2),{color:'#ffd47a',weight:4,dashArray:'5 5',opacity:1,interactive:false}).addTo(s.layer);
    if(ready&&leg?.manualEnd)W.L.polyline(shape.slice(-2),{color:'#ffd47a',weight:4,dashArray:'5 5',opacity:1,interactive:false}).addTo(s.layer);
    const hit=W.L.polyline(shape,{color:'#fff',weight:18,opacity:0,interactive:true,className:'tak-route-hit-i678'}).addTo(s.hitLayer);
    hit.on('click',event=>{if(!active())return;
      if(event.originalEvent)W.L.DomEvent.stop(event.originalEvent);
      const clicked=closestOnShape(shape,event.latlng);
      const idx=Math.max(0,Math.min(pts.length-2,i));
      insertWaypoint(idx+1,clicked)});
    if(ready&&leg?.shape?.length>=2)legLabel(distanceMidpoint(leg.shape),pathDistance(leg.shape),i);
    if(failed){const middle=shape[Math.floor(shape.length/2)];const lbl=W.L.marker(middle,{interactive:false,icon:W.L.divIcon({className:'tak-route-failure-i654',html:'!',iconSize:[20,20],iconAnchor:[10,10]})}).addTo(W.map);S.labels.push(lbl)}
  });
  pts.forEach((p,i)=>{
    const marker=W.L.marker(p,{draggable:true,keyboard:true,autoPan:false,
      icon:W.L.divIcon({className:'tak-route-point-i654'+(S.pointModes[i]==='manual'?' is-manual':''),
      html:'<span>'+String(i+1)+'</span>',iconSize:[24,24],iconAnchor:[12,12]})}).addTo(W.map);
    marker.on('click',ev=>{
      if(ev.originalEvent)W.L.DomEvent.stop(ev.originalEvent);
      showMenu(i,marker.getLatLng())});
    marker.on('dragstart',()=>{S.suppressClickUntil=Date.now()+600;hideMenu();dropSnap();setWarning('Dragging waypoint '+(i+1)+'…')});
    marker.on('dragend',ev=>{S.suppressClickUntil=Date.now()+400;hideMenu();const next=ev.target.getLatLng();
      // Manual controls stay at exact drag location; Roads controls must snap within 20px.
      moveWaypoint(i,next).catch(e=>message('Waypoint could not move: '+e.message))});
    S.markers.push(marker);
  });
  drawHud();
  try{W.dispatchEvent(new Event('tak-map-route-geometry-i681'))}catch(_){}
}
function closestOnShape(shape,target){
  const map=W.map,p=map.latLngToLayerPoint(target);let best=Infinity,result=target;
  for(let j=1;j<shape.length;j++){
    const a=map.latLngToLayerPoint(shape[j-1]),b=map.latLngToLayerPoint(shape[j]);
    const dx=b.x-a.x,dy=b.y-a.y,t=Math.max(0,Math.min(1,((p.x-a.x)*dx+(p.y-a.y)*dy)/(dx*dx+dy*dy||1)));
    const q=W.L.point(a.x+t*dx,a.y+t*dy),d=p.distanceTo(q);
    if(d<best){best=d;result=map.layerPointToLatLng(q)}
  }return result;
}
function drawHud(){
  const hud=el('takRouteHudI654');if(!hud)return;const pts=normalizedPoints(),parts=[];let total=0;
  for(let i=0;i<pts.length-1;i++){
    const l=S.legs[i];let t='…';const m=legDistance(i);
    if(m!==null){total+=m;t=milesText(m)+(l.manualStart||l.manualEnd?' *':'')}else if(l?.status==='error'){const direct=pathDistance([pts[i],pts[i+1]]);total+=direct;t=milesText(direct)+' direct'}else if(l?.status==='pending'){const direct=pathDistance([pts[i],pts[i+1]]);total+=direct;t=milesText(direct)+' pending'}else{const direct=pathDistance([pts[i],pts[i+1]]);total+=direct;t=milesText(direct)+' direct'}
    parts.push('<div class="tak-route-leg-i654" title="Waypoint '+(i+1)+' to '+(i+2)+'">'+
      '<span>'+(i+1)+' → '+(i+2)+'</span><strong>'+t+'</strong></div>');
  }
  const pending=S.legs.some(l=>l?.status==='pending'),errors=S.legs.some(l=>l?.status==='error');
  hud.hidden=!active();
  hud.innerHTML='<div class="tak-route-hud-head-i654"><strong>Route distance</strong><span>'+(pts.length>=2?milesText(total)+(allReady()?'':' *'):'Calculating')+'</span></div>'+
    '<div class="tak-route-hud-legs-i654">'+(parts.join('')||'<small>Click the map to start a route.</small>')+'</div>'+
    (pending||S.previewPending?'<div class="tak-route-warning-i654">Calculating route…</div>':'')+
    (errors?'<div class="tak-route-warning-i654">Disconnected leg — full route can still be saved with marked direct connectors.</div>':'')+
    (S.legs.some(l=>l?.manualStart||l?.manualEnd)?'<small>* Dashed gold segment is manually placed.</small>':'')+
    (S.warning?'<div class="tak-route-warning-i654">'+escapeHtml(S.warning)+'</div>':'')+
    (pts.length>=2?'<div class="tak-route-transform-actions-i673">'+
      '<button type="button" data-route-edit-action="reverse" '+(S.operationBusy?'disabled':'')+'>Reverse</button>'+
      '<button type="button" data-route-edit-action="return" '+(S.operationBusy?'disabled':'')+'>Back to Start</button></div>':'')+
    (S.editing?'<div class="tak-route-edit-actions-i659">'+
      '<button type="button" data-route-edit-action="save">Save Changes</button>'+
      '<button type="button" data-route-edit-action="copy">Save as New Route</button>'+
      '<button type="button" data-route-edit-action="cancel">Cancel</button></div>':'');
}

function signatureI673(a,b,mode,modeA,modeB){return mode+':'+modeA+':'+modeB+':'+a.lat.toFixed(7)+','+a.lng.toFixed(7)+':'+b.lat.toFixed(7)+','+b.lng.toFixed(7)}
function routeSnapshot(){return {points:normalizedPoints().slice(),pointModes:S.pointModes.slice(),segmentModes:S.segmentModes.slice(),legs:S.legs.map(l=>l&&{...l,shape:Array.isArray(l.shape)?l.shape.slice():[]})}}
function restoreSnapshot(snapshot){const s=st();if(!s||!snapshot)return;s.points=snapshot.points.slice();S.pointModes=snapshot.pointModes.slice();S.segmentModes=snapshot.segmentModes.slice();S.legs=snapshot.legs.map(l=>l&&{...l,shape:l.shape.slice()});S.warning='';renderLine()}
function commitTransaction(before,points,pointModes,segmentModes,legs){
  if(!active())return false;S.dirty++;dropSnap();const s=st();if(!s)return false;
  s.points=points;S.pointModes=pointModes;S.segmentModes=segmentModes;S.legs=legs;
  S.undoTransaction={snapshot:before,dirty:S.dirty};S.warning='';renderLine();return true;
}
async function routeLegWithNavigation(a,b,modeA,modeB){
  const pair=await Promise.all([a,b].map((pt,i)=>((i?modeB:modeA)==='manual')
    ?requestJson('/api/tak-map/routing/snap',llObj(pt)).then(x=>W.L.latLng(x.lat,x.lon)):Promise.resolve(pt)));
  const data=await requestJson('/api/tak-map/routing/resolve',{locations:pair.map(llObj),mode:'roads',unrestricted:true});
  const path=data.geometry?.coordinates?.filter(valid).map(asLL);
  if(!path||path.length<2)throw Error('Navigation returned no connected road geometry');
  const gapA=pxDistance(a,path[0]),gapB=pxDistance(b,path[path.length-1]);
  if((modeA!=='manual'&&gapA>RADIUS)||(modeB!=='manual'&&gapB>RADIUS))throw Error('Navigation path no longer connects within 20px');
  const manualStart=modeA==='manual'&&gapA>.5,manualEnd=modeB==='manual'&&gapB>.5;
  if(manualStart)path.unshift(a);if(manualEnd)path.push(b);
  return {shape:path,manualStart,manualEnd};
}
async function reverseRoute(){
  if(S.operationBusy||S.saveBusy||!allReady())return message('Finish calculating the route before reversing it.');
  const original=routeSnapshot(),pts=original.points.slice().reverse(),modes=original.pointModes.slice().reverse();
  const segments=original.segmentModes.slice().reverse(),epoch=S.dirty;
  S.operationBusy=true;S.warning='Reversing route — validating travel direction…';drawHud();
  try{
    const legs=original.legs.slice().reverse().map((old,i)=>{
      const shape=old.shape.slice().reverse(),mode=segments[i];return {...old,shape,mode,
        manualStart:old.manualEnd,manualEnd:old.manualStart,signature:signatureI673(pts[i],pts[i+1],mode,modes[i],modes[i+1])};
    });
    // A reversed Valhalla route may cross a one-way segment in the wrong direction.
    // Revalidate *routed* legs with a bounded concurrency of 2; no map redraws while running.
    let cursor=0;
    const worker=async()=>{while(cursor<legs.length){const i=cursor++;if(segments[i]!=='roads')continue;
      const result=await routeLegWithNavigation(pts[i],pts[i+1],modes[i],modes[i+1]);
      legs[i]={...legs[i],...result,status:'ready'};
    }};
    await Promise.all(Array.from({length:Math.min(2,legs.length)},worker));
    if(epoch!==S.dirty||!active())return;
    commitTransaction(original,pts,modes,segments,legs);
  }catch(e){S.warning='Reverse failed: '+String(e.message||e)+' — original route retained.';drawHud()}
  finally{S.operationBusy=false;drawHud()}
}
async function backToStart(){
  if(S.operationBusy||S.saveBusy||!allReady())return message('Finish calculating the route before returning to start.');
  const original=routeSnapshot(),pts=original.points,first=pts[0],last=pts.at(-1),epoch=S.dirty;
  if(distance(first,last)<2){message('Already back at start.');return}
  S.operationBusy=true;S.warning='Calculating return leg to starting point…';drawHud();
  try{
    const routed=await routeLegWithNavigation(last,first,original.pointModes.at(-1),original.pointModes[0]);
    if(epoch!==S.dirty||!active())return;
    const controlPoints=pts.concat([W.L.latLng(first.lat,first.lng)]),modes=original.pointModes.concat(original.pointModes[0]);
    const segments=original.segmentModes.concat('roads');
    const index=segments.length-1,leg={...routed,status:'ready',mode:'roads',
      signature:signatureI673(last,first,'roads',modes[index],modes[index+1])};
    commitTransaction(original,controlPoints,modes,segments,original.legs.concat([leg]));
  }catch(e){S.warning='Back to Start failed: '+String(e.message||e)+' — no return waypoint added.';drawHud()}
  finally{S.operationBusy=false;drawHud()}
}
function escapeHtml(text){return String(text).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function showMenu(i,p){hideMenu();const node=D.createElement('div');node.className='tak-route-menu-i654';
  node.setAttribute('role','menu');node.innerHTML='<div class="tak-route-menu-title-i654">Waypoint '+(i+1)+'</div>'+
    '<button type="button" data-op="manual" role="menuitem">'+(S.pointModes[i]==='manual'?'✓ ':'')+'Manual</button>'+
    '<button type="button" data-op="copy" role="menuitem">Copy Coordinates</button>'+
    '<button type="button" data-op="delete" role="menuitem">Delete</button>';
  D.body.appendChild(node);S.menu=node;
  const pix=W.map.latLngToContainerPoint(p),box=W.map.getContainer().getBoundingClientRect();
  node.style.left=Math.max(8,Math.min(innerWidth-160,box.left+pix.x+12))+'px';
  node.style.top=Math.max(8,Math.min(innerHeight-104,box.top+pix.y-6))+'px';
  node.addEventListener('pointerdown',ev=>ev.stopPropagation());
  node.addEventListener('click',async ev=>{const op=ev.target.closest('button')?.dataset.op;if(!op)return;ev.stopPropagation();
    if(op==='copy'){
      const ll=normalizedPoints()[i],value=ll.lat.toFixed(6)+', '+ll.lng.toFixed(6);
      try{await navigator.clipboard.writeText(value);message('Copied coordinates: '+value)}
      catch(_){const field=D.createElement('textarea');field.value=value;D.body.appendChild(field);field.select();try{D.execCommand('copy');message('Copied coordinates: '+value)}catch(err){message('Copy failed; coordinates: '+value)}field.remove()}
    } else if(op==='delete'){
      deleteWaypoint(i);
    } else if(op==='manual'){
      S.pointModes[i]=S.pointModes[i]==='manual'?'roads':'manual';
      message(S.pointModes[i]==='manual'?'Waypoint '+(i+1)+' is manual (no snapping).':'Waypoint '+(i+1)+' uses Roads snapping.');
      recompute();
    }hideMenu()});
}
function hideMenu(){if(S.menu){S.menu.remove();S.menu=null}}
function pxDistance(a,b){return W.map.latLngToContainerPoint(a).distanceTo(W.map.latLngToContainerPoint(b))}
async function requestJson(path,payload,signal){const r=await fetch(path,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload),signal,cache:'no-store'});
  let body;try{body=await r.json()}catch(_){throw new Error('Routing service returned an invalid response')}
  if(!r.ok||body?.ok!==true)throw new Error(body?.error||'Routing service unavailable');return body;}
async function getSnap(point,signal){
  const found=await requestJson('/api/tak-map/routing/snap',llObj(point),signal);
  const ll=W.L.latLng(found.lat,found.lon);
  if(pxDistance(point,ll)>RADIUS)throw new Error('No mapped road within 20px');
  return ll;
}
async function acceptPoint(ll,isManual=false){if(isManual||S.mode==='manual')return ll;
  if(S.snap&&Date.now()-S.snap.when<2200&&pxDistance(ll,S.snap.input)<8&&pxDistance(ll,S.snap.loc)<=RADIUS)return S.snap.loc;
  return getSnap(ll);
}
function showPreview(points,manual=false){layerRemove(S.preview);S.preview=null;
  if(!points||points.length<2)return;
  S.preview=W.L.polyline(points,{color:manual?'#f6bb63':'#50ddca',weight:3,
    opacity:.93,dashArray:'7 6',interactive:false}).addTo(W.map);
}
function schedulePreview(point){
  if(!active()){dropSnap();return}
  const seq=++S.previewSeq;S.snapRequest++;clearTimeout(S.snapTimer);try{S.previewAbort?.abort()}catch(_){}
  S.previewAbort=typeof AbortController!=='undefined'?new AbortController():null;const signal=S.previewAbort?.signal;
  const last=normalizedPoints().at(-1);
  if(S.mode==='manual'){
    S.snap=null;layerRemove(S.hover);S.hover=null;S.previewPending=false;
    showPreview(last?[last,point]:null,true);return;
  }
  S.snapTimer=setTimeout(async()=>{
    try{
      const loc=await getSnap(point,signal);
      if(seq!==S.previewSeq||!active()||S.mode!=='roads')return;
      S.snap={input:point,loc,when:Date.now()};layerRemove(S.hover);
      S.hover=W.L.circleMarker(loc,{radius:7,color:'#50ddca',fillColor:'#50ddca',fillOpacity:.32,weight:2,interactive:false}).addTo(W.map);
      if(!last){showPreview(null);S.previewPending=false;return}
      S.previewPending=true;drawHud();
      const data=await requestJson('/api/tak-map/routing/resolve',{
        locations:[llObj(last),llObj(loc)],mode:'roads',unrestricted:true},signal);
      if(seq!==S.previewSeq||!active()||S.mode!=='roads')return;
      const path=data.geometry?.coordinates?.filter(valid).map(asLL);
      if(!path||path.length<2)throw new Error('No connected preview path');
      showPreview(path);
    }catch(_){if(seq===S.previewSeq){showPreview(null);layerRemove(S.hover);S.hover=null;S.snap=null}}
    finally{if(seq===S.previewSeq){S.previewPending=false;drawHud()}}
  },210);
}
function ensureModes(){const n=normalizedPoints().length;while(S.pointModes.length<n)S.pointModes.push('manual');S.pointModes.length=n;while(S.segmentModes.length<n-1)S.segmentModes.push('manual');S.segmentModes.length=Math.max(0,n-1)}
function recompute(){
  const editEpoch=S.editEpoch;dropSnap();S.undoTransaction=null;const pts=normalizedPoints();ensureModes();const previous=S.legs;const next=[];S.dirty++;
  for(let i=0;i<pts.length-1;i++){
    const mode=lineMode(i),sig=lineSignature(pts[i],pts[i+1],mode,i);
    const old=previous.find(l=>l?.signature===sig&&l?.status==='ready');
    if(old){next.push(old);continue}
    if(mode==='manual'){next.push({signature:sig,status:'ready',mode,shape:[pts[i],pts[i+1]]});continue}
    next.push({signature:sig,status:'pending',mode,shape:[pts[i],pts[i+1]]});
  }
  S.legs=next;renderLine();
  next.forEach((leg,i)=>{
    if(leg.status!=='pending')return;
    const a=pts[i],b=pts[i+1],sig=leg.signature;
    Promise.all([a,b].map(async(pt,offset)=>{
      if(S.pointModes[i+offset]!=='manual')return pt;
      const found=await requestJson('/api/tak-map/routing/snap',llObj(pt));
      return W.L.latLng(found.lat,found.lon);
    })).then(pair=>{
      // A canceled edit must not start another resolve after its snap replies.
      if(editEpoch!==S.editEpoch||S.legs[i]!==leg||!active())return null;
      return requestJson('/api/tak-map/routing/resolve',
       {locations:pair.map(llObj),mode:'roads',unrestricted:true});})
      .then(data=>{
        if(!data||editEpoch!==S.editEpoch||!active()||S.legs[i]!==leg)return;
        if(!normalizedPoints()[i+1]||lineSignature(normalizedPoints()[i],normalizedPoints()[i+1],lineMode(i),i)!==sig)return;
        const path=data.geometry?.coordinates?.filter(valid).map(asLL);
        if(!path||path.length<2)throw new Error('Routing engine returned no connected path');
        // Roads controls must connect within 20 SCREEN pixels. A manually overridden
        // single waypoint may lie off-graph: draw an EXPLICIT direct connector at
        // that endpoint, retaining routed graph geometry for the remainder.
        const startGap=pxDistance(a,path[0]),endGap=pxDistance(b,path[path.length-1]);
        if((S.pointModes[i]!=='manual'&&startGap>RADIUS)||
           (S.pointModes[i+1]!=='manual'&&endGap>RADIUS))
          throw new Error('Routing result did not connect within 20px');
        leg.manualStart=S.pointModes[i]==='manual'&&startGap>.5;
        leg.manualEnd=S.pointModes[i+1]==='manual'&&endGap>.5;
        if(leg.manualStart)path.unshift(a);
        if(leg.manualEnd)path.push(b);
        leg.status='ready';leg.shape=path;renderLine();
      })
      .catch(err=>{if(editEpoch!==S.editEpoch||!active()||S.legs[i]!==leg)return;leg.status='error';leg.error=String(err.message||err);renderLine()});
  });
}
async function addWaypoint(ll){
  try{const chosenMode=S.mode,point=await acceptPoint(ll),s=st();if(!active()||!s)return;
    const isNext=s.points.length>0;s.points.push(point);S.pointModes.push(chosenMode);if(isNext)S.segmentModes.push(chosenMode);setWarning('');recompute();
  }catch(e){console.error('i654 add waypoint:',e);message(String(e.message||e)+' — switch to Manual or choose a closer road.')}
}
async function insertWaypoint(index,ll){
  const existing=normalizedPoints();if(!active()||index<1||index>=existing.length)return;
  try{const oldMode=S.segmentModes[index-1]||'manual';const point=oldMode==='roads'?await acceptPoint(ll):ll,s=st();s.points.splice(index,0,point);
    S.pointModes.splice(index,0,oldMode);S.segmentModes.splice(index-1,1,oldMode,oldMode);setWarning('');recompute();
  }catch(e){message(String(e.message||e)+' — no waypoint inserted.')}
}
function deleteWaypoint(index){
  const s=st();if(!s||index<0||index>=s.points.length)return;
  s.points.splice(index,1);S.pointModes.splice(index,1);
  if(index===0)S.segmentModes.shift();
  else if(index>=s.points.length)S.segmentModes.pop();
  else S.segmentModes.splice(index,1);
  hideMenu();setWarning('');recompute();
}
async function moveWaypoint(index,ll){
  const s=st();if(!s||!s.points[index])return;
  try{const point=S.pointModes[index]==='manual'?ll:await getSnap(ll);
    if(!s.points[index])return;s.points[index]=point;setWarning('');recompute();
  }catch(e){message(String(e.message||e)+' — previous waypoint restored.');renderLine()}
}

// Serialize the resolved road vertices directly into the GeoJSON upload. Do not
// temporarily replace v233RouteState.points: that array belongs to the editor,
// and old finish/name-dialog wrappers can read or restore only the anchor points.
function resolvedSaveState(){
  const saved=buildSaveGeometry();
  return {ready:!!saved,controlCount:normalizedPoints().length,
    vertexCount:saved?.vertexCount||0,distanceM:saved?.distanceM??null,
    fallbackCount:saved?.fallbackIndices.length||0,
    pending:S.legs.some(l=>l?.status==='pending'),failed:S.legs.some(l=>l?.status==='error'),
    fullyRouted:!!saved&&!saved.fallbackIndices.length};
}
async function saveResolvedRoute(overrides={}){
  if(S.saveBusy||S.operationBusy)return false;
  const fields=overrides&&typeof overrides==='object'?overrides:{};
  const value=(key,id,fallback='')=>Object.prototype.hasOwnProperty.call(fields,key)
    ? String(fields[key]??'') : (el(id)?.value||fallback);
  const prepared=buildSaveGeometry();
  if(!prepared){message('Add at least two valid route waypoints.');return false}
  const shape=prepared.shape;
  // Clone the final geometry before any prompt, upload, redraw or asynchronous
  // refresh can alter the current editor state.
  const coordinates=shape.map(p=>[Number(p.lng),Number(p.lat)]);
  if(coordinates.some(p=>!valid(p))){message('Route contains invalid coordinates.');return false}
  const get=(id,fallback='')=>el(id)?.value||fallback;
  let name=String(value('name','routeNameInput','')).trim();
  if(!name||(!Object.prototype.hasOwnProperty.call(fields,'name')&&/^Route\s+\d{1,2}[:/]\d{1,2}/i.test(name))){
    const suggestion=name||'Route '+new Date().toLocaleString();
    const entered=W.prompt('Route name:',suggestion);
    if(entered===null)return false;
    name=String(entered||'').trim()||suggestion;
    if(el('routeNameInput'))el('routeNameInput').value=name;
  }
  const notes=value('notes','routeNotesInput'),method=get('routeMethodInput','Driving');
  const direction=get('routeDirectionInput','Infil'),type=get('routeTypeInput','Primary');
  const order=get('routeOrderInput','Ascending Check Points'),prefix=get('routePrefixInput','CP');
  const color=value('color','routeColorInput','#ff6f2e'),style=get('routeStyleInput','solid');
  const category=value('category','routeCategoryInput','General');
  const meters=pathDistance(shape);
  const routingDatasetId=(W.TakMapRoutingDataI675?.currentDatasetId?.()||'');
  const controlCount=prepared.controlCount;
  const properties={name,kind:'route',source:'TAK Map Route Tool',notes,
    category,route_category:category,stroke_color:color,
    length_m:meters,length_km:meters/1000,length_miles:meters/METERS_PER_MILE,
    start_lat:shape[0].lat,start_lon:shape[0].lng,
    end_lat:shape[shape.length-1].lat,end_lon:shape[shape.length-1].lng,
    remarks:'Method: '+method+'\nDirection: '+direction+'\nRoute Type: '+type+
      '\nOrder: '+order+'\nPrefix: '+prefix+'\nLine Style: '+style+'\nNotes: '+notes,
    route_method:method,route_direction:direction,route_type:type,
    checkpoint_order:order,checkpoint_prefix:prefix,color,line_style:style,
    lineStyle:style,style,route_style:style,atak_cot_type:'b-m-r',
    atak_route_metadata:{method,direction,routetype:type,order,prefix,color,style},
    takmap_route_editor:'resolved-line-v2',route_control_point_count:controlCount,
    route_geometry_quality:prepared.fallbackIndices.length?'mixed-with-direct-connectors':'fully-routed',
    route_fallback_leg_indices:prepared.fallbackIndices.join(','),
    route_fallback_leg_count:prepared.fallbackIndices.length,
    route_resolved_vertex_count:coordinates.length,
    route_segment_modes:S.segmentModes.join(',').slice(0,400),
    route_leg_label_count:S.legs.length,route_editor_version:'i677',
    route_control_format:'lat-lon-mode-per-index',
    route_leg_geometry_format:'end-vertex-index-per-index',
    takmap_routing_dataset_id_i675:routingDatasetId};
  normalizedPoints().forEach((p,i)=>{properties['route_cp_'+i]=[p.lat.toFixed(7),p.lng.toFixed(7),S.pointModes[i]||'roads'].join(',')});
  prepared.legEnds.forEach((end,i)=>{properties['route_leg_end_'+i]=String(end)});
  S.legs.forEach((leg,i)=>{if(leg?.status!=='ready')return;
    const center=distanceMidpoint(leg.shape);if(!center)return;
    properties['route_leg_label_'+i]=[center.lat.toFixed(7),center.lng.toFixed(7),Math.round(pathDistance(leg.shape))].join(',');
  });
  const feature={type:'Feature',geometry:{type:'LineString',coordinates},properties};
  const safe=String(name).replace(/[\\/:*?"<>|]+/g,'-').slice(0,80)||'TAK Map Route';
  const updateExisting=!!S.editing&&!S.saveAsNew;
  const editRef=S.editing&&{...S.editing};
  const body=new FormData();
  if(!updateExisting)body.append('files',new File([new Blob([JSON.stringify({type:'FeatureCollection',features:[feature]})],
    {type:'application/geo+json'})],safe+'.geojson',{type:'application/geo+json'}));
  S.saveBusy=true;
  try{
    const response=updateExisting
      ?await fetch('/api/tak-map/route-update-i659',{method:'POST',credentials:'same-origin',cache:'no-store',
        headers:{'Content-Type':'application/json'},body:JSON.stringify({import_id:editRef.importId,
          object_id:editRef.objectId,expected_revision:editRef.revision,feature})})
      :await fetch('/api/tak-map/import',{method:'POST',body,credentials:'same-origin',cache:'no-store'});
    let result;try{result=await response.json()}catch(_){throw Error('Invalid route-save response')}
    if(!response.ok||result?.ok!==true)throw Error(result?.error||'Route upload failed');
    // i677: A filename is NOT a route identity. The importer appends a fresh
    // record on each upload and returns its unique ID in `added`. In particular,
    // result.imports can contain many earlier saves with the identical name.
    const additions=Array.isArray(result.added)?result.added:[];
    const savedImportId=updateExisting?String(editRef.importId||''):
      String(additions.find(item=>item&&item.name===safe+'.geojson'&&item.id)?.id||'');
    if(!savedImportId)throw Error('Route uploaded but server did not identify the new import; full route remains editable');
    // Compare every persisted vertex in order, rather than only endpoints.
    const sameRoute=(entry)=>Array.isArray(entry?.coords)&&entry.coords.length===coordinates.length&&entry.coords.every((pt,i)=>
      Array.isArray(pt)&&Math.abs(Number(pt[0])-coordinates[i][1])<1e-5&&
      Math.abs(Number(pt[1])-coordinates[i][0])<1e-5);
    const routeFromImport=(imp)=>{
      if(!imp||String(imp.id||'')!==savedImportId)return null;
      const items=(imp.features||[]).filter(f=>f&&f.kind==='route');
      return updateExisting?items.find(f=>String(f.object_id||f.local_id||'')===String(editRef.objectId||'')):
        items.find(f=>sameRoute(f))||items[0]||null;
    };
    // A successful POST is not sufficient. GET must return the exact newly
    // created (or updated) record; never fall back to a same-named older import.
    // Allow a short bounded settle window if a backed storage view lags POST.
    let stored=null,checkFile=null,lastCheckError=null;
    for(let attempt=0;attempt<3;attempt++){
      if(attempt)await new Promise(resolve=>setTimeout(resolve,120*attempt));
      try{
        const check=await fetch('/api/tak-map/imported',{credentials:'same-origin',cache:'no-store'});
        if(!check.ok)throw Error('HTTP '+check.status);
        const checkData=await check.json();
        checkFile=(Array.isArray(checkData?.imports)?checkData.imports:[]).find(item=>
          String(item?.id||'')===savedImportId);
        stored=routeFromImport(checkFile);
        if(stored&&sameRoute(stored))break;
        lastCheckError=checkFile?'stored route geometry is incomplete':'new route ID was not found in Local Data';
      }catch(e){lastCheckError=String(e&&e.message||e)}
    }
    if(!stored||!sameRoute(stored))throw Error('Route save not verified for import '+savedImportId+': '+
      (lastCheckError||'stored geometry missing or incomplete')+'; full editable route retained');
    const geometryVariance=false;
    try{if(typeof W.refreshImports==='function')await W.refreshImports();
      else{if(typeof W.refreshLocalData==='function')await W.refreshLocalData();
        if(typeof W.drawImportedObjects==='function')W.drawImportedObjects();}}
    catch(e){console.warn('Route saved; map refresh deferred',e)}
    S.editing=null;S.saveAsNew=false;
    if(typeof W.v233ClearRoute==='function')W.v233ClearRoute();
    else{const s=st();if(s)s.points=[];S.legs=[];clearLayers()}
    if(typeof W.v233ClosePanel==='function')W.v233ClosePanel('routeEditPanel');
    if(typeof W.setActiveMapTool==='function')W.setActiveMapTool('move');
    if(geometryVariance||prepared.fallbackIndices.length){
      const note=D.createElement('div');note.className='tak-route-save-info-i675';
      note.setAttribute('role','status');note.textContent=prepared.fallbackIndices.length?'Entire route saved with '+prepared.fallbackIndices.length+' clearly marked direct connector(s) where road routing was unavailable.':'Route saved; stored geometry was rounded slightly.';
      Object.assign(note.style,{position:'fixed',right:'18px',bottom:'26px',zIndex:'8000',
        maxWidth:'310px',padding:'10px 13px',border:'1px solid #759fb5',borderRadius:'9px',
        background:'#182b3aeF',color:'#eaf7ff',boxShadow:'0 12px 28px #0009',fontSize:'12px'});
      D.body.append(note);setTimeout(()=>note.remove(),8500);
    }
    return true;
  }catch(e){message('Save failed: '+String(e.message||e)+' — route still editable.');return false}
  finally{S.saveBusy=false}
}

function ensureUi(){
  if(el(ID)&&el('takRouteSelectorI654')&&el('takRouteHudI654'))return;
  const style=D.createElement('style');style.id=ID;style.textContent=`
    .tak-route-selector-i654{position:fixed!important;z-index:12000;left:310px;top:115px;display:flex;align-items:center;gap:3px;padding:3px;border:1px solid #4a5965;border-radius:11px;background:#101923ec;color:#e8f2f7;box-shadow:0 6px 20px #0008;pointer-events:auto}
    .tak-route-selector-i654 button{padding:6px 10px;background:transparent;border:0;border-radius:7px;color:inherit;cursor:pointer;font:600 12px system-ui}
    .tak-route-selector-i654 button.active{background:#227d94;color:white}
    #takRouteNetworkStateI655{color:#f6c778;font:600 11px system-ui;max-width:200px;padding:0 8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
    @media(max-width:1100px){#takRouteNetworkStateI655{max-width:145px}}
    body.tak-route-roads-i654 .tak-route-live-preview-v491{display:none!important}
    .tak-route-hud-i654{position:fixed;z-index:11000;right:16px;bottom:72px;background:#121b25ee;border:1px solid #3b4c5b;border-radius:12px;width:210px;max-height:calc(100vh - 175px);overflow-y:auto;padding:10px 12px;color:#eef5f7;font:12px system-ui;box-shadow:0 8px 22px #0007}
    .tak-route-hud-i654[hidden],.tak-route-selector-i654[hidden]{display:none!important}
    .tak-route-hud-head-i654,.tak-route-leg-i654{display:flex;justify-content:space-between;gap:10px;padding:5px 0}
    .tak-route-hud-head-i654{border-bottom:1px solid #3b4c5b}.tak-route-hud-legs-i654{overflow:visible;max-height:none}
    .tak-route-leg-i654{color:#aebfc9}.tak-route-leg-i654 strong{color:#e8eff3}
    .tak-route-warning-i654{padding:6px 0;color:#ffc579}
    .tak-route-point-i654{border-radius:50%;background:#173340;border:2px solid #71d3e1;text-align:center;line-height:20px;color:white;font-weight:700;font-size:11px;box-shadow:0 2px 7px #0009}
    .tak-route-point-i654.is-manual{background:#5d3c19;border-color:#ffd47a}
    .tak-route-failure-i654{color:white;background:#ca444c;border-radius:50%;font-weight:900;text-align:center;line-height:20px}
    .tak-route-distance-icon-i658{background:transparent;border:0;pointer-events:none!important}
    .tak-route-distance-chip-i658{display:inline-block;white-space:nowrap;padding:3px 7px;border-radius:7px;
      background:#101a24eF;color:#f4f7f9;border:1px solid #7ebbd1;box-shadow:0 2px 8px #000a;
      font:700 11px/16px system-ui;text-align:center;pointer-events:none}
    .tak-route-menu-i654{position:fixed;z-index:19000;min-width:142px;display:grid;padding:4px;border-radius:7px;background:#111b25;border:1px solid #526779;box-shadow:0 10px 28px #000a;color:white;font:700 11px system-ui}
    .tak-route-menu-title-i654{font-weight:800;padding:3px 4px;color:#b7ccd6;text-transform:uppercase;font-size:10px}
    .tak-route-menu-i654 button{border:0;border-radius:4px;background:transparent;color:white;font-weight:750;text-align:left;padding:4px;cursor:pointer;line-height:1.25}
    .tak-route-menu-i654 button[data-op=delete]{color:#ff8e8e}
    .tak-route-transform-actions-i673{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:10px;padding:9px 0 3px;border-top:1px solid #3b4c5b}
    .tak-route-transform-actions-i673 button{padding:7px 3px;background:#1c3443;color:#eef7fa;border:1px solid #4b7889;border-radius:6px;font:750 11px system-ui;cursor:pointer}
    .tak-route-transform-actions-i673 button:disabled{opacity:.45;cursor:wait}
    .tak-route-edit-actions-i659{display:flex;flex-wrap:wrap;gap:5px;margin-top:9px;border-top:1px solid #3b4c5b;padding-top:9px}
    .tak-route-edit-actions-i659 button{padding:6px 8px;border:1px solid #526779;border-radius:6px;background:#213747;color:#eef7fa;font:700 11px system-ui;cursor:pointer}
    .tak-route-edit-actions-i659 button[data-route-edit-action=save]{background:#135b6e;border-color:#40a4bb}
    .tak-route-saved-edit-i659{margin:7px 0 2px;padding:6px 12px;border:1px solid #458da7;border-radius:7px;background:#143b4c;color:#eef7fa;font:800 12px system-ui;cursor:pointer}
    .tak-route-menu-i654 button:hover{background:#26495d}
    @media(max-width:700px){.tak-route-selector-i654{max-width:calc(100vw - 32px);flex-wrap:wrap}.tak-route-hud-i654{right:9px;bottom:64px;width:170px;max-height:calc(100vh - 155px)}}
  `;if(!el(ID))D.head.appendChild(style);
  const selector=D.createElement('div');selector.className='tak-route-selector-i654';selector.id='takRouteSelectorI654';
  selector.innerHTML='<button data-mode="manual" type="button">Manual</button><button data-mode="roads" type="button" class="active" title="Use mapped roads and tracks">Roads</button><span id="takRouteNetworkStateI655" role="status">Preparing road network…</span>';
  const hud=D.createElement('div');hud.id='takRouteHudI654';hud.className='tak-route-hud-i654';hud.hidden=true;
  // Place controls above the map in the viewport, clear of the zoom badge and floating toolbar.
  // An HTML element with id=map may exist as window.map before Leaflet initialization.
  if(!el('takRouteSelectorI654'))D.body.appendChild(selector);
  if(!el('takRouteHudI654'))D.body.appendChild(hud);
  selector.addEventListener('click',ev=>{const mode=ev.target.closest('button')?.dataset.mode;if(!mode)return;
    // Selected mode controls NEW waypoints/legs; previously resolved route legs remain as saved.
    S.mode=mode;selector.querySelectorAll('button').forEach(b=>b.classList.toggle('active',b.dataset.mode===mode));
    dropSnap();setWarning('');visibility();
  });
}
async function routerHealth(force=false){
  if(!force&&Date.now()-S.lastRouterCheck<4000)return;
  S.lastRouterCheck=Date.now();
  try{
    const response=await fetch('/api/tak-map/ndm/status',{credentials:'same-origin',cache:'no-store'});
    if(!response.ok)throw Error('Routing status request failed');
    const data=await response.json();
    S.routerReady=!!data.routing_enabled;
    S.routerState=S.routerReady?'ready':(data.router_state==='starting'?'preparing':'unavailable');
  }catch(_){S.routerReady=false;S.routerState='unavailable'}
  const label=el('takRouteNetworkStateI655');
  if(label){label.textContent=S.routerReady?'Road network ready':S.routerState==='preparing'?'Preparing road network…':'Road routing unavailable';
    label.style.color=S.routerReady?'#7ddab0':'#f6c778'}
}
function savedImports(){
  try{if(typeof lastImports!=='undefined'&&Array.isArray(lastImports))return lastImports}catch(_){}
  return Array.isArray(W.lastImports)?W.lastImports:[];
}
// i666: Saved routes show a single endpoint callout; editing still shows leg distances.
function savedTotalLabel(feature){
  if(!W.map||W.map.getZoom()<11)return;
  if(S.editing&&String(S.editing.objectId)===String(feature.object_id||feature.local_id||''))return;
  if(feature.__layer&&typeof W.map.hasLayer==='function'&&!W.map.hasLayer(feature.__layer))return;
  const shape=(feature.coords||[]).filter(c=>Array.isArray(c)&&c.length>=2).map(c=>W.L.latLng(Number(c[0]),Number(c[1])));
  if(shape.length<2||shape.some(p=>!Number.isFinite(p.lat)||!Number.isFinite(p.lng)))return;
  const total=pathDistance(shape);if(!Number.isFinite(total)||total<=0)return;
  const endpoint=shape.at(-1),last=shape.at(-2);
  const ep=W.map.latLngToContainerPoint(endpoint),prev=W.map.latLngToContainerPoint(last);
  // Never clamp a far-away endpoint into a viewport corner. The callout belongs
  // to the saved route endpoint and is shown only while that endpoint is visible.
  const visibleSize=W.map.getSize();
  if(!Number.isFinite(ep.x)||!Number.isFinite(ep.y)||
      ep.x<0||ep.y<0||ep.x>visibleSize.x||ep.y>visibleSize.y)return;
  let dx=ep.x-prev.x,dy=ep.y-prev.y,mag=Math.hypot(dx,dy);
  if(mag<.001){dx=1;dy=0;mag=1}
  const normX=-dy/mag,normY=dx/mag;
  const name=String(feature.name||feature.properties?.name||'Route').trim().slice(0,100)||'Route';
  const width=Math.min(210,Math.max(82,Math.ceil(name.length*6.4+20),92));
  const height=42,viewport=W.map.getSize(),pad=8;
  const distFromEndpoint=65;
  const candidates=[1,-1].map(sign=>{
    let x=ep.x+normX*distFromEndpoint*sign,y=ep.y+normY*distFromEndpoint*sign;
    const originalX=x,originalY=y;
    x=Math.max(pad+width/2,Math.min(viewport.x-pad-width/2,x));
    y=Math.max(pad+height/2,Math.min(viewport.y-pad-height/2,y));
    return {x,y,score:Math.hypot(x-originalX,y-originalY)*4+
      ((((x-ep.x)*normX+(y-ep.y)*normY)*sign)<16?100:0)};
  });
  // Prefer a nearby point on the normal, with enough distance not to cover trail.
  candidates.sort((a,b)=>a.score-b.score);
  const c=candidates[0];
  const dirX=ep.x-c.x,dirY=ep.y-c.y;
  const edgeScale=Math.min(width/2/Math.max(.01,Math.abs(dirX)),height/2/Math.max(.01,Math.abs(dirY)));
  const endPoint=W.L.point(c.x+dirX*edgeScale,c.y+dirY*edgeScale);
  const ll=W.map.containerPointToLatLng(W.L.point(c.x,c.y));
  const html='<span class="tak-route-total-chip-i666"><strong>'+escapeHtml(name)+'</strong><span>'+escapeHtml(milesText(total))+'</span></span>';
  const leader=W.L.polyline([endpoint,W.map.containerPointToLatLng(endPoint)],{
    color:'#b4bdc6',weight:1.2,opacity:.85,interactive:false,lineCap:'round'}).addTo(W.map);
  const label=W.L.marker(ll,{interactive:false,keyboard:false,zIndexOffset:420,
    icon:W.L.divIcon({className:'tak-route-saved-total-i666',html,iconSize:[width,height],iconAnchor:[width/2,height/2]})}).addTo(W.map);
  S.savedLabels.push(leader,label);
}
function refreshSavedDistanceLabels(){
  S.savedLabels.forEach(layerRemove);S.savedLabels=[];
  if(!W.map||W.map.getZoom()<11)return;
  try{if(typeof state!=='undefined'&&state.imported===false)return}catch(_){ }
  for(const file of savedImports())for(const feature of (file.features||[])){
    if(feature.kind==='route')savedTotalLabel(feature);
  }
}
// Reopen saved routes with control points, not hundreds of Valhalla geometry vertices.
function savedPointAt(shape,ratio){
  const total=pathDistance(shape);if(total<=0)return shape[0];const target=total*ratio;
  let used=0;for(let i=1;i<shape.length;i++){const d=distance(shape[i-1],shape[i]);
    if(used+d>=target){const t=d?(target-used)/d:0;
      return W.L.latLng(shape[i-1].lat+(shape[i].lat-shape[i-1].lat)*t,
        shape[i-1].lng+(shape[i].lng-shape[i-1].lng)*t)}used+=d}
  return shape.at(-1);
}
function savedRouteControls(feature){
  const p=feature.properties||{},shape=(feature.coords||[]).filter(x=>Array.isArray(x)&&x.length>=2)
    .map(c=>W.L.latLng(Number(c[0]),Number(c[1])));
  if(shape.length<2||shape.some(p=>!Number.isFinite(p.lat)||!Number.isFinite(p.lng)))throw Error('Saved geometry is invalid');
  let count=Math.min(300,Math.max(2,Number(p.route_control_point_count)||2));
  const exact=Array.from({length:count},(_,i)=>{
    const row=String(p['route_cp_'+i]||'').split(','),lat=Number(row[0]),lon=Number(row[1]);
    return row.length>=3&&Number.isFinite(lat)&&Number.isFinite(lon)&&Math.abs(lat)<=90&&Math.abs(lon)<=180
      ?{point:W.L.latLng(lat,lon),mode:row[2]==='manual'?'manual':'roads'}:null;
  });
  const preserved=exact.every(Boolean);if(!preserved)count=Math.min(count,shape.length);
  const controls=preserved?exact.map(x=>x.point):Array.from({length:count},(_,i)=>savedPointAt(shape,i/(count-1)));
  const pointModes=preserved?exact.map(x=>x.mode):Array(count).fill('roads');
  const rawModes=String(p.route_segment_modes||'').split(',');
  const segmentModes=Array.from({length:count-1},(_,i)=>rawModes[i]==='manual'?'manual':'roads');
  const ends=Array.from({length:count-1},(_,i)=>Number(p['route_leg_end_'+i]));
  const boundaries=preserved&&ends.every((n,i)=>Number.isInteger(n)&&n>=(i?ends[i-1]+1:1)&&n<shape.length)&&ends.at(-1)===shape.length-1
    ?ends:Array.from({length:count-1},(_,i)=>{
      const wanted=(i+1)/(count-1),target=pathDistance(shape)*wanted;let d=0;
      for(let j=1;j<shape.length;j++){d+=distance(shape[j-1],shape[j]);if(d>=target)return j}return shape.length-1;
    });
  const fallbackIndices=new Set(String(p.route_fallback_leg_indices||'').split(',').filter(x=>/^\d+$/.test(x)).map(Number));
  let start=0;const legs=boundaries.map((end,i)=>{
    end=Math.max(start+1,Math.min(shape.length-1,end));
    const path=shape.slice(start,end+1);start=end;
    return {status:fallbackIndices.has(i)?'error':'ready',fallback:fallbackIndices.has(i),mode:segmentModes[i],shape:path,
      signature:lineSignature(controls[i],controls[i+1],segmentModes[i],i)};
  });
  return {controls,pointModes,segmentModes,legs,preserved};
}
function startEditingSavedRoute(feature,file){
  if(S.saveBusy)return false;
  if(normalizedPoints().length>0&&!W.confirm('Discard the current unsaved route and edit this saved route?'))return false;
  if(S.editing&&!W.confirm('Discard the current unsaved edits?'))return false;
  try{
    const parsed=savedRouteControls(feature),id=String(feature.object_id||feature.local_id||'');
    const importId=String(file.id||feature.import_id||'');
    if(!id||!importId||!feature.route_revision_i659)throw Error('Route identity is unavailable; refresh the saved routes.');
    try{W.map.closePopup()}catch(_){}
    if(typeof W.v233ClearRoute==='function')W.v233ClearRoute();
    if(typeof W.setActiveMapTool==='function')W.setActiveMapTool('route');
    const state=st();state.points=parsed.controls;S.pointModes=parsed.pointModes;
    S.segmentModes=parsed.segmentModes;S.legs=parsed.legs;
    S.editing={importId,objectId:id,revision:String(feature.route_revision_i659),name:feature.name};
    S.saveAsNew=false;S.mode='roads';
    state.name=feature.name||'';state.notes=String(feature.properties?.notes||'');
    state.category=String(feature.properties?.category||'General');
    state.color=String(feature.properties?.color||'#ff6f2e');
    for(const [dom,value] of [['routeNameInput',state.name],['routeNotesInput',state.notes],['routeColorInput',state.color]]){
      if(el(dom))el(dom).value=value;
    }
    if(el('takRouteSelectorI654'))el('takRouteSelectorI654').querySelectorAll('button[data-mode]')
      .forEach(b=>b.classList.toggle('active',b.dataset.mode==='roads'));
    visibility();renderLine();refreshSavedDistanceLabels();
    if(!parsed.preserved)message('Legacy route: control waypoint positions reconstructed from its saved geometry.');
    return true;
  }catch(err){message('Could not edit saved route: '+String(err.message||err));return false}
}
function removeStrandedEditLayersI684(){
  // Clear only draft markers; do not disturb saved-route labels or route layers.
  const saved=new Set(S.savedLabels);
  try{W.map?.eachLayer?.(layer=>{
    if(saved.has(layer))return;
    const cls=String(layer?.options?.icon?.options?.className||'');
    if(/tak-route-point-i654|tak-route-failure-i654/.test(cls)||
       (cls.includes('tak-route-distance-icon-i658')&&!saved.has(layer)))layerRemove(layer);
  })}catch(error){console.warn('[TAK Map] route edit cleanup',error)}
}
function cancelSavedEdit(){
  if(!S.editing&&!S.markers.length&&!S.labels.length)return;
  // Invalidate pending snaps/roads BEFORE touching the current draft state.
  S.editEpoch++;S.dirty++;dropSnap();
  S.editing=null;S.saveAsNew=false;S.operationBusy=false;
  if(typeof W.v233ClearRoute==='function')W.v233ClearRoute();
  else{const state=st();if(state)state.points=[];S.legs=[];clearLayers()}
  clearLayers();removeStrandedEditLayersI684();hideMenu();
  if(typeof W.setActiveMapTool==='function')W.setActiveMapTool('move');
  visibility();refreshSavedDistanceLabels();
  try{W.dispatchEvent(new CustomEvent('tak-map-route-edit-canceled-i684'))}catch(_){}
}
function attachSavedRouteEditButtons(){
  for(const file of savedImports())for(const feature of (file.features||[])){
    if(feature.kind!=='route'||!feature.import_id&&!file.id||file.id==='webform-live')continue;
    for(const layer of [feature.__layer,feature.__hitLayer]){
      if(!layer||layer.__takRouteEditI659)continue;layer.__takRouteEditI659=true;
      layer.on('popupopen',()=>{
        const root=layer.getPopup?.()?.getElement?.();
        if(!root||root.querySelector('[data-tak-edit-route-i659]'))return;
        const host=root.querySelector('.feature-popup');if(!host)return;
        const btn=D.createElement('button');btn.type='button';btn.dataset.takEditRouteI659='1';
        btn.textContent='Edit Route';btn.className='tak-route-saved-edit-i659';
        btn.addEventListener('click',ev=>{ev.preventDefault();ev.stopPropagation();startEditingSavedRoute(feature,file)});
        host.appendChild(btn);
      });
    }
  }
}
function watchImportedRoutes(){
  if(typeof W.drawImportedObjects==='function'&&!W.drawImportedObjects.__takRouteLabelsI658){
    const prior=W.drawImportedObjects;
    const wrapped=function(){const result=prior.apply(this,arguments);setTimeout(()=>{refreshSavedDistanceLabels();attachSavedRouteEditButtons()},0);return result};
    wrapped.__takRouteLabelsI658=true;W.drawImportedObjects=wrapped;
    try{drawImportedObjects=wrapped}catch(_){}
  }
  refreshSavedDistanceLabels();attachSavedRouteEditButtons();
  if(W.map&&!S.savedLabelEventsI666){
    S.savedLabelEventsI666=true;
    W.map.on('moveend zoomend resize',()=>{clearTimeout(S.labelRefreshTimerI666);S.labelRefreshTimerI666=setTimeout(refreshSavedDistanceLabels,80)});
  }
}
function placeRouteMode(){
  const selector=el('takRouteSelectorI654'),mapNode=W.map?.getContainer?.()||el('map');
  if(!selector||!mapNode)return;
  const box=mapNode.getBoundingClientRect();
  // The header overlays the page. Keep Manual / Roads INSIDE the map,
  // safely below the header, map zoom buttons and top status banners.
  const width=selector.getBoundingClientRect().width||270;
  selector.style.left=Math.max(box.left+8,Math.min(box.right-width-8,box.left+(box.width>750?54:8)))+'px';
  selector.style.top=Math.max(box.top+45,Math.min(box.bottom-55,box.top+56))+'px';
}
function visibility(){if(S.installed&&(!el('takRouteSelectorI654')||!el('takRouteHudI654')))ensureUi();
  const on=active(),selector=el('takRouteSelectorI654'),hud=el('takRouteHudI654');
  if(on&&!S.wasActive&&normalizedPoints().length===0&&!S.editing){
    S.mode='roads';
    if(selector)selector.querySelectorAll('button[data-mode]').forEach(b=>b.classList.toggle('active',b.dataset.mode==='roads'));
  }
  S.wasActive=on;
  if(D.body.classList.contains('tak-route-roads-i654')!==(on&&S.mode==='roads'))
    D.body.classList.toggle('tak-route-roads-i654',on&&S.mode==='roads');
  if(selector){selector.hidden=!on;selector.style.display=on?'flex':'none';if(on)placeRouteMode()}
  if(hud)hud.hidden=!on;if(!on){hideMenu();dropSnap();if(S.markers.length||S.labels.length)clearLayers()}else if(S.mode==='roads')routerHealth()}
function install(){
  if(S.installed)return true;
  if(!W.map||typeof W.map.getContainer!=='function'||typeof W.map.latLngToContainerPoint!=='function'||
     !W.v233RouteState||!W.v234RedrawRoute||!W.v233RouteMapClick||!W.v233FinishRoute)return false;
  ensureUi();
  W.v233RouteMapClick=function(ll){if(Date.now()<S.suppressClickUntil)return;return addWaypoint(ll)};
  W.v234RedrawRoute=renderLine;
  W.v233UndoRoute=function(){if(S.operationBusy)return;if(S.undoTransaction&&S.undoTransaction.dirty===S.dirty){const snapshot=S.undoTransaction.snapshot;S.undoTransaction=null;S.dirty++;restoreSnapshot(snapshot);return}const s=st();if(!s?.points.length)return;s.points.pop();S.pointModes.pop();S.segmentModes.pop();dropSnap();setWarning('');recompute()};
  W.v233ClearRoute=function(){const s=st();S.editEpoch++;S.dirty++;S.suppressClickUntil=0;S.undoTransaction=null;if(s)s.points=[];S.pointModes=[];S.segmentModes=[];S.legs=[];clearLayers();hideMenu();dropSnap();setWarning('');drawHud();try{W.dispatchEvent(new Event('tak-map-route-geometry-i681'))}catch(_){} };
  S.fullShape=fullShape;
  S.getResolvedSaveState=resolvedSaveState;
  S.saveResolvedRoute=saveResolvedRoute;
  S.startEditingSavedRoute=startEditingSavedRoute;
  S.cancelSavedEdit=cancelSavedEdit;
  S.insertWaypoint=insertWaypoint;S.moveWaypoint=moveWaypoint;S.deleteWaypoint=deleteWaypoint;
  S.reverseRoute=reverseRoute;S.backToStart=backToStart;
  // The existing Save Route modal owns Finish. Its Save button delegates back
  // to this resolved-geometry API, rather than the old control-point uploader.
  W.v233FinishRoute=typeof W.TakMapRouteUiV500?.open==='function'
    ? W.TakMapRouteUiV500.open : saveResolvedRoute;
  const previousSwitch=W.setActiveMapTool;
  if(typeof previousSwitch==='function')W.setActiveMapTool=function(){const out=previousSwitch.apply(this,arguments);setTimeout(visibility,0);return out};
  const previousToggle=W.toggleMapTool;
  if(typeof previousToggle==='function')W.toggleMapTool=function(){const out=previousToggle.apply(this,arguments);setTimeout(visibility,0);return out};
  const hud=el('takRouteHudI654');if(hud)hud.addEventListener('click',async event=>{
    const action=event.target.closest('button[data-route-edit-action]')?.dataset.routeEditAction;
    if(!action)return;event.preventDefault();event.stopPropagation();
    if(action==='reverse'){await reverseRoute();return}
    if(action==='return'){await backToStart();return}
    if(!S.editing||S.operationBusy)return;
    if(action==='cancel'){cancelSavedEdit();return}
    if(action==='save'){S.saveAsNew=false;await saveResolvedRoute({name:st()?.name||S.editing.name,
      color:st()?.color||currentLineColor(),notes:st()?.notes||'',category:st()?.category||'General'});return}
    if(action==='copy'){S.saveAsNew=true;
      if(typeof W.TakMapRouteUiV500?.open==='function')W.TakMapRouteUiV500.open();
      else message('Save Route dialog is unavailable.');}
  });
  W.map.on('mousemove',ev=>schedulePreview(ev.latlng));
  W.map.on('click',()=>{if(S.menu)hideMenu()});
  D.addEventListener('pointerdown',ev=>{if(S.menu&&!S.menu.contains(ev.target)&&!ev.target.closest('.tak-route-point-i654'))hideMenu()},true);
  W.map.on('zoomend',()=>{dropSnap();drawHud()});
  W.addEventListener('resize',placeRouteMode);
  if(typeof ResizeObserver!=='undefined'){try{new ResizeObserver(placeRouteMode).observe(W.map.getContainer())}catch(_){}}
  D.addEventListener('keydown',ev=>{if(ev.key==='Escape')hideMenu()});
  if(typeof MutationObserver!=='undefined'){
    const obs=new MutationObserver(visibility);obs.observe(D.body,{attributes:true,subtree:false,attributeFilter:['class']});
  }
  W.map.on('click',()=>setTimeout(visibility,0));
  setInterval(()=>{visibility();if(active()&&S.mode==='roads')routerHealth()},2000);
  routerHealth(true);watchImportedRoutes();
  visibility();if(normalizedPoints().length>1)recompute();else renderLine();S.installed=true;return true;
}
function boot(){if(install())return;let count=0;const retry=setInterval(()=>{if(install()||++count>150)clearInterval(retry)},200)}
if(D.readyState==='loading')D.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
