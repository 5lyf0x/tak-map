/* TAK Map i670: VEIL uses authentic ADSBx aircraft silhouettes and shared ADS-B panel. */
(()=>{'use strict';
const V='1.4.0-i672';
const COLORS={military:'#0775d3',civilian:'#0ca751',government:'#7d009a',unknown:'#b4ab25'};
const TYPE_IDS={adsb:'ADS-B',ais:'AIS',aprs:'APRS',remote_id:'Remote ID'};
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const lastAircraftHeadings=new Map();
function heading(o){
 const sources=[o?.heading,o?.courseDeg,o?.motion?.courseDeg,o?.track?.courseDeg,o?.track?.course,o?.trackDeg];
 const key=o?.service==='adsb'?String(o?.canonicalKey||o?.id||''):'';
 const observed=Number(o?.timestamp)||0,expires=Number(o?.stale)||0;
 const now=Date.now()/1000;
 for(const value of sources){
  if(value===null||value===undefined||value===''||typeof value==='boolean')continue;
  const n=Number(value);if(!Number.isFinite(n)||Math.abs(n)>36000)continue;
  const degree=((n%360)+360)%360;
  if(key&&observed>0&&expires>now)lastAircraftHeadings.set(key,{degree,observed,expires});
  return degree;
 }
 // The last live heading may bridge brief track omissions, but never an expired aircraft.
 if(key&&expires>now){const prior=lastAircraftHeadings.get(key);
  if(prior&&prior.expires>now&&Math.abs(observed-prior.observed)<=90)return prior.degree;}
 if(key&&lastAircraftHeadings.size>4000){for(const [k,prev] of lastAircraftHeadings)if(prev.expires<=now)lastAircraftHeadings.delete(k)}
 return null;
}
function altitude(o){const x=o?.hae;if(x===null||x===undefined||x==='')return null;const n=Number(x);return Number.isFinite(n)&&n>=-1000&&n<=50000?n:null}
function category(o){
 const metadata=o?.enrichment||{},identity=o?.identity||{},values=[o?.classification,o?.aircraftClass,o?.classKey,metadata.classification,metadata.aircraft_class,metadata.class_key,metadata.category_class,identity.classification,identity.category].map(v=>String(v||'').toLowerCase());
 const direct=values.find(v=>/military|government|govt|civilian|civil|private|commercial|unknown/.test(v));
 if(direct){if(/military/.test(direct))return 'military';if(/gov|public/.test(direct))return 'government';if(/civil|private|commercial/.test(direct))return 'civilian';return 'unknown'}
 if(o?.is_military===true)return 'military';if(o?.is_govt===true)return 'government';
 const icao=String(o?.identity?.icao||o?.identity?.hex||'').toLowerCase();
 if(/^[a-f0-9]{6}$/.test(icao)){
  try{const row=window.TakMapControllers?.adsb?.stable?.get(icao);const c=String(row?.classKey||'').toLowerCase();
   if(c==='military')return 'military';if(c==='govt'||c==='government')return 'government';
   if(c==='civil'||c==='civilian')return 'civilian'}catch(_){}
 }
 return 'unknown';
}
function rotor(o){const t=[o?.type,o?.enrichment?.aircraft_type,o?.enrichment?.type,o?.enrichment?.model,o?.enrichment?.description,o?.enrichment?.category].join(' ').toLowerCase();return /helicopter|helo|rotor|rotary|\ba7\b|h60|uh-?60|b407|r44/.test(t)}
function targetSvg(o){
 const selection=window.TakMapAdsbxI670?.select(o)||{shape:'unknown',viewBox:'-2.5 -2.5 22 22',path:'M 4 15 L 2 10 7 8 7 3 9 1 10 8 16 10 14 13 10 11 10 15 Z'};
 const degree=heading(o)??0;
 // No generic affiliation disc or target-ring overlay. Keep the original ADSBx path intact.
 const src=String(selection.path||'').replace(/["<>]/g,'');const box=String(selection.viewBox||'0 0 32 32').replace(/["<>]/g,'');
 return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40" role="img" aria-label="${category(o)} aircraft ${selection.type||''}" data-adsbx-shape="${selection.shape}" data-adsbx-type="${selection.type||''}"><g transform="rotate(${degree} 20 20)"><svg x="3" y="3" width="34" height="34" viewBox="${box}" preserveAspectRatio="xMidYMid meet"><path d="${src}" fill="#ffffff" stroke="#000000" stroke-width="1" vector-effect="non-scaling-stroke" stroke-linejoin="round"/></svg></g></svg>`;
}
function glyphSvg(o){if(o.service==='adsb')return targetSvg(o);if(o.service==='aprs')return window.TakMapVeilAprsI672?.path(o)||'';const kind=o.service;
 const svg=kind==='ais'?'<path d="M12 21h16l-3 9H15l-3-9m8-14v14M14 15h12l-3-6h-6l-3 6"/>':kind==='remote_id'?'<path d="M14 15l-5-5m17 5 5-5M14 25l-5 5m17-5 5 5M16 16h8v8h-8z"/><circle cx="9" cy="10" r="3"/><circle cx="31" cy="10" r="3"/><circle cx="9" cy="30" r="3"/><circle cx="31" cy="30" r="3"/>':'<path d="M17 30V15h6v15M12 30h16M10 13c6-7 14-7 20 0M14 16c4-4 8-4 12 0"/>';
 return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><circle cx="20" cy="20" r="17" fill="#122535" fill-opacity=".92" stroke="#c4d5dd" stroke-width="1.8"/><g stroke="#f2f6fa" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" fill="none">${svg}</g></svg>`;
}
function iconSize(o){return o?.service==='adsb'?43.2:o?.service==='aprs'?44:36}
function image(o){if(o.service==='aprs')return window.TakMapVeilAprsI672?.path(o)||null;return 'data:image/svg+xml;charset=utf-8,'+encodeURIComponent(glyphSvg(o))}
function markerHtml(o){if(o.service==='aprs')return `<span class="tak-veil-aprs-wrap-i672">${window.TakMapVeilAprsI672?.markerHtml(o)||''}<span class="tak-veil-aprs-label-i672">${esc(o.title||o.identity?.callsign||'')}</span></span>`;return `<span class="tak-veil-icon-i669">${glyphSvg(o)}</span>`}
function adsbRow(o){const ident=o.identity||{},en=o.enrichment||{},key=String(o.canonicalKey||'');const icao=String(ident.icao||ident.icao24||ident.hex||(key.startsWith('adsb:icao:')?key.slice(10):'')).toLowerCase();const h=heading(o),alt=altitude(o);
 const id='veil-'+(String(o.__veilKey||o.id||'').replace(/[^a-zA-Z0-9_-]/g,'-')).slice(0,140);
 const speed=Number(o.speedMps);
 return {id,hex:/^[a-f0-9]{6}$/.test(icao)?icao:'',icao:/^[a-f0-9]{6}$/.test(icao)?icao:'',callsign:String(ident.callsign||o.title||'').slice(0,60),
  flight:String(ident.flight||o.title||'').slice(0,60),lat:Number(o.lat),lon:Number(o.lon),track_deg:h,heading:h,
  altitude_ft:alt===null?undefined:alt*3.280839895,altitude_ref:alt===null?'not supplied':'HAE (WGS84 ellipsoid)',
  speed_kt:Number.isFinite(speed)&&o.speedMps!==null&&o.speedMps!==''?speed*1.943844:undefined,
  category_class:category(o),aircraft_class:category(o),is_helo:rotor(o),type:String(en.type_designator||en.icao_type||en.aircraft_type||en.type||''),
  aircraft_type:String(en.type_designator||en.icao_type||en.aircraft_type||en.type||''),description:String(en.description||''),
  owner_operator:String(en.operator||en.owner_operator||en.ownOp||''),registration:String(en.registration||ident.registration||''),
  source:'XTAK VEIL · '+String(o.nodeId||'')};
}
function openAdsb(o,marker){const panel=window.TakMapAdsbSidebarI610;
 if(panel&&typeof panel.openExternal==='function')return panel.openExternal(adsbRow(o),marker);
 return false;
}
function genericPopup(o){let s='<div class="tak-veil-i665-popup"><b>XTAK VEIL · '+esc(TYPE_IDS[o.service]||o.service)+'</b><div>'+esc(o.title)+'</div>';
 s+='<div>Node: '+esc(o.nodeId)+'</div>';
 if(o.heading!==null&&o.heading!==undefined)s+='<div>Heading: '+esc(o.heading)+'°</div>';
 if(altitude(o)!==null)s+='<div>Height above ellipsoid: '+esc(Math.round(altitude(o)))+' m</div>';
 if(window.TakMapVeilPhase3I668)s+=window.TakMapVeilPhase3I668.provenance(o);
 return s+'</div>';
}
function altitudePlacement(o,localTerrainHeight){const m=altitude(o);if((o.service==='adsb'||o.service==='remote_id')&&m!==null)return {height:m,reference:'NONE',source:'reported HAE'};
 if((o.service==='adsb'||o.service==='remote_id')&&m===null)return {height:localTerrainHeight??0,reference:localTerrainHeight===null?'CLAMP_TO_GROUND':'NONE',source:'altitude unavailable'};
 if(o.service==='ais')return {height:0,reference:'CLAMP_TO_GROUND',source:'sea surface'};
 return {height:localTerrainHeight??0,reference:localTerrainHeight===null?'CLAMP_TO_GROUND':'NONE',source:'terrain surface'};
}
window.TakMapVeilVisualI670=window.TakMapVeilVisualI669=Object.freeze({version:V,COLORS,category,heading,altitude,rotor,iconSize,image,markerHtml,adsbRow,openAdsb,genericPopup,altitudePlacement});
const st=document.createElement('style');st.id='takMapVeilVisualCssI669';st.textContent='.tak-veil-icon-i669,.tak-veil-icon-i669 svg{display:block;width:100%;height:100%}.tak-veil-i665-marker{background:transparent!important;border:0!important}';
st.textContent+=' .tak-veil-aprs-wrap-i672{position:relative;display:block;width:44px;height:44px;overflow:visible}.tak-veil-aprs-icon-i672{display:grid;place-items:center;width:44px;height:44px;overflow:visible}.tak-veil-aprs-icon-i672 img{display:block;object-fit:contain;max-width:none}.tak-veil-aprs-label-i672{position:absolute;top:50%;left:44px;transform:translateY(-50%);max-width:155px;padding:2px 5px;border-radius:4px;background:rgba(18,22,27,.88);border:1px solid rgba(255,255,255,.22);color:#fff;font-size:10px;font-weight:650;line-height:1.2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;pointer-events:none;box-shadow:0 1px 4px rgba(0,0,0,.5)}';
(document.head||document.documentElement).append(st);
})();
