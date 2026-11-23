/* TAK Map i696 — real NOAA MRMS historical observations, no synthetic frames. */
(()=>{'use strict';
if(window.TakMapRadarHistoryI696)return;
const D=document,W=window,URL='/api/tak-map/weather/radar/history-i696';
const $=id=>D.getElementById(id);
const h={frames:[],window:60,speed:1,loop:true,mode:'live',playing:false,index:-1,
  catalogPending:false,checked:0,error:'',seq:0,timer:null,lastRequested:'',unavailableMinutes:0};
const weather=()=>W.TakMapNativeWeatherI693;
const live=()=>weather()?.state;
const fmt=s=>{const d=new Date(s);return Number.isFinite(d.getTime())?d.toLocaleTimeString([],{hour:'numeric',minute:'2-digit'}):'—'};
const fmtUtc=s=>s?new Date(s).toISOString().replace('T',' ').replace('.000Z',' UTC'):'';
const frame=()=>h.frames[h.index]||null;
function stop(){h.playing=false;clearTimeout(h.timer);h.timer=null;render()}
function setMode(mode){h.mode=mode;render()}
function mount(){const settings=$('takWeatherRadarSettingsI691');if(!settings)return false;
 if($('takRadarHistoryI696'))return true;
 const panel=D.createElement('div');panel.id='takRadarHistoryI696';panel.className='tak-radar-history-i696';
 panel.innerHTML=`
  <div class="tak-radar-history-head-i696"><b>RADAR HISTORY</b><span id="takRadarHistorySpanI696">1h selected</span></div>
  <div class="tak-radar-history-windows-i696" role="group" aria-label="Radar history window">
   <button type="button" data-radar-window="30">30m</button><button type="button" data-radar-window="60">1h</button><button type="button" data-radar-window="120">2h</button><button type="button" data-radar-window="240">4h</button></div>
  <div class="tak-radar-history-clock-i696"><time id="takRadarStartI696">—</time><span id="takRadarSelectedI696">LIVE</span><time id="takRadarEndI696">—</time></div>
  <input id="takRadarTimelineI696" class="tak-soft-pill-i678" type="range" min="0" max="1" step="1" value="0" style="--tak-soft-pill-pct:0%" disabled aria-label="Radar observation timeline"/>
  <div class="tak-radar-history-controls-i696">
   <button type="button" data-radar-action="first" aria-label="First radar frame" title="First frame">⏮</button>
   <button type="button" data-radar-action="prev" aria-label="Previous radar frame" title="Previous frame">◀</button>
   <button type="button" data-radar-action="play" aria-label="Play historical radar" title="Play radar history">▶</button>
   <button type="button" data-radar-action="next" aria-label="Next radar frame" title="Next frame">▶</button>
   <button type="button" data-radar-action="last" aria-label="Last radar frame" title="Last frame">⏭</button>
   <button type="button" data-radar-action="live" class="tak-radar-live-i696" aria-label="Return to live radar">LIVE</button>
  </div>
  <div class="tak-radar-history-options-i696"><label>Speed<select id="takRadarSpeedI696" aria-label="Radar playback speed"><option value="1">1×</option><option value="2">2×</option><option value="4">4×</option></select></label><label>Loop<input id="takRadarLoopI696" type="checkbox" checked></label></div>
  <small id="takRadarHistoryStatusI696" class="tak-radar-history-status-i696" role="status">Checking historical radar…</small>`;
 const status=$('takWeatherRadarStatusI691');if(status)status.insertAdjacentElement('afterend',panel);else settings.appendChild(panel);
 panel.addEventListener('click',event=>{
  const win=event.target.closest('button[data-radar-window]');if(win){stop();h.window=Number(win.dataset.radarWindow);refresh(true);return}
  const action=event.target.closest('button[data-radar-action]')?.dataset.radarAction;
  if(!action)return;
  if(action==='live'){toLive();return}
  if(action==='play'){if(h.playing)stop();else play();return}
  if(!h.frames.length)return;
  stop();if(action==='first')choose(0);else if(action==='last')choose(h.frames.length-1);
  else if(action==='prev')choose(Math.max(0,(h.index<0?h.frames.length-1:h.index)-1));
  else if(action==='next')choose(Math.min(h.frames.length-1,h.index+1));
 });
 $('takRadarTimelineI696').addEventListener('input',event=>{const target=Number(event.target.value);stop();choose(target)});
 $('takRadarSpeedI696').addEventListener('change',event=>{h.speed=[1,2,4].includes(Number(event.target.value))?Number(event.target.value):1;render()});
 $('takRadarLoopI696').addEventListener('change',event=>{h.loop=!!event.target.checked;render()});
 render();return true
}
function render(){const panel=$('takRadarHistoryI696');if(!panel)return;
 const s=live(),available=h.frames.length>=3;
 const enabled=!!s?.radar;
 panel.hidden=!enabled;
 if(!enabled)return;
 for(const b of panel.querySelectorAll('[data-radar-window]')){b.classList.toggle('active',Number(b.dataset.radarWindow)===h.window);b.setAttribute('aria-pressed',String(Number(b.dataset.radarWindow)===h.window))}
 const start=h.frames[0],end=h.frames[h.frames.length-1],selected=frame();
 $('takRadarStartI696').textContent=fmt(start?.valid_time_utc);
 $('takRadarEndI696').textContent=fmt(end?.valid_time_utc);
 $('takRadarSelectedI696').textContent=h.mode==='history'&&selected?fmt(selected.valid_time_utc):'LIVE';
 $('takRadarSelectedI696').title=h.mode==='history'&&selected?fmtUtc(selected.valid_time_utc):'Latest verified radar';
 $('takRadarHistorySpanI696').textContent=h.unavailableMinutes?h.unavailableMinutes+'m available':'No history';
 const timeline=$('takRadarTimelineI696');timeline.disabled=!available;
 const maxIndex=Math.max(1,h.frames.length-1),index=Math.max(0,h.mode==='history'?h.index:h.frames.length-1);
 timeline.max=String(maxIndex);timeline.value=String(index);
 timeline.style.setProperty('--tak-soft-pill-pct',((index/maxIndex)*100).toFixed(2)+'%');
 timeline.setAttribute('aria-valuetext',h.mode==='history'&&selected?fmt(selected.valid_time_utc):'LIVE');
 const play=panel.querySelector('[data-radar-action="play"]');play.textContent=h.playing?'❚❚':'▶';play.setAttribute('aria-label',h.playing?'Pause radar history':'Play historical radar');
 for(const b of panel.querySelectorAll('button[data-radar-action]')){if(b.dataset.radarAction!=='live')b.disabled=!available;b.classList.toggle('active',b.dataset.radarAction==='live'&&h.mode==='live')}
 $('takRadarSpeedI696').value=String(h.speed);$('takRadarLoopI696').checked=h.loop;
 const status=$('takRadarHistoryStatusI696');
 let message=h.error?'LIVE ONLY · '+h.error:(!available?'LIVE ONLY · fewer than three observed frames':
  h.catalogPending?'Updating observations…':h.mode==='live'?`${h.frames.length} observations · ready for playback`:
  `History ${Math.max(0,h.index+1)}/${h.frames.length} · ${h.playing?'playing':'paused'}`);
 if(h.mode==='history'&&selected){
  const ready=weather()?.historyReady?.(selected.frame_id);
  message=(!ready?'Buffering history · previous radar retained · ':'')+message;
 }
 status.textContent=message;
}
async function refresh(force=false){const s=live();if(!s?.radar||h.catalogPending)return;
 if(!force&&Date.now()-h.checked<75000)return;
 h.catalogPending=true;h.checked=Date.now();h.seq++;const seq=h.seq;render();
 try{const ctl=new AbortController();const timer=setTimeout(()=>ctl.abort(),18000);
  let response;try{response=await fetch(URL+'?window='+h.window,{credentials:'same-origin',cache:'no-store',signal:ctl.signal})}finally{clearTimeout(timer)}
  if(!response.ok)throw Error('HTTP '+response.status);
  const data=await response.json();if(seq!==h.seq)return;
  if(!data.ok||!Array.isArray(data.frames))throw Error('Malformed radar history');
  const frames=data.frames.filter(f=>f&&/^h\d{13}_[a-f0-9]{16}$/.test(f.frame_id)&&Number.isFinite(Date.parse(f.valid_time_utc)));
  frames.sort((a,b)=>Date.parse(a.valid_time_utc)-Date.parse(b.valid_time_utc));
  const current=frame()?.frame_id;
  h.frames=frames.slice(-48);h.unavailableMinutes=data.window_available_minutes||0;h.error='';
  if(h.frames.length<3||data.historical_supported===false)h.error='history unavailable';
  if(h.mode==='history'){
   const index=h.frames.findIndex(f=>f.frame_id===current);
   if(index<0){stop();h.error='selected frame expired · select LIVE';}
   else h.index=index;
  }
 }catch(error){if(seq!==h.seq)return;h.error=String(error.message||error).slice(0,110)}
 finally{if(seq===h.seq){h.catalogPending=false;render()}}
}
function choose(index){const s=live();if(!s?.radar||!h.frames.length)return false;
 const i=Math.round(Number(index));if(!Number.isInteger(i)||i<0||i>=h.frames.length)return false;
 const f=h.frames[i];if(!weather()?.selectHistory?.(f))return false;
 h.index=i;h.mode='history';h.lastRequested=f.frame_id;render();return true;
}
async function play(){if(!live()?.radar)return;
 if(h.frames.length<3){await refresh(true);if(h.frames.length<3)return}
 if(!choose(h.mode==='history'&&h.index>=0?h.index:0))return;
 h.playing=true;queue();render();
}
function queue(){clearTimeout(h.timer);if(!h.playing)return;
 const f=frame();if(!f){stop();return}
 // A partially downloaded historical viewport is NEVER promoted by the player.
 // The existing weather renderer keeps the last-good image under its candidate.
 const ready=weather()?.historyReady?.(f.frame_id);
 if(!ready){h.timer=setTimeout(queue,650);render();return}
 h.timer=setTimeout(()=>{
  if(!h.playing||!live()?.radar)return stop();
  if(D.visibilityState==='hidden'||!isExpanded()){stop();return}
  const next=h.index+1;
  if(next>=h.frames.length){if(!h.loop){stop();return}choose(0)}else choose(next);
  queue();
 },Math.max(350,1200/h.speed));render();
}
function toLive(){stop();h.mode='live';h.index=-1;h.error='';weather()?.leaveHistory?.();render()}
function isExpanded(){const panel=$('takNativeWeatherI691');return !!panel&&!panel.querySelector('.tak-weather-body-i691')?.hidden}
function tick(){if(!mount())return;const s=live();if(!s?.radar){if(h.playing)stop();render();return}
 if(!isExpanded()&&h.playing)stop();
 if(!h.catalogPending&&Date.now()-h.checked>75000)refresh();
 render();
}
D.addEventListener('visibilitychange',()=>{if(D.visibilityState==='hidden')stop()});
W.TakMapRadarHistoryI696={state:h,refresh,choose,play,stop,toLive};
if(D.readyState==='loading')D.addEventListener('DOMContentLoaded',tick,{once:true});else tick();
setInterval(tick,1800);
})();
