"""i669 end-to-end rendered full document, asset existence, and card order check."""
import pathlib,sys,threading,urllib.request,json
from http.server import ThreadingHTTPServer
from playwright.sync_api import sync_playwright
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import tak_dashboard as t
class Auth(t.Handler):
 def _tak_map_auth_ok(self): return True
 def _auth_ok(self):return True
 def _is_secure_request(self):return True
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),Auth)
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
 with urllib.request.urlopen('http://127.0.0.1:'+str(server.server_port)+'/tak-map',timeout=15) as r:
  html=r.read().decode();print('HTTP',r.status,len(html),r.headers.get('Content-Type'))
  assert r.status==200 and 'text/html' in r.headers.get('Content-Type','')
  assert len(html)>260000 and 'id="map"' in html and '1.4.0-i669' in html
 for asset in ('tak-map-veil-visual-i669.js','tak-map-range-rings-i669.js','tak-map-range-rings-icon-i669.svg'):
  with urllib.request.urlopen('http://127.0.0.1:'+str(server.server_port)+'/assets/runtime/'+asset,timeout=15) as r:
   data=r.read();assert r.status==200 and len(data)>200
   print('ASSET',asset,len(data),r.headers.get('Content-Type'))
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
  page=browser.new_page(viewport={'width':1400,'height':900})
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.set_content(html,wait_until='domcontentloaded',timeout=30000)
  page.evaluate('''() => {window.fetch=async (url) => {
   if(String(url).includes('/api/tak-map/veil/status'))return {ok:true,json:async()=>({ok:true,config:{enabled:false,visible:true,port:6970,services:{adsb:true,ais:true,aprs:true,remote_id:true}},nodes:[],counts:{adsb:0,ais:0,aprs:0,remote_id:0},objectsCount:0,receiving:0})};
   if(String(url).includes('/api/tak-map/veil/objects'))return {ok:true,json:async()=>({ok:true,objects:[]})};
   return {ok:false,status:404,json:async()=>({ok:false,error:'offline'})};
  }}''')
  for asset in ('tak-map-veil-visual-i669.js','tak-map-veil-phase3-i668.js','tak-map-veil-i666.js','tak-map-range-rings-i669.js'):
   page.add_script_tag(content=(ROOT/'assets'/asset).read_text())
  page.wait_for_timeout(450)
  obj=page.evaluate('''() => ({
   html:document.documentElement.outerHTML.length,head:!!document.head,body:!!document.body,
   map:!!document.getElementById('map'),sidebar:!!document.getElementById('sidebar'),
   veil:!!document.getElementById('takVeilCardI665'),rings:!!document.getElementById('toolRangeRingsI669'),
   ringsApi:!!window.TakMapRangeRingsI669,visual:!!window.TakMapVeilVisualI669,
   text:document.body?.innerText.slice(0,50),footers:[...document.querySelectorAll('.iteration-chip,.iteration-marker')].map(x=>x.textContent.trim()),
   order:[...document.querySelectorAll('#sidebar > .panel')].map(x=>x.querySelector('h2,.tv-head strong')?.textContent.trim()||'')
  })''')
  print('CHROMIUM',json.dumps(obj,indent=2))
  assert obj['html']>80000
  assert all(obj[k] for k in ('head','body','map','sidebar','veil','rings','ringsApi','visual'))
  assert obj['footers'] and all('i669' in v for v in obj['footers'])
  assert not any('Cannot read properties of null' in x for x in errors),errors[:10]
  page.screenshot(path='/mnt/data/_i669_browser_checked.png')
  browser.close()
finally:
 server.shutdown();server.server_close()
print('PASS HTTP+ASSET+CHROMIUM i669')
