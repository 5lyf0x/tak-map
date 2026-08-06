#!/usr/bin/env python3
from __future__ import annotations
import importlib.util,pathlib,sys,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('tak_dashboard_i583_scheduler',ROOT/'tak_dashboard.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
assert m._I583_MEMBERSHIP_INTERVAL_SECONDS==10
assert m._I583_FULL_COT_INTERVAL_SECONDS==20
assert m._I583_BROWSER_POLL_SECONDS==5
cfg={'marti_url':'https://ots.example:8443','api_url':'https://ots.example'}
sess={'auth_mode':'ots-user','username':'tester','profile':{'username':'tester'}}
key=m._i568_state_key(cfg,sess);m._I568_STATES.clear()
class FakeThread:
    made=[]
    def __init__(self,target=None,args=(),name='',daemon=None):self.target,self.args,self.name,self.daemon=target,args,name,daemon;self.made.append(self)
    def start(self):pass
orig=m.threading.Thread;m.threading.Thread=FakeThread
try:
    state=m._i568_state(key)
    with m._I568_STATE_LOCK:
        state['last_success_epoch']=time.time()-11;state['i581_last_membership_success_epoch']=time.time()-11;state['i581_last_full_cot_epoch']=time.time()-25;state['in_flight']=False
    scheduled,why=m._i568_schedule_refresh(key,cfg,sess,'TOKEN','automatic',force=False)
    assert scheduled and why=='scheduled-full-i583'
    state=m._i568_state(key);assert state['i583_active_mode']=='full'
    # Many automatic browser polls during an active full pass do not recursively
    # queue another full pass.
    for _ in range(20):
        ok,why=m._i568_schedule_refresh(key,cfg,sess,'TOKEN','i583-automatic-poll',force=False)
        assert not ok and why=='already-running-coalesced-i583'
    assert state['i583_pending_full'] is False
    # A post-save request queues exactly one membership pass, and repeated save
    # followups remain coalesced to one boolean flag.
    for _ in range(5):m._i568_schedule_refresh(key,cfg,sess,'TOKEN','i583-post-save-membership-fastpath',force=False)
    assert state['i583_pending_membership'] is True
    # Manual refresh while busy queues exactly one full pass.
    for _ in range(5):m._i568_schedule_refresh(key,cfg,sess,'TOKEN','manual',force=True)
    assert state['i583_pending_full'] is True
finally:m.threading.Thread=orig
# Worker completion drains at most one queued operation. Full takes precedence
# over membership and both flags are cleared before scheduling.
state=m._i568_state(key)
with m._I568_STATE_LOCK:
    state['generation']=99;state['i583_worker_running']=True;state['in_flight']=True
    state['i583_active_mode']='full';state['i583_pending_full']=True;state['i583_pending_membership']=True
m._i583_worker_before=lambda *args,**kwargs:None
drained=[]
m._i568_schedule_refresh=lambda *args,**kwargs:drained.append((args,kwargs)) or (True,'recorded')
m._i568_refresh_worker(key,cfg,sess,'TOKEN','test-finish',99)
assert len(drained)==1 and drained[0][1].get('force') is True,drained
assert not state.get('i583_pending_full') and not state.get('i583_pending_membership')
assert state['i583_worker_running'] is False and state['in_flight'] is False
client=(ROOT/'assets/tak-map-data-sync-i553.js').read_text()
assert "const V='i583'" in client and 'automaticPollMs:5000' in client
assert 'function installAutomaticPoll()' in client and "setInterval(async()=>" in client
assert "'i583-automatic-poll'" in client and 'pollTimerInstalled:!!S.pollTimer' in client
print('i583 single-flight scheduler and actual five-second browser polling timer tests passed')
