"""Developer smoke test for i668: real HTTP response + Chromium DOM lifecycle.

Requires Playwright and local Chromium on the DEV machine, not Raspberry Pi.
The container's browser policy blocks localhost navigation, so obtain the full
live HTTP response with urllib and feed those exact bytes to Chromium. Externally
referenced runtime JS is injected separately from the shipping source.
"""
import pathlib, sys, threading, urllib.request, json
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
import tak_dashboard as t
ROOT=pathlib.Path(__file__).resolve().parents[1]
class Authed(t.Handler):
    def _tak_map_auth_ok(self): return True
    def _auth_ok(self): return True
    def _is_secure_request(self): return True
    def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),Authed)
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
try:
    with urllib.request.urlopen(f'http://127.0.0.1:{server.server_port}/tak-map',timeout=12) as response:
        body=response.read().decode()
        print('HTTP',response.status,'BYTES',len(body.encode()),'Content-Type',response.headers.get('Content-Type'))
        assert response.status==200 and 'text/html' in response.headers.get('Content-Type','')
        assert len(body)>200_000 and 'id="map"' in body and 'i668' in body
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
        page=browser.new_page(viewport={'width':1400,'height':900})
        errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.set_content(body,wait_until='domcontentloaded',timeout=30000)
        # Only the VEIL Phase2 asset is injected here; scripts are loaded from
        # network in an installed TAK Map, but the test browser is offline.
        page.evaluate('''() => {window.fetch=async (url) => {
          if (String(url).includes('/api/tak-map/veil/status'))return {
            ok:true,json:async()=>({ok:true,config:{enabled:false,port:6970,services:{adsb:true,ais:true,aprs:true,remote_id:true}},nodes:[],counts:{adsb:3,ais:2,aprs:1,remote_id:0},objectsCount:6,receiving:0,lanIPs:[]})};
          if (String(url).includes('/api/tak-map/veil/objects'))return {ok:true,json:async()=>({ok:true,objects:[]})};
          return {ok:false,status:404,json:async()=>({ok:false,error:'Offline test stub'})}
        }}''')
        page.add_script_tag(content=(ROOT/'assets/tak-map-veil-phase3-i668.js').read_text())
        page.add_script_tag(content=(ROOT/'assets/tak-map-veil-i666.js').read_text())
        page.wait_for_timeout(200)
        report=page.evaluate('''() => ({
          len:document.documentElement.outerHTML.length,
          head:!!document.head,body:!!document.body,
          map:!!document.getElementById('map'),sidebar:!!document.getElementById('sidebar'),
          mesh:!!document.getElementById('tokenMeshCardI660'),veil:!!document.getElementById('takVeilCardI665'),
          veilClient:!!window.TakMapVeilI666,
          footer:[...document.querySelectorAll('.iteration-chip,.iteration-marker')].map(e=>e.textContent),
          sourceLabels:[...document.querySelectorAll('#tvServicesI665 label')].map(el=>el.textContent.trim())
        })''')
        print('Chromium DOM',json.dumps(report,indent=2))
        assert report['len']>80000
        assert all(report[k] for k in ['head','body','map','sidebar','mesh','veil','veilClient'])
        assert report['footer'] and all('i668' in v for v in report['footer'])
        assert len(report['sourceLabels'])==4
        assert all(x in ''.join(report['sourceLabels']) for x in ['ADS-B','AIS','APRS','Remote ID'])
        for selector,card in [('#meshHeaderI663','#tokenMeshCardI660'),('#takVeilHeaderI665','#tvBodyI665')]:
            page.locator(selector).click(position={'x':8,'y':12},force=True)
            if card=='#tvBodyI665':assert page.locator(card).is_hidden()
            else:assert 'collapsed' in page.locator(card).get_attribute('class')
            page.locator(selector).click(position={'x':8,'y':12},force=True)
            if card=='#tvBodyI665':assert not page.locator(card).is_hidden()
            else:assert 'collapsed' not in page.locator(card).get_attribute('class')
        assert not any('Cannot read properties of null' in e for e in errors),errors[:3]
        page.screenshot(path='/mnt/data/_i668_browser_checked.png')
        browser.close()
finally:server.shutdown();server.server_close()
print('HTTP + CHROMIUM DOM PASS')
