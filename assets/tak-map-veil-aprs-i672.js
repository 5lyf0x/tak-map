/* TAK Map i672: XTAK VEIL v0.4.0-r50 APRS renderer parity. Original Node Map artwork and category logic. */
(()=>{'use strict';
const assetRoot='/assets/runtime/veil-aprs-r50/';
const CATEGORIES=Object.freeze(['base','vehicle','portable','digipeater','weather','aircraft','marine','object','emergency','generic']);
function normalized(o){
 const a=o?.aprs||{},ident=o?.identity||{};
 const symbol=String(a.symbolCode||a.symbol||ident.symbol||'');
 const symbolTable=String(a.symbolTable||ident.symbolTable||'');
 const callsign=String(ident.callsign||o?.title||'');
 const weather=a.weather===true||String(a.weather||'').toLowerCase()==='true'||symbol==='_';
 return {identity:{...ident,symbol,symbolTable,callsign},metadata:{weather:weather?true:null},objectType:String(a.objectType||o?.objectType||'')};
}
function aprsCategory(o){const i=o?.identity||{},m=o?.metadata||{},symbol=String(i.symbol||'');if(m.weather!=null||symbol==='_')return'weather';if(symbol==='#'||symbol==='&')return'digipeater';if(symbol==='!')return'emergency';if(["'",'^','O'].includes(symbol))return'aircraft';if(['Y','s'].includes(symbol))return'marine';if(['>','j','k','u','v'].includes(symbol))return'vehicle';if(['[','b','p'].includes(symbol))return'portable';if(o?.objectType==='aprs_object')return'object';if(['-','r','h'].includes(symbol))return'base';if(!symbol){const call=String(i.callsign||'').toUpperCase();if(/-9$/.test(call))return'vehicle';if(/-7$/.test(call))return'portable';if(/-11$/.test(call))return'aircraft';if(/-8$/.test(call))return'marine';}return'generic';}
function category(o){return aprsCategory(normalized(o))}
function path(o){const cat=category(o);return assetRoot+'aprs-'+(CATEGORIES.includes(cat)?cat:'generic')+'.svg'}
function imgSize(o){return ['base','digipeater','weather'].includes(category(o))?38:40}
function markerHtml(o){
 const size=imgSize(o),url=path(o);
 return `<span class="tak-veil-aprs-icon-i672"><img src="${url}" alt="" width="${size}" height="${size}" draggable="false"></span>`;
}
window.TakMapVeilAprsI672=Object.freeze({source:'XTAK VEIL 0.4.0-r50',category,path,imgSize,markerHtml,normalized});
})();
