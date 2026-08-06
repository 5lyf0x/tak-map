#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, json, os, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TMP=Path(tempfile.mkdtemp(prefix='tak-map-i512-local-'))
os.environ['TAK_DASHBOARD_DATA_DIR']=str(TMP/'data')
os.environ['TAK_MAP_LOCAL_PASSWORD_ITERATIONS']='200000'
spec=importlib.util.spec_from_file_location('tak_dashboard_i512',ROOT/'tak_dashboard.py')
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

class Dummy:
    client_address=('127.0.0.1',12345)
handler=Dummy()

store=mod._i512_load_local_accounts()
admin=store['users']['administrator']
assert admin['is_admin'] and admin['must_change_password']
assert mod._i512_verify_password(admin['password_hash'],'password')
assert admin['password_hash'] != 'password' and admin['password_hash'].startswith('pbkdf2_sha256$')
assert admin['tak_uid'].startswith('TAKMAP-LOCAL-')

account,error,status=mod._i512_authenticate_local(handler,'administrator','password')
assert status==200 and account and not error
admin_token=mod._i512_create_local_session(account)
sess=mod.TAK_MAP_SESSIONS[admin_token]
public=mod._i509_session_public(sess)
assert public['display_identity']=='LOCAL ADMIN' and public['must_change_password'] is True
assert mod._i512_forced_change(sess)
# Exercise the real request shape: _tak_map_session() returns a copy, so the live session must be updated by token.
mod._I512_REQUEST_CONTEXT.session_token=admin_token
session_copy=mod.get_tak_map_session(admin_token)
changed=mod._i512_change_local_password(session_copy,{'current_password':'password','new_password':'Eight888','confirm_password':'Eight888'})
mod._I512_REQUEST_CONTEXT.session_token=''
assert changed['ok'] and 'successfully' in changed['message'].lower()
assert not mod._i512_forced_change(mod.TAK_MAP_SESSIONS[admin_token])
sess=mod.TAK_MAP_SESSIONS[admin_token]
try: mod._i512_change_local_password(sess,{'current_password':'Eight888','new_password':'Seven77','confirm_password':'Seven77'})
except ValueError as e: assert 'at least 8 characters' in str(e)
else: raise AssertionError('Seven-character password accepted')
assert mod._i512_local_admin_ready()

created=mod._i512_manage_local_users({'action':'create','username':'operator1','password':'Temporary-Password-512','callsign':'RAVEN 12'},sess)
assert any(u['username']=='operator1' for u in created['users'])
user=mod._i512_load_local_accounts()['users']['operator1']
stable_uid=user['tak_uid']
account,error,status=mod._i512_authenticate_local(handler,'operator1','Temporary-Password-512')
assert status==200 and account

# OTS active blocks local non-admins but never deletes them or changes their UID.
cfg=mod._i509_default_ots_config(); cfg.update({'enabled':True,'login_enabled':True,'base_url':'https://ots.example','api_url':'https://ots.example','configured_at':'2026-07-21T00:00:00Z'})
mod._i511_write_ots_config(mod._i509_normalize_ots_config(cfg,cfg))
account,error,status=mod._i512_authenticate_local(handler,'operator1','Temporary-Password-512')
assert account is None and status==403 and 'unavailable' in error.lower()
assert mod._i512_load_local_accounts()['users']['operator1']['tak_uid']==stable_uid
account,error,status=mod._i512_authenticate_local(handler,'administrator','Eight888')
assert status==200 and account['is_admin']

# Disconnect restores local users and preserves OTS settings.
result=mod._i512_disconnect_ots(); assert result['ok']
cfg2=mod._i509_load_ots_config(); assert cfg2['enabled'] is False and cfg2['login_enabled'] is False and cfg2['base_url']=='https://ots.example'
account,error,status=mod._i512_authenticate_local(handler,'operator1','Temporary-Password-512')
assert status==200 and account

# Callsign changes do not change stable UID and collisions are rejected.
user_token=mod._i512_create_local_session(account); usess=mod.TAK_MAP_SESSIONS[user_token]
old_uid=usess['profile']['tak_uid']
updated=mod._i512_update_callsign(usess,'RAVEN 13')
assert updated['callsign']=='RAVEN 13' and updated['tak_uid']==old_uid
try: mod._i512_update_callsign(sess,'RAVEN 13')
except ValueError as e: assert 'already assigned' in str(e)
else: raise AssertionError('Duplicate callsign accepted')
for bad in ('A'*33,'BAD<CALL',''):
    if bad=='': continue
    try: mod._i512_callsign(bad)
    except ValueError: pass
    else: raise AssertionError('Invalid callsign accepted: '+bad)

# OTS identity preference uses EUD suggestion until selected, then keeps stable UID.
profile={'username':'alice','user_id':'42','callsign':'SLYFOX','display_identity':'SLYFOX'}
cfg3={'base_url':'https://ots.example'}
p1=mod._i512_apply_ots_identity(cfg3,profile); uid1=p1['tak_uid']
ots_session={'auth_mode':'ots-user','username':'alice','profile':p1,'callsign':p1['callsign'],'display_identity':p1['display_identity'],'tak_uid':uid1}
mod._i512_update_callsign(ots_session,'VIPER 6')
assert ots_session['profile']['callsign']=='VIPER 6' and ots_session['profile']['tak_uid']==uid1
p2=mod._i512_apply_ots_identity(cfg3,profile)
assert p2['callsign']=='VIPER 6' and p2['suggested_callsign']=='SLYFOX' and p2['tak_uid']==uid1

# User-triggered CoT carries a TAK-native creator UID/callsign without replacing
# the map object's own contact callsign/name.
mod._I512_REQUEST_CONTEXT.identity={'username':'alice','callsign':'VIPER 6','tak_uid':uid1}
sample_xml='<event version="2.0" uid="OBJECT-1" type="u-d-p"><point lat="1" lon="2" hae="0" ce="1" le="1"/><detail><contact callsign="OBJECT NAME"/></detail></event>'
stamped=mod._i512_stamp_cot_creator(sample_xml)
assert 'uid="'+uid1+'"' in stamped and 'callsign="VIPER 6"' in stamped
assert '<contact callsign="OBJECT NAME"' in stamped
candidates=mod._v337_candidate_creators('SERVICE-UID')
assert candidates and all(c.get('callsign')=='VIPER 6' for c in candidates)
mod._I512_REQUEST_CONTEXT.identity={}

# User-scoped Data Sync translates stored OTS session credentials into the auth shape.
captured={}
old_headers=mod._i511_auth_headers
old_context=mod._i509_ssl_context
old_urlopen=mod.urlopen
class FakeResp:
    status=200
    def __enter__(self): return self
    def __exit__(self,*a): return False
    def read(self,n=-1): return b'{"missions":[]}'
def fake_headers(cfg,auth): captured.update(auth); return {'Authorization':'Bearer '+str(auth.get('token') or '')}
mod._i511_auth_headers=fake_headers
mod._i509_ssl_context=lambda cfg: None
mod.urlopen=lambda req,timeout=0,context=None: FakeResp()
res=mod._i512_request_json({}, {'ots_token':'USER-TOKEN','ots_cookies':{'session':'COOKIE'},'ots_csrf_token':'CSRF'}, 'https://ots.example/api/missions')
assert res['ok'] and captured['token']=='USER-TOKEN' and captured['cookies']=={'session':'COOKIE'} and captured['csrf_token']=='CSRF'
mod._i511_auth_headers=old_headers; mod._i509_ssl_context=old_context; mod.urlopen=old_urlopen
sample={'missions':[{'name':'Alpha','contents':[{'uid':'UID-1','callsign':'MISSION POINT','lat':34.1,'lon':-117.2}]}]}
assert mod._i512_mission_names(sample)==['Alpha']
rows=mod._i512_mission_api_objects(sample,'Alpha')
assert any(r.get('uid')=='UID-1' for r in rows)

cfgout=mod.tak_map_config()
assert cfgout['tak_map_iteration']=='i537'
assert cfgout['ots_integration']['login_options']==['OpenTAKServer Login','Local Login']
assert cfgout['ots_integration']['forced_default_password_change']
assert cfgout['composite_basemaps']['tak_map_python_tile_proxy_for_gateway'] is False
assert cfgout['composite_basemaps']['required_gateway_transport']=='dedicated-read-only-https-listener-without-client-certificate-request'
assert 'takMapAccountsV512' in mod.TAK_MAP_HTML
assert 'OpenTAKServer Login' in mod.TAK_MAP_LOGIN_HTML and 'Local Login' in mod.TAK_MAP_LOGIN_HTML
print('i512 local accounts, callsign, and OTS disconnect compatibility tests passed under i517')
