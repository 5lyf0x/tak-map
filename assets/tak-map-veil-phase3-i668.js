/* TAK Map i668 VEIL Phase 3: non-destructive, strict identity display broker.
   Source databases, source groups, native icons and CoT are never modified.
   Native cross-source suppression is intentionally OFF by default. */
(()=>{'use strict';
const byId=new Map();let source=null,view=null,previousView=null;
const esc=s=>String(s??'').replace(/[&<>"']/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[x]));
const timestamp=o=>Number(o.timestamp)||0;
const eligible=o=>Number.isFinite(Number(o.lat))&&Number.isFinite(Number(o.lon))&&Math.abs(Number(o.lat))<=90&&Math.abs(Number(o.lon))<=180&&Number(o.stale)>Date.now()/1000&&timestamp(o)<=Date.now()/1000+120;
const safeKey=o=>typeof o.canonicalKey==='string'&&/^(adsb:icao:[a-f0-9]{6}|ais:mmsi:[1-9][0-9]{8}|aprs:(?:station:[A-Z0-9-]{1,9}|object:[A-Z0-9-]{1,9}:[A-Z0-9 -]{1,50})|rid:[a-z0-9_]+:[A-Z0-9-]{4,64})$/.test(o.canonicalKey)?o.canonicalKey:null;
const live=o=>String(o.freshness||'LIVE').toUpperCase()!=='STALE';
function compare(a,b){const la=live(a),lb=live(b);if(la!==lb)return la?-1:1;const delta=timestamp(b)-timestamp(a);if(Math.abs(delta)>.001)return delta>0?1:-1;const pa=a.transport==='api_event'||a.transport==='api'?1:0,pb=b.transport==='api_event'||b.transport==='api'?1:0;if(pa!==pb)return pb-pa;return String(a.id).localeCompare(String(b.id))}
function select(raw,config={}){
 const active=(Array.isArray(raw)?raw:[]).filter(eligible),group=new Map();
 for(const o of active){if(config.services?.[o.service]===false)continue;
  const key=config.mergeVeilDuplicates!==false&&safeKey(o)||'unique:'+String(o.id);
  if(!group.has(key))group.set(key,[]);group.get(key).push(o);
 }
 const winners=[],uniqueCounts={adsb:0,ais:0,aprs:0,remote_id:0};
 let merged=0,nativeSuppressed=0;
 const nativeKeys=config.crossSourceDedup===true?visibleNativeKeys():null;
 for(const [key,candidates] of group){candidates.sort(compare);const chosen={...candidates[0]};
  // Preserve the elected fresh position while recovering APRS symbol data omitted by a competing transport.
  // The broker only groups validated canonical identity, so no station/callsign proximity guesses.
  if(chosen.service==='aprs'&&candidates.length>1){
    const a=chosen.aprs||{},code=String(a.symbolCode||'');
    if(!code){const donor=candidates.find(o=>o!==candidates[0]&&o.service==='aprs'&&o.aprs?.symbolCode&&
      live(o)&&Math.abs(timestamp(o)-timestamp(chosen))<=90&&Number(o.stale)>Date.now()/1000);
      if(donor)chosen.aprs={...donor.aprs,...a,symbolCode:donor.aprs.symbolCode,
        symbolTable:a.symbolTable||donor.aprs.symbolTable,overlay:a.overlay||donor.aprs.overlay,
        objectType:a.objectType||donor.aprs.objectType,weather:a.weather==='true'?'true':donor.aprs.weather};
    }
  }
  // A heading is a time-sensitive property of the same aircraft. Never copy one from unrelated identities.
  if(chosen.service==='adsb'&&(chosen.heading===null||chosen.heading===undefined||chosen.heading==='')){
    const donor=candidates.find(o=>o!==candidates[0]&&o.service==='adsb'&&o.heading!==null&&
      o.heading!==undefined&&o.heading!==''&&Number.isFinite(Number(o.heading))&&live(o)&&
      Math.abs(timestamp(o)-timestamp(chosen))<=45&&Number(o.stale)>Date.now()/1000);
    if(donor)chosen.heading=donor.heading;
  }
  chosen.__veilCandidates=candidates.map(o=>({nodeId:o.nodeId,transport:o.transport||'udp',timestamp:o.timestamp,id:o.id}));
  chosen.__veilCount=candidates.length;chosen.__veilKey=key;merged+=candidates.length-1;
  if(nativeKeys && nativeKeys.has(key)){
    nativeSuppressed++;continue;
  }
  winners.push(chosen);uniqueCounts[chosen.service]=(uniqueCounts[chosen.service]||0)+1;
 }
 return {objects:winners,uniqueCounts,rawCount:active.length,merged,nativeSuppressed};
}
function visibleNativeKeys(){
 const keys=new Set();
 try{
  const native=window.TakMapVeilNativeI668?.();
  if(native?.adsbVisible||native?.terrainAdsbVisible){
   for(const a of (native.aircraft||[])){
    const x=String(a.icao||a.hex||'').toLowerCase().replace(/^icao[-:]/,'');
    if(/^[a-f0-9]{6}$/.test(x)&&Number.isFinite(Number(a.lat))&&Number.isFinite(Number(a.lon))&&
       Number(a.seen_seconds??a.seen_pos??a.seen??999)<=45)keys.add('adsb:icao:'+x);
   }
  }
 }catch(_){}
 try{
  const gateway=window.TakMapGatewayDataV476;
  if(gateway?.searchVisible&&gateway?.snapshot){
   const ids=new Set(gateway.searchVisible().map(x=>String(x.id)));
   for(const x of gateway.snapshot()){
    if(x.source!=='ais_vessels'||!ids.has(String(x.id)))continue;
    const m=String(x.properties?.metadata?.mmsi||'');
    if(/^[1-9][0-9]{8}$/.test(m)&&(!x.stale_at||Date.parse(x.stale_at)>Date.now()))
      keys.add('ais:mmsi:'+m);
   }
  }
 }catch(_){}
 return keys;
}
function provenance(o){const rows=o.__veilCandidates||[];
 return rows.length?'<div style="margin-top:6px;border-top:1px solid #4b6672;padding-top:5px"><b>Observations ('+rows.length+')</b>'+rows.slice(0,8).map(x=>'<div>'+esc(x.nodeId)+' · '+esc(x.transport)+' · '+esc(new Date(x.timestamp*1000).toLocaleTimeString())+'</div>').join('')+'</div>':'';
}
let clickHandlerI669=null;
function remove3D(){
 if(clickHandlerI669){try{clickHandlerI669.destroy()}catch(_){}clickHandlerI669=null}
 if(view&&source){try{view.dataSources.remove(source,true)}catch(_){}}
 view=null;source=null;
}
function show3D(objects){
 const scene=window.TakMapVeilSceneI668?.(),v=window.TakMapVeilVisualI669;
 if(!scene?.active||!scene.viewer||!window.Cesium){remove3D();return false}
 const viewer=scene.viewer,C=window.Cesium;
 if(view!==viewer){remove3D();view=viewer;source=new C.CustomDataSource('XTAK VEIL i669');void viewer.dataSources.add(source);
  if(typeof C.ScreenSpaceEventHandler==='function'&&viewer.scene?.canvas){
  clickHandlerI669=new C.ScreenSpaceEventHandler(viewer.scene.canvas);
  clickHandlerI669.setInputAction(ev=>{
   const picked=viewer.scene.pick(ev.position),e=picked&&picked.id,o=e&&e.__takVeilObjectI669;
   if(!o||o.service!=='adsb')return;
   if(!v?.openAdsb(o,null))viewer.selectedEntity=e;
  },C.ScreenSpaceEventType.LEFT_CLICK);
  }
 }
 const seen=new Set();
 for(const o of objects){
  const id=String(o.__veilKey||o.id);seen.add(id);
  const lat=Number(o.lat),lon=Number(o.lon);if(!Number.isFinite(lat)||!Number.isFinite(lon))continue;
  let entity=source.entities.getById(id);if(!entity)entity=source.entities.add({id});
  const local=window.TakMapTerrainOverlayHooksI669;
  const localHeight=local?.local&&typeof local.sampleLocal==='function'?local.sampleLocal(lat,lon):null;
  const place=v?.altitudePlacement(o,Number.isFinite(localHeight)?localHeight+3:null)||{height:0,reference:'CLAMP_TO_GROUND'};
  const h=place.height,ref=place.reference==='NONE'?C.HeightReference.NONE:C.HeightReference.CLAMP_TO_GROUND;
  entity.name=String(o.title||o.objectId||'VEIL');
  entity.position=C.Cartesian3.fromDegrees(lon,lat,h);
  const iconPx=v?.iconSize?.(o)||36;
  const aprsPixels=o.service==='aprs'?window.TakMapVeilAprsI672?.imgSize(o):null;
  entity.billboard={image:v?v.image(o):null,width:aprsPixels||iconPx,height:aprsPixels||iconPx,verticalOrigin:C.VerticalOrigin.CENTER,
    heightReference:ref,disableDepthTestDistance:Number.POSITIVE_INFINITY};
  entity.label=o.service==='aprs'?{text:String(o.title||o.identity?.callsign||'').slice(0,70),
    font:'bold 11px Arial',fillColor:C.Color.WHITE,showBackground:true,
    backgroundColor:C.Color.fromCssColorString('rgba(18,22,27,0.88)'),
    pixelOffset:new C.Cartesian2(27,0),horizontalOrigin:C.HorizontalOrigin.LEFT,
    verticalOrigin:C.VerticalOrigin.CENTER,disableDepthTestDistance:Number.POSITIVE_INFINITY}:undefined;
  entity.description='<div><b>XTAK VEIL</b> '+esc(o.title)+'<div>Altitude placement: '+esc(place.source||'terrain')+'</div>'+provenance(o)+'</div>';
  entity.__takVeilObjectI669=o;
 }
 for(const e of source.entities.values.slice())if(!seen.has(e.id))source.entities.remove(e);
 viewer.scene.requestRender();return true;
}
function render(objects,config,leafletRender){const elected=select(objects,config);
 if(show3D(elected.objects))leafletRender([]);else leafletRender(elected.objects);
 window.TakMapVeilPhase3StatsI668={uniqueCount:elected.objects.length,rawCount:elected.rawCount,
   merged:elected.merged,nativeSuppressed:elected.nativeSuppressed,uniqueCounts:elected.uniqueCounts};
 return elected;
}
window.TakMapVeilPhase3I668={select,render,provenance,remove3D};
})();
