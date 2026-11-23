/* TAK Map i673 — MVUM: live NDM/Valhalla graph-edge overlay, not USDA MVUM legal map. */
(function(W,D){'use strict';
const state={enabled:false,map:null,layer:null,epoch:0,timer:null,tileCache:new Map(),running:0,queue:[],revision:'',status:'Off',requests:0,bufferHits:0,pending:0};
const MAX_CACHE=620,MAX_CONCURRENT=6;const boundButtons=new WeakSet();
let bufferToken=0,bufferSchedule=null;const runningJobs=new Set(),failures=new Map();
function status(txt){state.status=String(txt);const el=D.getElementById('takMvumStatusI673');if(el)el.textContent=state.status;const b=D.getElementById('takMvumButtonI673');if(b){b.title='NDM Navigation Network — '+state.status;b.setAttribute('aria-pressed',String(state.enabled));b.classList.toggle('active',state.enabled)}}
function readVar(b,at,end){let n=0,shift=0,v;do{if(at.i>=end||shift>56)throw Error('Invalid MVT varint');v=b[at.i++];n+=(v&127)*2**shift;shift+=7}while(v&128);return n}
function skip(b,p,wire,end){if(wire===0)readVar(b,p,end);else if(wire===1)p.i+=8;else if(wire===2){const n=readVar(b,p,end);p.i+=n}else if(wire===5)p.i+=4;else throw Error('Unsupported MVT wire type');if(p.i>end)throw Error('Truncated MVT')}
function fields(b,start,end,cb){const p={i:start};while(p.i<end){const h=readVar(b,p,end),id=Math.floor(h/8),w=h%8;if(w===2){const n=readVar(b,p,end),begin=p.i,stop=begin+n;if(stop>end)throw Error('Truncated MVT field');cb(id,b,begin,stop,2);p.i=stop}else if(w===0){const begin=p.i;readVar(b,p,end);cb(id,b,begin,p.i,0)}else{skip(b,p,w,end)}}}
// Project graph geometry into the destination tile while keeping the stroke width
// in screen pixels. Never upscale an already rasterized parent canvas.
function geometry(b,start,end,ctx,extent,view){const p={i:start},scale=(256/extent)*(view?.scale||1),dx=view?.offsetX||0,dy=view?.offsetY||0;let x=0,y=0;ctx.beginPath();let paths=0,pts=0;while(p.i<end){const cmd=readVar(b,p,end),op=cmd&7,count=cmd>>3;if(count>500000)throw Error('Too many MVT coordinates');if(op===1||op===2){for(let i=0;i<count;i++){x+=zig(readVar(b,p,end));y+=zig(readVar(b,p,end));if(op===1){ctx.moveTo(x*scale-dx,y*scale-dy);paths++}else ctx.lineTo(x*scale-dx,y*scale-dy);pts++}}else if(op===7){/* polygon closure irrelevant for edges */}else throw Error('Invalid MVT geometry');}if(paths&&pts>=2)ctx.stroke();return pts}
function zig(n){return n%2?-(n+1)/2:n/2}
function drawMvt(data,canvas,view,clear=true){const ctx=canvas.getContext('2d');if(!ctx)return;if(clear)ctx.clearRect(0,0,256,256);ctx.strokeStyle='#E53935';ctx.lineWidth=1.5;ctx.lineCap='round';ctx.lineJoin='round';const b=new Uint8Array(data);if(b.length>2500000)throw Error('MVT too large');let features=0;
 fields(b,0,b.length,(id,b,s,e)=>{if(id!==3)return;let name='',extent=4096,feat=[];
  fields(b,s,e,(k,b,a,z)=>{if(k===1)name=new TextDecoder().decode(b.subarray(a,z));else if(k===5){const p={i:a};extent=readVar(b,p,z)||4096}else if(k===2)feat.push([a,z])});
  if(name!=='edges')return;for(const [a,z] of feat){let typ=0,g=null;fields(b,a,z,(k,b,i,j)=>{if(k===3){const p={i};typ=readVar(b,p,j)}else if(k===4)g=[i,j]});if(typ===2&&g){geometry(b,g[0],g[1],ctx,extent,view);features++}}});return features}
function key(z,x,y){return state.revision+':'+z+'/'+x+'/'+y}
function pruneQueued(){for(const j of runningJobs){if(j.buffer&&j.view!==bufferToken)j.ctl?.abort()}const dropped=state.queue.filter(j=>j.buffer&&j.view!==bufferToken);state.queue=state.queue.filter(j=>!(j.buffer&&j.view!==bufferToken));dropped.forEach(j=>{state.tileCache.delete(j.k);j.reject(Error('MVUM view changed'))})}
function getTile(z,x,y,buffer=false){const k=key(z,x,y),hit=state.tileCache.get(k);if(hit){state.bufferHits++;state.tileCache.delete(k);state.tileCache.set(k,hit);return hit}
 const epoch=state.epoch,view=bufferToken;const promise=new Promise((resolve,reject)=>{const job={z,x,y,k,epoch,view,buffer,resolve,reject};if(buffer)state.queue.push(job);else state.queue.unshift(job);pump()});state.tileCache.set(k,promise);
 // Errors may fall back to a coarser graph tile. Do not force GridLayer.redraw()
 // after a failed request: it destroys every visible tile and causes flashing.
 promise.catch(()=>{if(state.tileCache.get(k)===promise)state.tileCache.delete(k)});while(state.tileCache.size>MAX_CACHE){const oldest=state.tileCache.keys().next().value;state.tileCache.delete(oldest)}return promise}
function pump(){pruneQueued();while(state.running<MAX_CONCURRENT&&state.queue.length){const j=state.queue.shift();if(j.epoch!==state.epoch||!state.enabled||(j.buffer&&j.view!==bufferToken)){state.tileCache.delete(j.k);j.reject(Error('MVUM view changed'));continue}state.running++;state.requests++;
 const ctl=new AbortController(),timeout=setTimeout(()=>ctl.abort(),18000);j.ctl=ctl;runningJobs.add(j);
 fetch('/api/tak-map/ndm/network/tiles/current/'+j.z+'/'+j.x+'/'+j.y+'.pbf',{credentials:'same-origin',signal:ctl.signal,cache:'no-store'})
  .then(async r=>{if(!r.ok)throw Error('NDM network tile unavailable ('+r.status+')');return r.arrayBuffer()})
  .then(j.resolve,j.reject).finally(()=>{clearTimeout(timeout);runningJobs.delete(j);state.running--;pump()});}}
// Server supports z11–z16 only. For z17–z24, reproject the native z16
// VECTOR tile into the child viewport; the network is never asked for z>16.
// For native misses, fall back to z11 vectors, NOT an enlarged 256px image.
function drawParentTile(bytes,z,x,y,sourceZ,canvas){
 const factor=2**(z-sourceZ),px=Math.floor(x/factor),py=Math.floor(y/factor);
 return drawMvt(bytes,canvas,{scale:factor,offsetX:(x-px*factor)*256,offsetY:(y-py*factor)*256});
}
function drawTile(z,x,y,canvas){
 if(z===9||z===10){
  // Native NDM tiles begin at z11. Reproject actual vector edges to the
  // lower-zoom viewport; never blow up an existing raster tile.
  const factor=2**(11-z),count=factor*factor,cell=256/factor;
  return Promise.allSettled(Array.from({length:count},(_,i)=>getTile(11,x*factor+(i%factor),y*factor+Math.floor(i/factor))))
   .then(parts=>{const ctx=canvas.getContext('2d');ctx.clearRect(0,0,256,256);
    parts.forEach((part,i)=>{if(part.status!=='fulfilled')return;
      const col=i%factor,row=Math.floor(i/factor);ctx.save();ctx.beginPath();ctx.rect(col*cell,row*cell,cell,cell);ctx.clip();
      drawMvt(part.value,canvas,{scale:1/factor,offsetX:-col*cell,offsetY:-row*cell},false);ctx.restore();
    });});
 }
 const sourceZ=Math.min(z,16),factor=2**(z-sourceZ);
 const sourceX=Math.floor(x/factor),sourceY=Math.floor(y/factor);
 return getTile(sourceZ,sourceX,sourceY).then(buf=>{
   if(z===sourceZ)return drawMvt(buf,canvas);
   return drawParentTile(buf,z,x,y,sourceZ,canvas);
 }).catch(async err=>{
   if(sourceZ<=11)throw err;
   const baseFactor=2**(z-11),parentX=Math.floor(x/baseFactor),parentY=Math.floor(y/baseFactor);
   const bytes=await getTile(11,parentX,parentY);
   return drawParentTile(bytes,z,x,y,11,canvas);
 });
}
function inBounds(b){return b&&[b.west,b.south,b.east,b.north].every(Number.isFinite)}
async function probe(){const r=await fetch('/api/tak-map/ndm/network/status',{credentials:'same-origin',cache:'no-store'});if(!r.ok)throw Error('NDM status unavailable');const j=await r.json();if(!j.ok||!j.router_ready)throw Error('Router offline');const ver=String(j.graph_revision||'current-uncertain');if(ver!==state.revision){state.revision=ver;state.tileCache.clear();failures.clear()}return j}
function clearPending(){state.epoch++;bufferToken++;clearTimeout(bufferSchedule);for(const j of runningJobs)j.ctl?.abort();state.queue.splice(0).forEach(j=>{state.tileCache.delete(j.k);j.reject(Error('MVUM stopped'))})}
function warmBuffer(){if(!state.enabled||!state.map||!state.layer)return;bufferToken++;pruneQueued();clearTimeout(bufferSchedule);
 const m=state.map,z=Math.max(9,Math.min(16,Math.round(m.getZoom())));if(m.getZoom()<9){status('Zoom 9 or higher to view NDM roads');return}
 // At z9/z10 the visible tiles already consume multiple source vectors: avoid speculative buffer requests.
 if(z<11)return;
 const half=m.getSize(),c=m.project(m.getCenter(),z),ratio=2**(z-m.getZoom()),padX=half.x*ratio,padY=half.y*ratio;
 const minX=Math.floor((c.x-padX)/256),maxX=Math.floor((c.x+padX)/256),minY=Math.floor((c.y-padY)/256),maxY=Math.floor((c.y+padY)/256),n=2**z;
 const view=bufferToken;let row=Math.max(0,minY),col=minX,scheduled=0;
 function batch(){if(view!==bufferToken||!state.enabled)return;if(state.queue.length>=120){bufferSchedule=setTimeout(batch,250);return}let count=0;
  while(row<=Math.min(n-1,maxY)&&count<48){const x=((col%n)+n)%n,y=row;col++;if(col>maxX){col=minX;row++}if(z===10){for(let k=0;k<4;k++)getTile(11,x*2+(k%2),y*2+Math.floor(k/2),true).catch(()=>{})}else getTile(z,x,y,true).catch(()=>{});count++;scheduled++}
  status('MVUM on · '+scheduled+' buffer tiles requested');if(row<=Math.min(n-1,maxY))bufferSchedule=setTimeout(batch,100);
 }
 // Priority for new onscreen tiles comes from GridLayer createTile; defer speculative work.
 bufferSchedule=setTimeout(batch,250);
}
function schedule(){clearTimeout(state.timer);if(!state.enabled)return;state.timer=setTimeout(warmBuffer,320)}
async function toggle(){install();if(!state.map){status('Map is not ready');return}if(state.enabled){state.enabled=false;clearPending();if(state.layer&&state.map?.hasLayer(state.layer))state.map.removeLayer(state.layer);status('Off · cached tiles retained');return}
 state.enabled=true;status('Checking NDM network…');try{const j=await probe();if(!state.enabled)return;
  if(!state.layer){const Grid=W.L.GridLayer.extend({createTile:function(c,done){const canvas=D.createElement('canvas');const ratio=Math.min(2,Math.max(1,Number(W.devicePixelRatio)||1));canvas.width=Math.round(256*ratio);canvas.height=Math.round(256*ratio);canvas.style.width='256px';canvas.style.height='256px';canvas.getContext('2d')?.setTransform?.(ratio,0,0,ratio,0,0);const z=c.z,x=((c.x%2**z)+2**z)%2**z,y=c.y;
    if(z<9){setTimeout(()=>done(null,canvas),0);return canvas}drawTile(z,x,y,canvas).then(()=>done(null,canvas)).catch(()=>done(null,canvas));return canvas}});
   state.layer=new Grid({pane:'takMvumPaneI673',tileSize:256,updateWhenIdle:true,updateWhenZooming:false,keepBuffer:10,minZoom:9,maxZoom:24,opacity:1});}
  state.layer.addTo(state.map);status(j.coverage_note||'MVUM on');schedule();
 }catch(e){state.enabled=false;status(String(e.message||e));}}
// MVUM is a Route toolbar control, not an NDM/map readiness indicator.
// Render it whenever the Route toolbar exists, even while Leaflet/NDM is loading.
function ensureButton(){
 const bar=D.getElementById('routeMiniToolbar');if(!bar)return false;
 let button=D.getElementById('takMvumButtonI673');
 if(button&&!bar.contains(button)){button.remove();button=null}
 if(!button){
  button=D.createElement('button');button.type='button';button.className='tool-btn tak-mvum-btn-i673';
  button.id='takMvumButtonI673';button.title='NDM Navigation Network';button.textContent='MVUM';
  button.setAttribute('aria-label','MVUM NDM Navigation Network');
 }
 // Bind both native toolbar-created and fallback-injected buttons exactly once.
 // A later compact-toolbar rebuild can replace this DOM node at any time.
 if(!boundButtons.has(button)){
  boundButtons.add(button);button.dataset.takMvumBoundI696='1';
  button.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();toggle()});
 }
 // The compact toolbar styles intentionally set text-only buttons to font-size:0.
 // MVUM has no SVG, so ensure its text remains visible despite later CSS.
 button.style.setProperty('font-size','10px','important');
 button.style.setProperty('line-height','1.1','important');
 button.style.setProperty('white-space','nowrap','important');
 button.style.setProperty('display','grid','important');
 button.style.setProperty('place-items','center','important');
 button.style.setProperty('font-family','Manrope,system-ui,sans-serif','important');
 const undo=bar.querySelector('[onclick*="v233UndoRoute"],[title*="Undo"],button[data-tool="undo"]');
 if(undo&&button!==undo.previousElementSibling)bar.insertBefore(button,undo);
 else if(!bar.contains(button))bar.insertBefore(button,bar.firstChild);
 let st=D.getElementById('takMvumStatusI673');
 if(st&&!bar.contains(st)){st.remove();st=null}
 if(!st){st=D.createElement('small');st.id='takMvumStatusI673';st.className='tak-mvum-status-i673';bar.appendChild(st)}
 status(state.status);return true;
}
function mapIfReady(){
 const candidates=[W.takLeafletMap,W.map];
 return candidates.find(m=>m&&typeof m.getPane==='function'&&typeof m.createPane==='function'&&typeof m.on==='function'&&typeof m.getZoom==='function')||null;
}
function install(){
 const hasToolbar=ensureButton();
 const m=mapIfReady();
 if(m&&state.map!==m){
  if(state.map&&typeof state.map.off==='function')state.map.off('moveend zoomend resize',schedule);
  state.map=m;
  if(!m.getPane('takMvumPaneI673')){const pane=m.createPane('takMvumPaneI673');pane.style.zIndex='330';pane.style.pointerEvents='none'}
  m.on('moveend zoomend resize',schedule);
 }
 return hasToolbar;
}
function watchToolbar(){
 if(!D.body||typeof MutationObserver==='undefined')return;
 // Watch toolbar identity and children; not map tile mutations or CSS restyles.
 const ob=new MutationObserver(records=>{
  const bar=D.getElementById('routeMiniToolbar');
  if(!bar)return;
  const button=D.getElementById('takMvumButtonI673');
  const st=D.getElementById('takMvumStatusI673');
  const undo=bar.querySelector('[onclick*="v233UndoRoute"],[title*="Undo"],button[data-tool="undo"]');
  if(button&&bar.contains(button)&&boundButtons.has(button)&&st&&bar.contains(st)&&(!undo||button===undo.previousElementSibling))return;
  if(records.some(r=>r.target===bar||[...r.addedNodes,...r.removedNodes].some(n=>n.nodeType===1&&(
    n.id==='routeMiniToolbar'||n.id==='takMvumButtonI673'||n.id==='takMvumStatusI673'||n.querySelector?.('#routeMiniToolbar,#takMvumButtonI673,#takMvumStatusI673'))))){
    queueMicrotask(install);
  }
 });
 ob.observe(D.body,{childList:true,subtree:true});
}
const css=D.createElement('style');css.textContent=`#routeMiniToolbar #takMvumButtonI673{font-size:10px!important;font-weight:850!important;color:#e7f7f9!important;letter-spacing:.3px;padding:1px!important}#routeMiniToolbar #takMvumButtonI673.active{background:#17617b!important;border:1px solid #59b9d5!important}#routeMiniToolbar .tak-mvum-status-i673{font-size:0!important;display:none!important}`;D.head.appendChild(css);
W.TakMapMvumI673={state,toggle,install,warmBuffer,drawMvt,drawTile,getTile,ensureButton};let tries=0;const t=setInterval(()=>{if((install()&&state.map)||++tries>120)clearInterval(t)},200);
// Recovery is deliberately limited to toolbar identity; never redraw the map.
W.setInterval(()=>{const bar=D.getElementById('routeMiniToolbar');if(bar&&(!bar.querySelector('#takMvumButtonI673')||!boundButtons.has(bar.querySelector('#takMvumButtonI673'))))ensureButton()},1600);if(D.readyState==='loading')D.addEventListener('DOMContentLoaded',watchToolbar,{once:true});else watchToolbar();
})(window,document);
