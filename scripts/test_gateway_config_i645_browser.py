from pathlib import Path
import json,threading
from http.server import HTTPServer,BaseHTTPRequestHandler
from playwright.sync_api import sync_playwright
JS=str(Path(__file__).resolve().parents[1]/'assets'/'tak-map-gateway-config-i645.js')
HTML='''<!doctype html><html><head></head><body><div id="sidebar"><div id="gatewayDataPanelV476" class="gateway-data-v491"><div class="gateway-status-row"><div id="gatewayDataStatusV476"><span></span><span>Connecting</span></div><button id="gatewayDataRefreshV476" class="layer-button">Refresh</button></div></div></div></body></html>'''
settings={'ok':True,'host':'10.10.10.101','port':8090,'protocol':'http','auth_mode':'none','verify_tls':True,'ca_cert_path':'','client_cert_path':'','client_key_path':'','api_url':'http://10.10.10.101:8090/api/external-sources/v1','configuration_error':''}
class Host(BaseHTTPRequestHandler):
 def do_GET(self):
  b=HTML.encode();self.send_response(200);self.send_header('Content-Type','text/html');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
 def log_message(self,*a):pass
http=HTTPServer(('127.0.0.1',0),Host);threading.Thread(target=http.serve_forever,daemon=True).start()
ORIGIN='http://127.0.0.1:'+str(http.server_port)
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
 page=browser.new_page()
 posts=[]
 def handler(route):
  url=route.request.url
  if url.endswith('/api/tak-map/gateway-data/settings') and route.request.method=='GET':
   return route.fulfill(status=200,content_type='application/json',body=json.dumps(settings))
  if '/api/tak-map/gateway-data/settings' in url and route.request.method=='POST':
   payload=route.request.post_data_json;posts.append((url,payload))
   result={'ok':True,'message':'Gateway Data health and capabilities are reachable.'}
   return route.fulfill(status=200,content_type='application/json',body=json.dumps(result))
  return route.fulfill(status=200,content_type='text/html',body=HTML)
 page.expose_binding('recordGwPost',lambda source,url,body:posts.append((url,json.loads(body))))
 page.set_content(HTML)
 page.evaluate('''(settings)=>{window.__gwPosts=[];window.fetch=async (url,options={})=>{if(options.method==='POST'){await window.recordGwPost(url,options.body);window.__gwPosts.push([url,JSON.parse(options.body)]);return {ok:true,status:200,json:async()=>({ok:true,message:'Gateway Data health and capabilities are reachable.'})}}return {ok:true,status:200,json:async()=>settings}}}''',settings)
 page.add_script_tag(path=JS)
 page.wait_for_selector('#gatewayConfigButtonI645')
 assert page.locator('#gatewayConfigButtonI645').inner_text()=='Configure'
 assert page.locator('#gatewayConfigActionGroupI645').locator('button').all_inner_texts()==['Configure','Refresh']
 page.locator('#gatewayConfigButtonI645').click()
 page.wait_for_selector('#takGatewayConfigModalI645:not([hidden])')
 assert page.locator('#gwcHostI645').input_value()=='10.10.10.101'
 assert page.locator('#gwcAuthI645').input_value()=='none'
 assert not page.locator('#gwcCaBlockI645').is_visible()
 page.locator('#gwcProtocolI645').select_option('https')
 assert page.locator('#gwcPortI645').input_value()=='9443'
 assert page.locator('#gwcVerifyI645').is_checked()
 assert page.locator('#gwcVerifyI645').is_disabled()
 assert page.locator('#gwcCaBlockI645').is_visible()
 page.locator('#gwcProtocolI645').select_option('http')
 page.locator('#gwcTestI645').click()
 page.wait_for_function("document.querySelector('#gwcStatusI645').textContent.includes('reachable')")
 assert page.evaluate('window.__gwPosts.at(-1)[1].protocol')=='http' and page.evaluate('window.__gwPosts.at(-1)[1].auth_mode')=='none'
 page.keyboard.press('Escape')
 assert page.locator('#takGatewayConfigModalI645').is_hidden()
 page.locator('#gatewayConfigButtonI645').click()
 page.wait_for_selector('#gwcHostI645')
 page.locator('#gwcSaveI645').click()
 page.wait_for_timeout(300)
 assert any(not url.endswith('/test') for url,_ in posts),posts
 print('PASS: Chromium modal opens/closes, adjacent Configure/Refresh, populated settings, protocol/port/TLS behavior, Test and Save requests')
 browser.close()
http.shutdown()
