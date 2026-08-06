#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import pathlib
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tak_dashboard_i581_cadence', ROOT / 'tak_dashboard.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader is not None
spec.loader.exec_module(mod)

assert mod._I581_MEMBERSHIP_INTERVAL_SECONDS == 10
assert mod._I581_FULL_COT_INTERVAL_SECONDS == 20
assert mod._I568_SNAPSHOT_MAX_AGE_SECONDS == 10

snapshot_root = pathlib.Path(tempfile.mkdtemp(prefix='takmap-i581-snapshots-'))
mod._I568_SNAPSHOT_ROOT = snapshot_root
mod._I568_STATES.clear()

mission = 'MISSION-I581'
current_uids = ['UID-A', 'UID-B']
enrichment_calls: list[str] = []


def marker(uid: str) -> dict:
    offset = 1 if uid == 'UID-A' else 2 if uid == 'UID-B' else 3
    return {
        'uid': uid,
        'event_uid': uid,
        'mission': mission,
        'mission_name': mission,
        'callsign': uid,
        'name': uid,
        'lat': 34.0 + offset / 100,
        'lon': -118.0 - offset / 100,
        'cot_type': 'a-f-G',
        'source': 'OpenTAKServer MissionUID discovery i581 test',
        'kind': 'datasync',
        'is_mission_object': True,
    }


def fake_build_snapshot(cfg, sess, token, reason):
    uids = [marker(uid) for uid in current_uids]
    mission_row = {
        'name': mission,
        'passwordProtected': False,
        'uids': uids,
        'contents': [],
    }
    snapshot = {
        'ok': True,
        'version': 'i581',
        'missions': [mission_row],
        'mission_uids': [dict(row) for row in uids],
        'mission_content': [],
        'objects': [dict(row) for row in uids],
    }
    acquired = {
        'responses': {},
        'mission_names': [mission],
        'mission_rows': [mission_row],
        'timings': [],
        'summary': {'version': 'i581', 'phase': 'discovery', 'discovery_ok': True, 'mission_count': 1},
    }
    return snapshot, acquired


def fake_call(cfg, sess, token, url, path, label, timeout):
    enrichment_calls.append(path)
    result = {'ok': True, 'status': 200, 'body': '<events/>', 'json': {}, 'error': ''}
    timing = {'endpoint': label, 'url_path': path, 'ok': True, 'status': 200, 'duration_seconds': 0.001, 'error': ''}
    return url, result, timing


def fake_build_from_acquired(cfg, sess, acquired, previous=None, phase='enrichment'):
    out = mod._i568_clone(previous or {})
    out['objects'] = [dict(row, enriched_i581=True) for row in out.get('objects', [])]
    out['version'] = 'i581'
    return out

mod._i568_build_snapshot = fake_build_snapshot
mod._i569_call = fake_call
mod._i570_build_from_acquired = fake_build_from_acquired
mod._i568_set_context = lambda token, sess: None
mod._i568_clear_context = lambda: None

cfg = {'marti_url': 'https://ots.example:8443', 'api_url': 'https://ots.example'}
sess = {'auth_mode': 'ots-user', 'username': 'tester', 'profile': {'username': 'tester'}}
key = mod._i568_state_key(cfg, sess)


def run_worker(generation: int, full: bool, reason: str):
    state = mod._i568_state(key)
    with mod._I568_STATE_LOCK:
        state['generation'] = generation
        state['in_flight'] = True
        state['i581_requested_full'] = full
        state['i581_requested_mode'] = 'membership-and-full-cot' if full else 'membership-only'
    mod._i568_refresh_worker(key, cfg, sess, 'TOKEN', reason, generation)
    return mod._i568_state(key)

# Initial run performs membership plus full CoT enrichment.
state = run_worker(1, True, 'initial-i581-test')
assert state['i581_last_membership_success_epoch'] > 0
assert state['i581_last_full_cot_epoch'] > 0
assert len(enrichment_calls) == 1
assert {row['uid'] for row in state['snapshot']['objects']} == {'UID-A', 'UID-B'}

# Authoritative membership deletion publishes immediately and must not be
# resurrected by the prior enriched last-known-good snapshot.
current_uids[:] = ['UID-A']
enrichment_calls.clear()
state = run_worker(2, False, 'membership-delete-i581-test')
assert enrichment_calls == []
assert {row['uid'] for row in state['snapshot']['objects']} == {'UID-A'}
assert state['snapshot']['data_sync_authoritative_prune_i581']['deleted_uids_never_preserved_by_lkg'] is True
assert len(state.get('i581_last_deleted') or []) == 1

# A new UID triggers immediate CoT enrichment for the affected Mission even
# though the 20-second full interval is not due.
current_uids[:] = ['UID-A', 'UID-C']
enrichment_calls.clear()
state = run_worker(3, False, 'membership-add-i581-test')
assert len(enrichment_calls) == 1 and enrichment_calls[0].endswith('/cot')
assert {row['uid'] for row in state['snapshot']['objects']} == {'UID-A', 'UID-C'}
assert all(row.get('enriched_i581') for row in state['snapshot']['objects'])
assert len(state.get('i581_last_added') or []) == 1

# Discovery failure preserves the current snapshot rather than interpreting a
# failed/empty response as an authoritative deletion.
prior_snapshot = mod._i568_clone(state['snapshot'])
mod._i568_build_snapshot = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError('simulated OTS failure'))
state = run_worker(4, False, 'failure-i581-test')
assert state['snapshot'] == prior_snapshot
assert 'simulated OTS failure' in state['last_error']

# Scheduler mode selection: a regular due membership check remains lightweight;
# force/manual always requests membership plus full CoT.
class FakeThread:
    created = []
    def __init__(self, target=None, args=(), name='', daemon=None):
        self.target, self.args, self.name, self.daemon = target, args, name, daemon
        FakeThread.created.append(self)
    def start(self):
        return None

original_thread = mod.threading.Thread
mod.threading.Thread = FakeThread
try:
    with mod._I568_STATE_LOCK:
        state = mod._i568_state(key)
        state['in_flight'] = False
        state['last_attempt_started_epoch'] = 0
        state['i581_last_full_cot_epoch'] = time.time()
        state['last_success_epoch'] = time.time() - 11
    scheduled, why = mod._i568_schedule_refresh(key, cfg, sess, 'TOKEN', 'regular-cadence', force=False)
    assert scheduled and why == 'scheduled-membership'
    assert mod._i568_state(key)['i581_requested_full'] is False

    with mod._I568_STATE_LOCK:
        state = mod._i568_state(key)
        state['in_flight'] = False
        state['last_attempt_started_epoch'] = 0
    scheduled, why = mod._i568_schedule_refresh(key, cfg, sess, 'TOKEN', 'manual-refresh', force=True)
    assert scheduled and why == 'scheduled-full'
    assert mod._i568_state(key)['i581_requested_full'] is True
finally:
    mod.threading.Thread = original_thread

print('i581 Data Sync cadence, deletion pruning, addition enrichment, failure LKG, and manual-force checks passed')
