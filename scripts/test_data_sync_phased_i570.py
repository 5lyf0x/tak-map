#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, json, os, pathlib, sys, tempfile, threading, time

ROOT = pathlib.Path(__file__).resolve().parents[1]

def event(uid: str, callsign: str, lat: float, lon: float) -> str:
    return (f'<event version="2.0" uid="{uid}" type="a-f-G-U-C" how="h-e" '
            f'time="2026-07-27T12:00:00Z" start="2026-07-27T12:00:00Z" stale="2026-07-27T12:10:00Z">'
            f'<point lat="{lat}" lon="{lon}" hae="0" ce="10" le="10"/>'
            f'<detail><contact callsign="{callsign}"/></detail></event>')

with tempfile.TemporaryDirectory(prefix='tak-map-i570-phased-') as td:
    os.environ['TAK_DASHBOARD_DATA_DIR'] = td
    spec = importlib.util.spec_from_file_location('tak_dashboard_i570_phased', ROOT / 'tak_dashboard.py')
    m = importlib.util.module_from_spec(spec); sys.modules[spec.name] = m; assert spec.loader; spec.loader.exec_module(m)
    cfg = {'api_url':'https://ots.test','base_url':'https://ots.test','marti_url':'https://ots.test:8443'}
    sess = {'auth_mode':'ots-user','username':'darktek','callsign':'raptor','tak_uid':'ANDROID-darktek',
            'profile':{'username':'darktek','tak_uid':'ANDROID-darktek'}}
    missions = [
        {'name':'FAST','passwordProtected':False,'uids':[{'data':'FAST-1','details':{'callsign':'FAST-DISCOVERY','type':'a-f-G-U-C','location':{'lat':34.1,'lon':-117.1}}}],'contents':[]},
        {'name':'FAIL','passwordProtected':False,'uids':[{'data':'FAIL-1','details':{'callsign':'FAIL-DISCOVERY','type':'a-f-G-U-C','location':{'lat':34.2,'lon':-117.2}}}],'contents':[]},
        {'name':'SLOW','passwordProtected':False,'uids':[{'data':'SLOW-1','details':{'callsign':'SLOW-DISCOVERY','type':'a-f-G-U-C','location':{'lat':34.3,'lon':-117.3}}}],'contents':[]},
    ]
    discovery = {'version':3,'type':'Mission','data':missions}
    calls=[]
    def fake(path, method='GET', body=None, headers=None, token='', public_host='', timeout=25):
        calls.append({'path':path,'at':time.monotonic(),'thread':threading.current_thread().name,'timeout':timeout,
                      'session_token':getattr(m._I529_REQUEST_CONTEXT,'session_token',''),
                      'auth_mode':getattr(m._I529_REQUEST_CONTEXT,'auth_mode','')})
        if path == '/Marti/api/missions?passwordProtected=true':
            return {'ok':True,'status':200,'body':json.dumps(discovery),'json':discovery,'error':'','identity_mode':'per-user-enrolled-marti-certificate'}
        if path.endswith('/FAST/cot'):
            time.sleep(.05)
            body='<events>'+event('FAST-1','FAST-ENRICHED',34.1,-117.1)+'</events>'
            return {'ok':True,'status':200,'body':body,'json':{},'error':'','identity_mode':'per-user-enrolled-marti-certificate'}
        if path.endswith('/FAIL/cot'):
            time.sleep(.12)
            return {'ok':False,'status':503,'body':'','json':{},'error':'temporary failure','identity_mode':'per-user-enrolled-marti-certificate'}
        if path.endswith('/SLOW/cot'):
            time.sleep(.55)
            body='<events>'+event('SLOW-1','SLOW-ENRICHED',34.3,-117.3)+'</events>'
            return {'ok':True,'status':200,'body':body,'json':{},'error':'','identity_mode':'per-user-enrolled-marti-certificate'}
        raise AssertionError('Unexpected Mission request: '+path)
    m._i569_mission_request = fake

    # Direct build proves the one-mission/multi-mission first boundary is discovery-only.
    m._i568_set_context('SESSION', sess)
    try:
        started=time.monotonic(); first, acquired=m._i568_build_snapshot(cfg,sess,'SESSION','direct'); elapsed=time.monotonic()-started
    finally:
        m._i568_clear_context()
    assert elapsed < .35, elapsed
    assert [c['path'] for c in calls] == ['/Marti/api/missions?passwordProtected=true'], calls
    assert acquired['summary']['phase']=='discovery'
    assert acquired['summary']['mission_count']==3
    assert acquired['summary']['cot_enrichment_pending_count']==3
    assert len(first.get('objects') or [])==3

    # Background worker must publish all discovery objects before optional CoT completes.
    calls.clear()
    key=m._i568_state_key(cfg,sess)
    state=m._i568_state(key)
    started=time.monotonic()
    scheduled,why=m._i568_schedule_refresh(key,cfg,sess,'SESSION','phased-test',force=True)
    assert scheduled and why=='scheduled',(scheduled,why)
    early=None
    deadline=time.monotonic()+.40
    while time.monotonic()<deadline:
        with m._I568_STATE_LOCK:
            snap=m._i568_clone(state.get('snapshot')) if isinstance(state.get('snapshot'),dict) else None
            summary=m._i568_clone(state.get('acquisition_summary') or {})
            inflight=bool(state.get('in_flight'))
        if snap and len(snap.get('objects') or [])==3:
            early=(snap,summary,inflight,time.monotonic()-started)
            break
        time.sleep(.01)
    assert early, 'discovery snapshot was not published promptly'
    assert early[3] < .40, early[3]
    assert early[2] is True, early
    assert early[1].get('phase') in ('discovery-published','mission-enrichment-published'), early[1]

    incremental=None
    deadline=time.monotonic()+.45
    while time.monotonic()<deadline:
        with m._I568_STATE_LOCK:
            summary=m._i568_clone(state.get('acquisition_summary') or {})
            inflight=bool(state.get('in_flight'))
        if summary.get('cot_enrichment_success_count',0)>=1 and inflight:
            incremental=(summary,time.monotonic()-started)
            break
        time.sleep(.01)
    assert incremental, 'fast mission enrichment was not published while slow mission remained pending'
    assert incremental[1] < .50, incremental
    assert incremental[0].get('last_published_mission')=='FAST', incremental[0]

    deadline=time.monotonic()+2.0
    final=None
    while time.monotonic()<deadline:
        with m._I568_STATE_LOCK:
            final_snap=m._i568_clone(state.get('snapshot')) if isinstance(state.get('snapshot'),dict) else None
            final_summary=m._i568_clone(state.get('acquisition_summary') or {})
            inflight=bool(state.get('in_flight'))
        if final_snap and not inflight and final_summary.get('phase')=='ready':
            final=(final_snap,final_summary)
            break
        time.sleep(.02)
    assert final, 'phased refresh did not reach ready state'
    assert final[1]['cot_enrichment_success_count']==2, final[1]
    assert final[1]['cot_enrichment_failure_count']==1, final[1]
    assert final[1]['cot_enrichment_pending_count']==0, final[1]
    assert set(final[1]['mission_status'])=={'FAST','FAIL','SLOW'}, final[1]
    assert len(final[0].get('objects') or [])==3, final[0]
    by_uid={m._i555_object_uid(row):row for row in final[0].get('objects') or []}
    assert set(by_uid)=={'FAST-1','FAIL-1','SLOW-1'}, by_uid
    assert all(c['session_token']=='SESSION' and c['auth_mode']=='ots-user' for c in calls), calls
    assert all(c['timeout']<=4 for c in calls if c['path'].endswith('/cot')), calls

print('i570 discovery-first, single/multi-mission incremental Data Sync worker passed')
