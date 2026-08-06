#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, os, pathlib, sys, tempfile, time

ROOT = pathlib.Path(__file__).resolve().parents[1]
os.environ['TAK_MAP_DATA_DIR'] = tempfile.mkdtemp(prefix='tak-map-i602-identity-')
os.environ['TAK_MAP_MIL_ROOT'] = str(ROOT / 'assets/mil2525')
os.environ['TAK_MAP_TEST_SKIP_ADSB_WARMUP'] = '1'
spec = importlib.util.spec_from_file_location('tak_dashboard_i602_identity', ROOT / 'tak_dashboard.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader
spec.loader.exec_module(mod)

assert mod.TAK_MAP_ITERATION == 'i602'
assert mod.tak_map_config()['version'] == '1.3.0-i602'

cfg = {'api_url':'https://ots','base_url':'https://ots','marti_url':'https://ots:8443'}
sess = {'auth_mode':'ots-user','username':'alice','tak_uid':'alice-uid','callsign':'ALICE'}
mission = 'TAKMAP-DATASYNC-TEST2'
state = {
    'discovery_uids': ['CONTENT-UUID-A'],
    'event_uid': 'COT-EVENT-UID-A',
    'empty': False,
}
network = {'cot': 0}

def event_xml(uid):
    return (
        f'<event version="2.0" uid="{uid}" type="a-f-G-U-C" how="h-e" '
        'time="2026-07-30T20:00:00Z" start="2026-07-30T20:00:00Z" stale="2026-07-30T20:10:00Z">'
        '<point lat="34.100000" lon="-117.200000" hae="100" ce="10" le="10"/>'
        '<detail><contact callsign="IDENTITY TEST"/></detail></event>'
    )

def discovery_result():
    row = {
        'name': mission,
        'passwordProtected': True,
        'uids': list(state['discovery_uids']),
        'contents': [],
    }
    return {'ok':True,'status':200,'json':{'version':3,'type':'Mission','data':[row]},'body':{},'error':''}

def run_parallel(jobs, cfg_arg, sess_arg, token, deadline, workers):
    responses = {url: discovery_result() for url, path, endpoint, timeout in jobs}
    timings = [{'endpoint':endpoint,'ok':True,'status':200,'duration_seconds':0.001,'error':''}
               for url, path, endpoint, timeout in jobs]
    return responses, timings

mod._i569_run_parallel = run_parallel
mod._i572_creator_uid = lambda: 'creator'
mod._i572_load_password = lambda name, session=None: {'ok':True,'password':'secret'}
mod._i591_load_index = lambda session=None: {}
mod._i591_remember_mission = lambda *a, **k: None
mod._i591_mark_validated = lambda *a, **k: None
mod._i591_invalidate_validation = lambda *a, **k: None
mod._i564_invalidate_mission_token = lambda *a, **k: None
mod._i572_subscribe_with_password = lambda *a, **k: {
    'ok':True,'status':200,'token':'mission-token','source':'test','reused':True,
}

def cot(path, method='GET', body=None, headers=None, token='', timeout=0, **kwargs):
    network['cot'] += 1
    assert token == 'mission-token'
    body_text = '<events></events>' if state['empty'] else '<events>' + event_xml(state['event_uid']) + '</events>'
    return {'ok':True,'status':200,'json':{},'body':body_text,'error':''}
mod._i564_mission_request_raw = cot
mod._i600_schedule_supplement = lambda *a, **k: False

# Full /cot cycle: discovery content UUID differs from the authoritative CoT UID.
raw1, acq1 = mod._i600_build_raw_snapshot(
    cfg, sess, 'user-token', 'initial',
    {'force_cot':True, 'previous_discovery_uid_by_mission':{}}, None, None,
)
first, access1, lkg = mod._i601_reconcile(raw1, acq1, None, cfg, sess, {})
lkg = mod._i600_update_lkg(lkg, first, acq1)
assert network['cot'] == 1
assert [mod._i599_uid(row) for row in first['objects']] == ['COT-EVENT-UID-A']
assert acq1['mission_results_i599'][mission.lower()]['discovery_uids_i599'] == ['CONTENT-UUID-A']

# Membership-only cycle: same discovery fingerprint, no /cot request. The full
# cached CoT event set must survive unchanged despite the identifier mismatch.
raw2, acq2 = mod._i600_build_raw_snapshot(
    cfg, sess, 'user-token', 'membership-only',
    {
        'force_cot':False,
        'last_cot_epoch_by_mission':{mission.lower():time.time()},
        'previous_discovery_uid_by_mission':{mission.lower():['CONTENT-UUID-A']},
    },
    first, None,
)
assert acq2['summary']['cot_request_count'] == 0, acq2['summary']
second, access2, lkg2 = mod._i601_reconcile(raw2, acq2, first, cfg, sess, lkg)
assert [mod._i599_uid(row) for row in second['objects']] == ['COT-EVENT-UID-A'], second['objects']
assert not mod._i601_validate_snapshot(second, acq2, lkg)
continuity = second['data_sync_continuity_i601']['per_mission'][mission]
assert continuity['discovery_uids_used_to_prune_cot'] is False
assert continuity['object_count'] == 1
assert second['data_sync_reconciliation_i599']['per_mission'][mission]['discovery_uid_pruning_disabled_i601'] is True

# A changed discovery/content UUID fingerprint forces an immediate full /cot
# refresh. It is a trigger only; it is still never used to filter CoT event UIDs.
state['discovery_uids'] = ['CONTENT-UUID-B']
raw3, acq3 = mod._i600_build_raw_snapshot(
    cfg, sess, 'user-token', 'membership-changed',
    {
        'force_cot':False,
        'last_cot_epoch_by_mission':{mission.lower():time.time()},
        'previous_discovery_uid_by_mission':{mission.lower():['CONTENT-UUID-A']},
    },
    second, None,
)
assert acq3['summary']['cot_request_count'] == 1, acq3['summary']
assert acq3['mission_results_i599'][mission.lower()]['new_uid_detected_i599'] is True
third, access3, lkg3 = mod._i601_reconcile(raw3, acq3, second, cfg, sess, lkg2)
assert [mod._i599_uid(row) for row in third['objects']] == ['COT-EVENT-UID-A']

# A subsequent membership-only cycle with the new discovery fingerprint again
# preserves the complete CoT event set without another /cot call.
raw4, acq4 = mod._i600_build_raw_snapshot(
    cfg, sess, 'user-token', 'membership-only-2',
    {
        'force_cot':False,
        'last_cot_epoch_by_mission':{mission.lower():time.time()},
        'previous_discovery_uid_by_mission':{mission.lower():['CONTENT-UUID-B']},
    },
    third, None,
)
assert acq4['summary']['cot_request_count'] == 0
fourth, access4, lkg4 = mod._i601_reconcile(raw4, acq4, third, cfg, sess, lkg3)
assert [mod._i599_uid(row) for row in fourth['objects']] == ['COT-EVENT-UID-A']
assert not mod._i601_validate_snapshot(fourth, acq4, lkg3)

# Only a real successful empty /cot result may clear the Mission object set.
state['empty'] = True
raw5, acq5 = mod._i600_build_raw_snapshot(
    cfg, sess, 'user-token', 'authoritative-empty',
    {
        'force_cot':True,
        'last_cot_epoch_by_mission':{mission.lower():time.time()},
        'previous_discovery_uid_by_mission':{mission.lower():['CONTENT-UUID-B']},
    },
    fourth, None,
)
fifth, access5, lkg5 = mod._i601_reconcile(raw5, acq5, fourth, cfg, sess, lkg4)
assert acq5['summary']['cot_request_count'] == 1
assert not mod._i599_rows_for_mission(fifth, 'objects', mission)
assert fifth['data_sync_reconciliation_i599']['per_mission'][mission]['successful_empty_cot_authoritative_i599'] is True

# Final-worker state stores the discovery fingerprint separately from CoT UIDs.
state['empty'] = False
state['discovery_uids'] = ['CONTENT-UUID-C']
state['event_uid'] = 'COT-EVENT-UID-C'
key = mod._i568_state_key(cfg, sess)
with mod._I568_STATE_LOCK:
    worker_state = mod._i568_state(key)
    worker_state.clear()
    worker_state.update({
        'key': key,
        'snapshot': third,
        'generation': 61,
        'i599_worker_running': True,
        'in_flight': True,
        'i599_last_cot_epoch_by_mission': {mission.lower(): time.time()},
        'i601_last_discovery_uids_by_mission': {mission.lower(): ['CONTENT-UUID-C']},
        'i601_mission_lkg': mod._i600_update_lkg({}, third, acq3),
    })
assert mod._i568_refresh_worker(key, cfg, sess, 'user-token', 'worker-membership-only', 61, False) is True
with mod._I568_STATE_LOCK:
    worker_state = mod._i568_state(key)
    assert worker_state['completed_generation_i601'] == 61
    assert worker_state['i601_last_discovery_uids_by_mission'][mission.lower()] == ['CONTENT-UUID-C']
    assert [mod._i599_uid(row) for row in worker_state['snapshot']['objects']] == ['COT-EVENT-UID-A']
    assert worker_state['snapshot']['data_sync_continuity_i601']['discovery_uids_never_prune_cot_events'] is True

print('i602 discovery/CoT identity separation and continuity regression passed')
