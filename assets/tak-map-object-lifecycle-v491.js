(function(){
  'use strict';
  const w=window,d=document;
  if(w.TakMapObjectLifecycleV486)return;

  const registryById=new Map();
  const layerToId=new WeakMap();
  let startupLocalControlsRendered=false;
  let startupLocalControlRenderCount=0;
  const old={
    importedFeatures:w.importedFeatures,
    addObjectLayer:w.addObjectLayer,
    drawImportedObjects:w.drawImportedObjects,
    drawDataSyncObjects:w.drawDataSyncObjects,
    renderLocalActions:w.renderLocalActions,
    renderLocalSection:w.renderLocalSection,
    localDataSets:w.localDataSets,
    localDataAction:w.localDataAction,
    renderDataSyncRows:w.renderDataSyncRows,
    deleteDataSyncItem:w.deleteDataSyncItem,
    popupEditKey:w.popupEditKey,
    popupEditForm:w.popupEditForm,
    deletePopupEdit:w.deletePopupEdit,
    refreshTerrain3DObjects:w.refreshTerrain3DObjects,
    terrain3DDataHash:w.terrain3DDataHash
  };

  function asText(value){return String(value==null?'':value).trim()}
  function appState(){try{return state}catch(_){return w.state||null}}
  function currentImports(){try{if(typeof lastImports!=='undefined'&&Array.isArray(lastImports))return lastImports}catch(_){}return Array.isArray(w.lastImports)?w.lastImports:[]}
  function setCurrentImports(value){try{lastImports=value}catch(_){}try{w.lastImports=value}catch(_){}}
  function currentDataSync(){try{if(typeof lastDataSync!=='undefined'&&lastDataSync)return lastDataSync}catch(_){}return w.lastDataSync||null}
  function currentMap(){try{if(typeof map!=='undefined'&&map)return map}catch(_){}return w.map||w.takLeafletMap||null}
  function currentImportedLayer(){try{if(typeof importedLayer!=='undefined'&&importedLayer)return importedLayer}catch(_){}return w.importedLayer||null}
  function currentDataSyncLayer(){try{if(typeof dataSyncLayer!=='undefined'&&dataSyncLayer)return dataSyncLayer}catch(_){}return w.dataSyncLayer||null}
  function escapeHtml(value){
    try{return typeof w.esc==='function'?w.esc(value):String(value==null?'':value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}catch(_){return String(value==null?'':value)}
  }

  let deleteDialogOpenCount=0;
  function installDeleteDialogCss(){
    if(d.getElementById('takMapDeleteDialogStyleV486'))return;
    const style=d.createElement('style');style.id='takMapDeleteDialogStyleV486';style.textContent=`
.tak-delete-dialog-overlay-v491{position:fixed;inset:0;z-index:20050;display:grid;place-items:center;padding:18px;background:rgba(0,0,0,.68);backdrop-filter:blur(3px)}
.tak-delete-dialog-v491{width:min(430px,calc(100vw - 36px));border:1px solid rgba(255,111,46,.42);border-radius:16px;background:linear-gradient(180deg,rgba(16,25,34,.99),rgba(7,13,19,.99));box-shadow:0 28px 80px rgba(0,0,0,.68),0 0 0 1px rgba(255,255,255,.025);overflow:hidden;color:#dce6ea}
.tak-delete-dialog-head-v491{display:flex;align-items:center;gap:10px;padding:15px 16px 11px;border-bottom:1px solid rgba(255,255,255,.075)}
.tak-delete-dialog-icon-v491{display:grid;place-items:center;width:28px;height:28px;flex:0 0 28px;border:1px solid rgba(255,95,87,.45);border-radius:9px;background:rgba(255,95,87,.12);color:#ff8a83;font-size:17px;font-weight:900}
.tak-delete-dialog-head-v491 h3{margin:0;color:#f1f6f8;font-size:.93rem;letter-spacing:.025em}
.tak-delete-dialog-body-v491{padding:15px 16px 14px;color:#d7e1e6;font-size:.82rem;line-height:1.45}
.tak-delete-dialog-body-v491 p{margin:0}.tak-delete-dialog-note-v491{margin-top:9px!important;color:#93a5af;font-size:.73rem}
.tak-delete-dialog-list-v491{display:grid;gap:7px;margin-top:11px;max-height:min(42vh,320px);overflow:auto;padding-right:2px}
.tak-delete-dialog-item-v491{display:grid;grid-template-columns:auto minmax(0,1fr);gap:3px 9px;padding:9px 10px;border:1px solid rgba(255,255,255,.075);border-radius:10px;background:rgba(255,255,255,.025)}
.tak-delete-dialog-item-v491 b{grid-column:1/-1;overflow:hidden;color:#f1f6f8;font-size:.78rem;text-overflow:ellipsis;white-space:nowrap}
.tak-delete-dialog-item-v491 span{color:#8fa2ad;font-size:.68rem}.tak-delete-dialog-item-v491 span:nth-of-type(even){color:#cbd7dd;text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.tak-delete-dialog-more-v491{padding:6px 2px 0;color:#8fa2ad;font-size:.68rem;text-align:center}
.tak-delete-dialog-actions-v491{display:flex;justify-content:flex-end;gap:8px;padding:11px 16px 15px;border-top:1px solid rgba(255,255,255,.065)}
.tak-delete-dialog-actions-v491 button{min-width:88px;margin:0;padding:8px 13px;border:1px solid #3b4b57;border-radius:10px;background:#15212a;color:#dbe5e9;font-size:.75rem;font-weight:850;cursor:pointer}
.tak-delete-dialog-actions-v491 button:hover,.tak-delete-dialog-actions-v491 button:focus-visible{border-color:#647985;background:#1b2a34;outline:none}
.tak-delete-dialog-actions-v491 .danger{border-color:rgba(255,95,87,.64);background:rgba(255,95,87,.16);color:#ffd9d6}
.tak-delete-dialog-actions-v491 .danger:hover,.tak-delete-dialog-actions-v491 .danger:focus-visible{background:rgba(255,95,87,.28);color:#fff}
`;(d.head||d.documentElement).appendChild(style)
  }
  function confirmDeleteDialog(options){
    options=options||{};installDeleteDialogCss();deleteDialogOpenCount++;
    return new Promise(resolve=>{
      const prior=d.getElementById('takMapDeleteDialogV486');if(prior)prior.remove();
      const overlay=d.createElement('div');overlay.id='takMapDeleteDialogV486';overlay.className='tak-delete-dialog-overlay-v491';
      const allItems=Array.isArray(options.items)?options.items.filter(Boolean):[];const shown=allItems.slice(0,6);
      const itemHtml=shown.length?`<div class="tak-delete-dialog-list-v491">${shown.map(item=>`<div class="tak-delete-dialog-item-v491"><b>${escapeHtml(item.name||'Unnamed item')}</b><span>Type</span><span>${escapeHtml(item.type||'Object')}</span><span>Source</span><span>${escapeHtml(item.source||'Unknown')}</span>${item.location?`<span>Location</span><span>${escapeHtml(item.location)}</span>`:''}</div>`).join('')}${allItems.length>shown.length?`<div class="tak-delete-dialog-more-v491">+ ${allItems.length-shown.length} more item${allItems.length-shown.length===1?'':'s'}</div>`:''}</div>`:'';
      overlay.innerHTML=`<div class="tak-delete-dialog-v491" role="dialog" aria-modal="true" aria-labelledby="takDeleteDialogTitleV486"><div class="tak-delete-dialog-head-v491"><span class="tak-delete-dialog-icon-v491" aria-hidden="true">×</span><h3 id="takDeleteDialogTitleV486">${escapeHtml(options.title||'Delete item')}</h3></div><div class="tak-delete-dialog-body-v491"><p>${escapeHtml(options.message||'Delete this item?')}</p>${itemHtml}${options.note?`<p class="tak-delete-dialog-note-v491">${escapeHtml(options.note)}</p>`:''}</div><div class="tak-delete-dialog-actions-v491"><button type="button" data-dialog-cancel>Cancel</button><button type="button" class="danger" data-dialog-confirm>${escapeHtml(options.confirmLabel||'Delete')}</button></div></div>`;
      const previous=d.activeElement;let settled=false;
      function finish(value){if(settled)return;settled=true;d.removeEventListener('keydown',onKey,true);overlay.remove();try{previous&&previous.focus&&previous.focus()}catch(_){}resolve(Boolean(value))}
      function onKey(event){if(event.key==='Escape'){event.preventDefault();finish(false)}else if(event.key==='Tab'){const buttons=Array.from(overlay.querySelectorAll('button'));if(!buttons.length)return;const first=buttons[0],last=buttons[buttons.length-1];if(event.shiftKey&&d.activeElement===first){event.preventDefault();last.focus()}else if(!event.shiftKey&&d.activeElement===last){event.preventDefault();first.focus()}}}
      overlay.addEventListener('click',event=>{if(event.target===overlay||event.target.closest('[data-dialog-cancel]'))finish(false);else if(event.target.closest('[data-dialog-confirm]'))finish(true)});
      d.addEventListener('keydown',onKey,true);d.body.appendChild(overlay);setTimeout(()=>{const b=overlay.querySelector('[data-dialog-cancel]');b&&b.focus()},0)
    })
  }
  w.TakMapDialogV486={version:'i491',confirmDelete:confirmDeleteDialog,diagnostics:()=>({version:'i491',themed:true,nativeConfirm:false,enrichedDetails:true,openCount:deleteDialogOpenCount,open:!!d.getElementById('takMapDeleteDialogV486')})};w.TakMapDialogV482=w.TakMapDialogV486;
  function objectKind(object){
    try{
      if(typeof w.localDataKindForFeature==='function'){
        const value=w.localDataKindForFeature(object);
        if(value==='points')return 'point';if(value==='routes')return 'route';if(value==='shapes')return 'shape'
      }
    }catch(_){}
    const value=asText(object&& (object.object_kind||object.kind||object.geometry||object.geometry_type||object.type)).toLowerCase();
    if(/route|track|line/.test(value))return 'route';
    if(/polygon|shape|area|rectangle|ellipse|circle|freehand/.test(value))return 'shape';
    return 'point'
  }
  function directLatLon(object){
    if(!object||typeof object!=='object')return null;
    const lat=Number(object.lat),lon=Number(object.lon!=null?object.lon:object.lng);if(Number.isFinite(lat)&&Number.isFinite(lon))return {lat,lon};
    const geometry=object.geometry&&typeof object.geometry==='object'?object.geometry:null;const coords=geometry&&geometry.coordinates;
    if(String(geometry&&geometry.type||'').toLowerCase()==='point'&&Array.isArray(coords)&&coords.length>=2){const glat=Number(coords[1]),glon=Number(coords[0]);if(Number.isFinite(glat)&&Number.isFinite(glon))return {lat:glat,lon:glon}}
    return null
  }
  function flattenCoords(value,out){out=out||[];if(!Array.isArray(value))return out;if(value.length>=2&&Number.isFinite(Number(value[0]))&&Number.isFinite(Number(value[1]))){out.push([Number(value[0]),Number(value[1])]);return out}for(const child of value)flattenCoords(child,out);return out}
  function objectCoordinatePairs(object){
    if(!object||typeof object!=='object')return [];
    const direct=directLatLon(object);if(direct)return [[direct.lon,direct.lat]];
    const geometry=object.geometry&&typeof object.geometry==='object'?object.geometry:null;
    if(geometry&&Array.isArray(geometry.coordinates))return flattenCoords(geometry.coordinates,[]);
    if(Array.isArray(object.coords))return object.coords.map(pair=>Array.isArray(pair)&&pair.length>=2?[Number(pair[1]),Number(pair[0])]:null).filter(pair=>pair&&Number.isFinite(pair[0])&&Number.isFinite(pair[1]));
    return []
  }
  function formatLatLon(lat,lon){
    if(!Number.isFinite(Number(lat))||!Number.isFinite(Number(lon)))return '';
    try{if(typeof w.formatCoords==='function')return asText(w.formatCoords(Number(lat),Number(lon)))}catch(_){}
    return Number(lat).toFixed(5)+', '+Number(lon).toFixed(5)
  }
  function objectLocationSummary(object){
    const pairs=objectCoordinatePairs(object);if(!pairs.length)return '';
    const kind=objectKind(object);if(kind==='point')return formatLatLon(pairs[0][1],pairs[0][0]);
    const lats=pairs.map(p=>p[1]),lons=pairs.map(p=>p[0]);const center={lat:(Math.min(...lats)+Math.max(...lats))/2,lon:(Math.min(...lons)+Math.max(...lons))/2};
    if(kind==='route'){const start=formatLatLon(pairs[0][1],pairs[0][0]),end=formatLatLon(pairs[pairs.length-1][1],pairs[pairs.length-1][0]);return pairs.length+' points · '+start+' → '+end}
    return pairs.length+' vertices · center '+formatLatLon(center.lat,center.lon)
  }
  function detailForObject(object,sourceOverride,nameOverride,typeOverride){
    object=object&&typeof object==='object'?object:{};const kind=objectKind(object);
    return {name:asText(nameOverride||object.callsign||object.name||object.title||object.filename||object.uid||'Unnamed item'),type:asText(typeOverride||({point:'Point',route:'Route',shape:'Shape'}[kind]||kind||'Object')),source:asText(sourceOverride||object.mission_name||object.import_name||object.source||object.source_kind||(sourceKeyFor(object)==='datasync'?'Data Sync':'Local Data')),location:objectLocationSummary(object)}
  }
  function detailsForIds(ids,sourceFallback){return (ids||[]).map(id=>{const entry=entryForId(id);return entry?detailForObject(entry.object,sourceFallback||entry.source):{name:'Selected item',type:'Object',source:sourceFallback||'TAK Map',location:''}})}
  function canonicalId(object,sourceKey){
    if(!object||typeof object!=='object')return '';
    let value=asText(object.canonical_id||object.canonicalId);
    if(value)return value;
    const source=asText(object.source_kind||sourceKey).toLowerCase();
    if(source==='local'||source==='imported'){
      value=asText(object.object_id||object.local_id||object._local_id||object.source_id);
      return value&&value.startsWith('local-')?'local:'+value:''
    }
    if(source==='datasync'||source==='data-sync'){
      value=asText(object.object_id);
      return value&&value.startsWith('datasync-')?'datasync:'+value:''
    }
    return ''
  }
  function sourceKeyFor(object,sourceKey){
    const value=asText(object&&object.source_kind||sourceKey).toLowerCase();
    if(value==='imported')return 'local';
    if(value==='data-sync')return 'datasync';
    return value
  }
  function allOwnedLayers(object,primary){
    const out=[];
    const add=value=>{if(value&&typeof value==='object'&&!out.includes(value)&&(typeof value.addTo==='function'||typeof value.getLatLng==='function'||typeof value.getLatLngs==='function'||typeof value.on==='function'))out.push(value)};
    add(primary);
    if(!object||typeof object!=='object')return out;
    ['__layer','__hitLayer','_layer','layer','hitLayer','labelLayer','controlLayer','centerLayer','outlineLayer','marker','label'].forEach(key=>add(object[key]));
    ['__layers','_layers','layers','__selectionLayers','representations','_takSelectionOwnedLayers'].forEach(key=>{const values=object[key];if(Array.isArray(values))values.forEach(add)});
    return out
  }
  function deleteMetaFor(object,sourceKey){
    const canonical=canonicalId(object,sourceKey);
    const source=sourceKeyFor(object,sourceKey);
    if(!canonical)return null;
    if(source==='local'){
      const localId=canonical.split(':',2)[1]||'';
      return {supported:Boolean(localId),kind:'local',canonicalId:canonical,localId,objectId:canonical,source:'Local Data',identityOrigin:'canonical-object-registry'}
    }
    if(source==='datasync'){
      const supported=object.delete_supported===true||Boolean(object.mission_name&&object.mission_delete_target&&object.mission_delete_value);
      return {supported,kind:'datasync',canonicalId:canonical,stableId:asText(object.source_id||object.uid||object.mission_delete_value),objectId:canonical,source:asText(object.source||'Data Sync'),missionName:asText(object.mission_name),deleteTarget:asText(object.mission_delete_target),deleteValue:asText(object.mission_delete_value),identityOrigin:'canonical-object-registry',reason:supported?'':asText(object.delete_unavailable_reason||'No Mission API-owned deletion identity is available.')}
    }
    return null
  }
  function clonePopupContent(value){
    try{if(typeof value==='string'||typeof value==='function')return value;if(value&&value.cloneNode)return value.cloneNode(true);if(value&&value.outerHTML)return value.outerHTML}catch(_){}
    return value
  }
  function canonicalPopupTemplate(entry){
    if(!entry)return null;
    for(const layer of entry.layers||[]){
      try{const popup=layer&&layer.getPopup&&layer.getPopup();if(popup)return {popup,layer,content:clonePopupContent(popup.getContent?popup.getContent():popup._content),options:Object.assign({},popup.options||{})}}catch(_){}
    }
    return null
  }
  function canonicalPopupAnchor(layer,entry){
    try{
      /* Area popups always belong at the geometry center. Opening them at the
         pointer made hover and click appear to be two different popup designs
         and allowed a popup to jump around the outline. */
      if(entry&&entry.kind==='shape'){
        if(layer&&typeof layer.getBounds==='function'){const b=layer.getBounds();if(b&&typeof b.getCenter==='function')return b.getCenter()}
        const pairs=objectCoordinatePairs(entry.object);if(pairs.length){const lats=pairs.map(p=>p[1]),lons=pairs.map(p=>p[0]);return {lat:(Math.min(...lats)+Math.max(...lats))/2,lng:(Math.min(...lons)+Math.max(...lons))/2}}
      }
      if(layer&&typeof layer.getLatLng==='function')return layer.getLatLng();
      if(layer&&typeof layer.getCenter==='function')return layer.getCenter();
      if(layer&&typeof layer.getBounds==='function'){const b=layer.getBounds();if(b&&typeof b.getCenter==='function')return b.getCenter()}
    }catch(_){}
    return null
  }
  function canonicalPopupState(entry){
    if(!entry.popupState)entry.popupState={hoverLayers:new Set(),popupLayers:new Set(),pinnedLayer:null,closeTimer:0,openLayers:new Set()};
    return entry.popupState
  }
  function popupOpen(layer){try{return !!(layer&&layer.isPopupOpen&&layer.isPopupOpen())}catch(_){return false}}
  function setPopupCompatibility(entry,guarded){
    if(!entry)return;const st=canonicalPopupState(entry),clicked=!!st.pinnedLayer;
    for(const owned of entry.layers||[]){
      if(!owned)continue;
      try{
        owned._takPopupHover=!!guarded&&!clicked;
        owned.__v353Hovering=!!guarded&&!clicked;
        owned.__v461Hovering=!!guarded&&!clicked;
        owned.__v463Hovered=!!guarded&&!clicked;
        owned.__v461PopupPinned=!!guarded;
        owned.__v463Pinned=!!guarded;
        owned.__v461Pinned=!!clicked;
        owned.__v353PopupPinned=!!clicked;
        owned._takPopupPinned=!!clicked;
        const p=owned.getPopup&&owned.getPopup();if(p)p.__v463Pinned=!!guarded
      }catch(_){}
    }
  }
  function clearCanonicalCloseTimer(entry){const st=canonicalPopupState(entry);if(st.closeTimer){clearTimeout(st.closeTimer);st.closeTimer=0}}
  function closeCanonicalPopups(entry){
    if(!entry)return;const st=canonicalPopupState(entry);clearCanonicalCloseTimer(entry);
    for(const owned of entry.layers||[]){try{if(popupOpen(owned)&&owned.closePopup)owned.closePopup()}catch(_){}}
    st.openLayers.clear();st.hoverLayers.clear();st.popupLayers.clear();st.pinnedLayer=null;setPopupCompatibility(entry,false);
    try{if(w.__takCanonicalPinnedEntryV492===entry)w.__takCanonicalPinnedEntryV492=null}catch(_){}
    try{if(w._takPinnedPopupLayer&&entry.layers&&entry.layers.has(w._takPinnedPopupLayer))w._takPinnedPopupLayer=null}catch(_){}
  }
  function scheduleCanonicalClose(entry){
    if(!entry)return;const st=canonicalPopupState(entry);clearCanonicalCloseTimer(entry);
    if(st.pinnedLayer||st.hoverLayers.size||st.popupLayers.size)return;
    /* Legacy popup managers close after 120-150 ms. Keep their recognized
       guard flags set until this single canonical owner decides to close. */
    st.closeTimer=setTimeout(()=>{st.closeTimer=0;if(st.pinnedLayer||st.hoverLayers.size||st.popupLayers.size)return;setPopupCompatibility(entry,false);for(const owned of entry.layers||[]){try{if(popupOpen(owned)&&owned.closePopup)owned.closePopup()}catch(_){}}},340)
  }
  function clearPinnedCanonicalEntry(entry,close){
    if(!entry)return;const st=canonicalPopupState(entry);st.pinnedLayer=null;st.hoverLayers.clear();st.popupLayers.clear();setPopupCompatibility(entry,false);
    if(close)for(const owned of entry.layers||[]){try{if(popupOpen(owned)&&owned.closePopup)owned.closePopup()}catch(_){}}
    try{if(w.__takCanonicalPinnedEntryV492===entry)w.__takCanonicalPinnedEntryV492=null}catch(_){}
    try{if(w._takPinnedPopupLayer&&entry.layers&&entry.layers.has(w._takPinnedPopupLayer))w._takPinnedPopupLayer=null}catch(_){}
  }
  function stopCanonicalPopupEvent(ev){
    try{if(ev)ev._stopped=true;const oe=ev&&ev.originalEvent;if(oe){oe._stopped=true;if(w.L&&w.L.DomEvent){if(w.L.DomEvent.stopPropagation)w.L.DomEvent.stopPropagation(oe);if(w.L.DomEvent.preventDefault)w.L.DomEvent.preventDefault(oe)}}}catch(_){}
  }
  function prepareCanonicalPopupContent(layer,popup){
    try{
      const gf=w.TakMapGeofencingV491;
      if(gf&&typeof gf.preparePopup==='function')return gf.preparePopup(popup,layer)!==false
    }catch(_){}
    return false
  }
  function openCanonicalPopup(layer,entry,ev){
    try{
      const popup=layer.getPopup&&layer.getPopup();if(!popup)return false;
      const at=(entry&&entry.kind==='shape')?canonicalPopupAnchor(layer,entry):(ev&&ev.latlng||canonicalPopupAnchor(layer,entry));
      if(at&&popup.setLatLng)popup.setLatLng(at);
      if(popup.options){popup.options.autoPan=false;popup.options.keepInView=false;popup.options.autoClose=false;popup.options.closeOnClick=false}
      popup._source=layer;
      /* i498: the canonical Edit + Geofence row and read-only popup body must be the popup's stored
         content before Leaflet renders it. A post-popupopen DOM decoration is
         not durable when Leaflet receives a repeated hover/click while the
         same popup is already open and therefore emits no new popupopen event. */
      prepareCanonicalPopupContent(layer,popup);
      const st=canonicalPopupState(entry);
      if(popupOpen(layer)){
        st.openLayers.add(layer);
        bindCanonicalPopupRoot(layer,entry,popup);
        return true
      }
      if(typeof layer.openPopup==='function')layer.openPopup(at||undefined);
      st.openLayers.add(layer);return true
    }catch(_){return false}
  }
  function bindCanonicalPopupRoot(layer,entry,popup){
    setTimeout(()=>{try{
      const root=popup&&popup.getElement&&popup.getElement();if(!root)return;
      const key='takCanonicalPopupV492';if(root.dataset&&root.dataset[key]==='1')return;if(root.dataset)root.dataset[key]='1';
      const st=canonicalPopupState(entry);
      root.addEventListener('mouseenter',()=>{st.popupLayers.add(layer);clearCanonicalCloseTimer(entry);setPopupCompatibility(entry,true)});
      root.addEventListener('mouseleave',()=>{st.popupLayers.delete(layer);scheduleCanonicalClose(entry)});
      for(const type of ['pointerdown','mousedown','touchstart','click','wheel'])root.addEventListener(type,e=>e.stopPropagation())
    }catch(_){}},0)
  }
  function retireLegacyPopupInteraction(layer){
    if(!layer||typeof layer.off!=='function'||layer.__takLegacyPopupInteractionRetiredV494)return;
    layer.__takLegacyPopupInteractionRetiredV494=true;
    /* Shape/route renderers historically installed their own mouseover,
       mouseout, click, popupopen, and popupclose handlers before canonical
       lifecycle registration. Leaving those handlers in place lets a delayed
       legacy mouseout timer reopen or replace the popup after the canonical
       hover popup closes. Canonical ownership is now exclusive for these
       geometry layers, so remove all pre-existing popup interaction handlers
       before installing the single owner below. */
    for(const type of ['mouseover','mouseout','click','popupopen','popupclose']){
      try{layer.off(type)}catch(_){}
    }
    try{if(layer._openPopup)delete layer._openPopup}catch(_){}
    /* Prevent the older document-wide popup managers from attaching a second
       set of layer hover/click handlers after canonical registration. Their
       map-level compatibility logic may remain, but this geometry layer has a
       single event owner from this point forward. */
    layer.__v461PopupBound=true;
    layer.__v462PopupBound=true;
    layer.__v463LifecycleBound=true;
  }
  function bindCanonicalPopupInteraction(layer,entry){
    if(!layer||!entry||typeof layer.on!=='function'||layer.__takCanonicalPopupOwnerV492)return;
    retireLegacyPopupInteraction(layer);
    layer.__takCanonicalPopupOwnerV492=true;
    try{if(layer.options)layer.options.bubblingMouseEvents=false}catch(_){}
    layer.on('mouseover',ev=>{const st=canonicalPopupState(entry);st.hoverLayers.add(layer);clearCanonicalCloseTimer(entry);setPopupCompatibility(entry,true);openCanonicalPopup(layer,entry,ev)});
    layer.on('mouseout',()=>{const st=canonicalPopupState(entry);st.hoverLayers.delete(layer);scheduleCanonicalClose(entry)});
    layer.on('click',ev=>{
      stopCanonicalPopupEvent(ev);
      try{const old=w.__takCanonicalPinnedEntryV492;if(old&&old!==entry)clearPinnedCanonicalEntry(old,true)}catch(_){}
      const st=canonicalPopupState(entry);clearCanonicalCloseTimer(entry);st.pinnedLayer=layer;st.hoverLayers.add(layer);w.__takCanonicalPinnedEntryV492=entry;w._takPinnedPopupLayer=layer;setPopupCompatibility(entry,true);openCanonicalPopup(layer,entry,ev)
    });
    layer.on('popupopen',ev=>{const popup=ev&&ev.popup||layer.getPopup&&layer.getPopup();const st=canonicalPopupState(entry);st.openLayers.add(layer);if(st.pinnedLayer===layer)setPopupCompatibility(entry,true);bindCanonicalPopupRoot(layer,entry,popup);setTimeout(()=>{try{const gf=w.TakMapGeofencingV491;if(gf&&typeof gf.attachPopup==='function')gf.attachPopup(popup)}catch(_){}},0)});
    layer.on('popupclose',()=>{const st=canonicalPopupState(entry);st.openLayers.delete(layer);st.popupLayers.delete(layer);if(st.pinnedLayer===layer)clearPinnedCanonicalEntry(entry,false);else if(!st.pinnedLayer&&!st.hoverLayers.size&&!st.popupLayers.size)setPopupCompatibility(entry,false)})
  }
  function independentPopupForLayer(layer,template,used){
    if(!layer||!template)return null;let popup=null;
    try{popup=layer.getPopup&&layer.getPopup()}catch(_){}
    const shared=!!(popup&&used.has(popup));
    const wrongSource=!!(popup&&popup._source&&popup._source!==layer);
    if(!popup||shared||wrongSource){
      try{if(popup&&layer.unbindPopup)layer.unbindPopup()}catch(_){}
      try{if(layer.bindPopup)layer.bindPopup(clonePopupContent(template.content),Object.assign({},template.options,{autoPan:false,keepInView:false,autoClose:false,closeOnClick:false}));popup=layer.getPopup&&layer.getPopup()}catch(_){}
    }
    if(popup){
      try{popup._source=layer;if(popup.options)Object.assign(popup.options,{autoPan:false,keepInView:false,autoClose:false,closeOnClick:false})}catch(_){}
      used.add(popup)
    }
    return popup
  }
  function syncCanonicalPopupEntry(entry){
    if(!entry||!['shape','route'].includes(entry.kind))return false;
    const template=canonicalPopupTemplate(entry);if(!template)return false;
    let changed=false;const used=new Set();
    for(const layer of entry.layers||[]){
      if(!layer)continue;
      try{
        if(layer.options){layer.options.interactive=true;layer.options.bubblingMouseEvents=false}
        const before=layer.getPopup&&layer.getPopup();const popup=independentPopupForLayer(layer,template,used);if(popup&&popup!==before)changed=true;
        bindCanonicalPopupInteraction(layer,entry)
      }catch(_){}
    }
    return changed
  }
  function syncCanonicalPopups(){for(const entry of registryById.values())syncCanonicalPopupEntry(entry)}
  function register(object,sourceKey,primary,ownerGroup){
    const canonical=canonicalId(object,sourceKey);
    if(!canonical)return null;
    const source=sourceKeyFor(object,sourceKey);
    const layers=allOwnedLayers(object,primary);
    let entry=registryById.get(canonical);
    if(!entry){entry={objectId:canonical,source,kind:objectKind(object),object,layers:new Set(),ownerGroups:new Set()};registryById.set(canonical,entry)}
    entry.object=object;entry.source=source;entry.kind=objectKind(object);
    if(ownerGroup)entry.ownerGroups.add(ownerGroup);
    const meta=deleteMetaFor(object,sourceKey);
    object._takSelectionObject=object;object._takSelectionCanonicalId=canonical;object._takSelectionDeleteMeta=meta;object._takCanonicalObjectId=canonical;
    for(const layer of layers){
      entry.layers.add(layer);layerToId.set(layer,canonical);
      layer._takCanonicalObjectId=canonical;layer._takSelectionCanonicalId=canonical;layer._takSelectionObject=object;layer._takSelectionDeleteMeta=meta;layer._takSelectionOwnedLayers=layers;
      if(ownerGroup)layer._takSelectionOwnerGroup=ownerGroup
    }
    object._takSelectionOwnedLayers=layers;
    syncCanonicalPopupEntry(entry);
    return entry
  }
  function entryForLayer(layer){const id=layer&& (layer._takCanonicalObjectId||layerToId.get(layer));return id?registryById.get(id)||null:null}
  function entryForId(id){return registryById.get(asText(id))||null}
  function removeEntryLayers(id){
    const entry=entryForId(id);if(!entry)return false;
    for(const layer of entry.layers){
      try{
        const group=layer._takSelectionOwnerGroup;
        if(group&&typeof group.removeLayer==='function')group.removeLayer(layer);
        else if(currentMap()&&typeof currentMap().hasLayer==='function'&&currentMap().hasLayer(layer))currentMap().removeLayer(layer);
        else if(typeof layer.remove==='function')layer.remove()
      }catch(_){}
    }
    registryById.delete(id);return true
  }
  function clearSource(source){
    for(const [id,entry] of Array.from(registryById.entries())){
      if(entry.source!==source)continue;
      for(const layer of entry.layers||[]){
        try{layerToId.delete(layer)}catch(_){}
        try{if(layer._takCanonicalObjectId===id)delete layer._takCanonicalObjectId}catch(_){}
        try{if(layer._takSelectionCanonicalId===id)delete layer._takSelectionCanonicalId}catch(_){}
        try{if(layer._takSelectionObject===entry.object)delete layer._takSelectionObject}catch(_){}
        try{if(layer._takSelectionDeleteMeta&&layer._takSelectionDeleteMeta.canonicalId===id)delete layer._takSelectionDeleteMeta}catch(_){}
        try{delete layer._takSelectionOwnedLayers;delete layer._takSelectionOwnerGroup}catch(_){}
      }
      try{
        const object=entry.object;
        if(object&&object._takCanonicalObjectId===id)delete object._takCanonicalObjectId;
        if(object&&object._takSelectionCanonicalId===id)delete object._takSelectionCanonicalId;
        if(object&&object._takSelectionObject===object)delete object._takSelectionObject;
        if(object&&object._takSelectionDeleteMeta&&object._takSelectionDeleteMeta.canonicalId===id)delete object._takSelectionDeleteMeta;
        if(object)delete object._takSelectionOwnedLayers
      }catch(_){}
      registryById.delete(id)
    }
  }

  function installFunction(name,fn){try{w[name]=fn;eval(name+'=w[name]')}catch(_){try{w[name]=fn}catch(__){}}}

  const importedFeaturesV486=function(){
    const out=[];
    for(const imp of currentImports()){
      const liveWebform=asText(imp&&imp.id)==='webform-live'||asText(imp&&imp.source).toLowerCase()==='webform';
      (imp.features||[]).forEach((raw,index)=>{
        const feature=raw;
        feature.import_id=asText(imp.id||imp.name);feature.import_name=asText(imp.name);feature.import_feature_index=index;feature.uploaded=imp.uploaded;
        if(liveWebform){feature.source_kind='webform';feature.object_kind=objectKind(feature);out.push(feature);return}
        const objectId=asText(feature.object_id||feature.local_id||feature._local_id||feature.source_id);
        if(objectId.startsWith('local-')){
          feature.object_id=objectId;feature.local_id=objectId;feature._local_id=objectId;feature.source_id=objectId;feature.source_kind='local';feature.canonical_id='local:'+objectId;feature.object_kind=objectKind(feature)
        }
        out.push(feature)
      })
    }
    const routeEnds=[];
    for(const feature of out){
      const type=asText(feature.kind||feature.geometry||feature.geometry_type||feature.type).toLowerCase();const coords=Array.isArray(feature.coords)?feature.coords:[];
      if((type.includes('route')||type.includes('track')||type.includes('linestring'))&&coords.length>=2)routeEnds.push(coords[0],coords[coords.length-1])
    }
    function nearEndpoint(feature){
      if(feature.lat==null||feature.lon==null)return false;const lat=Number(feature.lat),lon=Number(feature.lon);if(!Number.isFinite(lat)||!Number.isFinite(lon))return false;
      const type=asText(feature.kind||feature.geometry||feature.geometry_type||feature.type).toLowerCase();if(type.includes('route')||type.includes('linestring')||type.includes('track'))return false;
      return routeEnds.some(point=>Array.isArray(point)&&Math.abs(Number(point[0])-lat)<.00010&&Math.abs(Number(point[1])-lon)<.00010)
    }
    return out.filter(feature=>!nearEndpoint(feature))
  };
  installFunction('importedFeatures',importedFeaturesV486);

  const addObjectLayerV486=function(group,object,sourceKey){
    const layer=old.addObjectLayer?old.addObjectLayer(group,object,sourceKey):null;
    register(object,sourceKey==='imported'?'local':sourceKey,layer,group);
    return layer
  };
  installFunction('addObjectLayer',addObjectLayerV486);

  const drawImportedObjectsV486=function(){
    clearSource('local');
    try{if(appState()&&appState().local)appState().local.hidden={}}catch(_){}
    const result=old.drawImportedObjects?old.drawImportedObjects():undefined;
    for(const feature of importedFeaturesV486())register(feature,'local',feature.__layer,currentImportedLayer());
    removeHideUi();return result
  };
  installFunction('drawImportedObjects',drawImportedObjectsV486);

  const drawDataSyncObjectsV486=function(items){
    clearSource('datasync');
    const result=old.drawDataSyncObjects?old.drawDataSyncObjects(items):undefined;
    for(const object of items||[])register(object,'datasync',object.__layer,currentDataSyncLayer());
    return result
  };
  installFunction('drawDataSyncObjects',drawDataSyncObjectsV486);

  const localDataSetsV486=function(){
    const sets={routes:[],points:[],shapes:[]};
    for(const feature of importedFeaturesV486()){
      const objectId=canonicalId(feature,'local');if(!objectId)continue;
      const kind=objectKind(feature)==='route'?'routes':objectKind(feature)==='shape'?'shapes':'points';
      sets[kind].push({id:objectId,name:asText(feature.name||feature.callsign||feature.title||feature.uid||objectId),source:asText(feature.import_name||feature.source||'Local Data'),shown:true,feature})
    }
    return sets
  };
  installFunction('localDataSets',localDataSetsV486);

  const renderLocalActionsV486=function(kind,items){
    const ids=typeof w.selectedLocal==='function'?w.selectedLocal(kind):[];
    if(!ids.length)return '';
    const label=typeof w.localSelectedLabel==='function'?w.localSelectedLabel(kind,ids.length):(ids.length+' selected');
    return `<div class="local-actions ${escapeHtml(kind)}"><div class="local-actions-top"><span id="localActionCount_${escapeHtml(kind)}" class="muted local-selected-count">${escapeHtml(label)}</span></div><div class="local-action-buttons"><button class="layer-button" onclick="localDataAction('${escapeHtml(kind)}','goto')">Go To</button><button class="layer-button" onclick="localDataAction('${escapeHtml(kind)}','publish')">Publish</button><button class="layer-button" onclick="localDataAction('${escapeHtml(kind)}','export')">Export</button><button class="layer-button" data-tak-delete-source="local" data-tak-delete-kind="${escapeHtml(kind)}" onclick="return localDataAction('${escapeHtml(kind)}','delete')">Delete</button></div></div>`
  };
  installFunction('renderLocalActions',renderLocalActionsV486);

  const renderLocalSectionV486=function(kind,title,items){
    const collapsed=Boolean(appState()&&appState().localCollapsed&&appState().localCollapsed[kind]);
    let html=`<div class="local-section ${collapsed?'collapsed':''}"><div class="subgroup-title local-section-title" onclick="toggleLocalSection('${escapeHtml(kind)}')"><span class="subgroup-label"><span class="toggle">${collapsed?'›':'⌄'}</span>${escapeHtml(title)}</span><span class="chip">${items.length}</span><button class="layer-button unselect-local-btn" onclick="unselectLocalSection('${escapeHtml(kind)}',event)">Unselect All</button></div><div class="local-data-list">`;
    html+=items.length?items.slice(0,120).map(item=>{
      const checked=appState()&&appState().local&&appState().local[kind]&&appState().local[kind][item.id]?'checked':'';
      const coords=kind==='points'&&item.feature&&item.feature.lat!=null&&item.feature.lon!=null&&typeof w.formatCoords==='function'?w.formatCoords(item.feature.lat,item.feature.lon):'';
      const meta=coords||asText(item.source||'Local Data');
      return `<div class="local-data-row ${checked?'selected-local':''}"><label class="local-data-main"><input type="checkbox" ${checked} onchange="toggleLocalItem('${escapeHtml(kind)}','${escapeHtml(item.id)}',this.checked)"><span><b>${escapeHtml(item.name)}</b><small>${escapeHtml(meta)}</small></span></label><button class="layer-button local-goto-btn" onclick="centerLocalItem('${escapeHtml(kind)}','${escapeHtml(item.id)}',event)">Go To</button></div>`
    }).join(''):`<div class="muted" style="padding:8px">No local ${escapeHtml(String(title).toLowerCase())} yet.</div>`;
    return html+`</div>${renderLocalActionsV486(kind,items)}</div></div>`
  };
  installFunction('renderLocalSection',renderLocalSectionV486);

  async function postObjectDelete(ids){
    const response=await fetch('/api/tak-map/object-delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({object_ids:ids}),cache:'no-store'});
    let json={};try{json=await response.json()}catch(_){throw new Error('Delete endpoint did not return JSON.')}
    if(!response.ok)throw new Error(json.error||('HTTP '+response.status));return json
  }
  async function refreshObjectSources(result){
    try{if(result&&Array.isArray(result.imports))setCurrentImports(result.imports)}catch(_){}
    try{if(typeof w.refreshImports==='function')await w.refreshImports()}catch(_){}
    try{if(typeof w.refreshDataSync==='function')await w.refreshDataSync(true,'canonical-object-delete')}catch(_){}
    try{if(typeof w.refreshLocalData==='function')await w.refreshLocalData()}catch(_){}
  }

  const localDataActionV486=async function(kind,action){
    const ids=typeof w.selectedLocal==='function'?w.selectedLocal(kind):[];
    if(!ids.length){alert('Select one or more objects first.');return false}
    if(action==='hide'||action==='show'){alert('Individual-object hiding is not available.');return false}
    if(action==='goto'){if(typeof w.centerSelectedLocal==='function')w.centerSelectedLocal(kind,ids);return true}
    if(action==='export'){if(typeof w.downloadLocalData==='function')w.downloadLocalData(kind,ids);return true}
    if(action==='publish'){if(typeof w.openLocalDataPublish==='function')w.openLocalDataPublish(kind,ids);return true}
    if(action!=='delete')return false;
    if(!await confirmDeleteDialog({title:'Delete Local Data',message:'Review the Local Data item'+(ids.length===1?'':'s')+' that will be permanently deleted.',items:detailsForIds(ids,'Local Data'),note:'This action cannot be undone.'}))return false;
    try{
      const result=await postObjectDelete(ids);const deleted=new Set(result.deleted_ids||[]);
      const selectedState=appState()&&appState().local&&appState().local[kind];
      if(selectedState)for(const id of deleted)delete selectedState[id];
      for(const id of deleted)removeEntryLayers(id);
      await refreshObjectSources(result);
      const unchanged=[...(result.not_found_ids||[]),...(result.unsupported_ids||[]),...(result.failed_ids||[])];
      if(unchanged.length)alert('Some objects were left unchanged because their source did not confirm deletion: '+unchanged.join(', '));
      return result
    }catch(error){alert('Delete failed: '+String(error&&error.message||error));return false}
  };
  installFunction('localDataAction',localDataActionV486);

  const popupEditKeyV486=function(object){
    const canonical=canonicalId(object,object&&object.source_kind);
    if(canonical)return canonical;
    try{return old.popupEditKey?asText(old.popupEditKey(object)):''}catch(_){return ''}
  };
  installFunction('popupEditKey',popupEditKeyV486);

  const popupEditFormV486=function(object,source){
    const key=popupEditKeyV486(object);const objectId=canonicalId(object,object&&object.source_kind);const canEdit=Boolean(key);const canDelete=Boolean(objectId&&(sourceKeyFor(object,object&&object.source_kind)==='local'||object&&object.delete_supported===true));
    const name=asText(object&& (object.callsign||object.name||object.title||object.uid||object.id));const type=asText(object&& (object.type||object.cot_type||object.category));
    const asset=typeof w.assetDescriptor==='function'?w.assetDescriptor(object):'';const notes=typeof w.popupNotes==='function'?w.popupNotes(object):'';
    const lat=object&&object.lat!=null?Number(object.lat).toFixed(6):'';const lon=object&&object.lon!=null?Number(object.lon).toFixed(6):'';
    return `<details class="popup-edit" data-key="${escapeHtml(key)}" data-object-id="${escapeHtml(objectId)}" data-source="${escapeHtml(source||object&&object.source||'tak-map')}" onclick="event.stopPropagation()" ontoggle="popupEditToggle(this)" oninput="markPopupEditDirty(this)" onkeydown="popupEditKeyNav(event)"><summary>Edit Data</summary><label>Name<input name="name" value="${escapeHtml(name)}" ${canEdit?'':'disabled'}></label><label>Type<input name="type" value="${escapeHtml(type)}" ${canEdit?'':'disabled'}></label><label>Asset<input name="asset" value="${escapeHtml(asset)}" ${canEdit?'':'disabled'}></label><div class="popup-edit-grid"><label>Lat<input name="lat" value="${escapeHtml(lat)}" ${canEdit?'':'disabled'}></label><label>Lon<input name="lon" value="${escapeHtml(lon)}" ${canEdit?'':'disabled'}></label></div><label>Notes<textarea name="notes" rows="2" ${canEdit?'':'disabled'}>${escapeHtml(notes)}</textarea></label><div class="popup-edit-actions"><button type="button" onclick="savePopupEdit(this)" ${canEdit?'':'disabled'}>Save</button><button type="button" onclick="cancelPopupEdit(this)">Cancel</button><button type="button" class="danger-action" onclick="deletePopupEdit(this)" ${canDelete?'':'disabled title="Deletion is unavailable because this object has no source-owned identity."'}>Delete</button><span class="popup-edit-status">${canEdit?'':'Read-only: no stable source identity.'}</span></div></details>`
  };
  installFunction('popupEditForm',popupEditFormV486);

  const deletePopupEditV486=async function(button){
    const box=button&&button.closest&&button.closest('.popup-edit');if(!box)return false;
    const objectId=asText(box.dataset.objectId);const status=box.querySelector('.popup-edit-status');
    if(!objectId){if(status)status.textContent='Delete unavailable: no stable source identity.';return false}
    const objectName=asText((box.querySelector('[name="name"]')||{}).value||'this item');const entry=entryForId(objectId);const detail=detailForObject(entry&&entry.object||{},asText(box.dataset.source||'TAK Map'),objectName,asText((box.querySelector('[name="type"]')||{}).value||''));if(!await confirmDeleteDialog({title:'Delete Item',message:'Review the item that will be permanently deleted.',items:[detail],note:'This action cannot be undone.'}))return false;
    try{
      if(status)status.textContent='Deleting...';const result=await postObjectDelete([objectId]);
      if(!(result.deleted_ids||[]).includes(objectId))throw new Error((result.results||[]).map(item=>item.error).filter(Boolean).join('; ')||'The source did not confirm deletion.');
      removeEntryLayers(objectId);if(status)status.textContent='Deleted.';await refreshObjectSources(result);
      try{if(typeof w.closePopupEditBox==='function')w.closePopupEditBox(box)}catch(_){}
      return true
    }catch(error){if(status)status.textContent='Delete failed: '+String(error&&error.message||error);return false}
  };
  installFunction('deletePopupEdit',deletePopupEditV486);

  const deleteDataSyncItemV486=async function(index,event){
    if(event&&event.stopPropagation)event.stopPropagation();
    const current=w.TakMapDeleteControllerI566||w.TakMapContextSidebarI564;
    if(current&&typeof current.deleteDataSyncItem==='function')return current.deleteDataSyncItem(index,event);
    const object=(currentDataSync()&&currentDataSync().objects||[])[Number(index)];if(!object)return false;
    const objectId=canonicalId(object,'datasync');
    if(!objectId||object.delete_supported!==true){try{console.warn(asText(object.delete_unavailable_reason||'Deletion is unavailable because Mission API ownership could not be resolved.'))}catch(_){}return false}
    const label=asText(object.callsign||object.name||object.uid||'this item'),mission=asText(object.mission_name);
    if(!await confirmDeleteDialog({title:'Delete Data Sync Item',message:'Review the Mission item that will be removed.',items:[detailForObject(object,mission?('Data Sync · '+mission):'Data Sync',label)],note:'This removes the item from its mission and cannot be undone.'}))return false;
    try{const result=await postObjectDelete([objectId]);if(!(result.deleted_ids||[]).includes(objectId))throw new Error((result.results||[]).map(item=>item.error).filter(Boolean).join('; ')||'Mission API did not confirm deletion.');removeEntryLayers(objectId);await refreshObjectSources(result);return true}
    catch(error){try{console.error('TAK Map Data Sync delete failed',String(error&&error.message||error))}catch(_){}return false}
  };
  installFunction('deleteDataSyncItem',deleteDataSyncItemV486);

  const renderDataSyncRowsV486=function(){
    const box=d.getElementById('dataSyncRows'),payload=currentDataSync();if(!box||!payload)return;
    const objects=Array.isArray(payload.objects)?payload.objects:[],packages=Array.isArray(payload.packages)?payload.packages:[];let html='';
    const truthy=value=>value===true||value===1||['1','true','yes','on'].includes(asText(value).toLowerCase());
    const missionName=row=>{try{return typeof w.missionNameFromAny==='function'?asText(w.missionNameFromAny(row)):asText(row&&(row.name||row.mission_name||row.mission||row.callsign||row.uid))}catch(_){return asText(row&&(row.name||row.mission_name||row.mission||row.callsign||row.uid))}};
    const rawMissionMeta=row=>{try{return typeof w.missionDisplayMeta==='function'?asText(w.missionDisplayMeta(row)):asText(row&&(row.description||row.guid||row.uid||''))}catch(_){return asText(row&&(row.description||row.guid||row.uid||''))}};
    const accessRows=()=>{let fallback=[];for(const key of ['mission_access_i599','mission_access_i596','mission_access_i595','mission_access_i594','mission_access_i591','mission_access_i576','mission_access_i575','mission_access_i573','mission_access_i572']){if(!Array.isArray(payload[key]))continue;fallback=payload[key];if(payload[key].length)return payload[key]}return fallback};
    const accessFor=name=>{let access=null;try{const api=w.TakMapMissionAccessI576;if(api&&typeof api.peek==='function')access=api.peek(name)}catch(_){}if(access)return access;const key=asText(name).toLowerCase();return accessRows().find(row=>asText(row&&row.mission).toLowerCase()===key)||null};
    const missions=[];const seenMissions=new Set();
    for(const row of (Array.isArray(payload.missions)?payload.missions:[])){const mission=missionName(row),key=mission.toLowerCase();if(!mission||seenMissions.has(key))continue;seenMissions.add(key);missions.push(row)}
    for(const access of accessRows()){const mission=asText(access&&access.mission),key=mission.toLowerCase();if(!mission||seenMissions.has(key))continue;seenMissions.add(key);missions.push({name:mission,mission,passwordProtected:truthy(access.protected)||truthy(access.password_protected),password_protected:truthy(access.protected)||truthy(access.password_protected),metadata_only:true,locked_descriptor_i594:truthy(access.locked)})}
    const missionCard=row=>{const mission=missionName(row),access=accessFor(mission);const protectedMission=!!((row&&(truthy(row.passwordProtected)||truthy(row.password_protected)||truthy(row.protected)))||(access&&(truthy(access.protected)||truthy(access.password_protected)||truthy(access.credential_configured)||truthy(access.password_stored_server_side))));const unlocked=!!(protectedMission&&access&&truthy(access.unlocked));const refreshing=!!(unlocked&&access&&String(access.content_state_i599||'').toLowerCase()==='loading');const stateText=unlocked?'Unlocked':'Locked';const controls=protectedMission?`<div class="tak-mission-access-i576"><span class="tak-mission-state-i576 tak-mission-control-i576 ${unlocked?'unlocked':'locked'}">${stateText}</span><button type="button" class="layer-button tak-mission-edit-i576 tak-mission-control-i576" data-mission-edit-i576="1" data-mission="${escapeHtml(mission)}">Edit</button></div>`:'';let meta=rawMissionMeta(row);if(refreshing)meta='Refreshing Mission contents…';else if(protectedMission&&!unlocked&&(truthy(row&&row.metadata_only)||!meta))meta='Password required';return `<div class="sync-card tak-mission-card-i576" data-mission-key="${escapeHtml(mission.toLowerCase())}"><div class="tak-mission-main-i576"><b>${escapeHtml(mission)}</b><small>${escapeHtml(meta)}</small></div>${controls}</div>`};
    const stableRender=value=>{if(typeof w.__takMapDataSyncStableRenderV368==='function')w.__takMapDataSyncStableRenderV368(box,value);else box.innerHTML=value};

    if(payload.locked&&payload.requires_mission_password)html+='<div class="muted tak-data-sync-locked-i594"><strong>Protected Mission locked</strong><br>Select Edit beside a Mission to enter its password. Mission contents remain hidden until OpenTAKServer accepts it.</div>';
    const warnings=[];
    try{for(const value of Array.isArray(payload.warnings)?payload.warnings:[]){const text=asText(value);if(text&&!warnings.includes(text))warnings.push(text)}const bg=payload.data_sync_background_i583||payload.data_sync_background_i582||payload.data_sync_background_i581||{};if(payload.stale&&bg.last_error){const text='Latest refresh warning: '+asText(bg.last_error);if(!warnings.includes(text))warnings.push(text)}}catch(_){}
    if(warnings.length)html+='<div class="muted tak-data-sync-warning-i590"><strong>Data Sync warning</strong><br>'+warnings.map(escapeHtml).join('<br>')+'</div>';
    if(!missions.length&&!objects.length&&!packages.length)html+='<div class="sync-card"><div class="sync-card-main"><b>No Missions discovered</b><small>TAK Map is waiting for OpenTAKServer Mission discovery. Use Refresh if this state persists.</small></div></div>';
    html+=w.renderDataSyncSection('missions','Missions',missions,missionCard,24);
    const groups={'Pointers':[],'Routes':[],'Shapes / Areas':[],'Files / Packages':[],'Other / Unknown':[]};
    objects.forEach((object,index)=>{object.__idx=index;const cat=w.dataSyncCategory(object);const key=cat==='Point Markers'?'Pointers':cat;(groups[key]||groups['Other / Unknown']).push(object)});packages.forEach(item=>groups['Files / Packages'].push(item));
    const card=object=>{const index=object.__idx,label=asText(object.callsign||object.uid||object.name||object.filename||object.id||'object');const meta=(typeof w.assetDescriptor==='function'?w.assetDescriptor(object):'')+(object.lat!=null&&typeof w.formatCoords==='function'?' · '+w.formatCoords(object.lat,object.lon):'');const supported=object.delete_supported===true&&Boolean(canonicalId(object,'datasync'));const deleteAction=supported?`<button class="layer-button" data-tak-delete-source="datasync" data-tak-delete-index="${index}" onclick="return deleteDataSyncItem(${index},event)">Delete</button>`:`<button class="layer-button" disabled title="${escapeHtml(object.delete_unavailable_reason||'No Mission API-owned deletion identity.')}">Delete unavailable</button>`;const actions=index!=null?`<div class="sync-card-actions"><button class="layer-button" onclick="openDataSyncItemEdit(${index},event)">Edit</button>${deleteAction}</div>`:'';return `<div class="sync-card sync-card-actionable" ${index!=null?`onclick="centerDataSyncIndex(${index})" style="cursor:pointer"`:''}><div class="sync-card-main"><b>${escapeHtml(label)}</b><small>${escapeHtml(meta)}</small></div>${actions}</div>`};
    html+=w.renderDataSyncSection('pointers','Pointers',groups['Pointers'],card,80);html+=w.renderDataSyncSection('routes','Routes',groups['Routes'],card,80);html+=w.renderDataSyncSection('shapes','Shapes / Areas',groups['Shapes / Areas'],card,80);html+=w.renderDataSyncSection('files','Files / Packages',groups['Files / Packages'],card,80);html+=w.renderDataSyncSection('other','Other / Unknown',groups['Other / Unknown'],card,80);
    stableRender(html)
  };
  installFunction('renderDataSyncRows',renderDataSyncRowsV486);
  w.__takMapMissionRowFinalRendererI576={version:'i602-authoritative-data-sync',owner:'takMapObjectLifecycleLoaderV486',authoritativeControls:true,stableDomNodes:true,package:'i602',lockedMissionRenderer:true,discoveredMissionRows:true,manualMissionEntry:false,mixedLockStates:true,pollSafe:true,firstNonemptyAccess:true,refreshingContentsState:true};
  w.__takMapMissionRowStableI577={version:'i577',owner:'takMapObjectLifecycleLoaderV486',stableDomNodes:true};

  function selectedMetaV486(item){
    const layers=(item&&item.layers&&item.layers.length?item.layers:[item&&item.layer]).filter(Boolean);
    for(const layer of layers){
      const entry=entryForLayer(layer);if(entry){const meta=deleteMetaFor(entry.object,entry.source);if(meta)return Object.assign({},meta,{item,layers:Array.from(entry.layers),object:entry.object})}
      const stamped=layer&&layer._takSelectionDeleteMeta;if(stamped&&stamped.canonicalId)return Object.assign({},stamped,{item,layers:layer._takSelectionOwnedLayers||layers,object:layer._takSelectionObject||null})
    }
    return {supported:false,kind:'unsupported',canonicalId:asText(item&& (item.canonicalId||item.id)||'unsupported'),item,layers,reason:'No canonical Local Data or Mission API identity is registered for this representation.'}
  }
  async function selectionDeleteV486(){
    const state=w.__takSelectionStateV477;const items=state&&Array.isArray(state.selected)?state.selected.slice():[];
    const metas=[];const seen=new Set();for(const item of items){const meta=selectedMetaV486(item);if(meta.supported&&!seen.has(meta.canonicalId)){seen.add(meta.canonicalId);metas.push(meta)}}
    const unsupported=items.filter(item=>!selectedMetaV486(item).supported);
    if(!metas.length){setSelectionStatus('None of the selected objects has a source-owned deletion identity.');refreshSelectionReview();return {deleted:0,unsupported:unsupported.length}}
    if(!await confirmDeleteDialog({title:'Delete Selected Items',message:'Review the selected item'+(metas.length===1?'':'s')+' that will be permanently deleted.',items:metas.map(meta=>detailForObject(meta.object,meta.source)),note:unsupported.length?(unsupported.length+' unsupported item'+(unsupported.length===1?' will':'s will')+' remain unchanged.'):'This action cannot be undone.'}))return false;
    setSelectionStatus('Deleting '+metas.length+' selected object'+(metas.length===1?'':'s')+'...');
    try{
      const result=await postObjectDelete(metas.map(meta=>meta.canonicalId));const deleted=new Set(result.deleted_ids||[]);
      for(const id of deleted)removeEntryLayers(id);
      if(state){state.selected=items.filter(item=>!deleted.has(selectedMetaV486(item).canonicalId));state.selectedIds=new Set(state.selected.map(item=>item.id))}
      await refreshObjectSources(result);refreshSelectionReview();
      const remaining=(result.not_found_ids||[]).length+(result.unsupported_ids||[]).length+(result.failed_ids||[]).length;
      setSelectionStatus('Deleted '+deleted.size+' object'+(deleted.size===1?'':'s')+(remaining?' · '+remaining+' left unchanged':''));clearSelectionAfterAction();
      return {deleted:deleted.size,deletedIds:Array.from(deleted),unsupported:unsupported.length,failures:result.failed_ids||[]}
    }catch(error){setSelectionStatus('Selection delete failed: '+String(error&&error.message||error));clearSelectionAfterAction();return false}
  }
  function setSelectionStatus(text){const note=d.getElementById('selectionDeleteNote');if(note)note.textContent=text}
  function refreshSelectionReview(){try{const api=w.TakMapSelectionV486||w.TakMapSelectionV479||w.TakMapSelectionV478;if(api&&typeof api.refreshReview==='function')api.refreshReview()}catch(_){}wireSelectionButton()}
  function fallbackSelectionReset(){try{const state=w.__takSelectionStateV477;if(state){state.selected=[];state.selectedIds=new Set();state.mode=null;state.drawing=false;state.bounds=null;state.circle=null;state.freehandPts=null}}catch(_){}try{const panel=d.getElementById('selectionReviewPanel');if(panel)panel.classList.remove('active')}catch(_){}try{const btn=d.getElementById('toolSelectArea');if(btn){btn.classList.remove('active');btn.setAttribute('aria-pressed','false')}}catch(_){} }
  function clearSelectionAfterAction(){const clear=d.getElementById('selectionClearBtn');try{const fn=clear&&clear.__takBaseSelectionActionV486;if(typeof fn==='function'){fn.call(clear,{preventDefault(){},stopPropagation(){},stopImmediatePropagation(){}});return true}}catch(_){}fallbackSelectionReset();refreshSelectionReview();return true}
  function wrapSelectionAction(id,after){const button=d.getElementById(id);if(!button)return false;const current=button.onclick;if(current&&current!==button.__takSelectionWrapperV486)button.__takBaseSelectionActionV486=current;const wrapper=function(event){let result;try{const base=button.__takBaseSelectionActionV486;if(typeof base==='function')result=base.call(this,event)}finally{try{after&&after()}catch(_){}}return result};button.__takSelectionWrapperV486=wrapper;button.onclick=wrapper;return true}
  function wireSelectionActions(){const clear=d.getElementById('selectionClearBtn');if(clear){const current=clear.onclick;if(current&&current!==clear.__takSelectionWrapperV486)clear.__takBaseSelectionActionV486=current;const wrapper=function(event){let result;try{const base=clear.__takBaseSelectionActionV486;if(typeof base==='function')result=base.call(this,event)}finally{fallbackSelectionReset();refreshSelectionReview()}return result};clear.__takSelectionWrapperV486=wrapper;clear.onclick=wrapper}wrapSelectionAction('selectionFitBtn',()=>clearSelectionAfterAction());wrapSelectionAction('selectionExportBtn',()=>clearSelectionAfterAction())}
  function installDeleteActionCapture(){
    if(w.__takDeleteActionCaptureV486)return;w.__takDeleteActionCaptureV486=true;
    d.addEventListener('click',event=>{
      let button=null;try{button=event.target&&event.target.closest&&event.target.closest('button')}catch(_){}if(!button||button.closest('.tak-delete-dialog-overlay-v491'))return;
      const onclick=asText(button.getAttribute('onclick'));
      let action=null;
      const explicitSource=asText(button.dataset&&button.dataset.takDeleteSource);
      if(explicitSource==='local')action=()=>localDataActionV486(asText(button.dataset.takDeleteKind),'delete');
      if(explicitSource==='datasync')action=()=>deleteDataSyncItemV486(Number(button.dataset.takDeleteIndex),event);
      const local=onclick.match(/localDataAction\(['"]([^'"]+)['"],['"]delete['"]\)/);if(!action&&local)action=()=>localDataActionV486(local[1],'delete');
      const sync=onclick.match(/deleteDataSyncItem\((\d+)/);if(!action&&sync)action=()=>deleteDataSyncItemV486(Number(sync[1]),event);
      if(!action&&/deletePopupEdit\(/.test(onclick))action=()=>deletePopupEditV486(button);
      if(!action)return;
      try{event.preventDefault();event.stopPropagation();event.stopImmediatePropagation()}catch(_){}action()
    },true)
  }
  function installSelectionActionCapture(){
    if(w.__takSelectionActionCaptureV486)return;w.__takSelectionActionCaptureV486=true;
    d.addEventListener('click',event=>{let button=null;try{button=event.target&&event.target.closest&&event.target.closest('#selectionFitBtn,#selectionExportBtn,#selectionDeleteBtn,#selectionClearBtn')}catch(_){}if(!button)return;
      if(button.id==='selectionDeleteBtn'){try{event.preventDefault();event.stopPropagation();event.stopImmediatePropagation()}catch(_){}selectionDeleteV486();return}
      setTimeout(()=>{fallbackSelectionReset();refreshSelectionReview()},0)
    },true)
  }
  function wireSelectionButton(){
    wireSelectionActions();
    const button=d.getElementById('selectionDeleteBtn');if(button){if(!button.__takSelectionDeleteWrapperV486)button.__takSelectionDeleteWrapperV486=function(event){try{event&&event.preventDefault();event&&event.stopPropagation()}catch(_){}selectionDeleteV486();return false};button.dataset.objectLifecycleV486='1';if(button.onclick!==button.__takSelectionDeleteWrapperV486)button.onclick=button.__takSelectionDeleteWrapperV486}
    const api=w.TakMapSelectionV486||w.TakMapSelectionV479||w.TakMapSelectionV478;
    if(api){
      api.deleteSelected=selectionDeleteV486;api.selectedDeleteMeta=selectedMetaV486;api.objectLifecycleVersion='i491';
      if(!api.__objectLifecycleDiagnosticsV486){const baseDiagnostics=typeof api.diagnostics==='function'?api.diagnostics.bind(api):null;api.diagnostics=function(){let out={};try{out=baseDiagnostics?Object.assign({},baseDiagnostics()||{}):{}}catch(_){}return Object.assign(out,{version:'i491',objectLifecycleVersion:'i491',canonicalObjectRegistry:true,persistentLocalIds:true,missionApiDelete:true,perObjectHide:false,hideButton:false,themedDeleteDialog:true,nativeDeleteConfirm:false,selectionClearsAfterAction:true})};api.__objectLifecycleDiagnosticsV486=true}
      w.TakMapSelectionV486=api;w.TakMapSelectionV479=api;w.TakMapSelectionV478=api;w.TakMapSelectionV477=api
    }
  }

  function removeHideUi(root){
    try{if(appState()&&appState().local)appState().local.hidden={}}catch(_){}
    const scope=root&&root.querySelectorAll?root:d;
    const clear=d.getElementById('toolClearHidden');if(clear)clear.remove();
    const buttons=[];
    try{
      if(scope.matches&&scope.matches('.local-actions button,.popup-edit-actions button,.sync-card-actions button'))buttons.push(scope);
      buttons.push(...scope.querySelectorAll('.local-actions button,.popup-edit-actions button,.sync-card-actions button'))
    }catch(_){}
    for(const button of buttons){
      const text=asText(button.textContent).toLowerCase();
      const onclick=asText(button.getAttribute('onclick')).toLowerCase();
      if(text==='hide'||text==='show'||text==='clear hidden'||onclick.includes("'hide'")||onclick.includes("'show'"))button.remove()
    }
  }
  installFunction('clearHiddenMapItems',function(){try{if(appState()&&appState().local)appState().local.hidden={}}catch(_){}removeHideUi();return false});

  const terrainHashV486=function(){
    try{if(appState()&&appState().local)appState().local.hidden={}}catch(_){}
    return old.terrain3DDataHash?old.terrain3DDataHash():String(Date.now())
  };
  installFunction('terrain3DDataHash',terrainHashV486);
  const refreshTerrainV486=function(force,reason){try{if(appState()&&appState().local)appState().local.hidden={}}catch(_){}return old.refreshTerrain3DObjects?old.refreshTerrain3DObjects(force,reason):undefined};
  installFunction('refreshTerrain3DObjects',refreshTerrainV486);

  function ensureInitialLocalControls(){
    if(startupLocalControlsRendered)return true;
    const box=d.getElementById('localDataRows');
    if(!box||box.querySelector('.local-add-grid')){startupLocalControlsRendered=!!box;return !!box}
    if(typeof w.renderLocalDataRows!=='function')return false;
    try{w.renderLocalDataRows();startupLocalControlsRendered=true;startupLocalControlRenderCount++;return true}catch(_){return false}
  }

  function boot(){
    installDeleteActionCapture();installSelectionActionCapture();
    try{if(appState()&&appState().local)appState().local.hidden={}}catch(_){}
    ensureInitialLocalControls();removeHideUi();wireSelectionButton();
    /* Do not force sidebar rerenders during startup. The authoritative refresh paths
       own rendering; this module only registers objects that already exist. */
    try{for(const feature of importedFeaturesV486())register(feature,'local',feature.__layer,currentImportedLayer())}catch(_){}
    try{for(const object of (currentDataSync()&&currentDataSync().objects||[]))register(object,'datasync',object.__layer,currentDataSyncLayer())}catch(_){}
  }

  const api={version:'i502',registryById,entryForId,entryForLayer,register,canonicalId,deleteMetaFor,postObjectDelete,confirmDelete:confirmDeleteDialog,localDataAction:localDataActionV486,deleteDataSyncItem:deleteDataSyncItemV486,deletePopupEdit:deletePopupEditV486,selectionDelete:selectionDeleteV486,syncCanonicalPopups,diagnostics(){return {version:'i502',objects:registryById.size,local:Array.from(registryById.values()).filter(entry=>entry.source==='local').length,dataSync:Array.from(registryById.values()).filter(entry=>entry.source==='datasync').length,perObjectHide:false,canonicalDeleteEndpoint:'/api/tak-map/object-delete',documentWideObserver:false,startupSidebarRerenders:false,startupLocalControlRenderCount,themedDeleteDialog:true,nativeDeleteConfirm:false,selectionClearsAfterAction:true,selectionActionCapture:true,deleteActionCapture:true,enrichedDeleteDetails:true,canonicalShapePopupOwner:true,popupPropagation:true,unifiedShapeRoutePopupDesign:true,duplicateEditControls:false,legacyEditSummaryRemoved:true,legacyDetailsEditorRemoved:true,productionPopupMarkupEditWiring:true,primaryActionsInsidePaddedPopupBody:true,inlineReadOnlyToEditFields:true,inlineEditActions:['Save','Cancel','Delete'],shapePopupAnchor:'geometry-center',hoverClickSamePopupDesign:true,legacyPopupHandlersRetired:true,hoverCloseReopenRaceFixed:true,storedPopupContentCanonical:true,reopenWithoutPopupopenSafe:true,singleGeometryPopupEventOwner:true}}};
  w.TakMapObjectLifecycleV486=api;
  [350,900,1800,3500,7000].forEach(ms=>setTimeout(syncCanonicalPopups,ms));
  w.TakMapObjectLifecycleV482=api;
  w.TakMapObjectLifecycleV479=api;
  if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',()=>setTimeout(boot,80),{once:true});else setTimeout(boot,80);
  [500,1800,4200].forEach(ms=>setTimeout(boot,ms));
  console.log('[TAK Map] object-lifecycle-v492: loaded');
})();
