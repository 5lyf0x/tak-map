"""Chromium interactive tests: range rings modal, independent centers/sets, persisted names."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
 page=browser.new_page(viewport={'width':1024,'height':800})
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.set_content('''<!doctype html><html><head></head><body style="background:#102330;color:white;font-family:Arial">
 <div id="floatingMapToolbar" style="display:flex;gap:5px"><button id="toolMove" class="tool-btn">Pan</button><button id="toolCoords">Coordinates</button></div>
 <div id="map" style="height:650px;">Simulated Leaflet map</div></body></html>''')
 page.evaluate('''() => {
  const store=new Map();
  Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>store.has(k)?store.get(k):null,setItem:(k,v)=>store.set(k,String(v)),removeItem:k=>store.delete(k)}});
  window.__mockMarkers=[];window.__mockLayers=[];
  window.map={getContainer:()=>document.getElementById('map'),getCenter:()=>({lat:34, lng:-118}),
    on(){},off(){},once(){},addLayer(x){window.__mockLayers.push(x)},removeLayer(x){window.__mockLayers=window.__mockLayers.filter(z=>z!==x)}};
  function marker(pos, opts){const out={pos,opts,handler:null,on(evt,fn){if(evt==='click')this.handler=fn;return this},addTo(g){g.items.push(this);window.__mockMarkers.push(this);return this}};return out}
  window.L={layerGroup:()=>({items:[],addTo(map){map.addLayer(this);return this}}),polyline:(pts,opts)=>({pts,opts,addTo(g){g.items.push(this);return this}}),
  marker,divIcon:opt=>opt,DomEvent:{stopPropagation(){}}};
 }''')
 page.add_script_tag(content=(ROOT/'assets/tak-map-range-rings-i669.js').read_text())
 assert page.locator('#toolRangeRingsI669').count()==1
 order=page.eval_on_selector_all('#floatingMapToolbar > *','e=>e.map(x=>x.id)')
 assert order==['toolMove','toolRangeRingsI669','toolCoords'],order
 page.locator('#toolRangeRingsI669').click()
 assert page.locator('#takRangeModalI669').is_visible()
 styles=page.locator('#trStyleI669 option').all_text_contents();assert styles==['Solid','Dashed'],styles
 assert page.locator('#trClearI669').is_hidden()
 page.locator('#trNameI669').fill('Base Camp')
 page.locator('#trIntervalI669').fill('2')
 page.locator('#trUnitsI669').select_option('km')
 page.locator('#trCountI669').fill('3')
 page.locator('#trRememberI669').check()
 page.locator('#trApplyI669').click()
 s=page.evaluate('window.TakMapRangeRingsI669.sets')
 assert len(s)==1 and s[0]['name']=='Base Camp' and s[0]['remember'] and s[0]['interval']==2,s
 persisted=page.evaluate("JSON.parse(localStorage.getItem('takMap.rangeRings.i669.v1'))")
 assert len(persisted)==1 and persisted[0]['name']=='Base Camp',persisted
 page.locator('#toolRangeRingsI669').click()
 page.locator('#trNameI669').fill('Overwatch')
 page.locator('#trRememberI669').uncheck()
 page.locator('#trApplyI669').click()
 assert len(page.evaluate('window.TakMapRangeRingsI669.sets'))==2
 assert len(page.evaluate("JSON.parse(localStorage.getItem('takMap.rangeRings.i669.v1'))"))==1
 # Reopen only by clicking a center marker (not circumference) -- exercise marker event directly.
 count=page.evaluate('''() => {
  const center=window.__mockMarkers.find(m=>m.opts.title==='Base Camp' && m.handler);
  if(!center)throw Error('Base Camp center marker missing');
  center.handler({originalEvent:{}});return document.querySelector('#trNameI669').value;
 }''')
 assert count=='Base Camp',count
 assert page.locator('#trClearI669').is_visible()
 page.locator('#trNameI669').fill('Base Camp Updated')
 page.locator('#trApplyI669').click()
 assert 'Base Camp Updated' in [x['name'] for x in page.evaluate('window.TakMapRangeRingsI669.sets')]
 page.evaluate('''() => {
  const center=window.__mockMarkers.filter(m=>m.opts.title==='Overwatch' && m.handler).at(-1);
  if(!center)throw Error('Overwatch center missing');center.handler({});
 }''')
 assert page.locator('#trNameI669').input_value()=='Overwatch'
 page.screenshot(path='/mnt/data/_i669_range_rings_modal_checked.png')
 page.locator('#trClearI669').click()
 s=page.evaluate('window.TakMapRangeRingsI669.sets');assert len(s)==1 and s[0]['name']=='Base Camp Updated',s
 assert len(page.evaluate("JSON.parse(localStorage.getItem('takMap.rangeRings.i669.v1'))"))==1
 assert not errors,errors
 print('PASS Chromium Range Rings: toolbar order, new sets, edit center, labels, clear targeted, persistence, Solid/Dashed only')
 browser.close()
