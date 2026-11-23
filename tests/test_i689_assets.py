"""i689 focused HTTP-handler checks: true JS/CSS bytes, auth, GET/HEAD, no HTML fallback."""
import ast,io,unittest
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'tak_dashboard.py').read_text()
module=ast.parse(source)
fn=next(x for x in module.body if isinstance(x,ast.FunctionDef) and x.name=='_i689_get')
static={
'/assets/runtime/tak-map-sidebar-order-i684.js':('tak-map-sidebar-order-i684.js','application/javascript; charset=utf-8'),
'/assets/runtime/tak-map-sidebar-uniform-i684.css':('tak-map-sidebar-uniform-i684.css','text/css; charset=utf-8'),
'/assets/tak-map-sidebar-order-i684.js':('tak-map-sidebar-order-i684.js','application/javascript; charset=utf-8'),
'/assets/tak-map-sidebar-uniform-i684.css':('tak-map-sidebar-uniform-i684.css','text/css; charset=utf-8'),
'/assets/runtime/tak-map-infrastructure-i689.js':('tak-map-infrastructure-i689.js','application/javascript; charset=utf-8'),
'/assets/runtime/tak-map-infrastructure-i689.css':('tak-map-infrastructure-i689.css','text/css; charset=utf-8')}
ns={'Path':Path,'urlparse':urlparse,'__file__':str(ROOT/'tak_dashboard.py'),'_I689_STATIC_ASSETS':static,'_I689_GET_PREVIOUS':lambda self:setattr(self,'previous',True)}
exec(compile(ast.Module(body=[fn],type_ignores=[]),str(ROOT/'tak_dashboard.py'),'exec'),ns)
handler=ns['_i689_get']
class Fake:
 def __init__(self,path,method='GET',allowed=True):
  self.path=path;self.command=method;self.status=None;self.headers={};self.wfile=io.BytesIO();self.allowed=allowed
 def _tak_map_auth_ok(self):return self.allowed
 def _require_tak_map_login(self):self.status=302;return None
 def send_response(self,n):self.status=n
 def send_header(self,k,v):self.headers[k]=v
 def end_headers(self):pass
class I689Assets(unittest.TestCase):
 def test_assets_valid_get_and_head(self):
  for path,(name,mime) in static.items():
   body=(ROOT/'assets'/name).read_bytes()
   for method in ('GET','HEAD'):
    with self.subTest(path=path,method=method):
     item=Fake(path+'?v=1.4.0-i689',method);handler(item)
     self.assertEqual(item.status,200)
     self.assertEqual(item.headers.get('Content-Type'),mime)
     self.assertEqual(item.headers.get('Content-Length'),str(len(body)))
     self.assertEqual(item.headers.get('X-Content-Type-Options'),'nosniff')
     self.assertEqual(item.wfile.getvalue(),body if method=='GET' else b'')
     self.assertNotIn(b'<!doctype html',item.wfile.getvalue()[:100].lower())
 def test_missing_sidebar_terminal_404(self):
  item=Fake('/assets/runtime/tak-map-sidebar-nonexistent.js');handler(item)
  self.assertEqual(item.status,404);self.assertFalse(item.wfile.getvalue())
 def test_historical_runtime_delegation(self):
  item=Fake('/assets/runtime/tak-map-i636.js');handler(item)
  self.assertTrue(getattr(item,'previous',False))
 def test_authentication(self):
  item=Fake('/assets/runtime/tak-map-sidebar-order-i684.js',allowed=False);handler(item)
  self.assertEqual(item.status,302);self.assertFalse(item.wfile.getvalue())
 def test_app_html_wiring(self):
  self.assertIn('TAK_MAP_HTML=TAK_MAP_HTML.replace(\'/assets/tak-map-sidebar-order-i684.js?\',',source)
  self.assertIn("TAK_MAP_ITERATION='i689'",source)
  self.assertIn('tak-map-infrastructure-i689.js',source)
if __name__=='__main__':unittest.main()
