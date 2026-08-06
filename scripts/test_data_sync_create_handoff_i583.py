#!/usr/bin/env python3
from __future__ import annotations
import importlib.util,pathlib,sys,tempfile,time
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('tak_dashboard_i583_create',ROOT/'tak_dashboard.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
m._I568_SNAPSHOT_ROOT=pathlib.Path(tempfile.mkdtemp(prefix='takmap-i583-create-'));m._I568_STATES.clear()
cfg={'marti_url':'https://ots.example:8443','api_url':'https://ots.example'}
sess={'auth_mode':'ots-user','username':'tester','profile':{'username':'tester'}}
key=m._i568_state_key(cfg,sess);state=m._i568_state(key)
state['snapshot']={'ok':True,'objects':[],'mission_uids':[],'missions':[{'name':'ALPHA','uids':[]}]}
uid='TAKMAP-MISSION-POINT-CREATE123'
full={'uid':uid,'event_uid':uid,'cot_uid':uid,'mission':'ALPHA','mission_name':'ALPHA','callsign':'Mech Inf','name':'Mech Inf','lat':34.2,'lon':-118.3,'sidc':'SFGPUCIZ-------','cot_type':'a-f-G-U-C-I-Z','type':'a-f-G-U-C-I-Z','mil2525_name':'friendly-ground-unit-infantry-mechanized','mil2525_file':'friendly-ground-unit-infantry-mechanized.svg','kind':'datasync','is_mission_object':True}
# Replace only the dependencies captured by the final i583 wrapper.
m._i583_save_before=lambda payload:({'ok':True,'redraw_allowed':True,'point':{'uid':uid,'mission_name':'ALPHA','name':'Mech Inf','lat':34.2,'lon':-118.3,'sidc':'SFGPUCIZ-------','cot_type':'a-f-G-U-C-I-Z'}},200)
m._i570_snapshot_find=lambda u,mission='': full if u==uid else None
m._i570_context_state_key=lambda cfg=None,sess=None:key
m._i509_load_ots_config=lambda:cfg
m._i570_context_session=lambda:sess
scheduled=[]
m._i568_schedule_refresh=lambda *args,**kwargs:scheduled.append((args,kwargs)) or (False,'test-coalesced')
payload={'mission_name':'ALPHA','name':'Mech Inf','lat':34.2,'lon':-118.3,'affiliation':'friendly','symbol':{'kind':'milstd2525c','sidc':'SFGPUCIZ-------','cot_type':'a-f-G-U-C-I-Z','name':'friendly-ground-unit-infantry-mechanized','file':'friendly-ground-unit-infantry-mechanized.svg','label':'MECH INF'}}
reply,status=m._i555_save_point(payload)
assert status==200 and reply['optimistic_data_sync_handoff_i583']['active'] is True
assert scheduled and scheduled[-1][0][-1]=='i583-post-save-membership-fastpath'
state=m._i568_state(key)
assert len(state['i583_optimistic_rows'])==1
visible=m._i568_response_payload(state)
rows=[r for r in visible['objects'] if r.get('uid')==uid]
assert len(rows)==1 and rows[0]['callsign']=='Mech Inf' and rows[0]['sidc']=='SFGPUCIZ-------'
# Persistence survives process/state restart before canonical membership arrives.
m._I568_STATES.clear();reloaded=m._i568_state(key)
assert len(reloaded['i583_optimistic_rows'])==1
visible=m._i568_response_payload(reloaded);assert any(r.get('uid')==uid for r in visible['objects'])
# A generic membership publish cannot replace the known symbol.
reloaded['generation']=7;reloaded['i583_worker_running']=True
partial={'ok':True,'objects':[{'uid':uid,'event_uid':uid,'mission':'ALPHA','callsign':uid,'name':uid,'lat':34.2,'lon':-118.3,'sidc':'SFGPU----------','cot_type':'a-f-G-U'}],
         'mission_uids':[],'missions':[{'name':'ALPHA','uids':[]}],
         'data_sync_membership_corroboration_i582':{'mission_decisions':{'alpha':'accepted-complete-nonempty'}}}
acquired={'timings':[],'summary':{'phase':'membership-published'}}
m._i582_publish_state(key,7,partial,acquired,'membership-published',membership={'alpha':[uid.lower()]},candidates={},added={( 'alpha',uid.lower())},deleted=set(),keep_in_flight=True)
row=next(r for r in m._i568_state(key)['snapshot']['objects'] if r.get('uid')==uid)
assert row['callsign']=='Mech Inf' and row['sidc']=='SFGPUCIZ-------'
# Exact-UID CoT publish retires the shadow and leaves the canonical row.
auth=dict(full);auth['source']='Mission /cot authoritative'
enriched={'ok':True,'objects':[auth],'mission_uids':[auth],'missions':[{'name':'ALPHA','uids':[auth]}],
          'data_sync_membership_corroboration_i582':{'mission_decisions':{'alpha':'accepted-complete-nonempty'}}}
m._i582_publish_state(key,7,enriched,acquired,'full-cot-enrichment-published',membership={'alpha':[uid.lower()]},candidates={},added=set(),deleted=set(),keep_in_flight=False,full_cot_completed=True)
state=m._i568_state(key);assert state['i583_optimistic_rows']=={}
row=next(r for r in state['snapshot']['objects'] if r.get('uid')==uid)
assert row['source']=='Mission /cot authoritative' and not row.get('data_sync_optimistic_i583')
print('i583 save response, persistent immediate visibility, partial-row protection, restart persistence, and exact-UID handoff tests passed')
