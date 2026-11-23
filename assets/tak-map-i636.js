(function(w,d){
'use strict';
const V='i636',ENDPOINT='/api/tak-map/card-states';
const KNOWN={takGfMasterV491:'geofencing',adsbHeaderEnableV476:'adsb',dataSyncHeaderEnableV476:'data_sync',satEnableV409:'satellite',gatewayDataMasterV476:'gateway_data',localDataHeaderEnableV486:'local_data'};
let states={};
function text(v){return String(v==null?'':v).trim()}
function load(){try{const x=new XMLHttpRequest();x.open('GET',ENDPOINT+'?_='+Date.now(),false);x.withCredentials=true;x.send(null);if(x.status>=200&&x.status<300){const j=JSON.parse(x.responseText||'{}');if(j&&j.states&&typeof j.states==='object')states=j.states}}catch(_){}}
function b(k){return Object.prototype.hasOwnProperty.call(states,k)?!!states[k]:null}
function seed(){try{let v=b('geofencing');if(v!==null)sessionStorage.setItem('takmap.geofence.master',v?'1':'0')}catch(_){}try{let v=b('adsb');if(v!==null)localStorage.setItem('takmap.adsb.localDisabled',v?'0':'1')}catch(_){}try{let v=b('data_sync');if(v!==null)localStorage.setItem('takmap.dataSync.disabled',v?'0':'1')}catch(_){}try{let v=b('gateway_data');if(v!==null)localStorage.setItem('takmap.gatewayData.master',v?'1':'0')}catch(_){}try{let v=b('satellite');if(v!==null){let p={};try{p=JSON.parse(localStorage.getItem('takMapSatellitePrefsV409')||'{}')||{}}catch(_){}p.enabled=v;localStorage.setItem('takMapSatellitePrefsV409',JSON.stringify(p))}}catch(_){}
}
function titleKey(el){if(!el)return'';if(KNOWN[el.id])return KNOWN[el.id];const panel=el.closest&&el.closest('.panel');if(!panel)return'';const inHeader=!!(el.closest('.tak-card-header-actions-v491,.gateway-master-actions,.tak-gf-head-actions-v491')||el===panel.querySelector(':scope > h2 input'));if(!inHeader)return'';if(el.id)return 'id:'+el.id;const h=panel.querySelector('h2');const t=text(h&&h.textContent).replace(/[▸▾]/g,'').replace(/\s+/g,' ');return t?'title:'+t:''}
function apply(el){if(!el||el.type!=='checkbox'||el.dataset.takI634Hydrated==='1')return;const key=titleKey(el);if(!key||!Object.prototype.hasOwnProperty.call(states,key))return;el.dataset.takI634Hydrated='1';const want=!!states[key];if(el.checked!==want){el.checked=want;try{el.dispatchEvent(new Event('change',{bubbles:true}))}catch(_){}}}
function applyAll(root){try{if(root&&root.matches&&root.matches('input[type=checkbox]'))apply(root);(root||d).querySelectorAll&&Array.from((root||d).querySelectorAll('input[type=checkbox]')).forEach(apply)}catch(_){}}
function save(key,enabled){states[key]=!!enabled;try{fetch(ENDPOINT,{method:'POST',credentials:'same-origin',cache:'no-store',headers:{'Content-Type':'application/json'},body:JSON.stringify({key:key,enabled:!!enabled})}).catch(()=>{})}catch(_){}}
function installCapture(){d.addEventListener('change',ev=>{const el=ev.target;if(!el||el.type!=='checkbox')return;const key=titleKey(el);if(key)save(key,!!el.checked)},true)}
function esc(s){return text(s).replace(/[&<>\"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;'}[c]||c))}
function binding(name){try{return Object.prototype.hasOwnProperty.call(w,name)?w[name]:(0,eval)(name)}catch(_){return null}}
function currentObjects(){const ds=binding('lastDataSync')||w.__takMapLastDataSyncJsonI570||w.__takMapLastDataSyncJsonI553||{};return Array.isArray(ds.objects)?ds.objects:[]}
function ensureSearch(){const panel=d.getElementById('dataSyncPanelV476')||Array.from(d.querySelectorAll('.panel')).find(p=>/^Data Sync\b/i.test(text(p.querySelector('h2')&&p.querySelector('h2').textContent)));if(!panel||d.getElementById('takDataSyncGlobalSearchI634'))return;const body=panel.querySelector('.panel-body');const rows=d.getElementById('dataSyncRows');if(!body||!rows)return;const host=d.createElement('div');host.id='takDataSyncGlobalSearchI634';host.className='tak-ds-search-i634';host.innerHTML='<input id="takDataSyncSearchInputI634" type="search" placeholder="Search all Mission objects" autocomplete="off"><div id="takDataSyncSearchResultsI634" class="tak-ds-search-results-i634" hidden></div>';body.insertBefore(host,rows);const input=host.querySelector('input'),results=host.querySelector('div');input.addEventListener('input',()=>{const q=text(input.value).toLowerCase();if(!q){results.hidden=true;results.innerHTML='';return}const objs=currentObjects(),hits=[];objs.forEach((o,i)=>{const ms=Array.isArray(o.mission_memberships)?o.mission_memberships:[];const hay=[o.callsign,o.name,o.uid,o.id,o.type,o.cot_type,o.category,...ms].map(text).join(' ').toLowerCase();if(hay.includes(q))hits.push([o,i,ms])});results.innerHTML=hits.slice(0,40).map(([o,i,ms])=>'<button type="button" data-i="'+i+'"><b>'+esc(o.callsign||o.name||o.uid||o.id||'Object')+'</b><small>'+esc((o.type||o.cot_type||'Object')+(ms.length?' · '+ms.join(', '):''))+'</small></button>').join('')||'<span>No matching Mission objects.</span>';results.hidden=false});results.addEventListener('click',ev=>{const btn=ev.target.closest('button[data-i]');if(!btn)return;const i=Number(btn.dataset.i);try{const fn=binding('centerDataSyncIndex');if(typeof fn==='function')fn(i)}catch(_){}results.hidden=true})}
function style(){if(d.getElementById('takI634Style'))return;const s=d.createElement('style');s.id='takI634Style';s.textContent='.tak-ds-search-i634{margin:7px 0}.tak-ds-search-i634>input{width:100%;padding:7px 9px;border:1px solid #334553;border-radius:8px;background:#091018;color:#eef5f8}.tak-ds-search-results-i634{max-height:210px;overflow:auto;margin-top:5px;border:1px solid rgba(255,255,255,.12);border-radius:8px;background:#0a1118}.tak-ds-search-results-i634 button{display:block;width:100%;margin:0;padding:7px 9px;text-align:left;border:0;border-bottom:1px solid rgba(255,255,255,.07);border-radius:0;background:transparent;color:#eef5f8}.tak-ds-search-results-i634 button small{display:block;color:#8fa2ad;margin-top:2px}.tak-ds-search-results-i634>span{display:block;padding:8px;color:#8fa2ad}';d.head.appendChild(s)}
load();seed();w.__takMapCardStatesI634=states;installCapture();
function boot(){style();applyAll(d);ensureSearch();if(w.MutationObserver){const mo=new MutationObserver(ms=>{for(const m of ms)for(const n of m.addedNodes||[])if(n&&n.nodeType===1){applyAll(n);ensureSearch()}});mo.observe(d.body,{childList:true,subtree:true})}setTimeout(ensureSearch,500);setTimeout(ensureSearch,2500)}
if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
w.TakMapCardStateI634=Object.freeze({version:V,snapshot:()=>Object.assign({},states),refresh:()=>{load();seed();applyAll(d);return Object.assign({},states)}});
})(window,document);

/* TAK Map i636 canonical TAK shape rendering + backward compatibility */
(function(w,d){
'use strict';
const V='i636';
function text(v){return String(v==null?'':v).trim()}
function binding(name){try{return Object.prototype.hasOwnProperty.call(w,name)?w[name]:(0,eval)(name)}catch(_){return null}}
function assign(name,fn){try{w[name]=fn}catch(_){}try{(0,eval)(name+'=window.'+name)}catch(_){}return fn}
function nativeShape(o){const t=text(o&&(o.cot_type||o.type||o.event_type)).toLowerCase();return !!(o&&o.tak_shape_i636)||/^u-d-/.test(t)||/^u-r-b-(?:c-c|bullseye)/.test(t)}
function closedShape(o){if(o&&typeof o.shape_closed_i636==='boolean')return o.shape_closed_i636;const t=text(o&&(o.cot_type||o.type)).toLowerCase();return ['u-d-r','u-d-p','u-d-c-c','u-d-c-e','u-d-v','u-d-v-m','u-r-b-c-c','u-r-b-bullseye'].includes(t)}
function styleFor(o){let color=text(o&&o.color)||text(o&&o.style_i636&&o.style_i636.stroke_css)||'#ffb000';let fill=text(o&&o.fill_color)||text(o&&o.style_i636&&o.style_i636.fill_css)||color;let weight=Number(o&&o.weight);if(!Number.isFinite(weight))weight=Number(o&&o.style_i636&&o.style_i636.weight);if(!Number.isFinite(weight))weight=2;weight=Math.max(.5,Math.min(12,weight));let opacity=Number(o&&o.opacity);if(!Number.isFinite(opacity))opacity=Number(o&&o.style_i636&&o.style_i636.stroke_opacity);if(!Number.isFinite(opacity))opacity=.9;let fillOpacity=Number(o&&o.fill_opacity);if(!Number.isFinite(fillOpacity))fillOpacity=Number(o&&o.style_i636&&o.style_i636.fill_opacity);if(!Number.isFinite(fillOpacity))fillOpacity=.18;let line=text(o&&(o.line_style||o.strokeStyle)||(o&&o.style_i636&&o.style_i636.line_style)).toLowerCase();return {color,fillColor:fill,weight,opacity:Math.max(0,Math.min(1,opacity)),fillOpacity:Math.max(0,Math.min(1,fillOpacity)),dashArray:/dash|dot/.test(line)?'8,7':null,bubblingMouseEvents:false}}
function patchAreaRows(){const old=binding('shapeAreaPopupRows');if(typeof old!=='function'||old.__takI636)return;const fn=function(o){if(nativeShape(o)&&!closedShape(o))return'';return old.apply(this,arguments)};fn.__takI636=true;fn.__takI636Base=old;assign('shapeAreaPopupRows',fn)}
function patchCategory(){const old=binding('dataSyncCategory');if(typeof old!=='function'||old.__takI636)return;const fn=function(o){if(nativeShape(o))return 'Shapes / Areas';return old.apply(this,arguments)};fn.__takI636=true;fn.__takI636Base=old;assign('dataSyncCategory',fn)}
function patchRenderer(){const old=binding('addObjectLayer');if(typeof old!=='function'||old.__takI636)return;const fn=function(group,o,sourceKey){
  if(!nativeShape(o))return old.apply(this,arguments);
  let layer=null;
  try{
    const shapeCoords=binding('shapeCoords'),collect=binding('collectCoordPairs'),centerFn=binding('objectCenter');
    const popupFn=binding('layerPopupForObject'),stabilize=binding('stabilizeLayerPopup'),stamp=binding('takMapStampSelectionIdentityV478'),search=binding('addSearchItem');
    const pts=typeof shapeCoords==='function'?shapeCoords(o):(o&&o.coords)||[];
    const flat=typeof collect==='function'?collect(pts):[];
    const closed=closedShape(o),need=closed?3:2;
    if(flat.length<need)return null;
    const opts=styleFor(o),popup=typeof popupFn==='function'?popupFn(o,'Shapes / Areas'):'';
    if(closed){layer=w.L.polygon(pts,opts).bindPopup(popup,{autoPan:false,keepInView:false,autoClose:false,closeOnClick:false}).addTo(group)}
    else{const lineOpts=Object.assign({},opts);delete lineOpts.fillColor;delete lineOpts.fillOpacity;layer=w.L.polyline(pts,lineOpts).bindPopup(popup,{autoPan:false,keepInView:false,autoClose:false,closeOnClick:false}).addTo(group)}
    if(typeof stabilize==='function')stabilize(layer);o.__layer=layer;
    if(typeof stamp==='function')try{stamp(group,o,sourceKey,layer)}catch(_){}
    const cen=typeof centerFn==='function'?centerFn(o):null;
    if(cen&&typeof search==='function')search(sourceKey||'datasync',(sourceKey==='imported'?'Imported ':'Data Sync ')+'Shapes / Areas',o.callsign||o.name||o.uid||o.id||'Shape',cen[0],cen[1],layer,o);
    return layer;
  }catch(e){try{console.warn('[TAK Map i636] shape render skipped',o,e)}catch(_){}return null}
  };
  fn.__takI636=true;fn.__takI636Base=old;assign('addObjectLayer',fn)
}
function mark(){try{d.documentElement.dataset.takShapeCompat='i636'}catch(_){}w.__takMapShapeCompatI636={version:V,nativeTypes:['u-d-r','u-d-p','u-d-f','u-d-f-m','u-d-c-c','u-d-c-e','u-d-v','u-d-v-m','u-r-b-c-c','u-r-b-bullseye'],canonicalOutput:true,legacyRead:true}}
function boot(){patchAreaRows();patchCategory();patchRenderer();mark()}
if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',()=>setTimeout(boot,50),{once:true});else setTimeout(boot,50);
[200,600,1200,2500,5000,9000].forEach(ms=>setTimeout(boot,ms));
})(window,document);
