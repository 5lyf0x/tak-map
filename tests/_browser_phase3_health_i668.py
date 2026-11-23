"""i668 real Chromium modal + Settings settings test with offline simulated VEIL health."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
html=(ROOT/'assets/tak-map-veil-i665.html').read_text()
html=html[:html.index('<script src=')]
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
 page=browser.new_page(viewport={'width':900,'height':820})
 page.set_content('<html><body style="background:#15212c"><div id="sidebar">'+html+'</div></body></html>')
 page.evaluate('''() => {
 window.mockEnabled=true;window.mockHealthFetches=0;
 window.node={nodeId:'VEIL-01',name:'VEIL NODE 01',host:'192.168.1.110',port:8080,apiSubscribed:true,apiState:'synced',objects:3,state:'receiving'};
 window.fetch=async(url,params) => {
  url=String(url);let data={ok:true};
  if(url.includes('/status')) data={ok:true,config:{enabled:window.mockEnabled,visible:true,mergeVeilDuplicates:true,crossSourceDedup:false,services:{adsb:true,ais:true,aprs:true,remote_id:true}},nodes:[window.node],counts:{adsb:3,ais:0,aprs:0,remote_id:0},objectsCount:3,receiving:1};
  else if(url.includes('/objects'))data={ok:true,objects:[]};
  else if(url.includes('/health')) {window.mockHealthFetches++;data={ok:true,state:'synced',observationCount:3,counts:{adsb:3},health:{veilUptimeSeconds:120,cpuTemperatureC:43.3,load:{oneMinute:0.6},memory:{availableBytes:536870912},storage:{freeBytes:10737418240},sdr:{connected:true},warnings:[]}}}
  return {ok:true,json:async()=>data};
 };
 }''')
 page.add_script_tag(content=(ROOT/'assets/tak-map-veil-phase3-i668.js').read_text())
 page.add_script_tag(content=(ROOT/'assets/tak-map-veil-i666.js').read_text())
 page.wait_for_timeout(400)
 page.locator('#tvNodesI665 button:text-is("Details")').click()
 page.wait_for_timeout(250)
 assert page.locator('#tvModalTitleI665').inner_text()=='VEIL Node Details'
 report=page.locator('#tvHealthI668').inner_text()
 assert '43.3' in report and '0.6' in report and '512' in report,report
 assert page.evaluate('window.mockHealthFetches')==1
 page.locator('#tvModalCloseI665').click()
 page.locator('#tvSettingsI665').click()
 assert page.locator('#tvMergeVeilI668').is_checked()
 assert not page.locator('#tvCrossI668').is_checked()
 page.locator('#tvModalCloseI665').click()
 page.evaluate('window.mockEnabled=false')
 page.evaluate('window.TakMapVeilI666.refresh()')
 page.wait_for_timeout(200)
 page.locator('#tvNodesI665 button:text-is("Details")').click()
 page.wait_for_timeout(100)
 assert page.evaluate('window.mockHealthFetches')==1, 'Disabled VEIL must not request health'
 print('PASS i668 Chromium health Details, sanctioned values, dedup settings, master-off health gate')
 browser.close()
