/* TAK Map i676 — draggable Tactical HUD routing selector; per-browser persistence.
 * i675 API and DOM ids retained for backward-compatible package activation. */
(function(W,D){'use strict';
const ID='takRouteDataI675', endpoint='/api/tak-map/routing/datasets-i675';
const S={open:false,visible:false,fetching:false,activating:false,activeId:'',datasets:[],lastCheck:0,job:null,error:'',lastReadyId:''};
const POSITION_KEY='tak-map.routing-data.position.i676';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const el=id=>D.getElementById(id);
function routeActive(){try{return W.activeMapTool==='route'||(typeof activeMapTool!=='undefined'&&activeMapTool==='route')||!!el('toolRoute')?.classList.contains('active')||!!el('routeMiniToolbar')?.classList.contains('active')}catch(_){return false}}
function currentRouteIsDirty(){const state=W.takRouteEditorI654,legacy=W.v233RouteState;
  return Boolean((legacy?.points?.length||0)>0||state?.editing||state?.saveBusy||state?.operationBusy)}
function current(){return S.datasets.find(x=>x.active)||S.datasets.find(x=>x.dataset_id===S.activeId)}
function notify(message){const bar=el('takRouteDataMessageI675');if(!bar)return;bar.textContent=message;bar.hidden=!message}
function mapBounds(){return el('map')?.getBoundingClientRect()||null}
function clamp(n,min,max){return Math.max(min,Math.min(max,n))}
function storedPosition(){try{const p=JSON.parse(W.localStorage.getItem(POSITION_KEY)||'null');
  return p&&Number.isFinite(p.right)&&Number.isFinite(p.top)?p:null}catch(_){return null}}
function position(reset=false){const host=el(ID),r=mapBounds();if(!host||!r)return;
  if(r.width<175||r.height<65){host.hidden=true;return}
  if(reset){try{W.localStorage.removeItem(POSITION_KEY)}catch(_){}}
  if(S.dragging)return;
  const width=155,height=25,margin=7;
  const saved=storedPosition();
  // A conservative default: below the zoom badge, above the right tool strip.
  const right=saved?saved.right:29,top=saved?saved.top:50;
  const x=clamp(r.right-right-width,r.left+margin,r.right-width-margin);
  const y=clamp(r.top+top,r.top+margin,r.bottom-height-margin);
  host.style.left=x+'px';host.style.top=y+'px';host.style.right='auto';
  positionMenu();
}
function positionMenu(){const host=el(ID),r=mapBounds();if(!host||!r)return;
  const bounds=host.getBoundingClientRect();
  for(const menu of [el('takRouteDataMenuI675'),el('takRouteDataMessageI675')]){
    if(!menu)continue;
    const width=menu.id==='takRouteDataMenuI675'?284:250;
    const roomLeft=bounds.right-r.left;
    menu.style.left=roomLeft>=width+7?'auto':'0';
    menu.style.right=roomLeft>=width+7?'0':'auto';
    const below=r.bottom-(bounds.bottom+5);
    menu.style.top=below<145?'auto':'29px';menu.style.bottom=below<145?'29px':'auto';
  }
}
function setAbsolute(x,y){const r=mapBounds(),host=el(ID);if(!r||!host)return;
  host.style.left=clamp(x,r.left+7,r.right-162)+'px';
  host.style.top=clamp(y,r.top+7,r.bottom-32)+'px';
  host.style.right='auto';positionMenu();
}
function persistPosition(){const r=mapBounds(),host=el(ID);if(!r||!host)return;
  const b=host.getBoundingClientRect();
  try{W.localStorage.setItem(POSITION_KEY,JSON.stringify({right:Math.round(r.right-b.right),top:Math.round(b.top-r.top)}))}catch(_){}}
function bindDrag(grip,host){let gesture=null;
  grip.addEventListener('pointerdown',event=>{
    if(event.button!==0&&event.pointerType!=='touch')return;
    event.preventDefault();event.stopPropagation();S.open=false;render();
    const rect=host.getBoundingClientRect();
    gesture={id:event.pointerId,startX:event.clientX,startY:event.clientY,left:rect.left,top:rect.top};
    S.dragging=true;try{grip.setPointerCapture(event.pointerId)}catch(_){}
  });
  grip.addEventListener('pointermove',event=>{if(!gesture||gesture.id!==event.pointerId)return;
    event.preventDefault();event.stopPropagation();setAbsolute(gesture.left+event.clientX-gesture.startX,gesture.top+event.clientY-gesture.startY)});
  const finish=event=>{if(!gesture||gesture.id!==event.pointerId)return;
    event.preventDefault();event.stopPropagation();gesture=null;S.dragging=false;
    try{grip.releasePointerCapture(event.pointerId)}catch(_){}persistPosition();position()};
  grip.addEventListener('pointerup',finish);grip.addEventListener('pointercancel',finish);
  grip.addEventListener('keydown',event=>{const move={ArrowLeft:[-10,0],ArrowRight:[10,0],ArrowUp:[0,-10],ArrowDown:[0,10]}[event.key];
    if(!move)return;event.preventDefault();event.stopPropagation();
    const b=host.getBoundingClientRect();setAbsolute(b.left+move[0],b.top+move[1]);persistPosition()});
}

function render(){const host=el(ID),button=el('takRouteDataButtonI675'),value=el('takRouteDataValueI675'),menu=el('takRouteDataMenuI675');if(!host||!button||!menu)return;
  const info=current(),busy=S.activating||['preparing','restarting'].includes(S.job?.status);
  S.activating=busy;host.classList.toggle('busy',busy);
  value.textContent=busy?'SWITCHING':(info?.label||'NO GRAPH');
  button.title=busy?'Switching routing graph':('Routing Data: '+(info?.label||'none')+' — select package');
  button.setAttribute('aria-expanded',String(S.open));button.disabled=busy;
  menu.hidden=!S.open;
  const rows=S.datasets.map(data=>{
    const opt=D.createElement('button');opt.type='button';opt.className='tak-route-data-option-i675';
    opt.setAttribute('role','option');opt.setAttribute('aria-selected',String(data.active));
    const name=D.createElement('span');name.className='tak-route-data-name-i675';name.textContent=data.label;
    const status=D.createElement('span');status.className='tak-route-data-state-i675';status.textContent=data.active?'ACTIVE':'READY';
    opt.append(name,status);opt.disabled=busy||data.active;
    opt.addEventListener('click',event=>{event.stopPropagation();void choose(data.dataset_id)});
    return opt;
  });
  menu.replaceChildren();const header=D.createElement('div');header.className='tak-route-data-head-i675';header.textContent='AVAILABLE ROUTING PACKAGES';menu.append(header,...rows);
  if(!rows.length){const note=D.createElement('div');note.className='tak-route-data-none-i675';note.textContent='No installed routing packages. Register them in NDM Data.';menu.append(note)}
  if(S.error){const note=D.createElement('div');note.className='tak-route-data-error-i675';note.textContent=S.error;menu.append(note)}
  if(busy){const note=D.createElement('div');note.className='tak-route-data-working-i675';note.textContent=S.job?.status==='preparing'?'Verifying and preparing graph…':'Restarting local Valhalla…';menu.append(note)}
  const reset=D.createElement('button');reset.type='button';reset.className='tak-route-data-reset-i676';reset.textContent='Reset Position';
  reset.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();S.open=false;position(true);render()});
  menu.append(reset);positionMenu();
}
async function refresh(force=false){if(S.fetching||(!force&&Date.now()-S.lastCheck<(S.activating?1600:9000)))return;
  S.fetching=true;S.lastCheck=Date.now();
  try{const response=await fetch(endpoint,{credentials:'same-origin',cache:'no-store'});
    const body=await response.json();if(!response.ok||!body?.ok)throw Error(body?.error||'Routing catalog unavailable');
    S.datasets=Array.isArray(body.datasets)?body.datasets.filter(x=>/^[0-9a-f]{64}$/.test(String(x.dataset_id||''))):[];
    S.activeId=String(body.active_dataset_id||'');S.job=body.switch||{};
    if(S.job.status==='error'){S.error=S.job.error||'Routing graph switch failed';notify(S.error)}
    else if(S.activating&&S.job.status==='ready'){
      S.error='';notify('Routing graph ready: '+(current()?.label||'selected package'));
      try{if(typeof W.TakMapMvumI673?.state?.tileCache?.clear==='function')W.TakMapMvumI673.state.tileCache.clear()}catch(_){}
      try{if(W.takRouteEditorI654){W.takRouteEditorI654.lastRouterCheck=0;W.takRouteEditorI654.routerReady=true}}catch(_){}
    } else if(S.activating&&['preparing','restarting'].includes(S.job.status)){
      notify(S.job.status==='preparing'?'Verifying routing package…':'Activating routing package…')
    }
    S.activating=['preparing','restarting'].includes(S.job.status);
  }catch(error){S.error=String(error.message||error).slice(0,200);notify(S.error)}
  finally{S.fetching=false;render()}
}
async function choose(datasetId){if(S.activating||S.fetching)return;
  if(currentRouteIsDirty()){S.open=true;S.error='Finish or clear the current route before switching routing graphs.';render();notify(S.error);return}
  const target=S.datasets.find(x=>x.dataset_id===datasetId&&!x.active);if(!target)return;
  S.open=false;S.error='';S.activating=true;S.job={status:'preparing',dataset_id:datasetId};render();notify('Verifying '+target.label+' graph…');
  try{const response=await fetch('/api/tak-map/routing/activate-i675',{
      method:'POST',credentials:'same-origin',cache:'no-store',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({dataset_id:datasetId})});
    const body=await response.json();if(!response.ok||!body?.ok)throw Error(body?.error||'Graph activation failed');
    if(body.already_active){S.activating=false;S.job={status:'ready',dataset_id:datasetId};notify('Graph already active');}
  }catch(error){S.error=String(error.message||error).slice(0,200);S.activating=false;S.job={status:'error',error:S.error};S.open=true;notify(S.error)}
  render();void refresh(true);
}
function visibility(){const host=el(ID);if(!host)return;const on=routeActive();host.hidden=!on;host.style.display=on?'flex':'none';
  if(on!==S.visible){S.visible=on;if(on){position();void refresh(true)}else{S.open=false;notify('');render()}}
  if(on)position();}
function install(){if(el(ID)||!el('map'))return Boolean(el(ID));
  const host=D.createElement('section');host.id=ID;host.className='tak-route-data-hud-i675';host.hidden=true;
  host.innerHTML='<button id="takRouteDataGripI676" class="tak-route-data-grip-i676" type="button" title="Drag routing selector" aria-label="Drag routing selector">⠿</button>'+
    '<button id="takRouteDataButtonI675" type="button" aria-label="Routing Data" aria-haspopup="listbox" aria-expanded="false">'+
    '<span class="tak-route-data-prefix-i675">DATA</span><strong id="takRouteDataValueI675">GRAPH</strong>'+
    '<span class="tak-route-data-chevron-i675" aria-hidden="true">⌄</span></button>'+
    '<div id="takRouteDataMenuI675" role="listbox" aria-label="Available routing packages" hidden></div>'+
    '<div id="takRouteDataMessageI675" role="status" aria-live="polite" hidden></div>';
  D.body.append(host);
  const button=el('takRouteDataButtonI675');button.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();S.open=!S.open;S.error='';render();if(S.open)void refresh(true)});
  bindDrag(el('takRouteDataGripI676'),host);
  host.addEventListener('pointerdown',e=>e.stopPropagation());host.addEventListener('click',e=>e.stopPropagation());
  D.addEventListener('pointerdown',e=>{if(S.open&&!host.contains(e.target)){S.open=false;render()}},true);
  D.addEventListener('keydown',e=>{if(e.key==='Escape'&&S.open){S.open=false;render();button.focus()}});
  W.addEventListener('resize',position);
  render();visibility();return true;
}
const css=D.createElement('style');css.id='takRouteDataStyleI675';css.textContent=`
#${ID}{position:fixed;z-index:4100;display:flex;width:155px;height:25px;max-width:155px;box-sizing:border-box;color:#e8f7ff;font-family:Manrope,Inter,system-ui,sans-serif;pointer-events:auto}
#${ID}[hidden],#${ID} [hidden]{display:none!important}
#${ID} #takRouteDataButtonI675{box-sizing:border-box!important;display:flex!important;align-items:center!important;width:137px!important;max-width:137px!important;height:25px!important;min-height:25px!important;padding:0 8px!important;margin:0!important;gap:6px!important;border:1px solid #65a9bb!important;border-radius:1px!important;background:linear-gradient(155deg,#091520fa,#153346f8)!important;color:#e5f6ff!important;clip-path:polygon(0 0,calc(100% - 7px) 0,100% 7px,100% 100%,7px 100%,0 calc(100% - 7px));font-size:11px!important;cursor:pointer!important;text-align:left!important;overflow:hidden!important;line-height:1!important;box-shadow:none!important}
#${ID} .tak-route-data-prefix-i675{font-size:8px!important;color:#9dd2e7!important;font-family:monospace;letter-spacing:.07em;font-weight:800;flex:none}
#${ID} #takRouteDataValueI675{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-family:monospace;font-size:11px;font-weight:800;color:#f1fbff}
#${ID} .tak-route-data-chevron-i675{margin-left:auto;font-size:15px;color:#abe6ff;flex:none;transform:translateY(-2px)}
#${ID}.busy #takRouteDataValueI675{color:#fbd08d;font-size:9px}
#${ID} .tak-route-data-grip-i676{box-sizing:border-box!important;width:18px!important;min-width:18px!important;max-width:18px!important;height:25px!important;min-height:25px!important;margin:0!important;padding:0!important;border:1px solid #65a9bb!important;border-right:0!important;background:#173043!important;color:#a5d2e4!important;font:900 12px monospace!important;touch-action:none;cursor:grab!important;user-select:none}
#${ID} .tak-route-data-grip-i676:active{cursor:grabbing!important}
#${ID} .tak-route-data-grip-i676:focus-visible{outline:2px solid #e4f5ff!important;outline-offset:2px}
#${ID} .tak-route-data-reset-i676{width:100%;min-height:27px;background:#142e3c!important;border:1px solid #3e667b!important;color:#c3d9e6!important;font:700 10px monospace!important;text-align:left;padding:6px 9px!important;cursor:pointer!important}
#${ID} .tak-route-data-reset-i676:hover{background:#28516a!important} 
#${ID} #takRouteDataMenuI675{box-sizing:border-box;position:absolute;top:29px;right:0;width:min(284px,calc(100vw - 25px));max-height:min(350px,60vh);overflow:auto;background:#0b1c28f7;color:#e9f6fd;border:1px solid #5a9eb4;box-shadow:0 14px 32px #02080ecc;padding:6px;z-index:5000}
#${ID} .tak-route-data-head-i675{font:800 9px monospace;letter-spacing:.07em;color:#a3d0df;padding:7px 8px}
#${ID} .tak-route-data-option-i675{width:100%;display:flex!important;align-items:center;justify-content:space-between;gap:8px;border:0!important;background:transparent!important;color:#eef7ff!important;padding:9px!important;min-height:33px!important;cursor:pointer!important;text-align:left!important;font-size:12px!important;border-radius:2px!important}
#${ID} .tak-route-data-option-i675:hover:not(:disabled),#${ID} .tak-route-data-option-i675:focus-visible{background:#254358!important;outline:1px solid #6aaac4!important}
#${ID} .tak-route-data-option-i675:disabled{cursor:default!important;opacity:.83}
#${ID} .tak-route-data-name-i675{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#${ID} .tak-route-data-state-i675{color:#8ed6d4;font:800 9px monospace;border:1px solid #3e7280;padding:3px 5px;flex:none}
#${ID} .tak-route-data-error-i675{padding:8px;color:#ffb29e;font-size:11px;line-height:1.4}
#${ID} .tak-route-data-working-i675,#${ID} .tak-route-data-none-i675{padding:8px;color:#d0e0ea;font-size:11px;line-height:1.4}
#${ID} #takRouteDataMessageI675{position:absolute;right:0;top:29px;width:250px;max-width:calc(100vw - 45px);border:1px solid #58788c;background:#132938ef;padding:7px 9px;font-size:10px;color:#cae4ee;box-shadow:0 4px 15px #0007}
#${ID} #takRouteDataMenuI675:not([hidden])~#takRouteDataMessageI675{display:none!important}
@media(max-width:450px){#${ID} #takRouteDataMenuI675{width:min(250px,calc(100vw - 25px))}}
`;
D.head.append(css);
W.TakMapRoutingDataI675={state:S,refresh,choose,install,position,routeActive,currentDatasetId:()=>S.activeId};
let tries=0;const retry=setInterval(()=>{if(install()||++tries>130)clearInterval(retry)},250);
setInterval(()=>{if(!el(ID))return;visibility();if(S.visible)void refresh()},500);
})(window,document);

/* i675 sidebar and Soft Pill basemap presentation corrections. Existing
   Geofences/Mesh collapse handlers and independent toggles are left intact. */
(function(D){'use strict';
const style=D.createElement('style');style.id='takMapSidebarAndSoftPillI675';style.textContent=`
/* Collapsed cards align with the established Geofences header. */
#sidebar #tokenMeshCardI660,#sidebar #geofencePanelV491{border-radius:13px!important;margin-bottom:8px!important}
#sidebar #tokenMeshCardI660 .ms-header{min-height:50px!important;padding:8px 10px 8px 12px!important;gap:6px!important;background:var(--panel,#101923)!important}
#sidebar #tokenMeshCardI660.collapsed .ms-header{border-bottom:0!important}
#sidebar #tokenMeshCardI660 .ms-title{font-family:Manrope,system-ui,sans-serif!important;font-size:12px!important;font-weight:800!important;letter-spacing:.06em!important;line-height:1.25!important}
#sidebar #tokenMeshCardI660 .ms-chip{padding:0 7px!important;font-size:10px!important;line-height:1!important;height:23px!important;min-height:23px!important;border-radius:999px!important}
#sidebar #tokenMeshCardI660 .ms-chip::before{display:none!important;content:none!important}
#sidebar #tokenMeshCardI660 .ms-chip.none{color:#adbfc8!important;border-color:#586d7a!important;background:#233440!important}
#sidebar #tokenMeshCardI660 .ms-chip.offline{color:#ffd19a!important;border-color:#8c6a37!important;background:#3c2c18!important}
#sidebar #tokenMeshCardI660 .ms-chip.online{color:#8ce0b8!important;border-color:#31845d!important;background:#133b2a!important}
#sidebar #tokenMeshCardI660 .ms-switch{width:38px!important;height:21px!important;padding:1px!important}
#sidebar #tokenMeshCardI660 .ms-switch .ms-knob{width:17px!important;height:17px!important;transform:translateX(16px)!important}
#sidebar #tokenMeshCardI660 .ms-switch[aria-checked="false"] .ms-knob{transform:translateX(0)!important}
#sidebar #tokenMeshCardI660 .ms-collapse{width:18px!important;height:23px!important;color:#b8c3cb!important}
#sidebar .panel.collapsible.collapsed:not(#tokenMeshCardI660):not(#geofencePanelV491){padding:0!important;overflow:hidden!important;border-radius:9px!important}
#sidebar .panel.collapsible.collapsed:not(#tokenMeshCardI660):not(#geofencePanelV491)>h2{min-height:42px!important;display:flex!important;align-items:center!important;margin:0!important;padding:7px 10px 7px 9px!important;gap:6px!important;font-size:12px!important;font-family:Manrope,system-ui,sans-serif!important;font-weight:800!important;letter-spacing:.06em!important;line-height:1.25!important}
`;
D.head.append(style);
})(document);
