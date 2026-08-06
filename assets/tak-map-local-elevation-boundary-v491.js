/* TAK Map i491 persistent Local Elevation coverage boundary */
(function(){
  'use strict';
  const V='v491', NAME='TakMapLocalElevationBoundaryV476';
  const SOURCE_NAME='TAK Local Elevation Coverage Boundary v491';
  const LEGACY_RE=/tak-local-dem-bounds-v(?:320|352|400|401|402)|local elevation coverage boundary/i;
  const RED_CSS='#ff2020';
  const S={
    installedAt:Date.now(),viewer:null,dataSource:null,attached:false,signature:'',
    refreshes:0,rebuilds:0,reattaches:0,viewerChanges:0,legacyRemoved:0,
    lastReason:'',lastError:'',lastRefreshAt:0,lastVisibleAt:0,
    busy:false,queued:false,timer:0,watchdog:0,observer:null,eventRemovers:[],stopped:false
  };

  function sourceIsLocal(){
    try{return String(window.terrain3DElevationSource||localStorage.getItem('takMapTerrainElevationSource')||'streamed').toLowerCase()==='local'}catch(_){return false}
  }
  function currentViewer(){
    try{return (typeof terrain3DViewer!=='undefined'&&terrain3DViewer)||window.terrain3DViewer||null}catch(_){return window.terrain3DViewer||null}
  }
  function paneActive(){
    try{const p=document.getElementById('terrain3dPane');return !!((p&&p.classList&&p.classList.contains('active'))||(document.body&&document.body.classList&&document.body.classList.contains('terrain-3d-active')))}catch(_){return false}
  }
  function tileValues(){
    try{
      const src=window.takLocalElevation&&window.takLocalElevation.tiles;
      const vals=src instanceof Map?Array.from(src.values()):[];
      const seen=new Set(),out=[];
      for(const t of vals){
        if(!t)continue;
        const id=String(t.id||t.name||'');
        const b=bboxOf(t);
        if(!b)continue;
        const key=id||[b.west,b.south,b.east,b.north].join(',');
        if(seen.has(key))continue;
        seen.add(key);out.push({id:key,bbox:b});
      }
      return out;
    }catch(_){return []}
  }
  function bboxOf(t){
    try{
      let west=Number(t.lon0),east=Number(t.lon1),south=Number(t.lat0),north=Number(t.lat1);
      if(![west,east,south,north].every(Number.isFinite)&&Array.isArray(t.bbox)&&t.bbox.length>=4){
        west=Number(t.bbox[0]);south=Number(t.bbox[1]);east=Number(t.bbox[2]);north=Number(t.bbox[3]);
      }
      if(![west,east,south,north].every(Number.isFinite))return null;
      west=Math.max(-180,Math.min(180,west));east=Math.max(-180,Math.min(180,east));
      south=Math.max(-90,Math.min(90,south));north=Math.max(-90,Math.min(90,north));
      const w=Math.min(west,east),e=Math.max(west,east),s=Math.min(south,north),n=Math.max(south,north);
      return e>w&&n>s?{west:w,east:e,south:s,north:n}:null;
    }catch(_){return null}
  }
  function signature(items){return items.map(x=>x.id+':'+[x.bbox.west,x.bbox.south,x.bbox.east,x.bbox.north].join(',')).sort().join('|')}
  function dataSourceAttached(v,ds){
    try{return !!(v&&v.dataSources&&ds&&typeof v.dataSources.contains==='function'&&v.dataSources.contains(ds))}catch(_){return false}
  }
  function removeEventHooks(){
    for(const rm of S.eventRemovers.splice(0)){try{rm()}catch(_){}}
  }
  function bindViewerEvents(v){
    if(!v||v.__takLocalBoundaryEventsV476)return;
    try{v.__takLocalBoundaryEventsV476=true}catch(_){}
    const add=(ev,reason)=>{
      try{if(ev&&typeof ev.addEventListener==='function'){const rm=ev.addEventListener(()=>schedule(reason,60));if(typeof rm==='function')S.eventRemovers.push(rm)}}catch(_){}
    };
    add(v.camera&&v.camera.moveEnd,'camera-moveend');
    add(v.scene&&v.scene.morphComplete,'scene-morph');
    add(v.terrainProviderChanged,'terrain-provider-change');
    add(v.imageryLayers&&v.imageryLayers.layerAdded,'imagery-added');
    add(v.imageryLayers&&v.imageryLayers.layerRemoved,'imagery-removed');
    add(v.imageryLayers&&v.imageryLayers.layerMoved,'imagery-moved');
    try{
      const ev=v.dataSources&&v.dataSources.dataSourceRemoved;
      if(ev&&typeof ev.addEventListener==='function'){
        const rm=ev.addEventListener(ds=>{if(ds===S.dataSource){S.attached=false;schedule('data-source-removed',20)}});
        if(typeof rm==='function')S.eventRemovers.push(rm);
      }
    }catch(_){}
  }
  function cleanupLegacy(v){
    try{
      const vals=(v&&v.entities&&v.entities.values)||[];
      for(const ent of vals.slice?vals.slice():Array.from(vals)){
        try{
          const text=String(ent&&ent.id||'')+' '+String(ent&&ent.name||'');
          if(LEGACY_RE.test(text)){v.entities.remove(ent);S.legacyRemoved++}
        }catch(_){}
      }
      try{window.__v402LocalTerrainBounds=[]}catch(_){}
    }catch(_){}
  }
  function clearDataSource(){
    try{if(S.dataSource&&S.dataSource.entities)S.dataSource.entities.removeAll()}catch(_){}
    S.signature='';
  }
  async function ensureDataSource(v){
    if(!v||!window.Cesium)return null;
    if(S.viewer!==v){
      removeEventHooks();
      S.viewer=v;S.attached=false;S.signature='';S.viewerChanges++;
      S.dataSource=null;
    }
    if(!S.dataSource){
      S.dataSource=new window.Cesium.CustomDataSource(SOURCE_NAME);
      try{S.dataSource.name=SOURCE_NAME}catch(_){}
    }
    if(!dataSourceAttached(v,S.dataSource)){
      const added=v.dataSources.add(S.dataSource);
      if(added&&typeof added.then==='function')await added;
      S.attached=true;S.reattaches++;
    }else S.attached=true;
    try{v.dataSources.raiseToTop(S.dataSource)}catch(_){}
    try{S.dataSource.show=true}catch(_){}
    bindViewerEvents(v);
    return S.dataSource;
  }
  function red(C){
    try{return C.Color.fromCssColorString(RED_CSS).withAlpha(.98)}catch(_){return C.Color&&C.Color.RED?C.Color.RED:RED_CSS}
  }
  function addBoundaryEntity(ds,item,index){
    const C=window.Cesium,b=item.bbox;
    const degrees=[b.west,b.south,b.east,b.south,b.east,b.north,b.west,b.north,b.west,b.south];
    const material=red(C);
    return ds.entities.add({
      id:'tak-local-dem-bounds-v491-'+index+'-'+String(item.id).replace(/[^a-z0-9_.-]/gi,'_').slice(0,80),
      name:'Local elevation coverage boundary v491',
      show:true,
      polyline:{
        positions:C.Cartesian3.fromDegreesArray(degrees),
        width:5,
        clampToGround:true,
        material:material,
        depthFailMaterial:material,
        zIndex:2147483647,
        arcType:C.ArcType&&C.ArcType.GEODESIC!==undefined?C.ArcType.GEODESIC:undefined,
        shadows:C.ShadowMode&&C.ShadowMode.DISABLED!==undefined?C.ShadowMode.DISABLED:undefined,
        show:true
      },
      properties:{takMapLayer:'local-elevation-coverage-boundary',takMapVersion:V}
    });
  }
  async function refresh(reason,force){
    if(S.stopped)return diagnostics();
    if(S.busy){S.queued=true;return diagnostics()}
    S.busy=true;S.lastReason=String(reason||'refresh');S.lastError='';
    try{
      const v=currentViewer();
      if(!sourceIsLocal()){
        clearDataSource();
        try{if(S.dataSource)S.dataSource.show=false}catch(_){}
        cleanupLegacy(v);
        return diagnostics();
      }
      if(!v||!window.Cesium)return diagnostics();
      const ds=await ensureDataSource(v);
      cleanupLegacy(v);
      const items=tileValues(),sig=signature(items);
      const entityCount=ds&&ds.entities&&ds.entities.values?ds.entities.values.length:0;
      if(force||sig!==S.signature||entityCount!==items.length){
        ds.entities.removeAll();
        items.forEach((item,i)=>addBoundaryEntity(ds,item,i));
        S.signature=sig;S.rebuilds++;
      }
      try{ds.show=true}catch(_){}
      try{window.__v402LocalTerrainBounds=Array.from((ds.entities&&ds.entities.values)||[])}catch(_){}
      try{v.dataSources.raiseToTop(ds)}catch(_){}
      try{v.scene&&v.scene.requestRender&&v.scene.requestRender()}catch(_){}
      S.refreshes++;S.lastRefreshAt=Date.now();
      if(items.length){S.lastVisibleAt=Date.now()}
      return diagnostics();
    }catch(e){
      S.lastError=String(e&&e.message||e);
      try{console.warn('[TAK Map] local elevation boundary v491 refresh failed',e)}catch(_){}
      return diagnostics();
    }finally{
      S.busy=false;
      if(S.queued){S.queued=false;schedule('queued',40)}
    }
  }
  function schedule(reason,delay){
    if(S.stopped)return;
    clearTimeout(S.timer);
    S.timer=setTimeout(()=>refresh(reason||'scheduled',false),Number(delay)||120);
  }
  function wrap(name,delay){
    try{
      const old=window[name];
      if(typeof old!=='function'||old.__takLocalBoundaryV476)return;
      const fn=function(){
        const out=old.apply(this,arguments);
        if(out&&typeof out.then==='function')out.then(()=>schedule(name,delay||100)).catch(()=>schedule(name+'-error',delay||100));
        else schedule(name,delay||100);
        return out;
      };
      fn.__takLocalBoundaryV476=true;fn.__takLocalBoundaryPrevious=old;window[name]=fn;
      try{eval(name+'=window["'+name+'"]')}catch(_){}
    }catch(_){}
  }
  function installWrappers(){
    ['ensureTerrain3DViewer','enableTerrain3D','toggleTerrain3D','refreshTerrain3DAll','refreshTerrain3DBaseLayer','setTerrain3DQuality','setTerrain3DElevationSource'].forEach(n=>wrap(n,n==='ensureTerrain3DViewer'?250:120));
  }
  function patchDiagnostics(){
    try{
      const old=window.TakMapDiagnostics;
      if(typeof old!=='function'||old.__takLocalBoundaryV476)return;
      const fn=function(){const out=old.apply(this,arguments)||{};out.version=V;out.localElevationBoundary=diagnostics();return out};
      fn.__takLocalBoundaryV476=true;fn.__takLocalBoundaryPrevious=old;window.TakMapDiagnostics=fn;
    }catch(_){}
  }
  function watchdog(){
    if(S.stopped)return;
    try{
      installWrappers();patchDiagnostics();
      const v=currentViewer();
      if(!sourceIsLocal()){
        if(S.dataSource&&S.dataSource.show!==false){clearDataSource();S.dataSource.show=false}
        cleanupLegacy(v);return;
      }
      if(!v||!window.Cesium)return;
      const items=tileValues();
      const count=S.dataSource&&S.dataSource.entities&&S.dataSource.entities.values?S.dataSource.entities.values.length:0;
      const needs=S.viewer!==v||!dataSourceAttached(v,S.dataSource)||!S.dataSource||S.dataSource.show===false||count!==items.length||S.signature!==signature(items);
      if(needs)refresh('watchdog-repair',true);
      else{
        try{v.dataSources.raiseToTop(S.dataSource)}catch(_){}
        if(paneActive())try{v.scene&&v.scene.requestRender&&v.scene.requestRender()}catch(_){}
      }
    }catch(e){S.lastError=String(e&&e.message||e)}
  }
  function diagnostics(){
    const v=currentViewer();
    let entityCount=0,attached=false,show=false;
    try{entityCount=S.dataSource&&S.dataSource.entities&&S.dataSource.entities.values?S.dataSource.entities.values.length:0}catch(_){}
    try{attached=dataSourceAttached(v,S.dataSource)}catch(_){}
    try{show=!!(S.dataSource&&S.dataSource.show!==false)}catch(_){}
    return {
      version:V,installedAt:S.installedAt,sourceLocal:sourceIsLocal(),terrainPaneActive:paneActive(),viewerPresent:!!v,
      viewerCurrent:S.viewer===v,dedicatedDataSource:true,dataSourceName:SOURCE_NAME,dataSourceAttached:attached,dataSourceShown:show,
      entityCount,decodedCoverageAreas:tileValues().length,clampToGround:true,depthFailMaterial:true,zIndex:2147483647,
      width:5,color:RED_CSS,alwaysVisiblePolicy:'dedicated-data-source + ground-clamped + depth-fail + raise-to-top + lifecycle watchdog',
      refreshes:S.refreshes,rebuilds:S.rebuilds,reattaches:S.reattaches,viewerChanges:S.viewerChanges,legacyRemoved:S.legacyRemoved,
      lastReason:S.lastReason,lastError:S.lastError,lastRefreshAt:S.lastRefreshAt,lastVisibleAt:S.lastVisibleAt,watchdogActive:!!S.watchdog
    };
  }
  function stop(){S.stopped=true;clearTimeout(S.timer);clearInterval(S.watchdog);S.watchdog=0;removeEventHooks()}
  function boot(){
    installWrappers();patchDiagnostics();
    try{
      if(!S.observer&&window.MutationObserver){
        S.observer=new MutationObserver(()=>schedule('terrain-dom-change',80));
        const pane=document.getElementById('terrain3dPane');
        if(pane)S.observer.observe(pane,{attributes:true,attributeFilter:['class','style']});
        if(document.body)S.observer.observe(document.body,{attributes:true,attributeFilter:['class']});
      }
    }catch(_){}
    schedule('boot',250);
    if(!S.watchdog)S.watchdog=setInterval(watchdog,1800);
    try{console.info('[TAK Map] local-elevation-boundary-v491: loaded')}catch(_){}
  }

  const api={version:V,refresh:(reason,force)=>refresh(reason||'manual',force!==false),diagnostics,stop};
  window[NAME]=api;
  window.getTakMapLocalElevationBoundaryDiagnosticsV476=diagnostics;
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>setTimeout(boot,80),{once:true});else setTimeout(boot,80);
})();
