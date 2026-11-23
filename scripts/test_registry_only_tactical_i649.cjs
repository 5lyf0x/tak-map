#!/usr/bin/env node
'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const root=process.cwd();
const code=fs.readFileSync('assets/tak-map-milstd2525c-i553.js','utf8');
const gw=fs.readFileSync('assets/tak-map-gateway-data-v491.js','utf8');
const dash=fs.readFileSync('tak_dashboard.py','utf8');
const registry=fs.readFileSync('assets/tak-map-icon-registry-i572.js','utf8');
const catalog=JSON.parse(fs.readFileSync('assets/mil2525/icons.json','utf8'));
const manifest=JSON.parse(fs.readFileSync('assets/tak-map-deferred-i553.json','utf8'));
for(const [id,content] of [['takMapMilStd2525CLoaderI553',code],['takMapGatewayDataLoaderV476',gw]]) {
 const row=manifest.scripts.filter(x=>x.id===id);assert.equal(row.length,1);assert.equal(row[0].code,content);
}
const names=new Set(catalog.map(x=>x.name));
for(const aff of ['friendly','neutral','hostile','unknown'])for(const domain of ['ground','air','sea-surface','subsurface','space'])assert(names.has(`${aff}-${domain}-generic`),`${aff} ${domain}`);
function run(source) {
 const document={readyState:'loading',addEventListener(){},querySelectorAll(){return []},getElementById(){return null},documentElement:{},head:{appendChild(){}}};
 const window={document,setTimeout(){},clearTimeout(){},fetch:async()=>({ok:true,json:async()=>catalog}),addEventListener(){},dispatchEvent(){}};
 const ctx={window,document,console,Set,Map,Object,Array,String,RegExp,Promise,setTimeout(){},clearTimeout(){},encodeURIComponent,CustomEvent:function(){}};
 vm.createContext(ctx);vm.runInContext(source,ctx);
 const api=window.TakMapMilStd2525CI553;assert(api);api._resetCatalogForTest(catalog);
 const cases=[
  [{cot_type:'a-f-G-U-C-I'},'friendly-ground-'],
  [{cot_type:'a-n-S-X-M-P'},'neutral-sea-surface-'],
  [{cot_type:'a-n-S-Q-Z-FUTURE'},'neutral-sea-surface-generic'],
  [{cot_type:'a-h-A-Z-Z-FUTURE'},'hostile-air-generic'],
  [{cot_type:'a-u-U-Z-Z-FUTURE'},'unknown-subsurface-generic'],
  [{cot_type:'a-f-P-Z-Z-FUTURE'},'friendly-space-generic'],
  [{sidc:'SNGPQQ---------',iconsetPath:'other/not-found'},'neutral-ground-generic'],
  [{cot_type:'not-a-tactical-type'},'unknown-ground-generic'],
  [{},'unknown-ground-generic']
 ];
 for(const [obj,expected] of cases){
  const html=api.iconHtml(obj);
  assert(html.includes('class="tak-mil2525-img"'),JSON.stringify(obj));
  assert(html.includes('/mil2525/svg/'),JSON.stringify(obj));
  assert(!html.includes('<svg')&&!html.includes('<path')&&!html.includes('tak-usericon-i553'),html);
  const match=html.match(/\/mil2525\/svg\/([^"?]+)\.svg/);assert(match,html);
  const name=decodeURIComponent(match[1]);assert(names.has(name),name);
  assert(name.startsWith(expected),`${name} vs ${expected}`);
  const generated=api.resolveSymbol(obj);
  assert(!generated.ok || names.has(generated.name));
 }
 assert(!source.includes('function userIconFallbackHtml('));
 assert(!source.includes("w.milShape(affiliationSlug(promoted)"));
 return cases.length;
}
assert.equal(run(code),9);
assert.equal(run(manifest.scripts.find(x=>x.id==='takMapMilStd2525CLoaderI553').code),9);
assert(!/\$\{frame\}\$\{body\|\|/.test(dash),'inline tactical frame still present');
assert(!gw.includes("if(src==='ais_vessels'){const icon=aisIconProfile(feature)"),'AIS PNG fallback remains');
assert(gw.includes("takmap:milstd-catalog-ready"),'missing catalog-ready redraw');
assert(registry.includes("if (tacticalSourceMetadata(object)) return typeof base === 'function'"),'registry tactical authority missing');
assert(registry.includes("if (!tacticalSourceMetadata(object) && icon && icon.kind === 'custom'"),'Data Sync registry authority missing');
console.log('PASS: registry-only MIL-STD tactical icons; 18 resolver cases, source/deferred parity, CoT/AIS fallback, no inline X');
