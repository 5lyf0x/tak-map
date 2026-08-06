#!/usr/bin/env python3
from pathlib import Path
import importlib.util, sys, tempfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('tak_i572_focused',ROOT/'tak_dashboard.py')
m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m; spec.loader.exec_module(m)

# Stable synthetic authenticated user context.
m._I512_REQUEST_CONTEXT.identity={'username':'i572-test','identity_key':'i572-test','tak_uid':'TAKMAP-TEST-UID','callsign':'TEST'}
m._I529_REQUEST_CONTEXT.auth_mode='ots'
m._I529_REQUEST_CONTEXT.session_token='test-session'
m._i572_creator_uid=lambda:'TAKMAP-TEST-UID'

with tempfile.TemporaryDirectory() as td:
    td=Path(td)
    m._I572_MISSION_SECRET_ROOT=td/'mission-unlocks'
    m._I572_MISSION_SECRET_ROOT.mkdir()
    m._I529_CREDENTIAL_ROOT=td/'credentials'
    m._I529_MASTER_SECRET_FILE=td/'master.secret'
    m._I564_MISSION_TOKENS.clear(); m._I572_PROTECTED_MISSIONS.clear()
    m._i572_set_protected('LOCKED-MISSION',True)

    # Successful unlock returns no secret, persists ciphertext, and caches token.
    m._i564_mission_request_raw=lambda *a,**k:{'ok':True,'status':200,'json':{'data':{'token':'MISSION-TOKEN'}}}
    reply,status=m._i572_unlock_action({'action':'unlock','mission':'LOCKED-MISSION','password':'MissionSecret!23'})
    assert status==200 and reply['ok'] and reply['unlocked']
    assert 'MissionSecret!23' not in repr(reply) and 'MISSION-TOKEN' not in repr(reply)
    record=m._i572_record_path('LOCKED-MISSION').read_text()
    assert 'MissionSecret!23' not in record and 'password_encrypted' in record
    assert m._i572_load_password('LOCKED-MISSION')['password']=='MissionSecret!23'

    # Invalid password is one definitive 401 and is never stored.
    m._i572_remove_password('LOCKED-MISSION'); m._I564_MISSION_TOKENS.clear()
    m._i564_mission_request_raw=lambda *a,**k:{'ok':False,'status':401,'json':{'error':'Invalid password'},'body':'{"error":"Invalid password"}'}
    reply,status=m._i572_unlock_action({'action':'unlock','mission':'LOCKED-MISSION','password':'wrong'})
    assert status==401 and reply['invalid_password'] and not m._i572_load_password('LOCKED-MISSION')['configured']

    # Protected save preflight prevents publication when locked.
    called={'count':0}
    def should_not_publish(payload):
        called['count']+=1
        return {'ok':True},200
    m._i572_save_before=should_not_publish
    reply,status=m._i555_save_point({'uid':'POINT-1','mission_name':'LOCKED-MISSION','name':'P','lat':1,'lon':2})
    assert status==428 and reply['mission_password_required'] and reply['publication_attempted'] is False
    assert called['count']==0

    # A protected read-back 401 stops after one call rather than four retries.
    calls={'count':0}
    def unauthorized(*a,**k):
        calls['count']+=1
        return {'ok':False,'status':401,'json':{'error':'Invalid password'},'body':'{"error":"Invalid password"}'}
    m._ots_mission_api_request=unauthorized
    out=m._i528_confirm_readback('LOCKED-MISSION','POINT-1','TAKMAP-TEST-UID')
    assert not out['ok'] and out['mission_password_required'] and calls['count']==1 and len(out['attempts'])==1

    # Exact-UID ingest confirmation is truthful success even if authorization races afterward.
    m._i572_set_protected('OPEN-MISSION',False)
    m._i572_save_before=lambda payload:({'ok':False,'publish':{'points':[{
        'per_user_cot_ingest':{'ingest_confirmed':True},
        'mission_readback':{'attempts':[{'status':401,'error':'Invalid password'}]}
    }]}},502)
    reply,status=m._i555_save_point({'uid':'POINT-2','mission_name':'OPEN-MISSION','name':'P2','lat':1,'lon':2,
                                     'symbol':{'kind':'custom','cot_type':'a-n-G','iconsetpath':'set/group/icon.png'}})
    assert status==200 and reply['ok'] and reply['server_ingest_confirmed'] and reply['mission_readback_deferred']

print('i572 focused protected-Mission/save tests passed')
