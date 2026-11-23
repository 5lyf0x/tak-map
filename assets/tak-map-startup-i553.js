(function(w,d){
'use strict';
const V='i553';
const D=w.TakMapStartupDiagnosticsI553=w.TakMapStartupDiagnosticsI553||{
  version:V,loaderStartedAt:performance.now(),domReadyAt:0,firstPaintAt:0,
  leafletStartedAt:0,leafletReadyAt:0,leafletSource:'',coreStartedAt:0,coreReadyAt:0,
  coreInitCalledAt:0,shellReadyAt:0,dataSyncControlStartedAt:0,dataSyncControlReadyAt:0,manifestFetchedAt:0,manifestParsedAt:0,
  runtimeStartedAt:0,runtimeReadyAt:0,deferredTotal:0,deferredLoaded:0,
  deferredFailed:[],longTasks:[],errors:[],dataSyncRequests:0,dataSyncStartupRequests:0,
  mutation:{nativeBatches:0,deliveredCallbacks:0,coalescedBatches:0,broadObservers:0,parkedBroadObservers:0,activatedBroadObservers:0,suppressedBroadAttributeObservers:0,records:0,activatedAt:0}
};
function now(){try{return performance.now()}catch(_){return Date.now()}}
function recordError(stage,error,id){D.errors.push({stage,id:id||'',at:now(),error:String(error&&error.stack||error)});if(D.errors.length>50)D.errors.shift()}
function setStatus(text){try{const el=d.getElementById('mapStatus');if(el)el.textContent=text}catch(_){}}
try{new PerformanceObserver(list=>{for(const e of list.getEntries()){D.longTasks.push({startTime:e.startTime,duration:e.duration});if(D.longTasks.length>100)D.longTasks.shift()}}).observe({type:'longtask',buffered:true})}catch(_){}
try{w.addEventListener('error',e=>recordError('window-error',e.error||e.message,''),true);w.addEventListener('unhandledrejection',e=>recordError('unhandled-rejection',e.reason,''),true)}catch(_){}

// Count Data Sync calls from the earliest possible point. This is diagnostic and
// deliberately does not alter request/response behavior.
(function installFetchDiagnostics(){
  const current=w.fetch;if(typeof current!=='function'||current.__takMapStartupI553)return;
  const wrapped=function(input,init){
    try{const url=String(input&&input.url||input||'');if(/\/api\/tak-map\/data-sync(?:[/?]|$)/.test(url)){D.dataSyncRequests++;if(/(?:[?&]reason=startup(?:&|$)|[?&]reason=startup-state(?:&|$))/.test(url))D.dataSyncStartupRequests++}}catch(_){}
    return current.apply(this,arguments)
  };
  wrapped.__takMapStartupI553=true;wrapped.__takMapStartupBaseI553=current;w.fetch=wrapped;
})();

// During startup, older compatibility modules can ask for the same read-only
// state several times. Coalesce those GETs for a short window so one response
// fan-outs to all callers without serializing or delaying first render.
(function installStartupGetCoordinator(){
  const base=w.fetch;if(typeof base!=='function'||base.__takMapGetCoordinatorI553)return;
  const ttlByPath=new Map([
    ['/api/tak-map/ots/session',15000],['/api/tak-map/adsb-settings',15000],
    ['/api/tak-map/custom-basemaps',15000],['/api/tak-map/status-banner',15000],
    ['/api/tak-map/euds',15000],['/mil2525/icons.json',30000]
  ]);
  const inflight=new Map(),cache=new Map();
  D.requestCoordinator={network:0,coalesced:0,cacheHits:0,activeUntilMs:now()+30000};
  function keyFor(input,init){
    try{
      const method=String((init&&init.method)||(input&&input.method)||'GET').toUpperCase();if(method!=='GET')return null;
      if(now()>D.requestCoordinator.activeUntilMs)return null;
      const u=new URL(String(input&&input.url||input||''),d.baseURI||location.href),ttl=ttlByPath.get(u.pathname);if(!ttl)return null;
      u.searchParams.delete('_');const pairs=Array.from(u.searchParams.entries()).sort((a,b)=>a[0].localeCompare(b[0])||a[1].localeCompare(b[1]));
      return {key:u.pathname+(pairs.length?'?'+new URLSearchParams(pairs).toString():''),ttl};
    }catch(_){return null}
  }
  const wrapped=function(input,init){
    const info=keyFor(input,init);if(!info)return base.apply(this,arguments);
    const cached=cache.get(info.key),t=now();
    if(cached&&cached.expires>t){D.requestCoordinator.cacheHits++;try{return Promise.resolve(cached.response.clone())}catch(_){cache.delete(info.key)}}
    const active=inflight.get(info.key);
    if(active){D.requestCoordinator.coalesced++;return active.then(r=>r.clone())}
    D.requestCoordinator.network++;
    const args=arguments,ctx=this;
    const pending=Promise.resolve().then(()=>base.apply(ctx,args)).then(r=>{
      try{if(r&&r.ok&&typeof r.clone==='function')cache.set(info.key,{response:r.clone(),expires:now()+info.ttl})}catch(_){}
      return r
    }).finally(()=>inflight.delete(info.key));
    inflight.set(info.key,pending);return pending.then(r=>r.clone())
  };
  wrapped.__takMapGetCoordinatorI553=true;wrapped.__takMapGetCoordinatorBaseI553=base;w.fetch=wrapped;
})();

// Broad legacy observers are parked through deferred-module loading and the
// initial optional-data phase. They receive one bounded reconciliation callback
// after activation, then use coalesced native observation for later changes.
(function installMutationGate(){
  const Native=w.MutationObserver;if(!Native||Native.__takMapMutationGateI553)return;
  const broadRegistry=new Set();let active=false,sharedNative=null,flushTimer=0;
  let pendingRecords=[],deliveryQueue=[],deliveryBatch=[],deliveryScheduled=false;
  D.mutation.sharedNativeBroadObservers=0;D.mutation.brokerFlushes=0;D.mutation.maxBrokerBatch=0;
  function isBroadTarget(target,o){return !!(o&&o.subtree&&(target===d.body||target===d.documentElement||target===d))}
  function scheduleDelivery(){
    if(deliveryScheduled)return;deliveryScheduled=true;
    const run=function(deadline){
      deliveryScheduled=false;let delivered=0;
      while(deliveryQueue.length&&delivered<2&&(!deadline||typeof deadline.timeRemaining!=='function'||deadline.timeRemaining()>3)){
        const self=deliveryQueue.shift();if(!self||!self._broadRegistered)continue;
        delivered++;D.mutation.deliveredCallbacks++;
        try{self._callback(deliveryBatch,self)}catch(e){recordError('mutation-callback',e,'')}
      }
      if(deliveryQueue.length){deliveryScheduled=true;try{if(typeof requestIdleCallback==='function')requestIdleCallback(run,{timeout:100});else setTimeout(()=>run(null),16)}catch(_){setTimeout(()=>run(null),16)}}
      else deliveryBatch=[];
    };
    try{if(typeof requestIdleCallback==='function')requestIdleCallback(run,{timeout:120});else setTimeout(()=>run(null),16)}catch(_){setTimeout(()=>run(null),16)}
  }
  function flushBroad(){
    flushTimer=0;if(!active||!pendingRecords.length)return;
    const batch=pendingRecords.splice(0,200);pendingRecords.length=0;
    D.mutation.brokerFlushes++;D.mutation.maxBrokerBatch=Math.max(D.mutation.maxBrokerBatch,batch.length);
    deliveryBatch=batch;deliveryQueue=Array.from(broadRegistry);scheduleDelivery();
  }
  function queueBroad(records){
    const rows=Array.from(records||[]);D.mutation.nativeBatches++;D.mutation.records+=rows.length;D.mutation.coalescedBatches++;
    if(pendingRecords.length<200)pendingRecords.push.apply(pendingRecords,rows.slice(0,200-pendingRecords.length));
    if(flushTimer)return;flushTimer=setTimeout(flushBroad,500);
  }
  function ensureShared(){
    if(sharedNative||!active||!broadRegistry.size)return;
    sharedNative=new Native(queueBroad);sharedNative.observe(d.documentElement||d,{subtree:true,childList:true});
    D.mutation.sharedNativeBroadObservers=1;
  }
  function Budgeted(callback){
    if(!(this instanceof Budgeted))throw new TypeError('MutationObserver constructor requires new');
    this._callback=callback;this._broad=false;this._broadRegistered=false;this._target=null;this._options=null;
    const self=this;this._native=new Native(function(records){D.mutation.nativeBatches++;D.mutation.records+=records.length;D.mutation.deliveredCallbacks++;try{callback(records,self)}catch(e){recordError('mutation-callback',e,'')}})
  }
  Budgeted.prototype.observe=function(target,options){
    const o=Object.assign({},options||{}),broad=isBroadTarget(target,o);
    if(broad){
      if(!this._broad){this._broad=true;D.mutation.broadObservers++}
      if(o.attributes){o.attributes=false;delete o.attributeFilter;delete o.attributeOldValue;D.mutation.suppressedBroadAttributeObservers++;if(!o.childList)o.childList=true}
      o.characterData=false;delete o.characterDataOldValue;
      this._target=target;this._options=o;this._broadRegistered=true;broadRegistry.add(this);
      D.mutation.parkedBroadObservers=active?0:broadRegistry.size;if(active){D.mutation.activatedBroadObservers=broadRegistry.size;ensureShared()}
      return;
    }
    this._target=target;this._options=o;return this._native.observe(target,o)
  };
  Budgeted.prototype.disconnect=function(){
    this._broadRegistered=false;broadRegistry.delete(this);D.mutation.parkedBroadObservers=active?0:broadRegistry.size;D.mutation.activatedBroadObservers=active?broadRegistry.size:0;
    try{return this._native.disconnect()}finally{if(!broadRegistry.size&&sharedNative){sharedNative.disconnect();sharedNative=null;D.mutation.sharedNativeBroadObservers=0}}
  };
  Budgeted.prototype.takeRecords=function(){return this._native.takeRecords()};
  function activate(){
    if(active)return {active:true,activated:D.mutation.activatedBroadObservers};
    active=true;D.mutation.activatedAt=now();D.mutation.parkedBroadObservers=0;D.mutation.activatedBroadObservers=broadRegistry.size;ensureShared();
    // One bounded reconciliation pass replaces thousands of startup deliveries.
    deliveryBatch=[{type:'childList',target:d.body||d.documentElement,addedNodes:[],removedNodes:[]}];deliveryQueue=Array.from(broadRegistry);scheduleDelivery();
    return {active:true,activated:D.mutation.activatedBroadObservers}
  }
  Budgeted.__takMapMutationGateI553=true;Budgeted.NativeMutationObserverI553=Native;
  w.NativeMutationObserverI553=Native;w.MutationObserver=Budgeted;
  w.TakMapMutationGateI553=Object.freeze({activate,isActive:()=>active,diagnostics:()=>JSON.parse(JSON.stringify(D.mutation))});
})();
function nextPaint(){return new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))}
function yieldBudget(){return new Promise(resolve=>{const done=()=>requestAnimationFrame(resolve);try{if(typeof requestIdleCallback==='function')requestIdleCallback(done,{timeout:120});else setTimeout(done,0)}catch(_){setTimeout(done,0)}})}
function loadScript(src,id,timeoutMs){return new Promise((resolve,reject)=>{
  const s=d.createElement('script');let done=false,timer=0;
  const finish=(error)=>{if(done)return;done=true;if(timer)clearTimeout(timer);s.onload=s.onerror=null;if(error){try{s.remove()}catch(_){}reject(error)}else resolve(s)};
  s.id=id;s.src=src;s.async=true;s.dataset.takMapStartup=V;s.onload=()=>finish();s.onerror=()=>finish(new Error('Script load failed: '+src));
  timer=setTimeout(()=>finish(new Error('Script load timeout: '+src)),Math.max(1000,Number(timeoutMs)||8000));(d.head||d.documentElement).appendChild(s)
})}
async function ensureLeaflet(){
  if(w.L&&typeof w.L.map==='function'){D.leafletSource='preloaded';D.leafletReadyAt=now();return}
  D.leafletStartedAt=now();const sources=[
    ['unpkg','https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'],
    ['cdnjs','https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js']
  ];
  let last=null;
  for(const row of sources){try{await loadScript(row[1],'takMapLeaflet_'+row[0]+'_I553',4500);if(w.L&&typeof w.L.map==='function'){D.leafletSource=row[0];D.leafletReadyAt=now();return}}catch(e){last=e;recordError('leaflet-load',e,row[0])}}
  throw last||new Error('Leaflet map engine unavailable')
}
function executeClassicScript(entry){return new Promise((resolve,reject)=>{
  const code=String(entry&&entry.code||'')+'\n//# sourceURL=/assets/runtime/i553-deferred/'+encodeURIComponent(String(entry&&entry.id||'script'))+'.js\n';
  const blob=new Blob([code],{type:'application/javascript'}),url=URL.createObjectURL(blob),s=d.createElement('script');
  s.id=String(entry&&entry.id||('takMapDeferredI553_'+D.deferredLoaded));s.async=false;s.src=url;s.dataset.takMapDeferred=V;
  const clean=()=>{URL.revokeObjectURL(url);s.onload=s.onerror=null};s.onload=()=>{clean();resolve()};s.onerror=()=>{const e=new Error('Deferred runtime failed: '+s.id);clean();reject(e)};(d.head||d.documentElement).appendChild(s)
})}
async function loadDeferredRuntime(manifestPromise,dataSyncPromise){
  D.runtimeStartedAt=now();
  try{
    const text=await manifestPromise;D.manifestFetchedAt=now();await nextPaint();
    const manifest=JSON.parse(text);D.manifestParsedAt=now();
    const rows=Array.isArray(manifest.scripts)?manifest.scripts:[];D.deferredTotal=rows.length;
    for(const entry of rows){
      await yieldBudget();
      try{await executeClassicScript(entry);D.deferredLoaded++}
      catch(e){D.deferredFailed.push(String(entry&&entry.id||''));recordError('deferred-script',e,String(entry&&entry.id||''))}
    }
  }catch(e){recordError('deferred-manifest',e,'')}
  D.runtimeReadyAt=now();
  try{d.querySelectorAll('.iteration-chip,.iteration-marker').forEach(el=>el.textContent=V)}catch(_){}
  try{d.documentElement.dataset.takMapRuntime='ready';w.dispatchEvent(new CustomEvent('takmap:runtime-ready-i553',{detail:{loaded:D.deferredLoaded,total:D.deferredTotal,failed:D.deferredFailed.slice()}}))}catch(_){}
  let optionalPromise=Promise.resolve();
  try{if(typeof w.__takMapStartOptionalDataI553==='function')optionalPromise=Promise.resolve(w.__takMapStartOptionalDataI553())}catch(e){recordError('optional-data-start',e,'')}
  await Promise.allSettled([Promise.resolve(dataSyncPromise),optionalPromise]);
  try{if(w.TakMapMutationGateI553)w.TakMapMutationGateI553.activate()}catch(e){recordError('mutation-gate-activate',e,'')}
  D.initialDataReadyAt=now();
  try{w.dispatchEvent(new CustomEvent('takmap:initial-data-ready-i553',{detail:{dataSync:w.__takMapDataSyncStartupResultI553||null,mutation:D.mutation}}))}catch(_){}
}
async function start(){
  if(w.__takMapStartupLoaderStartedI553)return;w.__takMapStartupLoaderStartedI553=true;D.domReadyAt=now();setStatus('Loading map engine…');
  try{d.documentElement.dataset.takMapShell='loading'}catch(_){}
  const manifestPromise=fetch('/assets/runtime/tak-map-deferred-i553.json?v=1.4.0-i670',{cache:'force-cache',credentials:'same-origin'}).then(r=>{if(!r.ok)throw new Error('Runtime manifest HTTP '+r.status);return r.text()});
  await nextPaint();D.firstPaintAt=now();
  try{await ensureLeaflet();D.coreStartedAt=now();await loadScript('/assets/runtime/tak-map-core-i553.js?v=1.4.0-i670','takMapCoreLoaderI553',15000);D.coreReadyAt=now();D.coreInitCalledAt=now();if(typeof w.__takMapCoreInitI553!=='function')throw new Error('TAK Map core did not register its initializer');await w.__takMapCoreInitI553();D.shellReadyAt=now();D.dataSyncControlStartedAt=now();await loadScript('/assets/runtime/tak-map-data-sync-i553.js?v=1.4.0-i636','takMapDataSyncControlI553',8000);await new Promise(resolve=>setTimeout(resolve,0));D.dataSyncControlReadyAt=now();if(!w.__takMapDataSyncControlReadyI553)throw new Error('Data Sync startup owner did not initialize');const dataSyncPromise=(typeof w.__takMapStartDataSyncI553==='function'?Promise.resolve(w.__takMapStartDataSyncI553()):Promise.resolve(null));await nextPaint();loadDeferredRuntime(manifestPromise,dataSyncPromise)}catch(e){recordError('startup',e,'');setStatus('Map failed to initialize: '+String(e&&e.message||e));try{d.documentElement.dataset.takMapShell='error'}catch(_){}}
}
if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',start,{once:true});else start();
D.snapshot=function(){return JSON.parse(JSON.stringify(D))};
})(window,document);
