"""Authenticated i690 asset, API, identity and LAN semantics checks."""
import http.client,threading,unittest
from pathlib import Path
from http.server import ThreadingHTTPServer
import tak_dashboard as app
ROOT=Path(app.__file__).resolve().parent
class Serving(app.Handler):
 def _tak_map_auth_ok(self):return True
 def log_message(self,*args):pass
class Deny(app.Handler):
 def _tak_map_auth_ok(self):return False
 def log_message(self,*args):pass
class HTTP(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.server=ThreadingHTTPServer(('127.0.0.1',0),Serving)
  cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
 @classmethod
 def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.thread.join(3)
 def get(self,path,method='GET'):
  c=http.client.HTTPConnection('127.0.0.1',self.server.server_address[1],timeout=15)
  try:
   c.request(method,path);r=c.getresponse();return r.status,dict(r.getheaders()),r.read()
  finally:c.close()
 def test_assets_get_head(self):
  for suffix,mime in [('tak-map-status-strip-i690.js','application/javascript'),('tak-map-status-strip-i690.css','text/css')]:
   content=(ROOT/'assets'/suffix).read_bytes()
   for method in ('GET','HEAD'):
    with self.subTest(path=suffix,method=method):
     status,h,body=self.get('/assets/runtime/'+suffix+'?v=1.4.0-i690',method)
     self.assertEqual(status,200);self.assertTrue(h['Content-Type'].startswith(mime));self.assertEqual(int(h['Content-Length']),len(content));self.assertEqual(body,content if method=='GET' else b'')
 def test_api(self):
  status,h,body=self.get('/api/tak-map/status-network-i690')
  import json
  result=json.loads(body);self.assertEqual(status,200);self.assertTrue(result['ok']);self.assertIn(result['lan']['state'],('Unknown','Offline','Available'))
  self.assertIsInstance(result['tak']['enabled'],bool);self.assertIsInstance(result['tak']['configured'],bool)
 def test_page(self):
  s,h,data=self.get('/tak-map');self.assertEqual(s,200)
  self.assertIn(b'/assets/runtime/tak-map-status-strip-i690.js?v=1.4.0-i690',data)
  self.assertIn(b'/assets/runtime/tak-map-status-strip-i690.css?v=1.4.0-i690',data)
  self.assertIn(b'tak-map-infrastructure-i689.js?v=1.4.0-i690',data)
  self.assertIn(b'tak-map-sidebar-order-i684.js?v=1.4.0-i690',data)
 def test_unauthorized_i690_endpoint(self):
  class Fake:
   path='/api/tak-map/status-network-i690'
   def _tak_map_auth_ok(self):return False
   def _require_tak_map_login(self):self.denied=True
  f=Fake();app._i690_get(f);self.assertTrue(f.denied)
if __name__=='__main__':unittest.main()
