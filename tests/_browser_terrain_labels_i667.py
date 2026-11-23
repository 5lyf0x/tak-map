"""i667 3D route-endpoint label placement and viewport suppression fixture."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'assets/tak-map-core-i553.js').read_text()
start=s.index('// i667: Saved route endpoint labels in Cesium')
end=s.index('function terrainBillboardImage(o)',start)
methods=s[start:end]
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
 page=browser.new_page(viewport={'width':900,'height':600})
 page.set_content('''<html><body style="margin:0;background:#17212a"><div id="terrain3dCanvas" style="width:900px;height:600px;position:relative"></div></body></html>''')
 page.evaluate('''() => {
  window.terrain3DActive=true;
  window.terrain3DViewer={camera:{positionCartographic:{height:2000}},scene:{}};
  window.Cesium={Cartesian3:{fromDegrees:(x,y,h=0)=>({x,y,h})},SceneTransforms:{wgs84ToWindowCoordinates:(_sc,p)=>({x:450+p.x*80,y:300+p.y*80})}};
  window.testZoom=15;window.map={getZoom:()=>window.testZoom};
  window.terrainCoordinatesI667=c=>c;
  window.routeCoords=o=>o.coords;
  window.terrainElevationI667=()=>null;
 }''')
 page.add_script_tag(content=methods)
 result=page.evaluate('''() => {
  terrainSavedRouteAddI667({name:'Yumtheska Camp 1',coords:[[0,-.5],[0,0]]});
  terrainDrawSavedLabelsI667(true);
  const root=document.getElementById('takTerrainSavedLabelsI667');
  const label=root.querySelector('.tak-route-total-chip-i667');
  const line=root.querySelector('svg line');
  const shown=label.style.display!=='none'&&label.textContent.includes('Yumtheska Camp 1')&&label.textContent.includes('mi')&&line.getAttribute('display')!=='none';
  const noArrow=!root.innerHTML.includes('marker-end')&&!root.querySelector('svg marker');
  terrainSavedRoutesI667[0].end=[0,20];terrainDrawSavedLabelsI667(true);
  const offscreenHidden=label.style.display==='none'&&line.getAttribute('display')==='none';
  window.testZoom=10;terrainDrawSavedLabelsI667(true);
  return {shown,noArrow,offscreenHidden,zoom10Hidden:root.style.display==='none'};
 }''')
 assert all(result.values()),result
 print('i667 3D route labels viewport/zoom/plain leader browser PASS',result)
 browser.close()
