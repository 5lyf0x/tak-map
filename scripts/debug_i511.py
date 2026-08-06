#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, json, os, ssl, subprocess, tempfile, threading, faulthandler
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
faulthandler.enable(); faulthandler.dump_traceback_later(10, repeat=True)
print('DBG start', flush=True)
TMP=Path(tempfile.mkdtemp(prefix='tak-map-i511-identity-'))
DATA=TMP/'data'; DATA.mkdir()
os.environ['TAK_DASHBOARD_DATA_DIR']=str(DATA)

ca_key=TMP/'ca.key'; ca=TMP/'ca.pem'; key=TMP/'server.key'; csr=TMP/'server.csr'; cert=TMP/'server.pem'; ext=TMP/'ext.cnf'
subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-keyout',str(ca_key),'-out',str(ca),'-days','2','-subj','/CN=i511 OTS Test CA','-addext','basicConstraints=critical,CA:TRUE','-addext','keyUsage=critical,keyCertSign,cRLSign'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
subprocess.run(['openssl','req','-newkey','rsa:2048','-nodes','-keyout',str(key),'-out',str(csr),'-subj','/CN=localhost'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
ext.write_text('subjectAltName=DNS:localhost,IP:127.0.0.1\nextendedKeyUsage=serverAuth\n')
subprocess.run(['openssl','x509','-req','-in',str(csr),'-CA',str(ca),'-CAkey',str(ca_key),'-CAcreateserial','-out',str(cert),'-days','2','-extfile',str(ext)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)

class FakeOTS(BaseHTTPRequestHandler):
    user_kind='admin'
    def log_message(self,*args): pass
    def send_json(self,code,obj):
        body=json.dumps(obj).encode(); self.send_response(code); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    def authenticated(self): return bool(self.headers.get('Authorization') or self.headers.get('Authentication-Token'))
    def do_POST(self):
        n=int(self.headers.get('Content-Length','0') or 0); raw=self.rfile.read(n)
        if self.path=='/oauth/token' and b'alice' in raw and b'secret' in raw: return self.send_json(200,{'access_token':'LOGIN-SECRET-TOKEN'})
        return self.send_json(401,{'error':'bad credentials'})
    def do_GET(self):
        if self.path in ('/','/api/health','/api/status'): return self.send_json(200,{'name':'OpenTAKServer'})
        if self.path=='/api/me':
            if not self.authenticated(): return self.send_json(401,{'error':'auth required'})
            roles=[{'name':'administrator','description':'OTS administrators','permissions':['users:read','users:write']}] if self.user_kind=='admin' else [{'name':'operator','permissions':['missions:read']}]
            return self.send_json(200,{
                'id':42,'username':'alice','active':True,'roles':roles,
                'groups':[{'id':3,'name':'Operations'}],
                'group_memberships':[{'group_id':3,'group_name':'Operations','read':True,'write':self.user_kind=='admin'}],
                'euds':[
                    {'uid':'older','callsign':'OLD CALL','last_status':'offline','last_event_time':'2026-07-19T08:00:00Z'},
                    {'uid':'current','callsign':'SLYFOX','last_status':'online','last_event_time':'2026-07-21T13:00:00Z','team':'Cyan','team_role':'Team Lead'},
                ],
                'token':'API-ME-SECRET-THAT-MUST-NOT-PERSIST',
            })
        if self.path in ('/api/groups','/api/missions','/Marti/api/contacts/all','/Marti/api/groups','/Marti/api/missions'):
            return self.send_json(200 if self.authenticated() else 401,{'items':[]})
        return self.send_json(404,{'error':'not found'})

class QuietServer(ThreadingHTTPServer):
    daemon_threads=True
    def handle_error(self,*args): pass
srv=QuietServer(('127.0.0.1',0),FakeOTS)
ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); ctx.load_cert_chain(str(cert),str(key)); srv.socket=ctx.wrap_socket(srv.socket,server_side=True)
threading.Thread(target=srv.serve_forever,daemon=True).start(); port=srv.server_address[1]

spec=importlib.util.spec_from_file_location('tak_dashboard_i511',ROOT/'tak_dashboard.py')
mod=importlib.util.module_from_spec(spec); print('DBG import', flush=True); spec.loader.exec_module(mod); print('DBG imported', flush=True)
base=f'https://localhost:{port}'
payload={'display_name':'Identity Test OTS','base_url':base,'api_url':base,'marti_url':base,'enrollment_url':base,'cot_host':'localhost','cot_port':port,'ca_cert_path':str(ca),'verify_tls':True,'enabled':False,'login_enabled':False}

# Safe profile normalization and callsign selection.
auth=mod._i509_authenticate_remote(mod._i509_normalize_ots_config(payload),'alice','secret')
assert auth['ok'] is True, auth
fetched=mod._i511_fetch_profile(mod._i509_normalize_ots_config(payload),auth,'alice')
assert fetched['ok'] is True, fetched
profile=fetched['profile']
assert profile['display_identity']=='SLYFOX', profile
assert profile['callsign']=='SLYFOX' and profile['team']=='Cyan' and profile['team_role']=='Team Lead', profile
assert profile['is_admin'] is True and 'administrator' in [x.lower() for x in profile['role_names']], profile
serialized=json.dumps(profile)
assert 'API-ME-SECRET' not in serialized and 'LOGIN-SECRET' not in serialized, serialized

# Administrator validation is persisted without credentials or /api/me token.
# Testing a candidate must not switch an already-active OTS origin until Save.
current_origin='https://current-ots.example'
current=mod._i509_normalize_ots_config({
    'display_name':'Current OTS','base_url':current_origin,'api_url':current_origin,
    'marti_url':'https://current-ots.example:8443','enrollment_url':'https://current-ots.example:8446',
    'cot_host':'current-ots.example','cot_port':8089,'ca_cert_path':str(ca),
    'verify_tls':True,'enabled':True,'login_enabled':True,'configured_at':'2026-07-20T12:00:00Z',
})
mod._i511_write_ots_config(current)
validated=mod._i509_auth_test({**payload,'username':'alice','password':'secret'})
assert validated['ok'] is True and validated['administrator_authenticated'] is True, validated
assert validated['profile']['display_identity']=='SLYFOX', validated
persisted=json.loads((DATA/'ots_connection.json').read_text())
assert persisted['base_url']==current_origin and persisted['enabled'] is True and persisted['login_enabled'] is True, persisted
assert persisted['last_admin_validation']['base_url']==base, persisted
assert persisted['last_admin_validation']['username']=='alice', persisted
assert persisted['last_admin_validation']['display_identity']=='SLYFOX', persisted
raw=json.dumps(persisted)
for secret in ('secret','LOGIN-SECRET','API-ME-SECRET'):
    assert secret not in raw, raw

# A non-administrator can authenticate but cannot validate configuration.
FakeOTS.user_kind='operator'
nonadmin=mod._i509_auth_test({**payload,'username':'alice','password':'secret'})
assert nonadmin['ok'] is False and nonadmin['administrator_required'] is True, nonadmin
assert nonadmin['profile']['is_admin'] is False, nonadmin
FakeOTS.user_kind='admin'

# Enabling login requires prior validation for the same OTS origin.
saved=mod._i509_save_ots_config({**payload,'enabled':True,'login_enabled':True})
assert saved['enabled'] is True and saved['login_enabled'] is True, saved
try:
    mod._i509_save_ots_config({**payload,'base_url':'https://different.example','api_url':'https://different.example','enabled':True,'login_enabled':True})
except ValueError as e:
    assert 'Validate an OpenTAKServer administrator' in str(e)
else:
    raise AssertionError('Changed OTS origin enabled without administrator validation')

# Session public data exposes identity/permissions but no credentials.
token=mod._i511_create_profile_session('alice','secret','ots-user',True,auth,profile)
public=mod._i509_session_public(mod.TAK_MAP_SESSIONS[token])
assert public['display_identity']=='SLYFOX' and public['is_admin'] is True, public
assert public['identity_source']=='OpenTAKServer' and public['connection_state']=='Authenticated', public
assert 'password' not in public and 'ots_token' not in public, public
local=mod._i511_local_profile('recovery-admin')
assert local['display_identity']=='LOCAL ADMIN' and local['is_admin'] is True, local

# Simplified status has exactly the six intended primary checks.
discovery={'summary':{'web_reachable':True,'strict_web_tls':True,'hostname_match':True}}
status=mod._i511_status_payload(saved,discovery)
assert list(status['checks'])==['web_reachable','tls_trusted','hostname_verified','administrator_authenticated','configuration_saved','login_enabled'],status
assert status['state']=='complete' and status['title']=='OTS Connection: Complete',status

cfg=mod.tak_map_config()
assert cfg['tak_map_iteration']=='i527', cfg
assert cfg['ots_integration']['ots_role_based_administration'] is True
assert cfg['ots_integration']['service_identity_preserved'] is True
assert 'takMapOtsIdentityV511' in mod.TAK_MAP_HTML

srv.shutdown(); srv.server_close()
print('i511 OTS identity and permissions tests passed')
