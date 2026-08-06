import importlib.util
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tak_dashboard_i565_atak_profile_test', ROOT / 'tak_dashboard.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

assert mod.TAK_MAP_ITERATION == 'i568'
assert mod._I565_ATAK_USER_AGENT == 'ATAK/5.4.0.14'
assert 'iTAK' not in mod._I565_ATAK_USER_AGENT
assert mod._I565_ATAK_COT_PROFILE['platform'] == 'ATAK-CIV'
source_headers = mod._i561_ots_auth_headers({'ots_token':'abc','ots_token_header':'Authorization','ots_token_prefix':'Bearer '})
assert source_headers['User-Agent'] == mod._I565_ATAK_USER_AGENT, source_headers
assert source_headers['Authorization'] == 'Bearer abc', source_headers

old_raw = mod._i565_mission_request_raw
old_creator = mod._i565_current_creator_uid
old_identity = mod._i565_request_identity_key
old_ots = mod._ots_mission_api_request
try:
    mod._i565_current_creator_uid = lambda path='': 'ANDROID-ATAK-EUD-01'
    mod._i565_request_identity_key = lambda: 'alice/ANDROID-ATAK-EUD-01'
    mod._I565_MISSION_TOKENS.clear()
    calls = []
    token_counter = {'value': 0}

    def raw(path, method='GET', body=None, headers=None, token='', public_host='', timeout=25):
        call = {'path': path, 'method': method, 'body': body, 'headers': dict(headers or {}), 'token': token}
        calls.append(call)
        ua = call['headers'].get('User-Agent', '')
        assert ua == mod._I565_ATAK_USER_AGENT, call
        assert 'iTAK' not in ua, call
        if '/subscription?' in path and method == 'PUT':
            token_counter['value'] += 1
            return {'ok': True, 'status': 200, 'json': {'data': {'token': f"atak-token-{token_counter['value']}"}}}
        if path.startswith('/Marti/api/missions/Mission%20Alpha') and path.endswith('?creatorUid=ANDROID-ATAK-EUD-01') and method == 'PUT':
            return {'ok': True, 'status': 200, 'json': {'data': [{'token': 'create-token-1'}]}}
        if path == '/Marti/api/missions' and method == 'GET':
            return {'ok': True, 'status': 200, 'json': {'data': [{'name': 'Mission Alpha'}]}}
        if path.startswith('/Marti/sync/upload'):
            return {'ok': True, 'status': 200, 'json': {'Hash': 'abc'}}
        return {'ok': True, 'status': 200, 'json': {'data': []}}

    mod._i565_mission_request_raw = raw
    mod._ots_mission_api_request = mod._i565_atak_mission_request

    # Discovery uses the centralized ATAK profile but does not invent a Mission token.
    r = mod._ots_mission_api_request('/Marti/api/missions', method='GET', headers={'User-Agent':'iTAK/2.9.1 legacy-callsite'})
    assert r['ok'] and r['user_agent_family'] == 'ATAK' and not r['mission_token_used'], r
    assert calls[-1]['headers']['User-Agent'] == mod._I565_ATAK_USER_AGENT, calls[-1]

    # Mission child resources acquire/cache the Mission token exactly like ATAK.
    r = mod._ots_mission_api_request('/Marti/api/missions/Mission%20Alpha/cot', method='GET')
    assert r['ok'] and r['mission_token_used'] and r['mission_token_auto_acquired'], r
    assert calls[-1]['token'] == 'atak-token-1', calls

    before = token_counter['value']
    r = mod._ots_mission_api_request('/Marti/api/missions/Mission%20Alpha/contents?creatorUid=ANDROID-ATAK-EUD-01', method='PUT', body=b'{}', headers={'Content-Type':'application/json'})
    assert r['ok'] and r['mission_token_used'], r
    assert token_counter['value'] == before, (token_counter, calls)
    assert calls[-1]['token'] == 'atak-token-1', calls

    # Upload and mission creation also carry the same ATAK profile. A returned
    # mission token is cached for subsequent reads/writes.
    r = mod._ots_mission_api_request('/Marti/sync/upload?name=x.zip&creatorUid=ANDROID-ATAK-EUD-01', method='POST', body=b'zip')
    assert r['ok'] and r['user_agent'] == mod._I565_ATAK_USER_AGENT, r
    mod._I565_MISSION_TOKENS.clear()
    r = mod._ots_mission_api_request('/Marti/api/missions/Mission%20Alpha?creatorUid=ANDROID-ATAK-EUD-01', method='PUT', body=b'')
    assert r['ok'], r
    r = mod._ots_mission_api_request('/Marti/api/missions/Mission%20Alpha/cot', method='GET')
    assert r['ok'] and calls[-1]['token'] == 'create-token-1', calls

    # Authorization failure refreshes once, then retries with the new token.
    mod._I565_MISSION_TOKENS.clear()
    calls.clear(); token_counter['value'] = 0
    protected_count = {'value': 0}
    def raw_refresh(path, method='GET', body=None, headers=None, token='', public_host='', timeout=25):
        calls.append({'path':path,'method':method,'headers':dict(headers or {}),'token':token})
        assert (headers or {}).get('User-Agent') == mod._I565_ATAK_USER_AGENT
        if '/subscription?' in path:
            token_counter['value'] += 1
            return {'ok': True, 'status': 200, 'json': {'data': {'token': f"refresh-token-{token_counter['value']}"}}}
        protected_count['value'] += 1
        if protected_count['value'] == 1:
            return {'ok': False, 'status': 401, 'json': {'error':'Mission token expired'}}
        return {'ok': True, 'status': 200, 'json': {}}
    mod._i565_mission_request_raw = raw_refresh
    r = mod._ots_mission_api_request('/Marti/api/missions/Mission%20Alpha/cot', method='GET')
    assert r['ok'] and r['mission_token_refresh_attempted'] is True, r
    assert token_counter['value'] == 2 and protected_count['value'] == 2, (calls, r)
    assert [c['token'] for c in calls if '/cot' in c['path']] == ['refresh-token-1','refresh-token-2'], calls

finally:
    mod._i565_mission_request_raw = old_raw
    mod._i565_current_creator_uid = old_creator
    mod._i565_request_identity_key = old_identity
    mod._ots_mission_api_request = old_ots
    mod._I565_MISSION_TOKENS.clear()

# Every CoT publication path receives ATAK takv/contact metadata, including
# point, route, shape, presence, and terminal delete XML passed through this helper.
source = '''<?xml version="1.0" encoding="UTF-8"?>
<event version="2.0" uid="P1" type="a-f-G-U-C" how="h-e" time="2026-07-27T00:00:00Z" start="2026-07-27T00:00:00Z" stale="2026-07-27T00:10:00Z"><point lat="34" lon="-118" hae="0" ce="10" le="10"/><detail><contact callsign="P1"/><takv device="TAK Map" platform="TAK Map" os="Web" version="1.3.0-i565"/><takmap version="i565"/></detail></event>'''
transformed = mod._i565_atak_cot_xml(source)
root = ET.fromstring(transformed)
detail = root.find('detail')
takv = detail.find('takv')
contact = detail.find('contact')
meta = detail.find('takmap')
assert takv.attrib == mod._I565_ATAK_COT_PROFILE, takv.attrib
assert contact.attrib.get('endpoint') == '*:-1:stcp', contact.attrib
assert meta.attrib.get('dataSyncClientProfile') == 'ATAK', meta.attrib

cfg = mod.tak_map_config()
profile = cfg['data_sync_client_profile_i565']
assert profile['client'] == 'ATAK' and profile['itak_user_agent'] is False, profile
assert profile['mission_discovery'] and profile['mission_subscription'] and profile['content_listing'], profile
assert profile['mission_cot_read'] and profile['create_edit_associate_delete'] and profile['semantic_readback'], profile
print('i565 centralized ATAK HTTP/Mission-token/CoT profile checks passed')
