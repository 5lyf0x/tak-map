#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, json, os, pathlib, sys, tempfile, threading, time
ROOT=pathlib.Path(__file__).resolve().parents[1]
CUSTOM_PATH='db450cbe-2fec-47fb-bd2b-ba2db89b035e/Incident Management/water point.png'
with tempfile.TemporaryDirectory(prefix='tak-map-i569-auth-worker-') as td:
    os.environ['TAK_DASHBOARD_DATA_DIR']=td
    spec=importlib.util.spec_from_file_location('tak_dashboard_i569_auth_worker',ROOT/'tak_dashboard.py')
    mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;assert spec.loader;spec.loader.exec_module(mod)
    cfg={'api_url':'https://ots.test','base_url':'https://ots.test','marti_url':'https://ots.test:8443'}
    sess={'auth_mode':'ots-user','username':'darktek','callsign':'raptor','tak_uid':'ANDROID-darktek',
          'profile':{'username':'darktek','tak_uid':'ANDROID-darktek'}}
    calls=[]
    cot_xml=(f'<event version="2.0" uid="CUSTOM-1" type="a-n-G" how="h-e" '
             f'time="2026-07-27T12:00:00Z" start="2026-07-27T12:00:00Z" stale="2026-07-27T12:10:00Z">'
             f'<point lat="34.1001" lon="-117.2002" hae="0" ce="10" le="10"/>'
             f'<detail><contact callsign="WATER"/><usericon iconsetpath="{CUSTOM_PATH}"/></detail></event>')
    def fake_client(path,method='GET',body=None,headers=None,token='',public_host='',timeout=25):
        ctx={
            'path':path,'thread':threading.current_thread().name,
            'session_token':getattr(mod._I529_REQUEST_CONTEXT,'session_token',''),
            'auth_mode':getattr(mod._I529_REQUEST_CONTEXT,'auth_mode',''),
            'identity':dict(getattr(mod._I512_REQUEST_CONTEXT,'identity',{}) or {}),
            'timeout':timeout,
        }
        calls.append(ctx)
        assert ctx['session_token']=='USER-SESSION-TOKEN',ctx
        assert ctx['auth_mode']=='ots-user',ctx
        assert ctx['identity'].get('username')=='darktek',ctx
        time.sleep(.02)
        if path=='/Marti/api/missions?passwordProtected=true':
            payload={'version':3,'type':'Mission','data':[{'name':'TAKMAP-DATASYNC-TEST','passwordProtected':False,'uids':[
                {'data':'CUSTOM-1','details':{'callsign':'WATER','type':'a-n-G','iconsetPath':CUSTOM_PATH,
                                             'location':{'lat':34.1001,'lon':-117.2002}}},
                {'data':'SOF-1','details':{'callsign':'SOF','type':'a-f-F-N-S',
                                           'location':{'lat':34.2,'lon':-117.3}}}],
                'contents':[]}]}
        elif path.endswith('/cot'):
            return {'ok':True,'status':200,'body':'<events>'+cot_xml+'</events>','json':{},'error':'',
                    'identity_mode':'per-user-enrolled-marti-certificate','user_agent_family':'ATAK',
                    'mission_token_used':True}
        else:
            raise AssertionError('Unexpected Mission request: '+path)
        # Match the real per-user client: raw JSON text in body, parsed value in json.
        return {'ok':True,'status':200,'body':json.dumps(payload),'json':payload,'error':'',
                'identity_mode':'per-user-enrolled-marti-certificate','user_agent_family':'ATAK',
                'mission_token_used':path.endswith('/cot')}
    mod._i569_mission_request=fake_client
    mod._i568_set_context('USER-SESSION-TOKEN',sess)
    try:
        result,acquired=mod._i568_build_snapshot(cfg,sess,'USER-SESSION-TOKEN','test')
    finally:
        mod._i568_clear_context()
    assert acquired['summary']['discovery_ok'] is True,acquired
    assert acquired['mission_names']==['TAKMAP-DATASYNC-TEST'],acquired
    assert acquired['summary']['mission_count']==1,acquired
    assert calls[0]['path']=='/Marti/api/missions?passwordProtected=true',calls
    assert not any(c['path'].endswith('/contents') for c in calls),calls
    assert all(c['thread'].startswith('ThreadPoolExecutor') for c in calls),calls
    assert all(c['session_token']=='USER-SESSION-TOKEN' for c in calls),calls
    by_uid={str(r.get('uid') or r.get('event_uid') or ''):r for r in result.get('objects') or []}
    assert {'CUSTOM-1','SOF-1'} <= set(by_uid),by_uid.keys()
    assert by_uid['CUSTOM-1'].get('data_sync_current_iconset_path_i567')==CUSTOM_PATH,by_uid['CUSTOM-1']
    assert by_uid['SOF-1'].get('mil2525_file')=='friendly-ground-unit-special-forces.svg',by_uid['SOF-1']
    assert result['data_sync_background_worker_i569']['thread_context_installed_per_request'] is True
    assert result['data_sync_background_worker_i569']['parsed_json_response_adapter'] is True
print('i569 background worker uses per-user ATAK Mission client inside executor threads and parses real client response shape')
