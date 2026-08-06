#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, os, json, pathlib, sys, tempfile, uuid
ROOT=pathlib.Path(__file__).resolve().parents[1]
os.environ['TAK_MAP_MIL_ROOT']=str(ROOT/'assets/mil2525')
os.environ['TAK_MAP_TEST_SKIP_ADSB_WARMUP']='1'
spec=importlib.util.spec_from_file_location('tak_dashboard_i591_marker',ROOT/'tak_dashboard.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
assert m.TAK_MAP_ITERATION=='i601'
assert m.tak_map_config()['version']=='1.3.0-i601'
uid=str(uuid.uuid4())
marker={'uid':uid,'name':'Transit Van','latitude':34.626357,'longitude':-116.821146,'type':'a-f-G-E-V-C-M-L','hae':0.0,'ce':9999999.0,'le':9999999.0}
publish={
 'mission':'TAKMAP-DATASYNC-TEST2','event_uids':[uid],
 'points':[{
  'uid':uid,'source_uid':uid,'name':'Transit Van','lat':34.626357,'lon':-116.821146,
  'sidc':'SFGPEVCML------','cot_type':'a-f-G-E-V-C-M-L',
  'iconset_path':'COT_MAPPING_2525C/a-f/a-f-G-E-V-C-M-L',
  'per_user_cot_ingest':{
   'ok':True,'event_uid':uid,'i583_hf1_transport':'ots-marker-api',
   'marker_payload':marker,'marker_api_result':{'ok':True,'status':200,'json':{'success':True}},
   'live_eud_socket_used':False,'eud_presence':False,'point_uid_used_as_eud_identity':False},
  'associate_uid':{
   'ok':True,'status':200,'skipped':True,
   'reason':'existing-point-edit-does-not-reassociate',
   'association_endpoint':'existing-mission-membership-preserved'},
  'mission_readback':{
   'ok':False,'status':200,'event_uid':uid,
   'attempts':[{'attempt':n,'ok':True,'status':200,'exact_uid_present':False} for n in range(1,5)],
   'error':'The exact point UID was not returned by Mission read-back within the bounded confirmation window.'}
 }]}
payload={
 'mission_name':'TAKMAP-DATASYNC-TEST2','name':'Transit Van','lat':34.626357,'lon':-116.821146,
 'affiliation':'friendly','symbol':{
  'kind':'milstd2525c','name':'friendly-ground-equipment-van','label':'VAN',
  'sidc':'SFGPEVCVV------','cot_type':'a-f-G-E-V-C-V-V',
  'takmap_symbology_concept_i580':'ground-equipment-van'}}
# Feed the exact live response shape into the integrated hf1 wrapper.
m._i584p_save_before=lambda _:({'ok':False,'publish':json.loads(json.dumps(publish)),'error':'Mission read-back pending'},502)
m._i583_store_optimistic=lambda request,reply:{'uid':uid,'key':'test-state','mission':'TAKMAP-DATASYNC-TEST2'}
m._i583hf5_correct_optimistic_record=lambda optimistic,row: optimistic.update(row)
m._i568_schedule_refresh=lambda *a,**k: True
m._i509_load_ots_config=lambda:{}
m._i570_context_session=lambda:{}
with tempfile.TemporaryDirectory() as td:
 m._I584_PARITY_HF2_ROOT=pathlib.Path(td)
 m._i584p2_current_state_key=lambda:'test-state'
 reply,status=m._i555_save_point(payload)
 assert status==200 and reply['ok'] is True
 assert reply['status_label']=='Published · awaiting Mission index'
 assert reply['publication_complete'] is True and reply['mission_readback_deferred'] is True
 assert reply['existing_membership_association_counts_as_success_i584_hf1'] is True
 point=reply['point']
 assert point['uid']==uid and point['name']=='Transit Van'
 assert point['sidc']=='SFGPEVCML------'
 assert point['cot_type']=='a-f-G-E-V-C-M-L'
 assert point['iconset_path']=='COT_MAPPING_2525C/a-f/a-f-G-E-V-C-M-L'
 assert point['affiliation']=='F'
 persisted=reply.get('transport_authority_persisted_i584_hf2')
 assert persisted and persisted['uid']==uid and persisted['generic_rows_cannot_downgrade'] is True
 auth=m._i584p2_load_store('test-state')[uid]
 assert auth['sidc']=='SFGPEVCML------' and auth['affiliation']=='F'
 # A later incomplete Mission membership row must be promoted by exact UID
 # through the final i601 response owner, not an obsolete historical wrapper.
 generic={'uid':uid,'name':'Transit Van','lat':34.626357,'lon':-116.821146,'type':'t-x-d-d','iconsetPath':None,'mission':'TAKMAP-DATASYNC-TEST2'}
 state={'key':'test-state','snapshot':{'ok':True,'objects':[generic],'mission_uids':[],'missions':[]},'last_success_epoch':1.0,'completed_generation_i599':1,'snapshot_generation_i599':1}
 out=m._i568_response_payload(state)
 assert out['version']=='i601'
 row=out['objects'][0]
 assert row['sidc']=='SFGPEVCML------' and row['cot_type']=='a-f-G-E-V-C-M-L'
 assert row['iconsetPath']=='COT_MAPPING_2525C/a-f/a-f-G-E-V-C-M-L'
 assert row['affiliation']=='friendly'
 assert row['generic_mission_row_cannot_downgrade_i584_hf2'] is True
 assert out['data_sync_icon_parity_i585']['single_authoritative_catalog'] is True
print('i591 live Transit Van response shape, nonblocking delayed index, exact-UID persistence, generic-row promotion, affiliation, and final release response passed')
