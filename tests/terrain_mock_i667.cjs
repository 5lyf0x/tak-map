// i667 terrain renderer functional fixture; no external Cesium or network required.
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const root=path.resolve(__dirname,'..');
const src=fs.readFileSync(path.join(root,'assets/tak-map-core-i553.js'),'utf8');
const start=src.indexOf('// i667: One Cesium overlay lifecycle');
const finish=src.indexOf('function terrainAddObject(o,source){',start);
assert(start>0&&finish>start);
const code=src.slice(start,finish);
const collection=()=>({values:[],add(v){this.values.push(v);return v},removeAll(){this.values=[]}});
const viewer={entities:collection(),dataSources:{values:[],add(o){this.values.push(o);return Promise.resolve(o)}},
  camera:{positionCartographic:{height:1500},computeViewRectangle(){const d=Math.PI/180;return {west:-1*d,east:1*d,south:-1*d,north:1*d}}},
  scene:{globe:{ellipsoid:{}}}};
class DS{constructor(name){this.name=name;this.entities=collection()}}
const Cesium={CustomDataSource:DS,ArcType:{GEODESIC:3},HeightReference:{CLAMP_TO_GROUND:9},
 Cartesian3:{fromDegrees:(x,y,z=0)=>({x,y,z}),fromDegreesArray:a=>a},
 PolylineDashMaterialProperty:class {constructor(v){this.color=v.color;this.dashLength=v.dashLength}},
 SceneTransforms:{wgs84ToWindowCoordinates:(_,p)=>({x:p.x*100+250,y:p.y*100+250})}};
const window={Cesium,terrain3DElevationSource:'streamed',sampleLocalElevationAt:()=>100,
 TakMapIconRegistryI572:{resolveObjectSymbol:o=>o.registryIcon||null}};
const sandbox={window,Cesium,terrain3DViewer:viewer,terrain3DQuality:'high',
 map:{getZoom:()=>15},terrain3DActive:true,
 terrainQualitySettings:()=>({maxRouteVerts:650,maxShapeVerts:420}),
 terrainSimplifyCoordList:p=>p,terrainPointVisible:(lat,lon)=>Math.abs(lat)<=1&&Math.abs(lon)<=1,
 collectCoordPairs:function walk(a){let out=[];for(const v of a||[]){if(Array.isArray(v)&&v.length>=2&&typeof v[0]==='number'&&typeof v[1]==='number')out.push(v);else if(Array.isArray(v))out=out.concat(walk(v))}return out},
 isFiniteLatLon:(a,b)=>Number.isFinite(+a)&&Number.isFinite(+b)&&Math.abs(+a)<=90&&Math.abs(+b)<=180,
 cesiumColor:(color,opacity)=>({color,opacity}),generatedMil2525File:()=>('mil.svg'),mil2525IconFilePath:f=>'/mil2525/'+f,
 console};
vm.createContext(sandbox);
vm.runInContext(code,sandbox,{timeout:10000});
// Viewport intersection with endpoints outside must render.
sandbox.terrainPolylineEntity([[0,-4],[0,4]],'Crossing','#abc123',{color:'#ee3311',line_style:'dashed',weight:5});
let objs=viewer.dataSources.values[0].entities.values;
assert.strictEqual(objs.length,1,'crossing route should draw');
assert.strictEqual(objs[0].polyline.width,5);
assert.strictEqual(objs[0].polyline.clampToGround,true);
assert(objs[0].polyline.material instanceof Cesium.PolylineDashMaterialProperty);
assert.strictEqual(objs[0].polyline.material.color.color,'#ee3311');
// Entirely offscreen route suppressed.
sandbox.terrainPolylineEntity([[8,8],[9,9]],'off','#ff0000',{});
assert.strictEqual(objs.length,1,'offscreen route should not draw');
// Shape styling, fill control, dashed outline and partial overlap.
sandbox.terrainPolygonEntity([[.4,-2],[.4,2],[1.5,2]],'Shape','#ccc',
 {properties:{color:'#22aa33',fill_color:'#ffa500',fill:true,fill_opacity:.36,weight:4,line_style:'dashed'}});
objs=viewer.dataSources.values[0].entities.values;
assert.strictEqual(objs.length,3,'shape should have fill and outline');
assert.strictEqual(objs[1].polygon.material.color,'#ffa500');
assert.strictEqual(objs[1].polygon.material.opacity,.36);
assert.strictEqual(objs[2].polyline.width,4);
assert(objs[2].polyline.material instanceof Cesium.PolylineDashMaterialProperty);
sandbox.terrainPolygonEntity([[-.4,-.4],[-.4,.4],[.4,.4]],'Outline Only','#eee',
 {fill:false,color:'#1155aa'});
objs=viewer.dataSources.values[0].entities.values;
assert.strictEqual(objs.length,4,'fill disabled should only add one outline');
// A huge polygon may cover the entire camera view even when every edge is off-screen.
viewer.dataSources.values[0].entities.removeAll();
sandbox.terrainPolygonEntity([[-10,-10],[-10,10],[10,10],[10,-10]],'Enclosing area','#cc8800',{});
objs=viewer.dataSources.values[0].entities.values;
assert.strictEqual(objs.length,2,'enclosing polygon must be rendered');
viewer.dataSources.values[0].entities.removeAll();
// TAK native open shapes are lines, not filled/closed polygons; honor i636 metadata.
viewer.dataSources.values[0].entities.removeAll();
sandbox.terrainPolygonEntity([[0,0],[0,.2]],'Open CoT Shape','#fff',
 {shape_closed_i636:false,style_i636:{stroke_css:'#c057dc',line_style:'dashed',weight:7}});
objs=viewer.dataSources.values[0].entities.values;
assert.strictEqual(objs.length,1);
assert.strictEqual(objs[0].polyline.positions.length,4); // two lat/lon pairs, no closing leg
assert.strictEqual(objs[0].polyline.width,7);
assert.strictEqual(objs[0].polyline.material.color.color,'#c057dc');
viewer.dataSources.values[0].entities.removeAll();
// Explicit registry selection is more authoritative than CoT affiliation.
assert.strictEqual(sandbox.terrainBillboardImage({cot_type:'a-f-G-U-C',registryIcon:{kind:'custom',iconsetpath:'uid/Shapes/camp.png',asset_url:'/api/custom-camp.png'}}),'/api/custom-camp.png');
assert.strictEqual(sandbox.terrainBillboardImage({cot_type:'a-n-G-U-C',registryIcon:{kind:'custom',iconsetpath:'uid/Shapes/camp.png'}}),'/api/tak-map/icon-registry/icon?path=uid%2FShapes%2Fcamp.png');
assert.strictEqual(sandbox.terrainBillboardImage({}),'/mil2525/mil.svg');
// Local DEM heights must be elevated above the surface rather than globe-clamped.
window.terrain3DElevationSource='local';
viewer.dataSources.values[0].entities.removeAll();
sandbox.terrainPolylineEntity([[0,0],[.1,.1]],'DEM route','#f80',{color:'#f80'});
objs=viewer.dataSources.values[0].entities.values;
assert.strictEqual(objs.length,1);
assert.strictEqual(objs[0].polyline.clampToGround,false);
assert.strictEqual(objs[0].polyline.positions[0].z,105);
viewer.dataSources.values[0].entities.removeAll();
sandbox.terrainPolygonEntity([[0,0],[0,.1],[.1,.1]],'DEM shape','#f80',{color:'#f80'});
objs=viewer.dataSources.values[0].entities.values;
assert.strictEqual(objs[0].polygon.perPositionHeight,true);
assert.strictEqual(objs[1].polyline.positions[0].z,105);
// Data refresh may clear live entities without clearing managed terrain overlays.
viewer.entities.removeAll();assert.strictEqual(viewer.dataSources.values[0].entities.values.length,2);
console.log('i667 Cesium route/shape/custom-icon local-DEM fixture PASS');
