#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
import pathlib
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
os.environ['TAK_MAP_DATA_DIR'] = tempfile.mkdtemp(prefix='tak-map-i600-complete-')
os.environ['TAK_MAP_MIL_ROOT'] = str(ROOT / 'assets/mil2525')
os.environ['TAK_MAP_TEST_SKIP_ADSB_WARMUP'] = '1'

spec = importlib.util.spec_from_file_location('tak_dashboard_i600_complete', ROOT / 'tak_dashboard.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader
spec.loader.exec_module(mod)

assert mod.TAK_MAP_ITERATION == 'i600'
config = mod.tak_map_config()
assert config['data_sync_authoritative_i599']['membership_refresh_interval_seconds'] == 10
assert config['data_sync_authoritative_i599']['cot_refresh_interval_seconds'] == 20
assert config['data_sync_authoritative_i599']['network_get_contents_calls'] == 0

cfg = {'api_url': 'https://ots', 'base_url': 'https://ots', 'marti_url': 'https://ots:8443'}
sess = {'auth_mode': 'ots-user', 'username': 'alice', 'tak_uid': 'alice-uid', 'callsign': 'ALICE'}
protected = 'PROTECTED-ALPHA'
public = 'PUBLIC-BRAVO'
uid1 = 'POINT-1'
uid2 = 'POINT-2'
public_uid = 'PUBLIC-1'


def xml_event(uid, callsign, lat='34.1', lon='-117.2'):
    return (
        f'<event version="2.0" uid="{uid}" type="a-f-G-U-C" how="h-e" '
        'time="2026-07-30T12:00:00Z" start="2026-07-30T12:00:00Z" stale="2026-07-30T12:10:00Z">'
        f'<point lat="{lat}" lon="{lon}" hae="100" ce="10" le="10"/>'
        f'<detail><contact callsign="{callsign}"/></detail></event>'
    )

state = {
    'protected_uids': [uid1],
    'protected_contents': [{'hash': 'PKG-1', 'name': 'one.zip'}],
    'public_uids': [public_uid],
    'public_contents': [],
    'protected_xml': '<events>' + xml_event(uid1, 'PROTECTED ONE') + '</events>',
    'public_xml': '<events>' + xml_event(public_uid, 'PUBLIC ONE', '34.2', '-117.3') + '</events>',
    'protected_status': 200,
    'public_status': 200,
}
network = {'protected_cot': 0, 'public_cot': 0, 'subscribe': 0, 'invalidated': 0, 'contents_get': 0}


def discovery_payload(include_protected):
    rows = []
    if include_protected:
        rows.append({
            'name': protected, 'passwordProtected': True,
            'uids': list(state['protected_uids']), 'contents': list(state['protected_contents']),
        })
    rows.append({
        'name': public, 'passwordProtected': False,
        'uids': list(state['public_uids']), 'contents': list(state['public_contents']),
    })
    return {'ok': True, 'status': 200, 'json': {'version': 3, 'type': 'Mission', 'data': rows}, 'body': {}, 'error': ''}


def run_parallel(jobs, cfg_arg, sess_arg, token, deadline, workers):
    responses = {}
    timings = []
    for url, path, endpoint, timeout in jobs:
        responses[url] = discovery_payload('passwordProtected=true' in url)
        timings.append({'endpoint': endpoint, 'ok': True, 'status': 200, 'error': ''})
    return responses, timings

mod._i569_run_parallel = run_parallel
mod._i572_creator_uid = lambda: 'creator-alice'
mod._i572_load_password = lambda name, session=None: {'ok': name == protected, 'password': 'secret' if name == protected else ''}
mod._i572_store_password = lambda *a, **k: {'ok': True}
mod._i591_load_index = lambda session=None: {}
mod._i591_remember_mission = lambda *a, **k: None
mod._i591_mark_validated = lambda *a, **k: None
mod._i591_invalidate_validation = lambda *a, **k: None
mod._i564_invalidate_mission_token = lambda *a, **k: network.__setitem__('invalidated', network['invalidated'] + 1)


def subscribe(name, creator, password, server_host=''):
    network['subscribe'] += 1
    return {'ok': True, 'status': 200, 'token': 'mission-token', 'source': 'test-subscription', 'reused': network['subscribe'] > 1}

mod._i572_subscribe_with_password = subscribe


def protected_request(path, method='GET', body=None, headers=None, token='', timeout=0, **kwargs):
    assert not path.endswith('/contents'), 'GET /contents must never be issued'
    network['protected_cot'] += 1
    assert token == 'mission-token'
    if state['protected_status'] != 200:
        return {'ok': False, 'status': state['protected_status'], 'json': {}, 'body': None, 'error': 'protected failure'}
    return {'ok': True, 'status': 200, 'json': {}, 'body': state['protected_xml'], 'error': ''}


def public_request(path, method='GET', body=None, headers=None, timeout=0, **kwargs):
    assert not path.endswith('/contents'), 'GET /contents must never be issued'
    network['public_cot'] += 1
    if state['public_status'] != 200:
        return {'ok': False, 'status': state['public_status'], 'json': {}, 'body': None, 'error': 'public failure'}
    return {'ok': True, 'status': 200, 'json': {}, 'body': state['public_xml'], 'error': ''}

mod._i564_mission_request_raw = protected_request
mod._i569_mission_request = public_request

# Initial/forced content cycle: one /cot per unlocked Mission, no GET /contents.
initial = mod._i568_parallel_acquisition(cfg, sess, {'force_cot': True})
assert initial['summary']['cot_request_count'] == 2
assert initial['summary']['network_get_contents_calls'] == 0
assert network['protected_cot'] == 1 and network['public_cot'] == 1
assert initial['mission_results_i599'][protected.lower()]['cot_refresh_completed_i599'] is True

# Reconcile a completed authoritative cycle.
base = {
    'ok': True,
    'missions': initial['mission_rows'],
    'objects': [], 'mission_uids': [],
    'mission_content': [
        {'mission_name': protected, 'hash': 'PKG-1', 'name': 'one.zip'},
    ],
    'mission_content_mission': [], 'packages': [], 'mission_logs': [], 'mission_roles': [],
}
completed, completed_access = mod._i599_reconcile(base, initial, None, cfg, sess)
assert {mod._i599_uid(row) for row in completed['objects']} == {uid1, public_uid}
assert next(row for row in completed_access if row['mission'] == protected)['content_state_i599'] == 'ready'

# A 10-second membership-only cycle makes no /cot request, preserves completed
# objects, applies discovery content updates, and stops any loading state.
now = time.time()
before = dict(network)
state['protected_contents'] = [{'hash': 'PKG-2', 'name': 'two.zip'}]
member_only = mod._i568_parallel_acquisition(cfg, sess, {
    'force_cot': False,
    'last_cot_epoch_by_mission': {protected.lower(): now, public.lower(): now},
    'previous_uid_by_mission': mod._i599_snapshot_uid_map(completed),
})
assert member_only['summary']['cot_request_count'] == 0
assert network['protected_cot'] == before['protected_cot'] and network['public_cot'] == before['public_cot']
member_raw = {
    'ok': True,
    'missions': member_only['mission_rows'],
    'objects': [], 'mission_uids': [],
    'mission_content': [{'mission_name': protected, 'hash': 'PKG-2', 'name': 'two.zip'}],
    'mission_content_mission': [], 'packages': [], 'mission_logs': [], 'mission_roles': [],
}
member_snapshot, member_access = mod._i599_reconcile(member_raw, member_only, completed, cfg, sess)
assert {mod._i599_uid(row) for row in member_snapshot['objects']} == {uid1, public_uid}
assert any(str(row.get('hash') or '') == 'PKG-2' for row in member_snapshot['mission_content'])
assert not any(str(row.get('hash') or '') == 'PKG-1' for row in member_snapshot['mission_content'])
assert all(row['content_state_i599'] == 'ready' for row in member_access if row.get('unlocked'))

# Membership deletion is applied on the 10-second cycle without waiting for CoT.
state['protected_uids'] = []
member_removed = mod._i568_parallel_acquisition(cfg, sess, {
    'last_cot_epoch_by_mission': {protected.lower(): now, public.lower(): now},
    'previous_uid_by_mission': mod._i599_snapshot_uid_map(member_snapshot),
})
removed_snapshot, _ = mod._i599_reconcile(member_raw, member_removed, member_snapshot, cfg, sess)
assert not any(mod._i599_row_mission(row, 'objects') == protected for row in removed_snapshot['objects'])
assert any(mod._i599_uid(row) == public_uid for row in removed_snapshot['objects'])

# A newly discovered UID forces immediate CoT even inside the 20-second window.
state['protected_uids'] = [uid1, uid2]
state['protected_xml'] = '<events>' + xml_event(uid1, 'PROTECTED ONE') + xml_event(uid2, 'PROTECTED TWO') + '</events>'
before = dict(network)
new_uid_cycle = mod._i568_parallel_acquisition(cfg, sess, {
    'last_cot_epoch_by_mission': {protected.lower(): now, public.lower(): now},
    'previous_uid_by_mission': {protected.lower(): [uid1], public.lower(): [public_uid]},
})
assert new_uid_cycle['summary']['cot_due_to_new_uid_count'] == 1
assert network['protected_cot'] == before['protected_cot'] + 1
assert network['public_cot'] == before['public_cot']
new_snapshot, _ = mod._i599_reconcile(base, new_uid_cycle, member_snapshot, cfg, sess)
assert {uid1, uid2}.issubset({mod._i599_uid(row) for row in new_snapshot['objects']})

# Successful empty CoT is authoritative for only that Mission.
state['protected_xml'] = '<events></events>'
empty_cycle = mod._i568_parallel_acquisition(cfg, sess, {
    'force_cot': True,
    'previous_uid_by_mission': mod._i599_snapshot_uid_map(new_snapshot),
})
empty_snapshot, _ = mod._i599_reconcile(base, empty_cycle, new_snapshot, cfg, sess)
assert not any(mod._i599_row_mission(row, 'objects') == protected for row in empty_snapshot['objects'])
assert any(mod._i599_uid(row) == public_uid for row in empty_snapshot['objects'])

# A temporary CoT failure preserves only that Mission's LKG and records Error.
state['protected_xml'] = '<events>' + xml_event(uid1, 'PROTECTED ONE') + '</events>'
state['protected_status'] = 503
failed_cycle = mod._i568_parallel_acquisition(cfg, sess, {'force_cot': True})
failed_snapshot, failed_access = mod._i599_reconcile(base, failed_cycle, new_snapshot, cfg, sess)
assert any(mod._i599_uid(row) == uid1 for row in failed_snapshot['objects'])
failed_access_row = next(row for row in failed_access if row['mission'] == protected)
assert failed_access_row['content_state_i599'] == 'error'
assert failed_snapshot.get('partial') is True
state['protected_status'] = 200

# A locked Mission exposes only its descriptor while an unlocked Mission remains.
locked_acquired = mod._i568_clone(initial)
locked_acquired['mission_rows'] = [
    mod._i599_descriptor(protected, True, False, 'locked', sess=sess),
    next(row for row in initial['mission_rows'] if mod._i599_mission_name(row) == public),
]
locked_acquired['mission_results_i599'][protected.lower()] = {
    'mission': protected, 'protected': True, 'unlocked': False, 'state': 'locked'
}
mixed, mixed_access = mod._i599_reconcile(base, locked_acquired, new_snapshot, cfg, sess)
assert mixed['partially_locked_i599'] is True and mixed['locked'] is False
assert not any(mod._i599_row_mission(row, 'objects') == protected for row in mixed['objects'])
assert any(mod._i599_uid(row) == public_uid for row in mixed['objects'])

# Security projection is read-only and filters by explicit Mission scope, not a
# point callsign/name that happens to equal a locked Mission name.
scoped = mod._i568_clone(mixed)
scoped['objects'].append({'uid': 'UNSCOPED', 'name': protected, 'lat': 1, 'lon': 2})
worker_state = {'generation': 9, 'in_flight': True, 'i599_worker_running': True, 'i599_mission_access': mixed_access}
before_lifecycle = (worker_state['generation'], worker_state['in_flight'], worker_state['i599_worker_running'])
view, status = mod._i599_filter_security_view(scoped, worker_state, sess)
after_lifecycle = (worker_state['generation'], worker_state['in_flight'], worker_state['i599_worker_running'])
assert status == 200 and before_lifecycle == after_lifecycle
assert any(mod._i599_uid(row) == 'UNSCOPED' for row in view['objects'])

# Final worker stores per-Mission CoT completion time and a membership-only cycle
# does not reset Ready to Loading.
mod.tak_map_data_sync = lambda: {'ok': True, 'missions': [], 'objects': [], 'mission_uids': [], 'mission_content': [], 'mission_content_mission': [], 'packages': [], 'mission_logs': [], 'mission_roles': [], 'sources': []}
mod._i568_augment_before = lambda base_arg, cfg_arg, sess_arg: base_arg
key = mod._i568_state_key(cfg, sess)
with mod._I568_STATE_LOCK:
    backend_state = mod._i568_state(key)
    backend_state.update({'generation': 101, 'i599_worker_running': True, 'in_flight': True, 'snapshot': None})
assert mod._i568_refresh_worker(key, cfg, sess, 'user-token', 'forced-test', 101, True) is True
with mod._I568_STATE_LOCK:
    backend_state = mod._i568_state(key)
    assert backend_state['i599_last_cot_epoch_by_mission'][protected.lower()] > 0
    assert backend_state['completed_generation_i599'] == 101
    for access in backend_state['i599_mission_access']:
        if access.get('unlocked'):
            assert access['content_state_i599'] == 'ready'

print('i600 complete Data Sync cadence and reconciliation regression passed')
