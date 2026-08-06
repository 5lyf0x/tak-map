#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, json, os, pathlib, sys, tempfile, threading, time
ROOT=pathlib.Path(__file__).resolve().parents[1]
CUSTOM='db450cbe-2fec-47fb-bd2b-ba2db89b035e/Incident Management/water point.png'
with tempfile.TemporaryDirectory(prefix='tak-map-i569-worker-pipeline-') as td:
    os.environ['TAK_DASHBOARD_DATA_DIR']=td
    spec=importlib.util.spec_from_file_location('tak_dashboard_i569_worker_pipeline',ROOT/'tak_dashboard.py')
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;assert spec.loader;spec.loader.exec_module(m)
    cfg={'api_url':'https://ots.test','base_url':'https://ots.test','marti_url':'https://ots.test:8443'}
    sess={'auth_mode':'ots-user','username':'darktek','callsign':'raptor','tak_uid':'ANDROID-darktek','profile':{'username':'darktek','tak_uid':'ANDROID-darktek'}}
    calls=[]
    cot=(f'<event version="2.0" uid="CUSTOM-1" type="a-n-G" how="h-e" time="2026-07-27T12:00:00Z" start="2026-07-27T12:00:00Z" stale="2026-07-27T12:10:00Z"><point lat="34.1001" lon="-117.2002" hae="0" ce="10" le="10"/><detail><contact callsign="WATER"/><usericon iconsetpath="{CUSTOM}"/></detail></event>')
    def fake(path,method='GET',body=None,headers=None,token='',public_host='',timeout=25):
        ctx={'path':path,'thread':threading.current_thread().name,'token':getattr(m._I529_REQUEST_CONTEXT,'session_token',''),'auth':getattr(m._I529_REQUEST_CONTEXT,'auth_mode',''),'identity':dict(getattr(m._I512_REQUEST_CONTEXT,'identity',{}) or {}),'timeout':timeout}
        calls.append(ctx)
        assert ctx['token']=='SESSION'
        assert ctx['auth']=='ots-user'
        assert ctx['identity'].get('username')=='darktek'
        time.sleep(.03)
        if path=='/Marti/api/missions?passwordProtected=true':
            payload={'version':3,'type':'Mission','data':[{'name':'M','passwordProtected':False,'uids':[{'data':'CUSTOM-1','details':{'callsign':'WATER','type':'a-n-G','iconsetPath':CUSTOM,'location':{'lat':34.1001,'lon':-117.2002}}},{'data':'SOF-1','details':{'callsign':'SOF','type':'a-f-F-N-S','location':{'lat':34.2,'lon':-117.3}}}],'contents':[]}]}
            return {'ok':True,'status':200,'body':json.dumps(payload),'json':payload,'error':'','identity_mode':'per-user-enrolled-marti-certificate','user_agent_family':'ATAK','mission_token_used':False}
        if path.endswith('/cot'):
            return {'ok':True,'status':200,'body':'<events>'+cot+'</events>','json':{},'error':'','identity_mode':'per-user-enrolled-marti-certificate','user_agent_family':'ATAK','mission_token_used':True}
        raise AssertionError('Unexpected Mission request: '+path)
    m._i569_mission_request=fake
    m._i568_set_context('SESSION',sess)
    try:
        start=time.monotonic(); result,acq=m._i568_build_snapshot(cfg,sess,'SESSION','test'); elapsed=time.monotonic()-start
    finally: m._i568_clear_context()
    assert elapsed<1.0,elapsed
    assert acq['summary']['discovery_ok'] and acq['mission_names']==['M']
    assert acq['summary']['authoritative_discovery']=='/Marti/api/missions?passwordProtected=true'
    assert acq['summary']['mission_count']==1 and acq['summary']['mission_endpoint_count']==1
    assert acq['summary']['network_get_contents_calls']==0
    assert len(calls)==2,calls
    assert all(c['thread'].startswith('ThreadPoolExecutor') for c in calls)
    assert all(c['timeout']<=5 for c in calls)
    assert not any(c['path']=='/api/missions' for c in calls)
    by={str(r.get('uid') or r.get('event_uid') or ''):r for r in result.get('objects') or []}
    assert {'CUSTOM-1','SOF-1'}<=set(by),by.keys()
    assert by['CUSTOM-1'].get('data_sync_current_iconset_path_i567')==CUSTOM,by['CUSTOM-1']
    assert by['SOF-1'].get('mil2525_file')=='friendly-ground-unit-special-forces.svg',by['SOF-1']
    assert result['version']=='i569'
    diag=result['data_sync_background_worker_i569']
    assert diag['per_user_certificate'] and diag['thread_context_installed_per_request'] and diag['parsed_json_response_adapter']
print('i569 real-shape per-user ATAK worker pipeline passed')
