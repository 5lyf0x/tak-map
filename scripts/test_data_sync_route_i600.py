#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
import pathlib
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
os.environ['TAK_MAP_DATA_DIR'] = tempfile.mkdtemp(prefix='tak-map-i600-route-')
os.environ['TAK_MAP_MIL_ROOT'] = str(ROOT / 'assets/mil2525')
os.environ['TAK_MAP_TEST_SKIP_ADSB_WARMUP'] = '1'

spec = importlib.util.spec_from_file_location('tak_dashboard_i600_route', ROOT / 'tak_dashboard.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader
spec.loader.exec_module(mod)
assert mod.TAK_MAP_ITERATION == 'i600'

cfg = {'enabled':True,'login_enabled':True,'api_url':'https://ots','base_url':'https://ots','marti_url':'https://ots:8443'}
sess = {'auth_mode':'ots-user','username':'alice','callsign':'ALICE','tak_uid':'alice-uid','profile':{'username':'alice','tak_uid':'alice-uid'}}
mod._i509_load_ots_config = lambda: dict(cfg)

class FakeHandler(mod.Handler):
    def __init__(self, path: str):
        self.path = path
        self.sent = None
    def _tak_map_auth_ok(self): return True
    def _tak_map_session(self): return dict(sess)
    def _tak_map_token(self): return 'user-token'
    def _require_tak_map_login(self): raise AssertionError('unexpected login requirement')
    def _send_json(self, payload, status=200, headers=None):
        self.sent = (payload, status, headers)
        return payload

key = mod._i568_state_key(cfg, sess)
ready_access = [
    mod._i599_descriptor('OPEN-MISSION', False, True, 'ready', sess=sess),
    mod._i599_descriptor('LOCKED-MISSION', True, False, 'locked', sess=sess),
]
snapshot = {
    'ok':True,'version':'i599',
    'missions':[{'name':'OPEN-MISSION'}, mod._i599_descriptor('LOCKED-MISSION', True, False, 'locked', sess=sess)],
    'objects':[{'mission':'OPEN-MISSION','mission_name':'OPEN-MISSION','uid':'OPEN-1','callsign':'OPEN-1','lat':34.0,'lon':-117.0}],
    'mission_uids':[{'mission':'OPEN-MISSION','mission_name':'OPEN-MISSION','uid':'OPEN-1'}],
    'mission_content':[],'packages':[],'mission_logs':[],'mission_roles':[],'sources':[],
}
with mod._I568_STATE_LOCK:
    state = mod._i568_state(key)
    state.clear()
    state.update({
        'snapshot':mod._i568_clone(snapshot), 'generation':8,
        'completed_generation_i599':8, 'snapshot_generation_i599':8,
        'i599_worker_running':False, 'in_flight':False,
        'last_success_epoch':time.time(), 'last_attempt_started_epoch':time.time()-0.1,
        'last_attempt_completed_epoch':time.time(), 'last_error':'',
    })
    mod._i599_set_access(state, ready_access)

# Browser GET is a pure snapshot read. It must not validate a password, acquire a
# Mission, or mutate worker generation/lifecycle.
mod._i572_subscribe_with_password = lambda *a, **k: (_ for _ in ()).throw(AssertionError('GET revalidated Mission password'))
mod._i568_parallel_acquisition = lambda *a, **k: (_ for _ in ()).throw(AssertionError('GET acquired Mission data'))
scheduled = []
mod._i568_schedule_refresh = lambda *a, **k: (scheduled.append((a,k)) or True, 'scheduled-test')
with mod._I568_STATE_LOCK:
    before = (state['generation'], state['in_flight'], state['i599_worker_running'])
started = time.monotonic()
payload = FakeHandler('/api/tak-map/data-sync?reason=poll').do_GET()
elapsed = time.monotonic() - started
with mod._I568_STATE_LOCK:
    after = (state['generation'], state['in_flight'], state['i599_worker_running'])
assert elapsed < 0.10, elapsed
assert before == after and not scheduled, (before, after, scheduled)
assert payload['partially_locked_i599'] is True and payload['locked'] is False
assert [row['uid'] for row in payload['objects']] == ['OPEN-1']
assert any(row.get('mission') == 'LOCKED-MISSION' and row.get('locked') for row in payload['mission_access_i599'])
assert payload['data_sync_background_i599']['security_filter_read_only'] is True

# A force request only schedules one background generation and immediately
# returns the completed snapshot. No acquisition occurs in the request thread.
forced = FakeHandler('/api/tak-map/data-sync?force=1&reason=manual').do_GET()
assert len(scheduled) == 1, scheduled
assert [row['uid'] for row in forced['objects']] == ['OPEN-1']

# During a newer in-flight generation, the HTTP response keeps the completed
# snapshot and publishes explicit loading/generation state. Security projection
# remains read-only and preserves the unlocked Mission's object.
loading_access = [
    mod._i599_descriptor('OPEN-MISSION', False, True, 'loading', sess=sess),
    mod._i599_descriptor('LOCKED-MISSION', True, False, 'locked', sess=sess),
]
with mod._I568_STATE_LOCK:
    state['generation'] = 9
    state['completed_generation_i599'] = 8
    state['snapshot_generation_i599'] = 8
    state['i599_worker_running'] = True
    state['in_flight'] = True
    state['last_success_epoch'] = time.time()
    mod._i599_set_access(state, loading_access)
    before_loading = (state['generation'], state['in_flight'], state['i599_worker_running'])
transition = FakeHandler('/api/tak-map/data-sync?reason=poll').do_GET()
with mod._I568_STATE_LOCK:
    after_loading = (state['generation'], state['in_flight'], state['i599_worker_running'])
assert before_loading == after_loading
bg = transition['data_sync_background_i599']
assert bg['transitional_response'] is True and bg['generation'] == 9 and bg['completed_generation'] == 8
assert [row['uid'] for row in transition['objects']] == ['OPEN-1']
assert next(row for row in transition['mission_access_i599'] if row['mission']=='OPEN-MISSION')['content_state_i599'] == 'loading'

print('i600 browser-facing Data Sync route is nonblocking, read-only, generation-aware, and preserves completed mixed-Mission data')
