'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const root=process.cwd();
const moduleSrc=fs.readFileSync('assets/tak-map-milstd2525c-i553.js','utf8');
const manifest=JSON.parse(fs.readFileSync('assets/tak-map-deferred-i553.json','utf8'));
const deferred=manifest.scripts.find(s=>s.id==='takMapMilStd2525CLoaderI553');
assert(deferred);
const catalog=JSON.parse(fs.readFileSync('assets/mil2525/icons.json','utf8'));
function resolverFrom(code){
 const document={readyState:'loading',addEventListener(){},querySelectorAll(){return []},documentElement:{},head:{appendChild(){}}};
 const window={document, setTimeout(){},clearTimeout(){},fetch(){}};
 const ctx={window,document,console,Set,Map,Object,Array,String,RegExp,Promise,setTimeout(){},clearTimeout(){},encodeURIComponent};
 vm.createContext(ctx); vm.runInContext(code,ctx);
 const r=window.TakMapMilStd2525CI553;assert(r);r._resetCatalogForTest(catalog);return r;
}
const direct=resolverFrom(moduleSrc), runtime=resolverFrom(deferred.code);
const cases={
 'a-n-S-X-M-P':'neutral-sea-surface-civil-vessel.svg',
 'a-n-S-X-M-T-O':'neutral-sea-surface-tugboat.svg',
 'a-n-S-X-F-D-R':'neutral-sea-surface-civil-vessel.svg',
 'a-n-S-X-F-T-R':'neutral-sea-surface-fishing-vessel.svg',
 'a-n-S-X-F-D-F':'neutral-sea-surface-fishing-vessel.svg',
 'a-n-S-X-H':'neutral-sea-surface-civil-vessel.svg',
 'a-n-S-X-M-C':'neutral-sea-surface-cargo-ship.svg'
};
for(const [type,file] of Object.entries(cases)){
 for(const r of [direct,runtime]){
  const result=r.resolveSymbol({type});
  assert(result.ok && result.file===file && result.catalogSidc.startsWith('SNSP'), `${type}: ${JSON.stringify(result)}`);
 }
}
// Exercise the actual Gateway Data point-icon renderer against the resolver.
const js=fs.readFileSync('assets/tak-map-gateway-data-v491.js','utf8');
function extract(name,nextName){const i=js.indexOf('function '+name+'('),j=js.indexOf('function '+nextName+'(',i+1); assert(i>=0&&j>i);return js.slice(i,j);}
const code=extract('milMetadata','pointIcon')+extract('pointIcon','geometryError');
const L={divIcon(o){return o}};
const w={TakMapMilStd2525CI538:direct,mil2525IconHtml(o){return direct.resolveSymbol(o).file}};
const ctx={w,leaflet:()=>L,sourceColor:()=>'',aisIconProfile:()=>({src:'/assets/ais-civil.png',width:12,height:12,variant:'civil'}),iconSvg(){}};
vm.createContext(ctx);vm.runInContext(code,ctx);
function icon(props){return vm.runInContext('pointIcon(input)',Object.assign(ctx,{input:{properties:props}}));}
const passenger=icon({source:'ais_vessels',cot_type:'a-n-S-X-M-P',metadata:{vessel_name:'HERMOSA',symbol:'Passenger',mmsi:'366652000'}});
assert.strictEqual(passenger.iconSize[0],48);assert.strictEqual(passenger.iconSize[1],48);
assert.strictEqual(passenger.html,'neutral-sea-surface-civil-vessel.svg');
assert(passenger.className.includes('gateway-data-ais-milstd2525c-i648'));
const wrongSidc=icon({source:'ais_vessels',sidc:'SFGPUCI--------',cot_type:'a-n-S-X-M-P',metadata:{symbol:'Passenger'}});
assert.strictEqual(wrongSidc.html,'neutral-sea-surface-civil-vessel.svg');
const unknown=icon({source:'ais_vessels',cot_type:'a-n-S-X-UNKNOWN',metadata:{symbol:'Other'}});
assert.strictEqual(unknown.html,'neutral-sea-surface-civil-vessel.svg');
// Ensure non-AIS military symbols remain unchanged.
const ground=icon({source:'other',sidc:'SFGPUCI--------'});
assert.strictEqual(ground.html,'friendly-ground-unit-infantry.svg');
console.log('AIS neutral sea-surface resolver and renderer tests passed (direct + deferred, passenger, missing roles, wrong SIDC, non-AIS unchanged)');
