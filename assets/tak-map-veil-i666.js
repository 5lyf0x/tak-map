(()=>{'use strict';
const V='1.4.0-i668', D=document, $=id=>D.getElementById(id), esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])), path='/api/tak-map/veil/';
let state={config:{},nodes:[],counts:{},objectsCount:0}, found=[], selected=new Set(), mode='', layers=new Map(), lastPoll=0;
let pairIsAuto=false,pairNode=null,authBusy=false;
function map(){return window.map&&typeof window.map.getContainer==='function'?window.map:null}
async function api(endpoint,data){const r=await fetch(path+endpoint,{method:data===undefined?'GET':'POST',credentials:'same-origin',cache:'no-store',headers:{'Content-Type':'application/json'},...(data===undefined?{}:{body:JSON.stringify(data)})});const j=await r.json();if(!r.ok||j.ok===false)throw Error(j.error||'Request failed ('+r.status+')');return j}
// i694: Infrastructure follows BASEMAP and VEIL follows Infrastructure.
// Anchor to stable controls instead of text headings; do not fight the Infrastructure
// ordering observer or move the same card every 4 seconds.
function place(){
 const card=$('takVeilCardI665'),sidebar=$('sidebar');if(!card||!sidebar)return;
 const infra=$('takInfraCardI685');
 const panels=[...sidebar.querySelectorAll(':scope > .panel')];
 const base=[$('basemapSelect'),$('takBasemapBlendI673')].map(el=>el?.closest?.('.panel')).find(el=>el?.parentElement===sidebar)
    || panels.find(p=>/basemap/i.test((p.querySelector('h2,.tv-head strong')||{}).textContent||''));
 const anchor=infra?.parentElement===sidebar?infra:base;
 if(anchor&&anchor!==card&&card.previousElementSibling!==anchor)anchor.insertAdjacentElement('afterend',card);
}
// Other sidebar components initialize asynchronously; restore order when children move,
// without waiting for the VEIL poll and without touching collapse or toggle state.
function watchSidebarOrder(){
 const sidebar=$('sidebar');if(!sidebar||window.__takVeilOrderObserverI668)return;
 let scheduled=false;
 const observer=new MutationObserver(()=>{
  if(scheduled)return;scheduled=true;
  Promise.resolve().then(()=>{scheduled=false;place()});
 });
 observer.observe(sidebar,{childList:true});
 window.__takVeilOrderObserverI668=observer;
}
function pbutton(name,fn){const b=D.createElement('button');b.type='button';b.className='tv-button';b.textContent=name;b.addEventListener('click',fn);return b}
function message(text){$('tvModalErrorI665').textContent=text||''}
function open(name){mode=name;$('tvModalI665').classList.add('open');$('tvModalTitleI665').textContent={discover:'Discover VEIL Nodes',add:'Add VEIL Node',settings:'VEIL Settings'}[name]||name;$('tvModalContentI665').innerHTML='';$('tvModalActionsI665').replaceChildren();message('');if(name==='discover')discoverDialog();if(name==='add')addDialog();if(name==='settings')settingsDialog()}
function close(){
 if(mode==='pair'&&pairIsAuto&&pairNode){try{sessionStorage.setItem('takVeilDismissed:'+pairNode.nodeId,String(pairNode.apiAuthGeneration||0))}catch(_){}}
 const password=$('tvPasswordI666');if(password)password.value='';
 $('tvModalI665').classList.remove('open');mode='';pairNode=null;pairIsAuto=false;
}
function actions(...buttons){$('tvModalActionsI665').replaceChildren(...buttons)}
function discoveredList(){const host=$('tvListI665');if(!host)return;host.innerHTML='';for(const n of found){const label=D.createElement('label');label.className='tv-check';const check=D.createElement('input');check.type='checkbox';check.checked=selected.has(n.nodeId);check.disabled=!!n.added;check.addEventListener('change',()=>{if(check.checked)selected.add(n.nodeId);else selected.delete(n.nodeId);selectedCount()});const text=D.createElement('span');text.innerHTML='<b>'+esc(n.name)+'</b><div class="tv-muted">'+esc(n.host)+':'+n.port+' · '+esc(n.nodeVersion||'VEIL')+(n.added?' · Already added':'')+'</div>';label.append(check,text);host.append(label)}if(!found.length)host.textContent='No nodes discovered. Check Avahi/LAN connectivity or add manually.';selectedCount()}
function selectedCount(){const b=$('tvSelectedI665');if(b){b.textContent='Add Selected ('+selected.size+')';b.disabled=selected.size===0}}
async function scan(){message('');$('tvListI665').textContent='Scanning local mDNS…';selected.clear();try{const r=await api('discover',{});found=(r.nodes||[]).map(n=>({...n,added:state.nodes.some(o=>o.nodeId===n.nodeId)}));discoveredList();if(r.unverified)message(r.unverified+' discovered advertisements could not be verified.')}catch(e){found=[];discoveredList();message(e.message)}}
function discoverDialog(){const c=$('tvModalContentI665');c.innerHTML='<div class="tv-muted">Scan this LAN for _xtak-sensor._tcp VEIL services. Check multiple nodes to add them together.</div><div class="tv-actions" style="margin:9px 0;justify-content:space-between"><button class="tv-button" id="tvScanI665"><img src="/assets/runtime/xtak-veil-discover-i665.svg" alt=""> Scan LAN</button><span class="tv-muted" id="tvFoundCountI665"></span></div><div class="tv-actions" style="margin:6px 0"><button class="tv-mini" id="tvSelectAllI665">Select all</button><button class="tv-mini" id="tvClearI665">Clear all</button></div><div class="tv-scan-list" id="tvListI665"></div>';
$('tvScanI665').onclick=scan;$('tvSelectAllI665').onclick=()=>{found.filter(n=>!n.added).forEach(n=>selected.add(n.nodeId));discoveredList()};$('tvClearI665').onclick=()=>{selected.clear();discoveredList()};actions(pbutton('Cancel',close),pbutton('Add Selected (0)',async()=>{try{const toAdd=found.filter(n=>selected.has(n.nodeId));await api('add',{nodes:toAdd});close();await refresh();if(toAdd.length===1){const saved=state.nodes.find(n=>n.nodeId===toAdd[0].nodeId);if(saved)pairDialog(saved)}}catch(e){message(e.message)}}));$('tvModalActionsI665').lastChild.id='tvSelectedI665';$('tvSelectedI665').disabled=true;scan()}
function addDialog(){const c=$('tvModalContentI665');c.innerHTML='<div class="tv-field">Node name (optional)<input id="tvNameI665" maxlength="80" placeholder="VEIL Node 1"></div><div class="tv-field">LAN IP address / .local hostname<input id="tvHostI665" placeholder="192.168.1.110" autocomplete="off"></div><div class="tv-fields-two"><label class="tv-field">API port<input id="tvPortI665" type="number" min="1" max="65535" value="8080"></label><label class="tv-field">Protocol<select id="tvSchemeI665"><option value="http">HTTP</option></select></label></div><div class="tv-muted">Node identity is verified through its discovery API before adding. Network/API access must be enabled on the VEIL node.</div>';
 actions(pbutton('Cancel',close),pbutton('Test & Add Node',async()=>{message('Connecting to node…');try{const added=await api('add',{nodes:[{host:$('tvHostI665').value,port:Number($('tvPortI665').value),scheme:$('tvSchemeI665').value,name:$('tvNameI665').value}]});close();await refresh();const saved=state.nodes.find(n=>n.nodeId===added.nodes?.[0]?.nodeId)||state.nodes.at(-1);if(saved)pairDialog(saved)}catch(e){message(e.message)}}))}
function settingsDialog(){const cfg=state.config||{};const c=$('tvModalContentI665');c.innerHTML='<label class="tv-check"><input type="checkbox" id="tvAutoI665" '+(cfg.autoReconnect?'checked':'')+'><span>Automatically restart receiver after a failure</span></label><label class="tv-check"><input type="checkbox" id="tvVisibleI665" '+(cfg.visible?'checked':'')+'><span>Show VEIL observations on map</span></label><label class="tv-check"><input type="checkbox" id="tvMarkersI665" '+(cfg.showNodeMarkers?'checked':'')+'><span>Show node locations when provided</span></label>'+'<label class="tv-check"><input type="checkbox" id="tvMergeVeilI668" '+(cfg.mergeVeilDuplicates!==false?'checked':'')+'><span>Merge duplicate observations across VEIL nodes</span></label>'+
'<label class="tv-check"><input type="checkbox" id="tvCrossI668" '+(cfg.crossSourceDedup?'checked':'')+'><span>Merge duplicate targets across TAK Map sources (experimental)</span></label>'+
'<div class="tv-muted">Cross-source merging is off by default. Only verified ICAO/MMSI matches are eligible; native source controls remain independent.</div>'+
'<div class="tv-field">UDP CoT receiver port<input type="number" id="tvUdpI665" value="'+(cfg.port||6970)+'" min="1024" max="65535"></div><div class="tv-muted">Configure each VEIL node to send UDP CoT unicast to TAK Map LAN IP, port '+(cfg.port||6970)+'. Discovery alone does not start a CoT stream.</div>';
 actions(pbutton('Cancel',close),pbutton('Save Settings',async()=>{try{await api('settings',{port:Number($('tvUdpI665').value),visible:$('tvVisibleI665').checked,showNodeMarkers:$('tvMarkersI665').checked,autoReconnect:$('tvAutoI665').checked,mergeVeilDuplicates:$('tvMergeVeilI668').checked,crossSourceDedup:$('tvCrossI668').checked});close();refresh()}catch(e){message(e.message)}}))}
function pairDialog(node,automatic=false){
 if(!state.config?.enabled){if(!automatic)alert('Enable XTAK VEIL before connecting its API. The node remains saved for UDP CoT.');return}
 pairIsAuto=!!automatic;pairNode=node;open('pair');$('tvModalTitleI665').textContent='Connect VEIL API';
 const c=$('tvModalContentI665');
 c.innerHTML='<div class="tv-muted"><b>'+esc(node.name||node.nodeId)+'</b><div>'+esc(node.host)+':'+esc(node.port)+' · '+esc(node.nodeId)+'</div></div>'+
 '<label class="tv-field">Username<input type="text" id="tvUsernameI666" autocomplete="username" maxlength="128"></label>'+
 '<label class="tv-field">Password<input type="password" id="tvPasswordI666" autocomplete="current-password" maxlength="256"></label>'+
 '<label class="tv-check"><input type="checkbox" id="tvRememberI666"><span>Remember credentials on this TAK Map device</span></label>'+
 '<div class="tv-muted">Credentials remain on the TAK Map server. HTTP on a trusted LAN is not encrypted. Remembering is optional and off by default.</div>';
 actions(pbutton('Not Now',close),pbutton('Connect API',async()=>{
  message('Authenticating with VEIL…');
  try{await api('pair',{nodeId:node.nodeId,username:$('tvUsernameI666').value,password:$('tvPasswordI666').value,remember:$('tvRememberI666').checked});
   pairIsAuto=false;close();await refresh();
  }catch(e){message(e.message)}}));
 $('tvUsernameI666').focus();
}
function detailsDialog(node){open('details');$('tvModalTitleI665').textContent='VEIL Node Details';
 const c=$('tvModalContentI665');
 c.innerHTML='<div class="tv-muted"><b>'+esc(node.name||node.nodeId)+'</b><div>'+esc(node.host)+':'+esc(node.port)+'</div></div>'+
 '<div class="tv-section">CONNECTION</div><div class="tv-muted">UDP: '+esc(node.state==='receiving'?'Receiving':node.state||'Waiting')+'</div>'+
 '<div class="tv-muted">API: '+esc(node.apiState||'Not subscribed')+'</div>'+
 '<div class="tv-muted">Last snapshot: '+esc(node.apiLastSync?new Date(node.apiLastSync*1000).toLocaleString():'Not reported')+'</div>'+
 '<div class="tv-section">NODE HEALTH</div><div class="tv-muted" id="tvHealthI668">'+(state.config?.enabled&&node.apiSubscribed?'Checking read-only node health…':'Not available (VEIL disabled or UDP only)')+'</div>'+
 '<div class="tv-section">OBSERVATIONS</div><div class="tv-muted" id="tvObservationsI668">Observations on this node: '+esc(node.objects??0)+'</div>';
 actions(pbutton('Close',close),...(node.apiSubscribed?[pbutton('Unpair API',async()=>{
  if(!confirm('Unpair API synchronization for '+(node.name||node.nodeId)+'? UDP reception remains available.'))return;
  try{await api('unpair',{nodeId:node.nodeId});close();refresh()}catch(e){message(e.message)}
 })]:[]));
 if(!state.config?.enabled||!node.apiSubscribed)return;
 void api('health?nodeId='+encodeURIComponent(node.nodeId)).then(r=>{
  if(mode!=='details'||!$('tvHealthI668'))return;
  const h=r.health||{},values=[];
  const add=(name,v)=>{if(v!==undefined&&v!==null&&v!=='')values.push('<div>'+esc(name)+': '+esc(typeof v==='object'?JSON.stringify(v):v)+'</div>')};
  add('VEIL uptime (s)',h.veilUptimeSeconds);add('CPU temperature (°C)',h.cpuTemperatureC??h.cpuTemperature??h.temperatureC);
  add('Load (1 min)',h.load?.oneMinute);add('Memory available (MiB)',Number.isFinite(Number(h.memory?.availableBytes))?Math.round(Number(h.memory.availableBytes)/1048576):null);
  add('Storage free (GiB)',Number.isFinite(Number(h.storage?.freeBytes))?(Number(h.storage.freeBytes)/1073741824).toFixed(1):null);
  add('Undervoltage',h.throttling?.underVoltageNow===true?'Active':h.throttling?.underVoltageNow===false?'No':null);
  add('Last RF sample',h.lastSampleAt);
  add('Last node event',h.lastEventAt);add('SDR connected',h.sdr?.connected??h.usb?.sdrConnected);
  add('SDR usable',h.sdr?.usable??h.usb?.sdrUsable);add('SDR state',h.sdr?.state);
  add('Service',h.activeService?.name??h.activeService?.id);add('Service state',h.activeService?.state??h.activeService?.status);
  if(Array.isArray(h.warnings))add('Warnings',h.warnings.map(x=>x.message||x.code||x).join('; ')||'None reported');
  $('tvHealthI668').innerHTML=values.length?values.join(''):'Not reported'+(r.healthReason?' · '+esc(r.healthReason):'');
  if($('tvObservationsI668'))$('tvObservationsI668').textContent='Observations: '+(r.observationCount??node.objects??0)+' · '+Object.entries(r.counts||{}).map(([k,v])=>k.toUpperCase()+' '+v).join(' · ');
 }).catch(()=>{if(mode==='details'&&$('tvHealthI668'))$('tvHealthI668').textContent='Node health unavailable';});
}

function makeNodes(){const host=$('tvNodesI665');host.replaceChildren();
 for(const n of state.nodes||[]){
  const div=D.createElement('div');div.className='tv-node';
  const stamp=n.lastPacket?new Date(n.lastPacket*1000).toLocaleTimeString():'No packets yet';
  const udp=n.state==='receiving'?'Receiving':n.state==='waiting'?'Waiting':'Disabled';
  const apiStatus=!n.apiSubscribed?'UDP only':String(n.apiState||'reconnecting').replaceAll('_',' ');
  div.innerHTML='<div class="tv-node-line"><b>'+esc(n.name||n.nodeId)+'</b><span class="tv-muted">'+esc(apiStatus)+'</span></div>'+
   '<div class="tv-muted">'+esc(n.host)+':'+esc(n.port)+' · '+esc(n.objects)+' objects</div>'+
   '<div class="tv-muted">UDP: '+esc(udp)+' · last packet '+esc(stamp)+'</div>'+
   '<div class="tv-node-actions"></div>';
  const actions=div.querySelector('.tv-node-actions');
  const add=(label,fn)=>{const b=D.createElement('button');b.textContent=label;b.type='button';b.onclick=fn;actions.append(b)};
  add(!n.apiSubscribed?'Connect API':n.apiAuthRequired?'Log In':'API Details',()=>{
   if(!n.apiSubscribed||n.apiAuthRequired)pairDialog(n);else detailsDialog(n)
  });
  add('Details',()=>detailsDialog(n));
  add('Remove',async()=>{if(!confirm('Remove '+(n.name||n.nodeId)+' from TAK Map?'))return;
   try{await api('remove',{nodeId:n.nodeId});refresh()}catch(e){alert(e.message)}});
  host.append(div)
 }
 if(!state.nodes?.length)host.textContent='No nodes configured';
}
function makeServices(){const host=$('tvServicesI665');host.replaceChildren();
 for(const [key,label] of [['adsb','ADS-B'],['ais','AIS'],['aprs','APRS'],['remote_id','Remote ID']]){
  const el=D.createElement('label'),toggle=D.createElement('input');toggle.type='checkbox';
  toggle.checked=state.config?.services?.[key]!==false;
  toggle.onchange=async()=>{try{await api('settings',{services:{[key]:toggle.checked}});refresh()}catch(e){toggle.checked=!toggle.checked;alert(e.message)}};
  const title=D.createElement('span');title.textContent=label;
  const count=D.createElement('span');count.textContent=String(state.counts?.[key]||0);
  el.append(toggle,title,count);host.append(el)
 }
}
async function maybeAutoLogin(){
 if(authBusy||mode||!state.config?.enabled||document.visibilityState==='hidden'||D.querySelector('dialog[open]'))return;
 const node=(state.nodes||[]).find(n=>n.apiSubscribed&&n.apiAuthRequired&&n.apiState==='login_required'&&
   sessionStorage.getItem('takVeilDismissed:'+n.nodeId)!==String(n.apiAuthGeneration));
 if(!node)return;authBusy=true;
 try{
  const r=await api('prompt-check?nodeId='+encodeURIComponent(node.nodeId)+'&generation='+encodeURIComponent(node.apiAuthGeneration));
  if(r.show&&!mode&&state.config?.enabled&&(!D.querySelector('dialog[open]'))){
   const current=(state.nodes||[]).find(n=>n.nodeId===node.nodeId);
   if(current?.apiSubscribed&&current.apiAuthRequired&&current.apiAuthGeneration===node.apiAuthGeneration)
     pairDialog(current,true)
  }
 }catch(_){/* No modal on unreachable / unauthenticated page / timeout. */}
 finally{authBusy=false}
}
function update(){const toggle=$('tvEnableI665');toggle.checked=!!state.config?.enabled;const count=state.receiving||0,chip=$('tvStatusI665');chip.textContent=!state.config.enabled?'DISABLED':count?count+' RECEIVING':state.nodes?.length?'WAITING':'NO NODES';chip.classList.toggle('receiving',!!count);$('tvLiveStatusI665').textContent=!state.config.enabled?'VEIL receiver disabled':state.error||('Receiving from '+count+' of '+(state.nodes?.length||0)+' configured nodes');$('tvNodeCountI665').textContent=(state.nodes?.length||0)+' configured';$('tvObjectsI665').textContent=(state.objectsCount||0)+' unique'+(state.rawObservationsI668!==undefined?' / '+state.rawObservationsI668+' observed':'');$('tvDestinationI665').textContent='VEIL CoT unicast → '+(state.lanIPs?.length?state.lanIPs[0]:'TAK MAP LAN IP')+':'+(state.config?.port||6970)+' (UDP)';makeNodes();makeServices()}
function markerHtml(o){const visual=window.TakMapVeilVisualI669;return visual?visual.markerHtml(o):'<span class="tv-glyph">✈</span>'}
function popupHtml(o){const visual=window.TakMapVeilVisualI669;return visual?visual.genericPopup(o):'<b>XTAK VEIL</b>'}
function syncMap(objects){
 const m=map(),L=window.L,seen=new Set(),v=window.TakMapVeilVisualI669;
 if(!m||!L||typeof L.divIcon!=='function')return;
 for(const o of objects){
  if(state.config?.services?.[o.service]===false)continue;
  if(!Number.isFinite(Number(o.lat))||!Number.isFinite(Number(o.lon)))continue;
  const id=String(o.__veilKey||o.id),ll=[Number(o.lat),Number(o.lon)];seen.add(id);
  const iconPx=v?.iconSize?.(o)||36;
  const icon=L.divIcon({className:'tak-veil-i665-marker',html:markerHtml(o),iconSize:[iconPx,iconPx],iconAnchor:[iconPx/2,iconPx/2]});
  let p=layers.get(id);
  if(!p){p=L.marker(ll,{icon,zIndexOffset:550});p.addTo(m);layers.set(id,p)}
  else{p.setLatLng(ll);p.setIcon(icon)}
  p._takVeilObjectI669=o;
  if(o.service==='adsb'){
   p.unbindPopup();
   if(!p._takVeilClickI669){p._takVeilClickI669=true;p.on('click',e=>{
    const current=p._takVeilObjectI669;if(!current||current.service!=='adsb')return;
    if(e?.originalEvent){e.originalEvent.stopPropagation();e.originalEvent.preventDefault()}
    if(!window.TakMapVeilVisualI669?.openAdsb(current,p))p.bindPopup(popupHtml(current)).openPopup();
   })}
  }else p.bindPopup(popupHtml(o));
 }
 for(const [id,p] of layers){if(!seen.has(id)){
  if(p._takVeilObjectI669?.service==='adsb')window.TakMapAdsbSidebarI610?.removeExternal?.(window.TakMapVeilVisualI669?.adsbRow(p._takVeilObjectI669).id);
  m.removeLayer(p);layers.delete(id)
 }}
}
async function refresh(){try{state=await api('status');const r=await api('objects');
 const broker=window.TakMapVeilPhase3I668;
 if(broker&&state.config?.enabled&&state.config?.visible){const chosen=broker.render(r.objects||[],state.config,syncMap);
  state.objectsCount=chosen.objects.length;
  state.counts=chosen.uniqueCounts;
  state.rawObservationsI668=chosen.rawCount;
 }else{syncMap([]);if(broker)broker.remove3D()}
 update();try{D.dispatchEvent(new CustomEvent('takmap:veil-status-i690',{detail:state}))}catch(_){}void maybeAutoLogin()
 }catch(e){const status=$('tvLiveStatusI665');if(status)status.textContent='VEIL connection unavailable: '+e.message;syncMap([]);try{D.dispatchEvent(new CustomEvent('takmap:veil-error-i690'))}catch(_){}window.TakMapVeilPhase3I668?.remove3D()}}
function install(){place();watchSidebarOrder();if(!$('takVeilCardI665'))return;
 const toggle=$('tvEnableI665'),head=$('takVeilHeaderI665'),arrow=$('tvCollapseI665'),body=$('tvBodyI665');
 const collapse=(next)=>{body.hidden=!!next;arrow.textContent=next?'▸':'▾';arrow.setAttribute('aria-expanded',String(!next));
  try{localStorage.setItem('takVeilCollapsed',next?'1':'0')}catch(_){}};
 toggle.onchange=async ev=>{ev.stopPropagation();try{
  state=await api('settings',{enabled:ev.target.checked});
  if(!ev.target.checked&&mode==='pair')close();
  update();refresh()
 }catch(e){ev.target.checked=!ev.target.checked;alert(e.message)}};
 toggle.closest('label').addEventListener('click',ev=>ev.stopPropagation());
 arrow.onclick=ev=>{ev.preventDefault();ev.stopPropagation();collapse(!body.hidden)};
 head.setAttribute('tabindex','0');head.setAttribute('role','button');head.setAttribute('aria-label','Expand or collapse XTAK VEIL');
 head.onclick=ev=>{if(ev.target.closest('button,label,input'))return;collapse(!body.hidden)};
 head.onkeydown=ev=>{if(ev.target===head&&(ev.key==='Enter'||ev.key===' ')){ev.preventDefault();collapse(!body.hidden)}};
 try{collapse(localStorage.getItem('takVeilCollapsed')==='1')}catch(_){collapse(false)};
 $('tvDiscoverI665').onclick=()=>open('discover');$('tvAddI665').onclick=()=>open('add');
 $('tvSettingsI665').onclick=()=>open('settings');$('tvModalCloseI665').onclick=close;
 $('tvModalI665').onclick=e=>{if(e.target===$('tvModalI665'))close()};
 D.addEventListener('keydown',e=>{if(e.key==='Escape'&&mode)close()});
 refresh();setInterval(()=>{refresh()},4000)
}
if(D.readyState==='loading')D.addEventListener('DOMContentLoaded',install,{once:true});else install();
window.TakMapVeilI666={refresh,version:V,getStatus:()=>state,openNodeDetails:(nodeId)=>{const n=(state.nodes||[]).find(x=>String(x.nodeId)===String(nodeId));if(!n)return false;detailsDialog(n);return true}};
})();
