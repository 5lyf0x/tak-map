from pathlib import Path
from playwright.sync_api import sync_playwright
import json
ROOT=Path(__file__).resolve().parents[1]
js=(ROOT/'assets/tak-map-gateway-data-v491.js').read_text()
stop=js.index('setInterval(()=>{const r=replayActive()')
script=js[:stop]+'\nwindow.__i664Test={popup,aisDetailsHtml,css};\n})(window,document);'
mesh=(ROOT/'assets/tak-map-token-mesh-i664.html').read_text()
# Exclude the interactive backend JS from rendering until the test installs a response mock.
mesh_no_js=mesh.split('<script id="meshSlateScriptI662">',1)[0]
html='''<!doctype html><html><head><meta charset="UTF-8"><style>
body{margin:0;background:#0a121a;color:#e5eaed;font-family:Arial,sans-serif}
.panel{border-radius:14px;border:1px solid #344956}
.gateway-data-readonly-i615{width:355px;margin:16px;background:#10191f;border:1px solid #344451;border-radius:12px}
.gateway-context-i617 .kvp{display:grid;grid-template-columns:112px minmax(0,1fr);padding:8px 14px 14px;gap:0}
.gateway-context-i617 .kvp b,.gateway-context-i617 .kvp span{box-sizing:border-box;min-width:0;padding:8px 7px;border-bottom:1px solid #32424a;font-size:11px;line-height:1.42;overflow-wrap:anywhere;white-space:normal}
.gateway-context-i617 .kvp b{color:#9faab3;text-transform:uppercase}
.gateway-context-i617 .kvp span{color:#edf1f4}
</style></head><body><div id="mesh" style="width:350px;margin:15px"></div><div class="gateway-data-readonly-i615" id="popup"></div></body></html>'''
fixture={
 'id':'ais-367492920','properties':{
  'source':'ais_vessels','title':'WYATT M','event_time':'2026-11-07T08:00:00Z',
  'metadata':{'vessel_name':'WYATT M','mmsi':'367492920','symbol':'Merchant','speed_kn':9.4,'course_deg':124},
  'remarks':'AIS Vessel Name: WYATT M MMSI: 367492920 Vessel Type: Merchant Speed: 9.4 kn Course: 124° Heading: 122° Navigation Status: 15 Observed: 2026-11-07 08:00:40.336376043 +0000 UTC Distance: 29.8 mi Source: AISstream.io'}}
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
 page=b.new_page(viewport={'width':420,'height':1150},device_scale_factor=1)
 errors=[]
 page.on('pageerror',lambda x:errors.append(str(x)))
 page.set_content(html)
 page.add_script_tag(content=script)
 page.evaluate('(f)=>{window.__i664Test.css();document.querySelector("#popup").innerHTML=window.__i664Test.popup(f)}',fixture)
 labels=page.locator('#popup .gateway-ais-details-label-i664')
 values=page.locator('#popup .gateway-ais-details-value-i664')
 assert labels.count()==10,(labels.count(),labels.all_text_contents())
 assert values.count()==10,(values.count(),values.all_inner_texts())
 assert labels.all_text_contents()==['AIS Vessel Name','MMSI','Vessel Type','Speed','Course','Heading','Navigation Status','Observed','Distance','Source'],labels.all_text_contents()
 assert values.all_inner_texts()==['WYATT M','367492920','Merchant','9.4 kn','124°','122°','15','2026-11-07 08:00:40.336376043 +0000 UTC','29.8 mi','AISstream.io'],values.all_inner_texts()
 heading=page.locator('.gateway-ais-details-heading-i664')
 assert heading.count()==1
 assert heading.evaluate('(e)=>getComputedStyle(e).gridColumnStart')=='1'
 assert heading.evaluate('(e)=>getComputedStyle(e).gridColumnEnd')=='-1'
 key=labels.nth(0).bounding_box();val=values.nth(0).bounding_box()
 assert abs(key['y']-val['y'])<2 and val['x']>key['x']+80,(key,val)
 for i in range(1,labels.count()):
  prev=labels.nth(i-1).bounding_box();cur=labels.nth(i).bounding_box()
  assert cur['y']>prev['y'],(i,prev,cur)
 # Verify no raw HTML injection via untrusted AIS remarks.
 fixture['properties']['remarks']='AIS Vessel Name: <img src=x onerror=alert(1)> MMSI: 367492920 Source: AISstream.io'
 page.evaluate('(f)=>{document.querySelector("#popup").innerHTML=window.__i664Test.popup(f)}',fixture)
 assert page.locator('#popup img').count()==0
 assert '<img' in page.locator('.gateway-ais-details-value-i664').first.inner_text()
 # A non-AIS source still uses existing Details renderer.
 fixture['properties']['source']='nasa_firms'
 fixture['properties']['remarks']='Unchanged generic details'
 page.evaluate('(f)=>{document.querySelector("#popup").innerHTML=window.__i664Test.popup(f)}',fixture)
 assert page.locator('#popup .gateway-ais-details-label-i664').count()==0
 assert page.locator('#popup .gateway-popup-remarks-v491').count()==1
 # Real CSS switch states in browser.
 page.locator('#mesh').evaluate('(e,markup)=>e.innerHTML=markup',mesh_no_js)
 on=page.locator('#meshSwitchI662')
 knob=page.locator('#meshSwitchI662 .ms-knob')
 assert on.evaluate('(e)=>getComputedStyle(e).width')=='38px'
 assert on.evaluate('(e)=>getComputedStyle(e).height')=='20px'
 assert knob.evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgb(57, 217, 138)',knob.evaluate('(e)=>getComputedStyle(e).backgroundColor')
 assert page.locator('#tokenMeshStateI660').evaluate('(e)=>getComputedStyle(e,"::before").content')=='none'
 on.evaluate('(e)=>e.setAttribute("aria-checked","false")')
 page.wait_for_timeout(240)
 assert knob.evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgb(145, 162, 173)'
 assert not errors,errors
 print('PASS: actual AIS popup function creates full-width Details heading + 10 aligned two-column rows, escapes malicious HTML; non-AIS unchanged; green/gray Mesh switch and no status dot')
 b.close()
