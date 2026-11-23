'use strict';
// Minimal deterministic browser-state test for the active i553 core refresh logic.
const assert = require('assert');
const fs=require('fs');
const vm=require('vm');
const source=fs.readFileSync(require('path').join(__dirname,'../assets/tak-map-core-i553.js'),'utf8');
const start=source.indexOf('async function refreshImports()');
const end=source.indexOf('function toggleImportedObjects(',start);
assert(start>0&&end>start,'refreshImports must be defined in active core');
const method=source.slice(start,end);
const lastSession=[{id:'saved',name:'Existing Objects',features:[{object_id:'local-point',kind:'point',lat:34,lon:-118,coords:[[34,-118]]}]}];
const state={window:{},document:{getElementById:()=>({innerHTML:''})},
  fetch:async()=>({ok:false,status:500,json:async()=>({ok:false,error:'backend failed'})}),
  esc:(v)=>String(v),draws:0,lists:0,localRenders:0};
state.renderImportRows=()=>{state.lists++};state.drawImportedObjects=()=>{state.draws++};
state.refreshLocalData=()=>{state.localRenders++};
vm.createContext(state);
vm.runInContext(`let lastImports=${JSON.stringify(lastSession)};${method};globalThis.testRefresh=refreshImports;globalThis.getImports=()=>lastImports;`,state);
function bytesEqual(a,b){assert.deepStrictEqual(JSON.parse(JSON.stringify(a)),b)}
(async()=>{
  await state.testRefresh();
  bytesEqual(state.getImports(),lastSession);
  assert.strictEqual(state.draws,0,'failed HTTP request may not clear/repaint existing objects');
  state.fetch=async()=>({ok:true,json:async()=>({ok:false,imports:[]})});
  await state.testRefresh();
  bytesEqual(state.getImports(),lastSession);
  assert.strictEqual(state.draws,0,'ok:false response may not clear loaded objects');
  state.fetch=async()=>({ok:true,json:async()=>({ok:true,imports:[{id:'new',features:[{kind:'route',coords:[[34,-118],[35,-117]]}]}]})});
  await state.testRefresh();
  assert.strictEqual(state.getImports()[0].id,'new');
  assert.strictEqual(state.draws,1);
  assert.strictEqual(state.localRenders,1);
  // An earlier GET completing after a later GET must never revert newer data.
  let resolveEarlier, resolveLater;
  const earlier=new Promise(r=>resolveEarlier=r),later=new Promise(r=>resolveLater=r);
  let n=0;
  state.fetch=()=>++n===1?earlier:later;
  const first=state.testRefresh();const second=state.testRefresh();
  resolveLater({ok:true,json:async()=>({ok:true,imports:[{id:'latest',features:[]}]})});
  await second;
  resolveEarlier({ok:true,json:async()=>({ok:true,imports:[{id:'stale',features:[]}]})});
  await first;
  assert.strictEqual(state.getImports()[0].id,'latest');
  assert(source.includes('return out}function drawImportedObjects()'), 'importedFeatures must not hide saved point near route endpoint');
  assert(source.includes('if(!f._local_id)f._local_id=f.object_id||f.local_id'), 'frontend must preserve stable saved object IDs');
  assert(!source.includes('if(lid&&state.local.hidden[lid])continue;'),'2D/3D rendering must not inherit deprecated hide flags');
  console.log('PASS: 5 client hydration/visibility checks');
})().catch(err=>{console.error(err);process.exitCode=1});
