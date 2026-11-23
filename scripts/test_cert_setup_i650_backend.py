#!/usr/bin/env python3
"""Focused backend contract; never runs cert generation."""
from pathlib import Path
from http.server import ThreadingHTTPServer
from urllib.request import urlopen,Request
from urllib.error import HTTPError
import tempfile,importlib.util,os,threading,json,contextlib,io
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
 os.environ['TAK_DASHBOARD_DATA_DIR']=tmp
 os.environ['TAK_DASHBOARD_BIND']='127.0.0.1'
 os.environ['TAK_DASHBOARD_PORT']='0'
 spec=importlib.util.spec_from_file_location('takmap_i650_backend_test',ROOT/'tak_dashboard.py')
 module=importlib.util.module_from_spec(spec)
 with contextlib.redirect_stdout(io.StringIO()):spec.loader.exec_module(module)
 assert 'takMapCertSetupLoaderI650' in module.TAK_MAP_HTML
 assert module.TAK_MAP_HTML.count('takMapCertSetupLoaderI650')==1
 assert 'mapCertSetupBtn' not in module.TAK_MAP_HTML
 orig_auth=module.Handler._tak_map_auth_ok
 orig_session=module.Handler._tak_map_session
 module.Handler._tak_map_auth_ok=lambda self:True
 module.Handler._tak_map_session=lambda self:{'is_admin':False}
 srv=ThreadingHTTPServer(('127.0.0.1',0),module.Handler)
 t=threading.Thread(target=srv.serve_forever,daemon=True);t.start()
 base='http://127.0.0.1:'+str(srv.server_port)
 try:
  with urlopen(base+'/assets/runtime/tak-map-cert-setup-i650.js',timeout=10) as res:
   assert res.status==200 and b'takMapCertSetupBtnI650' in res.read()
  with urlopen(base+'/api/tak-map/cert-setup/status',timeout=10) as res:
   data=json.load(res)
   assert data.get('ok') and data.get('is_admin') is False and 'ca_fingerprint_sha256' in data
  for endpoint in ('/api/tak-map/cert-setup/generate',):
   req=Request(base+endpoint,method='POST',headers={'Content-Type':'application/json'},data=b'{"confirmation":"REGENERATE"}')
   try:
    urlopen(req,timeout=10)
    raise AssertionError('A nonadmin user should be rejected')
   except HTTPError as err:assert err.code==403
  # Retire the old unaudited endpoint so the admin confirmation cannot be bypassed.
  req=Request(base+'/api/cert-setup',method='POST',headers={'Content-Type':'application/x-www-form-urlencoded'},data=b'extra_sans=')
  try:
   urlopen(req,timeout=10);raise AssertionError('Legacy endpoint should be disabled')
  except HTTPError as err:assert err.code==410
  module.Handler._tak_map_session=lambda self:{'is_admin':True}
  # Even an admin cannot POST from a missing or different Origin.
  req=Request(base+'/api/tak-map/cert-setup/generate',method='POST',headers={'Content-Type':'application/json','Origin':'http://untrusted.invalid'},data=b'{"confirmation":"REGENERATE"}')
  try:
   urlopen(req,timeout=10);raise AssertionError('Cross-origin operation should be rejected')
  except HTTPError as err:assert err.code==403
  print('PASS: active HTML loader, runtime asset, authenticated status, admin-only and same-origin certificate generation gates')
 finally:
  srv.shutdown();srv.server_close();t.join(timeout=10)
  module.Handler._tak_map_auth_ok=orig_auth
  module.Handler._tak_map_session=orig_session
