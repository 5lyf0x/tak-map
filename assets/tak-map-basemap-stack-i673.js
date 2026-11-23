/* TAK Map i678: canonical 2D basemap stack. No delayed styling or row-wide dragging. */
(function(W,D){'use strict';
const LEGACY_KEY='takmap.basemap.blend.i673.v1';
const API='/api/tak-map/basemap-stack-i699';
const userPrefs={key:'',revision:0,loaded:false,pending:false,timer:null,saveInProgress:false,dirty:false,hydrating:false,legacy:undefined};
const MODES=['normal','multiply','screen','overlay','soft-light','hard-light','darken','lighten','difference','map-details','terrain-relief','contour-emphasis'];
const CUSTOM=new Set(MODES.slice(9));
const MODE_LABEL={normal:'Normal',multiply:'Multiply',screen:'Screen',overlay:'Overlay','soft-light':'Soft Light','hard-light':'Hard Light',darken:'Darken',lighten:'Lighten',difference:'Difference','map-details':'Map Details','terrain-relief':'Terrain Relief','contour-emphasis':'Contour Emphasis'};
const state={ready:false,expanded:true,order:[],enabled:new Set(),opacity:{},blend:{},tone:{},detail:{},layers:new Map(),pane:null,map:null,initialized:false,menu:null,drag:null,unsupported:{},tileErrors:{},catalogSignature:''};
const get=id=>(typeof config!=='undefined'&&Array.isArray(config?.basemaps)?config.basemaps:[]).find(b=>b.id===id);
// The basemap definition may change while its imported ID stays the same.
const sourceFingerprint=b=>JSON.stringify([b?.url,b?.minZoom,b?.maxZoom,b?.minNativeZoom,b?.maxNativeZoom,b?.bounds,b?.partial,!!(b?.tms??b?.options?.tms),b?.attribution]);
const all=()=>((typeof config!=='undefined'&&Array.isArray(config?.basemaps))?config.basemaps:[]).filter(b=>b&&b.id&&b.url);
const pct=(n,d=100)=>Math.max(0,Math.min(200,Number.isFinite(+n)?+n:d));
const clamp=n=>Math.min(100,pct(n));
const h=s=>String(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function snapshot(){return {order:state.order.slice(),enabled:[...state.enabled],opacity:state.opacity,blend:state.blend,tone:state.tone,detail:state.detail,expanded:state.expanded};}
function localKey(){return 'takmap.basemap.user.i699.'+userPrefs.key;}
function status(message, migrate=false){
 const host=D.getElementById('takBasemapBlendI673');if(!host)return;
 let box=D.getElementById('takBasemapSyncStatusI699');
 if(!box){box=D.createElement('div');box.id='takBasemapSyncStatusI699';host.insertAdjacentElement('beforebegin',box);}
 box.textContent=message||'';box.hidden=!message;
 if(migrate){const btn=D.createElement('button');btn.type='button';btn.textContent='Import this browser’s previous settings';
 btn.onclick=()=>{const legacy=userPrefs.legacy; if(legacy){restore('',legacy);apply();render();userPrefs.dirty=true;persist();}status('Migrating saved settings to this account…');};box.append(btn);}
}
function persist(){
 if(!userPrefs.loaded||!userPrefs.key||userPrefs.hydrating)return;
 userPrefs.dirty=true;
 try{localStorage.setItem(localKey(),JSON.stringify(snapshot()));}catch(_){}
 clearTimeout(userPrefs.timer);userPrefs.timer=setTimeout(saveUser,550);
}
async function saveUser(){
 if(!userPrefs.loaded||!userPrefs.dirty||userPrefs.saveInProgress)return;
 userPrefs.saveInProgress=true;userPrefs.dirty=false;
 const data=snapshot();
 try{
  const r=await fetch(API,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},
   body:JSON.stringify({revision:userPrefs.revision,preferences:data})});
  const j=await r.json();
  if(r.status===409||j.conflict){status('Basemap preferences were updated on another device. Loading latest settings…');await loadUser(true);return;}
  if(!r.ok||!j.ok)throw Error(j.error||'Save failed');
  userPrefs.revision=j.revision;status('');
 }catch(e){userPrefs.dirty=true;status('Basemap settings not synchronized: '+String(e.message||e));}
 finally{userPrefs.saveInProgress=false;if(userPrefs.dirty&&userPrefs.loaded){clearTimeout(userPrefs.timer);userPrefs.timer=setTimeout(saveUser,12000);}}
}
function restore(id,saved){
 const ids=all().map(b=>b.id),present=new Set(ids);
 saved=saved||{};const unique=a=>[...new Set((Array.isArray(a)?a:[]).filter(x=>typeof x==='string'&&x.length<181))];
 // Retain missing catalog IDs and their settings; only visible IDs render.
 state.order=unique([...unique(saved.order),...ids]);
 state.enabled=new Set(unique(Array.isArray(saved.enabled)?saved.enabled:[id]).filter(x=>!x.startsWith('__')));
 if(!ids.some(x=>state.enabled.has(x))&&ids.length)state.enabled.add(present.has(id)?id:ids[0]);
 for(const v of state.order){state.opacity[v]=clamp(saved.opacity?.[v]??100);state.blend[v]=MODES.includes(saved.blend?.[v])?saved.blend[v]:'normal';
 const t=saved.tone?.[v]||{};state.tone[v]={brightness:pct(t.brightness),contrast:pct(t.contrast),saturation:pct(t.saturation)};
 const d=saved.detail?.[v]||{};state.detail[v]={strength:clamp(d.strength??75),threshold:clamp(d.threshold??65)};}
 state.expanded=saved.expanded!==false;state.initialized=true;
}
async function loadUser(refresh=false){
 try{
  const r=await fetch(API,{credentials:'same-origin',cache:'no-store'});
  if(!r.ok)throw Error('HTTP '+r.status);
  const j=await r.json();if(!j.ok||!j.user_key)throw Error(j.error||'User preferences not available');
  userPrefs.key=j.user_key;userPrefs.revision=j.revision;userPrefs.loaded=true;
  if(j.preferences){userPrefs.hydrating=true;try{restore('',j.preferences);apply();render();userPrefs.dirty=false;}finally{userPrefs.hydrating=false;}status('');}
  else if(!refresh){
   try{userPrefs.legacy=JSON.parse(localStorage.getItem(LEGACY_KEY)||'null');}catch(_){}
   if(userPrefs.legacy&&userPrefs.legacy.order?.length)status('Previous browser settings can be imported for this account.',true);
   else status('');
  }
  return j;
 }catch(e){status('Basemap settings temporarily unavailable from server: '+String(e.message||e));return null;}
}
// Reconcile the canonical layer stack against the server's changing catalog.
// Imported Custom XML / Gateway layers arrive after the first boot. Never reset
// existing order, enablement, blend, tone or opacity when they are discovered.
function syncCatalog(){
 if(!state.initialized)return false;
 const catalog=all(),ids=catalog.map(b=>b.id),valid=new Set(ids);
 const signature=JSON.stringify(catalog.map(b=>[b.id,sourceFingerprint(b)])),catalogChanged=signature!==state.catalogSignature;state.catalogSignature=signature;
 if(!ids.length)return false;
 const old=state.order;
 const order=[...old,...ids.filter(id=>!old.includes(id))];
 const removed=old.filter(id=>!valid.has(id));
 const added=order.filter(id=>!old.includes(id));
 const orphaned=[...state.layers.keys()].filter(id=>!valid.has(id));
 const enabledBefore=[...state.enabled];
 const enabled=enabledBefore.slice();
 if(!enabled.some(id=>valid.has(id))){
   const preferred=(typeof config!=='undefined'&&config?.default_basemap)||'';
   const fallback=valid.has(preferred)?preferred:(catalog.find(b=>!b.importedBasemap)?.id||ids[0]);
   if(fallback)enabled.push(fallback);
 }
 const changed=catalogChanged||added.length>0||orphaned.length>0||
   enabledBefore.length!==enabled.length||enabledBefore.some(id=>!enabled.includes(id));
 if(!changed)return false;
 state.order=order;state.enabled=new Set(enabled);
 for(const id of added){
   state.opacity[id]=clamp(state.opacity[id]??100);
   state.blend[id]=MODES.includes(state.blend[id])?state.blend[id]:'normal';
   state.tone[id]=state.tone[id]||{brightness:100,contrast:100,saturation:100};
   state.detail[id]=state.detail[id]||{strength:75,threshold:65};
 }
 for(const id of removed){
   const layer=state.layers.get(id);
   if(layer){try{if(state.map?.hasLayer(layer))state.map.removeLayer(layer)}catch(_){}state.layers.delete(id)}
   // Preserve server preferences for temporarily unavailable catalog IDs.
 }
 if(state.ready)apply();else persist();
 render();
 return true;
}
function primaryChanged(id){try{if(id&&typeof config!=='undefined'){config.last_basemap=id;config.default_basemap=id}}catch(_){}// i699: Do not write legacy global map_prefs.json; saved user stack is authoritative.
 try{if(typeof updateOfflineSourceText==='function')updateOfflineSourceText();if(typeof refreshTerrain3DBaseLayer==='function'&&typeof terrain3DActive!=='undefined'&&terrain3DActive)refreshTerrain3DBaseLayer()}catch(_){}}
// Real pixel processing, never a CSS-only cosmetic placeholder. Cross-origin tiles
// must explicitly grant CORS; if not, mark the mode unavailable for that source.
function processPixels(data,mode,settings){const p=data.data,orig=new Uint8ClampedArray(p),w=data.width,hgt=data.height;const strength=settings.strength/100,threshold=settings.threshold/100;for(let y=0;y<hgt;y++)for(let x=0;x<w;x++){
 const i=(y*w+x)*4,r=orig[i],g=orig[i+1],b=orig[i+2],v=(.299*r+.587*g+.114*b)/255;
 const t=x>0?i-4:i,up=y>0?i-w*4:i;
 const edge=(Math.abs(r-orig[t])+Math.abs(g-orig[t+1])+Math.abs(b-orig[t+2])+Math.abs(r-orig[up])+Math.abs(g-orig[up+1])+Math.abs(b-orig[up+2]))/1530;
 let a=1;
 if(mode==='map-details') {const whiteness=Math.min(r,g,b)/255;const colorful=(Math.max(r,g,b)-Math.min(r,g,b))/255;const details=Math.max(edge*3.3,colorful*.85,(1-whiteness)*.58);a=Math.max(0,Math.min(1,(details-(threshold*.6))/(.18+(.8-threshold*.6))));}
 else if(mode==='terrain-relief'){a=Math.min(1,Math.abs(v-threshold)*2.5*strength);const shade=Math.round(v*255);p[i]=shade;p[i+1]=shade;p[i+2]=shade;}
 else if(mode==='contour-emphasis'){a=Math.max(0,Math.min(1,(edge*3.5-threshold*.45)*3));}
 p[i+3]=Math.round(orig[i+3]*a*(mode==='terrain-relief'?1:strength));
 }return data}
// i003: only local MBTiles use interactive loading and a small tile buffer.
// Native zoom bounds avoid HTTP requests above the downloaded zoom range.
function isOffline(b){return b?.type==='mbtiles'||String(b?.id||'').startsWith('offline_')}
function offlineViewportBounds(b){if(!isOffline(b)||!b.bounds||!W.L?.latLngBounds)return null;
 try{const a=String(b.bounds).split(',').map(Number);if(a.length!==4||!a.every(Number.isFinite)||a[0]>=a[2]||a[1]>=a[3]||a[1]<-90||a[3]>90)return null;
 return W.L.latLngBounds([[a[1],a[0]],[a[3],a[2]]]).pad(.05);}catch(_){return null}}
function layerOptions(b,custom){const off=isOffline(b);const opts={
 minZoom:Number(b.minZoom??0),maxZoom:Number(b.maxZoom??19),
 attribution:b.attribution||'',tms:!!(b.tms??b.options?.tms),pane:'takBasemapI673',
 updateWhenIdle:off?false:true,updateInterval:off?200:undefined,
 keepBuffer:off?(custom?2:3):(custom?5:8)
 };if(off){opts.minNativeZoom=Number(b.minNativeZoom??b.minZoom??0);opts.maxNativeZoom=Number(b.maxNativeZoom??b.maxZoom??19);
 const bounds=offlineViewportBounds(b);if(bounds)opts.bounds=bounds;}
 return opts}
// Pixel-heavy custom modes use a bounded one-tile-per-frame processing queue.
// CSS Blend modes continue to use the fast native Leaflet tile path.
const customTasks=[];let customTaskScheduled=false;
function pumpCustomTasks(){if(customTaskScheduled)return;customTaskScheduled=true;
 const tick=()=>{let ran=false;while(customTasks.length&&!ran){const task=customTasks.shift();if(task.tile._takCanceled)continue;ran=true;task.run();}
 if(customTasks.length)W.requestAnimationFrame?W.requestAnimationFrame(tick):setTimeout(tick,16);else customTaskScheduled=false;};
 if(W.requestAnimationFrame)W.requestAnimationFrame(tick);else setTimeout(tick,16)}
function customLayer(b,id){const cls=W.L.TileLayer.extend({createTile:function(coords,done){
 const canvas=D.createElement('canvas');canvas.width=256;canvas.height=256;
 const ctx=canvas.getContext('2d',{willReadFrequently:true});const image=new Image();image.crossOrigin='anonymous';
 let finished=false;const finish=err=>{if(finished)return;finished=true;done(err||null,canvas)};
 canvas._takCanceled=false;canvas._takCancel=()=>{canvas._takCanceled=true;image.onload=null;image.onerror=null;try{image.src=''}catch(_){}};
 image.onload=()=>{customTasks.push({tile:canvas,run:()=>{if(canvas._takCanceled)return;try{
 ctx.drawImage(image,0,0,256,256);const bytes=ctx.getImageData(0,0,256,256);
 ctx.putImageData(processPixels(bytes,state.blend[id],state.detail[id]),0,0);delete state.unsupported[id];finish();
 }catch(e){state.unsupported[id]='Tile pixel access blocked by source CORS or decoding restrictions';
 if(state.menu?.id===id)queueMicrotask(repaintMenu);ctx.clearRect(0,0,256,256);finish(e)}
 }});pumpCustomTasks()};
 image.onerror=()=>{if(canvas._takCanceled)return;state.unsupported[id]='Tile image could not be loaded with cross-origin permission';
 if(state.menu?.id===id)queueMicrotask(repaintMenu);finish(Error(state.unsupported[id]))};
 image.src=this.getTileUrl(coords);return canvas}});
 const lyr=new cls(b.url,layerOptions(b,true));lyr.on('tileunload',e=>{try{e.tile?._takCancel?.()}catch(_){}});return lyr}
function layerOf(b){const mode=state.blend[b.id],signature=sourceFingerprint(b),existing=state.layers.get(b.id);
 if(existing&&existing._takMode===mode&&existing._takSourceFingerprint===signature)return existing;
 if(existing&&state.map?.hasLayer(existing))state.map.removeLayer(existing);
 const lyr=CUSTOM.has(mode)?customLayer(b,b.id):W.L.tileLayer(b.url,{...layerOptions(b,false),opacity:1});
 lyr._takMode=mode;lyr._takSourceFingerprint=signature;state.layers.set(b.id,lyr);
 if(typeof lyr.on==='function'){
 state.tileErrors[b.id]=0;
 const status=()=>{const el=D.querySelector(`[data-base-tile-status-i696="${CSS.escape(b.id)}"]`);if(!el)return;
 if(state.tileErrors[b.id]<2){el.hidden=true;el.textContent='';return;}
 let message='Tile source unavailable · check source URL';
 if(isOffline(b)){
  const saved=offlineViewportBounds(b),view=state.map?.getBounds?.();
  message=saved&&view&&!saved.intersects(view)?'Outside downloaded map coverage':(b.partial?'Tile pending in partial pack or unavailable':'Offline tile missing or loading failed');
 }
 el.textContent=message;el.hidden=false;};
 lyr.on('tileerror',()=>{state.tileErrors[b.id]++;status()});
 lyr.on('tileload',()=>{if(state.tileErrors[b.id]){state.tileErrors[b.id]=0;status()}});
 }
 return lyr}
function decorate(id,lyr){const node=lyr.getContainer?.();if(!node)return;node.style.mixBlendMode=CUSTOM.has(state.blend[id])?'normal':state.blend[id];const t=state.tone[id]||{brightness:100,contrast:100,saturation:100};node.style.filter=`brightness(${t.brightness}%) contrast(${t.contrast}%) saturate(${t.saturation}%)`;node.style.pointerEvents='none'}
function apply(){if(!state.map)return;try{if(typeof baseLayer!=='undefined'&&baseLayer&&state.map.hasLayer(baseLayer)&&![...state.layers.values()].includes(baseLayer))state.map.removeLayer(baseLayer)}catch(_){}const ids=state.order.filter(id=>state.enabled.has(id)&&get(id));if(!ids.length)return;for(const [id,lyr] of state.layers)if(!ids.includes(id)&&state.map.hasLayer(lyr))state.map.removeLayer(lyr);ids.slice().reverse().forEach(id=>{const lyr=layerOf(get(id));lyr.setOpacity(clamp(state.opacity[id])/100);if(!state.map.hasLayer(lyr))lyr.addTo(state.map)});ids.forEach((id,i)=>{const l=layerOf(get(id));l.setZIndex(200+ids.length-i);decorate(id,l)});try{activeBasemap=ids[0];baseLayer=layerOf(get(ids.at(-1)));const s=D.getElementById('basemapSelect');if(s)s.value=ids[0]}catch(_){}persist()}
function selectSingle(id,opts){opts=opts||{};if(!state.ready||!get(id))return false;if(!state.initialized)restore(id);if(!opts.skipSave){state.enabled.clear();state.enabled.add(id);state.order=[id,...state.order.filter(x=>x!==id)];if(typeof basemapUserChanged!=='undefined')basemapUserChanged=true;primaryChanged(id)}apply();render();return true}
function changeEnabled(id,on){if(on)state.enabled.add(id);else{if(state.enabled.size<=1)return;state.enabled.delete(id)}closeMenu();apply();render();primaryChanged(state.order.find(x=>state.enabled.has(x)))}
function setOpacity(id,n){state.opacity[id]=clamp(n);const lyr=state.layers.get(id);if(lyr)lyr.setOpacity(state.opacity[id]/100);persist();const o=D.querySelector(`[data-basemap-percent-i673="${CSS.escape(id)}"]`);if(o)o.textContent=state.opacity[id]+'%';const s=D.querySelector(`[data-base-opacity-i673="${CSS.escape(id)}"]`);if(s)s.style.setProperty('--tak-soft-pill-pct',state.opacity[id]+'%')}
function move(from,to){if(from===to||to<0||to>=state.order.length)return;const o=state.order.splice(from,1)[0];state.order.splice(to,0,o);closeMenu();apply();render();primaryChanged(state.order.find(x=>state.enabled.has(x)))}
let hostMenu=null;function closeMenu(){if(state.menu?.anchor?.focus&&state.menu?.returnFocus)state.menu.anchor.focus({preventScroll:true});state.menu=null;if(hostMenu){hostMenu.remove();hostMenu=null}}
function rangeMarkup(id,field,label,amount,maximum=200){return `<label class="tak-pop-slider-i678"><span>${label}<output>${amount}%</output></span><input class="tak-soft-pill-i678" type="range" min="0" max="${maximum}" value="${amount}" data-tone-i678="${h(id)}" data-field-i678="${field}" style="--tak-soft-pill-pct:${amount/maximum*100}%"></label>`}
function menuContent(id,which){if(which==='blend')return `<div class="tak-pop-head-i678">BLEND MODE</div><div class="tak-pop-modes-i678">${MODES.map(mode=>`<button type="button" data-mode-i678="${mode}" class="${state.blend[id]===mode?'selected':''}">${h(MODE_LABEL[mode])}</button>`).join('')}</div>${CUSTOM.has(state.blend[id])?`<div class="tak-custom-adjust-i678"><small>${state.blend[id]==='contour-emphasis'?'EXPERIMENTAL':'CUSTOM'} · raster pixel processing</small>${rangeMarkup(id,'strength','Strength',state.detail[id].strength,100)}${rangeMarkup(id,'threshold','Threshold',state.detail[id].threshold,100)}</div>`:''}${state.unsupported[id]?`<p class="tak-pop-error-i678">${h(state.unsupported[id])}. This mode cannot render this tile source without CORS.</p>`:''}`;
 const t=state.tone[id]||{brightness:100,contrast:100,saturation:100};return `<div class="tak-pop-head-i678">TONE · ${h(get(id)?.label)}</div>${rangeMarkup(id,'brightness','Brightness',t.brightness)}${rangeMarkup(id,'contrast','Contrast',t.contrast)}${rangeMarkup(id,'saturation','Saturation',t.saturation)}<button type="button" class="tak-pop-reset-i678">Reset Tone</button>`}
function positionMenu(){if(!state.menu||!hostMenu)return;const a=state.menu.anchor;if(!D.contains(a)){closeMenu();return}const r=a.getBoundingClientRect(),size=hostMenu.getBoundingClientRect(),vw=W.innerWidth,vh=W.innerHeight;const width=Math.max(128,Math.min(190,r.width));hostMenu.style.width=width+'px';const x=Math.max(6,Math.min(vw-width-6,r.left));hostMenu.style.left=x+'px';const y=r.bottom+4;hostMenu.style.top=(y+Math.min(340,size.height)>vh-5?Math.max(5,r.top-Math.min(340,size.height)-4):y)+'px';}
function repaintMenu(){if(!state.menu||!hostMenu)return;hostMenu.innerHTML=menuContent(state.menu.id,state.menu.which);bindMenu();positionMenu()}
function updateMode(id,mode){
 if(!get(id)||!MODES.includes(mode))return;
 state.blend[id]=mode;
 delete state.unsupported[id];
 apply(); // apply() persists the new mode and updates the real Leaflet layer
 // The rows are not rerendered when the popover is open. Refresh the visible
 // label in place: previously only the title changed, leaving “Blend Screen”.
 const btn=D.querySelector(`[data-base-menu-i678="blend:${CSS.escape(id)}"]`);
 if(btn){
   btn.title='Blend: '+MODE_LABEL[mode];
   const value=btn.querySelector('span');
   if(value)value.textContent=MODE_LABEL[mode];
 }
 // For custom raster modes the popover stays open to show Strength/Threshold.
 // Retain scroll position so a lower menu selection doesn't jump to the top.
 if(state.menu?.id===id&&state.menu?.which==='blend'){
   const before=hostMenu?.querySelector('.tak-pop-modes-i678');
   const scrollTop=before?.scrollTop||0;
   repaintMenu();
   const after=hostMenu?.querySelector('.tak-pop-modes-i678');
   if(after)after.scrollTop=scrollTop;
 }
}
function bindMenu(){if(!state.menu||!hostMenu)return;const {id,which}=state.menu;// Keep Blend open for every selection (including built-in modes).
 // updateMode repaints the selected row in place while preserving its scroll offset.
 hostMenu.querySelectorAll('[data-mode-i678]').forEach(b=>b.addEventListener('click',()=>{if(which==='blend')updateMode(id,b.dataset.modeI678)}));hostMenu.querySelectorAll('[data-field-i678]').forEach(input=>{input.addEventListener('input',()=>{const field=input.dataset.fieldI678,n=+input.value;const custom=field==='strength'||field==='threshold';const obj=custom?(state.detail[id]||(state.detail[id]={strength:75,threshold:65})):(state.tone[id]||(state.tone[id]={brightness:100,contrast:100,saturation:100}));obj[field]=custom?clamp(n):pct(n);input.closest('label')?.querySelector('output')?.replaceChildren(D.createTextNode(obj[field]+'%'));input.style.setProperty('--tak-soft-pill-pct',(custom?obj[field]:obj[field]/2)+'%');if(custom){const lyr=state.layers.get(id);if(lyr?.redraw)lyr.redraw()}else decorate(id,state.layers.get(id));persist()})});hostMenu.querySelector('.tak-pop-reset-i678')?.addEventListener('click',()=>{state.tone[id]={brightness:100,contrast:100,saturation:100};decorate(id,state.layers.get(id));persist();repaintMenu()})}
function openMenu(id,which,anchor){if(state.menu?.id===id&&state.menu?.which===which){closeMenu();return}closeMenu();state.menu={id,which,anchor,returnFocus:false};hostMenu=D.createElement('div');hostMenu.id='takBasemapPopoverI678';hostMenu.setAttribute('role','dialog');hostMenu.setAttribute('aria-label',which==='blend'?'Blend mode':'Tone adjustments');D.body.appendChild(hostMenu);repaintMenu()}
function render(){const host=D.getElementById('takBasemapBlendI673');if(!host)return;closeMenu();const b=state.order.map(get).filter(Boolean);host.innerHTML=`<button type="button" class="tak-base-toggle-i673" aria-expanded="${state.expanded}"><span>BASEMAP LAYERS <small>${state.enabled.size} active</small></span><span>${state.expanded?'⌃':'⌄'}</span></button>`+(state.expanded?`<div class="tak-base-list-i673">${b.map(x=>`<div class="tak-base-item-i673" data-base-i673="${h(x.id)}"><div class="tak-base-line-i673"><span class="tak-base-handle-i673" draggable="true" tabindex="0" role="button" aria-label="Drag ${h(x.label)} to reorder" title="Drag to reorder">⠿</span><label><input type="checkbox" data-base-check-i673="${h(x.id)}" ${state.enabled.has(x.id)?'checked':''}><span>${h(x.label)}</span></label></div>${state.enabled.has(x.id)?`<small data-base-tile-status-i696="${h(x.id)}" ${state.tileErrors[x.id]>=2?'':'hidden'} style="margin-left:24px;color:#ffb09e;font-size:10px">${state.tileErrors[x.id]>=2?(isOffline(x)?'Offline tile missing or outside saved coverage':'Tile source unavailable · check source URL'):''}</small>`:""}${state.enabled.has(x.id)?`<div class="tak-base-opacity-i673"><input class="tak-soft-pill-i678" type="range" min="0" max="100" step="1" data-base-opacity-i673="${h(x.id)}" value="${state.opacity[x.id]}" style="--tak-soft-pill-pct:${state.opacity[x.id]}%"><output data-basemap-percent-i673="${h(x.id)}">${state.opacity[x.id]}%</output></div><div class="tak-base-controls-i678"><button data-base-menu-i678="blend:${h(x.id)}" title="Blend: ${h(MODE_LABEL[state.blend[x.id]])}" aria-haspopup="dialog">Blend <span>${h(MODE_LABEL[state.blend[x.id]])}</span>⌄</button><button data-base-menu-i678="tone:${h(x.id)}" aria-haspopup="dialog">Tone ⌄</button></div>`:''}</div>`).join('')}</div>`:'');host.querySelector('.tak-base-toggle-i673')?.addEventListener('click',()=>{state.expanded=!state.expanded;persist();render()});host.querySelectorAll('[data-base-check-i673]').forEach(e=>e.addEventListener('change',()=>changeEnabled(e.dataset.baseCheckI673,e.checked)));host.querySelectorAll('[data-base-opacity-i673]').forEach(e=>e.addEventListener('input',()=>setOpacity(e.dataset.baseOpacityI673,e.value)));host.querySelectorAll('[data-base-menu-i678]').forEach(button=>button.addEventListener('click',()=>{const [which,id]=button.dataset.baseMenuI678.split(':');openMenu(id,which,button)}));host.querySelectorAll('.tak-base-handle-i673').forEach(grip=>{grip.addEventListener('dragstart',e=>{state.drag=grip.closest('[data-base-i673]')?.dataset.baseI673;e.dataTransfer.effectAllowed='move';e.stopPropagation()});grip.addEventListener('dragend',()=>{state.drag=null})});host.querySelectorAll('.tak-base-item-i673').forEach(row=>{row.addEventListener('dragover',ev=>{if(state.drag)ev.preventDefault()});row.addEventListener('drop',ev=>{if(!state.drag)return;ev.preventDefault();const a=state.order.indexOf(state.drag),z=state.order.indexOf(row.dataset.baseI673);state.drag=null;if(a>=0&&z>=0)move(a,z)})})}
function boot(){const m=W.map||W.takLeafletMap;if(!m||typeof config==='undefined'||!config?.basemaps?.length)return false;state.map=m;state.ready=true;state.pane=m.getPane('takBasemapI673')||m.createPane('takBasemapI673');state.pane.style.zIndex='220';state.pane.style.isolation='isolate';const sel=D.getElementById('basemapSelect');if(!sel)return false;let host=D.getElementById('takBasemapBlendI673');if(!host){host=D.createElement('section');host.id='takBasemapBlendI673';sel.insertAdjacentElement('afterend',host)}if(!state.initialized)restore(typeof activeBasemap!=='undefined'&&activeBasemap?activeBasemap:sel.value||config.default_basemap);if(typeof baseLayer!=='undefined'&&baseLayer&&m.hasLayer(baseLayer))m.removeLayer(baseLayer);state.catalogSignature=JSON.stringify(all().map(b=>[b.id,sourceFingerprint(b)]));apply();render();if(!userPrefs.requested){userPrefs.requested=true;loadUser();}return true}
const css=D.createElement('style');css.id='takBaseStyleI678';css.textContent=`
#takBasemapBlendI673{margin:8px 0 10px;border:1px solid #374958;border-radius:10px;overflow:hidden;color:#e5eff6}#takBasemapBlendI673 button{cursor:pointer;color:inherit}#takBasemapBlendI673 .tak-base-toggle-i673{width:100%;display:flex;justify-content:space-between;align-items:center;border:0;background:#1b303d;padding:9px 11px;font-weight:750;font-size:12px}#takBasemapBlendI673 small{font-weight:400;color:#b4c8d0;margin-left:6px}#takBasemapBlendI673 .tak-base-list-i673{max-height:330px;overflow:auto;background:#12212d}#takBasemapBlendI673 .tak-base-item-i673{padding:7px 8px;border-top:1px solid #ffffff13}#takBasemapBlendI673 .tak-base-line-i673{display:flex;align-items:center;gap:5px}#takBasemapBlendI673 .tak-base-line-i673 label{display:flex;align-items:center;gap:8px;min-width:0;flex:1;cursor:pointer;font-size:12px}#takBasemapBlendI673 .tak-base-line-i673 label span{white-space:normal;overflow-wrap:anywhere}#takBasemapBlendI673 .tak-base-handle-i673{cursor:grab;color:#8299a7;font-size:17px;user-select:none}#takBasemapBlendI673 .tak-base-handle-i673:active{cursor:grabbing}#takBasemapBlendI673 .tak-base-opacity-i673{margin:4px 0 0 22px;display:flex;gap:8px;align-items:center}#takBasemapBlendI673 output{font-size:11px;color:#bfccd3;min-width:37px;text-align:right}
#takBasemapBlendI673 .tak-base-controls-i678{margin:6px 0 0 22px;display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:7px}#takBasemapBlendI673 .tak-base-controls-i678 button{height:27px;display:flex;align-items:center;justify-content:center;gap:4px;min-width:0;border:1px solid #425c70;border-radius:20px;background:#162b39;font-size:10px;font-weight:750;overflow:hidden;white-space:nowrap;padding:0 6px}#takBasemapBlendI673 .tak-base-controls-i678 button span{max-width:60%;overflow:hidden;text-overflow:ellipsis;color:#a6c8db;font-size:9px}
.tak-soft-pill-i678{appearance:none!important;-webkit-appearance:none!important;min-width:0;width:100%;height:24px!important;margin:0;background:transparent!important;cursor:pointer;outline:none}.tak-soft-pill-i678::-webkit-slider-runnable-track{height:10px;border-radius:99px;background:linear-gradient(90deg,#4f6878 0%,#4f6878 var(--tak-soft-pill-pct),#283c48 var(--tak-soft-pill-pct),#283c48 100%);border:1px solid #3b5262}.tak-soft-pill-i678::-moz-range-track{height:10px;border-radius:99px;background:linear-gradient(90deg,#4f6878 0%,#4f6878 var(--tak-soft-pill-pct),#283c48 var(--tak-soft-pill-pct),#283c48 100%);border:1px solid #3b5262}.tak-soft-pill-i678::-webkit-slider-thumb{appearance:none;-webkit-appearance:none;width:16px;height:16px;margin-top:-4px;border-radius:50%;background:#dceaf0;border:3px solid #263a47;box-shadow:0 1px 3px #0008}.tak-soft-pill-i678::-moz-range-thumb{width:16px;height:16px;border-radius:50%;background:#dceaf0;border:3px solid #263a47}.tak-soft-pill-i678:focus-visible{outline:2px solid #96cde4;outline-offset:2px;border-radius:20px}
#takBasemapPopoverI678{position:fixed;z-index:9500;box-sizing:border-box;max-height:min(350px,65vh);overflow-y:auto;border:1px solid #59849a;border-radius:7px;background:#142b3af8;color:#e9f3f8;padding:7px;box-shadow:0 12px 30px #0009;font:11px Manrope,Arial,sans-serif}#takBasemapPopoverI678 button{color:inherit;cursor:pointer}#takBasemapPopoverI678 .tak-pop-head-i678{font-size:9px;letter-spacing:.08em;color:#afcbd9;padding:4px 0 7px;font-weight:800}#takBasemapPopoverI678 .tak-pop-modes-i678{max-height:196px;overflow-y:auto;display:flex;flex-direction:column}#takBasemapPopoverI678 .tak-pop-modes-i678 button{border:0;background:transparent;text-align:left;padding:8px 5px;border-radius:4px;font-size:10px;white-space:normal}#takBasemapPopoverI678 .tak-pop-modes-i678 button.selected,#takBasemapPopoverI678 .tak-pop-modes-i678 button:hover{background:#365a73}#takBasemapPopoverI678 .tak-pop-slider-i678{display:block;padding:6px 0}#takBasemapPopoverI678 .tak-pop-slider-i678 span{display:flex;justify-content:space-between;font-size:10px}#takBasemapPopoverI678 .tak-pop-slider-i678 input{display:block;width:100%}#takBasemapPopoverI678 .tak-pop-reset-i678{width:100%;margin-top:6px;padding:7px;border:1px solid #5b7a8b;background:#294657;border-radius:5px}#takBasemapPopoverI678 .tak-custom-adjust-i678{border-top:1px solid #476276;margin-top:7px;padding-top:5px}#takBasemapPopoverI678 .tak-custom-adjust-i678 small{font-size:9px;color:#adc6d3}#takBasemapPopoverI678 .tak-pop-error-i678{color:#ffad95;font-size:9px;line-height:1.4}
`;D.head.appendChild(css);
D.addEventListener('pointerdown',e=>{if(state.menu&&!hostMenu?.contains(e.target)&&!state.menu.anchor?.contains(e.target))closeMenu()},true);D.addEventListener('keydown',e=>{if(e.key==='Escape'&&state.menu)closeMenu()},true);W.addEventListener('resize',positionMenu);D.addEventListener('scroll',positionMenu,true);
W.TakMapBaseStackI673={state,selectSingle,render,boot,syncCatalog,changeEnabled,setOpacity,move,processPixels,version:'i678'};
let n=0;const retry=setInterval(()=>{if(boot()||++n>60)clearInterval(retry)},250);
})(window,document);
