(function(){
  'use strict';
  const V='i610';
  const ID='TakMapAdsbSidebarI610';
  if(window[ID]&&window[ID].initialized)return;

  const state={
    initialized:false,leftId:'',rightId:'',pinned:false,followId:'',trackingIds:new Set(),trails:new Map(),
    markerBindings:0,leftOpens:0,rightOpens:0,drawPasses:0,lastError:'',timer:0,
    drawBase:null,drawWrapper:null,focusBase:null,focusWrapper:null,statusById:new Map(),
    panels:null,backgroundWorker:null,backgroundWorkerUrl:'',backgroundTicks:0,backgroundSamples:0,
    motionTargets:new Map(),latestPositions:new Map(),lastMotionSignature:'',lastVisibility:document.visibilityState||'visible',
    typeChanges:0,rotorOverrides:0,iconChanges:0,outsideBound:false,resizeBound:false
  };

  const BG_SOURCE=`'use strict';
  const motions=new Map();let tracking=new Set();let timer=0;
  function num(v){v=Number(v);return Number.isFinite(v)?v:null}
  function hdelta(a,b){let x=b-a;while(x>180)x-=360;while(x<-180)x+=360;return x}
  function ldelta(a,b){let x=b-a;while(x>180)x-=360;while(x<-180)x+=360;return x}
  function pose(m,now){if(!m)return null;const dur=Math.max(0,Number(m.duration)||0),p=!dur?1:Math.max(0,Math.min(1,(now-Number(m.startAt||0))/dur));const lat=Number(m.startLat)+(Number(m.targetLat)-Number(m.startLat))*p;const lon=Number(m.startLon)+ldelta(Number(m.startLon),Number(m.targetLon))*p;let heading=null;if(Number.isFinite(m.startHeading)&&Number.isFinite(m.targetHeading))heading=m.startHeading+hdelta(m.startHeading,m.targetHeading)*p;else if(Number.isFinite(m.targetHeading))heading=m.targetHeading;else if(Number.isFinite(m.startHeading))heading=m.startHeading;return {id:m.id,lat,lon,heading,alt_ft:m.alt_ft,time:now,complete:p>=1}}
  function tick(){const now=Date.now(),positions=[],samples=[];for(const m of motions.values()){const p=pose(m,now);if(!p)continue;positions.push(p);if(tracking.has(m.id))samples.push(p)}postMessage({type:'tick',now,positions,samples})}
  function start(){if(timer)return;timer=setInterval(tick,1000);tick()}
  onmessage=function(ev){const msg=ev.data||{};if(msg.type==='motion'){const now=Date.now();for(const x of msg.entries||[]){if(!x||!x.id)continue;const old=motions.get(x.id),cur=old?pose(old,now):null;motions.set(x.id,{id:x.id,startLat:cur?cur.lat:Number(x.startLat),startLon:cur?cur.lon:Number(x.startLon),targetLat:Number(x.targetLat),targetLon:Number(x.targetLon),startHeading:cur&&Number.isFinite(cur.heading)?cur.heading:num(x.startHeading),targetHeading:num(x.targetHeading),startAt:now,duration:Math.max(0,Number(x.duration)||0),alt_ft:num(x.alt_ft)})}const hasActive=Array.isArray(msg.activeIds),active=new Set(msg.activeIds||[]);for(const id of Array.from(motions.keys()))if(hasActive&&!active.has(id))motions.delete(id);start();return}if(msg.type==='tracking'){tracking=new Set(msg.ids||[]);start();return}if(msg.type==='clear'){motions.delete(msg.id);return}if(msg.type==='snapshot'){tick();return}if(msg.type==='stop'){if(timer)clearInterval(timer);timer=0;motions.clear();tracking.clear();close()}};
  start();`;

  function text(v){return String(v==null?'':v).trim()}
  function num(v){v=Number(v);return Number.isFinite(v)?v:null}
  function esc(v){return text(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
  function idOf(a){return text(a&&(a.id||a.hex||a.icao||a.icao24||a.uid||a.registration||a.tail||a.callsign||a.flight)).toLowerCase()}
  function isReplay(){try{if(document.body&&document.body.classList.contains('replay-mode-v415'))return true}catch(_){}try{const t=document.getElementById('replayModeToggleV415');if(t&&t.checked)return true}catch(_){}return false}
  function mapObj(){for(const candidate of [window.takLeafletMap,window.map])if(candidate&&typeof candidate.panTo==='function')return candidate;try{if(typeof map!=='undefined'&&map&&typeof map.panTo==='function')return map}catch(_){}return null}
  function mapNode(){const m=mapObj();try{if(m&&m.getContainer)return m.getContainer()}catch(_){}return document.getElementById('map')||document.querySelector('.leaflet-container')}
  function ctl(){return window.TakMapControllers&&window.TakMapControllers.adsb||null}

  const externalAircraftI669=new Map();

  function markerEntries(){
    const out=[],seen=new Set(),c=ctl();
    if(c&&c.markers instanceof Map)for(const [id,marker] of c.markers)if(marker&&!seen.has(marker)){seen.add(marker);out.push([text(id).toLowerCase(),marker])}
    for(const key of ['v320AircraftLayersById','v309AircraftLayersById','v303AircraftLayersById','v298AircraftLayersById','v240AircraftLayersById','v238AircraftLayersById','v236AircraftLayersById']){
      const obj=window[key];if(!obj||typeof obj!=='object')continue;
      for(const [id,marker] of Object.entries(obj))if(marker&&!seen.has(marker)){seen.add(marker);out.push([text(id).toLowerCase(),marker])}
    }
    return out;
  }
  function markerFor(id){id=text(id).toLowerCase();if(externalAircraftI669.has(id))return externalAircraftI669.get(id).marker||null;for(const [key,marker] of markerEntries())if(key===id||idOf(marker&&marker._takAdsbAircraft)===id)return marker;return null}
  function rowFor(id,marker){id=text(id).toLowerCase();if(externalAircraftI669.has(id))return externalAircraftI669.get(id).row;const c=ctl();let row=null;try{row=c&&c.data&&c.data.get&&c.data.get(id)}catch(_){}if(!row&&marker)row=marker._takAdsbAircraft||marker._adsbData||null;if(!row&&Array.isArray(window.lastAircraft))row=window.lastAircraft.find(a=>idOf(a)===id)||null;return row||{id}}
  function rowsNow(){const c=ctl();if(c&&Array.isArray(c.lastList)&&c.lastList.length)return c.lastList;if(Array.isArray(window.lastAircraft))return window.lastAircraft;return []}

  function blob(a){return [a&&a.category,a&&a.category_raw,a&&a.emitter_category,a&&a.adsb_category,a&&a.type,a&&a.aircraft_type,a&&a.description,a&&a.desc,a&&a.model,a&&a.t,a&&a.callsign,a&&a.flight,a&&a.registration,a&&a.owner_operator,a&&a.ownOp,a&&a.operator,a&&a.owner].filter(Boolean).join(' ').toUpperCase()}
  function emitterCategory(a){for(const k of ['category','category_raw','emitter_category','adsb_category']){const v=text(a&&a[k]).toUpperCase();if(/^A[0-7]$/.test(v))return v}return ''}
  function stableFor(id){const c=ctl();try{return c&&c.stable&&c.stable.get&&c.stable.get(id)||null}catch(_){return null}}
  function classValue(a,id){
    const stable=stableFor(id),k=text(stable&&stable.classKey).toLowerCase();if(k==='military')return 'Military';if(k==='govt'||k==='government')return 'Govt';if(k==='civil')return 'Civil';
    const explicit=text(a&&(a.class_key||a.classification||a.aircraft_class||a.owner_class)).toLowerCase();if(/mil/.test(explicit))return 'Military';if(/gov|public|law/.test(explicit))return 'Govt';if(/civil|commercial|private/.test(explicit))return 'Civil';
    const b=blob(a);if(/\b(MILITARY|USAF|USN|USMC|ARMY|NAVY|AIR FORCE|COAST GUARD|RCH|REACH)\b/.test(b))return 'Military';if(/\b(GOV|GOVT|GOVERNMENT|POLICE|SHERIFF|FIRE|EMS|RESCUE|MEDEVAC|NOAA|NASA|FEMA|CBP|USFS|CAL FIRE)\b/.test(b))return 'Govt';if(/\b(CIVIL|CIVILIAN|AIRLINE|COMMERCIAL|PRIVATE|GENERAL AVIATION)\b/.test(b))return 'Civil';return 'Unknown';
  }
  function typeValue(a,id){
    if(emitterCategory(a)==='A7')return 'Rotor';
    const stable=stableFor(id);if(text(stable&&stable.shape).toLowerCase()==='helo')return 'Rotor';
    const b=blob(a);if(/\b(HELICOPTER|HELI|HELO|ROTOR|ROTORCRAFT|ROTARY|GYRO|R22|R44|R66|H60|UH-?60|MH-?60|SH-?60|HH-?60|CH-?47|AH-?64|AS350|EC135|EC145|B407|B412|S-?76|S-?92|ROBINSON|SIKORSKY|EUROCOPTER|AIRBUS HELICOPTERS)\b/.test(b))return 'Rotor';
    if(text(stable&&stable.shape).toLowerCase()==='fixed')return 'Fixed-wing';
    const cat=emitterCategory(a);if(/^A[1-6]$/.test(cat))return 'Fixed-wing';
    if(/\b(FIXED[- ]?WING|AIRPLANE|AEROPLANE|JET|TURBOPROP|GLIDER|BOEING|AIRBUS|CESSNA|PIPER|BOMBARDIER|EMBRAER)\b/.test(b))return 'Fixed-wing';
    return 'Unknown';
  }
  function iconPrefix(marker,row,id){
    try{const el=marker&&marker.getElement&&marker.getElement(),img=el&&el.querySelector('[data-adsb-img],img[src*="/assets/adsb/"]'),src=text(img&&img.getAttribute('src'));const m=src.match(/adsb_(civ|gov|mil|unk)_(?:fixed|helo)\.png/i);if(m)return m[1].toLowerCase()}catch(_){}
    const cls=classValue(row,id);return cls==='Military'?'mil':cls==='Govt'?'gov':cls==='Unknown'?'unk':'civ';
  }
  function applyTypeAndIcon(id,row,marker){
    if(!row||!marker)return;const resolved=typeValue(row,id),stable=stableFor(id);
    if(resolved==='Rotor'){
      if(stable&&stable.shape!=='helo'){stable.shape='helo';state.typeChanges++;if(emitterCategory(row)==='A7')state.rotorOverrides++}
      const path=`/assets/adsb/adsb_${iconPrefix(marker,row,id)}_helo.png`;let changed=false,foundImg=false;
      try{const el=marker.getElement&&marker.getElement(),img=el&&el.querySelector('[data-adsb-img],img[src*="/assets/adsb/"]');if(img){foundImg=true;if(!text(img.getAttribute('src')).endsWith(path)){img.setAttribute('src',path);changed=true}}}catch(_){}
      if(!foundImg)try{if(window.aircraftIcon&&marker.setIcon){marker.setIcon(window.aircraftIcon(row));changed=true}}catch(_){}
      if(changed)state.iconChanges++;
    }
    try{marker._takAdsbAircraft=row;marker._takAdsbResolvedTypeI610=resolved}catch(_){}
  }

  function onGround(a){for(const key of ['on_ground','onground','ground','is_ground'])if(a&&typeof a[key]==='boolean')return a[key];for(const key of ['on_ground','onground','ground','airground','air_ground','flight_status','alt_baro']){const v=text(a&&a[key]).toLowerCase();if(!v)continue;if(['ground','on ground','true','1','gnd'].includes(v))return true;if(['airborne','air','false','0'].includes(v))return false}return false}
  function emergencyInfo(a){const squawk=text(a&&(a.squawk||a.transponder_code));if(['7500','7600','7700'].includes(squawk))return {active:true,label:squawk==='7500'?'Unlawful interference':squawk==='7600'?'Radio failure':'General emergency'};for(const key of ['emergency','emergency_status','emergency_state','alert']){const raw=text(a&&a[key]),v=raw.toLowerCase();if(!v||['none','no','false','0','normal','n/a'].includes(v))continue;return {active:true,label:raw}}return {active:false,label:'None reported'}}
  function titleOf(a,id){return text(a&&(a.callsign||a.flight||a.registration||a.hex||a.icao||a.id))||text(id).toUpperCase()||'ADS-B Aircraft'}
  function registration(a){return text(a&&(a.registration||a.tail||a.reg))||'—'}
  function icao(a,id){return (text(a&&(a.hex||a.icao||a.icao24))||text(id)).toUpperCase()||'—'}
  function model(a){return text(a&&(a.model||a.aircraft_model||a.description||a.desc||a.t||a.aircraft_type))||'—'}
  function cleanMeta(v){const s=text(v).replace(/\s+/g,' ');if(!s||/^(?:—|-|unknown|n\/?a|null|none|not available)$/i.test(s))return '';return s.slice(0,240)}
  function ownerOperator(a){
    const direct=cleanMeta(a&&(a.owner_operator??a.ownerOperator??a.ownOp??a.owner_op??a.operator_owner));if(direct)return direct;
    const owner=cleanMeta(a&&(a.owner_name??a.ownerName??a.owner));
    const operator=cleanMeta(a&&(a.operator_name??a.operatorName??a.operator??a.oper));
    if(owner&&operator&&owner.toLowerCase()!==operator.toLowerCase())return `${owner} / ${operator}`;
    return operator||owner||'';
  }
  function altitude(a){const raw=a&&(a.alt_ft??a.altitude_ft??a.alt_baro??a.altitude);if(text(raw).toLowerCase()==='ground')return 'Ground';const ft=num(raw);return ft==null?'—':`${Math.round(ft).toLocaleString()} ft MSL`}
  function speed(a){const kt=num(a&&(a.speed_kt??a.gs??a.speed??a.groundspeed));if(kt==null)return '—';return `${Math.round(kt).toLocaleString()} kt / ${Math.round(kt*1.150779448).toLocaleString()} mph`}
  function heading(a){const v=num(a&&(a.track_deg??a.track??a.true_heading??a.mag_heading??a.heading));return v==null?'—':`${Math.round(v)}°`}
  function headingNum(a){return num(a&&(a.track_deg??a.track??a.true_heading??a.mag_heading??a.heading))}
  function verticalRate(a){const v=num(a&&(a.vertical_rate_fpm??a.vert_rate??a.baro_rate??a.geom_rate??a.vertical_rate));if(v==null)return '—';return `${v>0?'+':''}${Math.round(v).toLocaleString()} ft/min`}
  function position(a,marker){let lat=num(a&&(a.lat??a.latitude)),lon=num(a&&(a.lon??a.lng??a.longitude));const latest=state.latestPositions.get(idOf(a));if(latest){lat=latest.lat;lon=latest.lon}if((lat==null||lon==null)&&marker&&marker.getLatLng)try{const p=marker.getLatLng();lat=num(p.lat);lon=num(p.lng)}catch(_){}return lat==null||lon==null?null:{lat,lon}}
  function dateTime(a){let v=a&&(a.updated||a.last_seen||a.seen||a.timestamp||a.time||a.lastSeen);if(v==null)return '—';let d;if(typeof v==='number')d=new Date(v<1e12?v*1000:v);else d=new Date(v);if(!Number.isFinite(d.getTime()))return text(v)||'—';const p=x=>String(x).padStart(2,'0');return `${p(d.getMonth()+1)}/${p(d.getDate())}/${d.getFullYear()} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`}

  function injectCss(){
    if(document.getElementById('takMapAdsbSidebarStyleI610'))return;const style=document.createElement('style');style.id='takMapAdsbSidebarStyleI610';style.textContent=`
      .tak-adsb-panel-i610{box-sizing:border-box;position:fixed;width:min(400px,calc(100vw - 28px));max-height:calc(100vh - 112px);z-index:2147482000;color:#edf1f4;background:linear-gradient(180deg,rgba(17,29,40,.992),rgba(7,15,23,.996));border:1px solid #596671;border-radius:13px;box-shadow:0 22px 64px rgba(0,0,0,.66);overflow:hidden;pointer-events:auto;opacity:1;transform:translateX(0);transition:opacity .16s ease,transform .18s ease}
      .tak-adsb-panel-i610.hidden{opacity:0;pointer-events:none}.tak-adsb-panel-left-i610.hidden{transform:translateX(-24px)}.tak-adsb-panel-right-i610.hidden{transform:translateX(24px)}
      .tak-adsb-panel-body-i610{max-height:calc(100vh - 112px);overflow-x:hidden;overflow-y:auto;overscroll-behavior:contain;scrollbar-gutter:stable;border-radius:12px}
      .tak-adsb-i610-root{position:relative}.tak-adsb-i610-top-actions{position:absolute;right:8px;top:7px;z-index:3;display:flex;gap:5px}.tak-adsb-i610-icon-btn{width:30px;height:30px;display:grid;place-items:center;border:1px solid #60707c;border-radius:8px;background:#17232d;color:#e4e8eb;cursor:pointer}.tak-adsb-i610-icon-btn:hover{border-color:#d7dde1;background:#25323d}.tak-adsb-i610-icon-btn svg{width:16px;height:16px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}.tak-adsb-i610-icon-btn.pin.active{color:#111920;background:linear-gradient(#edf2f5,#bcc7ce);border-color:#edf2f5}.tak-adsb-i610-close{font-size:19px;line-height:1}
      .tak-adsb-i610-chips{display:flex;flex-wrap:wrap;gap:7px;min-height:45px;padding:12px 82px 11px 12px;border-bottom:1px solid rgba(203,210,216,.22);background:#14212b}.tak-adsb-i610-chip{padding:5px 9px;border-radius:999px;border:1px solid #4a6170;background:#1a2b36;color:#dce8ee;font-size:10px;font-weight:900;letter-spacing:.04em;text-transform:uppercase}.tak-adsb-i610-chip.class{border-color:#607a3d;background:#26391c;color:#e4f3cc}.tak-adsb-i610-chip.type{border-color:#3e6b83;background:#173246;color:#e7f5fb}.tak-adsb-i610-chip.ground{border-color:#8a6b3e;background:#44331d;color:#f0e5ca}.tak-adsb-i610-chip.emergency{border-color:#ff6773;background:linear-gradient(180deg,#ff2638,#c51425);color:#fff;box-shadow:0 0 12px rgba(255,38,56,.85);letter-spacing:.08em}
      .tak-adsb-i610-identity{padding:12px;border-bottom:1px solid rgba(203,210,216,.16)}.tak-adsb-i610-name{font-size:20px;font-weight:900;color:#f2f6f8}.tak-adsb-i610-sub{margin-top:3px;color:#b8c5cd;font-size:11px;overflow-wrap:anywhere}
      .tak-adsb-i610-group{margin:10px 10px 0;border:1px solid #40515e;border-radius:9px;overflow:hidden;background:#101920}.tak-adsb-i610-group-title{padding:8px 9px;border-bottom:1px solid #354550;background:#17232c;color:#c5d1d8;font-size:9.5px;font-weight:900;letter-spacing:.09em;text-transform:uppercase}.tak-adsb-i610-row{display:grid;grid-template-columns:106px minmax(0,1fr);min-height:36px;border-bottom:1px solid #2e3c46}.tak-adsb-i610-row:last-child{border-bottom:0}.tak-adsb-i610-key{padding:9px 8px;background:#111b23;color:#93a3ae;font-size:9.5px;font-weight:900;text-transform:uppercase}.tak-adsb-i610-value{padding:9px;color:#e7edf1;font-size:11px;line-height:1.4;overflow-wrap:anywhere}.tak-adsb-i610-position{display:flex;align-items:center;gap:7px}.tak-adsb-i610-position span{min-width:0;flex:1}.tak-adsb-i610-copy{flex:0 0 auto;padding:4px 7px;border:1px solid #526776;border-radius:7px;background:#182833;color:#e0e9ee;font-size:9.5px;font-weight:850}
      .tak-adsb-i610-controls{padding:10px}.tak-adsb-i610-control-label{margin:0 0 8px;color:#9fb0bb;font-size:9.5px;font-weight:900;letter-spacing:.08em;text-transform:uppercase}.tak-adsb-i610-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}.tak-adsb-i610-btn{min-height:40px;border:1px solid #425866;border-radius:8px;background:#172631;color:#dbe7ed;font-size:12px;font-weight:900}.tak-adsb-i610-btn.active{border-color:#3d8d6a;background:#173b2f;color:#dff8ed;box-shadow:inset 0 0 0 1px rgba(96,220,158,.12)}.tak-adsb-i610-btn.clear{border-color:#8f4b54;background:#261b1e;color:#f0d9dc}.tak-adsb-i610-btn.save{border-color:#dbe3e8;background:linear-gradient(#edf2f5,#bcc7ce);color:#172027}.tak-adsb-i610-status{min-height:17px;margin-top:7px;color:#9be0bd;font-size:10px;font-weight:800}.tak-adsb-i610-status.bad{color:#ff8b95}
      .tak-adsb-save-i610{position:fixed;inset:0;z-index:2147483000;display:flex;align-items:center;justify-content:center;background:rgba(0,0,0,.5);backdrop-filter:blur(3px)}.tak-adsb-save-card-i610{width:min(430px,calc(100vw - 28px));padding:14px;border:1px solid #596a76;border-radius:13px;background:linear-gradient(180deg,#172530,#0b141c);box-shadow:0 20px 58px rgba(0,0,0,.62);color:#edf3f6}.tak-adsb-save-title-i610{font-size:15px;font-weight:900}.tak-adsb-save-sub-i610{margin-top:4px;color:#aab7c0;font-size:11px}.tak-adsb-save-input-i610{width:100%;margin:11px 0 8px;padding:9px;border:1px solid #566875;border-radius:8px;background:#0d1821;color:#edf3f6}.tak-adsb-save-actions-i610{display:flex;justify-content:flex-end;gap:8px}.tak-adsb-save-actions-i610 button{min-height:36px;padding:0 13px;border-radius:8px;border:1px solid #566875;background:#172631;color:#e6edf1;font-weight:850}.tak-adsb-save-actions-i610 button.primary{border-color:#dbe3e8;background:linear-gradient(#edf2f5,#bcc7ce);color:#172027}
      /* i647: selected aircraft only receive a clean white glow. */
      .leaflet-marker-icon.tak-adsb-selected-i647 .aircraft-wrap img.adsb-png-icon,
      .leaflet-marker-icon.tak-adsb-selected-i647 .aircraft-wrap img[data-adsb-img],
      .leaflet-marker-icon.tak-adsb-selected-i647 img[src*='/assets/adsb/'],
      .tak-adsb-selected-i647 .aircraft-wrap img.adsb-png-icon,
      .tak-adsb-selected-i647 img[data-adsb-img],
      .tak-adsb-selected-i647 img[src*='/assets/adsb/'],
      .tak-adsb-selected-i647 .aircraft-glyph{
        filter:drop-shadow(0 0 3px rgba(255,255,255,.98)) drop-shadow(0 0 5px rgba(255,255,255,.9))!important;
      }
      @media(max-width:900px){.tak-adsb-panel-i610{width:min(370px,calc(100vw - 22px))}}
    `;document.head.appendChild(style);
  }

  function ensurePanels(){
    if(state.panels&&state.panels.left&&state.panels.left.panel&&state.panels.left.panel.isConnected)return state.panels;
    const make=(side)=>{const panel=document.createElement('aside');panel.id=side==='left'?'takMapAdsbLeftSidebarI610':'takMapAdsbRightSidebarI610';panel.className=`tak-adsb-panel-i610 tak-adsb-panel-${side}-i610 hidden`;panel.setAttribute('aria-hidden','true');const body=document.createElement('div');body.className='tak-adsb-panel-body-i610';body.dataset.side=side;panel.appendChild(body);document.body.appendChild(panel);return {panel,body}};
    state.panels={left:make('left'),right:make('right')};positionPanels();return state.panels;
  }
  function toolbarRect(){for(const sel of ['#floatingMapToolbar','#floatingToolbarDock','#floatingToolbar','.floating-map-toolbar','.floating-toolbar']){const el=document.querySelector(sel);if(el&&el.getBoundingClientRect){const r=el.getBoundingClientRect();if(r.width&&r.height)return r}}return null}
  function positionPanels(){
    const panels=ensurePanels(),node=mapNode(),r=node&&node.getBoundingClientRect?node.getBoundingClientRect():{left:0,top:86,right:window.innerWidth,bottom:window.innerHeight,height:window.innerHeight-86};
    const inset=12,top=Math.max(72,r.top+inset),bottomInset=Math.max(10,window.innerHeight-r.bottom+inset),maxH=Math.max(180,Math.min(r.height-inset*2,window.innerHeight-top-bottomInset));
    panels.left.panel.style.left=Math.max(10,r.left+inset)+'px';panels.left.panel.style.right='auto';panels.left.panel.style.top='auto';panels.left.panel.style.bottom=bottomInset+'px';panels.left.panel.style.maxHeight=maxH+'px';panels.left.body.style.maxHeight=maxH+'px';
    const viewportWidth=document.documentElement&&document.documentElement.clientWidth||window.innerWidth,rightInset=Math.max(10,viewportWidth-r.right+inset);panels.right.panel.style.left='auto';panels.right.panel.style.right=rightInset+'px';panels.right.panel.style.top='auto';panels.right.panel.style.bottom=bottomInset+'px';panels.right.panel.style.maxHeight=maxH+'px';panels.right.body.style.maxHeight=maxH+'px';
  }
  function showPanel(which){const p=ensurePanels()[which];p.panel.classList.remove('hidden');p.panel.setAttribute('aria-hidden','false');positionPanels()}
  function hidePanel(which){const p=ensurePanels()[which];p.panel.classList.add('hidden');p.panel.setAttribute('aria-hidden','true');p.body.innerHTML=''}

  function trailState(id){id=text(id).toLowerCase();let t=state.trails.get(id);if(!t){t={id,points:[],line:null,meta:null,lastSavedPointCount:0,savedName:'',saveCount:0};state.trails.set(id,t)}return t}
  function updateTrailLine(t){const m=mapObj();if(!m||!window.L)return;const start=t.lastSavedPointCount>0?Math.max(0,t.lastSavedPointCount-1):0,ll=t.points.slice(start).map(p=>[p.lat,p.lon]);if(ll.length<2){if(t.line)try{m.removeLayer&&m.removeLayer(t.line)}catch(_){}t.line=null;return}if(!t.line)t.line=L.polyline(ll,{color:'#ff7a1a',weight:4,opacity:.94,interactive:false}).addTo(m);else t.line.setLatLngs(ll)}
  function appendTrailSample(id,p,row,when){if(!state.trackingIds.has(id)||!p)return;const t=trailState(id),last=t.points[t.points.length-1],time=Number(when)||Date.now();if(last){const same=Math.abs(last.lat-p.lat)<0.000001&&Math.abs(last.lon-p.lon)<0.000001;if(same&&time-last.time<4000)return}t.points.push({lat:p.lat,lon:p.lon,alt_ft:num(p.alt_ft??(row&&(row.alt_ft??row.altitude_ft??row.alt_baro))),time});if(t.points.length>12000)t.points.splice(0,t.points.length-12000);t.meta=row;updateTrailLine(t)}
  function appendCurrent(id){const marker=markerFor(id),row=rowFor(id,marker),p=position(row,marker);appendTrailSample(id,p,row,Date.now())}
  function clearTrail(id){const t=trailState(id);t.points=[];t.lastSavedPointCount=0;t.savedName='';t.saveCount=0;if(t.line)try{const m=mapObj();m&&m.removeLayer&&m.removeLayer(t.line)}catch(_){}t.line=null;setStatus(id,'Trail cleared.');renderPanels()}
  function postTracking(){try{ensureBackgroundWorker().postMessage({type:'tracking',ids:Array.from(state.trackingIds)})}catch(_){}}
  function toggleTrack(id){id=text(id).toLowerCase();if(state.trackingIds.has(id)){state.trackingIds.delete(id);setStatus(id,'Track recording paused; retained trail remains available.')}else{state.trackingIds.add(id);appendCurrent(id);setStatus(id,'Track recording active.')}postTracking();renderPanels()}
  function toggleFollow(id){id=text(id).toLowerCase();state.followId=state.followId===id?'':id;setStatus(id,state.followId?'Following aircraft.':'Follow stopped.');if(state.followId)followNow(id);renderPanels()}
  function followNow(id){const p=state.latestPositions.get(id)||position(rowFor(id,markerFor(id)),markerFor(id)),m=mapObj();if(!p||!m)return;try{m.panTo([p.lat,p.lon],{animate:!document.hidden,duration:.28})}catch(_){try{m.setView([p.lat,p.lon],m.getZoom(),{animate:!document.hidden})}catch(__){}}}
  function setStatus(id,msg){state.statusById.set(text(id).toLowerCase(),msg)}

  function controlHtml(id){const t=trailState(id),follow=state.followId===id,tracking=state.trackingIds.has(id),msg=state.statusById.get(id)||`${t.points.length} retained trail point${t.points.length===1?'':'s'}.`;return `<div class="tak-adsb-i610-controls"><div class="tak-adsb-i610-control-label">Aircraft controls</div><div class="tak-adsb-i610-grid"><button class="tak-adsb-i610-btn ${follow?'active':''}" data-adsb-i610-action="follow">Follow</button><button class="tak-adsb-i610-btn ${tracking?'active':''}" data-adsb-i610-action="track">Track</button><button class="tak-adsb-i610-btn clear" data-adsb-i610-action="clear">Clear Trail</button><button class="tak-adsb-i610-btn save" data-adsb-i610-action="save">Save Trail</button></div><div class="tak-adsb-i610-status ${/^save failed|at least/i.test(msg)?'bad':''}">${esc(msg)}</div></div>`}
  function renderBody(row,id,marker,side){const cls=classValue(row,id),type=typeValue(row,id),ground=onGround(row),em=emergencyInfo(row),p=position(row,marker),sq=text(row&&(row.squawk||row.transponder_code))||'—',ownerOp=ownerOperator(row),ownerRow=`<div class="tak-adsb-i610-row"><div class="tak-adsb-i610-key">Owner / Operator</div><div class="tak-adsb-i610-value">${esc(ownerOp||'Not reported')}</div></div>`,chips=[`<span class="tak-adsb-i610-chip class">${esc(cls)}</span>`,`<span class="tak-adsb-i610-chip type">${esc(type)}</span>`];if(ground)chips.push('<span class="tak-adsb-i610-chip ground">Ground</span>');if(em.active)chips.push('<span class="tak-adsb-i610-chip emergency">Emergency</span>');const pos=p?`${p.lat.toFixed(6)}, ${p.lon.toFixed(6)}`:'—';const pin=side==='left'?`<button class="tak-adsb-i610-icon-btn pin ${state.pinned?'active':''}" data-adsb-i610-action="pin" aria-pressed="${state.pinned?'true':'false'}" title="${state.pinned?'Unpin aircraft panel':'Pin aircraft panel'}"><svg viewBox="0 0 24 24"><path d="M9 3h6l-1 6 3 3v2H7v-2l3-3-1-6Z"/><path d="M12 14v7"/></svg></button>`:'';return `<div class="tak-adsb-i610-root" data-adsb-id="${esc(id)}" data-side="${side}"><div class="tak-adsb-i610-top-actions">${pin}<button class="tak-adsb-i610-icon-btn tak-adsb-i610-close" data-adsb-i610-action="close" title="Close">×</button></div><div class="tak-adsb-i610-chips">${chips.join('')}</div><div class="tak-adsb-i610-identity"><div class="tak-adsb-i610-name">${esc(titleOf(row,id))}</div><div class="tak-adsb-i610-sub">${esc(model(row))} · ${esc(registration(row))} · ${esc(icao(row,id))}</div></div><div class="tak-adsb-i610-group"><div class="tak-adsb-i610-group-title">Identification</div><div class="tak-adsb-i610-row"><div class="tak-adsb-i610-key">Callsign</div><div class="tak-adsb-i610-value">${esc(titleOf(row,id))}</div></div><div class="tak-adsb-i610-row"><div class="tak-adsb-i610-key">Registration</div><div class="tak-adsb-i610-value">${esc(registration(row))}</div></div><div class="tak-adsb-i610-row"><div class="tak-adsb-i610-key">ICAO Hex</div><div class="tak-adsb-i610-value">${esc(icao(row,id))}</div></div><div class="tak-adsb-i610-row"><div class="tak-adsb-i610-key">Aircraft</div><div class="tak-adsb-i610-value">${esc(model(row))}</div></div>${ownerRow}</div><div class="tak-adsb-i610-group"><div class="tak-adsb-i610-group-title">Flight</div><div class="tak-adsb-i610-row"><div class="tak-adsb-i610-key">Altitude</div><div class="tak-adsb-i610-value">${esc(altitude(row))}</div></div><div class="tak-adsb-i610-row"><div class="tak-adsb-i610-key">Ground Speed</div><div class="tak-adsb-i610-value">${esc(speed(row))}</div></div><div class="tak-adsb-i610-row"><div class="tak-adsb-i610-key">Track</div><div class="tak-adsb-i610-value">${esc(heading(row))}</div></div><div class="tak-adsb-i610-row"><div class="tak-adsb-i610-key">Vertical Rate</div><div class="tak-adsb-i610-value">${esc(verticalRate(row))}</div></div><div class="tak-adsb-i610-row"><div class="tak-adsb-i610-key">Squawk</div><div class="tak-adsb-i610-value">${esc(sq)}</div></div></div><div class="tak-adsb-i610-group"><div class="tak-adsb-i610-group-title">Position and status</div><div class="tak-adsb-i610-row"><div class="tak-adsb-i610-key">Position</div><div class="tak-adsb-i610-value tak-adsb-i610-position"><span>${esc(pos)}</span><button class="tak-adsb-i610-copy" data-adsb-i610-action="copy">Copy</button></div></div><div class="tak-adsb-i610-row"><div class="tak-adsb-i610-key">Last Seen</div><div class="tak-adsb-i610-value">${esc(dateTime(row))}</div></div><div class="tak-adsb-i610-row"><div class="tak-adsb-i610-key">Emergency</div><div class="tak-adsb-i610-value">${esc(em.label)}</div></div></div>${controlHtml(id)}</div>`}
  function renderPanel(which,id){const p=ensurePanels()[which],marker=markerFor(id),row=rowFor(id,marker),scroll=p.body.scrollTop;p.body.innerHTML=renderBody(row,id,marker,which);p.body.scrollTop=scroll;showPanel(which)}
  function renderPanels(){if(state.leftId)renderPanel('left',state.leftId);if(state.rightId)renderPanel('right',state.rightId)}

  function syncSelectionHighlights(){
    const selected=isReplay()?new Set():new Set([state.leftId,state.rightId].filter(Boolean));
    for(const [id,marker] of markerEntries()){
      const el=marker&&marker.getElement&&marker.getElement();
      if(!el||!el.classList)continue;
      const markerId=text(id||idOf(marker._takAdsbAircraft)).toLowerCase();
      el.classList.toggle('tak-adsb-selected-i647',selected.has(markerId));
    }
  }


  async function copyPosition(id,button){const marker=markerFor(id),p=position(rowFor(id,marker),marker);if(!p)return;const value=`${p.lat.toFixed(6)}, ${p.lon.toFixed(6)}`;try{await navigator.clipboard.writeText(value);button.textContent='Copied'}catch(_){button.textContent=value}setTimeout(()=>{try{button.textContent='Copy'}catch(_){}},1000)}
  function safeName(v){return text(v||'ADS-B Trail').replace(/[\\/:*?"<>|]+/g,'-').replace(/\s+/g,' ').trim()||'ADS-B Trail'}
  function openSaveDialog(id){const t=trailState(id),row=rowFor(id,markerFor(id));if(t.points.length<2){setStatus(id,'At least 2 trail points are required to save.');renderPanels();return}document.getElementById('takAdsbSaveDialogI610')?.remove();const div=document.createElement('div');div.id='takAdsbSaveDialogI610';div.className='tak-adsb-save-i610';const defaultName=t.savedName||safeName(`${titleOf(row,id)} ADS-B Trail ${new Date().toISOString().slice(0,16).replace(/[T:]/g,'-')}`);div.innerHTML=`<div class="tak-adsb-save-card-i610"><div class="tak-adsb-save-title-i610">Save aircraft trail</div><div class="tak-adsb-save-sub-i610">${esc(titleOf(row,id))} · ${t.points.length} points · saves to Local Data routes</div><input class="tak-adsb-save-input-i610" value="${esc(defaultName)}"><div class="tak-adsb-i610-status" data-save-status></div><div class="tak-adsb-save-actions-i610"><button data-save-act="cancel">Cancel</button><button class="primary" data-save-act="save">Save Trail</button></div></div>`;document.body.appendChild(div);div.addEventListener('click',async ev=>{const b=ev.target.closest&&ev.target.closest('[data-save-act]');if(ev.target===div||b&&b.dataset.saveAct==='cancel'){div.remove();return}if(!b||b.dataset.saveAct!=='save')return;const status=div.querySelector('[data-save-status]'),name=safeName(div.querySelector('input').value||defaultName);b.disabled=true;status.textContent='Saving…';try{await saveTrail(id,name);status.textContent='Saved to Local Data routes.';setStatus(id,'Trail saved to Local Data routes.');setTimeout(()=>{div.remove();renderPanels()},700)}catch(e){status.textContent='Save failed: '+String(e&&e.message||e);status.classList.add('bad');b.disabled=false}});setTimeout(()=>div.querySelector('input')?.focus(),20)}
  async function saveTrail(id,name){const t=trailState(id),row=rowFor(id,markerFor(id));if(t.points.length<2)throw new Error('At least 2 trail points are required.');const coords=t.points.map(p=>[p.lon,p.lat,p.alt_ft||0]),savedPointCount=coords.length,fc={type:'FeatureCollection',features:[{type:'Feature',geometry:{type:'LineString',coordinates:coords},properties:{name,kind:'route',category:'ADS-B Aircraft Trail',route_type:'adsb_aircraft_track',callsign:titleOf(row,id),icao_hex:icao(row,id),point_count:t.points.length,source:'TAK Map live ADS-B'}}]},blob=new Blob([JSON.stringify(fc,null,2)],{type:'application/geo+json'}),file=new File([blob],safeName(name)+'.geojson',{type:'application/geo+json'}),fd=new FormData();fd.append('files',file,file.name);const r=await fetch('/api/tak-map/import',{method:'POST',body:fd,cache:'no-store',credentials:'same-origin'});if(!r.ok)throw new Error(`HTTP ${r.status}`);try{if(typeof window.refreshLocalData==='function')await window.refreshLocalData()}catch(_){}try{if(typeof window.refreshImports==='function')await window.refreshImports()}catch(_){}t.savedName=name;t.saveCount++;t.lastSavedPointCount=savedPointCount;if(t.line)try{const m=mapObj();m&&m.removeLayer&&m.removeLayer(t.line)}catch(_){}t.line=null;updateTrailLine(t)}

  function togglePin(){if(!state.leftId)return;state.pinned=!state.pinned;if(!state.pinned&&state.rightId){state.rightId='';hidePanel('right')}renderPanels();syncSelectionHighlights()}
  function closePanel(side){if(side==='right'){state.rightId='';hidePanel('right');syncSelectionHighlights();return}const promote=state.rightId;state.leftId='';state.pinned=false;hidePanel('left');if(promote){state.rightId='';hidePanel('right');state.leftId=promote;renderPanel('left',promote)}syncSelectionHighlights()}
  function openAircraft(id,marker,center){if(isReplay())return false;id=text(id||idOf(marker&&marker._takAdsbAircraft)).toLowerCase();if(!id)return false;if(state.pinned&&state.leftId&&id!==state.leftId){state.rightId=id;state.rightOpens++;renderPanel('right',id)}else{state.leftId=id;state.leftOpens++;if(!state.pinned&&state.rightId){state.rightId='';hidePanel('right')}renderPanel('left',id)}if(center){const p=position(rowFor(id,marker),marker),m=mapObj();if(p&&m)try{m.setView([p.lat,p.lon],Math.max(m.getZoom(),13),{animate:true})}catch(_){}}syncSelectionHighlights();return true}
  function bindPanelActions(which){const body=ensurePanels()[which].body;if(body.dataset.actionsI610==='1')return;body.dataset.actionsI610='1';body.addEventListener('click',ev=>{const btn=ev.target&&ev.target.closest&&ev.target.closest('[data-adsb-i610-action]');if(!btn)return;ev.preventDefault();ev.stopPropagation();const root=btn.closest('.tak-adsb-i610-root'),id=text(root&&root.dataset.adsbId).toLowerCase(),action=btn.dataset.adsbI610Action;if(action==='follow')toggleFollow(id);else if(action==='track')toggleTrack(id);else if(action==='clear')clearTrail(id);else if(action==='save')openSaveDialog(id);else if(action==='copy')copyPosition(id,btn);else if(action==='pin')togglePin();else if(action==='close')closePanel(which)})}
  function bindPanels(){ensurePanels();bindPanelActions('left');bindPanelActions('right')}

  function stopEvent(ev){try{ev.preventDefault()}catch(_){}try{ev.stopPropagation()}catch(_){}try{ev.stopImmediatePropagation()}catch(_){}const oe=ev&&ev.originalEvent;if(oe){try{oe.preventDefault()}catch(_){}try{oe.stopPropagation()}catch(_){}try{oe.stopImmediatePropagation()}catch(_){}}}
  function bindMarker(id,marker){if(!marker||isReplay())return false;id=text(id||idOf(marker._takAdsbAircraft)).toLowerCase();if(!id)return false;const row=rowFor(id,marker);applyTypeAndIcon(id,row,marker);try{marker.closePopup&&marker.closePopup();marker.unbindPopup&&marker.unbindPopup()}catch(_){}try{if(marker._openPopup&&marker.off)marker.off('click',marker._openPopup,marker)}catch(_){}let el=null;try{el=marker.getElement&&marker.getElement()}catch(_){}if(el&&el.addEventListener){el.dataset.takAdsbMarkerI610='1';const oldEl=marker.__takAdsbPopupOwnerElementV502,old=marker.__takAdsbPopupOwnerHandlerV502;if(oldEl&&old&&old!==marker.__takAdsbSidebarDomHandlerI610)try{oldEl.removeEventListener('click',old,true)}catch(_){}if(marker.__takAdsbSidebarElementI610!==el){if(marker.__takAdsbSidebarElementI610&&marker.__takAdsbSidebarDomHandlerI610)try{marker.__takAdsbSidebarElementI610.removeEventListener('click',marker.__takAdsbSidebarDomHandlerI610,true)}catch(_){}const handler=ev=>{if(isReplay())return;stopEvent(ev);openAircraft(id,marker,false)};el.addEventListener('click',handler,true);marker.__takAdsbSidebarElementI610=el;marker.__takAdsbSidebarDomHandlerI610=handler;state.markerBindings++}marker.__takAdsbPopupOwnerElementV502=el;marker.__takAdsbPopupOwnerHandlerV502=marker.__takAdsbSidebarDomHandlerI610}if(marker.on&&marker.off&&!marker.__takAdsbSidebarLeafletHandlerI610){const handler=ev=>{if(isReplay())return;stopEvent(ev);openAircraft(id,marker,false)};marker.on('click',handler);marker.__takAdsbSidebarLeafletHandlerI610=handler}return true}

  function currentPose(id,row,marker){const latest=state.latestPositions.get(id);if(latest)return latest;try{const ll=marker&&marker.getLatLng&&marker.getLatLng();if(ll)return {lat:Number(ll.lat),lon:Number(ll.lng),heading:headingNum(row)}}catch(_){}return {lat:num(row&&(row.lat??row.latitude)),lon:num(row&&(row.lon??row.lng??row.longitude)),heading:headingNum(row)}}
  function configuredDuration(){let ms=5000;try{const d=window.TakMapAdsbWorkerV477&&window.TakMapAdsbWorkerV477.diagnostics&&window.TakMapAdsbWorkerV477.diagnostics();ms=Number(d&&d.actualIntervalMs||d&&d.configuredIntervalMs)||ms}catch(_){}return Math.max(700,Math.min(4500,ms*.9))}
  function syncMotion(rows){if(isReplay())return;const entries=[],active=[];for(const raw of rows||[]){const id=idOf(raw),lat=num(raw&&(raw.lat??raw.latitude)),lon=num(raw&&(raw.lon??raw.lng??raw.longitude));if(!id||lat==null||lon==null)continue;active.push(id);const marker=markerFor(id),start=currentPose(id,raw,marker),targetHeading=headingNum(raw),sig=`${lat.toFixed(6)},${lon.toFixed(6)},${targetHeading==null?'':targetHeading}`;if(state.motionTargets.get(id)===sig)continue;state.motionTargets.set(id,sig);entries.push({id,startLat:start.lat??lat,startLon:start.lon??lon,targetLat:lat,targetLon:lon,startHeading:start.heading,targetHeading,duration:configuredDuration(),alt_ft:num(raw.alt_ft??raw.altitude_ft??raw.alt_baro)})}if(entries.length||active.length)try{ensureBackgroundWorker().postMessage({type:'motion',entries,activeIds:active})}catch(_){}
  }
  function updateMarkerPose(id,p){const marker=markerFor(id);if(!marker||!p)return;try{marker.setLatLng&&marker.setLatLng([p.lat,p.lon])}catch(_){}try{const el=marker.getElement&&marker.getElement(),img=el&&el.querySelector('[data-adsb-img],img[src*="/assets/adsb/"]');if(img&&Number.isFinite(p.heading)){img.style.transform=`rotate(${p.heading}deg) scale(.75)`;img.style.transformOrigin='50% 50%'}}catch(_){}
  }
  function ensureBackgroundWorker(){if(state.backgroundWorker)return state.backgroundWorker;state.backgroundWorkerUrl=URL.createObjectURL(new Blob([BG_SOURCE],{type:'text/javascript'}));const w=new Worker(state.backgroundWorkerUrl,{name:'tak-map-adsb-interpolation-i610'});w.onmessage=ev=>{const msg=ev.data||{};if(msg.type!=='tick'||isReplay())return;state.backgroundTicks++;syncMotion(rowsNow());for(const p of msg.positions||[]){state.latestPositions.set(p.id,p);if(document.hidden)updateMarkerPose(p.id,p)}for(const p of msg.samples||[]){state.backgroundSamples++;appendTrailSample(p.id,p,rowFor(p.id,markerFor(p.id)),p.time)}if(state.followId&&!document.hidden)followNow(state.followId);renderPanels()};w.onerror=ev=>{state.lastError='Background interpolation worker failed: '+text(ev&&ev.message)};state.backgroundWorker=w;postTracking();return w}
  function visibilityChanged(){state.lastVisibility=document.visibilityState||'visible';try{ensureBackgroundWorker().postMessage({type:'snapshot'})}catch(_){}if(!document.hidden){for(const [id,p] of state.latestPositions)updateMarkerPose(id,p);if(state.followId)followNow(state.followId);renderPanels()}}

  function afterDraw(input){if(isReplay())return;state.drawPasses++;syncMotion(Array.isArray(input)?input:rowsNow());for(const [id,marker] of markerEntries()){bindMarker(id,marker);applyTypeAndIcon(id,rowFor(id,marker),marker)}renderPanels();syncSelectionHighlights()}
  function ensureDrawWrapper(){const current=window.drawAircraft;if(typeof current!=='function')return false;if(current.__takAdsbSidebarWrapperI610)return true;const wrapper=function(){const input=arguments[0];try{if(Array.isArray(input))syncMotion(input)}catch(_){}const out=current.apply(this,arguments);try{setTimeout(()=>afterDraw(input),0)}catch(_){}return out};wrapper.__takAdsbSidebarWrapperI610=true;wrapper.__takAdsbSidebarBaseI610=current;state.drawBase=current;state.drawWrapper=wrapper;window.drawAircraft=wrapper;return true}
  function ensureFocusWrapper(){const current=window.focusAdsbAircraft;if(typeof current!=='function')return false;if(current.__takAdsbSidebarFocusI610)return true;const wrapper=function(id){if(isReplay())return current.apply(this,arguments);id=text(decodeURIComponent(String(id||''))).toLowerCase();openAircraft(id,markerFor(id),true);return false};wrapper.__takAdsbSidebarFocusI610=true;wrapper.__takAdsbSidebarBaseI610=current;state.focusBase=current;state.focusWrapper=wrapper;window.focusAdsbAircraft=wrapper;return true}
  function bindOutside(){if(state.outsideBound)return;state.outsideBound=true;document.addEventListener('click',ev=>{if(!state.leftId)return;const t=ev.target;if(t&&t.closest&&t.closest('.tak-adsb-panel-i610,[data-tak-adsb-marker-i610="1"],[data-adsb-focus],.tak-veil-i665-marker,.tak-veil-icon-i669'))return;setTimeout(()=>{if(state.pinned){if(state.rightId)closePanel('right')}else if(state.leftId)closePanel('left')},0)},true)}
  function bindResize(){if(state.resizeBound)return;state.resizeBound=true;window.addEventListener('resize',positionPanels,{passive:true});document.addEventListener('visibilitychange',visibilityChanged);const m=mapObj();try{if(m&&m.on)m.on('moveend zoomend resize',positionPanels)}catch(_){} }
  function pass(){try{injectCss();bindPanels();bindOutside();bindResize();ensureDrawWrapper();ensureFocusWrapper();ensureBackgroundWorker();syncMotion(rowsNow());if(!isReplay())for(const [id,marker] of markerEntries())bindMarker(id,marker);syncSelectionHighlights();positionPanels();state.lastError=''}catch(e){state.lastError=String(e&&e.stack||e)}}
  function diagnostics(){const lt=state.leftId?trailState(state.leftId):null,panels=ensurePanels();return {version:V,initialized:state.initialized,replayMode:isReplay(),markersFound:markerEntries().length,markerBindings:state.markerBindings,leftOpens:state.leftOpens,rightOpens:state.rightOpens,leftId:state.leftId,rightId:state.rightId,pinned:state.pinned,followId:state.followId,trackingIds:Array.from(state.trackingIds),leftTrailPoints:lt?lt.points.length:0,leftLastSavedPointCount:lt?lt.lastSavedPointCount:0,backgroundWorker:!!state.backgroundWorker,backgroundTicks:state.backgroundTicks,backgroundSamples:state.backgroundSamples,lastVisibility:state.lastVisibility,leftPanelVisible:!panels.left.panel.classList.contains('hidden'),rightPanelVisible:!panels.right.panel.classList.contains('hidden'),leftZIndex:getComputedStyle(panels.left.panel).zIndex,rightZIndex:getComputedStyle(panels.right.panel).zIndex,typeChanges:state.typeChanges,rotorOverrides:state.rotorOverrides,iconChanges:state.iconChanges,drawWrapped:!!(window.drawAircraft&&window.drawAircraft.__takAdsbSidebarWrapperI610),focusWrapped:!!(window.focusAdsbAircraft&&window.focusAdsbAircraft.__takAdsbSidebarFocusI610),dataSyncTouched:false,sharedDynamicWidthI618:!!window.TakMapContextPanelSizingI618,scrollbarGutterStable:true,lastError:state.lastError}}
  function boot(){if(state.initialized)return;state.initialized=true;injectCss();bindPanels();pass();state.timer=setInterval(pass,1000);window.addEventListener('takmap:runtime-ready-i553',()=>setTimeout(pass,100));console.info('[TAK Map] adsb-sidebar-i610 loaded')}

  /* Live general-map search uses rendered aircraft markers, never raw/stale feed rows. */
  function searchVisibleAircraft(){
    if(isReplay())return [];
    const m=mapObj();if(!m)return [];
    const out=[],seen=new Set();
    for(const [key,marker] of markerEntries()){
      if(!marker)continue;
      if(typeof m.hasLayer==='function'&&!m.hasLayer(marker))continue;
      const row=rowFor(key,marker),id=idOf(row)||text(key).toLowerCase();
      if(!id||seen.has(id))continue;
      const p=position(row,marker);
      if(!p||!Number.isFinite(p.lat)||!Number.isFinite(p.lon))continue;
      seen.add(id);
      out.push({id,label:titleOf(row,id),lat:p.lat,lon:p.lon,layer:marker,
        category:text(row.type||row.aircraft_type||row.model||'Aircraft'),
        terms:[row.callsign,row.flight,row.registration,row.hex,row.icao,row.icao24,row.id,row.owner_operator,row.ownOp,row.owner,row.operator,row.owner_name,row.operator_name,row.description,row.aircraft_type,row.model,row.type]});
    }
    return out;
  }

  // VEIL aircraft use this exact same ADS-B details panel, including the existing
  // tracking/follow/save controls. Data remains in the external VEIL source.
  function openExternalI669(row,marker){
    if(!row||!row.id)return false;
    const id=text(row.id).toLowerCase();
    externalAircraftI669.set(id,{row:{...row},marker:marker||null});
    return openAircraft(id,marker||null,false);
  }
  function removeExternalI669(id){id=text(id).toLowerCase();externalAircraftI669.delete(id);
    if(state.leftId===id)closePanel('left');
    if(state.rightId===id)closePanel('right');
  }
  window[ID]=Object.freeze({version:V,openExternal:openExternalI669,removeExternal:removeExternalI669,searchVisible:searchVisibleAircraft,get initialized(){return state.initialized},diagnostics,open:(id)=>openAircraft(id,markerFor(id),false),refresh:pass,clearTrail,toggleTrack,toggleFollow,togglePin,close:()=>closePanel('left')});
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})();
