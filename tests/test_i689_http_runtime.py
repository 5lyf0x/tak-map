"""i689 real HTTP-handler route regression, authenticated assets and icon API fixture."""
import concurrent.futures,http.client,json,threading,unittest,urllib.parse
from http.server import ThreadingHTTPServer
import tak_dashboard as app
from pathlib import Path

class TestingHandler(app.Handler):
 def _tak_map_auth_ok(self):return True
 def log_message(self,*args):pass

class I689HTTP(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.server=ThreadingHTTPServer(('127.0.0.1',0),TestingHandler)
  cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
  cls.thread.start()
 @classmethod
 def tearDownClass(cls):
  cls.server.shutdown();cls.server.server_close();cls.thread.join(3)
 def get(self,path,method='GET'):
  conn=http.client.HTTPConnection('127.0.0.1',self.server.server_address[1],timeout=10)
  try:
   conn.request(method,path);r=conn.getresponse()
   return r.status,dict(r.getheaders()),r.read()
  finally:conn.close()
 def test_script_and_stylesheet_real_http_get_head(self):
  for name,mime in [('tak-map-sidebar-order-i684.js','application/javascript'),('tak-map-sidebar-uniform-i684.css','text/css'),('tak-map-infrastructure-i689.js','application/javascript'),('tak-map-infrastructure-i689.css','text/css')]:
   body=(Path(app.__file__).parent/'assets'/name).read_bytes()
   for method in ('GET','HEAD'):
    with self.subTest(name=name,method=method):
     status,headers,data=self.get('/assets/runtime/'+name+'?v=1.4.0-i690',method)
     self.assertEqual(status,200);self.assertTrue(headers['Content-Type'].startswith(mime));self.assertEqual(int(headers['Content-Length']),len(body))
     self.assertEqual(data,body if method=='GET' else b'')
 def test_old_url_and_historical_route(self):
  for path in ('/assets/tak-map-sidebar-order-i684.js','/assets/runtime/tak-map-i636.js'):
   s,h,data=self.get(path);self.assertEqual(s,200,path);self.assertIn('javascript',h['Content-Type'].lower());self.assertNotIn(b'<!doctype',data[:100].lower())
 def test_no_html_on_missing_sidebar_asset(self):
  status,h,b=self.get('/assets/runtime/tak-map-sidebar-missing.js');self.assertEqual(status,404);self.assertNotIn(b'<!doctype html',b)
 def test_actual_bundle_html_scripts(self):
  status,h,body=self.get('/tak-map');self.assertEqual(status,200)
  for name in ('tak-map-sidebar-order-i684.js','tak-map-sidebar-uniform-i684.css','tak-map-infrastructure-i689.js'):
   self.assertIn(('/assets/runtime/'+name+'?v=1.4.0-i690').encode(),body)
 def test_icon_service_known_icon(self):
  registry=app._i555_registry_load();root=app._i555_registry_file().parent.resolve();sample=None
  for path,row in registry['by_path'].items():
   candidate=(root/row.get('internal_path','')).resolve()
   if candidate.is_file() and str(candidate).startswith(str(root)+'/'):
    sample=path;break
  self.assertIsNotNone(sample)
  route='/api/tak-map/icon-registry/icon?path='+urllib.parse.quote(sample,safe='')
  status,headers,body=self.get(route);self.assertEqual(status,200);self.assertGreater(len(body),40)
  self.assertIn('image/',headers.get('Content-Type',''))
  with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
   futures=[pool.submit(self.get,route) for _ in range(12)]
   self.assertTrue(all(status==200 for status,_,_ in (f.result() for f in futures)))
if __name__=='__main__':unittest.main()
