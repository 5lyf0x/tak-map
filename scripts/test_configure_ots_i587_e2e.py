#!/usr/bin/env python3
import importlib.util, json, os, ssl, subprocess, tempfile, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TMP=Path(tempfile.mkdtemp(prefix='tak-map-i587-e2e-'))
DATA=TMP/'data'; DATA.mkdir()
os.environ['TAK_DASHBOARD_DATA_DIR']=str(DATA)
os.environ['TAK_MAP_MIL_ROOT']=str(ROOT/'assets/mil2525')
key=TMP/'key.pem'; cert=TMP/'cert.pem'; ca=TMP/'ca.pem'; cakey=TMP/'ca.key'; csr=TMP/'server.csr'; ext=TMP/'ext.cnf'
subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(cakey),'-out',str(ca),'-days','2','-subj','/CN=i587 OTS CA','-addext','basicConstraints=critical,CA:TRUE','-addext','keyUsage=critical,keyCertSign,cRLSign'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
subprocess.run(['openssl','req','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(csr),'-subj','/CN=localhost'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
ext.write_text('subjectAltName=DNS:localhost,IP:127.0.0.1\nextendedKeyUsage=serverAuth\n')
subprocess.run(['openssl','x509','-req','-in',str(csr),'-CA',str(ca),'-CAkey',str(cakey),'-CAcreateserial','-out',str(cert),'-days','2','-extfile',str(ext)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

class FakeOTS(BaseHTTPRequestHandler):
    def log_message(self,*a): pass
    def send_obj(self,status,obj,ctype='application/json'):
        body=obj if isinstance(obj,bytes) else json.dumps(obj).encode()
        self.send_response(status);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def authorized(self): return bool(self.headers.get('Authorization') or self.headers.get('Authentication-Token'))
    def do_GET(self):
        path=self.path.split('?',1)[0]
        if path=='/': return self.send_obj(200,{'name':'OpenTAKServer','version':'test'})
        if path=='/api/truststore': return self.send_obj(200,ca.read_bytes(),'application/x-pem-file')
        if path=='/Marti/api/version/config': return self.send_obj(200,{'version':'test'})
        if path=='/Marti/api/tls/signClient/v2': return self.send_obj(401,{'error':'credentials required'})
        if path=='/api/me':
            if not self.authorized(): return self.send_obj(401,{'error':'auth required'})
            return self.send_obj(200,{'username':'admin','callsign':'ADMIN','roles':[{'name':'administrator','permissions':['configuration:write']}],'groups':[{'name':'Ops'}]})
        if path in ('/api/groups','/api/missions','/Marti/api/contacts/all','/Marti/api/groups','/Marti/api/missions'):
            if not self.authorized(): return self.send_obj(401,{'error':'auth required'})
            return self.send_obj(200,{'items':[]})
        return self.send_obj(404,{'error':'not found'})
    def do_POST(self):
        n=int(self.headers.get('Content-Length','0') or 0);raw=self.rfile.read(n)
        if self.path=='/oauth/token':
            if b'admin' in raw and b'secret' in raw:return self.send_obj(200,{'access_token':'memory-only-token'})
            return self.send_obj(401,{'error':'bad credentials'})
        if self.path.startswith('/api/login?include_auth_token'):
            if b'admin' in raw and b'secret' in raw:return self.send_obj(200,{'response':{'user':{'authentication_token':'memory-only-security-token'}}})
            return self.send_obj(401,{'error':'bad credentials'})
        return self.send_obj(404,{'error':'not found'})
class Server(ThreadingHTTPServer):
    def handle_error(self,*a): pass
srv=Server(('127.0.0.1',0),FakeOTS)
ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);ctx.load_cert_chain(str(cert),str(key));srv.socket=ctx.wrap_socket(srv.socket,server_side=True)
threading.Thread(target=srv.serve_forever,daemon=True).start();port=srv.server_address[1]
base=f'https://localhost:{port}'

spec=importlib.util.spec_from_file_location('tak_dashboard_i587_e2e',ROOT/'tak_dashboard.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
payload={
 'server_address':base,'username':'admin','password':'secret',
 'api_url':base,'marti_url':base,'enrollment_url':base,'cot_host':'localhost','cot_port':port,
 'truststore_path':'/api/truststore',
 'enabled':True,'login_enabled':True,'data_sync_enabled':True,
 'automatic_user_certificate_enrollment':True,'automatic_trust_installation':True,
}
result=mod._i587_enroll_server(payload)
assert result['ok'] is True,result
assert result['status_label']=='Connected'
assert result['standard_endpoints_used'] is False # test uses explicit overrides
cfg=json.loads(mod.TAK_MAP_OTS_CONFIG_FILE.read_text())
assert cfg['base_url']==base and cfg['ca_cert_path']
for forbidden in ('username','password','otp','token','cookies','truststore_password'):
    assert forbidden not in cfg,(forbidden,cfg)
manifest=json.loads(mod._I587_ENROLLMENT_MANIFEST_FILE.read_text())
assert manifest['status']=='enrolled' and manifest['origin']==base
assert any(x.get('kind')=='ots-ca-chain' for x in manifest['files'])
assert Path(cfg['ca_cert_path']).read_text().startswith('-----BEGIN CERTIFICATE-----')
srv.shutdown();srv.server_close()
print('i587 Configure OTS end-to-end HTTPS discovery, trust installation, administrator validation, saved configuration, and manifest test passed')
