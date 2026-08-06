(function(){
'use strict';
const DEFAULT_VERSION='i620';
const AUTHORITY=window.__takMapReleaseIdentity||window.TakMapIdentityI620||null;
const AUTHORITY_VERSION=String(AUTHORITY&&AUTHORITY.iteration||'').trim();
const VERSION=/^(?:i|v)\d+$/i.test(AUTHORITY_VERSION)?AUTHORITY_VERSION:DEFAULT_VERSION;
const API_NAME='TakMapSidebarPerformanceV476';
if(window[API_NAME]&&window[API_NAME].loaded)return;

const S={
  version:VERSION,
  loaded:true,
  loadedAt:Date.now(),
  textContentGuardInstalled:false,
  setAttributeGuardInstalled:false,
  legacyObserversDisconnected:0,
  observerInstalled:false,
  normalizationRuns:0,
  normalizedElements:0,
  blockedSameTextWrites:0,
  coercedLegacyTextWrites:0,
  blockedSameAttributeWrites:0,
  coercedLegacyAttributeWrites:0,
  addedNodeScans:0,
  lastNormalizeAt:0,
  lastError:'',
};

const iterationSelector='.iteration-chip,.iteration-marker,[data-iteration]';
const versionToken=/^(?:i|v)\d+$/i;
const nativeSetAttribute=Element.prototype.setAttribute;
const nativeGetAttribute=Element.prototype.getAttribute;
const textDescriptor=Object.getOwnPropertyDescriptor(Node.prototype,'textContent');
const nativeTextGet=textDescriptor&&textDescriptor.get;
const nativeTextSet=textDescriptor&&textDescriptor.set;

function isIterationElement(node){
  if(!node||node.nodeType!==1)return false;
  try{return node.matches(iterationSelector)}catch(_){return false}
}
function currentText(node){
  try{return nativeTextGet?String(nativeTextGet.call(node)||''):String(node.textContent||'')}catch(_){return ''}
}
function normalizeToken(value){
  const text=String(value==null?'':value);
  return versionToken.test(text.trim())?VERSION:text;
}
function nativeWriteText(node,value){
  if(nativeTextSet)nativeTextSet.call(node,String(value));
}
function nativeWriteAttribute(node,name,value){
  nativeSetAttribute.call(node,name,String(value));
}

function installGuards(){
  try{
    if(!Element.prototype.__takMapIterationAttributeGuardV476){
      Object.defineProperty(Element.prototype,'__takMapIterationAttributeGuardV476',{value:true,configurable:true});
      Element.prototype.setAttribute=function(name,value){
        const attr=String(name||'').toLowerCase();
        if(attr==='data-iteration'&&isIterationElement(this)){
          const requested=String(value==null?'':value);
          const desired=versionToken.test(requested.trim())?VERSION:requested;
          const current=String(nativeGetAttribute.call(this,name)||'');
          if(current===desired){S.blockedSameAttributeWrites++;return;}
          if(desired!==requested)S.coercedLegacyAttributeWrites++;
          return nativeSetAttribute.call(this,name,desired);
        }
        if(attr==='data-tak-map-iteration'&&this===document.documentElement){
          const current=String(nativeGetAttribute.call(this,name)||'');
          if(current===VERSION){S.blockedSameAttributeWrites++;return;}
          if(String(value)!==VERSION)S.coercedLegacyAttributeWrites++;
          return nativeSetAttribute.call(this,name,VERSION);
        }
        return nativeSetAttribute.call(this,name,value);
      };
      S.setAttributeGuardInstalled=true;
    }else S.setAttributeGuardInstalled=true;
  }catch(error){S.lastError='setAttribute guard: '+String(error&&error.message||error)}

  try{
    if(textDescriptor&&nativeTextGet&&nativeTextSet&&!Node.prototype.__takMapIterationTextGuardV476){
      Object.defineProperty(Node.prototype,'__takMapIterationTextGuardV476',{value:true,configurable:true});
      Object.defineProperty(Node.prototype,'textContent',{
        configurable:textDescriptor.configurable,
        enumerable:textDescriptor.enumerable,
        get:nativeTextGet,
        set:function(value){
          if(isIterationElement(this)){
            const requested=String(value==null?'':value);
            const desired=normalizeToken(requested);
            const current=currentText(this);
            if(current===desired){S.blockedSameTextWrites++;return;}
            if(desired!==requested)S.coercedLegacyTextWrites++;
            return nativeTextSet.call(this,desired);
          }
          return nativeTextSet.call(this,value);
        }
      });
      S.textContentGuardInstalled=true;
    }else if(Node.prototype.__takMapIterationTextGuardV476)S.textContentGuardInstalled=true;
  }catch(error){S.lastError=(S.lastError?S.lastError+'; ':'')+'textContent guard: '+String(error&&error.message||error)}
}

function disconnectLegacyVersionObservers(){
  const explicit=['__takVersionObserverV442','__takMapVersionObserver','__takIterationObserver'];
  const seen=new Set();
  for(const key of explicit){
    try{
      const value=window[key];
      if(value&&typeof value.disconnect==='function'&&!seen.has(value)){
        value.disconnect();seen.add(value);S.legacyObserversDisconnected++;
      }
    }catch(_){}
  }
  try{
    for(const key of Object.getOwnPropertyNames(window)){
      if(!/(?:version|iteration).*observer|observer.*(?:version|iteration)/i.test(key))continue;
      const value=window[key];
      if(value&&typeof value.disconnect==='function'&&!seen.has(value)){
        value.disconnect();seen.add(value);S.legacyObserversDisconnected++;
      }
    }
  }catch(_){}
}

function normalizeElement(element){
  if(!isIterationElement(element))return 0;
  let changed=0;
  try{
    if(currentText(element)!==VERSION){nativeWriteText(element,VERSION);changed++;}
    if(nativeGetAttribute.call(element,'data-iteration')!==VERSION){nativeWriteAttribute(element,'data-iteration',VERSION);changed++;}
  }catch(error){S.lastError=String(error&&error.message||error)}
  return changed;
}
function normalizeRoot(root){
  S.normalizationRuns++;
  S.lastNormalizeAt=Date.now();
  let changed=0;
  try{
    if(root&&root.nodeType===1)changed+=normalizeElement(root);
    const scope=root&&typeof root.querySelectorAll==='function'?root:document;
    for(const element of scope.querySelectorAll(iterationSelector))changed+=normalizeElement(element);
    const html=document.documentElement;
    if(html&&nativeGetAttribute.call(html,'data-tak-map-iteration')!==VERSION){nativeWriteAttribute(html,'data-tak-map-iteration',VERSION);changed++;}
  }catch(error){S.lastError=String(error&&error.message||error)}
  S.normalizedElements+=changed;
  return changed;
}

function installObserver(){
  if(S.observerInstalled||!window.MutationObserver||!document.body)return;
  const observer=new MutationObserver(records=>{
    for(const record of records){
      if(record.type!=='childList'||!record.addedNodes.length)continue;
      for(const node of record.addedNodes){
        if(node.nodeType!==1)continue;
        S.addedNodeScans++;
        if(isIterationElement(node)||node.querySelector&&node.querySelector(iterationSelector))normalizeRoot(node);
      }
    }
  });
  observer.observe(document.body,{subtree:true,childList:true});
  S.observer=observer;
  S.observerInstalled=true;
}

function diagnostics(){
  const sidebar=document.getElementById('sidebar');
  const chips=[...document.querySelectorAll(iterationSelector)].map(el=>({
    text:currentText(el),
    dataIteration:nativeGetAttribute.call(el,'data-iteration')||'',
    className:typeof el.className==='string'?el.className:'',
  }));
  return {
    ...S,
    observer:undefined,
    currentIteration:VERSION,
    chipCount:chips.length,
    chips,
    sidebarPresent:!!sidebar,
    stable:chips.every(item=>item.text===VERSION&&item.dataIteration===VERSION),
    memoryPolicy:'one child-list-only observer; no attribute observation; legacy version writes normalized without DOM mutation',
  };
}

function boot(){
  installGuards();
  disconnectLegacyVersionObservers();
  normalizeRoot(document);
  installObserver();
  window[API_NAME]={loaded:true,diagnostics,normalize:()=>normalizeRoot(document),stop:()=>{try{S.observer&&S.observer.disconnect()}catch(_){}S.observerInstalled=false;}};
  console.log('[TAK Map] sidebar-performance-v491: loaded');
}

if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});
else boot();
})();
