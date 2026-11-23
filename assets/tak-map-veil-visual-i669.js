/* TAK Map i669: shared VEIL visual resolver, A3 ADS-B target ring and ADS-B panel adapter. */
(()=>{'use strict';
const V='1.4.0-i669';
const COLORS={military:'#0775d3',civilian:'#0ca751',government:'#7d009a',unknown:'#b4ab25'};
const TYPE_IDS={adsb:'ADS-B',ais:'AIS',aprs:'APRS',remote_id:'Remote ID'};
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function heading(o){const n=Number(o?.heading);return o?.heading===null||o?.heading===undefined||o?.heading===''||!Number.isFinite(n)?null:((n%360)+360)%360}
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
function planeShape(o){return rotor(o)?'<g fill="#f5f9fd"><rect x="18.4" y="10" width="3.2" height="20" rx="1.3"/><rect x="10" y="17.6" width="20" height="4.8" rx="2"/><rect x="11" y="29" width="18" height="1.8" rx=".8"/></g>':
 '<path d="M20 6.5c1.6 0 2.15 2.2 2.15 4.2v5.1l8.2 6.1v3.2l-8.2-2.6v6.4l3.3 2.25v2.25L20 30.8l-5.45 2.6v-2.25l3.3-2.25v-6.4l-8.2 2.6v-3.2l8.2-6.1v-5.1c0-2 .55-4.2 2.15-4.2Z" fill="#f5f9fd"/>'}
function targetSvg(o){const col=COLORS[category(o)],degree=heading(o)??0;
 // A3: eight independent arc sectors. Outer ring does NOT rotate; aircraft glyph does.
 const arcs=Array.from({length:8},(_,i)=>{const a=(i*45+6)*Math.PI/180,b=(i*45+39)*Math.PI/180;
  const x1=(20+16*Math.cos(a)).toFixed(2),y1=(20+16*Math.sin(a)).toFixed(2),x2=(20+16*Math.cos(b)).toFixed(2),y2=(20+16*Math.sin(b)).toFixed(2);
  return `<path d="M${x1} ${y1} A16 16 0 0 1 ${x2} ${y2}" fill="none" stroke="${col}" stroke-width="3" stroke-linecap="round"/>`}).join('');
 return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40" role="img" aria-label="${category(o)} aircraft"><circle cx="20" cy="20" r="13" fill="#0b2030" fill-opacity=".87"/>${arcs}<g transform="rotate(${degree} 20 20)">${planeShape(o)}</g></svg>`;
}
function glyphSvg(o){if(o.service==='adsb')return targetSvg(o);const kind=o.service;
 const svg=kind==='ais'?'<path d="M12 21h16l-3 9H15l-3-9m8-14v14M14 15h12l-3-6h-6l-3 6"/>':kind==='remote_id'?'<path d="M14 15l-5-5m17 5 5-5M14 25l-5 5m17-5 5 5M16 16h8v8h-8z"/><circle cx="9" cy="10" r="3"/><circle cx="31" cy="10" r="3"/><circle cx="9" cy="30" r="3"/><circle cx="31" cy="30" r="3"/>':'<path d="M17 30V15h6v15M12 30h16M10 13c6-7 14-7 20 0M14 16c4-4 8-4 12 0"/>';
 return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" width="40" height="40"><circle cx="20" cy="20" r="17" fill="#122535" fill-opacity=".92" stroke="#c4d5dd" stroke-width="1.8"/><g stroke="#f2f6fa" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" fill="none">${svg}</g></svg>`;
}
function image(o){return 'data:image/svg+xml;charset=utf-8,'+encodeURIComponent(glyphSvg(o))}
function markerHtml(o){return `<span class="tak-veil-icon-i669">${glyphSvg(o)}</span>`}
function adsbRow(o){const ident=o.identity||{},en=o.enrichment||{},key=String(o.canonicalKey||'');const icao=String(ident.icao||ident.icao24||ident.hex||(key.startsWith('adsb:icao:')?key.slice(10):'')).toLowerCase();const h=heading(o),alt=altitude(o);
 const id='veil-'+(String(o.__veilKey||o.id||'').replace(/[^a-zA-Z0-9_-]/g,'-')).slice(0,140);
 const speed=Number(o.speedMps);
 return {id,hex:/^[a-f0-9]{6}$/.test(icao)?icao:'',icao:/^[a-f0-9]{6}$/.test(icao)?icao:'',callsign:String(ident.callsign||o.title||'').slice(0,60),
  flight:String(ident.flight||o.title||'').slice(0,60),lat:Number(o.lat),lon:Number(o.lon),track_deg:h,heading:h,
  altitude_ft:alt===null?undefined:alt*3.280839895,altitude_ref:alt===null?'not supplied':'HAE (WGS84 ellipsoid)',
  speed_kt:Number.isFinite(speed)&&o.speedMps!==null&&o.speedMps!==''?speed*1.943844:undefined,
  category_class:category(o),aircraft_class:category(o),is_helo:rotor(o),type:String(en.aircraft_type||en.type||''),
  aircraft_type:String(en.aircraft_type||en.type||''),description:String(en.description||''),
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
window.TakMapVeilVisualI669=Object.freeze({version:V,COLORS,category,heading,altitude,rotor,image,markerHtml,adsbRow,openAdsb,genericPopup,altitudePlacement});
const st=document.createElement('style');st.id='takMapVeilVisualCssI669';st.textContent='.tak-veil-icon-i669,.tak-veil-icon-i669 svg{display:block;width:36px;height:36px}.tak-veil-i665-marker{background:transparent!important;border:0!important}';
(document.head||document.documentElement).append(st);
})();
