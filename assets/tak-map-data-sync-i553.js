(function(w,d){
'use strict';
const V='i602', STORAGE='takmap.dataSync.disabled';
const S={loadedAt:Date.now(),enabled:true,requests:0,networkRequests:0,completed:0,coalesced:0,suppressedDisabled:0,suppressedLegacy:0,suppressedBackoff:0,suppressedMinInterval:0,retries:0,timeouts:0,lastHttpStatus:0,lastError:'',lastReason:'',lastRequestStartedAt:0,lastRequestCompletedAt:0,lastDurationMs:0,lastGoodAt:0,lastGoodJson:null,lastDeliveredJson:null,inFlight:null,nextAllowedAt:0,consecutiveFailures:0,layerWasVisible:false,fetchInstalled:false,legacySweepsNeutralized:false,apiOwnersInstalled:false,activeController:null,requestTimeoutMs:12000,minIntervalMs:4000,automaticPollMs:5000,followupTimer:0,followupCount:0,lastSnapshotGeneration:0,pollTimer:0,pollTicks:0,securityLocked:false,lockedRecord:null,coreRefresh:null,ownedRefresh:null,ownedForce:null};
try{S.enabled=localStorage.getItem(STORAGE)!=='1'}catch(_){S.enabled=true}
const baseFetch=w.fetch.bind(w);
function $(id){return d.getElementById(id)}
function dataLayer(){try{return typeof dataSyncLayer!=='undefined'?dataSyncLayer:w.dataSyncLayer}catch(_){return w.dataSyncLayer||null}}
function mapObj(){try{return w.map||(typeof map!=='undefined'?map:null)}catch(_){return null}}
function esc(value){return String(value==null?'':value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function responseFrom(record){return new Response(record.body,{status:record.status,statusText:record.statusText||'',headers:record.headers||{'Content-Type':'application/json','Cache-Control':'no-store'}})}
function backgroundState(state,message,extra){return Object.assign({version:V,state,snapshot_available:false,refreshing:false,message:message||''},extra||{})}
function synthetic(kind,extra){const data=Object.assign({ok:true,version:V,objects:[],missions:[],mission_content:[],mission_uids:[],message:'',data_sync_control:{version:V,kind,enabled:S.enabled,last_good_at:S.lastGoodAt||0}},extra||{});return {status:200,statusText:'OK',headers:{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-TAK-Map-Data-Sync-Control':V},body:JSON.stringify(data)}}
function preserveCompletedCollections(json){
 const stable=Object.assign({},json||{});if(!S.lastGoodJson)return stable;
 for(const key of ['objects','mission_uids','mission_content','packages','mission_logs','mission_roles']){
  if((!Array.isArray(stable[key])||stable[key].length===0)&&Array.isArray(S.lastGoodJson[key]))stable[key]=S.lastGoodJson[key];
 }
 return stable;
}
function cachedRecord(kind){
 if(S.lastGoodJson){const latest=S.lastDeliveredJson?preserveCompletedCollections(S.lastDeliveredJson):Object.assign({},S.lastGoodJson);return synthetic(kind,Object.assign({},latest,{stale:true,data_sync_control:{version:V,kind,enabled:S.enabled,last_good_at:S.lastGoodAt||0}}));}
 const message=kind==='disabled'?'Data Sync disabled.':'Data Sync temporarily unavailable. Waiting for the server snapshot.';
 return synthetic(kind,{available:false,message,data_sync_background_i583:backgroundState(kind==='disabled'?'disabled':'client-temporary-unavailable',message,{last_error:S.lastError||''})});
}
function requestInfo(input,init){try{const raw=typeof input==='string'?input:String(input&&input.url||'');const u=new URL(raw,(d&&d.baseURI)||location.href);if(u.pathname!=='/api/tak-map/data-sync')return null;const reason=u.searchParams.get('reason')||'';return {url:u,method:String((init&&init.method)||(input&&input.method)||'GET').toUpperCase(),reason,force:u.searchParams.get('force')==='1',backgroundFollowup:reason.indexOf('i570-background-followup')===0||reason.indexOf('i590-background-followup')===0||reason.indexOf('i591-background-followup')===0}}catch(_){return null}}
function legacyReason(reason){const r=String(reason||'').toLowerCase();return /^v39[12]-/.test(r)||r.includes('orphan-sweep')||r.includes('v392-sweep')||r.startsWith('auto-load-')||r.includes('-followup-1')||r.includes('-followup-2')||r.includes('-followup-3')}
function transientStatus(status){return status===502||status===503||status===504}
function completedSnapshot(json){if(!json||typeof json!=='object')return false;const bg=json.data_sync_background_i599||json.data_sync_background_i583||json.data_sync_background_i570||{};return bg.snapshot_available!==false&&!bg.transitional_response&&json.initial_ots_refresh_in_progress!==true}
function adoptExistingSnapshot(){try{const json=w.__takMapLastDataSyncJsonI553||w.__takMapLastDataSyncJsonI570||null;if(!completedSnapshot(json))return false;S.lastGoodJson=json;S.lastGoodAt=Date.now();const bg=json.data_sync_background_i599||json.data_sync_background_i583||json.data_sync_background_i570||{};S.lastSnapshotGeneration=Math.max(S.lastSnapshotGeneration,Number(bg.snapshot_generation||bg.completed_generation||0));return true}catch(_){return false}}
function wait(ms){return new Promise(resolve=>setTimeout(resolve,ms))}
function showStatus(text){try{const panel=$('dataSyncPanelV476');const rows=$('dataSyncRows');if(panel)panel.dataset.dataSyncStatus=String(text||'');if(rows&&!S.lastGoodJson&&!rows.querySelector('.sync-card,.datasync-section'))rows.innerHTML='<div class="muted">'+esc(text||'Data Sync unavailable.')+'</div>'}catch(_){} }
function clearFollowup(){if(S.followupTimer){clearTimeout(S.followupTimer);S.followupTimer=0}S.followupCount=0}
function scheduleFollowup(){
 // i602 has one automatic polling owner. A server-side worker remains visible
 // through explicit background state; the browser does not create retry storms.
 return false;
}
function applyPayloadState(json){
 try{
  if(!json||typeof json!=='object')return json;
  if(json.locked&&json.requires_mission_password){const msg=String(json.message||'Mission password required.');showStatus(msg);clearFollowup();return json;}
  const bg=json.data_sync_background_i599||json.data_sync_background_i583||json.data_sync_background_i570||{};const state=String(bg.state||'');const snapshotAvailable=bg.snapshot_available!==false;
  if(state==='initial-refresh-in-progress'||json.initial_ots_refresh_in_progress){
   const msg=String(json.message||bg.message||'Initial OTS refresh in progress');
   const rows=$('dataSyncRows'),mc=$('missionCount'),oc=$('dataSyncObjectCount');
   if(rows)rows.innerHTML='<div class="muted tak-data-sync-initial-i570"><strong>'+esc(msg)+'</strong><br><span>TAK Map is retrieving your OpenTAKServer missions, contents, and CoT objects in the background.</span></div>';
   if(mc)mc.textContent='Refreshing missions';if(oc)oc.textContent='Refreshing objects';showStatus(msg);scheduleFollowup();return json;
  }
  if(bg.refreshing){showStatus(snapshotAvailable?'Refreshing OTS missions in the background. Showing the last successful snapshot.':'Initial OTS refresh in progress');scheduleFollowup()}
  else{clearFollowup();if(bg.last_error&&snapshotAvailable)showStatus('Showing the last successful Data Sync snapshot. Latest OTS refresh warning: '+String(bg.last_error));else if(snapshotAvailable)showStatus('Data Sync ready.')}
 }catch(_){}
 return json;
}
async function rawRecord(input,init){
 const started=Date.now(),controller=new AbortController(),prior=init&&init.signal;let timeoutHit=false;
 const forwardAbort=()=>{try{controller.abort(prior&&prior.reason)}catch(_){}};
 if(prior){if(prior.aborted)forwardAbort();else try{prior.addEventListener('abort',forwardAbort,{once:true})}catch(_){}}
 const timer=setTimeout(()=>{timeoutHit=true;try{controller.abort(new DOMException('Data Sync request timed out','TimeoutError'))}catch(_){controller.abort()}},S.requestTimeoutMs);
 S.activeController=controller;
 try{const next=Object.assign({},init||{},{signal:controller.signal});const resp=await baseFetch(input,next);const body=await resp.text();const headers={};try{resp.headers.forEach((v,k)=>{headers[k]=v})}catch(_){}return {status:resp.status,statusText:resp.statusText,headers,body,durationMs:Date.now()-started}}
 catch(error){if(timeoutHit){const e=new Error('Data Sync request timed out');e.name='TimeoutError';throw e}throw error}
 finally{clearTimeout(timer);if(S.activeController===controller)S.activeController=null;if(prior)try{prior.removeEventListener('abort',forwardAbort)}catch(_){} }
}
function parseJsonRecord(rec){const ct=String((rec.headers&&((rec.headers['content-type'])||(rec.headers['Content-Type'])))||'').toLowerCase();if(!ct.includes('json'))throw new Error('Data Sync returned non-JSON content');return JSON.parse(rec.body||'{}')}
async function networkFlight(input,init,info){
 const started=Date.now();S.lastRequestStartedAt=started;S.lastReason=info.reason||'interval';S.networkRequests++;let rec=null;
 try{
  rec=await rawRecord(input,init);
  if(transientStatus(rec.status)&&S.enabled){S.retries++;await wait(900);if(!S.enabled)throw new Error('Data Sync disabled');S.networkRequests++;rec=await rawRecord(input,init)}
  S.lastHttpStatus=rec.status;S.lastDurationMs=Date.now()-started;S.lastRequestCompletedAt=Date.now();S.completed++;
  if(rec.status===423){
   const json=parseJsonRecord(rec);
   if(json&&json.locked){S.securityLocked=true;S.lockedRecord=rec;S.lastGoodJson=null;S.lastDeliveredJson=json;S.lastGoodAt=0;w.__takMapLastDataSyncJsonI553=null;w.__takMapLastDataSyncJsonI570=null;clearFollowup();S.consecutiveFailures=0;S.nextAllowedAt=0;S.lastError='Mission password required.';applyPayloadState(json);return rec;}
  }
  if(rec.status>=200&&rec.status<300){
   let json=parseJsonRecord(rec);S.securityLocked=!!(json&&json.locked);S.lockedRecord=S.securityLocked?rec:null;const bg=json&&(json.data_sync_background_i599||json.data_sync_background_i583||json.data_sync_background_i570)||{};const initial=bg.snapshot_available===false||json.initial_ots_refresh_in_progress===true;const transitional=!!bg.transitional_response;
   if(transitional&&!S.lastGoodJson)adoptExistingSnapshot();if(transitional&&S.lastGoodJson){json=preserveCompletedCollections(json);rec=Object.assign({},rec,{body:JSON.stringify(json)})}S.lastDeliveredJson=json;
   if(!initial&&!transitional){const gen=Number(bg.snapshot_generation||bg.completed_generation||0);if(!gen||gen>=S.lastSnapshotGeneration){S.lastSnapshotGeneration=Math.max(S.lastSnapshotGeneration,gen);S.lastGoodJson=json;w.__takMapLastDataSyncJsonI553=json;w.__takMapLastDataSyncJsonI570=json;try{const api=w.TakMapMilStd2525CI553||w.TakMapMilStd2525CI538;if(api&&typeof api.learnMissionPointUids==='function')api.learnMissionPointUids(json)}catch(_){}S.lastGoodAt=Date.now()}}
   S.consecutiveFailures=0;S.nextAllowedAt=0;S.lastError='';applyPayloadState(json);return rec;
  }
  throw Object.assign(new Error('HTTP '+rec.status),{status:rec.status})
 }catch(error){
  S.lastDurationMs=Date.now()-started;S.lastRequestCompletedAt=Date.now();S.completed++;S.lastError=String(error&&error.message||error);S.lastHttpStatus=Number(error&&error.status)||Number(rec&&rec.status)||0;if(S.lastHttpStatus===504||/timeout|timed out/i.test(S.lastError))S.timeouts++;
  S.consecutiveFailures=Math.min(8,S.consecutiveFailures+1);const delay=Math.min(60000,5000*Math.pow(2,Math.max(0,S.consecutiveFailures-1)));S.nextAllowedAt=Date.now()+delay;showStatus(S.lastGoodJson?'Data Sync refresh failed. Showing the last successful snapshot.':'Data Sync temporarily unavailable. Waiting for the server snapshot.');return cachedRecord('transient-failure')
 }finally{S.inFlight=null}
}
async function controlledFetch(input,init){
 const info=requestInfo(input,init);if(!info)return baseFetch(input,init);S.requests++;
 if(info.method!=='GET')return baseFetch(input,init);
 if(!S.enabled){S.suppressedDisabled++;return responseFrom(cachedRecord('disabled'))}
 if(legacyReason(info.reason)){S.suppressedLegacy++;return responseFrom(cachedRecord('legacy-sweep-suppressed'))}
 const now=Date.now();if(S.inFlight){S.coalesced++;return responseFrom(await S.inFlight)}
 if(S.nextAllowedAt>now&&!info.backgroundFollowup){S.suppressedBackoff++;return responseFrom(cachedRecord('backoff'))}
 if(S.lastGoodAt&&now-S.lastGoodAt<S.minIntervalMs&&!info.force&&!info.backgroundFollowup){S.suppressedMinInterval++;return responseFrom(cachedRecord('minimum-interval'))}
 S.inFlight=networkFlight(input,init,info);return responseFrom(await S.inFlight)
}
w.fetch=controlledFetch;w.__takMapDataSyncFetchI599=controlledFetch;S.fetchInstalled=true;
function neutralizeLegacySweeps(){const noop=async reason=>({ok:true,version:V,suppressed:true,reason:reason||'legacy-sweep-disabled'});try{w.sweepTakMapOrphanMissionLayersV391=noop;w.sweepTakMapOrphanMissionLayersV392=noop;w.forceDataSyncOrphanSweepV391=noop;w.forceDataSyncOrphanSweepV392=noop;S.legacySweepsNeutralized=true}catch(_){}}
function installApiOwners(){
 if(!S.coreRefresh){
  const candidate=typeof w.refreshDataSync==='function'?w.refreshDataSync:null;
  if(candidate&&!candidate.__takMapI599Owner)S.coreRefresh=candidate.bind(w);
 }
 if(!S.ownedRefresh){
  S.ownedRefresh=async function(force,reason){
   if(!S.enabled){S.suppressedDisabled++;const disabled=JSON.parse(cachedRecord('disabled').body);applyPayloadState(disabled);return disabled}
   const result=S.coreRefresh?await S.coreRefresh(!!force,reason||'i602-refresh'):{ok:true,version:V,available:false};
   return applyPayloadState(result);
  };
  S.ownedRefresh.__takMapI599Owner=true;
  S.ownedForce=function(reason){
   if(!S.enabled){S.suppressedDisabled++;return Promise.resolve(JSON.parse(cachedRecord('disabled').body))}
   return S.ownedRefresh(true,reason||'i602-manual-refresh');
  };
  S.ownedForce.__takMapI599Owner=true;
 }
 if(w.refreshDataSync!==S.ownedRefresh)w.refreshDataSync=S.ownedRefresh;
 if(w.forceDataSyncSync!==S.ownedForce)w.forceDataSyncSync=S.ownedForce;
 w.__takMapDataSyncFetchI599=controlledFetch;
 S.apiOwnersInstalled=true;
}
function applyLayerVisibility(on){const layer=dataLayer(),m=mapObj();if(!layer||!m)return;try{if(!on){S.layerWasVisible=!!(m.hasLayer&&m.hasLayer(layer));if(S.layerWasVisible&&m.removeLayer)m.removeLayer(layer)}else if(S.layerWasVisible&&m.addLayer&&!m.hasLayer(layer))m.addLayer(layer)}catch(_){}}
function setEnabled(on,reason){
 S.enabled=!!on;try{localStorage.setItem(STORAGE,S.enabled?'0':'1')}catch(_){}applyLayerVisibility(S.enabled);
 const panel=$('dataSyncPanelV476');if(panel)panel.classList.toggle('tak-card-disabled-v491',!S.enabled);const input=$('dataSyncHeaderEnableV476');if(input&&input.checked!==S.enabled){input.checked=S.enabled;const btn=input.closest('.tak-header-switch-v491')&&input.closest('.tak-header-switch-v491').querySelector('.tak-header-switch-button-v491');if(btn)btn.setAttribute('aria-checked',S.enabled?'true':'false')}
 if(!S.enabled){clearFollowup();try{if(S.activeController)S.activeController.abort(new DOMException('Data Sync disabled','AbortError'))}catch(_){}showStatus('Data Sync disabled.');return Promise.resolve({ok:true,disabled:true})}
 S.nextAllowedAt=0;showStatus('Data Sync enabled. Refreshing…');try{const fn=w.refreshDataSync||(typeof refreshDataSync==='function'?refreshDataSync:null);return fn?Promise.resolve(fn(true,reason||'i591-enable')):Promise.resolve({ok:true,enabled:true})}catch(e){return Promise.resolve({ok:false,error:String(e)})}
}
function isEnabled(){return !!S.enabled}
function blockDisabledActions(ev){if(S.enabled)return;const panel=$('dataSyncPanelV476');if(!panel)return;const target=ev.target&&ev.target.closest&&ev.target.closest('#dataSyncPanelV476 .panel-body button,#dataSyncPanelV476 .panel-body input,#dataSyncPanelV476 .panel-body select,#dataSyncPanelV476 .panel-body a');if(!target)return;try{ev.preventDefault();ev.stopPropagation();ev.stopImmediatePropagation()}catch(_){}showStatus('Enable Data Sync to use this action.')}
d.addEventListener('click',blockDisabledActions,true);
function diagnostics(){const tomb=(S.lastGoodJson&&S.lastGoodJson.data_sync_deleted_uid_tombstones_i553)||{};return {version:V,enabled:S.enabled,securityLocked:S.securityLocked,fetchInstalled:S.fetchInstalled,legacySweepsNeutralized:S.legacySweepsNeutralized,apiOwnersInstalled:S.apiOwnersInstalled,requestTimeoutMs:S.requestTimeoutMs,minIntervalMs:S.minIntervalMs,automaticPollMs:S.automaticPollMs,requests:S.requests,networkRequests:S.networkRequests,completed:S.completed,inFlight:!!S.inFlight,coalesced:S.coalesced,suppressedDisabled:S.suppressedDisabled,suppressedLegacy:S.suppressedLegacy,suppressedBackoff:S.suppressedBackoff,suppressedMinInterval:S.suppressedMinInterval,retries:S.retries,timeouts:S.timeouts,lastHttpStatus:S.lastHttpStatus,lastError:S.lastError,lastReason:S.lastReason,lastRequestStartedAt:S.lastRequestStartedAt,lastRequestCompletedAt:S.lastRequestCompletedAt,lastDurationMs:S.lastDurationMs,lastGoodAt:S.lastGoodAt,lastGoodAgeMs:S.lastGoodAt?Date.now()-S.lastGoodAt:null,nextAllowedAt:S.nextAllowedAt,consecutiveFailures:S.consecutiveFailures,layerWasVisible:S.layerWasVisible,backgroundFollowupCount:S.followupCount,pollTimerInstalled:!!S.pollTimer,pollTicks:S.pollTicks,deletedUidTombstones:Number(tomb.count||0)}}
function installAutomaticPoll(){if(S.pollTimer)return;S.pollTimer=setInterval(async()=>{if(!S.enabled)return;S.pollTicks++;try{if(typeof w.refreshDataSync==='function')await w.refreshDataSync(false,'i602-automatic-poll')}catch(_){}},S.automaticPollMs)}
function applyInitialState(){applyLayerVisibility(S.enabled);const panel=$('dataSyncPanelV476');if(panel)panel.classList.toggle('tak-card-disabled-v491',!S.enabled);const input=$('dataSyncHeaderEnableV476');if(input){input.checked=S.enabled;const host=input.closest('.tak-header-switch-v491');const btn=host&&host.querySelector('.tak-header-switch-button-v491');if(btn)btn.setAttribute('aria-checked',S.enabled?'true':'false')}showStatus(S.enabled?'Data Sync ready.':'Data Sync disabled.')}
function boot(){adoptExistingSnapshot();neutralizeLegacySweeps();installApiOwners();installAutomaticPoll();applyInitialState();[700,2200].forEach(ms=>setTimeout(()=>{adoptExistingSnapshot();neutralizeLegacySweeps();installApiOwners()},ms))}
const api=Object.freeze({setEnabled,isEnabled,diagnostics,refresh:()=>setEnabled(true,'manual-api-refresh')});
w.TakMapDataSyncControlI591=api;w.TakMapDataSyncControlI590=api;w.TakMapDataSyncControlI589=api;w.TakMapDataSyncControlI585=api;w.TakMapDataSyncControlI584=api;w.TakMapDataSyncControlI583=api;w.TakMapDataSyncControlI581=api;w.TakMapDataSyncControlI570=api;w.TakMapDataSyncControlI553=api;w.TakMapDataSyncControlV476=api;
boot();w.__takMapDataSyncControlReadyI583=true;w.__takMapDataSyncControlReadyI581=true;w.__takMapDataSyncControlReadyI570=true;w.__takMapDataSyncControlReadyI553=true;
try{w.dispatchEvent(new CustomEvent('takmap:data-sync-control-ready-i602',{detail:diagnostics()}))}catch(_){}
console.info('[TAK Map] data-sync-control-i602: loaded');
})(window,document);
