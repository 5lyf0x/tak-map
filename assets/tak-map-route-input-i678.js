/* i678 Route Creation: map-object click isolation without modifying saved objects. */
(function(W,D){'use strict';
let map=null;
function active(){const b=D.getElementById('toolRoute');return !!(b?.classList.contains('active')||(W.activeMapTool==='route'))}
function routeHandle(target){return !!target.closest?.('.tak-route-point-i654,.tak-route-hit-i678,.tak-route-distance-icon-i658,.tak-route-failure-i654')}
function unrelatedMapObject(target){return !!target.closest?.('.leaflet-interactive,.leaflet-marker-icon,.leaflet-marker-shadow,.leaflet-tooltip,.leaflet-popup,.leaflet-overlay-pane canvas')}
function capture(e){if(!active()||e.button!==0||!unrelatedMapObject(e.target)||routeHandle(e.target))return;
 const container=map?.getContainer?.();if(!container)return;const bounds=container.getBoundingClientRect();if(e.clientX<bounds.left||e.clientX>=bounds.right||e.clientY<bounds.top||e.clientY>=bounds.bottom)return;
 // Route click is consumed at capture phase, before NWS/marker Leaflet listeners.
 // No synthetic map click is dispatched, avoiding duplicate waypoint creation.
 e.preventDefault();e.stopImmediatePropagation();const p=map.mouseEventToContainerPoint(e),ll=map.containerPointToLatLng(p);
 try{if(typeof W.v233RouteMapClick==='function')W.v233RouteMapClick(ll)}catch(err){console.warn('Route waypoint input failed',err)}
}
function routeStatus(){if(!map)return;const on=active();const c=map.getContainer();c.classList.toggle('tak-route-exclusive-i678',on);if(on){try{map.closePopup()}catch(_){}}}
function init(){map=W.map||W.takLeafletMap;if(!map?.getContainer||!D.getElementById('toolRoute'))return false;const c=map.getContainer();if(c.dataset.routeExclusiveI678)return true;c.dataset.routeExclusiveI678='1';c.addEventListener('click',capture,true);
 // Delegated map toolbar changes are observed without polling the DOM.
 const btn=D.getElementById('toolRoute');const observer=new MutationObserver(routeStatus);observer.observe(btn,{attributes:true,attributeFilter:['class']});
 const prior=W.setActiveMapTool;if(typeof prior==='function')W.setActiveMapTool=function(...args){const result=prior.apply(this,args);queueMicrotask(routeStatus);return result};
 const priorToggle=W.toggleMapTool;if(typeof priorToggle==='function')W.toggleMapTool=function(...args){const result=priorToggle.apply(this,args);queueMicrotask(routeStatus);return result};
 routeStatus();return true}
const style=D.createElement('style');style.id='takRouteExclusiveI678';style.textContent='.tak-route-exclusive-i678 .leaflet-popup,.tak-route-exclusive-i678 .leaflet-tooltip{pointer-events:none!important}';D.head.appendChild(style);
let tries=0;const t=setInterval(()=>{if(init()||++tries>120)clearInterval(t)},200);
W.TakMapRouteInputI678={active,capture,init};
})(window,document);
