#!/usr/bin/env python3
"""Exercise actual i651 HTTP handlers and authorization; no service mutation."""
import contextlib,io,json,os,runpy,sys,tempfile,threading,urllib.error,urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ndm_packages_i651 import Catalog
from test_ndm_i651 import make_routing

with tempfile.TemporaryDirectory(prefix='takmap-i651-httptest-') as tmp:
    os.environ['TAK_DASHBOARD_DATA_DIR']=tmp
    with contextlib.redirect_stdout(io.StringIO()):
        ns=runpy.run_path(str(ROOT/'tak_dashboard.py'),run_name='i651_http_test')
    H=ns['Handler']
    hglobal=H.do_GET.__globals__
    hglobal['_i651_catalog']=Catalog(Path(tmp)/'ndm',external_roots=[Path(tmp)])
    H._tak_map_auth_ok=lambda self:self.headers.get('X-Test-Auth','')=='yes'
    H._require_tak_map_login=lambda self:self._send_json({'ok':False,'error':'Login required'},401)
    H._tak_map_session=lambda self:{'admin':self.headers.get('X-Test-Admin')=='yes'}
    hglobal['_i540_is_admin']=lambda session:bool(session.get('admin'))
    file=Path(tmp)/'nav.zip';make_routing(file)
    http=ThreadingHTTPServer(('127.0.0.1',0),H)
    t=threading.Thread(target=http.serve_forever,daemon=True);t.start()
    base=f'http://127.0.0.1:{http.server_address[1]}'
    def request(path,method='GET',admin=False,auth=True,origin=None,data=None,ctype='application/json'):
        headers={'X-Test-Auth':'yes' if auth else 'no','X-Test-Admin':'yes' if admin else 'no'}
        if origin is not None:headers['Origin']=origin
        if data is not None:headers['Content-Type']=ctype
        req=urllib.request.Request(base+path,data=data,method=method,headers=headers)
        try:
            with urllib.request.urlopen(req,timeout=5) as resp:return resp.status,json.loads(resp.read())
        except urllib.error.HTTPError as e:return e.code,json.loads(e.read())
    try:
        assert request('/api/tak-map/ndm/catalog',auth=False)[0]==401
        assert request('/api/tak-map/ndm/catalog')[0]==200
        assert request('/api/tak-map/ndm/discover')[0]==403
        code,body=request('/api/tak-map/ndm/discover',admin=True)
        assert code==200 and body['available']
        token=body['available'][0]['discovery_id']
        data=json.dumps({'discovery_id':token}).encode()
        assert request('/api/tak-map/ndm/register-existing','POST',admin=False,origin=base,data=data)[0]==403
        assert request('/api/tak-map/ndm/register-existing','POST',admin=True,origin='https://evil.example',data=data)[0]==403
        assert request('/api/tak-map/ndm/register-existing','POST',admin=True,data=data)[0]==403
        code,body=request('/api/tak-map/ndm/register-existing','POST',admin=True,origin=base,data=data)
        assert code==200 and body['ok'],(code,body)
        dataset=body['dataset']['dataset_id']
        assert 'zip_path' not in str(body)
        assert request('/api/tak-map/ndm/catalog')[1]['datasets'][0]['dataset_id']==dataset
        assert request('/api/tak-map/ndm/activate','POST',admin=True,origin=base,data=data)[0]==409
        assert request('/api/tak-map/routing/resolve','POST',origin=base,data=b'{"locations":[],"mode":"roads"}')[0]==400
        assert request('/api/tak-map/ndm/datasets/'+dataset,'DELETE',admin=True,origin='https://evil.example')[0]==403
        assert request('/api/tak-map/ndm/datasets/'+dataset,'DELETE',admin=True,origin=base)[0]==200
        assert file.is_file(), 'Unregister must not remove NDM package'
        print('PASS: HTTP login/admin/same-origin gates, register/discover/catalog, activation refusal, safe unregister')
    finally:
        http.shutdown();http.server_close()
