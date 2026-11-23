#!/usr/bin/env python3
"""Live search asset must load through the installed TAK Map runtime route."""
import os,importlib.util,tempfile,threading
from http.server import ThreadingHTTPServer
from urllib.request import urlopen
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='takmap-live-search-') as data_dir:
 os.environ['TAK_DASHBOARD_DATA_DIR']=data_dir
 os.environ['TAK_DASHBOARD_BIND']='127.0.0.1'
 os.environ['TAK_DASHBOARD_PORT']='0'
 spec=importlib.util.spec_from_file_location('live_search_test_app',ROOT/'tak_dashboard.py')
 app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
 assert app.TAK_MAP_HTML.count('takMapLiveSearchLoaderI650')==1
 assert 'id="layerSearch"' in app.TAK_MAP_HTML
 server=ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
 t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
 try:
  url='http://127.0.0.1:%s/assets/runtime/tak-map-live-search-i650.js'%server.server_address[1]
  with urlopen(url,timeout=10) as response:
   body=response.read()
   assert response.status==200
   assert response.headers.get_content_type() in ('text/javascript','application/javascript')
   assert body==(ROOT/'assets/tak-map-live-search-i650.js').read_bytes()
 finally:
  server.shutdown();server.server_close();t.join(timeout=10)
print('PASS: live map search runtime JS served and injected once on TAK Map page')
