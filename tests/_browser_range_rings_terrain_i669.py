"""Browser-mocked Cesium rings: local DEM drape, streamed terrain, clicked center edit."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
 page=browser.new_page();page.set_content('<html><head></head><body><div id="floatingMapToolbar"><button id="toolMove">Pan</button><button id="toolCoords">Coordinates</button></div></body></html>')
 page.evaluate('''() => {
  const list=new Map();window.__list=list;
  const viewer={scene:{canvas:{},pick:()=>({id:list.get(window.__pick)}),requestRender(){}},dataSources:{add(s){},remove(s){}},
   camera:{getPickRay(){return {}},positionWC:{} }};
  viewer.scene.globe={pick:()=>({})};window.__view=viewer;
  window.TakMapVeilSceneI668=()=>({active:true,viewer});
  window.TakMapTerrainOverlayHooksI669={local:true,sampleLocal:()=>650};
  window.Cesium={
   Math:{toDegrees:x=>x},Cartographic:{fromCartesian:()=>({latitude:34,longitude:-118})},
   Cartesian2:class{constructor(x,y){this.x=x;this.y=y}},Cartesian3:{fromDegrees:(lon,lat,height)=>({lon,lat,height})},
   Color:{fromCssColorString:x=>({name:x,withAlpha:alpha=>({name:x,alpha})}),WHITE:'white'},
   ArcType:{GEODESIC:'GEODESIC'},LabelStyle:{FILL_AND_OUTLINE:'FILL_AND_OUTLINE'},HeightReference:{NONE:'NONE',CLAMP_TO_GROUND:'CLAMP'},VerticalOrigin:{CENTER:'CENTER',BOTTOM:'BOTTOM'},
   PolylineDashMaterialProperty:class{constructor(o){this.options=o}},
   CustomDataSource:class{constructor(){this.entities={add(o){let e={...o};list.set(e.id,e);return e},removeAll(){list.clear()},get values(){return [...list.values()]}}}},
   ScreenSpaceEventType:{LEFT_CLICK:'click'},
   ScreenSpaceEventHandler:class{constructor(){window.__handler=this}setInputAction(cb){this.onClick=cb}destroy(){}}
  }
 }''')
 page.add_script_tag(content=(ROOT/'assets/tak-map-range-rings-i669.js').read_text())
 page.locator('#toolRangeRingsI669').click()
 page.locator('#trNameI669').fill('Terrain Camp')
 page.locator('#trCountI669').fill('3')
 page.locator('#trStyleI669').select_option('dashed')
 page.locator('#trApplyI669').click()
 data=page.evaluate('''() => {
  const all=[...window.__list.values()];return {size:all.length,rings:all.filter(x=>x.polyline).map(x=>({clamped:x.polyline.clampToGround,heights:x.polyline.positions.map(p=>p.height)})),center:all.find(x=>x.id.endsWith(':center')).label.text,sourceActive:window.TakMapRangeRingsI669.diagnostics().terrain}
 }''')
 assert data['size']==7 and data['center']=='Terrain Camp' and data['sourceActive'],data
 assert all(not r['clamped'] and min(r['heights'])==652 and max(r['heights'])==652 for r in data['rings']),data
 page.evaluate('''() => {window.__pick=[...window.__list.keys()].find(x=>x.endsWith(':center'));window.__handler.onClick({position:{}})}''')
 assert page.locator('#takRangeModalI669').is_visible()
 assert page.locator('#trNameI669').input_value()=='Terrain Camp'
 page.locator('#trCancelI669').click()
 page.evaluate('window.TakMapTerrainOverlayHooksI669.local=false')
 page.wait_for_timeout(1900)
 stat=page.evaluate('''() => [...window.__list.values()].filter(x=>x.polyline).map(x=>x.polyline.clampToGround)''')
 assert len(stat)==3 and all(stat),stat
 print('PASS Chromium range rings Cesium: 3x DEM-draped lines, center click modal, streamed terrain ground clamp')
 browser.close()
