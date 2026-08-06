#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, json, pathlib, sys, uuid
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('tak_dashboard_i584_marker',ROOT/'tak_dashboard.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
assert m.TAK_MAP_ITERATION=='i584'

point_uid=str(uuid.uuid4())
xml=f'''<event version="2.0" uid="{point_uid}" type="a-f-G-E-V-A-T" time="2026-07-29T00:00:00Z" start="2026-07-29T00:00:00Z" stale="2026-07-30T00:00:00Z" how="h-e"><point lat="34.1234567" lon="-117.7654321" hae="812.5" ce="4.25" le="7.5"/><detail><contact callsign="Tank"/><usericon iconsetpath="COT_MAPPING_2525C/a-f/a-f-G-E-V-A-T"/></detail></event>'''
marker,icon_path=m._i583hf_marker_payload(xml)
assert marker=={
 'uid':point_uid,'name':'Tank','latitude':34.1234567,'longitude':-117.7654321,
 'type':'a-f-G-E-V-A-T','hae':812.5,'ce':4.25,'le':7.5}
assert icon_path=='COT_MAPPING_2525C/a-f/a-f-G-E-V-A-T'
assert m._i583hf_uuid4(point_uid)==point_uid
assert m._i583hf_uuid4('TAKMAP-MISSION-POINT-LEGACY')==''

token='test-marker-token-not-for-output'
assert m._i583hf4_extract_authentication_token({'response':{'user':{'authentication_token':token}}})==token
session_key='test-local-session'
m._I529_REQUEST_CONTEXT.session_token=session_key
with m.TAK_MAP_SESSIONS_LOCK:
    m.TAK_MAP_SESSIONS[session_key]={'auth_mode':'ots-user',m._I583_HF4_SESSION_TOKEN_FIELD:token}
m._i509_load_ots_config=lambda:{'base_url':'https://ots.example'}
calls=[]
def fake_send(cfg,base,path,method,body,timeout,marker_token,auth_mode):
    calls.append((path,method,marker_token,auth_mode,body))
    if auth_mode=='authentication-token-header':
        return {'ok':False,'status':401,'error':'header unsupported','i583_hf4_auth':{'method':auth_mode}}
    return {'ok':True,'status':200,'json':{'success':True},'i583_hf4_auth':{'method':auth_mode}}
m._i583hf4_send_marker_request=fake_send
res=m._i583hf_api_request('/api/markers',method='POST',payload=marker)
assert res['ok'] is True and res['status']==200
assert [row[3] for row in calls]==['authentication-token-header','auth_token-query']
assert all(row[2]==token for row in calls)
assert res['i583_hf4_attempts']==[
 {'method':'authentication-token-header','status':401},
 {'method':'auth_token-query','status':200}]
source=(ROOT/'tak_dashboard.py').read_text()
hf4=source[source.index('# --- TAK Map i583 reversible Mission-marker hotfix hf4'):source.index('# --- end TAK Map i583 reversible Mission-marker hotfix hf4 ---')]
assert "Authorization': 'Bearer" not in hf4 and 'Authorization: Bearer' not in hf4

publish={
 'mission':'ALPHA','event_uids':[point_uid],
 'points':[{
   'uid':point_uid,'name':'Tank','lat':34.1234567,'lon':-117.7654321,
   'per_user_cot_ingest':{
      'ok':True,'event_uid':point_uid,'i583_hf1_transport':'ots-marker-api',
      'marker_payload':marker,'live_eud_socket_used':False,'eud_presence':False,
      'point_uid_used_as_eud_identity':False},
   'associate_uid':{'ok':True,'status':200},
   'mission_readback':{'ok':False,'status':504,'error':'index pending'},
 }]}
m._i583hf5_save_before=lambda payload:({'ok':False,'publish':publish,'error':'Mission read-back pending'},502)
m._i583_store_optimistic=lambda payload,reply:None
payload={'mission_name':'ALPHA','name':'Tank','lat':34.1234567,'lon':-117.7654321,'affiliation':'friendly','symbol':{
 'kind':'milstd2525c','sidc':'SFGPEVAT-------','cot_type':'a-f-G-E-V-A-T',
 'name':'friendly-ground-equipment-engineer-vehicle-armored-tank','file':'friendly-ground-equipment-engineer-vehicle-armored-tank.svg','label':'TANK'}}
reply,status=m._i555_save_point(payload)
assert status==200 and reply['ok'] is True and reply['publication_complete'] is True
assert reply['mission_readback_deferred'] is True and reply['awaiting_mission_index'] is True
assert reply['local_data_retained'] is False and reply['placement_preview_must_close'] is True
assert reply['delete_supported'] is True and reply['mission_delete_value']==point_uid
assert reply['point']['uid']==point_uid and reply['point']['name']=='Tank'
assert reply['point']['lat']==34.1234567 and reply['point']['lon']==-117.7654321
assert reply['point']['delete_supported'] is True
assert reply['point_not_eud_i583_hf5'] is True and reply['exact_location_preserved_i583_hf5'] is True

bad=json.loads(json.dumps(publish));bad['points'][0]['associate_uid']={'ok':False,'status':500}
m._i583hf5_save_before=lambda payload:({'ok':False,'publish':bad,'error':'association failed'},502)
failed,failed_status=m._i555_save_point(payload)
assert failed_status==502 and failed['ok'] is False

out=m._i568_response_payload({'snapshot':{'ok':True,'objects':[],'mission_uids':[],'missions':[]}})
assert out['version']=='i584'
assert out['data_sync_marker_publication_i584']['point_not_eud_or_contact'] is True
print('i584 marker payload, dedicated OTS auth, no Bearer marker auth, delayed-index success, exact location, immediate Delete, association failure, and release response tests passed')
