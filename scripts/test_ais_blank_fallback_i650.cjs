'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const manifest=JSON.parse(fs.readFileSync('assets/tak-map-deferred-i553.json','utf8'));
const catalog=JSON.parse(fs.readFileSync('assets/mil2525/icons.json','utf8'));
const files={resolver:fs.readFileSync('assets/tak-map-milstd2525c-i553.js','utf8'),gateway:fs.readFileSync('assets/tak-map-gateway-data-v491.js','utf8')};
for(const [id,key] of [['takMapMilStd2525CLoaderI553','resolver'],['takMapGatewayDataLoaderV476','gateway']]){
 const s=manifest.scripts.filter(x=>x.id===id);assert.equal(s.length,1);assert.equal(s[0].code,files[key]);
}
const document={readyState:'loading',addEventListener(){},querySelectorAll(){return []},documentElement:{},head:{appendChild(){}}};
const window={document,setTimeout(){},clearTimeout(){},fetch:async()=>({ok:true,json:async()=>catalog}),addEventListener(){},dispatchEvent(){}};
const ctx={window,document,console,Set,Map,Object,Array,String,RegExp,Promise,setTimeout(){},clearTimeout(){},encodeURIComponent,CustomEvent:function(){}};
vm.createContext(ctx);vm.runInContext(files.resolver,ctx);
const r=window.TakMapMilStd2525CI553;assert(r);r._resetCatalogForTest(catalog);
function fakeImage(sidc,src,cotType){return {dataset:{sidc,cotType},onerror:null,style:{},_src:src,getAttribute(k){return k==='src'?this._src:''},set src(v){this._src=v},removeAttribute(k){if(k==='src')this._src=''}}}
let img=fakeImage('SNSP-----------','/mil2525/svg/neutral-sea-surface-tugboat.svg','a-n-S-X-M-T-U');r.onImageError(img);
assert(img._src.includes('neutral-sea-surface-civil-vessel.svg'),img._src);assert(!img._src.includes('-generic.svg'));
let generic=fakeImage('SNSP-----------','/mil2525/svg/neutral-sea-surface-generic.svg','a-n-S-X-M-NEW');r.onImageError(generic);
assert(generic._src.includes('neutral-sea-surface-civil-vessel.svg'),generic._src);
const code=files.gateway.slice(files.gateway.indexOf('function resolveAisTacticalSymbol('),files.gateway.indexOf('function milPointIcon('));
const c={};vm.createContext(c);vm.runInContext(code,c);
for(const t of ['a-n-S-X-M-P','a-n-S-X-M-C','a-n-S-X-Q-Z-Z','a-n-S-X','a-f-G-U-C-I','']){
 const o=c.resolveAisTacticalSymbol(r,{properties:{cot_type:t,source:'ais_vessels'}});
 assert(o,t);const res=r.resolveSymbol(o);assert(res.name.startsWith('neutral-sea-surface-')&&!res.name.endsWith('-generic'),`${t}: ${res.name}`);
}
console.log('PASS: 8 AIS blank-frame avoidance cases, registered visible vessel image on failure, direct/deferred script parity');
