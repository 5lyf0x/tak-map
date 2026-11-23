/* TAK Map v1.4.0-i689 — Infrastructure selection, verified map startup and themed minimum zoom. */
(function(W,D){'use strict';
const ID='takInfraCardI685', API='/api/tak-map/infrastructure/', FEATURE_CAP=5000;
const $=id=>D.getElementById(id),str=v=>v==null?'':String(v);
const esc=s=>str(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const saved=(key,f)=>{try{return JSON.parse(localStorage.getItem(key))??f}catch(_){return f}};
const S={data:null,open:new Set(saved('takmap.infra.open.i686',['water'])),collapsed:localStorage.getItem('takmap.infra.collapsed.i685')==='1',visible:localStorage.getItem('takmap.infra.visible.i694')!=='0',min:Number(localStorage.getItem('takmap.infra.min.i685')||36),map:null,viewer:null,ready:false,records:new Map(),selected:null,selection:null,drawBounds:null,drawFirst:null,drawLayer:null,errors:{},lastRender:0,searchResults:[],searchQuery:'',searchEpoch:0,loadEpoch:0,cardRevision:0};
if(!Number.isFinite(S.min))S.min=36;
const api=async(path,opts)=>{const r=await fetch(API+path,{credentials:'same-origin',cache:'no-store',...opts});const j=await r.json().catch(()=>({ok:false,error:'Invalid response'}));if(!r.ok||!j.ok)throw Error(j.error||'Infrastructure HTTP '+r.status);return j};
const post=(path,body)=>api(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
const state=()=>S.data||{categories:[],layers:[],jobs:[]},category=id=>state().categories.find(x=>x.id===id)||null,layerById=id=>state().layers.find(x=>x.id===id)||null;
const visibleCategory=cat=>!!cat&&!cat.hidden_offline;
// The page contains a #map DOM element: window.map can briefly resolve to that DIV.
// Never cache it or bind events until it is a genuine Leaflet-style map object.
const validMap=m=>!!m&&typeof m.on==='function'&&typeof m.off==='function'&&typeof m.addLayer==='function'&&typeof m.removeLayer==='function'&&typeof m.getBounds==='function'&&typeof m.getZoom==='function';
const getMap=()=>{let lexical=null;try{if(typeof map!=='undefined')lexical=map}catch(_){}
 for(const candidate of [lexical,W.takLeafletMap,W.map])if(validMap(candidate))return candidate;return null};
const viewer=()=>{try{if(typeof terrain3DViewer!=='undefined'&&terrain3DViewer?.entities)return terrain3DViewer}catch(_){}return W.terrain3DViewer||null};
function routeBusy(){try{return typeof activeMapTool!=='undefined'&&!['move','select',''].includes(str(activeMapTool||'move'))}catch(_){return false}}
function message(text,bad=false){const el=$('takInfraMessageI685');if(el){el.textContent=str(text);el.classList.toggle('error',!!bad)}}
function effectiveZoom(){const m=getMap();if(!m)return 0;let z=Number(m.getZoom?.());const v=viewer(),C=W.Cesium;
 if(v&&C&&v.scene?.mode===C.SceneMode.SCENE3D&&v.camera?.positionCartographic?.height>0){const h=v.camera.positionCartographic.height,hh=v.canvas?.clientHeight||800,fov=v.camera.frustum?.fovy||Math.PI/3,lat=m.getCenter?.()?.lat||0;const guess=Math.log2((156543.0339*Math.max(.01,Math.cos(lat*Math.PI/180)))/(2*h*Math.tan(fov/2)/hh));if(Number.isFinite(guess))z=guess}return Number.isFinite(z)?z:0}
const eligible=src=>S.visible&&src.mode==='offline'&&!!src.enabled&&!src.hidden&&visibleCategory(category(src.category_id))&&(src.min_zoom==null||effectiveZoom()>=Number(src.min_zoom));
const selectedLayers=()=>state().layers.filter(eligible);
const defaultColor=kind=>({sewer:'#66bdd0',line:'#eec477',point:'#b1a2f1',other:'#97cdd0'})[kind]||'#97cdd0';
const colorFor=src=>/^#[a-f\d]{6}$/i.test(src?.color||'')?src.color:defaultColor(src?.kind);
function nameFor(f,src){const p=f.properties||{};return str(p.NAME||p.name||p.FACILITY_NAME||p.PRESET_NAME||p.PIPE_LOCN||p.STRUCTURE_ID||p.STATION_NAME||p.PIPE_ID||f.id||src.name||'Infrastructure object')}
function diameter(p){const keys=new Set(['PIPE_DIAMETER','DIAMETER','DIAM','PIPE_DIA','DIAMETER_IN','DIAMETER_MM','DIAMETER_CM','DIAMETER_FT','DIA_IN','NOMINAL_DIAMETER']);for(const [k,v] of Object.entries(p||{})){const key=k.toUpperCase().replace(/ /g,'_');if(!keys.has(key)||v==null)continue;const mt=str(v).match(/\d+(?:\.\d+)?/);if(!mt)continue;let n=Number(mt[0]),unit=key.endsWith('_MM')?'mm':key.endsWith('_CM')?'cm':key.endsWith('_FT')?'ft':/\bmm\b/i.test(str(v))?'mm':/\bcm\b/i.test(str(v))?'cm':/\bft\b/i.test(str(v))?'ft':'in';n*=({mm:1/25.4,cm:1/2.54,ft:12,in:1})[unit];if(n>0&&n<1500)return Math.round(n*10)/10}return null}
function info(feature,src){const p=feature.properties||{},rows=[],add=(label,keys)=>{const key=keys.find(k=>p[k]!=null&&p[k]!=='');if(key)rows.push([label,p[key]])};
 if(src.kind==='sewer'){const d=diameter(p);if(d!=null)rows.push(['Diameter',d+' in'])}
 add('Structure Type',['MH_DESCRIPTION','MH_TYPE']);add('Type',['TYPE','type','FACILITY_TYPE','STRUCTURE_TYPE']);add('Material',['PIPE_MATERIAL','MATERIAL','material']);add('Voltage',['VOLTAGE','VOLTAGE_KV']);add('Operator',['OPERATOR','OWNER','OWNER_NAME']);add('Length',['PLAN_LENGTH','LENGTH_FT','SPAN_LENGTH']);add('Status',['STATUS','status']);
 const cell=(a,b)=>`<div class="kvp"><b>${esc(a)}</b><span>${esc(b)}</span></div>`;
 const pretty=v=>v===null?'null':typeof v==='object'?JSON.stringify(v):String(v);
 const raw=Object.entries(p).map(([k,v])=>cell(k,pretty(v))).join('')||cell('Attributes','No GIS attributes supplied');
 return `<div class="tak-infra-properties-i685">${cell('Category',category(src.category_id)?.label||src.category_id)}${cell('Layer',src.name)}${rows.map(([k,v])=>cell(k,pretty(v))).join('')}${cell('Source',src.metadata?.original_file||src.metadata?.provider||'Offline GIS import')}<section class="infra-raw-attrs" aria-label="GIS Attributes"><h3>GIS ATTRIBUTES (${Object.keys(p).length})</h3>${raw}</section><div class="infra-detail-actions" role="group" aria-label="Infrastructure object actions"><button type="button" data-infra-action="zoom">Zoom to Object</button><button type="button" data-infra-action="coords">Copy Coordinates</button><button type="button" data-infra-action="export">Export Object</button></div></div>`}
function clearSelection(){if(S.selection){const x=S.selection;try{if(x.stroke&&x.group)x.group.removeLayer(x.stroke)}catch(_){}try{if(x.entity&&x.viewer)x.viewer.entities.remove(x.entity)}catch(_){}try{if(x.pinned&&x.pinnedMap)x.pinnedMap.removeLayer(x.pinned)}catch(_){} }S.selection=null;S.selected=null;S.contextSignature=null}
function redOutline(f,src,shape){const C=W.Cesium,m=getMap();const col=colorFor(src);
 if(shape?.setStyle&&shape.getLatLngs&&W.L&&m){const weight=Number(shape.options?.weight||3)+4;const group=shape._infraParent||m;const stroke=W.L.polyline(shape.getLatLngs(),{color:'#e43b42',weight,opacity:.98,interactive:false,lineCap:'round',lineJoin:'round'}).addTo(group);stroke.bringToBack?.();shape.bringToFront?.();S.selection={stroke,group};return}
 if(shape?.polyline&&C){const v=viewer();try{const red=v.entities.add({polyline:{positions:shape.polyline.positions,width:7,material:C.Color.RED,clampToGround:true}});S.selection={entity:red,viewer:v};return}catch(_){}}
 if(m&&W.L){const pin=W.L.layerGroup().addTo(m);W.L.geoJSON(f,{style:()=>({color:'#e43b42',weight:7,interactive:false}),pointToLayer:(feat,ll)=>W.L.circleMarker(ll,{radius:10,color:'#e43b42',fillOpacity:0,weight:2,interactive:false})}).addTo(pin);W.L.geoJSON(f,{style:()=>({color:col,weight:3,interactive:false}),pointToLayer:(feat,ll)=>W.L.circleMarker(ll,{radius:6,color:col,fillColor:col,fillOpacity:.8,weight:2,interactive:false})}).addTo(pin);S.selection={pinned:pin,pinnedMap:m}}
}
function selectFeature(feature,src,shape){if(routeBusy())return;clearSelection();S.selected={feature,src};redOutline(feature,src,shape);const pane=W.TakMapContextSidebarI572;
 const object={uid:'infra:'+src.id+':'+str(feature._infraSelectionKey||feature.id||'point'),name:nameFor(feature,src),category:'infrastructure'};
 S.contextSignature=object.uid+'|'+JSON.stringify(feature.properties||{});if(pane?.showReadOnly)pane.showReadOnly({object,layer:shape||null,key:object.uid,kicker:'INFRASTRUCTURE · '+(category(src.category_id)?.label||''),title:object.name,html:info(feature,src),signature:S.contextSignature});else message('Selected '+object.name+'; Object Details unavailable',true)}
D.addEventListener('click',ev=>{const b=ev.target?.closest?.('[data-infra-action]');if(!b||!S.selected)return;ev.stopPropagation();const {feature,src}=S.selected;const action=b.dataset.infraAction;if(action==='export'){const data=new Blob([JSON.stringify({type:'FeatureCollection',features:[feature]})],{type:'application/geo+json'});const u=URL.createObjectURL(data),a=D.createElement('a');a.href=u;a.download='infrastructure-'+str(feature.id||src.id).replace(/[^\w-]/g,'_').slice(0,60)+'.geojson';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000)}else if(action==='zoom'){zoomTo(feature,src)}else if(action==='coords'){const p=firstPoint(feature.geometry?.coordinates);if(p)navigator.clipboard?.writeText?.(Number(p[1]).toFixed(6)+', '+Number(p[0]).toFixed(6))}},true);
function firstPoint(coords){if(!Array.isArray(coords))return null;if(coords.length>=2&&typeof coords[0]==='number'&&typeof coords[1]==='number')return coords;for(const part of coords){const p=firstPoint(part);if(p)return p}return null}
function zoomTo(feature,src){const m=getMap(),L=W.L;if(!m||!L)return;try{const layer=L.geoJSON(feature),b=layer.getBounds(),z=Math.max(Number(src?.min_zoom||0),m.getZoom());if(b.isValid()&&b.getNorthEast().distanceTo(b.getSouthWest())>5){m.fitBounds(b.pad(.2),{maxZoom:Math.max(z,16)});if(m.getZoom()<z)m.setZoom?.(z)}else{const p=firstPoint(feature.geometry?.coordinates);if(p)m.setView([p[1],p[0]],Math.max(z,15))}}catch(_){}}
function boxParts(bounds,scale=1){let [w,s,e,n]=bounds.map(Number);if(e<w)e+=360;const width=Math.min(e-w,360),height=Math.min(n-s,180),cx=w+width/2,cy=(s+n)/2;let a=cx-width*scale/2,b=cx+width*scale/2;const lo=Math.max(-90,cy-height*scale/2),hi=Math.min(90,cy+height*scale/2);if(b-a>=360)return[[-180,lo,180,hi]];while(a>180){a-=360;b-=360}while(a<-180){a+=360;b+=360}return b<=180?[[a,lo,b,hi]]:[[a,lo,180,hi],[-180,lo,b-360,hi]]}
function viewBox(){const b=getMap()?.getBounds?.();return b?[b.getWest(),b.getSouth(),b.getEast(),b.getNorth()]:null}
function inside(box,p){return p[0]>=box[0]&&p[0]<=box[2]&&p[1]>=box[1]&&p[1]<=box[3]}
function geometryVisible(f,boxes){const xs=[],ys=[];let isInside=false;function visit(node){if(!Array.isArray(node))return;if(node.length>=2&&typeof node[0]==='number'&&typeof node[1]==='number'){xs.push(node[0]);ys.push(node[1]);if(boxes.some(b=>inside(b,node)))isInside=true;return}for(const item of node)visit(item)}visit(f.geometry?.coordinates);if(isInside)return true;if(!xs.length)return false;const mi=Math.min(...xs),ma=Math.max(...xs),ni=Math.min(...ys),na=Math.max(...ys);return boxes.some(b=>mi<=b[2]&&ma>=b[0]&&ni<=b[3]&&na>=b[1])}
function withinCache(c,parts){return c&&parts.every(b=>c.some(q=>b[0]>=q[0]-1e-8&&b[2]<=q[2]+1e-8&&b[1]>=q[1]-1e-8&&b[3]<=q[3]+1e-8))}
function iconImage(src){if(src.point_symbol_mode!=='registry'||!src.point_symbol_ref)return null;try{const reg=W.TakMapIconRegistryI572||W.TakMapIconRegistryI556;const url=reg?.imageFor?.(src.point_symbol_ref);return url&&/^(?:\/|data:image\/|blob:)/.test(url)?url:null}catch(_){return null}}
function draw2d(features,src,group){const L=W.L;if(!L?.geoJSON)return;const col=colorFor(src),symbol=iconImage(src),lineWeight=src.kind==='sewer'?3:2;
 group._infraShapes=new Map();const visible=L.geoJSON({type:'FeatureCollection',features:features.filter(f=>!!f.geometry)}, {style:()=>({color:col,weight:lineWeight,opacity:.9,fillOpacity:.2}),pointToLayer:(f,ll)=>symbol?L.marker(ll,{icon:L.divIcon?L.divIcon({html:`<span class="infra-symbol-fallback-i689" style="--infra-dot:${esc(col)}"><img loading="lazy" decoding="async" src="${esc(symbol)}" alt="" onerror="this.hidden=true;this.parentNode.classList.add('infra-icon-failed-i689')"></span>`,iconSize:[28,28],iconAnchor:[14,14],className:'infra-registry-icon-i688'}):L.icon({iconUrl:symbol,iconSize:[28,28],iconAnchor:[14,14],className:'infra-registry-icon-i688'})}):L.circleMarker(ll,{radius:6,color:col,weight:2,fillColor:col,fillOpacity:.82}),onEachFeature:(f,shape)=>{
 shape._infraParent=group;
 // Provider IDs are not necessarily unique. Distinguish repeated IDs within one layer.
 const id=str(f.id);const nth=group._infraIdCounts?.get(id)||0;
 if(!group._infraIdCounts)group._infraIdCounts=new Map();group._infraIdCounts.set(id,nth+1);
 f._infraSelectionKey=src.id+':'+id+':'+nth;
 group._infraShapes.set(f._infraSelectionKey,shape);
 const pick=ev=>{if(routeBusy())return;const oe=ev?.originalEvent;
  if(oe){try{oe._infraHandled=true}catch(_){}try{L.DomEvent.stopPropagation(oe)}catch(_){}}
  selectFeature(f,src,shape)};
 shape.on('click',pick);
 if(shape instanceof L.Polyline&&!(shape instanceof L.Polygon)){
  // Transparent hit stroke adds 5px on *each side*, without changing visible geometry.
  const hit=L.polyline(shape.getLatLngs(),{color:'#ffffff',opacity:0.005,weight:lineWeight+10,interactive:true,renderer:shape.options.renderer||undefined,className:'infra-line-hit-i688'}).addTo(group);
  hit.on('click',pick);(group._infraHits||(group._infraHits=[])).push(hit);
 }
 }});visible.addTo(group);
 // Invisible line hit strokes must sit BELOW visible geometry, never cover icons/points.
 for(const hit of group._infraHits||[])try{hit.bringToBack?.()}catch(_){}
}
function draw3d(features,src,record){const v=viewer(),C=W.Cesium;if(!v?.entities||!C||v.scene?.mode!==C.SceneMode.SCENE3D)return;const col=C.Color.fromCssColorString(colorFor(src)),sym=iconImage(src);
 const add=(f,opts)=>{try{const entity=v.entities.add({...opts,properties:{infraSource:src.id,infraFeature:JSON.stringify(f)}});record.entities.push({viewer:v,entity})}catch(_){}};
 for(const f of features){const g=f.geometry||{},coords=g.coordinates;if(!coords)continue;
 const point=p=>add(f,{position:C.Cartesian3.fromDegrees(p[0],p[1]),point:{pixelSize:sym?6:9,color:col,outlineColor:C.Color.BLACK,outlineWidth:1,heightReference:C.HeightReference.CLAMP_TO_GROUND},...(sym?{billboard:{image:sym,width:28,height:28,heightReference:C.HeightReference.CLAMP_TO_GROUND}}:{})});
 const line=p=>{if(!p?.length)return;const pos=C.Cartesian3.fromDegreesArray(p.flatMap(q=>q.slice(0,2)));add(f,{polyline:{positions:pos,width:3,material:col,clampToGround:true}});add(f,{polyline:{positions:pos,width:13,material:C.Color.WHITE.withAlpha(.005),clampToGround:true}})};
 if(g.type==='Point')point(coords);else if(g.type==='MultiPoint')coords.forEach(point);else if(g.type==='LineString')line(coords);else if(g.type==='MultiLineString')coords.forEach(line);
 else if(g.type==='Polygon'&&coords[0]?.length)add(f,{polygon:{hierarchy:C.Cartesian3.fromDegreesArray(coords[0].flatMap(p=>p.slice(0,2))),material:col.withAlpha(.25),outline:true,outlineColor:col,heightReference:C.HeightReference.CLAMP_TO_GROUND}});
 else if(g.type==='MultiPolygon')for(const poly of coords)if(poly[0]?.length)add(f,{polygon:{hierarchy:C.Cartesian3.fromDegreesArray(poly[0].flatMap(p=>p.slice(0,2))),material:col.withAlpha(.25),outline:true,outlineColor:col,heightReference:C.HeightReference.CLAMP_TO_GROUND}})
 }
}
function removeGraphics(rec){try{if(rec.group)getMap()?.removeLayer(rec.group)}catch(_){}for(const e of rec.entities||[])try{e.viewer.entities.remove(e.entity)}catch(_){}rec.group=null;rec.entities=[]}
function removeRecord(id){const r=S.records.get(id);if(!r)return;r.epoch=(r.epoch||0)+1;r.abort?.abort();removeGraphics(r);S.records.delete(id);if(S.selected?.src?.id===id){clearSelection();W.TakMapContextSidebarI572?.hide?.('infrastructure-hidden')}}
function clearMap(){for(const id of [...S.records.keys()])removeRecord(id)}
function counts(){const view=viewBox(),boxes=view?boxParts(view):[];for(const src of state().layers.filter(x=>x.mode==='offline')){const node=D.querySelector('[data-infra-counter="'+CSS.escape(src.id)+'"]');if(!node)continue;let status='';if(!S.visible)status='Hidden by master toggle';else if(!src.enabled)status='Disabled';else if(src.hidden||!visibleCategory(category(src.category_id)))status='Category hidden';else if(!eligible(src))status='Hidden below z'+src.min_zoom;else{const rec=S.records.get(src.id),n=rec&&boxes.length?new Set((rec.features||[]).filter(f=>geometryVisible(f,boxes)).map(f=>str(f.id))).size:0;status=n.toLocaleString()+' / '+Number(src.feature_count||0).toLocaleString();if(rec?.featureCap)status+=' · LIMIT REACHED';else if(rec?.geometryLimited)status+=' · SIMPLIFIED';if(rec?.status==='loading')status+=' · loading';else if(rec?.status==='error')status+=' · ERROR'}node.textContent=status}
 const list=[...S.records.values()];const errors=list.filter(r=>r.status==='error').length;if(!S.visible)message('Infrastructure hidden · existing layer choices preserved');else message(list.reduce((sum,r)=>sum+r.features.length,0).toLocaleString()+' buffered features'+(errors?' · '+errors+' load errors':''),!!errors)}
function recolor(src){const rec=S.records.get(src.id);if(!rec)return;rec.cache=null;schedule(true)}
let fetchTimer=null;
function schedule(force=false){clearTimeout(fetchTimer);fetchTimer=setTimeout(()=>void refreshFeatures(force),250)}
async function refreshFeatures(force=false){const m=getMap();if(!m||!S.ready||!W.L)return;const view=viewBox();if(!view)return;const needed=selectedLayers(),ids=new Set(needed.map(x=>x.id));for(const id of [...S.records.keys()])if(!ids.has(id))removeRecord(id);
 const viewParts=boxParts(view),workParts=boxParts(view,1.5);const requests=[];
 for(const src of needed){let rec=S.records.get(src.id);if(!rec){rec={id:src.id,epoch:0,group:null,entities:[],features:[],cache:null,status:'new',abort:null,featureCap:false,geometryLimited:false};S.records.set(src.id,rec)}
 if(!force&&rec.cache&&withinCache(rec.cache,viewParts)&&rec.status==='ready')continue;
 const token=++rec.epoch;rec.abort?.abort();rec.abort=new AbortController();rec.status='loading';const controller=rec.abort;
 const stale=()=>rec.epoch!==token||controller.signal.aborted||!S.records.has(src.id)||!eligible(src);
 requests.push((async()=>{try{let items=[],limit=false,simple=false,seen=new Set();for(const region of workParts){const qs=new URLSearchParams({layer:src.id,mode:'offline',bbox:region.map(n=>n.toFixed(6)).join(','),minimum:String(S.min),zoom:String(effectiveZoom())});const result=await api('features?'+qs,{signal:controller.signal});if(stale())return;for(const f of result.features||[]){if(items.length>=FEATURE_CAP){limit=true;break}const key=str(f.id);if(!seen.has(key)){seen.add(key);items.push(f)}}limit=limit||!!result.feature_cap_reached;simple=simple||!!result.geometry_simplified}
 if(stale())return;const nextGroup=W.L.layerGroup(),nextRec={entities:[],group:nextGroup};draw2d(items,src,nextGroup);
 if(stale())return;const priorGroup=rec.group,priorEntities=rec.entities;rec.group=nextGroup;rec.entities=[];nextGroup.addTo(m);draw3d(items,src,rec);
 rec.features=items;rec.cache=workParts;rec.featureCap=limit;rec.geometryLimited=simple;rec.status='ready';rec.failures=0;
 try{if(priorGroup)m.removeLayer(priorGroup)}catch(_){}for(const x of priorEntities)try{x.viewer.entities.remove(x.entity)}catch(_){}
 // Selection metadata survives replacement. Reconnect the outline to the new graphic.
 if(S.selected?.src.id===src.id){const picked=S.selected.feature;clearSelection();const feature=items.find(f=>f._infraSelectionKey===picked._infraSelectionKey)||items.find(f=>str(f.id)===str(picked.id));if(feature){S.selected={feature,src};redOutline(feature,src,nextGroup._infraShapes?.get(feature._infraSelectionKey)||null)}else{S.selected={feature:picked,src};redOutline(picked,src,null)}}
 }catch(err){if(stale()||err.name==='AbortError')return;rec.status='error';rec.cache=null;S.errors[src.id]=str(err.message);/* keep last committed geometry */
 rec.failures=(rec.failures||0)+1;const tries=rec.failures;
 if(tries<=4)setTimeout(()=>{if(S.records.get(src.id)===rec&&rec.epoch===token&&eligible(src))schedule()},Math.min(15000,500*Math.pow(2,tries)));}finally{if(rec.epoch===token)counts()}})())
 }
 counts();await Promise.allSettled(requests)
}
function bind3d(){const v=viewer(),C=W.Cesium;if(!v?.canvas||!C||v===S.viewer)return;S.viewer=v;
 try{v.camera.moveEnd.addEventListener(()=>schedule())}catch(_){}
 v.canvas.addEventListener('click',e=>{if(routeBusy())return;const b=v.canvas.getBoundingClientRect();let found=null;try{for(const hit of v.scene.drillPick(new C.Cartesian2(e.clientX-b.left,e.clientY-b.top),12)){const p=hit?.id?.properties;if(!p?.infraFeature)continue;const f=JSON.parse(p.infraFeature.getValue?.()||'{}'),src=layerById(p.infraSource.getValue?.());if(src&&eligible(src)){found={f,src,shape:hit.id};break}}}catch(_){}
 if(found)selectFeature(found.f,found.src,found.shape);else if(S.selected)clearSelection()},false)
}
function updateJobs(){const root=$('takInfraJobsI685');if(!root)return;const live=state().jobs.filter(j=>!['complete','canceled'].includes(j.status)).slice(0,6);const ids=new Set(live.map(j=>j.id));root.querySelectorAll('[data-infra-job]').forEach(node=>{if(!ids.has(node.dataset.infraJob))node.remove()});for(const job of live){let node=Array.from(root.querySelectorAll('[data-infra-job]')).find(n=>n.dataset.infraJob===job.id);if(!node){node=D.createElement('div');node.className='infra-job';node.dataset.infraJob=job.id;node.innerHTML='<div data-job-title></div><div class="infra-progress" data-job-progress></div><button class="infra-btn" type="button" data-job-action></button>';root.append(node);node.querySelector('button').onclick=()=>void jobOperation(node.querySelector('button').dataset.jobOp,job.id)}const src=layerById(job.source_id);node.querySelector('[data-job-title]').textContent=(src?.name||job.source_id)+' · '+job.status;node.querySelector('[data-job-progress]').textContent=Number(job.received||0).toLocaleString()+' features saved'+(job.error?' · '+job.error:'');const action=node.querySelector('button');action.textContent=job.status==='interrupted'?'Resume':'Cancel';action.dataset.jobOp=job.status==='interrupted'?'download-resume':'download-cancel'}}

// Accessible TAK Map styled zoom listbox. Portal is fixed to body and outlives status polls.
const ZOOM_VALUES=[null,...Array.from({length:23},(_,i)=>i)];
const zoomText=z=>z==null?'Always':'z'+z+'+';
function closeMinZoom(focus=false){const shown=S.zoomMenu;if(!shown)return;
 shown.menu.remove();S.zoomMenu=null;shown.trigger.setAttribute('aria-expanded','false');
 if(focus&&shown.trigger.isConnected)shown.trigger.focus();
}
function openMinZoom(trigger,src){
 if(S.zoomMenu?.trigger===trigger){closeMinZoom(true);return}
 closeMinZoom();const menu=D.createElement('div');menu.className='infra-zoom-menu-i689';menu.id='infra-zoom-list-i689';menu.setAttribute('role','listbox');menu.setAttribute('aria-label','Minimum visibility zoom for '+src.name);
 const current=src.min_zoom==null?null:Number(src.min_zoom);
 let active=ZOOM_VALUES.findIndex(v=>v===current);if(active<0)active=0;
 const items=ZOOM_VALUES.map((v,i)=>{const el=D.createElement('button');el.type='button';el.className='infra-zoom-choice-i689';el.role='option';el.id='infra-zoom-option-i689-'+i;el.textContent=zoomText(v);el.dataset.index=String(i);el.setAttribute('aria-selected',v===current?'true':'false');el.tabIndex=-1;el.onclick=e=>{e.stopPropagation();closeMinZoom();if(v!==current)void submitManage({op:'layer-minzoom',id:src.id,min_zoom:v})};menu.append(el);return el});
 D.body.append(menu);S.zoomMenu={menu,trigger,items,active};trigger.setAttribute('aria-expanded','true');trigger.setAttribute('aria-controls',menu.id);
 const rect=trigger.getBoundingClientRect(),maxHeight=Math.min(232,Math.max(92,D.documentElement.clientHeight-24));menu.style.maxHeight=maxHeight+'px';
 const width=Math.max(116,rect.width);menu.style.width=width+'px';const left=Math.min(Math.max(8,rect.left),Math.max(8,D.documentElement.clientWidth-width-8));menu.style.left=left+'px';
 const enoughBelow=D.documentElement.clientHeight-rect.bottom>=Math.min(maxHeight,160);const top=enoughBelow?rect.bottom+4:Math.max(6,rect.top-4-maxHeight);menu.style.top=top+'px';
 // Scroll only the popover, not the surrounding page/sidebar.
 const picked=items[active];menu.scrollTop=Math.max(0,picked.offsetTop-menu.clientHeight/2+picked.offsetHeight/2);
 picked.focus({preventScroll:true});
}
function createMinZoomControl(src){const root=D.createElement('div');root.className='infra-zoom-control-i689';const button=D.createElement('button');button.type='button';button.className='infra-minzoom infra-zoom-trigger-i689';button.title='Minimum visibility zoom';button.setAttribute('aria-label','Minimum zoom for '+src.name);button.setAttribute('aria-haspopup','listbox');button.setAttribute('aria-expanded','false');button.textContent=zoomText(src.min_zoom);button.onclick=e=>{e.stopPropagation();openMinZoom(button,src)};root.append(button);return root}
D.addEventListener('pointerdown',e=>{const open=S.zoomMenu;if(open&&!open.menu.contains(e.target)&&!open.trigger.contains(e.target))closeMinZoom()},true);
D.addEventListener('keydown',e=>{const o=S.zoomMenu;if(!o)return;
 if(e.key==='Escape'||e.key==='Tab'){closeMinZoom(e.key==='Escape');if(e.key==='Escape')e.preventDefault();return}
 let n=o.active;if(['ArrowDown','ArrowUp','Home','End','PageDown','PageUp'].includes(e.key)){
  e.preventDefault();if(e.key==='Home')n=0;else if(e.key==='End')n=o.items.length-1;else n=Math.max(0,Math.min(o.items.length-1,n+(e.key==='ArrowDown'?1:e.key==='ArrowUp'?-1:e.key==='PageDown'?6:-6)));
  o.active=n;const item=o.items[n];item.focus({preventScroll:true});if(item.offsetTop<o.menu.scrollTop)o.menu.scrollTop=item.offsetTop;
  else if(item.offsetTop+item.offsetHeight>o.menu.scrollTop+o.menu.clientHeight)o.menu.scrollTop=item.offsetTop+item.offsetHeight-o.menu.clientHeight;
 }else if(e.key==='Enter'||e.key===' '){e.preventDefault();o.items[o.active].click()}
},true);

function render(){closeMinZoom();const card=$(ID);if(!card)return;updateHeader();
 const list=$('takInfraCategoriesI685');list.replaceChildren();for(const cat of state().categories){if(!visibleCategory(cat))continue;const layers=state().layers.filter(x=>x.mode==='offline'&&!x.hidden&&x.category_id===cat.id),sec=D.createElement('section');sec.className='infra-category';sec.dataset.category=cat.id;
 const h=D.createElement('button');h.className='infra-cat-head';h.type='button';h.innerHTML=`<span class="name">${esc(cat.label)}</span><span class="infra-cat-count">${layers.length}</span><span>${S.open.has(cat.id)?'▾':'▸'}</span>`;h.onclick=()=>{S.open.has(cat.id)?S.open.delete(cat.id):S.open.add(cat.id);localStorage.setItem('takmap.infra.open.i686',JSON.stringify([...S.open]));render()};sec.append(h);
 if(S.open.has(cat.id)){const controls=D.createElement('div');controls.className='infra-actions';const button=(label,fn)=>{const b=D.createElement('button');b.type='button';b.className='infra-btn';b.textContent=label;b.onclick=fn;controls.append(b)};
 button('+ Import',()=>importFile(cat.id));button('Rename',()=>renameCategory(cat));button('Remove',()=>manageCategory(cat));sec.append(controls);
 if(!layers.length){const empty=D.createElement('div');empty.className='infra-empty';empty.textContent='No offline datasets. Import GIS files or download a region.';sec.append(empty)}
 for(const src of layers){const row=D.createElement('div');row.className='infra-layer';row.style.borderLeftColor=colorFor(src);const cb=D.createElement('input');cb.type='checkbox';cb.checked=!!src.enabled;cb.title='Show layer';cb.onchange=()=>void submitManage({op:'layer-enable',id:src.id,enabled:cb.checked});const name=D.createElement('div');name.className='infra-layer-name-area';name.innerHTML=`<div class="infra-layer-name">${esc(src.name)}</div><div class="infra-layer-meta" data-infra-counter="${esc(src.id)}"></div>`;const tools=D.createElement('div');tools.className='infra-tools';
 const color=D.createElement('input');color.type='color';color.className='infra-color';color.value=colorFor(src);color.title='Layer color';color.onchange=()=>void submitManage({op:'layer-color',id:src.id,color:color.value},{recolor:true});tools.append(color);
 tools.append(createMinZoomControl(src));
 const tool=(title,fn)=>{const b=D.createElement('button');b.type='button';b.className='infra-btn';b.textContent=title;b.onclick=fn;tools.append(b)};
 tool('Filter',()=>openFilter(src));if(src.kind==='point'||src.kind==='other')tool('Symbol',()=>chooseSymbol(src));tool('Export',()=>exportLayer(src));tool('✕',()=>deleteLayer(src));row.append(cb,name,tools);sec.append(row)
 }}list.append(sec)}$('takInfraMinI685').value=str(S.min);updateJobs();counts();S.cardRevision++}
async function load(opts={}){try{const result=await api('state');S.data=result;const first=!S.ready;S.ready=true;if(!opts.jobsOnly)render();else updateJobs();if(first||opts.refresh)schedule(true)}catch(e){message(e.message,true)}}
async function submitManage(payload,options={}){try{S.data=await post('manage',payload);render();schedule(true);refreshSearch();return true}catch(e){message(e.message,true);return false}}
function renameCategory(cat){const name=prompt('Infrastructure category name',cat.label);if(name?.trim())void submitManage({op:'category-rename',id:cat.id,name:name.trim()})}
function manageCategory(cat){if(confirm('Remove '+cat.label+' from Infrastructure? Saved GIS data will remain and can be restored.'))void submitManage({op:'category-hide',id:cat.id,mode:'offline',hidden:true})}
function addCategory(){const name=prompt('New Infrastructure category');if(name?.trim())void submitManage({op:'category-create',name:name.trim()})}
function deleteLayer(src){if(!confirm('Permanently delete '+src.name+' and its '+Number(src.feature_count||0).toLocaleString()+' features?'))return;void submitManage({op:'layer-delete',id:src.id})}
function fileInput(){return $('takInfraImportInputI685')}
function importFile(cat){const input=fileInput();input.dataset.category=cat;input.value='';input.click()}
async function onFile(){const input=fileInput(),file=input.files?.[0];if(!file)return;const cat=input.dataset.category||'water',name=prompt('Imported dataset name',file.name.replace(/\.[^.]+$/,''));if(name===null)return;const kind=prompt('Layer type: sewer, point, line, other','other')||'other';message('Importing '+file.name+'…');const params=new URLSearchParams({category:cat,name:name||file.name,kind,filename:file.name});try{const r=await fetch(API+'import?'+params,{method:'POST',body:file,credentials:'same-origin'}),j=await r.json();if(!r.ok||!j.ok)throw Error(j.error||'Import failed');await load({refresh:true});message('Imported '+j.count.toLocaleString()+' features.')}catch(e){message(e.message,true)}}
function exportLayer(src){const fmt=prompt('Export format: gpkg, geojson, zip (Shapefile), kml, kmz','gpkg');if(!fmt)return;if(!['gpkg','geojson','zip','kml','kmz'].includes(fmt.toLowerCase()))return message('Unsupported export format',true);W.location.href=API+'export?'+new URLSearchParams({layer:src.id,format:fmt.toLowerCase()})}
function startDownload(){const online=state().layers.filter(x=>x.mode==='online'&&!x.hidden&&x.url);if(!online.length)return message('No configured GIS providers available for download',true);const list=online.map((x,i)=>(i+1)+'. '+x.name).join('\n');const n=Number(prompt('Choose a provider number to download for the map area:\n'+list,'1'));const source=online[n-1];if(!source)return;const b=S.drawBounds||viewBox();if(!b)return message('Map bounds unavailable',true);if(!confirm('Download '+source.name+' for the selected geographic area?'))return;void post('jobs',{op:'download-start',source_id:source.id,bbox:b}).then(()=>{S.drawBounds=null;void load()}).catch(e=>message(e.message,true))}
async function jobOperation(op,id){try{await post('jobs',{op,id});await load({jobsOnly:true})}catch(e){message(e.message,true)}}
function drawRegion(){const m=getMap(),L=W.L;if(!m||!L)return message('2D map unavailable',true);S.drawBounds=null;S.drawFirst=null;if(S.drawLayer)m.removeLayer(S.drawLayer);message('Click two opposite corners of the area to download.');function capture(e){if(routeBusy())return;const ll=e.latlng;if(!S.drawFirst){S.drawFirst=ll;return}m.off('click',capture);const a=S.drawFirst;S.drawBounds=[Math.min(a.lng,ll.lng),Math.min(a.lat,ll.lat),Math.max(a.lng,ll.lng),Math.max(a.lat,ll.lat)];S.drawFirst=null;S.drawLayer=L.rectangle([[S.drawBounds[1],S.drawBounds[0]],[S.drawBounds[3],S.drawBounds[2]]],{color:'#8dc2df',weight:2,fillOpacity:.07,interactive:false}).addTo(m);message('Download area selected. Click Download when ready.')}m.on('click',capture)}
function chooseSymbol(src){const registry=W.TakMapIconRegistryI572||W.TakMapIconRegistryI556;
 const mode=prompt('Marker style: type "dot" for Circle Dot, or "registry" to choose a TAK Icon Registry symbol',src.point_symbol_mode||'dot');if(!mode)return;
 if(mode.toLowerCase()==='dot'){void submitManage({op:'layer-symbol',id:src.id,point_symbol_mode:'dot',point_symbol_ref:null});return}
 if(mode.toLowerCase()!=='registry')return message('Choose dot or registry',true);
 if(!registry?.open)return message('TAK Icon Registry is not ready',true);
 S.iconTarget=src.id;registry.open('infrastructure',src.point_symbol_ref||null)}
D.addEventListener('takmap:infrastructure-icon-selected',event=>{const src=layerById(S.iconTarget);if(!src)return;const icon=event.detail?.icon;if(icon?.kind)void submitManage({op:'layer-symbol',id:src.id,point_symbol_mode:'registry',point_symbol_ref:icon});S.iconTarget=null});
function openFilter(src){const old=src.filter_spec||{enabled:false,mode:'all',rules:[]};const dlg=D.createElement('div');dlg.className='infra-filter-backdrop';dlg.innerHTML=`<div class="infra-filter-modal" role="dialog" aria-modal="true"><div class="infra-filter-title"><strong>ATTRIBUTE FILTER — ${esc(src.name)}</strong><button type="button" data-filter-close>✕</button></div><label class="infra-inline"><input type="checkbox" data-filter-enabled ${old.enabled?'checked':''}> Enable filter</label><label class="infra-inline">Match <select data-filter-mode><option value="all">ALL (AND)</option><option value="any">ANY (OR)</option></select> conditions</label><div data-filter-rules></div><div class="infra-actions"><button type="button" class="infra-btn" data-filter-add>+ Rule</button><button type="button" class="infra-btn" data-filter-save>Save</button><button type="button" class="infra-btn" data-filter-close>Cancel</button></div><div class="infra-help" data-filter-message>Filters affect display and search, not stored GIS data.</div></div>`;D.body.append(dlg);
 const fieldList=D.createElement('datalist');fieldList.id='infra-fields-'+Math.random().toString(36).slice(2);dlg.append(fieldList);
 dlg.querySelector('[data-filter-mode]').value=old.mode||'all';const host=dlg.querySelector('[data-filter-rules]');
 const ops=[['=','='],['!=','≠'],['>','>'],['>=','≥'],['<','<'],['<=','≤'],['contains','Contains'],['not_contains','Does not contain'],['starts_with','Starts with'],['ends_with','Ends with'],['between','Between'],['empty','Is empty'],['not_empty','Is not empty']];
 function addRule(r={}){const row=D.createElement('div');row.className='infra-filter-rule';row.innerHTML=`<input data-field placeholder="GIS attribute" aria-label="GIS attribute" list="${fieldList.id}"><select data-op aria-label="Comparison operator">${ops.map(x=>`<option value="${x[0]}">${x[1]}</option>`).join('')}</select><input data-value placeholder="Value" aria-label="Comparison value"><input data-other placeholder="To" aria-label="Between end value"><select data-type aria-label="Data type"><option value="auto">Auto</option><option value="number">Number</option><option value="text">Text</option><option value="date">Date</option></select><button type="button" class="infra-btn" data-remove>✕</button>`;row.querySelector('[data-field]').value=r.field||'';row.querySelector('[data-op]').value=r.op||'=';row.querySelector('[data-value]').value=r.value??'';row.querySelector('[data-other]').value=r.other??'';row.querySelector('[data-type]').value=r.type||'auto';const op=row.querySelector('[data-op]'),refresh=()=>{row.querySelector('[data-other]').hidden=op.value!=='between';row.querySelector('[data-value]').hidden=['empty','not_empty'].includes(op.value)};op.onchange=refresh;refresh();row.querySelector('[data-remove]').onclick=()=>row.remove();host.append(row)}
 (old.rules||[]).forEach(addRule);if(!old.rules?.length)addRule();
 const close=()=>dlg.remove();dlg.querySelectorAll('[data-filter-close]').forEach(b=>b.onclick=close);dlg.querySelector('[data-filter-add]').onclick=()=>{if(host.children.length<12)addRule()};
 dlg.querySelector('[data-filter-save]').onclick=async()=>{const rules=[...host.children].map(row=>({field:row.querySelector('[data-field]').value.trim(),op:row.querySelector('[data-op]').value,type:row.querySelector('[data-type]').value,value:row.querySelector('[data-value]').value,other:row.querySelector('[data-other]').value}));if(rules.some(x=>!x.field))return dlg.querySelector('[data-filter-message]').textContent='Each rule requires an attribute name.';try{if(await submitManage({op:'layer-filter',id:src.id,filter_spec:{enabled:dlg.querySelector('[data-filter-enabled]').checked,mode:dlg.querySelector('[data-filter-mode]').value,rules}}))close()}catch(e){dlg.querySelector('[data-filter-message]').textContent=e.message}};
 api('fields?'+new URLSearchParams({layer:src.id})).then(r=>{for(const field of r.fields||[]){const opt=D.createElement('option');opt.value=field;fieldList.append(opt)}}).catch(()=>{});
}
function installSearch(){const input=$('layerSearch');if(!input||input.dataset.infraSearchI688)return;input.dataset.infraSearchI688='1';const original=W.renderSearchResults;
 const inject=()=>{const box=$('searchResults'),q=input.value.trim();if(!box||!q||S.searchQuery!==q||!S.searchResults.length)return;
  box.style.display='block';if(box.textContent?.includes('No matching map objects.'))box.replaceChildren();for(const item of S.searchResults){const b=D.createElement('button');b.type='button';b.className='search-result-item infra-search-hit-i688';const span=D.createElement('span'),title=D.createElement('b'),sub=D.createElement('small'),chip=D.createElement('span');title.textContent=item.label;sub.textContent='Infrastructure · '+item.category+' · '+item.layer_name;chip.textContent='OFFLINE';chip.className='search-result-chip';span.append(title,sub);b.append(span,chip);b.onclick=()=>void selectSearch(item);box.append(b)}};
 if(typeof original==='function'){W.renderSearchResults=function(...args){const result=original.apply(this,args);inject();return result}};
 let timer=null;input.addEventListener('input',()=>{clearTimeout(timer);const q=input.value.trim();S.searchEpoch++;S.searchResults=[];S.searchQuery=q;if(q.length<2)return;const epoch=S.searchEpoch;timer=setTimeout(async()=>{try{const reply=await api('search?'+new URLSearchParams({q,minimum:String(S.min),limit:'24'}));if(epoch!==S.searchEpoch||input.value.trim()!==q)return;S.searchResults=reply.results||[];W.renderSearchResults?.()}catch(e){if(epoch===S.searchEpoch)message('Search unavailable: '+e.message,true)}},250)});
}
function refreshSearch(){const input=$('layerSearch');if(input?.value.trim()){input.dispatchEvent(new Event('input',{bubbles:true}))}}
async function selectSearch(item){try{const j=await api('feature?'+new URLSearchParams({layer:item.layer_id,id:item.id,minimum:String(S.min)})),src=layerById(item.layer_id);if(!src||!eligible(src))return;zoomTo(j.feature,src);selectFeature(j.feature,src,null);$('searchResults').style.display='none'}catch(e){message('Cannot select infrastructure result: '+e.message,true)}}
// Place this card directly after the live BASEMAP panel, even if its heading is renamed.
// This runs on every Infrastructure probe and after direct sidebar reordering.
let observedSidebar=null, orderObserver=null;
function ensureOrder(){
 const side=$('sidebar'),card=$(ID);if(!side||!card)return false;
 const base=[$('basemapSelect'),$('takBasemapBlendI673')].map(el=>el?.closest?.('.panel')).find(el=>el?.parentElement===side)
  || [...side.children].find(el=>el.classList?.contains('panel')&&/^basemap(?:\s+layers)?$/i.test(el.querySelector('h2')?.textContent?.trim()||''));
 const veil=$('takVeilCardI665');
 if(base&&base!==card){
  if(card.parentElement!==side||base.nextElementSibling!==card)side.insertBefore(card,base.nextElementSibling);
  if(veil?.parentElement===side&&card.nextElementSibling!==veil)side.insertBefore(veil,card.nextElementSibling);
  return true
 }
 if(veil?.parentElement===side){if(card.nextElementSibling!==veil)side.insertBefore(card,veil);return true}
 return card.parentElement===side;
}
function observeOrder(side){
 if(observedSidebar===side)return;
 orderObserver?.disconnect?.();observedSidebar=side;
 if(typeof MutationObserver==='function'){orderObserver=new MutationObserver(()=>ensureOrder());orderObserver.observe(side,{childList:true})}
}
function updateHeader(){const card=$(ID);if(!card)return;
 const chk=$('takInfraVisibilityI694');if(chk){
  if(chk.checked!==S.visible)chk.checked=S.visible;
  const label=S.visible?'Hide infrastructure overlays':'Show infrastructure overlays';
  if(chk.getAttribute('aria-label')!==label)chk.setAttribute('aria-label',label);
  const parent=chk.closest('label');if(parent&&parent.title!==label)parent.title=label;
 }
 const status=card.querySelector('.infra-status'),state=S.visible?'OFFLINE':'HIDDEN';if(status&&status.textContent!==state)status.textContent=state;
 const expanded=String(!S.collapsed);card.querySelectorAll('.infra-collapse').forEach(el=>{if(el.getAttribute('aria-expanded')!==expanded)el.setAttribute('aria-expanded',expanded)});
 const arrow=card.querySelector('.infra-chevron'),glyph=S.collapsed?'▸':'▾';if(arrow&&arrow.textContent!==glyph)arrow.textContent=glyph;
 const body=card.querySelector('.infra-body');if(body&&body.hidden!==S.collapsed)body.hidden=S.collapsed;
}
function setVisible(show){const next=!!show;if(next===S.visible){updateHeader();return}
 S.visible=next;localStorage.setItem('takmap.infra.visible.i694',next?'1':'0');updateHeader();
 if(!next){clearTimeout(fetchTimer);clearMap();counts()}else{schedule(true);counts()}
}
// Upgrade older in-page Infrastructure headers without replacing the card/body.
// i694 only added the visibility switch when creating a NEW card, leaving
// pre-existing i688/i689 markup without a switch. Self-heal on every boot.
function ensureInfrastructureHeader(card){
 if(!card)return false;
 let head=card.querySelector('.infra-head');
 const current=head?.querySelector('#takInfraVisibilityI694')&&
   head.querySelector('.infra-header-title')&&head.querySelector('.infra-chevron-button');
 if(!current){
  const replacement=D.createElement('header');replacement.className='infra-head';
  replacement.innerHTML=`<button type="button" class="infra-collapse infra-header-title" aria-controls="takInfraBodyI685" aria-expanded="true"><span class="infra-title">INFRASTRUCTURE</span><span class="infra-status">OFFLINE</span></button><label class="infra-switch" title="Hide infrastructure overlays"><input id="takInfraVisibilityI694" type="checkbox" checked aria-label="Hide infrastructure overlays"><span aria-hidden="true"></span></label><button type="button" class="infra-collapse infra-chevron-button" aria-controls="takInfraBodyI685" aria-expanded="true" aria-label="Expand or collapse Infrastructure"><span class="infra-chevron">▾</span></button>`;
  if(head)head.replaceWith(replacement);else card.insertBefore(replacement,card.firstChild);
  head=replacement;
 }
 if(head.dataset.infraHeaderBoundI695!=='1'){
  head.dataset.infraHeaderBoundI695='1';
  const toggleCollapse=()=>{S.collapsed=!S.collapsed;localStorage.setItem('takmap.infra.collapsed.i685',S.collapsed?'1':'0');updateHeader()};
  head.querySelectorAll('.infra-collapse').forEach(btn=>btn.addEventListener('click',toggleCollapse));
  head.querySelector('#takInfraVisibilityI694')?.addEventListener('change',e=>setVisible(e.target.checked));
 }
 updateHeader();return true;
}
function install(){const side=$('sidebar');if(!side)return false;
 if($(ID)){observeOrder(side);ensureOrder();ensureInfrastructureHeader($(ID));return true}
 const b=D.createElement('section');b.className='panel';b.id=ID;b.dataset.skipAutoCollapsible='true';
 b.innerHTML=`<header class="infra-head"><button type="button" class="infra-collapse infra-header-title" aria-controls="takInfraBodyI685" aria-expanded="true"><span class="infra-title">INFRASTRUCTURE</span><span class="infra-status">OFFLINE</span></button><label class="infra-switch" title="Hide infrastructure overlays"><input id="takInfraVisibilityI694" type="checkbox" checked aria-label="Hide infrastructure overlays"><span aria-hidden="true"></span></label><button type="button" class="infra-collapse infra-chevron-button" aria-controls="takInfraBodyI685" aria-expanded="true" aria-label="Expand or collapse Infrastructure"><span class="infra-chevron">▾</span></button></header><div class="infra-body" id="takInfraBodyI685"><div class="infra-help">Saved and imported GIS layers. No automatic online streaming.</div><div class="infra-row between"><span class="infra-help">Sewer minimum diameter</span><select id="takInfraMinI685"><option value="36">36 in +</option><option value="48">48 in +</option><option value="60">60 in +</option><option value="0">All sizes</option></select></div><div id="takInfraCategoriesI685"></div><div class="infra-actions"><button class="infra-btn" type="button" data-action="category">+ Category</button><button class="infra-btn" type="button" data-action="restore">Restore</button><button class="infra-btn" type="button" data-action="download">Download</button><button class="infra-btn" type="button" data-action="draw">Draw area</button></div><div id="takInfraJobsI685"></div><div id="takInfraMessageI685" class="infra-message">Loading saved infrastructure…</div><input id="takInfraImportInputI685" type="file" accept=".geojson,.json,.gpkg,.zip,.kml,.kmz" hidden></div>`;
 side.appendChild(b);observeOrder(side);ensureOrder();
 ensureInfrastructureHeader(b);
 b.querySelector('[data-action="category"]').onclick=addCategory;b.querySelector('[data-action="download"]').onclick=startDownload;b.querySelector('[data-action="draw"]').onclick=drawRegion;
 b.querySelector('[data-action="restore"]').onclick=()=>{const removed=state().categories.filter(x=>x.hidden_offline);if(!removed.length)return message('No hidden Infrastructure categories');const name=prompt('Restore a category: '+removed.map(x=>x.label).join(', '),removed[0].label);const cat=removed.find(x=>x.label.toLowerCase()===str(name).toLowerCase());if(cat)void submitManage({op:'category-hide',id:cat.id,mode:'offline',hidden:false})};
 b.querySelector('#takInfraMinI685').onchange=e=>{S.min=Number(e.target.value);localStorage.setItem('takmap.infra.min.i685',str(S.min));for(const rec of S.records.values())rec.cache=null;schedule(true);refreshSearch()};fileInput().onchange=onFile;return true}
function monitorDetails(){const panel=$('takMapContextSidebarI572');if(!panel||S.observedPanel===panel||!W.MutationObserver)return;
 S.observedPanel=panel;S.panelObserver?.disconnect?.();S.panelObserver=new MutationObserver(()=>{if(!S.selected)return;
  if(panel.classList.contains('collapsed')){clearSelection();return}
  const signature=$('takMapContextSidebarBodyI572')?.dataset?.gatewayReadonlySignatureI615;
  if(signature&&S.contextSignature&&signature!==S.contextSignature)clearSelection()
 });S.panelObserver.observe(panel,{subtree:true,childList:true,attributes:true,attributeFilter:['class','data-gateway-readonly-signature-i615']})}
function boot(){if(!install())return;monitorDetails();const m=getMap();if(m&&m!==S.map){
  if(S.map){try{S.map.off('moveend zoomend',S.mapMoveHandler)}catch(_){}try{S.map.off('click',S.mapClickHandler)}catch(_){}
   // A new map instance must not reuse geometry attached to the previous map.
   for(const record of S.records.values()){record.epoch=(record.epoch||0)+1;record.abort?.abort();record.cache=null;
    if(record.group)try{S.map.removeLayer(record.group)}catch(_){}record.group=null;record.status='new'}
  }
  const onMove=()=>schedule();const onClick=e=>{if(routeBusy()||e.originalEvent?._infraHandled)return;
   if(S.selected){clearSelection();const p=W.TakMapContextSidebarI572;if(p?.diagnostics?.().open)p.hide?.('blank-map-click')}};
  // Only promote the map into shared state once listener registration succeeds.
  try{m.on('moveend zoomend',onMove);m.on('click',onClick)}catch(err){try{m.off('moveend zoomend',onMove);m.off('click',onClick)}catch(_){}return}
  S.map=m;S.mapMoveHandler=onMove;S.mapClickHandler=onClick;W.takLeafletMap=m;schedule()}
 const v=viewer(),viewMode=v?.scene?.mode;if(v&&(v!==S.viewer||viewMode!==S.viewerMode)){bind3d();S.viewerMode=viewMode;for(const rec of S.records.values()){rec.cache=null;for(const x of rec.entities||[])try{x.viewer.entities.remove(x.entity)}catch(_){}rec.entities=[]}schedule(true)}installSearch()}
function tick(){boot();const iconRegistry=W.TakMapIconRegistryI572||W.TakMapIconRegistryI556;
 if(!S.symbolsHydrated&&iconRegistry?.imageFor&&S.ready){S.symbolsHydrated=true;if(selectedLayers().some(x=>x.point_symbol_mode==='registry'))schedule(true)}
 if(!S.ready&&$(ID)){if(!S.loading){S.loading=true;load().finally(()=>{S.loading=false})}}}
if(D.readyState==='loading')D.addEventListener('DOMContentLoaded',()=>setTimeout(tick,200),{once:true});else setTimeout(tick,200);
const probe=setInterval(tick,800);
// Poll only job progress; never reconstruct the category controls during background updates.
setInterval(()=>{if(S.ready&&$(ID)&&!D.hidden)api('state').then(r=>{S.data.jobs=r.jobs;updateJobs()}).catch(()=>{})},5000);
W.TakMapInfrastructureI689={state:S,install,refreshFeatures,clearMap,selectFeature,boxParts,refreshSearch,setVisible,ensureOrder};
W.TakMapInfrastructureI688=W.TakMapInfrastructureI689;
})(window,document);
