#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
import pathlib
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
os.environ['TAK_MAP_DATA_DIR'] = tempfile.mkdtemp(prefix='tak-map-i599-authoritative-')
os.environ['TAK_MAP_MIL_ROOT'] = str(ROOT / 'assets/mil2525')
os.environ['TAK_MAP_TEST_SKIP_ADSB_WARMUP'] = '1'

spec = importlib.util.spec_from_file_location('tak_dashboard_i599_authoritative', ROOT / 'tak_dashboard.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader
spec.loader.exec_module(mod)

assert mod.TAK_MAP_ITERATION == 'i599'
assert mod.tak_map_config()['version'] == '1.3.0-i599'
real_augment_i599 = mod._i568_augment_before

cfg = {'api_url':'https://ots','base_url':'https://ots','marti_url':'https://ots:8443'}
sess = {'auth_mode':'ots-user','username':'alice','tak_uid':'alice-uid','callsign':'ALICE'}
mission = 'PROTECTED-ALPHA'
public_mission = 'PUBLIC-BRAVO'
uid = 'POINT-I599-1'
public_uid = 'POINT-I599-2'

def event_xml(event_uid, callsign, lat='34.1', lon='-117.2'):
    return (
        f'<event version="2.0" uid="{event_uid}" type="a-f-G-U-C" how="h-e" '
        'time="2026-07-30T12:00:00Z" start="2026-07-30T12:00:00Z" stale="2026-07-30T12:10:00Z">'
        f'<point lat="{lat}" lon="{lon}" hae="100" ce="10" le="10"/>'
        f'<detail><contact callsign="{callsign}"/></detail></event>'
    )

protected_discovery = {'ok':True,'status':200,'json':{'version':3,'type':'Mission','data':[
    {'name':mission,'passwordProtected':True,'contents':[{'hash':'PKG-1','name':'one.zip'}]},
    {'name':public_mission,'passwordProtected':False,'contents':[]},
]},'body':{},'error':''}
bare_discovery = {'ok':True,'status':200,'json':{'version':3,'type':'Mission','data':[
    {'name':public_mission,'passwordProtected':False,'contents':[]},
]},'body':{},'error':''}

network = {'protected_cot':0,'public_cot':0,'subscribe':0,'invalidated':0}
subscription_wrapper_i599 = mod._i572_subscribe_with_password

def run_parallel(jobs, cfg_arg, sess_arg, token, deadline, workers):
    responses = {}
    for url, path, endpoint, timeout in jobs:
        responses[url] = protected_discovery if 'passwordProtected=true' in url else bare_discovery
    return responses, [{'endpoint':j[2],'ok':True,'status':200,'error':''} for j in jobs]

mod._i569_run_parallel = run_parallel
mod._i572_creator_uid = lambda: 'creator-alice'
mod._i572_load_password = lambda name, session=None: {'ok': name == mission, 'password':'secret' if name == mission else ''}
mod._i572_store_password = lambda *a, **k: {'ok':True}
mod._i591_load_index = lambda session=None: {}
mod._i591_remember_mission = lambda *a, **k: None
mod._i591_mark_validated = lambda *a, **k: None
mod._i591_invalidate_validation = lambda *a, **k: None
mod._i564_invalidate_mission_token = lambda *a, **k: network.__setitem__('invalidated', network['invalidated'] + 1)

def subscribe(name, creator, password, server_host=''):
    network['subscribe'] += 1
    return {'ok':True,'status':200,'token':'mission-token','source':'test-subscription'}
mod._i572_subscribe_with_password = subscribe

def protected_cot(path, method='GET', body=None, headers=None, token='', timeout=0, **kwargs):
    network['protected_cot'] += 1
    assert token == 'mission-token'
    return {'ok':True,'status':200,'json':{},'body':'<events>'+event_xml(uid,'PROTECTED POINT')+'</events>','error':''}
mod._i564_mission_request_raw = protected_cot

def public_cot(path, method='GET', body=None, headers=None, timeout=0, **kwargs):
    network['public_cot'] += 1
    return {'ok':True,'status':200,'json':{},'body':'<events>'+event_xml(public_uid,'PUBLIC POINT','34.2','-117.3')+'</events>','error':''}
mod._i569_mission_request = public_cot

acquired = mod._i568_parallel_acquisition(cfg, sess)
assert acquired['summary']['discovery_ok'] is True
assert acquired['summary']['cot_request_count'] == 2
assert network['protected_cot'] == 1 and network['public_cot'] == 1, network
assert acquired['mission_results_i599'][mission.lower()]['unlocked'] is True
assert acquired['mission_results_i599'][mission.lower()]['state'] == 'ready'

# The raw builder bypasses all older Mission worker/reconciliation wrappers. This
# proves the final build uses the already-authorized /cot response exactly once.
mod.tak_map_data_sync = lambda: {'ok':True,'missions':[],'objects':[],'mission_uids':[],'mission_content':[],'packages':[],'sources':[]}
mod._i568_augment_before = lambda base, cfg_arg, sess_arg: base
raw, acquired2 = mod._i599_build_raw_snapshot(cfg, sess, 'user-token', 'test')
assert network['protected_cot'] == 2 and network['public_cot'] == 2, network
final, access = mod._i599_reconcile(raw, acquired2, None, cfg, sess)
assert any(str(row.get('uid') or row.get('event_uid')) == uid for row in final['objects']), final['objects']
assert any(str(row.get('uid') or row.get('event_uid')) == public_uid for row in final['objects']), final['objects']
assert next(row for row in access if row['mission'] == mission)['content_state_i599'] == 'ready'
assert final['data_sync_reconciliation_i599']['second_generic_cot_request'] is False

# Exercise the real mature normalization/augmentation path with the i599 seeded
# request context. It must consume the already-authorized response aliases and
# must not issue a second Mission /cot network request.
mod._i568_augment_before = real_augment_i599
before_real = dict(network)
raw_real, acquired_real = mod._i599_build_raw_snapshot(cfg, sess, 'user-token', 'real-augment-test')
assert network['protected_cot'] == before_real['protected_cot'] + 1, network
assert network['public_cot'] == before_real['public_cot'] + 1, network
final_real, access_real = mod._i599_reconcile(raw_real, acquired_real, final, cfg, sess)
assert any(str(row.get('uid') or row.get('event_uid')) == uid for row in final_real['objects']), final_real['objects']
assert any(str(row.get('uid') or row.get('event_uid')) == public_uid for row in final_real['objects']), final_real['objects']
assert any(str(row.get('hash') or (row.get('data') or {}).get('hash') or '') == 'PKG-1' for row in final_real.get('mission_content', [])), final_real.get('mission_content')
assert acquired_real['summary']['exactly_one_cot_request_per_unlocked_mission'] is True
assert acquired_real['summary']['network_get_contents_calls'] == 0
assert acquired_real['summary']['network_mission_detail_calls'] == 0
mod._i568_augment_before = lambda base, cfg_arg, sess_arg: base

# Final worker publication, not merely the intermediate parser/builder.
key = mod._i568_state_key(cfg, sess)
with mod._I568_STATE_LOCK:
    state = mod._i568_state(key)
    state.update({'generation':41,'i599_worker_running':True,'in_flight':True,'snapshot':None})
assert mod._i568_refresh_worker(key, cfg, sess, 'user-token', 'worker-test', 41) is True
with mod._I568_STATE_LOCK:
    state = mod._i568_state(key)
    assert state['completed_generation_i599'] == 41
    assert state['snapshot_generation_i599'] == 41
    assert state['i599_worker_running'] is False and state['in_flight'] is False
    assert any(str(row.get('uid') or row.get('event_uid')) == uid for row in state['snapshot']['objects'])

# Security filtering is read-only with respect to worker generation/lifecycle.
with mod._I568_STATE_LOCK:
    state['generation'] = 77
    state['in_flight'] = True
    state['i599_worker_running'] = True
before = (state['generation'], state['in_flight'], state['i599_worker_running'])
view, status = mod._i599_filter_security_view(state['snapshot'], state, sess)
after = (state['generation'], state['in_flight'], state['i599_worker_running'])
assert status == 200 and before == after, (before, after)

# Single-flight scheduling never queues a duplicate forced generation.
started, why = mod._i568_schedule_refresh(key, cfg, sess, 'user-token', 'duplicate-force', force=True)
assert started is False and why == 'already-running-singleflight-i599'
assert not state.get('i599_pending_refresh')
with mod._I568_STATE_LOCK:
    state['in_flight'] = False
    state['i599_worker_running'] = False

# Mixed lock states retain the unlocked Mission's content.
locked = 'LOCKED-CHARLIE'
mixed_acquired = mod._i568_clone(acquired2)
mixed_acquired['mission_rows'].append(mod._i599_descriptor(locked, True, False, 'locked', sess=sess))
mixed_acquired['mission_results_i599'][locked.lower()] = {'mission':locked,'protected':True,'unlocked':False,'state':'locked'}
mixed, mixed_access = mod._i599_reconcile(raw, mixed_acquired, final, cfg, sess)
assert mixed['partially_locked_i599'] is True and mixed['locked'] is False
assert any(str(row.get('uid') or row.get('event_uid')) == uid for row in mixed['objects'])
assert any(row['mission'] == locked and row['locked'] for row in mixed_access)
filtered, _ = mod._i599_filter_security_view(mixed, {'i599_mission_access':mixed_access}, sess)
assert any(str(row.get('uid') or row.get('event_uid')) == uid for row in filtered['objects'])
assert not any(str(row.get('mission') or row.get('mission_name')).lower() == locked.lower() for row in filtered['objects'])

# Successful empty /cot is authoritative and clears only that Mission.
empty_acquired = mod._i568_clone(acquired2)
url = cfg['marti_url'] + '/Marti/api/missions/' + mission + '/cot'
empty_acquired['responses'][url] = mod._i569_parsed_result({'ok':True,'status':200,'json':{},'body':'<events></events>','error':''})
empty_acquired['mission_rows'] = [row for row in empty_acquired['mission_rows'] if mod._i599_mission_name(row) == mission]
empty_acquired['mission_results_i599'] = {mission.lower():{'mission':mission,'protected':True,'unlocked':True,'state':'ready','cot_ok':True}}
empty, empty_access = mod._i599_reconcile({'missions':[],'objects':[],'mission_uids':[],'mission_content':[],'packages':[]}, empty_acquired, final, cfg, sess)
assert not any(mod._i599_mission_name(row).lower() == mission.lower() for row in empty['objects'])
assert next(row for row in empty_access if row['mission'] == mission)['content_authoritative_i599'] is True

# A non-auth /cot failure preserves that Mission's last-known-good data and stops
# loading with an explicit error state.
failed_acquired = mod._i568_clone(empty_acquired)
failed_acquired['responses'][url] = {'ok':False,'status':503,'json':{},'body':None,'error':'temporary outage'}
failed_acquired['mission_results_i599'][mission.lower()].update({'state':'error','cot_ok':False,'cot_status':503,'cot_error':'temporary outage'})
failed, failed_access = mod._i599_reconcile({'missions':[],'objects':[],'mission_uids':[],'mission_content':[],'packages':[]}, failed_acquired, final, cfg, sess)
assert any(str(row.get('uid') or row.get('event_uid')) == uid for row in failed['objects'])
failed_row = next(row for row in failed_access if row['mission'] == mission)
assert failed_row['content_state_i599'] == 'error' and failed_row['content_authoritative_i599'] is False
assert failed.get('partial') is True and failed.get('warnings')

# The password action validates exactly once, marks that returned token valid,
# and schedules only one worker after the validation state is available. The
# worker-side subscription wrapper can then reuse the token without another
# subscription network request.
unlock_calls = {'subscribe':0,'scheduled':0,'validated_token':'','stored':0}
mod._i572_session = lambda: dict(sess)
mod._i572_creator_uid = lambda: 'creator-alice'
mod._i572_store_password = lambda m, p, s=None: unlock_calls.__setitem__('stored', unlock_calls['stored']+1) or {'ok':True}
mod._i572_set_protected = lambda *a, **k: None
mod._i599_subscribe_before = lambda *a, **k: unlock_calls.__setitem__('subscribe', unlock_calls['subscribe']+1) or {'ok':True,'status':200,'token':'unlock-token','source':'password-test'}
mod._i591_mark_validated = lambda m, s, token, source='': unlock_calls.__setitem__('validated_token', token)
mod._i568_schedule_refresh = lambda *a, **k: (unlock_calls.__setitem__('scheduled', unlock_calls['scheduled']+1) or True, 'scheduled-i599')
reply, reply_status = mod._i572_unlock_action({'action':'unlock','mission':mission,'password':'secret'})
assert reply_status == 200 and reply.get('unlocked') is True and reply.get('content_state_i599') == 'loading', reply
assert unlock_calls == {'subscribe':1,'scheduled':1,'validated_token':'unlock-token','stored':1}, unlock_calls

# A replacement password must be validated itself. The action intentionally
# bypasses cache reuse so an old token can never make an arbitrary new password
# appear valid.
mod._i599_subscribe_before = lambda *a, **k: {'ok':False,'status':401,'invalid_password':True,'error':'Invalid Mission password.'}
wrong, wrong_status = mod._i572_unlock_action({'action':'unlock','mission':mission,'password':'wrong'})
assert wrong_status == 401 and wrong.get('invalid_password') is True
assert unlock_calls['stored'] == 1 and unlock_calls['scheduled'] == 1

# Cached valid subscription token is reused without a network subscription call.
cache_calls = {'network':0}
mod._i572_cached_token = lambda m, c: 'cached-token'
mod._i591_is_validated = lambda m, s=None: True
mod._i599_subscribe_before = lambda *a, **k: cache_calls.__setitem__('network', cache_calls['network']+1) or {'ok':True,'token':'network'}
mod._i572_subscribe_with_password = subscription_wrapper_i599
reused = mod._i572_subscribe_with_password(mission, 'creator-alice', 'secret')
assert reused['token'] == 'cached-token' and reused['reused'] is True and cache_calls['network'] == 0

# Protected /cot authorization expiry relocks and invalidates the stale token.
mod._i572_subscribe_with_password = lambda *a, **k: {'ok':True,'status':200,'token':'expired-token','source':'cache','reused':True}
mod._i564_mission_request_raw = lambda *a, **k: {'ok':False,'status':401,'json':{},'body':None,'error':'Mission token expired'}
mod._i569_run_parallel = run_parallel
expired = mod._i568_parallel_acquisition(cfg, sess)
info = expired['mission_results_i599'][mission.lower()]
assert info['state'] == 'locked' and info['unlocked'] is False and info['authorization_expired_i599'] is True
assert network['invalidated'] >= 1

print('i599 authoritative Data Sync backend regression passed')
