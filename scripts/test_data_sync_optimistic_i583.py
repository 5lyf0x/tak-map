#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, pathlib, sys, tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('tak_dashboard_i583_optimistic',ROOT/'tak_dashboard.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
assert m.TAK_MAP_ITERATION=='i583'
m._I568_SNAPSHOT_ROOT=pathlib.Path(tempfile.mkdtemp(prefix='takmap-i583-opt-'))
m._I568_STATES.clear()
cfg={'marti_url':'https://ots.example:8443','api_url':'https://ots.example'}
sess={'auth_mode':'ots-user','username':'tester','profile':{'username':'tester'}}
key=m._i568_state_key(cfg,sess); state=m._i568_state(key)
mission='alpha'; uid='TAKMAP-MISSION-POINT-TEST123'
shadow={'uid':uid,'event_uid':uid,'cot_uid':uid,'mission':'ALPHA','mission_name':'ALPHA','callsign':'Mech Inf','name':'Mech Inf','lat':34.1,'lon':-118.2,'sidc':'SFGPUCIZ-------','SIDC':'SFGPUCIZ-------','cot_type':'a-f-G-U-C-I-Z','type':'a-f-G-U-C-I-Z','mil2525_name':'friendly-ground-unit-infantry-mechanized','mil2525_file':'friendly-ground-unit-infantry-mechanized.svg','kind':'datasync','is_mission_object':True}
state['i583_optimistic_rows']={m._i583_shadow_key(mission,uid):{'row':shadow,'created_epoch':1,'membership_seen':False}}
# An old empty snapshot cannot remove the just-created point.
out=m._i583_merge_optimistic({'ok':True,'objects':[],'mission_uids':[],'missions':[]},state,'old-snapshot',{},allow_retire=False)
assert len(out['objects'])==1 and out['objects'][0]['uid']==uid
assert out['objects'][0]['sidc']=='SFGPUCIZ-------' and out['objects'][0]['callsign']=='Mech Inf'
# A partial generic row may add data but cannot downgrade the known icon/name.
generic={'uid':uid,'event_uid':uid,'mission':'ALPHA','callsign':uid,'name':uid,'lat':34.1,'lon':-118.2,'sidc':'SFGPU----------','cot_type':'a-f-G-U','type':'a-f-G-U'}
out=m._i583_merge_optimistic({'ok':True,'objects':[generic],'mission_uids':[generic],'missions':[{'name':'ALPHA','uids':[generic]}]},state,'membership-published',{mission:[uid.lower()]},allow_retire=True)
row=out['objects'][0]
assert row['callsign']=='Mech Inf' and row['sidc']=='SFGPUCIZ-------' and row['cot_type']=='a-f-G-U-C-I-Z'
record=next(iter(state['i583_optimistic_rows'].values())); assert record['membership_seen'] is True
# Exact-UID authoritative CoT enrichment completes the canonical handoff.
auth={'uid':uid,'event_uid':uid,'cot_uid':uid,'mission':'ALPHA','mission_name':'ALPHA','callsign':'Mech Inf','name':'Mech Inf','lat':34.1,'lon':-118.2,'sidc':'SFGPUCIZ-------','cot_type':'a-f-G-U-C-I-Z','type':'a-f-G-U-C-I-Z','source':'Mission /cot authoritative'}
out=m._i583_merge_optimistic({'ok':True,'objects':[auth],'mission_uids':[auth],'missions':[{'name':'ALPHA','uids':[auth]}]},state,'full-cot-enrichment-published',{mission:[uid.lower()]},allow_retire=True)
assert state['i583_optimistic_rows']=={}
assert out['objects'][0]['source']=='Mission /cot authoritative' and not out['objects'][0].get('data_sync_optimistic_i583')
# Once membership was seen, an authoritative complete nonempty membership result
# that omits the UID retires the shadow as a confirmed deletion.
state['i583_optimistic_rows']={m._i583_shadow_key(mission,uid):{'row':shadow,'created_epoch':1,'membership_seen':True}}
snap={'ok':True,'objects':[],'mission_uids':[],'missions':[{'name':'ALPHA','uids':[]}],
      'data_sync_membership_corroboration_i582':{'mission_decisions':{mission:'accepted-complete-nonempty'}}}
out=m._i583_merge_optimistic(snap,state,'membership-published',{mission:['another-uid']},allow_retire=True)
assert state['i583_optimistic_rows']=={} and out['objects']==[]
print('i583 optimistic create visibility, generic-downgrade prevention, canonical handoff, and deletion retirement tests passed')
