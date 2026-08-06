#!/usr/bin/env python3
from __future__ import annotations
import os, runpy, sys, threading, time, traceback

def hard_exit(code:int)->None:
    sys.stdout.flush();sys.stderr.flush();os._exit(code)

def hook(tp,val,tb):
    traceback.print_exception(tp,val,tb);hard_exit(1)
sys.excepthook=hook
os.environ['TAK_MAP_TEST_SKIP_ADSB_WARMUP']='1'
ns=runpy.run_path('tak_dashboard.py',run_name='tak_map_i491_server_singleflight')
fn=ns['tak_map_data_sync'];g=fn.__globals__;calls={'n':0};gate=threading.Barrier(8)
def base():
    calls['n']+=1;time.sleep(.18);return {'ok':True,'objects':[{'uid':'one'}],'missions':[]}
g['_i491_base_data_sync']=base
state=g['_I476_DS_SERVER_STATE']
with g['_I476_DS_LOCK']:
    state.update({'in_flight':False,'last_good':None,'last_good_at':0.0,'requests':0,'network_runs':0,'coalesced':0,'cache_hits':0,'last_error':''})
out=[]
def worker():
    gate.wait();out.append(fn())
threads=[threading.Thread(target=worker,daemon=True) for _ in range(8)]
for t in threads:t.start()
for t in threads:t.join(3)
assert all(not t.is_alive() for t in threads)
assert calls['n']==1,calls
assert state['network_runs']==1 and state['coalesced']>=7,state
cached=fn();assert calls['n']==1 and cached['_tak_map_data_sync_singleflight_i491']['served']=='short-cache'
print('Data Sync server single-flight test passed',flush=True)
hard_exit(0)
