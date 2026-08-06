const fs=require('fs'),vm=require('vm');
class MapMock{
  constructor(z){this.options={zoomSnap:.5,zoomDelta:.5};this.z=z;this.h={};this.scrollWheelZoom={enabled:()=>true};}
  on(t,f){(this.h[t]||(this.h[t]=[])).push(f);return this}
  fire(t){for(const f of this.h[t]||[])f()}
  getZoom(){return this.z}
  setZoom(z){this.z=z;this.fire('zoomend');return this}
}
global.window=global;global.document={readyState:'complete',hidden:false,addEventListener(){}};global.setTimeout=(f)=>{f();return 1};global.addEventListener=()=>{};global.L={Map:{mergeOptions(o){this.defaults=o}}};global.map=new MapMock(9.5);global.takLeafletMap=global.map;
vm.runInThisContext(fs.readFileSync('assets/tak-map-whole-zoom-v491.js','utf8'));
const d=TakMapWholeZoomV476.diagnostics();
if(map.options.zoomSnap!==1||map.options.zoomDelta!==1||map.getZoom()!==10||!d.wholeNumberOnly)throw new Error(JSON.stringify(d));
map.z=8.4;map.fire('zoomend');if(map.z!==8)throw new Error('zoom did not snap '+map.z);
console.log('whole zoom passed');
