(function(w,d){
'use strict';
const V='i491';
const S={loadedAt:Date.now(),dataSyncChipWrites:0,dataSyncChipSkips:0,dataSyncLastText:'',dataSyncLegacyMutations:0,satelliteOrderFixes:0,satelliteOrdered:false,adsbHeader:false,adsbManualCollapseOwner:false,adsbHeaderToggle:false,adsbToggleChanges:0,adsbFilters:false,adsbFilterRows:0,satelliteHeader:false,satelliteManualCollapseOwner:false,satelliteHeaderToggle:false,satelliteToggleChanges:0,satelliteStepper:false,dataSyncHeader:false,dataSyncManualCollapseOwner:false,dataSyncHeaderToggle:false,dataSyncToggleChanges:0,localDataHeader:false,localDataHeaderToggle:false,localDataToggleChanges:0,headerCounts:false,countObserver:false,countUpdates:0,adsbAltitude:false,adsbAltitudeChanges:0,adsbAltitudeMode:'all',adsbAltitudeUnit:'',adsbAltitudeThresholdMeters:3048,adsbAltitudeThresholdActive:true,legacyAdsbObserverDisconnected:false,captureSwitchOwner:true,observer:false,lastError:'',runs:0};
const $=id=>d.getElementById(id);
const q=(s,r)=>{try{return (r||d).querySelector(s)}catch(_){return null}};
const qa=(s,r)=>{try{return Array.from((r||d).querySelectorAll(s))}catch(_){return[]}};
function stop(ev){try{ev.stopPropagation()}catch(_){}try{ev.stopImmediatePropagation()}catch(_){} }
function slug(v){return String(v||'section').toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$/g,'')||'section'}
function findPanel(title){return qa('.sidebar .panel,.panel').find(p=>{const h=q(':scope > h2',p)||q('h2',p);if(!h)return false;const named=q('.tak-card-title-v491',h);if(named)return String(named.textContent||'').trim().toLowerCase()===String(title||'').toLowerCase();const clone=h.cloneNode(true);qa('.chip,.tak-header-count-v491,.panel-toggle',clone).forEach(n=>n.remove());return String(clone.textContent||'').replace(/[▸▾]/g,'').trim().toLowerCase()===String(title||'').toLowerCase()})||null}
function installCss(){
 if($('takMapCardControlsStyleV476'))return;
 const st=d.createElement('style');st.id='takMapCardControlsStyleV476';st.textContent=`
.panel>.tak-card-header-v491{display:flex!important;align-items:center!important;justify-content:space-between!important;gap:8px!important;min-height:28px!important;margin:0!important;cursor:pointer!important;user-select:none!important}
.panel>.tak-card-header-v491 .tak-card-title-v491{flex:1;min-width:0;color:inherit}
.tak-card-header-actions-v491{display:grid!important;grid-template-columns:max-content 40px 12px!important;align-items:center!important;justify-content:end!important;column-gap:8px!important;margin-left:auto!important}
.tak-card-chevron-v491{position:static!important;right:auto!important;margin:0!important;min-width:12px!important;text-align:right!important;color:var(--accent,#ff6f2e)!important;font-weight:1000!important}
.tak-header-switch-v491{position:relative;display:inline-flex;align-items:center;flex:0 0 auto;margin:0!important}
.tak-header-switch-v491>input{position:absolute!important;width:1px!important;height:1px!important;opacity:0!important;pointer-events:none!important;clip:rect(0 0 0 0)!important;clip-path:inset(50%)!important}
.tak-header-switch-button-v491{position:relative!important;display:block!important;width:40px!important;height:22px!important;min-width:40px!important;min-height:22px!important;margin:0!important;padding:0!important;border:1px solid #455561!important;border-radius:999px!important;background:#17212a!important;box-shadow:inset 0 1px 3px rgba(0,0,0,.45)!important;transition:background .16s ease,border-color .16s ease!important;cursor:pointer!important}
.tak-header-switch-knob-v491{position:absolute;top:3px;left:3px;width:14px;height:14px;border-radius:999px;background:#91a2ad;transition:transform .16s ease,background .16s ease,box-shadow .16s ease;pointer-events:none}
.tak-header-switch-button-v491[aria-checked="true"]{border-color:rgba(57,217,138,.65)!important;background:rgba(57,217,138,.18)!important}
.tak-header-switch-button-v491[aria-checked="true"] .tak-header-switch-knob-v491{transform:translateX(18px);background:#39d98a;box-shadow:0 0 8px rgba(57,217,138,.65)}
.tak-header-switch-button-v491:focus-visible{outline:2px solid var(--accent,#ff6f2e)!important;outline-offset:2px!important}

.adsb-settings-grid{display:grid!important;grid-template-columns:minmax(0,1fr) minmax(0,1fr)!important;gap:7px!important}
.adsb-settings-grid>.adsb-altitude-filter-v491{grid-column:1!important;order:20!important}.adsb-settings-grid>.adsb-altitude-threshold-v491{grid-column:2!important;order:21!important}.adsb-settings-grid>.adsb-center-source-row-v491{grid-column:1!important;order:30!important}.adsb-settings-grid>.adsb-center-combo-row-v491{grid-column:2!important;order:31!important}
.adsb-type-grid-v491{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:7px!important;margin-top:8px!important;padding:0!important;border:0!important;background:transparent!important}
.adsb-type-card-v491{--type-color:#9aa6af;position:relative!important;display:grid!important;grid-template-columns:34px minmax(0,1fr) 17px!important;gap:8px!important;align-items:center!important;min-height:44px!important;margin:0!important;padding:7px 9px 7px 7px!important;border:1px solid rgba(255,255,255,.105)!important;border-radius:9px!important;background:rgba(255,255,255,.022)!important;color:#e9f0f3!important;cursor:pointer!important;transition:border-color .14s ease,background .14s ease,opacity .14s ease,transform .14s ease!important;text-transform:none!important;letter-spacing:0!important}
.adsb-type-card-v491:hover{transform:translateY(-1px)!important;border-color:rgba(255,255,255,.22)!important;background:rgba(255,255,255,.034)!important}.adsb-type-card-v491.is-checked-v491{border-color:rgba(255,111,46,.58)!important;background:rgba(255,111,46,.085)!important}.adsb-type-card-v491:not(.is-checked-v491){opacity:.5!important}
.adsb-type-card-v491[data-type="civil"]{--type-color:#51d88a}.adsb-type-card-v491[data-type="govt"]{--type-color:#b56cff}.adsb-type-card-v491[data-type="military"]{--type-color:#5aa9ff}.adsb-type-card-v491[data-type="unknown"]{--type-color:#9aa6af}
.adsb-type-checkbox-v491{position:absolute!important;opacity:0!important;pointer-events:none!important;width:1px!important;height:1px!important}
.adsb-type-badge-v491{width:34px!important;height:34px!important;display:grid!important;place-items:center!important;border:1px solid var(--type-color)!important;border-radius:8px!important;background:rgba(255,255,255,.025)!important;color:var(--type-color)!important;font-size:.59rem!important;font-weight:950!important;letter-spacing:.05em!important}
.adsb-type-copy-v491{min-width:0!important}.adsb-type-name-v491{display:block!important;color:#e9f0f3!important;font-size:.72rem!important;font-weight:900!important;letter-spacing:.045em!important;text-transform:uppercase!important}
.adsb-type-check-v491{width:17px!important;height:17px!important;display:grid!important;place-items:center!important;border:1px solid rgba(255,255,255,.24)!important;border-radius:5px!important;background:rgba(0,0,0,.24)!important;color:transparent!important;font-size:.68rem!important;font-weight:950!important}.adsb-type-card-v491.is-checked-v491 .adsb-type-check-v491{border-color:#ff6f2e!important;background:#ff6f2e!important;color:#111!important}
@media(max-width:430px){.adsb-settings-grid>.adsb-altitude-filter-v491,.adsb-settings-grid>.adsb-altitude-threshold-v491,.adsb-settings-grid>.adsb-center-source-row-v491,.adsb-settings-grid>.adsb-center-combo-row-v491{grid-column:1/-1!important}.adsb-type-grid-v491{grid-template-columns:1fr!important}}
.adsb-altitude-label-v491{display:grid!important;gap:4px!important;min-width:0!important}
.adsb-altitude-label-v491>span:first-child{color:#8fa2ad!important;font-size:.68rem!important;font-weight:800!important;letter-spacing:.06em!important;text-transform:uppercase!important}
.adsb-altitude-select-v491{width:100%!important;min-width:0!important}
.adsb-altitude-value-v491{display:grid!important;grid-template-columns:minmax(0,1fr) auto!important;align-items:stretch!important;min-width:0!important;overflow:hidden!important;border:1px solid #334553!important;border-radius:10px!important;background:#091018!important}
.adsb-altitude-value-v491:focus-within{border-color:rgba(255,111,46,.72)!important;box-shadow:0 0 0 2px rgba(255,111,46,.10)!important}
.adsb-altitude-value-v491>input[type=number]{width:100%!important;min-width:0!important;margin:0!important;padding:7px 8px!important;border:0!important;border-radius:0!important;background:transparent!important;color:#eef5f8!important;box-shadow:none!important;outline:none!important;-moz-appearance:textfield!important;appearance:textfield!important}
.adsb-altitude-value-v491>input[type=number]::-webkit-inner-spin-button,.adsb-altitude-value-v491>input[type=number]::-webkit-outer-spin-button{-webkit-appearance:none!important;appearance:none!important;margin:0!important}
.adsb-altitude-unit-v491{min-width:38px!important;margin:0!important;padding:0 9px!important;border:0!important;border-left:1px solid rgba(255,255,255,.14)!important;border-radius:0!important;background:rgba(255,255,255,.035)!important;color:#fff!important;font-size:.72rem!important;font-weight:800!important;text-transform:none!important;cursor:pointer!important}
.adsb-altitude-unit-v491:hover,.adsb-altitude-unit-v491:focus-visible{background:rgba(255,255,255,.09)!important;color:#fff!important;outline:none!important}
.adsb-altitude-label-v491.is-all-v491 .adsb-altitude-value-v491{opacity:.48!important}
.adsb-altitude-label-v491.is-all-v491 .adsb-altitude-value-v491 input,.adsb-altitude-label-v491.is-all-v491 .adsb-altitude-unit-v491{cursor:not-allowed!important}
.tak-sat-stepper-v491{display:grid!important;grid-template-columns:minmax(0,1fr) 24px!important;align-items:stretch!important;width:100%!important;overflow:hidden!important;border:1px solid #334553!important;border-radius:10px!important;background:#091018!important;box-sizing:border-box!important}
.tak-sat-stepper-v491:focus-within{border-color:rgba(255,111,46,.72)!important;box-shadow:0 0 0 2px rgba(255,111,46,.10)!important}
.tak-sat-stepper-v491>input[type=number]{width:100%!important;min-width:0!important;margin:0!important;padding:7px 8px!important;border:0!important;border-radius:0!important;background:transparent!important;box-shadow:none!important;outline:none!important;-moz-appearance:textfield!important;appearance:textfield!important}
.tak-sat-stepper-v491>input[type=number]::-webkit-inner-spin-button,.tak-sat-stepper-v491>input[type=number]::-webkit-outer-spin-button{-webkit-appearance:none!important;appearance:none!important;margin:0!important}
.tak-sat-step-buttons-v491{display:grid;grid-template-rows:1fr 1fr;border-left:1px solid rgba(255,111,46,.34);background:rgba(255,111,46,.06)}
.tak-sat-step-buttons-v491 button{min-height:0!important;margin:0!important;padding:0!important;border:0!important;border-bottom:1px solid rgba(255,111,46,.22)!important;border-radius:0!important;background:linear-gradient(180deg,rgba(255,111,46,.20),rgba(255,111,46,.09))!important;color:var(--accent,#ff6f2e)!important;font-size:8px!important;font-weight:1000!important;line-height:1!important;cursor:pointer!important}
.tak-sat-step-buttons-v491 button:last-child{border-bottom:0!important}.tak-sat-step-buttons-v491 button:hover,.tak-sat-step-buttons-v491 button:focus-visible{color:#fff!important;background:rgba(255,111,46,.28)!important}
.panel.tak-card-disabled-v491>.panel-body{opacity:.46}
.panel.tak-card-disabled-v491>.panel-body button,.panel.tak-card-disabled-v491>.panel-body input,.panel.tak-card-disabled-v491>.panel-body select,.panel.tak-card-disabled-v491>.panel-body textarea{pointer-events:none!important}
.panel.tak-manual-card-v491.tak-card-collapsed-v491>.panel-body{display:none!important;visibility:hidden!important}
.panel.tak-manual-card-v491.tak-card-collapsed-v491>.tak-card-header-v491{margin-bottom:0!important;min-height:20px!important}
.tak-card-header-actions-v491>.tak-header-count-v491,.gateway-master-actions>.tak-header-count-v491{grid-column:1!important;justify-self:end!important}.tak-card-header-actions-v491>.tak-header-switch-v491,.gateway-master-actions>.gateway-switch{grid-column:2!important;justify-self:end!important}.tak-card-header-actions-v491>.tak-card-chevron-v491,.gateway-master-actions>.gateway-chevron{grid-column:3!important;justify-self:end!important}.tak-header-count-v491{display:inline-flex!important;width:max-content!important;min-width:0!important;max-width:none!important;flex:0 0 auto!important;align-items:center!important;justify-content:center!important;justify-self:end!important;min-height:20px!important;padding:2px 7px!important;border:1px solid rgba(255,111,46,.28)!important;border-radius:999px!important;background:rgba(255,111,46,.09)!important;color:#dce6ea!important;font-family:inherit!important;font-size:.64rem!important;font-style:normal!important;font-weight:900!important;letter-spacing:.04em!important;line-height:1!important;text-transform:uppercase!important;white-space:nowrap!important;pointer-events:none!important;font-variant-numeric:tabular-nums!important}
#missionCount,#dataSyncObjectCount{display:none!important}
`; (d.head||d.documentElement).appendChild(st)
}
function updateSwitchVisual(input){const wrap=input&&input.closest&&input.closest('.tak-header-switch-v491');const button=wrap&&q('.tak-header-switch-button-v491',wrap);if(button)button.setAttribute('aria-checked',input.checked?'true':'false')}
function switchWrap(input,title){
 const wrap=d.createElement('span');wrap.className='tak-header-switch-v491';wrap.title=title;
 input.setAttribute('aria-label',title);wrap.appendChild(input);
 const button=d.createElement('button');button.type='button';button.className='tak-header-switch-button-v491';button.setAttribute('role','switch');button.setAttribute('aria-label',title);button.setAttribute('aria-checked',input.checked?'true':'false');button.innerHTML='<span class="tak-header-switch-knob-v491"></span>';wrap.appendChild(button);
 input.addEventListener('change',()=>updateSwitchVisual(input));
 return wrap
}
/* Capture switch activation at document level so it runs before any historical
   capture listener installed directly on a card header (notably ADS-B v414). */
function captureSwitchClick(ev){
 const button=ev.target&&ev.target.closest&&ev.target.closest('.tak-header-switch-button-v491');if(!button)return;
 const wrap=button.closest('.tak-header-switch-v491'),input=wrap&&q('input[type="checkbox"]',wrap);if(!input||input.disabled)return;
 try{ev.preventDefault();ev.stopPropagation();ev.stopImmediatePropagation()}catch(_){}
 input.checked=!input.checked;updateSwitchVisual(input);
 input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}));
}
d.addEventListener('click',captureSwitchClick,true);

function numberFromText(value){const m=String(value==null?'':value).match(/-?\d+/);return m?Math.max(0,Number(m[0])||0):0}
function makeCountChip(id,text){let chip=$(id);if(!chip){chip=d.createElement('span');chip.id=id;chip.className='chip tak-header-count-v491'}chip.classList.add('tak-header-count-v491');chip.textContent=text;return chip}
function localCount(){try{if(typeof w.localDataSets==='function'){const sets=w.localDataSets()||{};return ['points','routes','shapes'].reduce((n,k)=>n+(Array.isArray(sets[k])?sets[k].length:0),0)}}catch(_){}return numberFromText(($('localDataCount')||{}).textContent)}
function stableRowKey(row,prefix,index){if(!row||typeof row!=='object')return prefix+':'+index;for(const key of ['canonical_id','object_id','source_id','uid','hash','id','filename','name']){const value=String(row[key]||'').trim();if(value)return prefix+':'+key+':'+value}return prefix+':'+index+':'+String(row.kind||row.type||'')}
function uniqueRowCount(rows,prefix){const seen=new Set();(Array.isArray(rows)?rows:[]).forEach((row,index)=>seen.add(stableRowKey(row,prefix,index)));return seen.size}
function dataSyncCounts(){try{const ds=globalBinding('lastDataSync')||w.lastDataSync;if(ds){const missions=uniqueRowCount(ds.missions,'mission'),objects=uniqueRowCount(ds.objects,'object'),packages=uniqueRowCount(ds.packages,'package');return {missions,items:objects+packages}}}catch(_){}return {missions:numberFromText(($('missionCount')||{}).textContent),items:numberFromText(($('dataSyncObjectCount')||{}).textContent)}}
function setStableDataSyncText(text){const chip=$('dataSyncHeaderCountV486');if(!chip)return false;text=String(text||'0 MIS, 0 ITEMS');if(chip.textContent===text&&S.dataSyncLastText===text){S.dataSyncChipSkips++;return false}chip.textContent=text;chip.dataset.authoritativeText=text;S.dataSyncLastText=text;S.dataSyncChipWrites++;return true}
function placeLegacyHeaderChip(panel,chip){if(!panel||!chip)return false;const header=q(':scope > h2',panel);if(!header)return false;const arrow=q(':scope > .panel-toggle',header)||q('.panel-toggle',header);if(chip.parentElement!==header)header.insertBefore(chip,arrow||null);return true}
function globalBinding(name){try{if(Object.prototype.hasOwnProperty.call(w,name))return w[name]}catch(_){}try{return (0,eval)(name)}catch(_){return undefined}}
function localDataEnabled(){const input=$('localDataHeaderEnableV486');try{const st=globalBinding('state');if(st&&typeof st.imported==='boolean')return !!st.imported}catch(_){}try{const m=globalBinding('map')||w.map||w.takLeafletMap,layer=globalBinding('importedLayer');if(m&&layer&&typeof m.hasLayer==='function')return !!m.hasLayer(layer)}catch(_){}return input?!!input.checked:true}
function setLocalDataEnabled(on){on=!!on;let changed=false;try{const fn=globalBinding('toggleImportedObjects');if(typeof fn==='function'){fn(on);changed=true}}catch(e){S.lastError=String(e&&e.message||e)}if(!changed){try{const st=globalBinding('state');if(st)st.imported=on;const m=globalBinding('map')||w.map||w.takLeafletMap,layer=globalBinding('importedLayer');if(m&&layer){if(on){if(typeof layer.addTo==='function')layer.addTo(m);const draw=globalBinding('drawImportedObjects');if(typeof draw==='function')draw()}else{if(typeof layer.clearLayers==='function')layer.clearLayers();if(typeof m.hasLayer==='function'&&m.hasLayer(layer)&&typeof m.removeLayer==='function')m.removeLayer(layer)}}changed=true}catch(e){S.lastError=String(e&&e.message||e)}}return changed}
function ensureLocalDataHeader(){
 let panel=$('localDataPanelV486')||findPanel('Local Data');if(!panel)return false;panel.id='localDataPanelV486';panel.dataset.collapseKey='localData';panel.dataset.manualCollapse='true';panel.dataset.skipAutoCollapsible='true';
 if(panel.dataset.cardControlsLocalDataV486==='1'){const input=$('localDataHeaderEnableV486');const on=localDataEnabled();if(input){input.checked=on;updateSwitchVisual(input)}panel.classList.toggle('tak-card-disabled-v491',!on);S.localDataHeader=S.localDataHeaderToggle=true;return true}
 const chip=$('localDataCount')||makeCountChip('localDataCount','0 ITEMS');chip.classList.add('chip','tak-header-count-v491');
 let input=$('localDataHeaderEnableV486');if(!input){input=d.createElement('input');input.id='localDataHeaderEnableV486';input.type='checkbox';input.checked=localDataEnabled()}
 const actions=d.createElement('span');actions.className='tak-card-header-actions-v491';actions.appendChild(chip);actions.appendChild(switchWrap(input,'Enable or disable Local Data'));
 const ctl=prepareManualPanel(panel,'Local Data',actions);if(!ctl)return false;
 input.addEventListener('change',()=>{setLocalDataEnabled(input.checked);panel.classList.toggle('tak-card-disabled-v491',!input.checked);updateSwitchVisual(input);S.localDataToggleChanges++});
 const on=localDataEnabled();input.checked=on;updateSwitchVisual(input);panel.classList.toggle('tak-card-disabled-v491',!on);panel.dataset.cardControlsLocalDataV486='1';S.localDataHeader=S.localDataHeaderToggle=true;return true
}
function updateHeaderCounts(){try{const local=$('localDataCount');if(local){const text=localCount()+' ITEMS';if(local.textContent!==text)local.textContent=text}const ds=dataSyncCounts();setStableDataSyncText(ds.missions+' MIS, '+ds.items+' ITEMS');for(const legacy of [$('missionCount'),$('dataSyncObjectCount')])if(legacy){legacy.hidden=true;legacy.setAttribute('aria-hidden','true')}const adsb=$('adsbHeaderCountV486');if(adsb){let n=0;try{const api=w.TakMapAdsbWorkerV477||w.TakMapAdsbWorkerV476;n=api&&api.snapshot?api.snapshot().length:numberFromText(($('bannerAdsb')||{}).textContent)}catch(_){n=numberFromText(($('bannerAdsb')||{}).textContent)}const text=n+' AIRCRAFT';if(adsb.textContent!==text)adsb.textContent=text}S.countUpdates++;S.headerCounts=true}catch(e){S.lastError=String(e&&e.message||e)}}
function bindCountObserver(){if(S.countObserver||!w.MutationObserver)return;const targets=[$('localDataCount'),$('missionCount'),$('dataSyncObjectCount'),$('bannerAdsb')].filter(Boolean);if(!targets.length)return;let pending=0;S.countObserver=new MutationObserver(()=>{S.dataSyncLegacyMutations++;clearTimeout(pending);pending=setTimeout(updateHeaderCounts,16)});targets.forEach(el=>S.countObserver.observe(el,{childList:true,characterData:true,subtree:true}))}

function neutralizeLegacyAdsb(){
 try{const o=w.__takMapAdsbCollapseObserverV414;if(o&&typeof o.disconnect==='function'){o.disconnect();S.legacyAdsbObserverDisconnected=true}}catch(_){}
 try{w.__takMapAdsbCollapseObserverV414=null}catch(_){}
}
function directBody(panel){
 let body=q(':scope > .panel-body',panel);if(body)return body;
 const h=q(':scope > h2',panel);if(!h)return null;
 body=d.createElement('div');body.className='panel-body';let n=h.nextSibling;while(n){const next=n.nextSibling;body.appendChild(n);n=next}panel.appendChild(body);return body
}
function collapseKey(panel,title){return 'takMapPanelCollapsed:'+(panel.dataset.sectionId||panel.dataset.collapseKey||slug(title))}
function prepareManualPanel(panel,title,actions){
 if(!panel)return null;panel.dataset.manualCollapse='true';panel.dataset.skipAutoCollapsible='true';panel.dataset.collapsibleReady='1';
 const body=directBody(panel);if(!body)return null;
 panel.classList.add('tak-manual-card-v491');const legacyCollapsed=panel.classList.contains('collapsed')||panel.classList.contains('tak-card-collapsed-v475');
 const old=q(':scope > h2',panel);if(!old)return null;
 const header=d.createElement('h2');header.className='tak-card-header-v491';header.tabIndex=0;header.setAttribute('role','button');
 const titleNode=d.createElement('span');titleNode.className='tak-card-title-v491';titleNode.textContent=title;header.appendChild(titleNode);
 const arrow=d.createElement('span');arrow.className='panel-toggle tak-card-chevron-v491';arrow.textContent='▾';actions.appendChild(arrow);header.appendChild(actions);old.replaceWith(header);
 panel.classList.remove('collapsible','collapsed','is-collapsed','tak-manual-card-v475','tak-card-collapsed-v475');
 const key=collapseKey(panel,title);let collapsed=legacyCollapsed;try{const saved=localStorage.getItem(key);if(saved!==null)collapsed=saved==='1'}catch(_){}
 function setCollapsed(value){collapsed=!!value;panel.classList.remove('collapsed','collapsible','is-collapsed','tak-card-collapsed-v475');panel.classList.toggle('tak-card-collapsed-v491',collapsed);body.hidden=collapsed;body.style.display=collapsed?'none':'';body.style.visibility=collapsed?'hidden':'';body.style.maxHeight='';body.setAttribute('aria-hidden',String(collapsed));header.setAttribute('aria-expanded',String(!collapsed));arrow.textContent=collapsed?'▸':'▾';try{localStorage.setItem(key,collapsed?'1':'0')}catch(_){}try{setTimeout(()=>{const m=w.map;m&&m.invalidateSize&&m.invalidateSize()},50)}catch(_){} }
 setCollapsed(collapsed);const toggle=()=>setCollapsed(!collapsed);
 header.addEventListener('click',ev=>{if(ev.target&&ev.target.closest&&ev.target.closest('.tak-header-switch-v491'))return;toggle()});
 header.addEventListener('keydown',ev=>{if(ev.target!==header&&!(ev.target&&ev.target.classList&&ev.target.classList.contains('tak-card-title-v491')))return;if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();toggle()}});
 return {panel,body,header,arrow,setCollapsed,isCollapsed:()=>collapsed}
}
function syncAdsbToggle(){
 const input=$('adsbHeaderEnableV476');if(!input)return;let on=true;try{on=localStorage.getItem('takmap.adsb.localDisabled')!=='1'}catch(_){}if(input.checked!==on)input.checked=on;updateSwitchVisual(input);const panel=q('.panel[data-collapse-key="adsbSettings"]');if(panel)panel.classList.toggle('tak-card-disabled-v491',!on)
}
function ensureAdsb(){
 neutralizeLegacyAdsb();const panel=q('.panel[data-collapse-key="adsbSettings"]');if(!panel)return false;panel.dataset.manualCollapse='true';panel.dataset.skipAutoCollapsible='true';
 if(panel.dataset.cardControlsAdsbV476==='1'){syncAdsbToggle();return true}
 let input=$('adsbHeaderEnableV476');if(!input){input=d.createElement('input');input.id='adsbHeaderEnableV476';input.type='checkbox';try{input.checked=localStorage.getItem('takmap.adsb.localDisabled')!=='1'}catch(_){input.checked=true}}
 const actions=d.createElement('span');actions.className='tak-card-header-actions-v491';actions.appendChild(makeCountChip('adsbHeaderCountV486','0 AIRCRAFT'));actions.appendChild(switchWrap(input,'Enable or disable ADS-B'));
 const ctl=prepareManualPanel(panel,'ADS-B',actions);if(!ctl)return false;
 input.addEventListener('change',()=>{try{const api=w.TakMapAdsbWorkerV476;if(input.checked){if(api&&api.enable)api.enable();else if(typeof w.enableTakMapAdsbLocal==='function')w.enableTakMapAdsbLocal()}else{if(api&&api.disable)api.disable();else if(typeof w.disableTakMapAdsbLocal==='function')w.disableTakMapAdsbLocal()}S.adsbToggleChanges++}catch(e){S.lastError=String(e&&e.message||e)}syncAdsbToggle()});
 panel.dataset.cardControlsAdsbV476='1';panel.dataset.v414AdsbCollapseFix='neutralized-i491';S.adsbHeader=S.adsbHeaderToggle=S.adsbManualCollapseOwner=true;syncAdsbToggle();
w.setTakMapAdsbPanelCollapsedV414=ctl.setCollapsed;return true
}
const ADSB_ALT_MODE_KEY='takmap.adsb.altitude.mode',ADSB_ALT_METERS_KEY='takmap.adsb.altitude.thresholdMeters',ADSB_ALT_UNIT_KEY='takmap.adsb.altitude.unit';
function adsbLocaleUnit(){
 let region='';try{const loc=new Intl.Locale((navigator&&navigator.language)||'en-US');region=String(loc.region||'').toUpperCase()}catch(_){const m=String((navigator&&navigator.language)||'').match(/[-_]([A-Za-z]{2})\b/);region=m?m[1].toUpperCase():''}return region==='US'?'ft':'m'
}
function adsbAltitudeState(){
 let mode='all',unit='',meters=3048,thresholdActive=true;try{mode=String(localStorage.getItem(ADSB_ALT_MODE_KEY)||'all').toLowerCase();unit=String(localStorage.getItem(ADSB_ALT_UNIT_KEY)||'').toLowerCase();const raw=localStorage.getItem(ADSB_ALT_METERS_KEY);if(raw===''){meters=null;thresholdActive=false}else if(raw!==null){const n=Number(raw);if(Number.isFinite(n)&&n>=0)meters=n;else{meters=null;thresholdActive=false}}}catch(_){}if(!['all','above','below'].includes(mode))mode='all';if(unit!=='ft'&&unit!=='m')unit=adsbLocaleUnit();return {mode,unit,meters,thresholdActive:thresholdActive&&meters!==null}
}
function adsbDisplayAltitude(meters,unit){if(meters==null)return '';return unit==='ft'?Math.round((meters/0.3048)/500)*500:Math.round(meters/100)*100}
function adsbMetersFromDisplay(value,unit){const n=Number(value);if(!Number.isFinite(n)||n<0)return null;return unit==='ft'?n*0.3048:n}
function emitAdsbAltitudeChange(reason){
 const state=adsbAltitudeState();S.adsbAltitudeMode=state.mode;S.adsbAltitudeUnit=state.unit;S.adsbAltitudeThresholdMeters=state.meters;S.adsbAltitudeThresholdActive=state.thresholdActive;S.adsbAltitudeChanges++;try{w.dispatchEvent(new CustomEvent('takmap:adsb-altitude-filter-change',{detail:Object.assign({reason:reason||'ui'},state)}))}catch(_){}return state
}
function ensureAdsbAltitude(){
 const grid=q('.panel[data-collapse-key="adsbSettings"] .adsb-settings-grid')||q('.adsb-settings-grid');if(!grid)return false;
 let mode=$('adsbAltitudeFilterV477'),input=$('adsbAltitudeThresholdV477'),unitBtn=$('adsbAltitudeUnitV477');
 if(!mode||!input||!unitBtn){
  const update=$('adsbUpdateInterval'),updateLabel=update&&update.closest('label');
  const filterLabel=d.createElement('label');filterLabel.className='adsb-altitude-label-v491 adsb-altitude-filter-v491';filterLabel.innerHTML='<span>Filter</span><select id="adsbAltitudeFilterV477" class="adsb-altitude-select-v491" aria-label="ADS-B altitude filter"><option value="all">All</option><option value="above">Above</option><option value="below">Below</option></select>';
  const altitudeLabel=d.createElement('label');altitudeLabel.className='adsb-altitude-label-v491 adsb-altitude-threshold-v491';altitudeLabel.innerHTML='<span>Altitude</span><span class="adsb-altitude-value-v491"><input id="adsbAltitudeThresholdV477" type="number" min="0" inputmode="numeric" aria-label="ADS-B altitude threshold"><button id="adsbAltitudeUnitV477" type="button" class="adsb-altitude-unit-v491" aria-label="Switch altitude unit">ft</button></span>';
  const insertBefore=updateLabel&&updateLabel.nextSibling;grid.insertBefore(filterLabel,insertBefore);grid.insertBefore(altitudeLabel,insertBefore);
  mode=$('adsbAltitudeFilterV477');input=$('adsbAltitudeThresholdV477');unitBtn=$('adsbAltitudeUnitV477')
 }
 const filterLabel=mode.closest('label'),altitudeLabel=input.closest('label');filterLabel&&filterLabel.classList.add('adsb-altitude-filter-v491');altitudeLabel&&altitudeLabel.classList.add('adsb-altitude-threshold-v491');
 function render(state){mode.value=state.mode;input.step=state.unit==='ft'?'500':'100';input.value=adsbDisplayAltitude(state.meters,state.unit);unitBtn.textContent=state.unit;unitBtn.title='Switch to '+(state.unit==='ft'?'meters':'feet');const all=state.mode==='all';input.disabled=all;unitBtn.disabled=all;altitudeLabel.classList.toggle('is-all-v491',all);altitudeLabel.classList.toggle('is-empty-v491',!state.thresholdActive);filterLabel.dataset.altitudeMode=state.mode;altitudeLabel.dataset.altitudeUnit=state.unit;altitudeLabel.dataset.thresholdActive=state.thresholdActive?'true':'false'}
 if(!mode.dataset.v491Bound){
  mode.dataset.v491Bound='1';let lastModeValue='',lastModeAppliedAt=0;
  const applyMode=()=>{let v=String(mode.value||'all').toLowerCase();if(!['all','above','below'].includes(v))v='all';const now=Date.now();try{localStorage.setItem(ADSB_ALT_MODE_KEY,v)}catch(_){}const state=adsbAltitudeState();render(state);if(v!==lastModeValue||now-lastModeAppliedAt>250){lastModeValue=v;lastModeAppliedAt=now;emitAdsbAltitudeChange('mode')}};
  mode.addEventListener('input',applyMode,true);mode.addEventListener('change',applyMode,true);
  const applyThreshold=()=>{const state=adsbAltitudeState(),raw=String(input.value==null?'':input.value).trim();if(raw===''){try{localStorage.setItem(ADSB_ALT_METERS_KEY,'')}catch(_){}altitudeLabel.classList.add('is-empty-v491');altitudeLabel.dataset.thresholdActive='false';emitAdsbAltitudeChange('threshold-clear');return}const meters=adsbMetersFromDisplay(raw,state.unit);if(meters==null)return;try{localStorage.setItem(ADSB_ALT_METERS_KEY,String(meters))}catch(_){}altitudeLabel.classList.remove('is-empty-v491');altitudeLabel.dataset.thresholdActive='true';emitAdsbAltitudeChange('threshold-input')};
  input.addEventListener('input',applyThreshold,true);input.addEventListener('change',applyThreshold,true);
  unitBtn.addEventListener('click',ev=>{ev.preventDefault();stop(ev);const state=adsbAltitudeState();if(state.mode==='all')return;const next=state.unit==='ft'?'m':'ft';try{localStorage.setItem(ADSB_ALT_UNIT_KEY,next)}catch(_){}render(emitAdsbAltitudeChange('unit'))})
 }
 const state=adsbAltitudeState();render(state);S.adsbAltitude=true;S.adsbAltitudeMode=state.mode;S.adsbAltitudeUnit=state.unit;S.adsbAltitudeThresholdMeters=state.meters;S.adsbAltitudeThresholdActive=state.thresholdActive;return true
}
function ensureAdsbFieldPairs(){
 const grid=q('.panel[data-collapse-key="adsbSettings"] .adsb-settings-grid')||q('.adsb-settings-grid');if(!grid)return false;
 const mode=$('adsbAltitudeFilterV477'),alt=$('adsbAltitudeThresholdV477');const filterLabel=mode&&mode.closest('label'),altLabel=alt&&alt.closest('label');
 const source=[$('adsbCenterSourceV275'),$('adsbCenterSource')].find(el=>el&&getComputedStyle(el).display!=='none')||$('adsbCenterSource');const combo=$('adsbCenterLatLon');const sourceLabel=source&&source.closest('label'),comboLabel=combo&&combo.closest('label');
 if(filterLabel){filterLabel.classList.add('adsb-altitude-filter-v491');if(filterLabel.parentElement!==grid)grid.appendChild(filterLabel)}if(altLabel){altLabel.classList.add('adsb-altitude-threshold-v491');if(altLabel.parentElement!==grid)grid.appendChild(altLabel)}
 if(sourceLabel){sourceLabel.classList.add('adsb-center-source-row-v491');if(sourceLabel.parentElement!==grid)grid.appendChild(sourceLabel)}if(comboLabel){comboLabel.classList.add('adsb-center-combo-row-v491');if(comboLabel.parentElement!==grid)grid.appendChild(comboLabel)}
 return !!(filterLabel&&altLabel&&sourceLabel&&comboLabel)
}
function ensureAdsbFilters(){
 const defs=[
  {id:'adsbFilterCivil',type:'civil',code:'CIV',name:'Civil'},
  {id:'adsbFilterGovt',type:'govt',code:'GOV',name:'Govt'},
  {id:'adsbFilterMilitary',type:'military',code:'MIL',name:'Military'},
  {id:'adsbFilterUnknown',type:'unknown',code:'UNK',name:'Unknown'}
 ];
 const inputs=defs.map(x=>$(x.id));if(inputs.some(x=>!x))return false;let box=inputs[0].closest('.adsb-v320-filter-row,.adsb-filter-box,.adsb-filter-box-v491,.adsb-type-grid-v491');if(!box)return false;
 const already=box.classList.contains('adsb-type-grid-v491')&&qa(':scope > .adsb-type-card-v491',box).length===4;
 if(!already){const frag=d.createDocumentFragment();defs.forEach((def,i)=>{const input=inputs[i];input.className='adsb-type-checkbox-v491';const card=d.createElement('label');card.className='adsb-type-card-v491';card.dataset.type=def.type;card.setAttribute('for',input.id);const badge=d.createElement('span');badge.className='adsb-type-badge-v491';badge.textContent=def.code;const copy=d.createElement('span');copy.className='adsb-type-copy-v491';copy.innerHTML='<span class="adsb-type-name-v491">'+def.name+'</span>';const check=d.createElement('span');check.className='adsb-type-check-v491';check.textContent='✓';card.append(input,badge,copy,check);frag.appendChild(card);const sync=()=>card.classList.toggle('is-checked-v491',!!input.checked);sync();if(!input.dataset.v491CardSync){input.dataset.v491CardSync='1';input.addEventListener('change',sync)}});box.replaceChildren(frag)}
 box.className='adsb-type-grid-v491';qa(':scope > .adsb-type-card-v491',box).forEach(card=>{const input=q('input',card);card.classList.toggle('is-checked-v491',!!(input&&input.checked))});S.adsbFilters=true;S.adsbFilterRows=qa(':scope > .adsb-type-card-v491',box).length;return S.adsbFilterRows===4
}

function ensureSatelliteOrder(){const panel=$('satelliteTrackingPanelV409')||$('satelliteTrackingPanelV408'),offline=findPanel('Offline Maps'),tools=findPanel('Tools');if(!panel||!offline||!tools||offline.parentNode!==tools.parentNode)return false;const parent=offline.parentNode;if(panel.parentNode!==parent||offline.nextElementSibling!==panel){offline.insertAdjacentElement('afterend',panel);S.satelliteOrderFixes++}S.satelliteOrdered=offline.nextElementSibling===panel&&panel.parentNode===parent;return S.satelliteOrdered}
function ensureSatellite(){
 const panel=$('satelliteTrackingPanelV409')||$('satelliteTrackingPanelV408');if(!panel)return false;ensureSatelliteOrder();const enable=$('satEnableV409'),count=$('satVisibleCountV409');if(!enable||!count)return false;count.classList.add('chip','tak-header-count-v491');
 if(panel.dataset.cardControlsSatelliteV476==='1'){panel.classList.toggle('tak-card-disabled-v491',!enable.checked);updateSwitchVisual(enable);return true}
 const sourceRow=enable.closest('.row');const actions=d.createElement('span');actions.className='tak-card-header-actions-v491';actions.appendChild(count);actions.appendChild(switchWrap(enable,'Enable or disable Satellite Tracking'));
 const ctl=prepareManualPanel(panel,'Satellite Tracking',actions);if(!ctl)return false;enable.addEventListener('change',()=>{panel.classList.toggle('tak-card-disabled-v491',!enable.checked);S.satelliteToggleChanges++});
 if(sourceRow&&sourceRow.isConnected&&(sourceRow.children.length===0||!sourceRow.textContent.trim()))sourceRow.remove();panel.classList.toggle('tak-card-disabled-v491',!enable.checked);panel.dataset.cardControlsSatelliteV476='1';S.satelliteHeader=S.satelliteHeaderToggle=S.satelliteManualCollapseOwner=true;return true
}
function ensureSatelliteStepper(){
 const input=$('satUpdateSecV409');if(!input)return false;if(input.closest('.tak-sat-stepper-v491')){S.satelliteStepper=true;return true}
 const old=input.closest('.tak-sat-stepper-v475');if(old){const parent=old.parentNode;parent.insertBefore(input,old);old.remove()}
 const wrap=d.createElement('span');wrap.className='tak-sat-stepper-v491';input.parentNode.insertBefore(wrap,input);wrap.appendChild(input);const controls=d.createElement('span');controls.className='tak-sat-step-buttons-v491';controls.innerHTML='<button type="button" data-dir="1" aria-label="Increase satellite update interval">▲</button><button type="button" data-dir="-1" aria-label="Decrease satellite update interval">▼</button>';wrap.appendChild(controls);
 controls.addEventListener('click',ev=>{const b=ev.target.closest('button');if(!b)return;ev.preventDefault();stop(ev);try{Number(b.dataset.dir)>0?input.stepUp():input.stepDown()}catch(_){const step=Number(input.step)||1;input.value=String((Number(input.value)||0)+(Number(b.dataset.dir)>0?step:-step))}input.dispatchEvent(new Event('input',{bubbles:true}));input.dispatchEvent(new Event('change',{bubbles:true}))});S.satelliteStepper=true;return true
}
function ensureDataSync(){
 let panel=$('dataSyncPanelV476')||findPanel('Data Sync');if(!panel)return false;panel.id='dataSyncPanelV476';panel.dataset.collapseKey='dataSync';panel.dataset.manualCollapse='true';panel.dataset.skipAutoCollapsible='true';
 if(panel.dataset.cardControlsDataSyncV476==='1'){const input=$('dataSyncHeaderEnableV476');const api=w.TakMapDataSyncControlV476;const on=api&&api.isEnabled?api.isEnabled():input&&input.checked;if(input){input.checked=!!on;updateSwitchVisual(input)}panel.classList.toggle('tak-card-disabled-v491',!on);return true}
 let input=$('dataSyncHeaderEnableV476');if(!input){input=d.createElement('input');input.id='dataSyncHeaderEnableV476';input.type='checkbox';const api=w.TakMapDataSyncControlV476;input.checked=api&&api.isEnabled?api.isEnabled():true}
 const actions=d.createElement('span');actions.className='tak-card-header-actions-v491';const count=makeCountChip('dataSyncHeaderCountV486','0 MIS, 0 ITEMS');count.classList.add('tak-header-count-v491');count.dataset.authoritativeOwner=V;actions.appendChild(count);actions.appendChild(switchWrap(input,'Enable or disable Data Sync'));
 const ctl=prepareManualPanel(panel,'Data Sync',actions);if(!ctl)return false;
 input.addEventListener('change',()=>{try{const api=w.TakMapDataSyncControlV476;if(api&&api.setEnabled)api.setEnabled(input.checked,'header-toggle');S.dataSyncToggleChanges++}catch(e){S.lastError=String(e&&e.message||e)}panel.classList.toggle('tak-card-disabled-v491',!input.checked);updateSwitchVisual(input)});
 panel.classList.toggle('tak-card-disabled-v491',!input.checked);panel.dataset.cardControlsDataSyncV476='1';S.dataSyncHeader=S.dataSyncHeaderToggle=S.dataSyncManualCollapseOwner=true;return true
}
function run(){S.runs++;installCss();try{neutralizeLegacyAdsb();ensureAdsb();ensureAdsbAltitude();ensureAdsbFieldPairs();ensureAdsbFilters();ensureSatellite();ensureSatelliteOrder();ensureSatelliteStepper();ensureDataSync();ensureLocalDataHeader();updateHeaderCounts();bindCountObserver()}catch(e){S.lastError=String(e&&e.message||e)}}
function boot(){run();[100,350,850,1600,3000,5500,9000,12000].forEach(ms=>setTimeout(run,ms));if(w.MutationObserver&&d.body&&!S.observer){let pending=0;S.observer=new MutationObserver(muts=>{let hit=false;for(const m of muts){for(const n of m.addedNodes||[]){if(n&&n.nodeType===1&&(n.id==='satelliteTrackingPanelV409'||n.id==='adsbV270Menu'||n.id==='dataSyncPanelV476'||(n.querySelector&&n.querySelector('#satelliteTrackingPanelV409,#adsbV270Menu,.adsb-filter-box,#dataSyncRows')))){hit=true;break}}if(hit)break}if(hit){clearTimeout(pending);pending=setTimeout(run,40)}});S.observer.observe(d.body,{childList:true,subtree:true})}}
function diagnostics(){
 const adsbPanel=q('.panel[data-collapse-key="adsbSettings"]'),satPanel=$('satelliteTrackingPanelV409')||$('satelliteTrackingPanelV408'),dsPanel=$('dataSyncPanelV476');
 return {version:V,loadedAt:S.loadedAt,captureSwitchOwner:S.captureSwitchOwner,legacyAdsbObserverDisconnected:S.legacyAdsbObserverDisconnected,adsbHeader:S.adsbHeader,adsbHeaderToggle:!!$('adsbHeaderEnableV476'),adsbManualCollapseOwner:!!(adsbPanel&&adsbPanel.dataset.manualCollapse==='true'&&adsbPanel.dataset.skipAutoCollapsible==='true'),adsbToggleChanges:S.adsbToggleChanges,adsbInternalButtonHidden:true,adsbFilters:S.adsbFilters,adsbFilterRows:qa('.adsb-type-grid-v491 > .adsb-type-card-v491').length,adsbFilterInputsThemed:qa('.adsb-type-checkbox-v491').length,adsbFilterDesign:'4A',adsbGovernmentColor:'#b56cff',adsbSecondaryText:false,adsbFieldPairs:ensureAdsbFieldPairs(),adsbAltitude:S.adsbAltitude,adsbAltitudeMode:S.adsbAltitudeMode,adsbAltitudeUnit:S.adsbAltitudeUnit,adsbAltitudeThresholdMeters:S.adsbAltitudeThresholdMeters,adsbAltitudeThresholdActive:S.adsbAltitudeThresholdActive,adsbAltitudeChanges:S.adsbAltitudeChanges,adsbAltitudeRowOrder:(()=>{const g=q('.adsb-settings-grid');return g?qa(':scope > label',g).map(x=>String(x.textContent||'').trim().split(/\s+/)[0]):[]})(),adsbAltitudeUnitWhite:!!($('adsbAltitudeUnitV477')&&getComputedStyle($('adsbAltitudeUnitV477')).color==='rgb(255, 255, 255)'),satelliteHeader:S.satelliteHeader,satelliteHeaderToggle:!!$('satEnableV409')&&!!$('satEnableV409').closest('.tak-card-header-actions-v491'),satelliteManualCollapseOwner:!!(satPanel&&satPanel.dataset.manualCollapse==='true'&&satPanel.dataset.skipAutoCollapsible==='true'),satelliteToggleChanges:S.satelliteToggleChanges,satelliteInternalEnableRowRemoved:!($('satEnableV409')&&$('satEnableV409').closest('.panel-body>.row')),satelliteStepper:S.satelliteStepper,satelliteNativeSpinnerHidden:!!q('.tak-sat-stepper-v491'),dataSyncHeader:S.dataSyncHeader,dataSyncHeaderToggle:!!$('dataSyncHeaderEnableV476'),dataSyncManualCollapseOwner:!!(dsPanel&&dsPanel.dataset.manualCollapse==='true'&&dsPanel.dataset.skipAutoCollapsible==='true'),dataSyncToggleChanges:S.dataSyncToggleChanges,localDataHeader:S.localDataHeader,localDataHeaderToggle:!!$('localDataHeaderEnableV486'),localDataEnabled:localDataEnabled(),localDataToggleChanges:S.localDataToggleChanges,headerCounts:S.headerCounts,localHeaderText:($('localDataCount')||{}).textContent||'',adsbHeaderText:($('adsbHeaderCountV486')||{}).textContent||'',dataSyncHeaderText:($('dataSyncHeaderCountV486')||{}).textContent||'',dataSyncChipWrites:S.dataSyncChipWrites,dataSyncChipSkips:S.dataSyncChipSkips,dataSyncLegacyMutations:S.dataSyncLegacyMutations,dataSyncAuthoritativeOwner:(($('dataSyncHeaderCountV486')||{}).dataset||{}).authoritativeOwner||'',satelliteOrdered:S.satelliteOrdered,satelliteOrderFixes:S.satelliteOrderFixes,countUpdates:S.countUpdates,countObserverInstalled:!!S.countObserver,runs:S.runs,observerInstalled:!!S.observer,lastError:S.lastError}
}
const api=Object.freeze({refresh:run,diagnostics});w.TakMapCardControlsV477=api;w.TakMapCardControlsV476=api;
if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',()=>setTimeout(boot,20),{once:true});else setTimeout(boot,20);
console.info('[TAK Map] card-controls-v491: loaded');
})(window,document);
