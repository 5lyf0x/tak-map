#!/usr/bin/env node
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.resolve(__dirname,'..');
const gw=fs.readFileSync(path.join(root,'assets/tak-map-gateway-data-v491.js'),'utf8');
const milSource=fs.readFileSync(path.join(root,'assets/tak-map-milstd2525c-i553.js'),'utf8');
const dashboard=fs.readFileSync(path.join(root,'tak_dashboard.py'),'utf8');
const pt=gw.slice(gw.indexOf('function pointIcon(feature)'),gw.indexOf('function featureIdentity(f)'));
assert(pt.startsWith('function pointIcon(feature)'));
assert(pt.indexOf('const mil=milPointIcon(feature);if(mil)return mil;')<pt.indexOf("if(src==='ais_vessels')"));
const mock={calls:0,leaflet:()=>({divIcon:x=>x}),sourceColor:()=> '#64c9e8',aisIconProfile:()=>({src:'/assets/ais-civil.png',width:12,height:12,variant:'civil'}),milPointIcon:f=>{mock.calls++;return f.properties.cot_type ? {className:'gateway-data-milstd2525c-i538 gateway-data-ais-milstd2525c-i648',iconSize:[48,48]}:null},iconSvg:()=>''};
const make=new Function('leaflet','sourceColor','milPointIcon','aisIconProfile','iconSvg',pt+'return pointIcon;')(...['leaflet','sourceColor','milPointIcon','aisIconProfile','iconSvg'].map(k=>mock[k]));
const ais=make({properties:{source:'ais_vessels',cot_type:'a-f-S-C'}});
assert.deepEqual(ais.iconSize,[48,48]);
assert.match(ais.className,/gateway-data-milstd2525c-i538/);
assert.equal(mock.calls,1);
const fallback=make({properties:{source:'ais_vessels'}});
assert.deepEqual(fallback.iconSize,[48,48]);
assert.match(fallback.className,/gateway-data-awaiting-milstd-i649/);
assert.match(gw,/gateway-data-milstd2525c-i538:not\(\.gateway-data-selected-i614\)\{filter:none!important\}/);
assert.match(gw,/gateway-data-ais-milstd2525c-i648.gateway-data-selected-i614\{filter:drop-shadow\(0 0 3px rgba\(255,48,48,\.98\)\)/);
assert(!dashboard.includes('.tak-icon-wrap{display:flex;align-items:center;justify-content:center;filter:drop-shadow('));
assert(!dashboard.includes('.tak-icon-selected{filter:drop-shadow('));
assert.match(milSource,/function ensureMilStd2525CNoShadowI648\(\)/);
assert.match(milSource,/\.tak-icon-wrap, \.tak-icon-wrap img, \.tak-icon-wrap svg/);
assert.match(milSource,/ensureMilStd2525CNoShadowI648\(\);\s*patchGlobals\(\)/);
const manifest=JSON.parse(fs.readFileSync(path.join(root,'assets/tak-map-deferred-i553.json'),'utf8'));
for(const [id,contents] of [['takMapGatewayDataLoaderV476',gw],['takMapMilStd2525CLoaderI553',milSource]]) {
 const rows=manifest.scripts.filter(x=>x.id===id);
 assert.equal(rows.length,1);
 assert.equal(rows[0].code,contents);
}
console.log('PASS: MIL-STD AIS priority (48px), fallback, all-symbol no-shadow CSS, red selection, synchronized deferred');
