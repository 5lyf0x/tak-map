#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, json, os, ssl, stat, subprocess, tempfile, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TMP=Path(tempfile.mkdtemp(prefix='tak-map-i510-trust-test-'))
DATA=TMP/'data'; DATA.mkdir()
os.environ['TAK_DASHBOARD_DATA_DIR']=str(DATA)

ca_key=TMP/'ca.key'; ca=TMP/'ca.pem'; server_key=TMP/'server.key'; csr=TMP/'server.csr'; server_cert=TMP/'server.pem'; ext=TMP/'ext.cnf'
subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(ca_key),'-out',str(ca),'-days','2','-subj','/CN=Legacy OTS Test CA','-addext','basicConstraints=critical,CA:TRUE','-addext','keyUsage=critical,keyCertSign,cRLSign'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
subprocess.run(['openssl','req','-newkey','rsa:2048','-nodes','-keyout',str(server_key),'-out',str(csr),'-subj','/CN=localhost'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
ext.write_text('subjectAltName=DNS:localhost,IP:127.0.0.1\nextendedKeyUsage=serverAuth\n')
subprocess.run(['openssl','x509','-req','-in',str(csr),'-CA',str(ca),'-CAkey',str(ca_key),'-CAcreateserial','-out',str(server_cert),'-days','2','-extfile',str(ext)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
legacy=TMP/'truststore-root-legacy.p12'
subprocess.run(['openssl','pkcs12','-export','-legacy','-nokeys','-in',str(ca),'-out',str(legacy),'-passout','pass:atakatak'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

class FakeOTS(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def send_blob(self,code,body,ctype='application/json'):
        if not isinstance(body,(bytes,bytearray)): body=json.dumps(body).encode()
        self.send_response(code); self.send_header('Content-Type',ctype); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        if self.path=='/api/truststore': return self.send_blob(200,legacy.read_bytes(),'application/x-pkcs12')
        if self.path in ('/','/api/health','/api/status'): return self.send_blob(200,{'name':'OpenTAKServer','version':'test'})
        if self.path.startswith('/Marti/') or self.path in ('/api/groups','/api/missions'): return self.send_blob(401,{'error':'authentication required'})
        return self.send_blob(404,{'error':'not found'})
    def do_POST(self):
        if self.path in ('/oauth/token','/api/login'): return self.send_blob(401,{'error':'authentication required'})
        return self.send_blob(404,{'error':'not found'})

class QuietServer(ThreadingHTTPServer):
    daemon_threads=True
    def handle_error(self,*args): pass
srv=QuietServer(('127.0.0.1',0),FakeOTS)
ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); ctx.load_cert_chain(str(server_cert),str(server_key)); srv.socket=ctx.wrap_socket(srv.socket,server_side=True)
threading.Thread(target=srv.serve_forever,daemon=True).start(); port=srv.server_address[1]

spec=importlib.util.spec_from_file_location('tak_dashboard_i510',ROOT/'tak_dashboard.py')
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

certs,details=mod._i510_pkcs12_certificates_detailed(legacy.read_bytes(),['atakatak'])
assert certs, details
assert details['mode']=='pkcs12-legacy' and details['used_legacy'] is True, details
failed,failed_details=mod._i510_pkcs12_certificates_detailed(legacy.read_bytes(),['definitely-wrong'])
assert not failed, failed_details
assert any(a.get('error') for a in failed_details['attempts']), failed_details

base=f'https://localhost:{port}'
payload={'display_name':'Legacy Test OTS','base_url':base,'api_url':base,'marti_url':base,'enrollment_url':base,'cot_host':'localhost','cot_port':port,'verify_tls':True,'truststore_password':'atakatak','enabled':False,'login_enabled':False}
partial=mod._i509_discover_ots(payload)
assert partial['ok'] is False and partial['primary_problem'], partial
assert 'TLS validation failed' in partial['primary_problem'], partial['primary_problem']

installed=mod._i509_install_truststore(payload)
assert installed['ok'] is True, installed
assert installed['version']=='i510', installed
assert installed['extraction']['mode']=='pkcs12-legacy', installed['extraction']
assert installed['extraction']['used_legacy'] is True
assert installed['certificates']==1, installed
path=Path(installed['path'])
assert path.is_file() and path.read_text().count('BEGIN CERTIFICATE')==1
assert stat.S_IMODE(path.stat().st_mode)==0o640, oct(stat.S_IMODE(path.stat().st_mode))
assert installed['certificate_identities'][0]['is_ca'] is True
assert installed['discovery']['ok'] is True, installed['discovery']
assert installed['discovery']['summary']['strict_web_tls'] is True
assert installed['discovery']['cot_tls']['strict_tls_ok'] is True
assert installed['discovery']['primary_problem']==''
persisted=json.loads((DATA/'ots_connection.json').read_text())
assert persisted['version']=='i512', persisted
assert persisted['ca_cert_path']==str(path)
assert 'truststore_password' not in persisted
assert persisted['last_discovery']['ok'] is True
assert mod.tak_map_config()['tak_map_iteration']=='i537'
assert mod.tak_map_config()['ots_integration']['truststore_legacy_fallback'] is True

srv.shutdown(); srv.server_close()
print('i510 Configure OTS legacy truststore tests passed')
