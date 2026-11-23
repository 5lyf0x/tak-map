/* TAK Map i686: Infrastructure Overlays. Separate from Local Data and map object persistence. */
(function(W,D){'use strict';
const ID='takInfraCardI685';const API='/api/tak-map/infrastructure/';
const readStore=(k,f)=>{try{return JSON.parse(localStorage.getItem(k))??f}catch(_){return f}};
const savedOpen=readStore('takmap.infra.open.i686',null);
const legacyOpen=readStore('takmap.infra.open.i685','water');
const S={mode:localStorage.getItem('takmap.infra.mode.i686')||localStorage.getItem('takmap.infra.mode.i685')||'online',
 data:null,open:new Set(Array.isArray(savedOpen)?savedOpen:Array.isArray(legacyOpen)?legacyOpen:legacyOpen?[legacyOpen]:['water']),
 collapsed:localStorage.getItem('takmap.infra.collapsed.i685')==='1',min:36,drawBounds:null,drawFirst:null,drawLayer:null,
 map:null,records:new Map(),selected:null,selection:null,jobsTimer:null,viewer:null,initialized:false,errors:{},
 onlineVisible:localStorage.getItem('takmap.infra.onlineVisible.i686')!=='0',
 offlineVisible:localStorage.getItem('takmap.infra.offlineVisible.i686')!=='0'};
try{S.min=Number(localStorage.getItem('takmap.infra.min.i685')||36)}catch(_){}
const FEATURE_CAP=5000;
const $=id=>D.getElementById(id);const str=v=>v==null?'':String(v);
const esc=s=>str(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const api=async(path,options)=>{const r=await fetch(API+path,{credentials:'same-origin',cache:'no-store',...options});const j=await r.json().catch(()=>({ok:false,error:'Invalid infrastructure service response'}));if(!r.ok||!j.ok)throw new Error(j.error||'Infrastructure HTTP '+r.status);return j};
const post=(path,obj)=>api(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(obj)});
const state=()=>S.data||{categories:[],layers:[],jobs:[]};
const category=id=>state().categories.find(x=>x.id===id)||null;
const layerById=id=>state().layers.find(x=>x.id===id)||null;
const selectedLayers=()=>state().layers.filter(x=>x.enabled&&!x.hidden&&!category(x.category_id)?.hidden&&(x.mode==='online'?S.onlineVisible:S.offlineVisible));
function getMap(){try{if(typeof map!=='undefined'&&map&&typeof map.getBounds==='function')return map;}catch(_){}return W.takLeafletMap||W.map||null;}
function viewer(){try{if(typeof terrain3DViewer!=='undefined'&&terrain3DViewer&&terrain3DViewer.entities)return terrain3DViewer;}catch(_){}return W.terrain3DViewer||null;}
function routeBusy(){try{return typeof activeMapTool!=='undefined'&&!['move','select',''].includes(String(activeMapTool||'move'))}catch(_){return false}}
function message(text,bad=false){const el=$('takInfraMessageI685');if(!el)return;el.textContent=str(text);el.classList.toggle('error',!!bad)}
function defaultColor(kind){return ({sewer:'#66bdd0',line:'#eec477',point:'#b1a2f1',other:'#97cdd0'})[kind]||'#97cdd0'}
function colorFor(src){const value=String(src?.color||'').toLowerCase();return /^#[0-9a-f]{6}$/.test(value)?value:defaultColor(src.kind)}
function nameFor(feature,src){const p=feature.properties||{};return str(p.NAME||p.name||p.FACILITY_NAME||p.PRESET_NAME||p.PIPE_LOCN||p.STRUCTURE_ID||p.STATION_NAME||src.name||'Infrastructure feature')}
function diameter(p){const keys=['PIPE_DIAMETER','DIAMETER','DIAM','PIPE_DIA','DIAMETER_IN','DIAMETER_MM','DIAMETER_CM','DIAMETER_FT','DIA_IN','NOMINAL_DIAMETER'];for(const [k,v] of Object.entries(p||{})){const key=k.toUpperCase().replace(/ /g,'_');if(!keys.includes(key)||v==null)continue;const match=str(v).match(/\d+(?:\.\d+)?/);if(!match)continue;let n=Number(match[0]),unit=key.endsWith('_MM')?'mm':key.endsWith('_CM')?'cm':key.endsWith('_FT')?'ft':/\bmm\b/i.test(str(v))?'mm':/\bcm\b/i.test(str(v))?'cm':/\bft\b/i.test(str(v))?'ft':'in';n*=({mm:1/25.4,cm:1/2.54,ft:12,in:1})[unit];if(n>0&&n<1500)return Math.round(n*10)/10;}return null}
function passes(feature,src){if(src.kind!=='sewer'||S.min<=0)return true;const d=diameter(feature.properties||{});return d!==null&&d>=S.min}
function tooltip(feature,src){const p=feature.properties||{};const lines=[nameFor(feature,src)];const type=p.PIPE_MATERIAL||p.MATERIAL||p.FACILITY_TYPE||p.TYPE||p.STRUCTURE_TYPE;const size=diameter(p);if(size!==null)lines.push(size+' in diameter');if(type)lines.push(str(type));return lines.map(esc).join('<br>')}
function info(feature,src){const p=feature.properties||{}, size=diameter(p),title=nameFor(feature,src);
 const rows=[];const add=(label,keys,convert)=>{for(const k of keys){if(p[k]!=null&&str(p[k])!==''){rows.push([label,convert?convert(p[k]):str(p[k])]);break;}}};
 add('Type',['TYPE','type','FACILITY_TYPE','STRUCTURE_TYPE']);if(src.kind==='sewer'&&size!==null)rows.unshift(['Diameter',size+' in']);
 add('Material',['PIPE_MATERIAL','MATERIAL','material']);add('Voltage',['VOLTAGE','VOLTAGE_KV','voltage']);add('Operator',['OPERATOR','OWNER','OWNER_NAME']);
 add('Length',['PLAN_LENGTH','LENGTH_FT','SPAN_LENGTH']);add('Flow Direction',['FLOW_DIR','FLOW_DIRECTION']);add('Status',['STATUS','status']);
 add('Structure ID',['STRUCTURE_ID','BRIDGE_ID']);add('Height',['HEIGHT','TOWER_HEIGHT']);add('Coordinates',['LATITUDE','latitude']);
 const available=new Set(rows.map(x=>x[0]));
 for(const [key,val] of Object.entries(p)){if(rows.length>=10)break;if(val==null||typeof val==='object')continue;if(!available.has(key)&&['CITY_OR_COMMUNITY','REGION','COUNTY','STATE'].includes(key))rows.push([key.replaceAll('_',' '),str(val)])}
 const base=rows.map(([k,v])=>`<div class="kvp"><b>${esc(k)}</b><span>${esc(v)}</span></div>`).join('')||'<div class="kvp"><b>Properties</b><span>Not reported</span></div>';
 const raw=Object.entries(p).map(([k,v])=>`<div class="kvp"><b>${esc(k)}</b><span>${esc(typeof v==='object'?JSON.stringify(v):v)}</span></div>`).join('');
 return `<div class="tak-infra-properties-i685"><div class="kvp"><b>Category</b><span>${esc(category(src.category_id)?.label||src.category_id)}</span></div><div class="kvp"><b>Layer</b><span>${esc(src.name)}</span></div>${base}<div class="kvp"><b>Mode</b><span>${esc(src.mode==='online'?'Online service':'Downloaded / imported')}</span></div><div class="kvp"><b>Source</b><span>${esc(src.url||src.metadata?.provider||'Local GIS import')}</span></div><div class="infra-detail-actions"><button type="button" data-infra-action="zoom">Zoom to Object</button><button type="button" data-infra-action="coords">Copy Coordinates</button><button type="button" data-infra-action="export">Export Object</button></div><details><summary>Original GIS Attributes (${Object.keys(p).length})</summary>${raw||'<p>No properties supplied.</p>'}</details></div>`}
function selectFeature(feature,src,shape){if(routeBusy())return;resetHighlight();const m=getMap();if(shape&&shape.setStyle){try{S.selection={shape,old:{color:shape.options.color,weight:shape.options.weight}};shape.setStyle({color:'#f8f8f8',weight:5})}catch(_){}}
  S.selected={feature,src};const pane=W.TakMapContextSidebarI572;const data={uid:'infra:'+src.id+':'+str(feature.id||JSON.stringify(feature.geometry).slice(0,50)),name:nameFor(feature,src),category:'infrastructure'};
  if(shape&&!shape.setStyle){try{if(shape.polyline){S.selection={entity:shape,old:shape.polyline.material};shape.polyline.material=W.Cesium.Color.WHITE}else if(shape.point){S.selection={entity:shape,old:shape.point.outlineColor};shape.point.outlineColor=W.Cesium.Color.WHITE}}catch(_){}}
  if(pane&&typeof pane.showReadOnly==='function')pane.showReadOnly({object:data,layer:shape||null,key:data.uid,kicker:'INFRASTRUCTURE · '+(category(src.category_id)?.label||''),title:data.name,html:info(feature,src),signature:data.uid+'|'+JSON.stringify(feature.properties||{})});
  else message('Infrastructure selected: '+data.name+'. Object Details is unavailable.',true)
}
function resetHighlight(){try{if(S.selection?.shape?.setStyle)S.selection.shape.setStyle(S.selection.old);else if(S.selection?.entity){const e=S.selection.entity;if(e.polyline)e.polyline.material=S.selection.old;if(e.point)e.point.outlineColor=S.selection.old}}catch(_){}S.selection=null;S.selected=null}
function removeRecord(id){const r=S.records.get(id);if(!r)return;
 try{r.abort?.abort()}catch(_){};r.epoch=(r.epoch||0)+1;
 if(r.group){try{getMap()?.removeLayer(r.group)}catch(_){}}
 for(const x of r.entities||[]){try{x.viewer.entities.remove(x.entity)}catch(_){}}
 if(S.selected?.src?.id===id){try{W.TakMapContextSidebarI572?.hide('infrastructure-layer-hidden')}catch(_){}resetHighlight()}
 S.records.delete(id);
}
function clearMap(){for(const id of [...S.records.keys()])removeRecord(id);}
function draw2d(features,src,group){if(typeof L==='undefined'||!L.geoJSON)return;const col=colorFor(src);
 const layer=L.geoJSON({type:'FeatureCollection',features:features.filter(f=>f.geometry&&passes(f,src))},{
 style:()=>({color:col,weight:src.kind==='sewer'?3:2,opacity:.88,fillOpacity:.2}),
 pointToLayer:(f,ll)=>L.circleMarker(ll,{radius:6,color:col,weight:2,fillColor:col,fillOpacity:.8}),
 onEachFeature:(f,l)=>{l.bindTooltip(tooltip(f,src),{sticky:true,direction:'top',className:'tak-infra-tooltip-i685'});l.on('click',ev=>{try{L.DomEvent.stopPropagation(ev.originalEvent)}catch(_){}selectFeature(f,src,l)})}
 });layer.addTo(group)}
function draw3d(features,src,record){const v=viewer(),C=W.Cesium;if(!v||!C||!v.entities)return;const col=C.Color.fromCssColorString(colorFor(src));
 for(const f of features){if(!f.geometry||!passes(f,src))continue;let g=f.geometry,coords=g.coordinates;if(!coords)continue;
 const add=opts=>{try{const entity=v.entities.add({...opts,properties:{infraSource:src.id,infraFeature:JSON.stringify(f)}});record.entities.push({viewer:v,entity});}catch(_){}};
 const point=p=>{if(!p)return;add({position:C.Cartesian3.fromDegrees(p[0],p[1]),point:{pixelSize:9,color:col,outlineColor:C.Color.BLACK,outlineWidth:1,heightReference:C.HeightReference.CLAMP_TO_GROUND}})};
 const line=pts=>{if(!pts?.length)return;add({polyline:{positions:C.Cartesian3.fromDegreesArray(pts.flatMap(p=>p.slice(0,2))),width:3,material:col,clampToGround:true}})};
 if(g.type==='Point')point(coords);else if(g.type==='MultiPoint')coords.forEach(point);
 else if(g.type==='LineString')line(coords);else if(g.type==='MultiLineString')coords.forEach(line);
 else if(g.type==='Polygon'){if(coords[0]?.length)add({polygon:{hierarchy:C.Cartesian3.fromDegreesArray(coords[0].flatMap(p=>p.slice(0,2))),material:col.withAlpha(.25),outline:true,outlineColor:col,heightReference:C.HeightReference.CLAMP_TO_GROUND}})}
 else if(g.type==='MultiPolygon')for(const poly of coords){if(poly[0]?.length)add({polygon:{hierarchy:C.Cartesian3.fromDegreesArray(poly[0].flatMap(p=>p.slice(0,2))),material:col.withAlpha(.25),outline:true,outlineColor:col,heightReference:C.HeightReference.CLAMP_TO_GROUND}})}
 }
}
function bind3d(){const v=viewer(),C=W.Cesium;if(!v||!C||S.viewer===v)return;S.viewer=v;
 const canvas=v.canvas;const hint=D.createElement('div');hint.className='tak-infra-hover3d-i685';hint.hidden=true;D.body.append(hint);
 function lookup(ev){const box=canvas.getBoundingClientRect(),hit=v.scene.pick(new C.Cartesian2(ev.clientX-box.left,ev.clientY-box.top));
  if(!hit?.id?.properties?.infraFeature)return null;
  const props=hit.id.properties,feat=JSON.parse(props.infraFeature.getValue?.()||'{}'),src=layerById(props.infraSource.getValue?.());
  return src?{feature:feat,src,entity:hit.id}:null;
 }
 try{
  let lastHover=0;
  canvas.addEventListener('pointermove',ev=>{if(Date.now()-lastHover<70)return;lastHover=Date.now();
   const result=lookup(ev);if(!result){hint.hidden=true;return}
   hint.innerHTML=tooltip(result.feature,result.src);hint.style.left=Math.min(ev.clientX+15,W.innerWidth-200)+'px';
   hint.style.top=Math.min(ev.clientY+10,W.innerHeight-80)+'px';hint.hidden=false;
  },{passive:true});
  canvas.addEventListener('pointerleave',()=>hint.hidden=true,{passive:true});
  canvas.addEventListener('click',ev=>{if(routeBusy())return;const result=lookup(ev);hint.hidden=true;if(result)selectFeature(result.feature,result.src,result.entity)},false);
 }catch(_){}
}
function objectAction(action){const selected=S.selected;if(!selected)return;
 const {feature,src}=selected;
 if(action==='export'){
  const body=new Blob([JSON.stringify({type:'FeatureCollection',features:[feature]})],{type:'application/geo+json'});
  const uri=URL.createObjectURL(body),link=D.createElement('a');link.href=uri;link.download='infrastructure-'+str(feature.id||src.id).replace(/[^a-zA-Z0-9_-]/g,'_').slice(0,60)+'.geojson';D.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(uri),1000);
 }else if(action==='coords'){
  const coords=feature.geometry?.coordinates;let p=null;function first(x){if(!Array.isArray(x))return;if(x.length>=2&&typeof x[0]==='number'&&typeof x[1]==='number'){p=x;return}for(const item of x){if(p)return;first(item)}}first(coords);
  if(p&&navigator.clipboard?.writeText)void navigator.clipboard.writeText(Number(p[1]).toFixed(6)+', '+Number(p[0]).toFixed(6));
 }else if(action==='zoom'){
  const m=getMap();if(!m||!W.L)return;try{const selectedLayer=L.geoJSON(feature),bounds=selectedLayer.getBounds();if(bounds.isValid())m.fitBounds(bounds.pad(.25));else m.panTo(selectedLayer.getLayers()[0].getLatLng())}catch(_){}
 }
}
D.addEventListener('click',ev=>{const b=ev.target?.closest?.('[data-infra-action]');if(!b)return;ev.stopPropagation();objectAction(b.dataset.infraAction)},true);
function bbox(){const m=getMap();if(!m)return null;if(S.drawBounds)return S.drawBounds;
 const b=m.getBounds();return[b.getWest(),b.getSouth(),b.getEast(),b.getNorth()].map(n=>Number(n.toFixed(6)))}
function viewBox(){const m=getMap();if(!m)return null;const b=m.getBounds();return[b.getWest(),b.getSouth(),b.getEast(),b.getNorth()];}
function boxParts(bounds,scale=1){
 // Return WGS84-safe boxes; handle dateline crossing without widening to 360 degrees.
 let [w,s,e,n]=bounds.map(Number);if(e<w)e+=360;
 let width=Math.min(e-w,360),height=Math.min(n-s,180);
 const cx=w+width/2,cy=(s+n)/2;let W0=cx-width*scale/2,E0=cx+width*scale/2;
 const S0=Math.max(-90,cy-height*scale/2),N0=Math.min(90,cy+height*scale/2);
 if(E0-W0>=360)return [[-180,S0,180,N0]];
 while(W0>180){W0-=360;E0-=360}while(W0< -180){W0+=360;E0+=360}
 if(E0<=180)return [[W0,S0,E0,N0]];
 return [[W0,S0,180,N0],[-180,S0,E0-360,N0]];
}
function containsPoint(bounds,pt){const [x,y]=pt;return y>=bounds[1]&&y<=bounds[3]&&x>=bounds[0]&&x<=bounds[2]}
function geometryVisible(feature,boxes){const g=feature?.geometry;if(!g)return false;
 const pts=[];function visit(v){if(!Array.isArray(v))return;if(v.length>=2&&typeof v[0]==='number'&&typeof v[1]==='number'){pts.push(v);return}for(const q of v)visit(q)}visit(g.coordinates);
 if(!pts.length)return false;
 if(pts.some(pt=>boxes.some(box=>containsPoint(box,pt))))return true;
 // For cross-viewport linework and enclosing polygons, bounding overlap is a safe
 // coarse visible-count estimate; geometry remains available for accurate hit-testing.
 const minx=Math.min(...pts.map(p=>p[0])),maxx=Math.max(...pts.map(p=>p[0]));
 const miny=Math.min(...pts.map(p=>p[1])),maxy=Math.max(...pts.map(p=>p[1]));
 return boxes.some(b=>minx<=b[2]&&maxx>=b[0]&&miny<=b[3]&&maxy>=b[1]);
}
function viewportContains(cache,boxes){return cache&&boxes.every(b=>cache.some(c=>b[0]>=c[0]-1e-8&&b[2]<=c[2]+1e-8&&b[1]>=c[1]-1e-8&&b[3]<=c[3]+1e-8))}
function labelCounts(src){const r=S.records.get(src.id);if(!src.enabled||(src.mode==='online'&&!S.onlineVisible)||(src.mode==='offline'&&!S.offlineVisible))return 'Disabled';
 if(!r)return src.mode==='offline'?'0 / '+Number(src.feature_count||0).toLocaleString():'0 visible';
 const visibleParts=boxParts(viewBox()||[-180,-90,180,90]);
 const visible=new Set((r.features||[]).filter(f=>geometryVisible(f,visibleParts)&&passes(f,src)).map(f=>String(f.id??JSON.stringify(f.geometry)))).size;
 const main=src.mode==='online'?visible.toLocaleString()+' visible':visible.toLocaleString()+' / '+Number(src.feature_count||0).toLocaleString();
 return main+(r.status==='loading'?' · loading':r.limited?' · LIMITED — zoom in':r.status==='error'?' · error':r.status==='partial'?' · partial':'');
}
function updateCounts(){for(const src of state().layers){const node=Array.from(D.querySelectorAll('[data-infra-counter]')).find(n=>n.dataset.infraCounter===src.id);if(node)node.textContent=labelCounts(src)}
 const list=[...S.records.values()];const limited=list.filter(x=>x.limited).length,errors=list.filter(x=>x.status==='error').length;
 message(list.reduce((n,r)=>n+(r.features?.length||0),0).toLocaleString()+' buffered features · '+limited+' limited layer(s)'+(errors?' · '+errors+' errors':''),!!errors);
}
function recolor(src){const rec=S.records.get(src.id);if(!rec)return;const value=colorFor(src);
 if(rec.group){try{rec.group.eachLayer(layer=>{if(layer.setStyle)layer.setStyle({color:value,fillColor:value});if(layer.eachLayer)layer.eachLayer(shape=>{if(shape.setStyle)shape.setStyle({color:value,fillColor:value})})})}catch(_){}}
 const C=W.Cesium;if(C)for(const x of rec.entities||[]){const e=x.entity,col=C.Color.fromCssColorString(value);try{if(e.point)e.point.color=col;if(e.polyline)e.polyline.material=col;if(e.polygon){e.polygon.material=col.withAlpha(.25);e.polygon.outlineColor=col}}catch(_){}}
 if(S.selected?.src?.id===src.id&&S.selection){
   if(S.selection.shape?.setStyle){S.selection.old.color=value;S.selection.shape.setStyle({color:'#f8f8f8',weight:5})}
   else if(S.selection.entity?.polyline){S.selection.old=C.Color.fromCssColorString(value);S.selection.entity.polyline.material=C.Color.WHITE}
 }

}
let fetchTimer=null;
function schedule(){clearTimeout(fetchTimer);fetchTimer=setTimeout(()=>void refreshFeatures(),300)}
async function refreshFeatures(force=false){const m=getMap();if(!m||!S.initialized||typeof L==='undefined')return;
 const active=selectedLayers(),ids=new Set(active.map(x=>x.id));
 for(const id of [...S.records.keys()])if(!ids.has(id))removeRecord(id);
 const view=viewBox();if(!view)return;const visibleBoxes=boxParts(view);
 const work=[];
 for(const src of active){
  let rec=S.records.get(src.id);if(!rec){rec={id:src.id,entities:[],features:[],epoch:0,status:'loading',limited:false,cache:null,abort:null};S.records.set(src.id,rec)}
  if(!force&&rec.cache&&viewportContains(rec.cache,visibleBoxes))continue;
  const epoch=++rec.epoch;rec.abort?.abort();rec.abort=new AbortController();rec.status='loading';
  const bounds=boxParts(view,1.5);const controller=rec.abort;
  const task=(async()=>{try{
    // Progressive online paging, one bounded provider page at a time. Offline
    // spatial queries already return a bounded, indexed result in one request.
    let features=[],limited=false,geometryLimited=false;const seen=new Set();
    let replaced=false;let pages=0;let unfinished=false;
    function prepare(){if(replaced)return;
      if(rec.group){try{m.removeLayer(rec.group)}catch(_){}}
      for(const x of rec.entities){try{x.viewer.entities.remove(x.entity)}catch(_){}}
      rec.entities=[];rec.group=L.layerGroup().addTo(m);rec.features=[];replaced=true;
    }
    for(const b of bounds){
      let offset=0,more=true;
      while(more){
        if(rec.epoch!==epoch||!S.records.has(src.id))return;
        const remaining=FEATURE_CAP-features.length;
        if(remaining<=0){limited=true;unfinished=true;break}
        const qp=new URLSearchParams({layer:src.id,mode:src.mode,bbox:b.map(v=>v.toFixed(6)).join(','),minimum:String(S.min)});
        if(src.mode==='online'){
          qp.set('offset',String(offset));qp.set('chunk',String(Math.min(500,remaining)));
        }
        const result=await api('features?'+qp,{signal:controller.signal});
        if(rec.epoch!==epoch||!S.records.has(src.id))return;
        pages++;
        const fresh=[];
        for(const f of result.features||[]){const key=str(f.id??JSON.stringify(f.geometry));
          if(seen.has(key))continue;seen.add(key);
          if(features.length<FEATURE_CAP){features.push(f);fresh.push(f)}else limited=true;
        }
        geometryLimited=geometryLimited||!!result.geometry_simplified;
        limited=limited||!!result.limited;
        if(fresh.length){
          prepare();rec.features=features.slice();
          draw2d(fresh,src,rec.group);draw3d(fresh,src,rec);rec.status='loading';updateCounts();
        }
        if(src.mode==='offline')break;
        more=!!result.has_more&&result.next_offset!=null;
        const next=Number(result.next_offset);
        if(more&&!(next>offset)){limited=true;unfinished=true;break}
        offset=next;
        // Avoid unbounded requests even when a provider yields only rejected
        // diameter-filtered features or keeps repeating empty result pages.
        if(pages>=24){limited=true;unfinished=true;break}
      }
      if(src.mode==='offline'||limited||unfinished)break;
    }
    if(rec.epoch!==epoch||!S.records.has(src.id))return;
    if(!replaced)prepare();
    rec.features=features;rec.cache=bounds;rec.limited=limited||unfinished;
    rec.status=rec.limited?'partial':'ready';
    bind3d();
  }catch(error){if(rec.epoch!==epoch||error.name==='AbortError')return;rec.status='error';S.errors[src.id]=str(error.message)}finally{if(rec.epoch===epoch)updateCounts()}})();
  work.push(task);
 }
 updateCounts();await Promise.all(work);
}
function render(){const card=$(ID);if(!card)return;const d=state();const body=card.querySelector('.infra-body');
 card.querySelector('.infra-head .infra-status').textContent=(S.mode==='online'?'ONLINE':'OFFLINE');
 body.hidden=S.collapsed;card.querySelector('.infra-chevron').textContent=S.collapsed?'▸':'▾';
 card.querySelectorAll('.infra-mode button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===S.mode)));
 const list=$('takInfraCategoriesI685');list.replaceChildren();
 for(const cat of d.categories){if(cat.hidden)continue;const layers=d.layers.filter(x=>x.category_id===cat.id&&x.mode===S.mode&&!x.hidden);
  const box=D.createElement('section');box.className='infra-category';
  const head=D.createElement('button');head.className='infra-cat-head';head.type='button';head.innerHTML=`<span class="name">${esc(cat.label)}</span><span class="infra-cat-count">${layers.length}</span><span>${S.open.has(cat.id)?'▾':'▸'}</span>`;
  head.onclick=()=>{if(S.open.has(cat.id))S.open.delete(cat.id);else S.open.add(cat.id);localStorage.setItem('takmap.infra.open.i686',JSON.stringify([...S.open]));render()};box.append(head);
  if(S.open.has(cat.id)){const controls=D.createElement('div');controls.className='infra-actions';
   const button=(label,fn)=>{const b=D.createElement('button');b.type='button';b.className='infra-btn';b.textContent=label;b.onclick=fn;controls.append(b)};
   button(S.mode==='online'?'+ Add Service':'+ Import',()=>S.mode==='online'?addService(cat.id):importFile(cat.id));
   button('Rename',()=>renameCategory(cat));button(cat.builtin?'Hide':'Delete',()=>manageCategory(cat));box.append(controls);
   if(!layers.length){const empty=D.createElement('div');empty.className='infra-empty';empty.textContent=S.mode==='online'?'No services configured. Add a source to display features.':'No offline datasets. Import GIS files or download from Online mode.';box.append(empty)}
   for(const src of layers){const row=D.createElement('div');row.className='infra-layer';
    const checkbox=D.createElement('input');checkbox.type='checkbox';checkbox.checked=!!src.enabled;checkbox.title='Show layer';checkbox.onchange=()=>void changeLayer(src.id,checkbox.checked);
    const name=D.createElement('div');name.innerHTML=`<div class="infra-layer-name">${esc(src.name)}</div><div class="infra-layer-meta" data-infra-counter="${esc(src.id)}">${esc(labelCounts(src))}</div>`;
    row.style.borderLeftColor=colorFor(src);
    const tools=D.createElement('div');tools.className='infra-tools';
    const picker=D.createElement('input');picker.type='color';picker.className='infra-color';picker.value=colorFor(src);picker.title='Layer color';picker.setAttribute('aria-label','Color for '+src.name);
    picker.onchange=()=>void submitManage({op:'layer-color',id:src.id,color:picker.value},{recolorId:src.id});tools.append(picker);
    const reset=D.createElement('button');reset.type='button';reset.className='infra-reset-color';reset.textContent='Reset';reset.title='Restore default layer color';
    reset.onclick=()=>void submitManage({op:'layer-color',id:src.id,color:''},{recolorId:src.id});tools.append(reset);
    const act=(label,fn)=>{const b=D.createElement('button');b.type='button';b.className='infra-btn';b.textContent=label;b.onclick=fn;tools.append(b)};
    if(S.mode==='online')act('↓',()=>downloadSource(src));else act('Export',()=>exportLayer(src));
    act('✕',()=>deleteLayer(src));row.append(checkbox,name,tools);box.append(row);
   }
  }list.append(box);
 }
 const jobList=$('takInfraJobsI685');jobList.replaceChildren();
 for(const job of d.jobs.filter(j=>!['complete','canceled'].includes(j.status)).slice(0,6)){
  const box=D.createElement('div');box.className='infra-job';const src=layerById(job.source_id);
  box.innerHTML=`<div>${esc(src?.name||job.source_id)} <strong>${esc(job.status)}</strong></div><div class="infra-progress">${Number(job.received).toLocaleString()} features saved${job.error?' · '+esc(job.error):''}</div>`;
  const act=D.createElement('button');act.className='infra-btn';act.textContent=job.status==='interrupted'?'Resume':'Cancel';act.onclick=()=>void jobOperation(job.status==='interrupted'?'download-resume':'download-cancel',job.id);box.append(act);jobList.append(box);
 }
 $('takInfraMinI685').value=String(S.min);updateCounts();
}
async function load(){try{S.data=await api('state');if(!S.initialized)S.initialized=true;render()}catch(e){message(str(e.message),true)}}
async function submitManage(payload,opts={}){try{S.data=await post('manage',payload);render();
 if(opts.recolorId){const src=layerById(opts.recolorId);if(src)recolor(src);updateCounts()}
 else if(payload.op==='category-rename'){updateCounts()}
 else schedule();
 }catch(e){message(e.message,true)}}
async function changeLayer(id,enabled){await submitManage({op:'layer-enable',id,enabled})}
function renameCategory(cat){const name=prompt('Infrastructure category name',cat.label);if(name?.trim())void submitManage({op:'category-rename',id:cat.id,name:name.trim()})}
function manageCategory(cat){if(cat.builtin){if(confirm('Hide '+cat.label+' from both Online and Offline? You can restore it later.'))void submitManage({op:'category-hide',id:cat.id,hidden:true});return}
 if(confirm('Delete empty custom category '+cat.label+'? Move or delete its layers first.'))void submitManage({op:'category-delete',id:cat.id})}
function addCategory(){const name=prompt('New infrastructure category');if(name?.trim())void submitManage({op:'category-create',name:name.trim()})}
function addService(category_id){const name=prompt('Name for the online GIS layer');if(!name?.trim())return;
 const url=prompt('Public HTTPS ArcGIS FeatureServer layer URL (ending /FeatureServer/0)');if(!url)return;
 const kind=prompt('Layer kind: sewer, point, line, other','other')||'other';void submitManage({op:'layer-add',category_id,name,url,kind})}
function deleteLayer(src){const builtIn=!src.id.startsWith('source-')&&!src.id.startsWith('import-')&&!src.id.startsWith('offline-');if(!confirm((builtIn?'Hide built-in service ':'Delete infrastructure layer ')+src.name+'?'+(builtIn?' It can be restored later.':' Offline geometry will be removed permanently.')))return;void submitManage({op:builtIn?'layer-hide':'layer-delete',id:src.id,hidden:true})}
const fileInput=()=>D.getElementById('takInfraImportInputI685');
function importFile(category){const f=fileInput();f.dataset.category=category;f.value='';f.click()}
async function onFile(){const input=fileInput(),file=input.files?.[0];if(!file)return;
 const category=input.dataset.category||'water';const name=prompt('Imported dataset name',file.name.replace(/\.[^.]+$/,''));if(name===null)return;
 const kind=prompt('Type for layer filtering: sewer, point, line, other','other')||'other';message('Importing '+file.name+'…');
 const params=new URLSearchParams({category,name:name||file.name,kind,filename:file.name});
 try{const r=await fetch(API+'import?'+params,{method:'POST',body:file,credentials:'same-origin'});const j=await r.json();if(!r.ok||!j.ok)throw new Error(j.error||'Import failed');message('Imported '+j.count.toLocaleString()+' features.');await load();schedule()}catch(e){message(e.message,true)}
}
function exportLayer(src){const types=['gpkg','geojson','zip','kml','kmz'];const type=prompt('Export format: gpkg, geojson, zip (Shapefile), kml, kmz','gpkg');if(!type)return;if(!types.includes(type.toLowerCase()))return message('Unsupported export format',true);
 const url=API+'export?'+new URLSearchParams({layer:src.id,format:type.toLowerCase()});W.location.href=url;
}
async function downloadSource(src){const b=bbox();if(!b)return message('Map bounds unavailable',true);
 if(!confirm('Download '+src.name+' for '+(S.drawBounds?'your drawn area':'the current map area')+'? No TAK Map bandwidth cap will be applied.'))return;
 try{const r=await post('jobs',{op:'download-start',source_id:src.id,bbox:b});message('Downloading '+src.name+' to server storage…');S.drawBounds=null;await load()}catch(e){message(e.message,true)}
}
async function jobOperation(op,id){try{await post('jobs',{op,id});await load()}catch(e){message(e.message,true)}}
function drawRegion(){const m=getMap();if(!m||!W.L)return message('2D map not available',true);S.drawBounds=null;S.drawFirst=null;
 if(S.drawLayer){m.removeLayer(S.drawLayer);S.drawLayer=null}message('Click two opposite corners of the area to download.');
 function capture(ev){if(routeBusy())return;const ll=ev.latlng;if(!S.drawFirst){S.drawFirst=ll;return}
  m.off('click',capture);const a=S.drawFirst;S.drawBounds=[Math.min(a.lng,ll.lng),Math.min(a.lat,ll.lat),Math.max(a.lng,ll.lng),Math.max(a.lat,ll.lat)];S.drawFirst=null;
  S.drawLayer=L.rectangle([[S.drawBounds[1],S.drawBounds[0]],[S.drawBounds[3],S.drawBounds[2]]],{color:'#8dc2df',weight:2,fillOpacity:.07,interactive:false}).addTo(m);message('Custom area selected for the next infrastructure download.');
 }
 m.on('click',capture)
}
function install(){if($(ID))return true;const side=$('sidebar');if(!side)return false;const b=D.createElement('section');b.className='panel';b.id=ID;
 b.innerHTML=`<header class="infra-head" role="button" tabindex="0" aria-label="Collapse Infrastructure"><span class="infra-title">INFRASTRUCTURE</span><span class="infra-status">ONLINE</span><span class="infra-chevron">▾</span></header><div class="infra-body"><div class="infra-mode"><button type="button" data-mode="online">ONLINE</button><button type="button" data-mode="offline">OFFLINE</button></div><div class="infra-help">Online and offline layers can display together. This switch only changes which layers you manage.</div>
 <div class="infra-origin"><label><input type="checkbox" id="takInfraOnlineVisibleI686"> Online on map</label><label><input type="checkbox" id="takInfraOfflineVisibleI686"> Offline on map</label></div><div class="infra-row between"><span class="infra-help">Sewer minimum diameter</span><select id="takInfraMinI685"><option value="36">36 in +</option><option value="48">48 in +</option><option value="60">60 in +</option><option value="0">All sizes</option></select></div><div id="takInfraCategoriesI685"></div><div class="infra-actions"><button type="button" class="infra-btn" data-action="category">+ Category</button><button type="button" class="infra-btn" data-action="restore">Restore hidden</button><button type="button" class="infra-btn" data-action="refresh">Refresh</button><button type="button" class="infra-btn" data-action="draw">Draw area</button></div><div id="takInfraJobsI685"></div><div class="infra-message" id="takInfraMessageI685">Select layers to view infrastructure.</div><input id="takInfraImportInputI685" type="file" accept=".geojson,.json,.gpkg,.zip,.kml,.kmz" hidden></div>`;
 const basemap=Array.from(side.children).find(el=>/^basemap$/i.test(el.querySelector('h2')?.textContent?.trim()||''));
 if(basemap?.nextSibling)side.insertBefore(b,basemap.nextSibling);else side.append(b);
 b.querySelector('.infra-head').onclick=()=>{S.collapsed=!S.collapsed;localStorage.setItem('takmap.infra.collapsed.i685',S.collapsed?'1':'0');render()};
 b.querySelector('.infra-head').onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();b.querySelector('.infra-head').click()}};
 b.querySelectorAll('.infra-mode button').forEach(button=>button.onclick=()=>{const next=button.dataset.mode;if(S.mode===next)return;S.mode=next;localStorage.setItem('takmap.infra.mode.i686',next);render();updateCounts()});
 b.querySelector('#takInfraMinI685').onchange=e=>{S.min=Number(e.target.value);localStorage.setItem('takmap.infra.min.i685',str(S.min));clearMap();schedule()};
 for(const [mode,key] of [['online','takInfraOnlineVisibleI686'],['offline','takInfraOfflineVisibleI686']]){
   const cb=$(key);cb.checked=mode==='online'?S.onlineVisible:S.offlineVisible;
   cb.onchange=()=>{S[mode+'Visible']=cb.checked;localStorage.setItem('takmap.infra.'+mode+'Visible.i686',cb.checked?'1':'0');schedule()};
 }

 b.querySelector('[data-action="category"]').onclick=addCategory;
 b.querySelector('[data-action="restore"]').onclick=()=>{const hidden=state().categories.filter(c=>c.hidden).map(c=>({id:c.id,name:c.label,op:'category-hide'})).concat(state().layers.filter(x=>x.hidden).map(x=>({id:x.id,name:x.name,op:'layer-hide'})));if(!hidden.length)return message('No hidden categories or layers.');const name=prompt('Restore a category or layer: '+hidden.map(x=>x.name).join(', '),hidden[0].name);const item=hidden.find(c=>c.name.toLowerCase()===str(name).toLowerCase());if(item)void submitManage({op:item.op,id:item.id,hidden:false})};
 b.querySelector('[data-action="refresh"]').onclick=()=>{void load();schedule()};
 b.querySelector('[data-action="draw"]').onclick=drawRegion;fileInput().onchange=onFile;
 void load();return true
}
function boot(){if(!install())return;const m=getMap();if(m&&m!==S.map){S.map=m;m.on('moveend zoomend',schedule);schedule()}bind3d()}
function tick(){if(!S.initialized)void boot();else{boot();const v=viewer();if(v!==S.viewer){S.viewer=null;bind3d();for(const id of [...S.records.keys()])removeRecord(id);schedule()}}}
if(D.readyState==='loading')D.addEventListener('DOMContentLoaded',()=>setTimeout(tick,250),{once:true});else setTimeout(tick,250);
let attempts=0;const probe=setInterval(()=>{tick();if(S.map&&S.initialized||++attempts>160)clearInterval(probe)},250);
S.jobsTimer=setInterval(()=>{if($(ID)&&!D.hidden)void load()},5000);
W.TakMapInfrastructureI686={state:S,install,refreshFeatures,clearMap,exportLayer,selectFeature,boxParts};
})(window,document);
