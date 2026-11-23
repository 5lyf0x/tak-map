import os,importlib.util,io,json,tempfile,threading,stat
from http.server import HTTPServer,BaseHTTPRequestHandler
from pathlib import Path
class Gateway(BaseHTTPRequestHandler):
    hits=[]
    def do_GET(self):
        Gateway.hits.append(self.path)
        route=self.path.split('?',1)[0]
        ok=route in ('/api/external-sources/v1/health','/api/external-sources/v1/capabilities','/api/external-sources/v1/snapshot')
        body=json.dumps({'ok':ok,'revision':22,'features':[],'auth':'none','error':None if ok else 'not found'}).encode()
        self.send_response(200 if ok else 404)
        self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def log_message(self,*a):pass
with tempfile.TemporaryDirectory() as td:
    os.environ['TAK_DASHBOARD_DATA_DIR']=td
    spec=importlib.util.spec_from_file_location('tak_dashboard_i645_test',str(Path(__file__).resolve().parents[1]/'tak_dashboard.py'))
    app=importlib.util.module_from_spec(spec);spec.loader.exec_module(app)
    server=HTTPServer(('127.0.0.1',0),Gateway);t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
    body={'host':'127.0.0.1','protocol':'http','port':str(server.server_port),'auth_mode':'none','verify_tls':False,'ca_cert_path':'','client_cert_path':'','client_key_path':''}
    settings=app._i645_parse_settings(body)
    assert app._i645_profile(settings)['configured']
    result,status=app._i645_test(settings)
    assert status==200 and result['ok'],(result,status)
    assert Gateway.hits==['/api/external-sources/v1/health','/api/external-sources/v1/capabilities'],Gateway.hits
    for bad,error in [({**body,'protocol':'ftp'},'Select HTTP'),({**body,'auth_mode':'certificate'},'HTTPS'),({**body,'host':'evil.com:abc'},'IPv6'),({**body,'host':'127.0.0.1/path'},'hostname'),({**body,'port':'99999'},'Port'),({**body,'ca_cert_path':'relative.pem'},'absolute')]:
        try:app._i645_parse_settings(bad)
        except ValueError as e:assert error in str(e),(bad,str(e))
        else:raise AssertionError('accepted bad settings '+str(bad))
    try:app._i645_parse_settings({**body,'protocol':'https','verify_tls':False})
    except ValueError as e:assert 'verification' in str(e)
    else:raise AssertionError('accepted insecure no-client-cert HTTPS')
    replay_before=app._tak_gateway_connection_profile('replay')
    class Handler:
        def __init__(self,path,admin=True,origin='http://example.test'):
            self.path=path;self.headers={'Origin':origin,'Host':'example.test','Content-Type':'application/json'}
            raw=json.dumps(body).encode();self.headers['Content-Length']=str(len(raw));self.rfile=io.BytesIO(raw)
            self.admin=admin
        def _tak_map_auth_ok(self):return True
        def _tak_map_session(self):return {'is_admin':self.admin}
        def _send_json(self,data,code=200):self.answer=(data,code);return self.answer
    save=Handler('/api/tak-map/gateway-data/settings')
    a=app.Handler.do_POST(save)
    assert a[1]==200 and a[0]['ok'],a
    assert stat.S_IMODE((Path(td)/'gateway_data_connection.json').stat().st_mode)==0o600
    loaded=app._tak_gateway_connection_profile('gateway_data')
    assert loaded['api_url']==settings['api_url'] and loaded['auth_mode']=='none' and loaded['configured'],loaded
    assert replay_before==app._tak_gateway_connection_profile('replay'),'Replay changed'
    config=app._i475_gateway_data_config()
    assert config['api_url']==settings['api_url'] and not config['client_certificate_required']
    proxy=Handler('/api/tak-map/gateway-data/snapshot')
    a=app._i475_gateway_data_proxy(proxy,'snapshot','since_revision=0')
    assert a[0]['ok'] and a[0]['revision']==22,a
    assert Gateway.hits[-1].startswith('/api/external-sources/v1/snapshot'),Gateway.hits
    test=Handler('/api/tak-map/gateway-data/settings/test')
    assert app.Handler.do_POST(test)[0]['ok']
    noadmin=Handler('/api/tak-map/gateway-data/settings',admin=False)
    assert app.Handler.do_POST(noadmin)[1]==403
    badorigin=Handler('/api/tak-map/gateway-data/settings',origin='https://other.example')
    assert app.Handler.do_POST(badorigin)[1]==403
    status_public=app._i645_public_settings()
    assert status_public['saved_override'] and status_public['host']=='127.0.0.1'
    server.shutdown()
    print('PASS: validation, HTTP no-cert health/capabilities, saved override 0600, dynamic snapshot proxy, Replay unchanged, admin+Origin guards, settings round-trip')
