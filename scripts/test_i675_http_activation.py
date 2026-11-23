"""Exercise real i675 management HTTP routes and authorization, without restarting Valhalla."""
import contextlib
import io
import json
import os
import runpy
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ndm_packages_i651 import Catalog

with tempfile.TemporaryDirectory(prefix='takmap-i675-http-') as tmp:
    os.environ['TAK_DASHBOARD_DATA_DIR']=tmp
    with contextlib.redirect_stdout(io.StringIO()):
        ns=runpy.run_path(str(ROOT/'tak_dashboard.py'),run_name='i675_http_test')
    H=ns['Handler']
    H._tak_map_auth_ok=lambda self:self.headers.get('X-Test-Auth','')=='yes'
    H._require_tak_map_login=lambda self:self._send_json({'ok':False,'error':'Login required'},401)
    H._tak_map_session=lambda self:{'admin':self.headers.get('X-Test-Admin')=='yes'}
    g=H.do_POST.__globals__
    g['_i540_is_admin']=lambda session:bool(session.get('admin'))
    class MockSwitcher:
        job={'status':'idle','dataset_id':'','error':''}
        def options(self):return {'ok':True,'datasets':[],'active_dataset_id':'','switch':self.job}
        def start(self,ident):
            assert ident=='b'*64
            return {'ok':True,'accepted':True,'status':'preparing','dataset_id':ident}
    g['_I675_ROUTING_SWITCHER']=MockSwitcher()
    g['_i651_catalog']=Catalog(Path(tmp)/'ndm',external_roots=[Path(tmp)])
    http=ThreadingHTTPServer(('127.0.0.1',0),H)
    thread=threading.Thread(target=http.serve_forever,daemon=True);thread.start()
    base='http://127.0.0.1:%d'%http.server_address[1]
    def req(path,method='GET',admin=False,auth=True,origin=None,payload=None):
        headers={'X-Test-Auth':'yes' if auth else 'no','X-Test-Admin':'yes' if admin else 'no'}
        if origin is not None:headers['Origin']=origin
        if payload is not None:headers['Content-Type']='application/json'
        request=urllib.request.Request(base+path,data=payload,headers=headers,method=method)
        try:
            with urllib.request.urlopen(request,timeout=5) as response:return response.status,response.read()
        except urllib.error.HTTPError as error:return error.code,error.read()
    try:
        assert req('/api/tak-map/routing/datasets-i675',auth=False)[0]==401
        code,body=req('/api/tak-map/routing/datasets-i675')
        assert code==200 and json.loads(body)['ok']
        assert req('/assets/runtime/tak-map-routing-dropdown-i675.js',auth=False)[0]==401
        code,asset=req('/assets/runtime/tak-map-routing-dropdown-i675.js')
        assert code==200 and b'takRouteDataButtonI675' in asset
        path='/api/tak-map/routing/activate-i675';data=json.dumps({'dataset_id':'b'*64}).encode()
        assert req(path,'POST',auth=False,admin=True,origin=base,payload=data)[0]==401
        assert req(path,'POST',admin=False,origin=base,payload=data)[0]==403
        assert req(path,'POST',admin=True,origin='https://evil.invalid',payload=data)[0]==403
        assert req(path,'POST',admin=True,payload=data)[0]==403
        code,body=req(path,'POST',admin=True,origin=base,payload=data)
        assert code==202 and json.loads(body)['accepted'],(code,body)
        print('PASS: i675 HTTP login, admin, same-origin, routing JS, graph-switch 202')
    finally:
        http.shutdown();http.server_close()
