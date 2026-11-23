/* General map search: synchronized live ADS-B and AIS markers (no hidden/stale objects). */
(function(window,document){
'use strict';
const ID='TakMapLiveSearchI650',SOURCE_ADSB='aircraft',SOURCE_AIS='gateway-ais-live';
if(window[ID])return;
let signature='',lastError='',syncs=0,aircraft=0,vessels=0;
const identities=new WeakMap();let serial=0;
const text=v=>String(v==null?'':v).trim();
function objectIdentity(value){if(!value||typeof value!=='object')return 0;if(!identities.has(value))identities.set(value,++serial);return identities.get(value)}
function visibleRows(api){try{return api&&typeof api.searchVisible==='function'?api.searchVisible():[]}catch(err){lastError=String(err&&err.message||err);return []}}
function signatureOf(adsb,ais){return JSON.stringify([adsb,ais].map(rows=>rows.map(r=>[
  r.id,r.label,r.lat,r.lon,r.category,objectIdentity(r.layer),...(r.terms||[]).map(text)
])))}
function proxyFor(row,focus){const key=text(row.id);return {
  getElement(){try{return row.layer&&row.layer.getElement&&row.layer.getElement()||null}catch(_){return null}},
  openPopup(){try{return focus(key)!==false}catch(_){return false}}
}}
function indexRow(source,kind,provider,row,focus){
  if(!row||!Number.isFinite(Number(row.lat))||!Number.isFinite(Number(row.lon)))return;
  const terms=[row.id,...(row.terms||[])].map(text).filter(Boolean).join(' ');
  window.addSearchItem(source,kind,text(row.label)||text(row.id),Number(row.lat),Number(row.lon),proxyFor(row,focus),{
    uid:terms,type:text(row.category)||kind,source:provider
  });
}
function sync(){
  if(typeof window.addSearchItem!=='function'||typeof window.clearSearchSource!=='function')return false;
  const adsbApi=window.TakMapAdsbSidebarI610,aisApi=window.TakMapGatewayDataV476;
  const adsb=visibleRows(adsbApi),ais=visibleRows(aisApi),next=signatureOf(adsb,ais);
  if(next===signature)return true;
  window.clearSearchSource(SOURCE_ADSB);
  window.clearSearchSource(SOURCE_AIS);
  for(const r of adsb)indexRow(SOURCE_ADSB,'ADS-B Aircraft','ADS-B',r,id=>adsbApi&&adsbApi.open&&adsbApi.open(id));
  for(const r of ais)indexRow(SOURCE_AIS,'AIS Vessel','Gateway AIS',r,id=>aisApi&&aisApi.focusSearchResult&&aisApi.focusSearchResult(id));
  signature=next;aircraft=adsb.length;vessels=ais.length;syncs++;
  if(typeof window.handleMapSearch==='function')window.handleMapSearch();
  return true;
}
function attachSearchInput(){const el=document.getElementById('layerSearch');if(!el||el.dataset.liveSearchI650)return;
  el.dataset.liveSearchI650='1';el.addEventListener('focus',sync,true);el.addEventListener('input',sync,true);
}
function boot(){attachSearchInput();sync()}
window[ID]=Object.freeze({sync,diagnostics:()=>({aircraft,vessels,syncs,lastError})});
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
window.addEventListener('takmap:runtime-ready-i553',boot);
setInterval(boot,1500);
})(window,document);
