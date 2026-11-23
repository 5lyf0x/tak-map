const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const src=fs.readFileSync(path.join(__dirname,'../assets/tak-map-mvum-i673.js'),'utf8');
function element(id=''){
 const e={id,children:[],parentElement:null,style:{values:{},setProperty(k,v){this.values[k]=v}},classList:{toggle(){}},_attrs:{},nodeType:1,
  setAttribute(k,v){this._attrs[k]=v},addEventListener(k,fn){this['on'+k]=fn},
  contains(n){return this===n||this.children.some(c=>c.contains(n))},
  insertBefore(n,ref){if(n.parentElement)n.parentElement.removeChild(n);let i=ref?this.children.indexOf(ref):-1;if(i<0)i=this.children.length;this.children.splice(i,0,n);n.parentElement=this;return n},
  appendChild(n){return this.insertBefore(n,null)},
  removeChild(n){const i=this.children.indexOf(n);if(i>=0)this.children.splice(i,1);n.parentElement=null},
  remove(){if(this.parentElement)this.parentElement.removeChild(this)},
  querySelector(s){if(s.includes('UndoRoute'))return this.children.find(x=>x.isUndo)||null;return null},
  querySelectorAll(){return[]}};
 Object.defineProperty(e,'firstChild',{get(){return this.children[0]||null}});
 Object.defineProperty(e,'previousElementSibling',{get(){if(!this.parentElement)return null;const a=this.parentElement.children;return a[a.indexOf(this)-1]||null}});
 return e;
}
const body=element('body'),head=element('head'),bar=element('routeMiniToolbar'),undo=element('undo');undo.isUndo=true;
body.appendChild(bar);bar.appendChild(undo);
const root={body,head,readyState:'complete',createElement(){return element()},getElementById(id){const stack=[body,head];while(stack.length){const n=stack.pop();if(n.id===id)return n;stack.push(...n.children)}return null}};
const win={};let observerCallback;
const sandbox={window:win,document:root,Map,Promise,AbortController,TextDecoder,Uint8Array,
 setInterval(fn){fn();return 1},clearInterval(){},setTimeout(){return 1},clearTimeout(){},
 queueMicrotask(fn){fn()},MutationObserver:class{constructor(fn){observerCallback=fn}observe(){}},
 fetch(){throw Error('Network must not be required to show button')}};
vm.createContext(sandbox);vm.runInContext(src,sandbox);
const api=win.TakMapMvumI673;
assert(api,'script exports MVUM controller');
assert(root.getElementById('takMvumButtonI673'),'button mounts without any map');
assert.strictEqual(bar.children[0].id,'takMvumButtonI673','MVUM is above Undo');
assert.strictEqual(bar.children[0].textContent,'MVUM');
assert.strictEqual(bar.children[0].style.values['font-size'],'10px','visible text overrides global icon-only styling');
assert.strictEqual(api.state.map,null,'no map required for initial mount');
// Map arrives later, exactly one handler is attached.
let calls=0;const fakePane=element('pane');win.takLeafletMap={getPane(){return fakePane},createPane(){return fakePane},on(){calls++},getZoom(){return 12}};
assert(api.install());assert.strictEqual(api.state.map,win.takLeafletMap);assert.strictEqual(calls,1);
assert(api.install());assert.strictEqual(calls,1,'no duplicate Leaflet handlers');
// Rebuilt toolbar must self-heal even if the old button was removed with it.
body.removeChild(bar);const replacement=element('routeMiniToolbar'),newUndo=element('undo');newUndo.isUndo=true;
replacement.appendChild(newUndo);body.appendChild(replacement);
observerCallback([{target:body,addedNodes:[replacement],removedNodes:[bar]}]);
assert.strictEqual(replacement.children[0].id,'takMvumButtonI673','button survives route toolbar replacement');
assert.strictEqual(root.getElementById('takMvumStatusI673').parentElement,replacement,'status follows button');
assert.strictEqual(replacement.children.filter(e=>e.id==='takMvumButtonI673').length,1,'exactly one MVUM');
console.log('MVUM route-toolbar mount, ordering, text visibility, late Leaflet init, toolbar replacement, duplicate guard: PASS');
