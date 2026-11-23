'use strict';
const assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs'),path=require('node:path');
const home=path.join(__dirname,'../assets');
const w={};const d={readyState:'loading',createElement:()=>({style:{},append(){}}),head:{append(){}},documentElement:{append(){}},addEventListener(){}};
const ctx={window:w,document:d,Math,Number,JSON,Map,Set,Date,console,encodeURIComponent,localStorage:{getItem:()=>null}};
vm.runInNewContext(fs.readFileSync(path.join(home,'tak-map-veil-visual-i669.js'),'utf8'),ctx);
const v=w.TakMapVeilVisualI669;assert.ok(v);
for(const [kind,code] of [['military','#0775d3'],['civilian','#0ca751'],['government','#7d009a'],['unknown','#b4ab25']]){
 const svg=decodeURIComponent(v.image({service:'adsb',classification:kind,heading:90}));
 assert.ok(svg.includes(code));assert.ok(svg.includes('rotate(90 20 20)'));assert.ok(svg.includes('A16 16'));
}
const a={service:'adsb',heading:270,hae:'3048',lat:34,lon:-118,id:'someid',identity:{icao:'abc123'}};
assert.equal(v.altitudePlacement(a,null).height,3048);
assert.equal(v.altitudePlacement(a,null).reference,'NONE');
assert.equal(v.altitudePlacement({...a,hae:undefined},null).source,'altitude unavailable');
assert.equal(v.altitudePlacement({service:'aprs'},103).height,103);
assert.equal(v.altitudePlacement({service:'ais'},null).reference,'CLAMP_TO_GROUND');
assert.equal(v.heading({heading:null}),null);assert.equal(v.heading({heading:361}),1);
assert.equal(v.adsbRow(a).altitude_ft,3048*3.280839895);
vm.runInNewContext(fs.readFileSync(path.join(home,'tak-map-range-rings-i669.js'),'utf8'),ctx);
const r=w.TakMapRangeRingsI669;assert.ok(r);
const s=r.normalize({name:'Test',center:{lat:34,lon:-118},interval:5,count:5,units:'mi',style:'dashed',remember:true},'one');
assert.ok(s&&s.style==='dashed');
assert.equal(r.normalize({...s,interval:500,units:'km'},'bad'),null);
const p=r.destination(s.center,5*1609.344,0);assert.ok(p.lat>s.center.lat);
function haversine(a,b){const rad=Math.PI/180,x=(b.lat-a.lat)*rad,y=(b.lon-a.lon)*rad;
 return 2*6371008.8*Math.asin(Math.sqrt(Math.sin(x/2)**2+Math.cos(a.lat*rad)*Math.cos(b.lat*rad)*Math.sin(y/2)**2));}
for(const ring of [1,3,5])for(const pt of r.ringPoints(s,ring).filter((_,i)=>i%14===0))
 assert.ok(Math.abs(haversine(s.center,pt)-ring*5*1609.344)<.5);
assert.ok(!fs.readFileSync(path.join(home,'tak-map-range-rings-i669.js'),'utf8').includes('value="dotted"'));
console.log('PASS i669 A3 colors, direction, valid HAE/unknown handling, geodesic multiple-ring math');
