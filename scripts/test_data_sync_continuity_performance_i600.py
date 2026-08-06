#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, os, pathlib, sys, tempfile, time

ROOT=pathlib.Path(__file__).resolve().parents[1]
os.environ['TAK_MAP_DATA_DIR']=tempfile.mkdtemp(prefix='tak-map-i600-')
os.environ['TAK_MAP_MIL_ROOT']=str(ROOT/'assets/mil2525')
os.environ['TAK_MAP_TEST_SKIP_ADSB_WARMUP']='1'
spec=importlib.util.spec_from_file_location('tak_dashboard_i600',ROOT/'tak_dashboard.py')
mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;assert spec.loader;spec.loader.exec_module(mod)
assert mod.TAK_MAP_ITERATION=='i600'
assert mod.tak_map_config()['version']=='1.3.0-i600'

cfg={'api_url':'https://ots','base_url':'https://ots','marti_url':'https://ots:8443'}
sess={'auth_mode':'ots-user','username':'alice','tak_uid':'alice-uid','callsign':'ALICE'}
mission='TEST-MISSION'
network={'cot':0,'subscribe':0,'legacy':0}
state={'uids':['P1'],'xml':'','contents':[],'status':200}

def event(uid,idx=1):
    return (f'<event version="2.0" uid="{uid}" type="a-f-G-U-C" how="h-e" '
            'time="2026-07-30T20:00:00Z" start="2026-07-30T20:00:00Z" stale="2026-07-30T20:10:00Z">'
            f'<point lat="{34+idx/1000:.6f}" lon="{-117-idx/1000:.6f}" hae="100" ce="10" le="10"/>'
            f'<detail><contact callsign="POINT {idx}"/></detail></event>')
state['xml']='<events>'+event('P1',1)+'</events>'

def discovery(include):
    rows=[{'name':mission,'passwordProtected':True,'uids':list(state['uids']),'contents':list(state['contents'])}]
    return {'ok':True,'status':200,'json':{'version':3,'type':'Mission','data':rows},'body':{},'error':''}

def run_parallel(jobs,cfg_arg,sess_arg,token,deadline,workers):
    responses={};timings=[]
    for url,path,endpoint,timeout in jobs:
        responses[url]=discovery(True)
        timings.append({'endpoint':endpoint,'ok':True,'status':200,'duration_seconds':0.001,'error':''})
    return responses,timings
mod._i569_run_parallel=run_parallel
mod._i572_creator_uid=lambda:'creator'
mod._i572_load_password=lambda name,session=None:{'ok':True,'password':'secret'}
mod._i591_load_index=lambda session=None:{}
mod._i591_remember_mission=lambda *a,**k:None
mod._i591_mark_validated=lambda *a,**k:None
mod._i591_invalidate_validation=lambda *a,**k:None
mod._i564_invalidate_mission_token=lambda *a,**k:None

def subscribe(*a,**k):
    network['subscribe']+=1
    return {'ok':True,'status':200,'token':'mission-token','source':'test','reused':network['subscribe']>1}
mod._i572_subscribe_with_password=subscribe

def cot(path,method='GET',body=None,headers=None,token='',timeout=0,**kwargs):
    network['cot']+=1
    assert token=='mission-token'
    if state['status']!=200:
        return {'ok':False,'status':state['status'],'json':{},'body':None,'error':'failure'}
    return {'ok':True,'status':200,'json':{},'body':state['xml'],'error':''}
mod._i564_mission_request_raw=cot

# The fast path must never invoke the legacy PostgreSQL scan.
def legacy_forbidden():
    network['legacy']+=1
    time.sleep(2)
    raise AssertionError('legacy tak_map_data_sync was invoked on the critical path')
mod.tak_map_data_sync=legacy_forbidden
mod._i600_schedule_supplement=lambda *a,**k:False

# Initial authoritative /cot cycle.
raw,acq=mod._i600_build_raw_snapshot(cfg,sess,'user-token','initial',{'force_cot':True},None,None)
first,access,lkg=mod._i600_reconcile(raw,acq,None,cfg,sess,{})
first,flat=mod._i600_flatten_snapshot_properties(first)
lkg=mod._i600_update_lkg(lkg,first,acq)
assert network['legacy']==0
assert [mod._i599_uid(r) for r in first['objects']]==['P1'],first['objects']
assert lkg[mission.lower()]['authoritative'] is True

# Exact live regression: /cot is skipped, previous snapshot is unavailable, but
# the per-Mission completed CoT cache must still carry P1 into the new generation.
now=time.time()
member_raw,member_acq=mod._i600_build_raw_snapshot(cfg,sess,'user-token','membership',{
    'force_cot':False,'last_cot_epoch_by_mission':{mission.lower():now},
    'previous_uid_by_mission':{mission.lower():['P1']},
},None,None)
assert member_acq['summary']['cot_request_count']==0
member,member_access,_=mod._i600_reconcile(member_raw,member_acq,None,cfg,sess,lkg)
assert [mod._i599_uid(r) for r in member['objects']]==['P1'],member['objects']
per=member['data_sync_reconciliation_i599']['per_mission'][mission]
assert per['membership_refresh_only_i599'] is True and per['authoritative'] is True
assert next(r for r in member_access if r['mission']==mission)['content_state_i599']=='ready'
assert not mod._i600_validate_snapshot(member,member_acq,lkg)

# A real successful empty /cot is the only condition that clears the Mission.
state['xml']='<events></events>'; state['uids']=[]
empty_raw,empty_acq=mod._i600_build_raw_snapshot(cfg,sess,'user-token','empty',{'force_cot':True},member,None)
empty,_,_=mod._i600_reconcile(empty_raw,empty_acq,member,cfg,sess,lkg)
assert not mod._i599_rows_for_mission(empty,'objects',mission)
assert empty['data_sync_reconciliation_i599']['per_mission'][mission]['successful_empty_cot_authoritative_i599'] is True

# Recursive properties wrappers are flattened once without changing coordinates.
wrapped={'objects':[{'uid':'X','mission':mission,'lat':1,'lon':2,'properties':{'a':1,'properties':{'b':2,'properties':{'c':3}}}}], 'mission_uids':[]}
cleaned,count=mod._i600_flatten_snapshot_properties(wrapped)
assert count==1 and cleaned['objects'][0]['properties']=={'c':3,'b':2,'a':1}
assert cleaned['objects'][0]['lat']==1 and cleaned['objects'][0]['lon']==2

# 200-object fixture through the real compatibility finalizer must stay bounded
# and preserve every UID/coordinate. This is intentionally a generous ceiling
# for shared CI runners; the legacy scan would exceed it by a large margin.
state['uids']=[f'P{i}' for i in range(200)]
state['xml']='<events>'+''.join(event(f'P{i}',i) for i in range(200))+'</events>'
started=time.monotonic()
big_raw,big_acq=mod._i600_build_raw_snapshot(cfg,sess,'user-token','big',{'force_cot':True},None,None)
big,_,big_lkg=mod._i600_reconcile(big_raw,big_acq,None,cfg,sess,{})
big,flat=mod._i600_flatten_snapshot_properties(big)
elapsed=time.monotonic()-started
assert len(big['objects'])==200,len(big['objects'])
assert len({mod._i599_uid(r) for r in big['objects']})==200
assert elapsed<8.0,elapsed
assert network['legacy']==0
perf=big_raw['data_sync_performance_i600']
assert perf['legacy_postgresql_scan_on_critical_path'] is False

# Optional PostgreSQL metadata is bounded to two consolidated queries, runs
# outside the critical path, and never injects unscoped historical rows.
pg_calls=[]
mod._candidate_ots_pg_uris=lambda:(['postgresql://test'],[])
def pg_query(uri,sql,timeout=0):
    pg_calls.append((sql,timeout))
    if len(pg_calls)==1:
        return ['mission_content','mission_roles'],''
    return [__import__('json').dumps({
        'mission_content':[
            {'uid':'SCOPED','mission_name':mission,'name':'Current package'},
            {'uid':'UNSCOPED','mission_name':None,'name':'Historical package'},
        ],
        'mission_roles':[{'id':1,'mission_name':mission,'username':'alice'}],
    })],''
mod._pg_query=pg_query
supp=mod._i600_pg_supplement_fast(cfg,[mission])
assert supp['ok'] is True and len(pg_calls)==2,pg_calls
assert [row['uid'] for row in supp['rows']['mission_content']]==['SCOPED']
assert len(supp['rows']['mission_roles'])==1
assert all(timeout==mod._I600_SUPPLEMENT_QUERY_TIMEOUT_SECONDS for _,timeout in pg_calls)

# Final worker publication alternates full and membership-only generations while
# retaining the completed 200-object snapshot.
key=mod._i568_state_key(cfg,sess)
with mod._I568_STATE_LOCK:
    s=mod._i568_state(key);s.clear();s.update({
        'key':key,'snapshot':big,'generation':10,'i599_worker_running':True,'in_flight':True,
        'i599_last_cot_epoch_by_mission':{mission.lower():time.time()},
        'i600_mission_lkg':mod._i600_update_lkg({},big,big_acq),
    })
assert mod._i568_refresh_worker(key,cfg,sess,'user-token','membership-worker',10,False) is True
with mod._I568_STATE_LOCK:
    s=mod._i568_state(key)
    assert len(s['snapshot']['objects'])==200
    assert s['last_attempt_duration_seconds']<8.0,s['last_attempt_duration_seconds']
    assert s['snapshot']['data_sync_performance_i600']['invariant_validation_passed'] is True
    assert s['completed_generation_i600']==10

print('i600 Data Sync continuity/performance regression passed')
