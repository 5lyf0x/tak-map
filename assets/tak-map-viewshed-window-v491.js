(function(w,d){
'use strict';
const VERSION='i491';
const STORAGE_KEY='takmap.viewshed.modulePos.i491';
const READY_ATTR='data-tak-viewshed-ready-v491';
const LEGACY_TOGGLE=typeof w.toggleViewshedModule==='function'?w.toggleViewshedModule:null;
const S={toolActive:false,toolDeactivations:0,toolStateBinds:0,panel:null,observer:null,desired:null,dragging:false,repairing:false,userPosition:false,repairs:0,opens:0,drags:0,boots:0,ownerInstalls:0,headerBound:false};
function $(id){try{return d.getElementById(id)}catch(_){return null}}
function q(sel,root){try{return (root||d).querySelector(sel)}catch(_){return null}}
function finite(n){n=Number(n);return Number.isFinite(n)?n:null}
function clamp(n,min,max){n=finite(n);if(n===null)n=min;return Math.max(min,Math.min(max,n))}
function viewport(){return {width:Math.max(320,w.innerWidth||d.documentElement.clientWidth||320),height:Math.max(320,w.innerHeight||d.documentElement.clientHeight||320)}}
function toolbarRect(){try{const el=$('floatingMapToolbar')||q('.floating-map-toolbar,.map-toolbar');const r=el&&el.getBoundingClientRect&&el.getBoundingClientRect();return r&&r.width>4&&r.height>4?r:null}catch(_){return null}}
function panelSize(panel){try{const r=panel.getBoundingClientRect();const cs=w.getComputedStyle(panel);return {width:Math.max(260,r.width||panel.offsetWidth||parseFloat(cs.width)||318),height:Math.max(180,r.height||panel.offsetHeight||parseFloat(cs.height)||440)}}catch(_){return {width:318,height:440}}}
function bounded(left,top,panel){const vp=viewport(),size=panelSize(panel),safe=8;return {left:Math.round(clamp(left,safe,Math.max(safe,vp.width-size.width-safe))),top:Math.round(clamp(top,safe,Math.max(safe,vp.height-Math.min(size.height,vp.height-safe*2)-safe)))}}
function memoryPosition(){try{const p=w.__takMapViewshedSessionPosV488;if(p&&finite(p.left)!==null&&finite(p.top)!==null)return {left:Number(p.left),top:Number(p.top)}}catch(_){}try{const raw=w.sessionStorage&&w.sessionStorage.getItem(STORAGE_KEY);const p=raw&&JSON.parse(raw);if(p&&finite(p.left)!==null&&finite(p.top)!==null)return {left:Number(p.left),top:Number(p.top)}}catch(_){}return null}
function savePosition(pos){if(!pos)return;const clean={left:Math.round(pos.left),top:Math.round(pos.top)};w.__takMapViewshedSessionPosV488=clean;try{w.sessionStorage&&w.sessionStorage.setItem(STORAGE_KEY,JSON.stringify(clean))}catch(_){} }
function defaultPosition(panel){const saved=memoryPosition();if(saved){S.userPosition=true;return bounded(saved.left,saved.top,panel)}const tb=toolbarRect(),size=panelSize(panel),gap=12;S.userPosition=false;if(tb)return bounded(tb.left-size.width-gap,tb.top,panel);const vp=viewport();return bounded(vp.width-size.width-88,88,panel)}
function isOpen(panel){if(!panel)return false;if(panel.classList.contains('v383-force-hidden'))return false;return panel.classList.contains('active')||panel.classList.contains('open')||panel.getAttribute('aria-hidden')==='false'}
function samePosition(panel,pos){if(!panel||!pos)return false;const left=parseFloat(panel.style.left),top=parseFloat(panel.style.top);return Number.isFinite(left)&&Number.isFinite(top)&&Math.abs(left-pos.left)<0.5&&Math.abs(top-pos.top)<0.5&&panel.style.right==='auto'}
function setImportant(style,name,value){try{style.setProperty(name,value,'important')}catch(_){try{style[name]=value}catch(__){}}}
function applyPosition(panel,pos,markReady){if(!panel||!pos)return false;const boundedPos=bounded(pos.left,pos.top,panel);S.desired=boundedPos;S.repairing=true;try{
  panel.style.removeProperty('inset');
  setImportant(panel.style,'position','fixed');
  setImportant(panel.style,'left',boundedPos.left+'px');
  setImportant(panel.style,'top',boundedPos.top+'px');
  setImportant(panel.style,'right','auto');
  setImportant(panel.style,'bottom','auto');
  panel.dataset.viewshedStableOpen='1';
  panel.dataset.viewshedUserPosition=S.userPosition?'1':'0';
  if(markReady!==false)panel.setAttribute(READY_ATTR,'1');
}finally{S.repairing=false}return true}
function setVisible(panel,visible){S.repairing=true;try{setImportant(panel.style,'visibility',visible?'visible':'hidden');setImportant(panel.style,'opacity',visible?'1':'0')}finally{S.repairing=false}}
function syncToolButton(){const btn=$('toolViewshed');if(btn){btn.classList.toggle('active',!!S.toolActive);btn.classList.remove('open');btn.setAttribute('aria-pressed',S.toolActive?'true':'false')}return S.toolActive}
function activateTool(){S.toolActive=true;syncToolButton();return true}
function deactivateTool(reason){if(S.toolActive)S.toolDeactivations++;S.toolActive=false;try{if(w.v249Viewshed)w.v249Viewshed.pickMode=null}catch(_){}try{const m=w.map||w.takLeafletMap;m&&m.getContainer&&m.getContainer().classList.remove('viewshed-pick-active')}catch(_){}syncToolButton();return false}
function bindToolState(){if(w.__takViewshedToolStateV488)return;w.__takViewshedToolStateV488=true;S.toolStateBinds++;
 const old=w.setActiveMapTool;if(typeof old==='function'&&!old.__takViewshedStateV488){const wrapped=function(tool){const out=old.apply(this,arguments);if(String(tool||'move').toLowerCase()!=='viewshed')deactivateTool('tool-switch');return out};wrapped.__takViewshedStateV488=true;wrapped.__takViewshedOriginal=old;w.setActiveMapTool=wrapped}
 d.addEventListener('click',function(ev){const btn=ev.target&&ev.target.closest&&ev.target.closest('.tool-btn');if(btn&&btn.id!=='toolViewshed')deactivateTool('toolbar-click')},true);
 d.addEventListener('keydown',function(ev){if(ev.key==='Escape'&&S.toolActive)deactivateTool('escape')},true)
}
function establish(panel){if(!panel||!isOpen(panel))return false;setVisible(panel,false);const pos=S.desired||defaultPosition(panel);applyPosition(panel,pos,true);setVisible(panel,true);syncToolButton();S.opens++;return true}
function repair(panel){if(!panel||S.dragging||S.repairing||!isOpen(panel))return false;if(!S.desired)return establish(panel);if(samePosition(panel,S.desired)&&panel.getAttribute(READY_ATTR)==='1')return false;S.repairs++;applyPosition(panel,S.desired,true);setVisible(panel,true);return true}
function closePanel(panel){if(!panel)return false;S.repairing=true;try{panel.classList.remove('active','open');panel.classList.add('v383-force-hidden');setImportant(panel.style,'display','none');panel.setAttribute('aria-hidden','true');panel.removeAttribute(READY_ATTR);panel.dataset.viewshedStableOpen='0';if(!S.userPosition)S.desired=null;deactivateTool('close')}finally{S.repairing=false}return true}
function openPanel(panel){if(!panel)return false;S.repairing=true;try{panel.classList.remove('v382-force-hidden','v383-force-hidden');panel.classList.add('active');setImportant(panel.style,'display','block');panel.setAttribute('aria-hidden','false');panel.removeAttribute(READY_ATTR)}finally{S.repairing=false}S.desired=S.userPosition&&memoryPosition()?bounded(memoryPosition().left,memoryPosition().top,panel):null;return establish(panel)}
function ensurePanel(){let panel=$('viewshedModule');if(panel)return panel;try{if(typeof LEGACY_TOGGLE==='function')LEGACY_TOGGLE.call(w,true)}catch(_){}panel=$('viewshedModule');if(panel){observePanel(panel);bindHeader(panel)}return panel}
function ownerToggle(on){const panel=ensurePanel();if(!panel)return false;const show=on==null?!isOpen(panel):!!on;if(show)activateTool();else deactivateTool('toggle-off');return show?openPanel(panel):closePanel(panel)}
ownerToggle.__takViewshedOwnerV487=true;
ownerToggle._v289Wrapped=true;
ownerToggle._v290Wrapped=true;
ownerToggle._v307Wrapped=true;
ownerToggle.__v350ViewshedTheme=true;
function ownerOpen(ev){try{ev&&ev.preventDefault&&ev.preventDefault();ev&&ev.stopPropagation&&ev.stopPropagation()}catch(_){}ownerToggle(true);return false}
ownerOpen.__v350ViewshedTheme=true;
ownerOpen.__v349ViewshedOwner=true;
function installOwner(){bindToolState();w.toggleViewshedModule=ownerToggle;w.openTakMapViewshed=ownerOpen;w.positionViewshedDefault=function(force){const panel=$('viewshedModule');if(!panel)return false;if(force&&!S.userPosition)S.desired=null;if(!S.desired)S.desired=defaultPosition(panel);return applyPosition(panel,S.desired,true)};const btn=$('toolViewshed');if(btn){btn.onclick=ownerOpen;syncToolButton()}S.ownerInstalls++}
function bindHeader(panel){if(!panel||S.headerBound)return;const header=q('.viewshed-head',panel);if(!header)return;S.headerBound=true;header.style.touchAction='none';header.addEventListener('pointerdown',function(event){
  if(event.button!==0||event.target.closest('button,input,select,textarea,a,label'))return;
  const rect=panel.getBoundingClientRect(),startX=event.clientX,startY=event.clientY,startLeft=rect.left,startTop=rect.top;
  S.dragging=true;S.userPosition=true;panel.dataset.viewshedUserPosition='1';
  try{event.preventDefault();event.stopPropagation();event.stopImmediatePropagation();header.setPointerCapture&&header.setPointerCapture(event.pointerId)}catch(_){}
  function move(ev){if(!S.dragging)return;try{ev.preventDefault();ev.stopPropagation()}catch(_){}const pos=bounded(startLeft+(ev.clientX-startX),startTop+(ev.clientY-startY),panel);S.desired=pos;applyPosition(panel,pos,true)}
  function finish(ev){if(!S.dragging)return;S.dragging=false;try{header.releasePointerCapture&&header.releasePointerCapture(event.pointerId)}catch(_){}if(S.desired)savePosition(S.desired);S.drags++;try{ev&&ev.preventDefault&&ev.preventDefault();ev&&ev.stopPropagation&&ev.stopPropagation()}catch(_){}header.removeEventListener('pointermove',move,true);header.removeEventListener('pointerup',finish,true);header.removeEventListener('pointercancel',finish,true)}
  header.addEventListener('pointermove',move,true);header.addEventListener('pointerup',finish,true);header.addEventListener('pointercancel',finish,true);
},true)}
function observePanel(panel){if(!panel||S.panel===panel&&S.observer)return;if(S.observer)try{S.observer.disconnect()}catch(_){}S.panel=panel;S.observer=new MutationObserver(function(){if(S.repairing||S.dragging)return;if(isOpen(panel)){if(!S.desired)establish(panel);else repair(panel)}else{panel.removeAttribute(READY_ATTR);panel.dataset.viewshedStableOpen='0';deactivateTool('panel-hidden');if(!S.userPosition)S.desired=null}});S.observer.observe(panel,{attributes:true,attributeFilter:['class','style','aria-hidden']})}
function installCss(){if($('takMapViewshedWindowStyleV488'))return;const st=d.createElement('style');st.id='takMapViewshedWindowStyleV488';st.textContent=`
#viewshedModule.active:not([${READY_ATTR}="1"]),#viewshedModule.open:not([${READY_ATTR}="1"]){visibility:hidden!important;opacity:0!important}
#viewshedModule[${READY_ATTR}="1"]{transition:opacity .12s ease,box-shadow .12s ease!important}
#viewshedModule .viewshed-head{cursor:move;cursor:grab;user-select:none}
#viewshedModule .viewshed-head:active{cursor:grabbing}
`;d.head.appendChild(st)}
function boot(){S.boots++;installCss();installOwner();bindToolState();const panel=$('viewshedModule');if(panel){observePanel(panel);bindHeader(panel);if(isOpen(panel)){if(!S.desired)establish(panel);else repair(panel)}}}
const api=Object.freeze({version:VERSION,boot,open:()=>ownerToggle(true),close:()=>ownerToggle(false),position:()=>S.desired&&Object.assign({},S.desired),diagnostics:function(){const panel=$('viewshedModule'),tb=toolbarRect(),r=panel&&panel.getBoundingClientRect();return {version:VERSION,active:isOpen(panel),toolActive:S.toolActive,ready:!!(panel&&panel.getAttribute(READY_ATTR)==='1'),userPosition:S.userPosition,desired:S.desired&&Object.assign({},S.desired),panel:r?{left:r.left,top:r.top,right:r.right,bottom:r.bottom,width:r.width,height:r.height}:null,toolbar:tb?{left:tb.left,top:tb.top,right:tb.right,bottom:tb.bottom,width:tb.width,height:tb.height}:null,repairs:S.repairs,opens:S.opens,drags:S.drags,boots:S.boots,ownerInstalls:S.ownerInstalls,toolDeactivations:S.toolDeactivations,toolStateBinds:S.toolStateBinds,observerScope:'viewshedModule-attributes-only',documentWideObserver:false,delayedRepositioning:false,snapBackAfterDrag:false}}});
w.TakMapViewshedWindowV488=api;w.TakMapViewshedWindowV487=api;
if(d.readyState==='loading')d.addEventListener('DOMContentLoaded',()=>setTimeout(boot,120),{once:true});else setTimeout(boot,120);
[500,1200,3000,5500,8500].forEach(ms=>setTimeout(boot,ms));
})(window,document);
