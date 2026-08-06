#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tak_dashboard_i602_delete_identity_test', ROOT / 'tak_dashboard.py')
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

assert mod.TAK_MAP_ITERATION == 'i602'
assert mod.tak_map_config()['version'] == '1.3.0-i602'

mission = 'TAKMAP-DATASYNC-TEST2'
event_uid = 'TAKMAP-MISSION-POINT-f4d266fe311a4995ba7e3d82eeca'
content_uuid = 'c2b7d3b6-d884-4d05-ac54-afb565be257'
payload = {
    'ok': True,
    'version': 'i601',
    'objects': [{
        'uid': event_uid,
        'event_uid': event_uid,
        'cot_uid': event_uid,
        'mission': mission,
        'mission_name': mission,
        'source': 'OpenTAKServer Mission /cot XML i598',
        'kind': 'datasync',
        'is_mission_object': True,
        'cot_xml_projected_i598': True,
        'lat': 34.1,
        'lon': -117.2,
        'callsign': 'Tank',
    }],
    # Discovery/content UUID intentionally differs from the CoT event UID.
    'mission_uids': [{
        'uid': content_uuid,
        'mission': mission,
        'mission_name': mission,
        'source': 'OpenTAKServer Mission discovery content identifier',
    }],
    'mission_access_i599': [{
        'mission': mission,
        'name': mission,
        'protected': True,
        'unlocked': True,
        'locked': False,
        'content_state_i599': 'ready',
        'content_authoritative_i599': True,
    }],
    'data_sync_reconciliation_i599': {
        'per_mission': {
            mission: {
                'state': 'ready',
                'authoritative': True,
                'object_count': 1,
                'cot_refresh_completed_i599': True,
            }
        }
    },
}

out = mod._i602_apply_deletion_identity(payload)
assert len(out['objects']) == 1
point = out['objects'][0]
expected_object_id = 'datasync-' + hashlib.sha256(('uid:' + event_uid).encode()).hexdigest()[:24]
assert point['object_id'] == expected_object_id
assert point['canonical_id'] == 'datasync:' + expected_object_id
assert point['mission_name'] == mission
assert point['mission_delete_target'] == 'uid'
assert point['mission_delete_value'] == event_uid
assert point['mission_delete_value'] != content_uuid
assert point['delete_supported'] is True
assert 'delete_unavailable_reason' not in point
assert point['deletion_identity_i602']['post_reconciliation'] is True
assert point['deletion_identity_i602']['discovery_content_uuid_not_used'] is True
assert out['data_sync_deletion_identity_i602']['identity'] == 'exact-mission-plus-cot-event-uid'
assert out['data_sync_deletion_identity_i602']['discovery_content_uuid_used_for_delete'] is False
assert mod._i601_validate_snapshot(out, {}, {}) == []

# Membership-only generations carry the same exact identity forward.
carried = mod._i602_apply_deletion_identity(out)
carried_point = carried['objects'][0]
assert carried_point['canonical_id'] == point['canonical_id']
assert carried_point['mission_delete_value'] == event_uid
assert carried_point['delete_supported'] is True

# A locked Mission cannot retain a stale positive deletion identity.
locked = dict(out)
locked['mission_access_i599'] = [{
    'mission': mission,
    'protected': True,
    'unlocked': False,
    'locked': True,
    'content_state_i599': 'locked',
    'content_authoritative_i599': False,
}]
locked['data_sync_reconciliation_i599'] = {'per_mission': {mission: {'state': 'locked', 'authoritative': False}}}
locked_out = mod._i602_apply_deletion_identity(locked)
locked_point = locked_out['objects'][0]
assert locked_point['delete_supported'] is False
assert locked_point['mission_delete_target'] == ''
assert locked_point['mission_delete_value'] == ''

# The existing tokenized Mission deletion transport receives exact Mission + CoT UID.
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
        calls.append({'path': path, 'method': method, 'token': token, 'headers': dict(headers or {})})
        if '/subscription?' in path:
            return {'ok': True, 'status': 200, 'json': {'data': {'token': 'mission-token-i602'}}}
        if '/contents?' in path:
            return {'ok': True, 'status': 200, 'json': {}}
        raise AssertionError(path)

    mod._ots_mission_api_request = request_ok
    result = mod._i565_tokenized_delete_record(point)
    assert result['status'] == 'deleted', result
    delete_call = next(call for call in calls if call['method'] == 'DELETE')
    assert '/Marti/api/missions/TAKMAP-DATASYNC-TEST2/contents?' in delete_call['path']
    assert 'uid=' + event_uid in delete_call['path']
    assert content_uuid not in delete_call['path']
    assert delete_call['token'] == 'mission-token-i602'
finally:
    mod._i528_strict_creator = old_creator
    mod._ots_mission_api_request = old_request
    mod._i565_request_identity_key = old_identity
    mod._I565_MISSION_TOKENS.clear()

# Invariant validation rejects a regression that removes the final delete fields.
broken = mod._i568_clone(out)
broken['objects'][0]['delete_supported'] = False
errors = mod._i601_validate_snapshot(broken, {}, {})
assert any('deletion identity incomplete' in error for error in errors), errors

print('i602 authoritative Mission deletion identity and exact tokenized delete target checks passed')
