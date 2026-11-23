const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const dir=path.join(__dirname,'../assets');
const document={head:{append(){}},documentElement:{},createElement:()=>({})};
const window={};
const ctx={window,document,console,encodeURIComponent,Number,Math,Object,Array,Set,Map,Date};vm.createContext(ctx);
for(const file of ['tak-map-adsbx-i670.js','tak-map-veil-aprs-i672.js','tak-map-veil-visual-i670.js','tak-map-veil-phase3-i668.js'])
  vm.runInContext(fs.readFileSync(path.join(dir,file),'utf8'),ctx,{filename:file});
const a=window.TakMapVeilAprsI672,v=window.TakMapVeilVisualI669,broker=window.TakMapVeilPhase3I668;
function aprs(symbol,extra={}){return {service:'aprs',aprs:{symbolCode:symbol,symbolTable:'/',weather:'false'},identity:{callsign:'K6ABC-9'},title:'K6ABC-9',...extra}}
for(const [sym,cat] of Object.entries({'_':'weather','#':'digipeater','!':'emergency','>':'vehicle','Y':'marine','^':'aircraft','b':'portable','-':'base','?':'generic'})){
 const o=aprs(sym);assert.equal(a.category(o),cat,cat);
 const url='/assets/runtime/veil-aprs-r50/aprs-'+cat+'.svg';
 assert.equal(v.image(o),url);assert.ok(v.markerHtml(o).includes(url));
 assert.ok(!v.markerHtml(o).includes('M17 30V15'),cat);
}
assert.equal(a.category(aprs('',{identity:{callsign:'K6XYZ-9'}})),'vehicle');
assert.equal(a.category(aprs('x',{aprs:{symbolCode:'x',objectType:'aprs_object'}})),'object');
const now=Date.now()/1000;
const base={service:'aprs',canonicalKey:'aprs:station:K6ABC-9',lat:34,lon:-118,
 timestamp:now,stale:now+120,freshness:'LIVE',nodeId:'a'};
const selected=broker.select([{...base,id:'udp-a',transport:'udp',timestamp:now-1,aprs:{symbolCode:'>',symbolTable:'/',weather:'false'}},
 {...base,id:'api-a',transport:'api',aprs:{symbolCode:'',symbolTable:'',weather:'false'}}]);
assert.equal(selected.objects.length,1);assert.equal(selected.objects[0].transport,'api');
assert.equal(selected.objects[0].aprs.symbolCode,'>');assert.equal(a.category(selected.objects[0]),'vehicle');
let adsb={service:'adsb',id:'a',canonicalKey:'adsb:icao:abcdef',heading:0,lat:34,lon:-118,
 timestamp:now,stale:now+120,identity:{icao:'abcdef'},enrichment:{type_designator:'A320'}};
assert.ok(v.image(adsb).includes('rotate(0%2020%2020)'));
assert.equal(v.heading(adsb),0);assert.equal(v.heading({...adsb,heading:90}),90);
assert.ok(v.image({...adsb,heading:90}).includes('rotate(90%2020%2020)'));
assert.ok(v.markerHtml(adsb).includes('stroke-width="1"'));
assert.ok(v.markerHtml({...adsb,heading:90}).includes('rotate(90 20 20)'));
assert.equal(v.heading({...adsb,heading:null,timestamp:now+1}),90);
assert.equal(v.heading({...adsb,heading:359}),359);
assert.equal(v.iconSize(adsb),43.2);
const selectedAdsb=broker.select([{...adsb,transport:'udp',timestamp:now-1,heading:180},
 {...adsb,id:'api-a',transport:'api',timestamp:now,heading:null}]);
assert.equal(selectedAdsb.objects[0].heading,180);
console.log('i672 original APRS r50 categories, both renderers, UDP/API metadata merge, ADS-B headings/stroke: PASS');
