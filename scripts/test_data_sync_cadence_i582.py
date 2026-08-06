#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, pathlib, sys, time
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('tak_dashboard_i582_cadence',ROOT/'tak_dashboard.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
assert m._I582_MEMBERSHIP_INTERVAL_SECONDS==10
assert m._I582_FULL_COT_INTERVAL_SECONDS==20
assert m._I582_BROWSER_POLL_SECONDS==5
assert m._I568_SNAPSHOT_MAX_AGE_SECONDS==10
cfg={'marti_url':'https://ots.example:8443','api_url':'https://ots.example'}
sess={'auth_mode':'ots-user','username':'tester','profile':{'username':'tester'}}
key=m._i568_state_key(cfg,sess)
m._I568_STATES.clear()
class FakeThread:
    created=[]
    def __init__(self,target=None,args=(),name='',daemon=None): self.target,self.args,self.name,self.daemon=target,args,name,daemon; self.created.append(self)
    def start(self): return None
orig=m.threading.Thread;m.threading.Thread=FakeThread
try:
    state=m._i568_state(key)
    with m._I568_STATE_LOCK:
        state['in_flight']=False;state['last_attempt_started_epoch']=0
        state['i581_last_full_cot_epoch']=time.time();state['last_success_epoch']=time.time()-11
    scheduled,why=m._i568_schedule_refresh(key,cfg,sess,'TOKEN','regular',force=False)
    assert scheduled and why=='scheduled-membership'
    assert m._i568_state(key)['i581_requested_full'] is False
    with m._I568_STATE_LOCK:
        state=m._i568_state(key);state['in_flight']=False;state['last_attempt_started_epoch']=0
    scheduled,why=m._i568_schedule_refresh(key,cfg,sess,'TOKEN','manual',force=True)
    assert scheduled and why=='scheduled-full'
    assert m._i568_state(key)['i581_requested_full'] is True
finally:
    m.threading.Thread=orig
print('i582 10-second membership, 20-second full CoT, and forced-manual scheduler checks passed')
