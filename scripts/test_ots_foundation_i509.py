#!/usr/bin/env python3
import importlib.util, json, os, ssl, subprocess, tempfile, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TMP=Path(tempfile.mkdtemp(prefix='tak-map-i509-test-'))
DATA=TMP/'data'; DATA.mkdir()
os.environ['TAK_DASHBOARD_DATA_DIR']=str(DATA)

key=TMP/'key.pem'; cert=TMP/'cert.pem'; ca=TMP/'ca.pem'; ca_key=TMP/'ca.key'; csr=TMP/'server.csr'; ext=TMP/'ext.cnf'
subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(ca_key),'-out',str(ca),'-days','2','-subj','/CN=Test OTS CA','-addext','basicConstraints=critical,CA:TRUE','-addext','keyUsage=critical,keyCertSign,cRLSign'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
subprocess.run(['openssl','req','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(csr),'-subj','/CN=localhost'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
ext.write_text('subjectAltName=DNS:localhost,IP:127.0.0.1\nextendedKeyUsage=serverAuth\n')
subprocess.run(['openssl','x509','-req','-in',str(csr),'-CA',str(ca),'-CAkey',str(ca_key),'-CAcreateserial','-out',str(cert),'-days','2','-extfile',str(ext)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
p12=TMP/'truststore-root.p12'
subprocess.run(['openssl','pkcs12','-export','-nokeys','-in',str(ca),'-out',str(p12),'-passout','pass:atakatak'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

class FakeOTS(BaseHTTPRequestHandler):
    oauth_enabled=True
    def log_message(self,*a): pass
    def _send(self,code,obj,ctype='application/json'):
        body=obj if isinstance(obj,bytes) else json.dumps(obj).encode()
        self.send_response(code); self.send_header('Content-Type',ctype); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        if self.path=='/api/truststore': return self._send(200,ca.read_bytes(),'application/x-pem-file')
        if self.path=='/api/me':
            if not (self.headers.get('Authorization') or self.headers.get('Authentication-Token')): return self._send(401,{'error':'auth required'})
            return self._send(200,{'id':7,'username':'alice','active':True,'roles':[{'name':'administrator','permissions':['users:read','configuration:write']}],'groups':[{'id':1,'name':'Operations'}],'group_memberships':[{'group_id':1,'group_name':'Operations','read':True,'write':True}],'euds':[{'uid':'old-eud','callsign':'OLDFOX','last_status':'offline','last_event_time':'2026-07-19T12:00:00Z'},{'uid':'new-eud','callsign':'SLYFOX','last_status':'online','last_event_time':'2026-07-21T12:00:00Z','team':'Cyan','team_role':'Team Lead'}],'token':'must-never-leak'})
        if self.path in ('/api/groups','/api/missions','/Marti/api/contacts/all','/Marti/api/groups','/Marti/api/missions'):
            if not (self.headers.get('Authorization') or self.headers.get('Authentication-Token')): return self._send(401,{'error':'auth required'})
            return self._send(200,{'items':[{'name':'test'}]})
        if self.path in ('/',''): return self._send(200,{'name':'OpenTAKServer'})
        return self._send(404,{'error':'not found'})
    def do_POST(self):
        n=int(self.headers.get('Content-Length','0') or 0); raw=self.rfile.read(n)
        if self.path=='/oauth/token':
            if self.oauth_enabled and b'alice' in raw and b'secret' in raw: return self._send(200,{'access_token':'test.jwt.token'})
            return self._send(401,{'error':'bad credentials'})
        if self.path.startswith('/api/login?include_auth_token'):
            if b'alice' in raw and b'secret' in raw: return self._send(200,{'meta':{'code':200},'response':{'user':{'authentication_token':'flask-security-token'}}})
            return self._send(401,{'error':'bad credentials'})
        if self.path=='/api/login': return self._send(401,{'error':'not used'})
        return self._send(404,{'error':'not found'})

class QuietServer(ThreadingHTTPServer):
    def handle_error(self,*a): pass
srv=QuietServer(('127.0.0.1',0),FakeOTS)
ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); ctx.load_cert_chain(str(cert),str(key)); srv.socket=ctx.wrap_socket(srv.socket,server_side=True)
threading.Thread(target=srv.serve_forever,daemon=True).start(); port=srv.server_address[1]

spec=importlib.util.spec_from_file_location('tak_dashboard_i509',ROOT/'tak_dashboard.py')
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
base=f'https://localhost:{port}'
payload={'base_url':base,'api_url':base,'marti_url':base,'enrollment_url':base,'cot_host':'localhost','cot_port':port,'ca_cert_path':str(ca),'verify_tls':True,'enabled':True,'login_enabled':True}

norm=mod._i509_normalize_ots_config(payload)
assert norm['base_url']==base and norm['cot_port']==port
result=mod._i509_discover_ots(payload)
assert result['summary']['web_reachable'] is True, result
assert result['summary']['strict_web_tls'] is True, result['certificate']
assert result['summary']['hostname_match'] is True, result['certificate']
assert result['summary']['cot_tls_reachable'] is True, result['cot_tls']
assert result['capabilities']['groups'].startswith('available'), result['capabilities']

auth=mod._i509_auth_test({**payload,'username':'alice','password':'secret'})
assert auth['ok'] is True and auth['administrator_authenticated'] is True, auth
assert auth['profile']['display_identity']=='SLYFOX' and auth['profile']['is_admin'] is True, auth
assert mod._i509_extract_token({'response':{'user':{'authentication_token':'nested-token'}}})=='nested-token'
assert mod._i509_pkcs12_certificates(p12.read_bytes(),['atakatak']), 'PKCS12 truststore extraction failed'
assert auth['capabilities']['groups']['status']==200, auth
assert 'token' not in auth and 'cookies' not in auth, auth
FakeOTS.oauth_enabled=False
auth_api=mod._i509_auth_test({**payload,'username':'alice','password':'secret'})
assert auth_api['ok'] is True and auth_api['administrator_authenticated'] is True, auth_api
assert auth_api['capabilities']['groups']['status']==200, auth_api
FakeOTS.oauth_enabled=True

saved=mod._i509_save_ots_config({**payload,'password':'must-not-persist','token':'must-not-persist','cookies':'must-not-persist'})
assert saved['login_enabled'] is True
persisted=json.loads((DATA/'ots_connection.json').read_text())
for forbidden in ('password','token','cookies','username','otp','truststore_password'):
    assert forbidden not in persisted, (forbidden,persisted)
public=mod._i509_public_ots_config(saved)
assert 'client_key_path' not in public
assert public['configured'] is True

installed=mod._i509_install_truststore(payload)
assert installed['ok'] and Path(installed['path']).is_file(), installed
assert installed['certificate_identities'][0]['sha256'], installed

assert 'takMapConfigureOtsV509' in mod.TAK_MAP_HTML
assert 'Configure OTS' in mod.TAK_MAP_HTML
assert 'takMapOtsLoginV509' not in mod.TAK_MAP_LOGIN_HTML
assert '>OpenTAKServer Login<' in mod.TAK_MAP_LOGIN_HTML and '>Local Login<' in mod.TAK_MAP_LOGIN_HTML
assert 'takMapConfigureOtsV509' not in mod.LOGIN_HTML
assert mod.tak_map_config()['tak_map_iteration']=='i537'
assert mod.tak_map_config()['ots_integration']['chat_ui'] is False
source=(ROOT/'tak_dashboard.py').read_text(errors='replace')
assert "'base_url':cfg.get('base_url') if cfg.get('configured') else ''" not in source
assert "parsed.path.startswith('/api/tak-map/tak-client/')" in source

srv.shutdown(); srv.server_close()
print('i509/i511 OTS foundation compatibility tests passed')
