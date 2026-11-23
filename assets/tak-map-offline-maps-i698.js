/* TAK Map v1.4.0-i698 — state-border offline download UI on existing sidebar. */
(function(w,d){'use strict';
const ID='i698', $=id=>d.getElementById(id);
let geojson=null, area='view', regionLayer=null, cesiumEntities=[], estimateTimer=null, chosenSource='', sourceList=[], attached=false;
let authoritativeSources=null, sourceRequest=null, sourceLoading=false, sourceError='', sourceLastFetch=0;
let activeJobId='', latestEstimate=null;
function escaped(value){return String(value==null?'':value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function number(n){return Math.round(Number(n)||0).toLocaleString('en-US');}
function size(n){n=Number(n)||0;return n>1073741824?(n/1073741824).toFixed(2)+' GB':n>1048576?(n/1048576).toFixed(1)+' MB':n>1024?(n/1024).toFixed(1)+' KB':n+' B';}
function cfg(){try{return typeof config!=='undefined'&&config||w.config||{};}catch(_){return w.config||{};}}
function theMap(){try{return typeof map!=='undefined'&&map||w.map||null;}catch(_){return w.map||null;}}
function selectedFeature(){return geojson&&geojson.features&&geojson.features.find(f=>f.id===area)||null;}
function menuOptions(){return [{id:'view',label:'Current View'},{id:'draw',label:'Draw Area'},...(geojson?geojson.features.map(f=>({id:f.id,label:f.properties.name})):[])];}
function clearHighlight(){try{if(regionLayer&&theMap())theMap().removeLayer(regionLayer);}catch(_){ }regionLayer=null;
 try{const v=typeof terrain3DViewer!=='undefined'?terrain3DViewer:w.terrain3DViewer;if(v&&v.entities)cesiumEntities.forEach(ent=>v.entities.remove(ent));}catch(_){}cesiumEntities=[];}
function renderHighlight(f){clearHighlight();const m=theMap();if(!f||!m||!w.L)return;
 try{regionLayer=L.geoJSON(f,{style:{color:'#ff8b44',weight:3,opacity:.95,fillColor:'#ffb45f',fillOpacity:.035},interactive:false});regionLayer.addTo(m);
 const pane=regionLayer.getBounds();if(pane&&pane.isValid()){
  if(f.id==='AK')m.setView([62.8,-150],4);
  else if(f.id==='HI')m.setView([20.6,-157],6);
  else m.fitBounds(pane,{padding:[25,25],maxZoom:9,animate:false});
 }
 }catch(e){console.warn('Offline region outline',e);}
 try{const v=typeof terrain3DViewer!=='undefined'?terrain3DViewer:w.terrain3DViewer;const C=w.Cesium;if(v&&C&&v.entities){
 for(const poly of f.geometry.coordinates){for(const ring of poly){if(ring.length<2)continue;
 const flat=[];for(const xy of ring){flat.push(xy[0],xy[1]);}const ent=v.entities.add({polyline:{positions:C.Cartesian3.fromDegreesArray(flat),width:2.3,material:C.Color.ORANGE,clampToGround:true}});cesiumEntities.push(ent);
 }}v.scene&&v.scene.requestRender&&v.scene.requestRender();}}
 catch(e){console.warn('Offline 3D region outline',e);}
}
function refreshOptions(){const select=$('offlineAreaSelectI698');if(!select)return;
 const term=String($('offlineAreaSearchI698')?.value||'').trim().toLowerCase();
 const all=menuOptions();const matched=all.filter(o=>!term||o.label.toLowerCase().includes(term));
 if(!matched.some(o=>o.id===area))matched.unshift(all.find(o=>o.id===area)||all[0]);
 select.innerHTML=matched.map(o=>`<option value="${escaped(o.id)}">${escaped(o.label)}</option>`).join('');select.value=area;
}
function boundsFromFeature(f){const a=[Infinity,Infinity,-Infinity,-Infinity];
 for(const poly of f.geometry.coordinates)for(const ring of poly)for(const [lon,lat] of ring){a[0]=Math.min(a[0],lon);a[1]=Math.min(a[1],lat);a[2]=Math.max(a[2],lon);a[3]=Math.max(a[3],lat);}
 return {west:a[0],south:a[1],east:a[2],north:a[3]};}
function updateSelection(next){area=next;latestEstimate=null;clearHighlight();
 const f=selectedFeature();const m=theMap();const helper=$('offlineAreaHelpI698');
 if(f){
   try{if(typeof stopOfflineAreaDraw==='function')stopOfflineAreaDraw();}catch(_){}
   if(m){try{if(typeof offlineAreaRect!=='undefined'&&offlineAreaRect){m.removeLayer(offlineAreaRect);offlineAreaRect=null;}}catch(_){}}
   try{offlineDownloadBounds=boundsFromFeature(f);}catch(_){}
   renderHighlight(f);
   if(helper)helper.textContent=f.properties.name+' · geographic boundary preview · tiles clipped to polygon';
   try{if(typeof updateOfflineBoundsText==='function')updateOfflineBoundsText();}catch(_){}
 }else if(next==='draw'){
   try{offlineDownloadBounds=null;}catch(_){}
   try{if(typeof startOfflineAreaDraw==='function')startOfflineAreaDraw();}catch(_){}
   if(helper)helper.textContent='Drag on the map to draw a custom download rectangle.';
 }else{
   try{if(typeof useCurrentViewForOffline==='function')useCurrentViewForOffline();}catch(_){}
   if(helper)helper.textContent='Uses your currently visible map bounds.';
 }
 refreshOptions();schedule();
}
// i699: Load sources AFTER the authenticated configuration is available.
// i698 rendered this select once at DOMContentLoaded, often before the async
// main init() fetched /api/tak-map/config. An empty list then stayed empty.
function getSources(){
 let rows=authoritativeSources===null?(cfg().offline_download_sources||[]):authoritativeSources;
 if(!Array.isArray(rows))rows=[];
 return rows.filter(b=>b&&b.id&&b.label);
}
function source(){return getSources().find(s=>String(s.id)===String(chosenSource))||null;}
function renderSources(){
 sourceList=getSources();const s=$('offlineSourceSelectI698');if(!s)return;
 if(!sourceList.some(x=>String(x.id)===String(chosenSource))){
  let id='';try{id=String(typeof activeBasemap!=='undefined'?activeBasemap:'');}catch(_){}
  chosenSource=sourceList.find(x=>String(x.id)===id)?.id||sourceList[0]?.id||'';
 }
 if(sourceList.length){
  s.innerHTML=sourceList.map(o=>`<option value="${escaped(o.id)}">${escaped(o.label)}</option>`).join('');
  s.value=chosenSource;s.disabled=false;s.title='';
 }else{
  chosenSource='';
  const label=sourceLoading?'Loading basemap sources…':sourceError?'Unable to load basemaps — click to retry':'No compatible basemap sources configured';
  s.innerHTML=`<option value="">${escaped(label)}</option>`;
  s.value='';s.disabled=false;s.title=sourceError||label;
 }
 s.setAttribute('aria-busy',sourceLoading?'true':'false');
}
async function refreshSources(force=false){
 if(sourceRequest)return sourceRequest;
 if(!force&&authoritativeSources!==null){renderSources();return authoritativeSources;}
 sourceLoading=true;sourceError='';sourceLastFetch=Date.now();renderSources();
 sourceRequest=(async()=>{
  const r=await fetch('/api/tak-map/config',{cache:'no-store',credentials:'same-origin'});
  if(!r.ok)throw new Error(r.status===401?'Sign in to load basemaps':'Basemap catalog HTTP '+r.status);
  const data=await r.json();
  if(!data||data.ok===false||!Array.isArray(data.offline_download_sources))
    throw new Error('Basemap source catalog missing from server configuration');
  authoritativeSources=data.offline_download_sources;
  sourceLoading=false;sourceError='';renderSources();schedule();
  return authoritativeSources;
 })().catch(err=>{
  sourceLoading=false;sourceError=String(err?.message||err);
  renderSources();
  const box=$('offlineEstimate');
  if(box&&!getSources().length)box.textContent='Unable to load basemap sources: '+sourceError;
  return getSources();
 }).finally(()=>{sourceRequest=null;});
 return sourceRequest;
}
function maybeRefreshSources(){
 if(!attached)return;
 // Refresh after a new import or when the app has been idle, but avoid an
 // HTTP request on every click while a source catalog request is in flight.
 if(authoritativeSources===null||sourceError||Date.now()-sourceLastFetch>5000)
  refreshSources(true);
}
function payload(){let minz=Number($('offlineMinZoom')?.value||8),maxz=Number($('offlineMaxZoom')?.value||13);
 if(!Number.isFinite(minz))minz=8;if(!Number.isFinite(maxz))maxz=13;
 return {source_id:chosenSource,area_id:selectedFeature()?area:'',
  bounds:(typeof offlineDownloadBounds!=='undefined'?offlineDownloadBounds:null),min_zoom:Math.min(minz,maxz),max_zoom:Math.max(minz,maxz),
  name:($('offlinePackName')?.value||'').trim()};}
async function request(url,body){const response=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),cache:'no-store'});
 const j=await response.json();if(!response.ok||!j.ok)throw new Error(j.error||'HTTP '+response.status);return j;}
function schedule(){clearTimeout(estimateTimer);estimateTimer=setTimeout(()=>estimate(true),400);}
async function estimate(silent){const box=$('offlineEstimate');try{
 const p=payload();if(!p.source_id)throw new Error('Select a configured basemap source first.');
 if(!p.area_id&&!p.bounds)throw new Error('Select or draw an area first.');
 if(box&&!silent)box.textContent='Estimating polygon-clipped tiles…';
 const j=await request('/api/tak-map/offline-estimate',p);latestEstimate=j;
 if(box)box.innerHTML=`<div class="offline-i698-estimate"><div class="offline-i698-metric"><span>Selected tiles</span><b>${number(j.tile_count)}</b></div><div class="offline-i698-metric"><span>Estimated storage</span><b>${size(j.estimated_bytes)}</b></div><div class="offline-i698-metric"><span>Internal download batches</span><b>${number(j.internal_jobs)} × up to ${number(j.max_tiles)}</b></div><div class="offline-region-helper">One offline map when finished; failed tiles recoverable separately.</div></div>`;
 return j;
 }catch(e){latestEstimate=null;if(box)box.innerHTML='<span class="danger">'+escaped(e.message||e)+'</span>';return null;}}
async function download(){const status=$('offlineJobStatus');try{
 const j=await estimate(false);if(!j)return;
 if(!j.tile_count)throw new Error('Selected area has no tiles at these zoom levels.');
 if(status)status.textContent='Starting download…';
 const result=await request('/api/tak-map/offline-download',payload());activeJobId=result.job.id;
 if(status)status.textContent='Downloading '+number(j.tile_count)+' tiles in '+number(j.internal_jobs)+' internal batches…';
 if(typeof pollOfflineJob==='function')pollOfflineJob(activeJobId);
 }catch(e){if(status)status.textContent='Download could not start: '+(e.message||e);}}
async function recover(id,action){const status=$('offlineJobStatus');try{
 if(action==='retry'){
  const result=await request('/api/tak-map/offline-retry-i698',{id});activeJobId=result.job.id;
  if(status)status.textContent='Retrying only missing tiles…';
  if(typeof pollOfflineJob==='function')pollOfflineJob(activeJobId);
 }else{
  await request('/api/tak-map/offline-finish-i698',{id});
  if(status)status.textContent='Offline map accepted with missing tiles; recovery list preserved.';
  if(typeof refreshOfflineMaps==='function')await refreshOfflineMaps(true);
 }
 }catch(e){if(status)status.textContent='Retry/Finish failed: '+(e.message||e);}}
// Rename updates the server catalog only: the MBTiles file, map ID, and tiles
// remain unchanged, so existing Apply/Send references continue to work.
function addRenameControl(card,m){
 if(!card||card.querySelector('.offline-rename-action'))return;
 const state=String(m.download_status||'').trim().toLowerCase();
 if(m.partial||m.resume_available||(String(m.created_by||'').toLowerCase()==='download'?state!=='complete':!['','complete'].includes(state)))return;
 const actions=card.querySelector('.row'),title=card.querySelector('.offline-card-title b');
 if(!actions||!title)return;
 const btn=d.createElement('button');btn.type='button';btn.className='layer-button offline-rename-action';btn.textContent='Rename';
 btn.setAttribute('aria-label','Rename '+String(m.name||m.filename||'offline map'));
 actions.insertBefore(btn,actions.children[1]||null);
 btn.addEventListener('click',()=>{
  if(card.querySelector('.offline-rename-editor'))return;
  const editor=d.createElement('div');editor.className='offline-rename-editor';
  const field=d.createElement('input');field.type='text';field.maxLength=120;field.value=String(m.name||m.filename||'');
  field.setAttribute('aria-label','New offline map name');field.autocomplete='off';
  const row=d.createElement('div');row.className='offline-rename-buttons';
  const save=d.createElement('button');save.type='button';save.className='layer-button';save.textContent='Save';
  const cancel=d.createElement('button');cancel.type='button';cancel.className='layer-button';cancel.textContent='Cancel';
  const error=d.createElement('div');error.className='offline-rename-error';error.setAttribute('role','alert');
  const close=()=>{editor.remove();btn.hidden=false;};
  cancel.addEventListener('click',close);
  async function submit(){
   const raw=field.value;const name=raw.trim().replace(/\s+/g,' ');
   if(!name||name.length>120||/[\/\\\x00-\x1f\x7f-\x9f]/.test(raw)){
    error.textContent='Enter 1–120 characters without slashes.';field.focus();return;
   }
   save.disabled=true;cancel.disabled=true;field.disabled=true;error.textContent='Saving…';
   try{
    const r=await fetch('/api/tak-map/offline-rename-i001',{method:'POST',credentials:'same-origin',cache:'no-store',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:m.id,name})});
    const j=await r.json();if(!r.ok||!j.ok)throw new Error(j.error||'HTTP '+r.status);
    const scrollBox=$('offlineMapRows');const scroll=scrollBox?.scrollTop||0;
    if(typeof refreshOfflineMaps==='function')await refreshOfflineMaps(true);
    else {title.textContent=j.map?.name||name;close();}
    if(scrollBox)scrollBox.scrollTop=scroll;
   }catch(e){error.textContent='Rename failed: '+String(e.message||e);save.disabled=false;cancel.disabled=false;field.disabled=false;field.focus();}
  }
  save.addEventListener('click',submit);
  field.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();submit();}else if(e.key==='Escape'){e.preventDefault();close();}});
  row.append(save,cancel);editor.append(field,row,error);
  const meta=card.querySelector('small');if(meta)meta.insertAdjacentElement('beforebegin',editor);else title.parentElement.insertAdjacentElement('afterend',editor);
  btn.hidden=true;field.focus();field.select();
 });
}
function addRowSchemeControl(card,m){
 if(!card||card.querySelector('.offline-row-scheme-i003')||String(m.created_by||'').toLowerCase()==='download')return;
 const actions=card.querySelector('.row');if(!actions)return;
 const holder=d.createElement('label');holder.className='offline-row-scheme-i003';holder.textContent='Tile rows: ';
 const input=d.createElement('select');input.setAttribute('aria-label','Imported map tile row order');
 for(const scheme of ['tms','xyz']){const o=d.createElement('option');o.value=scheme;o.textContent=scheme.toUpperCase();input.append(o)}
 input.value=String(m.tile_row_scheme||'tms').toLowerCase()==='xyz'?'xyz':'tms';
 const error=d.createElement('span');error.className='offline-row-scheme-error-i003';
 input.title='Select XYZ only when an imported MBTiles uses XYZ tile rows rather than standard TMS';
 input.addEventListener('change',async()=>{input.disabled=true;error.textContent='Saving…';
 try{const r=await fetch('/api/tak-map/offline-row-scheme-i003',{method:'POST',cache:'no-store',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:m.id,tile_row_scheme:input.value})});
 const j=await r.json();if(!r.ok||!j.ok)throw Error(j.error||'HTTP '+r.status);
 if(typeof refreshOfflineMaps==='function')await refreshOfflineMaps(true);else error.textContent='Saved';
 }catch(e){input.value=String(m.tile_row_scheme||'tms').toLowerCase()==='xyz'?'xyz':'tms';error.textContent=String(e.message||e)}finally{input.disabled=false;}});
 holder.append(input,error);actions.insertAdjacentElement('afterend',holder);
}
function decorateCards(){let maps=[];try{maps=(typeof offlineMaps!=='undefined'&&offlineMaps)||[]}catch(_){};
 maps=typeof w.takMapSortOfflineMapPacksI001==='function'?w.takMapSortOfflineMapPacksI001(maps):maps;
 const cards=[...d.querySelectorAll('#offlineMapRows .offline-card')];
 cards.forEach((card,i)=>{const m=maps[i];if(!m)return;
  addRenameControl(card,m);
  addRowSchemeControl(card,m);
  const failed=Number(m.failed_tile_count)||0;
  if(m.internal_jobs>1&&!card.querySelector('.offline-i698-part')){const small=card.querySelector('small');if(small)small.insertAdjacentHTML('beforeend',`<span class="offline-i698-part"> · ${number(m.internal_jobs)} internal batches · one map</span>`);}
  if(failed>0&&!m.partial&&!m.resume_available&&!card.querySelector('.offline-i698-recovery')){
   const badge=card.querySelector('.offline-status-chip');if(badge){badge.textContent='Incomplete';badge.classList.remove('good');badge.classList.add('offline-i698-warning');}
   const box=d.createElement('div');box.className='offline-i698-recovery';
   const text=d.createElement('div');text.className='offline-i698-recovery-head';text.textContent=number(failed)+' failed tiles · recoverable';box.append(text);
   const control=d.createElement('button');control.type='button';control.className='layer-button';control.textContent='Retry/Finish';box.append(control);
   const menu=d.createElement('div');menu.hidden=true;menu.className='offline-i698-recovery-menu';
   const retry=d.createElement('button');retry.type='button';retry.textContent='Retry Failed Tiles';retry.className='layer-button';retry.onclick=()=>recover(m.id,'retry');
   const finish=d.createElement('button');finish.type='button';finish.textContent='Finish As Is';finish.className='layer-button';finish.onclick=()=>recover(m.id,'finish');
   control.onclick=()=>{menu.hidden=!menu.hidden;};menu.append(retry,finish);box.append(menu);card.append(box);
  }
 });}
function wrapRender(){if(w.renderOfflineMapRows&&w.renderOfflineMapRows.__i698)return;
 if(typeof w.renderOfflineMapRows!=='function')return;
 const original=w.renderOfflineMapRows;
 const wrapped=function(){const ret=original.apply(this,arguments);try{decorateCards();}catch(e){console.warn('offline-map card decoration',e);}return ret;};
 wrapped.__i698=true;w.renderOfflineMapRows=wrapped;}
// Startup loader creates the main core renderer asynchronously, AFTER this
// file's DOMContentLoaded handler may have run. Reconnect when it is ready;
// otherwise clicking Refresh redraws the list without the Rename actions.
function reconcileOfflineMapCards(){
 try{wrapRender();decorateCards();}catch(e){console.warn('Offline map card startup hook',e);}
}
async function loadRegions(){try{
 const response=await fetch('/api/tak-map/offline-areas-i698',{cache:'no-store'});
 const data=await response.json();if(!response.ok||!data.ok||data.geojson?.features?.length!==52)throw new Error('Region catalog unavailable');
 geojson=data.geojson;refreshOptions();updateSelection(area);
 }catch(e){const helper=$('offlineAreaHelpI698');if(helper)helper.textContent='Unable to load U.S. state boundaries: '+e.message;}}
function attach(){if(attached||!$('offlinePackName')||!$('offlineMinZoom')||!$('offlineMaxZoom'))return false;
 const pack=$('offlinePackName');const parent=pack.closest('.panel');if(!parent)return false;
 const header=parent.querySelector('.subgroup-title');if(header&&/create offline map/i.test(header.textContent))header.remove();
 const oldArea=d.querySelector('button[onclick*="useCurrentViewForOffline"]')?.closest('.row');
 if(!oldArea)return false;
 oldArea.style.display='none';
 const box=d.createElement('div');box.id='offlineAreaSelectorI698';
 box.innerHTML='<label for="offlineAreaSelectI698">Download Area</label><input id="offlineAreaSearchI698" type="search" placeholder="Search 50 states and California regions…" autocomplete="off" aria-label="Search offline download areas"><select id="offlineAreaSelectI698" aria-label="Download area"></select><div id="offlineAreaHelpI698" class="offline-region-helper">Select Current View, Draw Area, or a state/region.</div><div class="offline-source-wrap"><label for="offlineSourceSelectI698">Basemap Source</label><select id="offlineSourceSelectI698" aria-label="Basemap source"></select></div>';
 const title=parent.querySelector('h2');if(title)title.insertAdjacentElement('afterend',box);else oldArea.insertAdjacentElement('afterend',box);
 parent.classList.add('tak-offline-i699');
 const coords=$('offlineBoundsText')?.closest('.row');if(coords)coords.style.display='none';
 const name=$('offlinePackName');if(name){name.placeholder='Optional offline map name';const nameLabel=d.createElement('label');nameLabel.textContent='Map Name (Optional)';nameLabel.setAttribute('for','offlinePackName');name.insertAdjacentElement('beforebegin',nameLabel);box.insertAdjacentElement('afterend',nameLabel);nameLabel.insertAdjacentElement('afterend',name);}
 const preview=[...parent.querySelectorAll('button')].find(b=>b.getAttribute('onclick')?.includes('previewOfflineZoom'));if(preview){preview.textContent='Preview Max';}
 const refresh=[...parent.querySelectorAll('button')].find(b=>b.getAttribute('onclick')?.includes('refreshOfflineMaps'));if(refresh)refresh.textContent='Refresh Offline Maps';
 const originalSource=$('offlineSourceText')?.closest('.row');if(originalSource)originalSource.style.display='none';
 $('offlineAreaSelectI698').onchange=e=>updateSelection(e.target.value);
 $('offlineAreaSearchI698').oninput=refreshOptions;
 $('offlineSourceSelectI698').onchange=e=>{chosenSource=e.target.value;schedule();};
 $('offlineSourceSelectI698').addEventListener('focus',maybeRefreshSources);
 $('offlineSourceSelectI698').addEventListener('pointerdown',maybeRefreshSources);
 const button=[...parent.querySelectorAll('button')].find(b=>b.getAttribute('onclick')?.includes('startOfflineDownload'));
 if(button){button.textContent='Download';button.removeAttribute('onclick');button.onclick=download;}
 for(const z of ['offlineMinZoom','offlineMaxZoom']){
  const input=$(z);input.removeAttribute('onchange');input.removeAttribute('oninput');input.addEventListener('change',schedule);input.addEventListener('input',schedule);
 }
 wrapRender();reconcileOfflineMapCards();renderSources();refreshOptions();attached=true;refreshSources(true);loadRegions();
 return true;}
function setup(){if(attach())return;let attempts=0;const retry=setInterval(()=>{if(attach()||++attempts>25)clearInterval(retry);},250);}
const diagnostic=()=>({version:ID,attached,regions:geojson?.features?.length||0,options:menuOptions().length,
 selectedArea:area,selectedSource:chosenSource,sources:sourceList.length,sourceLoading,sourceError,outlinePresent:!!regionLayer,lastTileEstimate:latestEstimate?.tile_count||0,
 downloadLabel:[...d.querySelectorAll('#offlinePackName')].length?'Download':null});
w.TakMapOfflineMapsI698=Object.freeze({diagnostic,setArea:updateSelection,estimate,download,recover,loadRegions,refreshSources});
w.addEventListener('takmap:shell-ready-i553',reconcileOfflineMapCards);
w.addEventListener('takmap:runtime-ready-i553',reconcileOfflineMapCards);
w.addEventListener('takmap:optional-data-ready-i553',reconcileOfflineMapCards);
w.addEventListener('takmap:runtime-ready',maybeRefreshSources);
w.addEventListener('focus',maybeRefreshSources);
if(w.__takMapShellReadyI553)reconcileOfflineMapCards();
if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',setup,{once:true});else setup();
})(window,document);
