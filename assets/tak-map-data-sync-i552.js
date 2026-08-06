(function(w,d){
'use strict';
const V='i552', STORAGE='takmap.dataSync.disabled';
const S={loadedAt:Date.now(),enabled:true,requests:0,networkRequests:0,completed:0,coalesced:0,suppressedDisabled:0,suppressedLegacy:0,suppressedBackoff:0,suppressedMinInterval:0,retries:0,timeouts:0,lastHttpStatus:0,lastError:'',lastReason:'',lastRequestStartedAt:0,lastRequestCompletedAt:0,lastDurationMs:0,lastGoodAt:0,lastGoodJson:null,inFlight:null,nextAllowedAt:0,consecutiveFailures:0,layerWasVisible:false,fetchInstalled:false,legacySweepsNeutralized:false,apiOwnersInstalled:false,activeController:null,requestTimeoutMs:15000,minIntervalMs:10000};
try{S.enabled=localStorage.getItem(STORAGE)!=='1'}catch(_){S.enabled=true}
const baseFetch=w.fetch.bind(w);
function $(id){return d.getElementById(id)}
function dataLayer(){try{return typeof dataSyncLayer!=='undefined'?dataSyncLayer:w.dataSyncLayer}catch(_){return w.dataSyncLayer||null}}
function mapObj(){try{return w.map||(typeof map!=='undefined'?map:null)}catch(_){return null}}
function responseFrom(record){return new Response(record.body,{status:record.status,statusText:record.statusText||'',headers:record.headers||{'Content-Type':'application/json','Cache-Control':'no-store'}})}
function synthetic(kind,extra){const data=Object.assign({ok:true,version:V,objects:[],missions:[],mission_content:[],mission_uids:[],data_sync_control:{kind,enabled:S.enabled,last_good_at:S.lastGoodAt||0}},extra||{});return {status:200,statusText:'OK',headers:{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store','X-TAK-Map-Data-Sync-Control':V},body:JSON.stringify(data)}}
function cachedRecord(kind){if(S.lastGoodJson)return synthetic(kind,Object.assign({},S.lastGoodJson,{stale:true,data_sync_control:{kind,enabled:S.enabled,last_good_at:S.lastGoodAt||0}}));return synthetic(kind,{available:false})}
function requestInfo(input,init){try{const raw=typeof input==='string'?input:String(input&&input.url||'');const u=new URL(raw,location.href);if(u.pathname!=='/api/tak-map/data-sync')return null;return {url:u,method:String((init&&init.method)||(input&&input.method)||'GET').toUpperCase(),reason:u.searchParams.get('reason')||'',force:u.searchParams.get('force')==='1'}}catch(_){return null}}
function legacyReason(reason){const r=String(reason||'').toLowerCase();return /^v39[12]-/.test(r)||r.includes('orphan-sweep')||r.includes('v392-sweep')||r.startsWith('auto-load-')||r.includes('-followup-')||r.endsWith('-followup')}
function transientStatus(status){return status===502||status===503||status===504}
function wait(ms){return new Promise(resolve=>setTimeout(resolve,ms))}
async function rawRecord(input,init){
 const started=Date.now(),controller=new AbortController(),prior=init&&init.signal;let timeoutHit=false;
 const forwardAbort=()=>{try{controller.abort(prior&&prior.reason)}catch(_){}};
 if(prior){if(prior.aborted)forwardAbort();else try{prior.addEventListener('abort',forwardAbort,{once:true})}catch(_){}}
 const timer=setTimeout(()=>{timeoutHit=true;try{controller.abort(new DOMException('Data Sync request timed out','TimeoutError'))}catch(_){controller.abort()}},S.requestTimeoutMs);
 S.activeController=controller;
 try{const next=Object.assign({},init||{},{signal:controller.signal});const resp=await baseFetch(input,next);const body=await resp.text();const headers={};try{resp.headers.forEach((v,k)=>{headers[k]=v})}catch(_){}return {status:resp.status,statusText:resp.statusText,headers,body,durationMs:Date.now()-started}}
 catch(error){if(timeoutHit){const e=new Error('Data Sync request timed out');e.name='TimeoutError';throw e}throw error}
 finally{clearTimeout(timer);if(S.activeController===controller)S.activeController=null;if(prior)try{prior.removeEventListener('abort',forwardAbort)}catch(_){}}
}
function parseJsonRecord(rec){const ct=String((rec.headers&&((rec.headers['content-type'])||(rec.headers['Content-Type'])))||'').toLowerCase();if(!ct.includes('json'))throw new Error('Data Sync returned non-JSON content');return JSON.parse(rec.body||'{}')}
async function networkFlight(input,init,info){
 const started=Date.now();S.lastRequestStartedAt=started;S.lastReason=info.reason||'interval';S.networkRequests++;
 let rec=null;
 try{
  rec=await rawRecord(input,init);
  if(transientStatus(rec.status)&&S.enabled){S.retries++;await wait(1200);if(!S.enabled)throw new Error('Data Sync disabled');S.networkRequests++;rec=await rawRecord(input,init)}
  S.lastHttpStatus=rec.status;S.lastDurationMs=Date.now()-started;S.lastRequestCompletedAt=Date.now();S.completed++;
  if(rec.status>=200&&rec.status<300){
   const json=parseJsonRecord(rec);S.lastGoodJson=json;w.__takMapLastDataSyncJsonI552=json;try{const api=w.TakMapMilStd2525CI552||w.TakMapMilStd2525CI538;if(api&&typeof api.learnMissionPointUids==='function')api.learnMissionPointUids(json)}catch(_){}S.lastGoodAt=Date.now();S.consecutiveFailures=0;S.nextAllowedAt=0;S.lastError='';return rec
  }
  throw Object.assign(new Error('HTTP '+rec.status),{status:rec.status})
 }catch(error){
  S.lastDurationMs=Date.now()-started;S.lastRequestCompletedAt=Date.now();S.completed++;S.lastError=String(error&&error.message||error);S.lastHttpStatus=Number(error&&error.status)||Number(rec&&rec.status)||0;if(S.lastHttpStatus===504||/timeout|timed out/i.test(S.lastError))S.timeouts++;
  S.consecutiveFailures=Math.min(8,S.consecutiveFailures+1);const delay=Math.min(60000,5000*Math.pow(2,Math.max(0,S.consecutiveFailures-1)));S.nextAllowedAt=Date.now()+delay;showStatus('Data Sync temporarily unavailable. Retrying with backoff.');return cachedRecord('transient-failure')
 }finally{S.inFlight=null}
}
function showStatus(text){try{const panel=$('dataSyncPanelV476');const rows=$('dataSyncRows');if(panel)panel.dataset.dataSyncStatus=String(text||'');if(rows&&!S.lastGoodJson&&!rows.querySelector('.sync-card,.datasync-section'))rows.innerHTML='<div class="muted">'+String(text||'Data Sync unavailable.')+'</div>'}catch(_){} }
async function controlledFetch(input,init){
 const info=requestInfo(input,init);if(!info)return baseFetch(input,init);S.requests++;
 if(info.method!=='GET')return baseFetch(input,init);
 if(!S.enabled){S.suppressedDisabled++;return responseFrom(synthetic('disabled',{disabled:true}))}
 if(legacyReason(info.reason)){S.suppressedLegacy++;return responseFrom(cachedRecord('legacy-sweep-suppressed'))}
 const now=Date.now();if(S.inFlight){S.coalesced++;return responseFrom(await S.inFlight)}
 if(S.nextAllowedAt>now){S.suppressedBackoff++;return responseFrom(cachedRecord('backoff'))}
 if(S.lastGoodAt&&now-S.lastGoodAt<S.minIntervalMs&&!info.force){S.suppressedMinInterval++;return responseFrom(cachedRecord('minimum-interval'))}
 S.inFlight=networkFlight(input,init,info);return responseFrom(await S.inFlight)
}
w.fetch=controlledFetch;S.fetchInstalled=true;
function neutralizeLegacySweeps(){
 const noop=async reason=>({ok:true,version:V,suppressed:true,reason:reason||'legacy-sweep-disabled'});
 try{w.sweepTakMapOrphanMissionLayersV391=noop;w.sweepTakMapOrphanMissionLayersV392=noop;w.forceDataSyncOrphanSweepV391=noop;w.forceDataSyncOrphanSweepV392=noop;S.legacySweepsNeutralized=true}catch(_){}
}
function installApiOwners(){
 if(S.apiOwnersInstalled)return;
 const originalRefresh=typeof w.refreshDataSync==='function'?w.refreshDataSync.bind(w):null;
 w.refreshDataSync=function(force,reason){if(!S.enabled){S.suppressedDisabled++;return Promise.resolve({ok:true,disabled:true,version:V})}return originalRefresh?originalRefresh(!!force,reason||'i552-refresh'):Promise.resolve({ok:true,version:V,available:false})};
 w.forceDataSyncSync=function(reason){if(!S.enabled){S.suppressedDisabled++;return Promise.resolve({ok:true,disabled:true,version:V})}return w.refreshDataSync(true,reason||'i552-force')};
 S.apiOwnersInstalled=true;
}
function applyLayerVisibility(on){
 const layer=dataLayer(),m=mapObj();if(!layer||!m)return;
 try{if(!on){S.layerWasVisible=!!(m.hasLayer&&m.hasLayer(layer));if(S.layerWasVisible&&m.removeLayer)m.removeLayer(layer)}else if(S.layerWasVisible&&m.addLayer&&!m.hasLayer(layer))m.addLayer(layer)}catch(_){}
}
function setEnabled(on,reason){
 S.enabled=!!on;try{localStorage.setItem(STORAGE,S.enabled?'0':'1')}catch(_){}applyLayerVisibility(S.enabled);
 const panel=$('dataSyncPanelV476');if(panel)panel.classList.toggle('tak-card-disabled-v491',!S.enabled);
 const input=$('dataSyncHeaderEnableV476');if(input&&input.checked!==S.enabled){input.checked=S.enabled;const btn=input.closest('.tak-header-switch-v491')&&input.closest('.tak-header-switch-v491').querySelector('.tak-header-switch-button-v491');if(btn)btn.setAttribute('aria-checked',S.enabled?'true':'false')}
 if(!S.enabled){try{if(S.activeController)S.activeController.abort(new DOMException('Data Sync disabled','AbortError'))}catch(_){}showStatus('Data Sync disabled.');return Promise.resolve({ok:true,disabled:true})}
 S.nextAllowedAt=0;showStatus('Data Sync enabled. Refreshing…');
 try{const fn=w.refreshDataSync||(typeof refreshDataSync==='function'?refreshDataSync:null);return fn?Promise.resolve(fn(true,reason||'i552-enable')):Promise.resolve({ok:true,enabled:true})}catch(e){return Promise.resolve({ok:false,error:String(e)})}
}
function isEnabled(){return !!S.enabled}
function blockDisabledActions(ev){
 if(S.enabled)return;const panel=$('dataSyncPanelV476');if(!panel)return;const target=ev.target&&ev.target.closest&&ev.target.closest('#dataSyncPanelV476 .panel-body button,#dataSyncPanelV476 .panel-body input,#dataSyncPanelV476 .panel-body select,#dataSyncPanelV476 .panel-body a');if(!target)return;try{ev.preventDefault();ev.stopPropagation();ev.stopImmediatePropagation()}catch(_){}showStatus('Enable Data Sync to use this action.')
}
d.addEventListener('click',blockDisabledActions,true);
function diagnostics(){const tomb=(S.lastGoodJson&&S.lastGoodJson.data_sync_deleted_uid_tombstones_i552)||{};return {version:V,enabled:S.enabled,fetchInstalled:S.fetchInstalled,legacySweepsNeutralized:S.legacySweepsNeutralized,apiOwnersInstalled:S.apiOwnersInstalled,requestTimeoutMs:S.requestTimeoutMs,minIntervalMs:S.minIntervalMs,automaticPollMs:10000,requests:S.requests,networkRequests:S.networkRequests,completed:S.completed,inFlight:!!S.inFlight,coalesced:S.coalesced,suppressedDisabled:S.suppressedDisabled,suppressedLegacy:S.suppressedLegacy,suppressedBackoff:S.suppressedBackoff,suppressedMinInterval:S.suppressedMinInterval,retries:S.retries,timeouts:S.timeouts,lastHttpStatus:S.lastHttpStatus,lastError:S.lastError,lastReason:S.lastReason,lastRequestStartedAt:S.lastRequestStartedAt,lastRequestCompletedAt:S.lastRequestCompletedAt,lastDurationMs:S.lastDurationMs,lastGoodAt:S.lastGoodAt,lastGoodAgeMs:S.lastGoodAt?Date.now()-S.lastGoodAt:null,nextAllowedAt:S.nextAllowedAt,consecutiveFailures:S.consecutiveFailures,layerWasVisible:S.layerWasVisible,deletedUidTombstones:Number(tomb.count||0)}}
function applyInitialState(){applyLayerVisibility(S.enabled);const panel=$('dataSyncPanelV476');if(panel)panel.classList.toggle('tak-card-disabled-v491',!S.enabled);const input=$('dataSyncHeaderEnableV476');if(input){input.checked=S.enabled;const host=input.closest('.tak-header-switch-v491');const btn=host&&host.querySelector('.tak-header-switch-button-v491');if(btn)btn.setAttribute('aria-checked',S.enabled?'true':'false')}showStatus(S.enabled?'Data Sync ready.':'Data Sync disabled.')}
function boot(){neutralizeLegacySweeps();installApiOwners();applyInitialState();[700,2200].forEach(ms=>setTimeout(()=>{neutralizeLegacySweeps();installApiOwners()},ms))}
const api=Object.freeze({setEnabled,isEnabled,diagnostics,refresh:()=>setEnabled(true,'manual-api-refresh')});
w.TakMapDataSyncControlI552=api;w.TakMapDataSyncControlV476=api;
boot();
w.__takMapDataSyncControlReadyI552=true;
try{w.dispatchEvent(new CustomEvent('takmap:data-sync-control-ready-i552',{detail:diagnostics()}))}catch(_){}
console.info('[TAK Map] data-sync-control-i552: loaded');
})(window,document);
