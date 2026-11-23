"""i669 Chromium mock Cesium: VEIL aircraft true HAE, ground classifications and click bridge."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
 page=browser.new_page()
 page.set_content('<html><head></head><body><div id="map"></div></body></html>')
 page.evaluate('''() => {
  window.__opened=[];
  window.TakMapAdsbSidebarI610={openExternal:(a,m)=>{window.__opened.push(a);return true}};
  const entities=new Map();window.__entities=entities;
  const view={scene:{canvas:{},pick(){return {id:entities.get(window.__pickId)}} ,requestRender(){}},dataSources:{add(s){},remove(s){} }};
  window.__view=view;window.TakMapVeilSceneI668=()=>({active:true,viewer:view});
  window.TakMapTerrainOverlayHooksI669={local:true,sampleLocal:(lat,lon)=>1280};
  window.Cesium={Color:{fromCssColorString:s=>({hex:s,withAlpha(a){return {hex:s,alpha:a}}}),WHITE:{},BLACK:{}},
    HeightReference:{NONE:'NONE',CLAMP_TO_GROUND:'CLAMP'},VerticalOrigin:{CENTER:'CENTER'},
    Cartesian3:{fromDegrees:(lon,lat,height)=>({lon,lat,height})},
    CustomDataSource:class{constructor(name){this.name=name;this.entities={getById:id=>entities.get(id),add:data=>{let e={...data};entities.set(e.id,e);return e},remove:e=>entities.delete(e.id),get values(){return [...entities.values()]}}}},
    ScreenSpaceEventHandler:class{constructor(canvas){window.__evtHandler=this}setInputAction(cb,type){this.cb=cb}destroy(){}},
    ScreenSpaceEventType:{LEFT_CLICK:'CLICK'}
  };
 }''')
 for path in ('tak-map-veil-visual-i669.js','tak-map-veil-phase3-i668.js'):
  page.add_script_tag(content=(ROOT/'assets'/path).read_text())
 vals=page.evaluate('''() => {
  const now=Date.now()/1000;
  const base={lat:34,lon:-118,timestamp:now-3,stale:now+150,freshness:'LIVE',nodeId:'veila',transport:'api'};
  const o=[
    {...base,id:'ac',service:'adsb',title:'N123',heading:135,hae:3048,classification:'military',identity:{icao:'abcd12'},canonicalKey:'adsb:icao:abcd12'},
    {...base,id:'ship',service:'ais',title:'Vessel',identity:{mmsi:'123456789'},canonicalKey:'ais:mmsi:123456789'},
    {...base,id:'station',service:'aprs',title:'WX',canonicalKey:'aprs:station:N6XXX-1'},
    {...base,id:'drone',service:'remote_id',hae:1600,title:'Drone',canonicalKey:'rid:serial:ABCDEFGH'}
  ];
  const chosen=window.TakMapVeilPhase3I668.render(o,{mergeVeilDuplicates:true,crossSourceDedup:false},()=>{});
  const keys=[...window.__entities.keys()];
  const ac=[...window.__entities.values()].find(e=>e.name==='N123');
  const ship=[...window.__entities.values()].find(e=>e.name==='Vessel');
  const station=[...window.__entities.values()].find(e=>e.name==='WX');
  const drone=[...window.__entities.values()].find(e=>e.name==='Drone');
  window.__pickId=ac.id;window.__evtHandler.cb({position:{x:1,y:2}});
  return {len:chosen.objects.length,keys,airHeight:ac.position.height,airRef:ac.billboard.heightReference,
  shipHeight:ship.position.height,shipRef:ship.billboard.heightReference,
  groundHeight:station.position.height,groundRef:station.billboard.heightReference,
  droneHeight:drone.position.height,droneRef:drone.billboard.heightReference,
  img:decodeURIComponent(ac.billboard.image),opened:window.__opened};
 }''')
 assert vals['len']==4,vals
 assert vals['airHeight']==3048 and vals['airRef']=='NONE',vals
 assert vals['droneHeight']==1600 and vals['droneRef']=='NONE',vals
 assert vals['groundHeight']==1283 and vals['groundRef']=='NONE',vals
 assert vals['shipRef']=='CLAMP',vals
 assert vals['opened'] and vals['opened'][0]['hex']=='abcd12',vals
 assert '#0775d3' in vals['img'] and 'rotate(135 20 20)' in vals['img'],vals['img'][:300]
 print('PASS Chromium VEIL Cesium: source marker categories, A3 color/heading, airborne HAE, ground DEM, AIS, shared ADS-B panel')
 browser.close()
