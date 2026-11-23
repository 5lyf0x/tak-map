'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const root=process.cwd();
const resolverCode=fs.readFileSync('assets/tak-map-milstd2525c-i553.js','utf8');
const deferred=JSON.parse(fs.readFileSync('assets/tak-map-deferred-i553.json','utf8')).scripts.find(s=>s.id==='takMapMilStd2525CLoaderI553');
assert(deferred, 'deferred MIL resolver');
const catalog=JSON.parse(fs.readFileSync('assets/mil2525/icons.json','utf8'));
const src=fs.readFileSync('assets/tak-map-gateway-data-v491.js','utf8');
function codeChunk(code,begin,end){const a=code.indexOf('function '+begin+'('),b=code.indexOf('function '+end+'(',a+1);assert(a>=0&&b>a,begin);return code.slice(a,b)}
const renderer=codeChunk(src,'milMetadata','pointIcon')+codeChunk(src,'pointIcon','geometryError');
const classes=[
 'a-n-S-X-M', 'a-n-S-X-F', 'a-n-S-X-R', 'a-n-S-X-M-T-O', 'a-n-S-X-F-D-R',
 'a-n-S-X-M-T-U','a-n-S-X-L','a-n-S-X-M-P','a-n-S-X-M-C',
 'a-n-S-X-M-O','a-n-S-X-M-F','a-n-S-X-F-T-R','a-n-S-X-F-D-F','a-n-S-X-H'
];
const future=[
 'a-n-S-X-M-NEW','a-n-S-X-F-NEW','a-n-S-X-M-T-U-NEW','a-n-S-X-F-D-R-NEW',
 'a-n-S-X-Q-Z-Z','a-n-S-X-X','a-n-S-X','a-f-G-U-C-I','bad-coordinates',''
];
function run(rCode){
 const document={readyState:'loading',addEventListener(){},querySelectorAll(){return []},documentElement:{},head:{appendChild(){}}};
 const window={document,setTimeout(){},clearTimeout(){},fetch(){}};
 const rctx={window,document,console,Set,Map,Object,Array,String,RegExp,Promise,setTimeout(){},clearTimeout(){},encodeURIComponent};
 vm.createContext(rctx);vm.runInContext(rCode,rctx);
 const resolver=window.TakMapMilStd2525CI553;assert(resolver);resolver._resetCatalogForTest(catalog);
 const L={divIcon(o){return o}};
 const w={TakMapMilStd2525CI538:resolver,mil2525IconHtml(o){return resolver.resolveSymbol(o).file}};
 const ctx={w,leaflet:()=>L,sourceColor:()=>'',aisIconProfile:()=>({src:'/assets/ais-civil.png',width:12,height:12,variant:'civil'}),iconSvg(){}};
 vm.createContext(ctx);vm.runInContext(renderer,ctx);
 function icon(properties){ctx.input={properties};return vm.runInContext('pointIcon(input)',ctx)}
 let count=0;
 for(const type of [...classes,...future]){
  for(const extra of [
   {},
   {sidc:'SFGPUCI--------',iconsetPath:'friendly-ground-unit-infantry'},
   {metadata:{symbol:'Unknown future AIS class',mil2525_sidc:'SFGPUCI--------'}}
  ]){
   const row={source:'ais_vessels',cot_type:type,metadata:{symbol:'Raw AIS class',...extra.metadata},...extra};
   const marker=icon(row);
   assert.strictEqual(marker.iconSize[0],48,JSON.stringify(row));
   assert.strictEqual(marker.iconSize[1],48,JSON.stringify(row));
   assert(marker.html.startsWith('neutral-sea-surface-'),JSON.stringify({row,icon:marker}));
   assert(marker.html.endsWith('.svg'));
   assert(marker.className.includes('gateway-data-ais-milstd2525c-i648'));
   count++;
  }
 }
 const known=icon({source:'ais_vessels',cot_type:'a-n-S-X-M-C'});
 assert.strictEqual(known.html,'neutral-sea-surface-cargo-ship.svg');
 const futureCargo=icon({source:'ais_vessels',cot_type:'a-n-S-X-M-C-FUTURE'});
 assert.strictEqual(futureCargo.html,'neutral-sea-surface-cargo-ship.svg');
 const futureOther=icon({source:'ais_vessels',cot_type:'a-n-S-X-M-ANOTHER'});
 assert.strictEqual(futureOther.html,'neutral-sea-surface-civil-vessel.svg');
 const nonAis=icon({source:'other',sidc:'SFGPUCI--------'});
 assert.strictEqual(nonAis.html,'friendly-ground-unit-infantry.svg');
 return count;
}
const a=run(resolverCode),b=run(deferred.code);
assert.strictEqual(a,b);
assert(!src.includes('366652000')&&!src.includes('HERMOSA'), 'AIS source cannot special-case one MMSI or vessel name');
console.log('Universal Gateway AIS symbol tests passed:',a,'cases each for direct/deferred resolver; source-guard, hierarchy, unknown classes and non-AIS all checked');
