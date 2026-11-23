"""i684 route details: no Points row, all notes fields on separate lines, HTML-safe."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 try:
  page=browser.new_page(viewport={'width':1200,'height':800})
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.set_content('<html><body style="margin:0"><div id="map" style="height:800px;width:1200px"></div><div id="sidebar"></div></body></html>')
  page.evaluate('''() => {
    window.map={getContainer:()=>document.getElementById('map'),getZoom:()=>12,panTo:()=>{},getSize:()=>({x:1200,y:800}),getBounds:()=>({contains:()=>true}),on:()=>{}};
    window.layerPopupForObject=()=>`<div class="tak-v322-popup"><div class="tak-v322-table">
      <div class="tak-v322-row"><b>Category</b><span>General</span></div>
      <div class="tak-v322-row"><b>Points</b><span>1625</span></div>
      <div class="tak-v322-row"><b>Length</b><span>33.76 mi</span></div>
      <div class="tak-v322-row"><b>Notes</b><span>Method: Driving Direction: Infil Route Type: Primary Order: Ascending Check Points Prefix: CP Line Style: solid Notes: rocky &lt;pass&gt; trail</span></div>
      </div></div>`;
  }''')
  page.add_script_tag(path=str(ROOT/'assets/tak-map-context-sidebar-i572.js'))
  page.evaluate('''() => TakMapContextSidebarI572.showObject({kind:'route',name:'Anza - Fish Creek',coords:[[33,-116],[33.1,-116.1]]},'local',null,false)''')
  rows=page.locator('.tak-v322-row')
  labels=rows.locator('b').all_inner_texts()
  assert 'Points' not in labels,labels
  note=rows.filter(has=page.locator('b:text-is("Notes")')).locator('span')
  lines=note.locator('div').all_inner_texts()
  assert lines==['Method: Driving','Direction: Infil','Route Type: Primary','Order: Ascending Check Points','Prefix: CP','Line Style: solid','Notes: rocky <pass> trail'],lines
  assert note.locator('pass').count()==0
  assert not errors,errors
  print('PASS route Points removed from display without dropping route data')
  print('PASS 7 individual safe route property/note lines')
 finally:browser.close()
