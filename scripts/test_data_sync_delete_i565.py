import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tak_dashboard_i565_delete_test', ROOT / 'tak_dashboard.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

assert mod.TAK_MAP_ITERATION == 'i565'
assert mod._I565_ATAK_USER_AGENT.startswith('ATAK/')
assert 'iTAK' not in mod._I565_ATAK_USER_AGENT

obj = {
    'object_id': 'point-uid-1',
    'mission_name': 'Mission Alpha',
    'mission_delete_target': 'uid',
    'mission_delete_value': 'POINT-UID-1',
    'delete_supported': True,
}

old_creator = mod._i528_strict_creator
old_request = mod._ots_mission_api_request
old_identity = mod._i565_request_identity_key
try:
    mod._i528_strict_creator = lambda: {
        'ok': True,
        'uid': 'ANDROID-ATAK-EUD-01',
        'source': 'per-user-enrolled-marti-certificate-i529',
        'shared_service_fallback': False,
    }
    mod._i565_request_identity_key = lambda: 'user-a/ANDROID-ATAK-EUD-01'
    mod._I565_MISSION_TOKENS.clear()
    calls = []

    def request_ok(path, method='GET', body=None, headers=None, token='', public_host='', timeout=25):
        calls.append({'path': path, 'method': method, 'body': body, 'headers': dict(headers or {}), 'token': token})
        if path.endswith('/subscription?uid=ANDROID-ATAK-EUD-01'):
            return {'ok': True, 'status': 200, 'json': {'data': {'token': 'mission-token-1'}}}
        if '/contents?' in path:
            return {'ok': True, 'status': 200, 'json': {'data': []}}
        raise AssertionError(path)

    mod._ots_mission_api_request = request_ok
    result = mod._i565_tokenized_delete_record(obj)
    assert result['status'] == 'deleted', result
    assert result['user_agent_family'] == 'ATAK' and result['mission_auth'] == 'ATAK-style subscription token', result
    assert len(calls) == 2, calls
    subscribe, delete = calls
    assert subscribe['method'] == 'PUT' and '/subscription?uid=ANDROID-ATAK-EUD-01' in subscribe['path'], subscribe
    assert subscribe['token'] == '', subscribe
    assert delete['method'] == 'DELETE' and '/contents?' in delete['path'], delete
    assert 'creatorUid=ANDROID-ATAK-EUD-01' in delete['path'] and 'uid=POINT-UID-1' in delete['path'], delete
    assert delete['token'] == 'mission-token-1', delete
    for call in calls:
        ua = call['headers'].get('User-Agent', '')
        assert ua == mod._I565_ATAK_USER_AGENT, call
        assert 'iTAK' not in ua, call
    assert result.get('shared_service_fallback') is not True

    # A rejected token is refreshed exactly once and the DELETE is retried.
    mod._I565_MISSION_TOKENS.clear()
    calls.clear()
    counts = {'subscription': 0, 'delete': 0}
    def request_refresh(path, method='GET', body=None, headers=None, token='', public_host='', timeout=25):
        calls.append({'path': path, 'method': method, 'headers': dict(headers or {}), 'token': token})
        if '/subscription?' in path:
            counts['subscription'] += 1
            return {'ok': True, 'status': 200, 'json': {'data': {'token': f"mission-token-{counts['subscription']}"}}}
        counts['delete'] += 1
        if counts['delete'] == 1:
            # Match the per-user Mission helper's HTTPError shape: status is nested in attempts.
            return {'ok': False, 'error': 'The per-user OpenTAKServer Mission API request failed.',
                    'attempts': [{'status': 401, 'error': 'HTTP Error 401', 'body_preview': '{"error":"Mission token expired"}'}]}
        return {'ok': True, 'status': 200, 'json': {}}
    mod._ots_mission_api_request = request_refresh
    result = mod._i565_tokenized_delete_record(obj)
    assert result['status'] == 'deleted' and result['token_refreshed'] is True, result
    assert counts == {'subscription': 2, 'delete': 2}, calls
    assert [c['token'] for c in calls if c['method'] == 'DELETE'] == ['mission-token-1', 'mission-token-2'], calls

    # Failure details are useful but tokens and certificate paths stay hidden.
    mod._I565_MISSION_TOKENS.clear()
    def request_fail(path, method='GET', body=None, headers=None, token='', public_host='', timeout=25):
        if '/subscription?' in path:
            return {'ok': True, 'status': 200, 'json': {'data': {'token': 'super-secret-token'}}}
        return {
            'ok': False,
            'status': 403,
            'json': {'error': 'Mission role does not permit deletion'},
            'body': '{"error":"Mission role does not permit deletion"}',
            'cert': '/var/lib/tak-map/users/alice/private.key',
        }
    mod._ots_mission_api_request = request_fail
    result = mod._i565_tokenized_delete_record(obj)
    assert result['status'] == 'failed' and result['http_status'] == 403, result
    assert 'Mission role does not permit deletion' in result['error'], result
    serialized = repr(result)
    assert 'super-secret-token' not in serialized and 'private.key' not in serialized, result

    # No per-user enrolled EUD identity means no Mission request and no fallback.
    request_count = 0
    mod._i528_strict_creator = lambda: {'ok': False, 'error': 'Per-user certificate not enrolled'}
    def should_not_call(*args, **kwargs):
        raise AssertionError('Mission API must not run without a per-user identity')
    mod._ots_mission_api_request = should_not_call
    result = mod._i565_tokenized_delete_record(obj)
    assert result['status'] == 'failed' and result['shared_service_fallback'] is False, result
finally:
    mod._i528_strict_creator = old_creator
    mod._ots_mission_api_request = old_request
    mod._i565_request_identity_key = old_identity
    mod._I565_MISSION_TOKENS.clear()

cfg = mod.tak_map_config()
assert cfg['data_sync_delete_ui']['right_context_sidebar'] is True
assert cfg['data_sync_delete_ui']['shared_card_sidebar_controller'] is True
assert cfg['data_sync_delete_ui']['native_alert_confirm_prompt'] is False
assert cfg['data_sync_mission_delete']['user_agent_family'] == 'ATAK'
assert cfg['data_sync_mission_delete']['itak_user_agent'] is False
assert cfg['data_sync_mission_delete']['mission_subscription_token'] is True
assert cfg['data_sync_mission_delete']['token_refresh_retry'] is True
print('i565 ATAK-style per-user Mission token acquisition, deletion, refresh retry, and sanitized failure checks passed')
