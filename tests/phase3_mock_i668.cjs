'use strict';
const assert=require('node:assert/strict'),vm=require('node:vm'),fs=require('node:fs'),path=require('node:path');
const w={};const ctx={window:w,Date,Number,String,Map,Set,Math,encodeURIComponent,console};
vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../assets/tak-map-veil-phase3-i668.js'),'utf8'),ctx);
const b=w.TakMapVeilPhase3I668;assert.ok(b);
const now=Date.now()/1000;
const obj=(id,node,key,t=now-2,lat=34)=>({id,nodeId:node,canonicalKey:key,service:key?.startsWith('ais:')?'ais':'adsb',transport:'api',timestamp:t,stale:now+90,lat,lon:-118,freshness:'LIVE'});
let rows=[obj('one','node1','adsb:icao:abc123',now-5),obj('two','node2','adsb:icao:abc123',now-1),obj('three','node1','adsb:icao:abc124')];
let r=b.select(rows,{mergeVeilDuplicates:true,services:{}});
assert.equal(r.objects.length,2);assert.equal(r.merged,1);assert.equal(r.objects.find(x=>x.canonicalKey==='adsb:icao:abc123').id,'two');
assert.equal(r.objects.find(x=>x.id==='two').__veilCandidates.length,2);
assert.equal(b.select(rows,{mergeVeilDuplicates:false}).objects.length,3);
rows=[obj('one','n1','adsb:icao:abc123'),obj('two','n2','adsb:icao:abc124',now-1,34)];
assert.equal(b.select(rows,{mergeVeilDuplicates:true}).objects.length,2); // proximity never merged
assert.equal(b.select([obj('one','n1',null),obj('two','n2',null)]).objects.length,2);
w.TakMapVeilNativeI668=()=>({adsbVisible:true,aircraft:[{icao:'abc123',lat:34,lon:-118,seen_seconds:2}]});
assert.equal(b.select([obj('one','n1','adsb:icao:abc123')],{crossSourceDedup:false}).objects.length,1);
assert.equal(b.select([obj('one','n1','adsb:icao:abc123')],{crossSourceDedup:true}).objects.length,0);
w.TakMapVeilNativeI668=()=>({adsbVisible:false,aircraft:[{icao:'abc123',lat:34,lon:-118,seen_seconds:2}]});
assert.equal(b.select([obj('one','n1','adsb:icao:abc123')],{crossSourceDedup:true}).objects.length,1);
let stale=obj('old','n1','adsb:icao:abc123',now-60);stale.stale=now-1;
assert.equal(b.select([stale]).objects.length,0);
rows=[obj('good','n1','adsb:icao:abc123',now-8),obj('stale','n2','adsb:icao:abc123',now-2)];rows[1].freshness='STALE';
assert.equal(b.select(rows).objects[0].id,'good');
assert.equal(b.select([obj('ais1','n1','ais:mmsi:311000397'),obj('ais2','n2','ais:mmsi:311000397')]).objects.length,1);
// Verify the exact elected objects enter an independent Cesium data source.
const scene={active:true,viewer:{dataSources:{added:[],add(x){this.added.push(x);return Promise.resolve(x)},remove(x){this.added=this.added.filter(y=>y!==x)}},scene:{requestRender(){}}}};
w.TakMapVeilSceneI668=()=>scene;
w.Cesium={CustomDataSource:class{constructor(){const entities=[];this.entities={values:entities,getById:id=>entities.find(x=>x.id===id),add:x=>{entities.push(x);return x},remove:x=>{const n=entities.indexOf(x);if(n>=0)entities.splice(n,1)}}}},
 Cartesian3:{fromDegrees:(x,y,h)=>({x,y,h})},VerticalOrigin:{BOTTOM:1},HeightReference:{CLAMP_TO_GROUND:1}};
let rendered=[];
const elected=b.render([obj('v1','n1','adsb:icao:abc123'),obj('v2','n2','adsb:icao:abc123')],{mergeVeilDuplicates:true},o=>{rendered=o});
assert.equal(elected.objects.length,1);assert.equal(rendered.length,0);assert.equal(scene.viewer.dataSources.added.length,1);
assert.equal(scene.viewer.dataSources.added[0].entities.values.length,1);
scene.active=false;b.render([obj('v1','n1','adsb:icao:abc123')],{},o=>{rendered=o});
assert.equal(rendered.length,1);assert.equal(scene.viewer.dataSources.added.length,0);
console.log('PASS i668 broker selection, provenance, invalid identity, stale/fallback, native guards');
