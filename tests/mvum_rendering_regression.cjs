const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const script=fs.readFileSync(path.join(__dirname,'../assets/tak-map-mvum-i673.js'),'utf8');
const v=n=>{let out=[];while(n>127){out.push((n&127)|128);n=Math.floor(n/128)}return Buffer.from([...out,n])};
const bytes=(id,content)=>Buffer.concat([v(id*8+2),v(content.length),content]);
const scalar=(id,n)=>Buffer.concat([v(id*8),v(n)]);
const zz=n=>n<0?(-n*2-1):n*2;
const geo=Buffer.concat([v(9),v(zz(2048)),v(zz(2048)),v(10),v(zz(512)),v(zz(0))]);
const feature=Buffer.concat([scalar(3,2),bytes(4,geo)]);
const layer=Buffer.concat([bytes(1,Buffer.from('edges')),bytes(2,feature),scalar(5,4096),scalar(15,2)]);
const tile=bytes(3,layer);
const fetches=[];
let failNative=false;
const doc={head:{appendChild(){}},body:null,readyState:'loading',addEventListener(){},getElementById(){return null},createElement(name){if(name==='style')return {textContent:''};throw Error('No parent canvases should be created')}};
const win={};
const sandbox={window:win,document:doc,Map,Promise,AbortController,TextDecoder,Uint8Array,
 setInterval(){return 1},clearInterval(){},setTimeout(){return 1},clearTimeout(){},
 fetch(url){fetches.push(url);if(failNative&&/\/12\//.test(url))return Promise.resolve({ok:false,status:503});return Promise.resolve({ok:true,arrayBuffer:async()=>tile})}};
vm.createContext(sandbox);vm.runInContext(script,sandbox);
const api=win.TakMapMvumI673;api.state.enabled=true;api.state.revision='test-graph';
function canvas(){const strokes=[];const ctx={clearRect(){},beginPath(){},moveTo(x,y){strokes.push(['move',x,y])},lineTo(x,y){strokes.push(['line',x,y])},stroke(){strokes.push(['stroke',this.lineWidth])},drawImage(){throw Error('Raster stretch is forbidden')},set strokeStyle(v){},set lineWidth(v){this._lineWidth=v},get lineWidth(){return this._lineWidth},set lineCap(v){},set lineJoin(v){}};return {strokes,getContext(){return ctx}}}
(async()=>{
 // A z17 viewport must fetch the highest native z16 VECTOR tile and reproject the geometry.
 const hi=canvas();await api.drawTile(17,131075,130001,hi);
 assert(fetches.some(u=>/\/16\/65537\/65000\.pbf/.test(u)), 'z17 must fetch z16 parent');
 assert(!fetches.some(u=>/\/17\//.test(u)), 'server has no z17 endpoint');
 assert.deepStrictEqual(hi.strokes[0],['move',0,0]);
 assert.deepStrictEqual(hi.strokes[1],['line',64,0]);
 assert.deepStrictEqual(hi.strokes[2],['stroke',1.5]);
 // If native z12 fails, use z11 geometry, not an enlarged 256px bitmap.
 failNative=true;
 const fallback=canvas();await api.drawTile(12,101,75,fallback);
 assert(fetches.some(u=>/\/12\/101\/75\.pbf/.test(u)), 'attempt native tile first');
 assert(fetches.some(u=>/\/11\/50\/37\.pbf/.test(u)), 'fallback to z11 vector data');
 assert.deepStrictEqual(fallback.strokes[0],['move',0,0]);
 assert.deepStrictEqual(fallback.strokes[1],['line',64,0]);
 assert.deepStrictEqual(fallback.strokes[2],['stroke',1.5]);
 // Failed network requests must not redraw every displayed route tile.
 assert(!script.includes('state.layer.redraw()'), 'global retry redraw causes road flashing');
 assert(!script.includes('maxNativeZoom:16'), 'native-zoom cap would upscale low-resolution canvases');
 assert(script.includes("canvas.getContext('2d')?.setTransform?.(ratio"),'high DPI canvas is configured');
 console.log('MVUM native vector z17 reprojection, z12→z11 vector fallback, fixed-width strokes, no raster stretching, no global retry redraw, HiDPI: PASS');
})().catch(e=>{console.error(e);process.exitCode=1});
