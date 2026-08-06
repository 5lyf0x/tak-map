#!/usr/bin/env python3
from __future__ import annotations
import runpy

ns = runpy.run_path('tak_dashboard.py', run_name='tak_map_login_i513_test')
assert ns['tak_map_config']()['tak_map_iteration'] == 'i537'
assert ns['tak_map_config']()['ots_integration']['login_request_body_single_read'] is True

calls = {'reads': 0, 'auth': []}

class Fake:
    def _is_secure_request(self):
        return True
    def _read_form(self):
        calls['reads'] += 1
        return {'mode': 'ots', 'username': 'alice', 'password': 'correct horse', 'otp': '123456'}
    def _send_json(self, payload, status=200, headers=None):
        return {'payload': payload, 'status': status, 'headers': headers or {}}
    def _tak_map_session_cookie(self, token):
        return f'tak_map_session={token}; Path=/'

g = ns['_i513_handle_login'].__globals__
g['_i509_load_ots_config'] = lambda: {'enabled': True, 'login_enabled': True, 'base_url': 'https://ots.example'}
def auth(cfg, username, password, otp):
    calls['auth'].append((username, password, otp))
    return {'ok': True, 'token': 'ots-token', 'cookies': {'session': 'cookie'}}
g['_i509_authenticate_remote'] = auth
g['_i511_fetch_profile'] = lambda cfg, auth, username: {'ok': True, 'profile': {'username': username, 'callsign': 'VIPER', 'display_identity': 'VIPER', 'is_admin': False, 'roles': [], 'euds': []}}
def create_session(username, password, mode, is_admin, auth, profile):
    token = 'session-token'
    g['TAK_MAP_SESSIONS'][token] = {'username': username, 'password': password, 'auth_mode': mode, 'is_admin': is_admin, 'profile': profile, 'callsign': profile.get('callsign'), 'display_identity': profile.get('display_identity')}
    return token
g['_i511_create_profile_session'] = create_session
g['_i509_session_public'] = lambda sess: {'username': sess['username'], 'callsign': sess.get('callsign'), 'is_admin': sess.get('is_admin', False)}

result = ns['_i513_handle_login'](Fake())
assert calls['reads'] == 1, calls
assert calls['auth'] == [('alice', 'correct horse', '123456')], calls
assert result['status'] == 200, result
assert result['payload']['ok'] is True and result['payload']['version'] == 'i517', result
assert result['headers']['Set-Cookie'].startswith('tak_map_session=session-token'), result

html = ns['TAK_MAP_LOGIN_HTML']
assert html.count('id="takMapLoginForm"') == 1
assert 'id="takMapAccountsV512"' not in html
assert 'id="takMapOtsLoginV509"' not in html
assert '>OpenTAKServer Login<' in html and '>Local Login<' in html
assert 'id="takMapLoginButton" type="submit">Login<' in html
assert "btn.textContent='Logging in...'" in html
assert "form.addEventListener('submit'" in html
print('i513 single-read OTS login handler and dedicated login-page tests passed')
