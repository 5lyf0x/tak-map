#!/usr/bin/env python3
"""Browser and integration contract: general map search reflects visible AIS/ADS-B markers."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
JS=ROOT/'assets/tak-map-live-search-i650.js'
GATEWAY=(ROOT/'assets/tak-map-gateway-data-v491.js').read_text()
ADSB=(ROOT/'assets/tak-map-adsb-sidebar-i610.js').read_text()
DASHBOARD=(ROOT/'tak_dashboard.py').read_text()
INSTALL=(ROOT/'install.sh').read_text()
assert 'function searchVisibleAis()' in GATEWAY and "row.source!=='ais_vessels'" in GATEWAY
assert "sourceOn('ais_vessels')" in GATEWAY and 'm.hasLayer(g)' in GATEWAY
assert 'searchVisible:searchVisibleAis,focusSearchResult:focusSearchAis' in GATEWAY
assert 'function searchVisibleAircraft()' in ADSB and 'm.hasLayer(marker)' in ADSB
assert 'if(isReplay())return []' in ADSB
assert 'searchVisible:searchVisibleAircraft' in ADSB
assert 'takMapLiveSearchLoaderI650' in DASHBOARD
assert 'tak-map-live-search-i650.js?install-check=i659' in INSTALL
assert 'install -m 0644 assets/tak-map-live-search-i650.js' in INSTALL
with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
  page=browser.new_page()
  page.set_content('<!doctype html><html><body><input id="layerSearch"><div id="searchResults"></div></body></html>')
  page.evaluate(r'''() => {
    const items = []; window.__items=items;window.__ops=[];
    window.addSearchItem = (src,kind,label,lat,lon,layer,meta)=>{
      items.push({id:src+':'+items.length,source:src,kind,label,lat,lon,layer,uid:meta.uid,type:meta.type,sourceLabel:meta.source});
    };
    window.clearSearchSource = src=>{for(let i=items.length-1;i>=0;i--)if(items[i].source===src)items.splice(i,1)};
    window.handleMapSearch = ()=>{
      const q=document.querySelector('#layerSearch').value.trim().toLowerCase();
      const out=items.filter(x=>[x.label,x.kind,x.source,x.uid,x.type].join(' ').toLowerCase().includes(q));
      document.querySelector('#searchResults').textContent=out.map(x=>x.label).join(',');
    };
    window.__data={adsb:[
      {id:'a54f01',label:'SWA3398',lat:34.1,lon:-118.1,category:'B737',terms:['SWA3398','N438WN','A54F01','Southwest Airlines'],layer:{getElement:()=>null}},
      {id:'b07001',label:'POLICE5',lat:34.2,lon:-118.2,category:'Rotor',terms:['POLICE5','N95PD'],layer:{getElement:()=>null}}
    ],ais:[
      {id:'ais-1',label:'HERMOSA',lat:33.7,lon:-118.2,category:'Passenger',terms:['HERMOSA','366652000','WCY7546','Passenger'],layer:{getElement:()=>null}},
      {id:'ais-2',label:'TUGBOAT',lat:33.8,lon:-118.3,category:'Towing',terms:['TUGBOAT','123456789','Towing'],layer:{getElement:()=>null}}
    ]};
    window.TakMapAdsbSidebarI610={searchVisible:()=>window.__data.adsb,open:(id)=>window.__ops.push(['adsb',id])};
    window.TakMapGatewayDataV476={searchVisible:()=>window.__data.ais,focusSearchResult:(id)=>window.__ops.push(['ais',id])};
  }''')
  page.add_script_tag(path=str(JS))
  page.wait_for_function("window.__items.length===4")
  assert page.evaluate("window.__items.filter(x=>x.source==='aircraft').length")==2
  assert page.evaluate("window.__items.filter(x=>x.source==='gateway-ais-live').length")==2
  for query,expected in [('3398','SWA3398'),('N438WN','SWA3398'),('A54F01','SWA3398'),('Southwest','SWA3398'),('366652000','HERMOSA'),('WCY7546','HERMOSA'),('Passenger','HERMOSA'),('123456789','TUGBOAT')]:
    page.locator('#layerSearch').fill(query)
    assert expected in page.locator('#searchResults').inner_text(),query
  page.evaluate("window.__items.find(x=>x.label==='HERMOSA').layer.openPopup()")
  page.evaluate("window.__items.find(x=>x.label==='SWA3398').layer.openPopup()")
  assert page.evaluate('window.__ops')==[['ais','ais-1'],['adsb','a54f01']]
  # Hidden, removed, and reappearing markers: sources are authoritative, no stale index.
  page.evaluate("window.__data.ais=[];window.__data.adsb=window.__data.adsb.filter(x=>x.id!=='b07001');window.TakMapLiveSearchI650.sync()")
  assert page.evaluate('window.__items.map(x=>x.label)')==['SWA3398']
  page.locator('#layerSearch').fill('HERMOSA')
  assert not page.locator('#searchResults').inner_text()
  page.evaluate("window.__data.ais=[{id:'ais-1',label:'HERMOSA',lat:33.9,lon:-118.1,category:'Passenger',terms:['366652000'],layer:{getElement:()=>null}}];window.TakMapLiveSearchI650.sync()")
  assert 'HERMOSA' in page.locator('#searchResults').inner_text()
  assert page.evaluate("window.__items.find(x=>x.label==='HERMOSA').lat")==33.9
  # no duplicate entries on unchanged cycles
  page.evaluate('window.TakMapLiveSearchI650.sync();window.TakMapLiveSearchI650.sync()')
  assert page.evaluate('window.__items.length')==2
  assert page.evaluate('window.TakMapLiveSearchI650.diagnostics().vessels')==1
  browser.close()
print('PASS: live map search integrates visible ADS-B/AIS, metadata, current positions, selection, filtering, refresh, no duplicates')
