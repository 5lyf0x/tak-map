/* i684: reorder existing sidebar cards without reconstructing their controls. */
(function(){'use strict';let done=false;
function reorder(){if(done)return true;const side=document.getElementById('sidebar');if(!side)return false;
const satellite=document.getElementById('satelliteTrackingPanelV409')||Array.from(side.querySelectorAll('.panel')).find(el=>/^Satellite Tracking$/i.test(el.querySelector('h2')?.textContent?.trim()||''));
const offline=Array.from(side.querySelectorAll('.panel')).find(el=>/^Offline Maps$/i.test(el.querySelector('h2')?.textContent?.trim()||''));
if(!satellite||!offline||satellite.parentNode!==offline.parentNode)return false;
if(satellite.nextElementSibling!==offline)offline.parentNode.insertBefore(satellite,offline);
done=true;return true;}
function boot(){if(reorder())return;let count=0;const timer=setInterval(()=>{if(reorder()||++count>=100)clearInterval(timer)},150)}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
