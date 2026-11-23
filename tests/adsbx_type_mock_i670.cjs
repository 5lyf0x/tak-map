const fs=require('fs'),vm=require('vm'),assert=require('assert');
const path=require('path');const dir=path.join(__dirname,'../assets');
const head={append(){}},document={createElement:()=>({set id(v){this._id=v},set textContent(v){this._css=v}}),head,documentElement:{}};
const window={TakMapAdsbSidebarI610:{openExternal(row){window._clicked=row;return true}}};
const ctx={window,document,console,encodeURIComponent,Number,Math,Object,Array,Set};vm.createContext(ctx);
for (const name of ['tak-map-adsbx-i670.js','tak-map-veil-visual-i670.js'])vm.runInContext(fs.readFileSync(dir+'/'+name,'utf8'),ctx,{filename:name});
const lib=window.TakMapAdsbxI670,vis=window.TakMapVeilVisualI669;
function obs(type,classif='civilian',h=75){return {service:'adsb',heading:h,classification:classif,nodeId:'node-a',id:'test',identity:{icao:'a1b2c3'},enrichment:{type_designator:type},lat:34,lon:-118,hae:2000}}
for(const [type,shape] of Object.entries({A320:'a320',A321:'a321',B738:'b738',B739:'b739',A359:'a359',A388:'a380',C130:'c130',F18:'f18',H60:'blackhawk',H64:'apache',C17:'c17',A319:'a319',SR22:'cirrus_sr22'})){
  let a=lib.select(obs(type));assert.equal(a.shape,shape,type);assert.equal(a.exact,true,type);assert.ok(a.path.length>100,type);
  const html=vis.markerHtml(obs(type)),svg=decodeURIComponent(vis.image(obs(type)));
  assert.ok(html.includes('data-adsbx-shape="'+shape+'"'),type);
  assert.ok(svg.includes('data-adsbx-shape="'+shape+'"'),type);
  assert.ok(html.includes('rotate(75 20 20)'),type);
  assert.ok(!html.includes('A16 16'),type);
}
let plain=lib.select(obs('QXYZ'));assert.ok(lib.shapes[plain.shape]);assert.equal(plain.exact,false);
let shared=lib.select(obs('F22'));assert.equal(shared.shape,'f35');assert.equal(shared.exact,true);
for(const cls of ['military','civilian','government','unknown']){const svg=vis.markerHtml(obs('A320',cls));assert.ok(svg.includes('fill="#ffffff"'));assert.ok(svg.includes('stroke="#000000" stroke-width="1"'));assert.equal(vis.iconSize(obs('A320',cls)),43.2)}
assert.ok(vis.openAdsb(obs('B738'),null));assert.equal(window._clicked.aircraft_type,'B738');assert.equal(window._clicked.source,'XTAK VEIL · node-a');
assert.equal(lib.version,'1.4.0-i670');assert.equal(vis.version,'1.4.0-i672');
assert.equal(Object.keys(lib.typeMappings).length,376);assert.equal(Object.keys(lib.shapes).length,30);
console.log('ADSBx exact mappings, original assets, category colors, heading, SVG parity, detail panel, fallback: PASS');
