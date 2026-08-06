(function(w,d){
'use strict';
const V='i491';
const S={loadedAt:Date.now(),mapsTuned:0,snaps:0,lastZoom:null,lastError:'',hooksInstalled:false};
function mapCandidates(){const out=[];for(const m of [w.map,w.takLeafletMap])if(m&&m.getZoom&&!out.includes(m))out.push(m);try{const r=w.TakMapReplayV415&&w.TakMapReplayV415.map;if(r&&r.getZoom&&!out.includes(r))out.push(r)}catch(_){}return out}
function integerZoom(z){z=Number(z);return Number.isFinite(z)?Math.round(z):z}
function tune(m){try{if(!m||!m.options)return false;m.options.zoomSnap=1;m.options.zoomDelta=1;if(m.touchZoom&&m.touchZoom._map&&m.touchZoom._map.options){m.touchZoom._map.options.zoomSnap=1;m.touchZoom._map.options.zoomDelta=1}if(!m.__takWholeZoomV476){m.__takWholeZoomV476=true;S.mapsTuned++;m.on&&m.on('zoomend',()=>{try{m.options.zoomSnap=1;m.options.zoomDelta=1;const z=Number(m.getZoom());const i=integerZoom(z);S.lastZoom=z;if(Number.isFinite(z)&&Math.abs(z-i)>1e-7){S.snaps++;m.setZoom(i,{animate:false})}}catch(e){S.lastError=String(e&&e.message||e)}})}const z=Number(m.getZoom&&m.getZoom());const i=integerZoom(z);if(Number.isFinite(z)&&Math.abs(z-i)>1e-7){S.snaps++;m.setZoom(i,{animate:false})}S.lastZoom=Number(m.getZoom&&m.getZoom());return true}catch(e){S.lastError=String(e&&e.message||e);return false}}
function installHooks(){try{const L=w.L;if(L&&L.Map&&L.Map.mergeOptions){L.Map.mergeOptions({zoomSnap:1,zoomDelta:1});S.hooksInstalled=true}}catch(e){S.lastError=String(e&&e.message||e)}}
function sweep(){installHooks();for(const m of mapCandidates())tune(m)}
if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',()=>setTimeout(sweep,0),{once:true});else setTimeout(sweep,0);
[250,700,1500,3000,6000,9000,12000].forEach(ms=>setTimeout(sweep,ms));
w.addEventListener('focus',sweep,{passive:true});d.addEventListener('visibilitychange',()=>{if(!d.hidden)sweep()});
w.TakMapWholeZoomV476=Object.freeze({tune:sweep,diagnostics:()=>({version:V,loadedAt:S.loadedAt,mapsTuned:S.mapsTuned,snaps:S.snaps,lastZoom:S.lastZoom,lastError:S.lastError,hooksInstalled:S.hooksInstalled,zoomSnap:mapCandidates()[0]?.options?.zoomSnap??null,zoomDelta:mapCandidates()[0]?.options?.zoomDelta??null,wholeNumberOnly:true})});
const old=w.TakMapDiagnostics;w.TakMapDiagnostics=function(){let out={};try{out=typeof old==='function'?old():{}}catch(e){out={diagnosticError:String(e&&e.message||e)}}out.version=V;out.wholeZoom=w.TakMapWholeZoomV476.diagnostics();return out};
console.info('[TAK Map] whole-zoom-v491: loaded');
})(window,document);
