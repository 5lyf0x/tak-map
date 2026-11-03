(function(window,document){
  'use strict';
  const VERSION='i621';
  const PACKAGE='1.4.0-i621';
  const SIZING='i621';
  /* i618 shared content-aware context sizing; horizontal scrolling is intentionally disabled. */
  const SCROLLBAR_GUTTER=14;
  const state={scheduled:false,observer:null,identityObserver:null,resizeObservers:new WeakMap(),fits:0,lastError:'',lastWidths:{}};
  const clamp=(value,min,max)=>Math.max(min,Math.min(max,value));
  const visible=el=>!!(el&&el.isConnected&&!el.classList.contains('hidden')&&!el.classList.contains('collapsed')&&el.getAttribute('aria-hidden')!=='true'&&getComputedStyle(el).display!=='none');
  function injectCss(){
    if(document.getElementById('takMapContextSizingStyleI618'))return;
    const style=document.createElement('style');style.id='takMapContextSizingStyleI618';style.textContent=`
      #takMapContextSidebarI572,.tak-adsb-panel-i610{box-sizing:border-box!important;max-width:calc(100vw - 24px)!important;overflow:hidden!important;scrollbar-gutter:stable!important}
      #takMapContextSidebarI572.gateway-data-nifc-i620{width:292px!important;max-width:min(430px,calc(100vw - 24px))!important}
      #takMapContextSidebarI572{display:flex!important;flex-direction:column!important;position:fixed!important;z-index:2147482000!important}
      #takMapContextSidebarI572 .tak-context-head-i572{flex:0 0 auto!important}
      #takMapContextSidebarBodyI572{flex:1 1 auto!important;min-height:0!important;overflow-y:auto!important;overflow-x:hidden!important;overscroll-behavior:contain!important;scrollbar-gutter:stable!important;scrollbar-width:thin!important;scrollbar-color:#4f7181 #0b161c!important}
      #takMapContextSidebarBodyI572::-webkit-scrollbar,.tak-adsb-panel-body-i610::-webkit-scrollbar{width:12px!important}
      #takMapContextSidebarBodyI572::-webkit-scrollbar-track,.tak-adsb-panel-body-i610::-webkit-scrollbar-track{background:#0b161c!important;border-left:1px solid rgba(72,100,112,.25)!important}
      #takMapContextSidebarBodyI572::-webkit-scrollbar-thumb,.tak-adsb-panel-body-i610::-webkit-scrollbar-thumb{min-height:48px!important;border:3px solid #0b161c!important;border-radius:999px!important;background:linear-gradient(180deg,#5a7d8d,#446474)!important}
      #takMapContextSidebarBodyI572::-webkit-scrollbar-thumb:hover,.tak-adsb-panel-body-i610::-webkit-scrollbar-thumb:hover{background:linear-gradient(180deg,#6f96a7,#5b8295)!important}
      .tak-adsb-panel-i610{scrollbar-gutter:stable!important}
      .tak-adsb-panel-body-i610{overflow-y:auto!important;overflow-x:hidden!important;scrollbar-gutter:stable!important;scrollbar-width:thin!important;scrollbar-color:#4f7181 #0b161c!important}
      #takMapContextSidebarI572 .feature-popup .kvp,#takMapContextSidebarI572 .point-popup-grid-i556,.tak-adsb-panel-i610 .tak-adsb-i610-row{min-width:0!important}
      #takMapContextSidebarI572 .feature-popup .kvp span,#takMapContextSidebarI572 .point-popup-value-i556,.tak-adsb-panel-i610 .tak-adsb-i610-value{min-width:0!important;max-width:100%!important;white-space:normal!important;overflow-wrap:anywhere!important;word-break:normal!important}
      @media(max-width:620px){#takMapContextSidebarI572,.tak-adsb-panel-i610{width:calc(100vw - 24px)!important;max-width:none!important}}
    `;document.head.appendChild(style);
  }
  function mapNode(){return document.getElementById('map')||document.querySelector('.leaflet-container')||document.body}
  function measure(el,value){
    value=String(value==null?'':value).trim();if(!value)return 0;
    const canvas=measure.canvas||(measure.canvas=document.createElement('canvas'));const ctx=canvas.getContext&&canvas.getContext('2d');
    if(!ctx)return Math.min(420,value.length*7);
    const cs=el?getComputedStyle(el):null;ctx.font=cs&&cs.font&&cs.font!=='normal normal normal normal 16px / normal serif'?cs.font:`${cs&&cs.fontWeight||600} ${cs&&cs.fontSize||'12px'} ${cs&&cs.fontFamily||'sans-serif'}`;
    return Math.ceil(ctx.measureText(value).width);
  }
  function longestVisible(selector,panel,cap){
    let best=0;panel.querySelectorAll(selector).forEach(el=>{
      if(!visibleElement(el))return;
      const parts=String(el.textContent||'').split(/\n|;/).map(x=>x.trim()).filter(Boolean);
      for(const part of parts)best=Math.max(best,Math.min(cap,measure(el,part)));
    });return best;
  }
  function visibleElement(el){
    if(!el||!el.isConnected)return false;
    if(el.closest('details:not([open])')&&!el.matches('details:not([open])>summary')&&!el.closest('summary'))return false;
    const cs=getComputedStyle(el);return cs.display!=='none'&&cs.visibility!=='hidden';
  }
  function controlsWidth(panel,cap){
    let best=0;panel.querySelectorAll('button,input,select,textarea,.tak-adsb-i610-grid,.point-popup-actions-i556').forEach(el=>{
      if(!visibleElement(el))return;
      const rect=el.getBoundingClientRect();const natural=Math.max(rect.width||0,el.scrollWidth||0,measure(el,el.textContent||el.value||''));best=Math.max(best,Math.min(cap,natural));
    });return best;
  }
  function mode(panel){return panel.classList.contains('tak-adsb-panel-i610')?'adsb':'context'}
  function isNifc(panel){return !!(panel&&panel.classList.contains('gateway-data-nifc-i620')||panel&&panel.getAttribute('data-gateway-source-key-i620')==='nifc_fire_perimeters')}
  function baseLimits(panel){
    const kind=mode(panel);const narrow=window.matchMedia&&window.matchMedia('(max-width:620px)').matches;
    if(kind==='context'&&isNifc(panel))return {min:narrow?280:292,max:narrow?window.innerWidth-24:430,valueCap:252,nifc:true};
    return kind==='adsb'?{min:narrow?280:344,max:narrow?window.innerWidth-24:462,valueCap:320}:{min:narrow?280:318,max:narrow?window.innerWidth-24:568,valueCap:382};
  }
  function preferred(panel){
    const limits=baseLimits(panel),kind=mode(panel),nifc=!!limits.nifc;
    const labelSel=kind==='adsb'?'.tak-adsb-i610-key':'.kvp b,.point-popup-label-i556,.tak-context-delete-summary-i572 b';
    const valueSel=kind==='adsb'?'.tak-adsb-i610-value,.tak-adsb-i610-name,.tak-adsb-i610-sub,.tak-adsb-i610-chip':'.kvp span,.point-popup-value-i556,.point-popup-title-i556,.point-popup-subtitle-i556,.tak-context-title-i572,.tak-context-kicker-i572';
    const labelCap=nifc?112:138,valueFloor=nifc?76:120;
    const label=clamp(longestVisible(labelSel,panel,labelCap),nifc?64:70,labelCap);
    const value=clamp(longestVisible(valueSel,panel,limits.valueCap),valueFloor,limits.valueCap);
    const headerTitle=longestVisible(kind==='adsb'?'.tak-adsb-i610-name,.tak-adsb-i610-sub':'.tak-context-title-i572,.tak-context-kicker-i572',panel,limits.max-(nifc?64:100));
    const row=label+value+(kind==='adsb'?40:(nifc?34:48))+SCROLLBAR_GUTTER;
    const controls=nifc?0:controlsWidth(panel,limits.max-28)+28+SCROLLBAR_GUTTER;
    const header=headerTitle+(nifc?58:96)+SCROLLBAR_GUTTER;
    return clamp(Math.ceil(Math.max(limits.min,row,controls,header)),limits.min,limits.max);
  }
  function mapRect(){const node=mapNode();try{return node.getBoundingClientRect()}catch(_){return {left:0,right:window.innerWidth,width:window.innerWidth}}}
  function isShown(panel){return visible(panel)}
  function setWidth(panel,width){
    width=Math.max(260,Math.round(width));const prior=Number(panel.dataset.takContextWidthI618||0);if(Math.abs(prior-width)<1)return;
    panel.dataset.takContextWidthI618=String(width);panel.style.setProperty('width',`${width}px`,'important');panel.style.setProperty('--tak-context-scrollbar-gutter-i618',`${SCROLLBAR_GUTTER}px`);state.fits++;state.lastWidths[panel.id||panel.className]=width;
  }
  function observe(panel){
    if(!panel||state.resizeObservers.has(panel)||!window.ResizeObserver)return;
    const ro=new ResizeObserver(()=>schedule());ro.observe(panel);state.resizeObservers.set(panel,ro);
  }
  function fitOne(panel,maxOverride){
    if(!panel||!panel.isConnected)return 0;observe(panel);const limits=baseLimits(panel);const rect=mapRect();let max=Math.min(limits.max,Math.max(260,rect.width-24),Math.max(260,window.innerWidth-24));if(Number.isFinite(maxOverride))max=Math.min(max,maxOverride);const target=Math.min(preferred(panel),max);setWidth(panel,target);return target;
  }
  function shown(sel){return Array.from(document.querySelectorAll(sel)).filter(isShown)}
  function resolvePairs(){
    const rect=mapRect(),gap=24,usable=Math.max(560,rect.width-24);
    const left=document.getElementById('takMapAdsbLeftSidebarI610');
    const right=document.getElementById('takMapAdsbRightSidebarI610');
    const context=document.getElementById('takMapContextSidebarI572');
    const leftOn=isShown(left),rightOn=isShown(right),contextOn=isShown(context);
    const rightPeer=rightOn?right:(contextOn?context:null);
    if(leftOn&&rightPeer){
      const lPref=preferred(left),rPref=preferred(rightPeer);let l=lPref,r=rPref;
      if(l+r+gap>usable){const minL=300,minR=300,room=usable-gap;const share=room/2;l=Math.max(minL,Math.min(lPref,share));r=Math.max(minR,Math.min(rPref,room-l));if(l+r>room){l=Math.max(270,room-r);r=Math.max(270,room-l)}}
      setWidth(left,l);setWidth(rightPeer,r);
    }
    if(rightOn&&contextOn){
      const room=Math.max(280,(usable-gap)/2);setWidth(right,Math.min(preferred(right),room));setWidth(context,Math.min(preferred(context),room));
    }
  }
  function fitAll(){
    try{injectCss();const panels=[document.getElementById('takMapContextSidebarI572'),...document.querySelectorAll('.tak-adsb-panel-i610')].filter(Boolean);panels.forEach(panel=>fitOne(panel));resolvePairs();state.lastError=''}catch(error){state.lastError=String(error&&error.stack||error)}
  }
  function schedule(){if(state.scheduled)return;state.scheduled=true;requestAnimationFrame(()=>{state.scheduled=false;fitAll()})}
  function fixIdentityNode(node){
    if(!node)return;if(node.nodeType===3)node=node.parentElement;if(!node||node.nodeType!==1)return;
    const fix=el=>{if(el.matches('.version-panel .release-main')){if(el.textContent!=='1.4.0')el.textContent='1.4.0';return}if(el.matches('.version-panel .version-product')){if(el.textContent!=='TAK Map')el.textContent='TAK Map';return}if(el.matches('.iteration-chip,.iteration-marker')){if(el.textContent!==VERSION)el.textContent=VERSION;if(el.getAttribute('data-iteration')!==VERSION)el.setAttribute('data-iteration',VERSION);return}if(el.hasAttribute('data-iteration')&&el.getAttribute('data-iteration')!==VERSION)el.setAttribute('data-iteration',VERSION)};
    fix(node);node.querySelectorAll&&node.querySelectorAll('.version-panel .release-main,.version-panel .version-product,.iteration-chip,.iteration-marker,[data-iteration]').forEach(fix);
  }
  function apply(){
    try{document.documentElement.dataset.takMapIteration=VERSION;document.documentElement.dataset.takMapPackage=PACKAGE;fixIdentityNode(document.documentElement)}catch(_){}
  }
  function boot(){
    injectCss();apply();fitAll();
    if(!state.observer&&window.MutationObserver){state.observer=new MutationObserver(records=>{for(const record of records){fixIdentityNode(record.target);record.addedNodes&&record.addedNodes.forEach(fixIdentityNode)}if(records.some(r=>r.type==='childList'||r.type==='characterData'))schedule()});state.observer.observe(document.body,{subtree:true,childList:true,characterData:true})}
    window.addEventListener('resize',schedule,{passive:true});window.addEventListener('orientationchange',()=>setTimeout(schedule,80),{passive:true});
    [100,350,800,1600,3200].forEach(delay=>setTimeout(fitAll,delay));setInterval(fitAll,2500);
  }
  const sizingApi=Object.freeze({version:SIZING,fit:fitOne,fitAll,schedule,preferredWidth:preferred,diagnostics:()=>({version:SIZING,fits:state.fits,lastWidths:Object.assign({},state.lastWidths),scrollbarGutter:SCROLLBAR_GUTTER,nifcContentWidth:true,lastError:state.lastError})});
  window.TakMapContextPanelSizingI620=window.TakMapContextPanelSizingI618=sizingApi;
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
  [0,100,500,1500,3500,6500].forEach(function(delay){setTimeout(()=>{apply();fitAll()},delay)});window.addEventListener('takmap:runtime-ready',()=>{apply();schedule()});
  window.TakMapPackageI620=window.TakMapPackageI618=window.TakMapPackageI617=window.TakMapPackageI616=window.TakMapPackageI615=window.TakMapPackageI614=window.TakMapPackageI613=window.TakMapPackageI612=window.TakMapPackageI607=window.TakMapPackageI602=window.TakMapPackageI599=window.TakMapPackageI592=window.TakMapPackageI591=window.TakMapPackageI590=window.TakMapPackageI589=window.TakMapPackageI585=window.TakMapPackageI583=window.TakMapPackageI581=window.TakMapPackageI580=Object.freeze({version:VERSION,packageVersion:PACKAGE,apply:apply,contextSizing:sizingApi});
})(window,document);
