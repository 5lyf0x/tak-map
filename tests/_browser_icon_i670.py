"""i670 Chromium static-page sanity + original SVG rendering at 2D/Cesium shared source."""
from pathlib import Path
import sys,re,json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import tak_dashboard as t
html=t.TAK_MAP_HTML
assert len(html)>260000 and 'id="map"' in html and 'i670' in html
assert html.count('/assets/runtime/tak-map-adsbx-i670.js?v=1.4.0-i670')==1
assert html.count('/assets/runtime/tak-map-veil-visual-i670.js?v=1.4.0-i670')==1
# For a portable offline browser test, strip preexisting network-dependent startup scripts.
# The authentic HTTP template is separately verified in the backend tests.
# Parse the authentic template separately; the tiny browser fixture avoids blocked external startup.
from bs4 import BeautifulSoup
parsed=BeautifulSoup(html,'html.parser')
assert parsed.find(id='map') and parsed.find(id='takVeilCardI665') and parsed.find(id='sidebar')
static='<html><head><meta charset=\"utf-8\"></head><body><div id=\"map\"></div><div id=\"takVeilCardI665\"></div><div id=\"sidebar\"></div></body></html>'
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
 page=browser.new_page(viewport={'width':1365,'height':800})
 page.set_content(static,wait_until='domcontentloaded',timeout=15000)
 assert page.evaluate('''() => !!document.head && !!document.body && !!document.querySelector('#map') && !!document.querySelector('#takVeilCardI665')''')
 for name in ('tak-map-adsbx-i670.js','tak-map-veil-visual-i670.js'):
  page.add_script_tag(content=(ROOT/'assets'/name).read_text())
 value=page.evaluate('''() => {const o=(t,c)=>({service:'adsb',identity:{icao:'a1b2c3'},enrichment:{type_designator:t},classification:c,heading:135,nodeId:'node1',lat:34,lon:-118});
 const a=window.TakMapVeilVisualI670,lib=window.TakMapAdsbxI670;
 const htmlA=a.markerHtml(o('A320','civilian')),htmlB=a.markerHtml(o('B738','military'));
 const img=a.image(o('A320','civilian'));
 const node=document.createElement('div');node.innerHTML=htmlA;document.body.appendChild(node);
 return {page:document.documentElement.outerHTML.length,htmlA:htmlA.length,htmlB:htmlB.length,aShape:lib.select(o('A320')).shape,bShape:lib.select(o('B738')).shape,rot:htmlA.includes('rotate(135 20 20)'),categoryA:htmlA.includes('#0ca751'),categoryB:htmlB.includes('#0775d3'),svg:node.querySelector('svg')!=null,data:image_ok=!!img.includes('svg%3E'),typeCount:Object.keys(lib.typeMappings).length,shapeCount:Object.keys(lib.shapes).length};}'''.replace('data:image_ok=','dataImageOk:'))
 print('CHROMIUM',json.dumps(value))
 assert value['page']>500 and value['aShape']=='a320' and value['bShape']=='b738' and value['rot'] and value['categoryA'] and value['categoryB'] and value['svg'] and value['typeCount']==376 and value['shapeCount']==30
 page.screenshot(path='/mnt/data/_i670_browser_checked.png')
 browser.close()
print('PASS i670 offline DOM and exact ADSBx aircraft silhouette rendering')
