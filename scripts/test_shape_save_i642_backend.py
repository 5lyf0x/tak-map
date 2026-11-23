#!/usr/bin/env python3
"""TAK Map i642 authoritative Mission Shape save contract."""
from pathlib import Path
import tempfile,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import tak_dashboard as t
RECT='<event uid="rect-i642" type="u-d-r" version="2.0"><point lat="34" lon="-118"/><detail><link point="34.01,-118.02,0"/><link point="33.99,-118.00,0"/><link point="34.00,-117.98,0"/><link point="34.02,-118.01,0"/><contact callsign="Rect"/><remarks>old</remarks><marti><dest mission="M"/></marti></detail></event>'
coords=[[34.012,-118.023],[33.988,-118.001],[34.001,-117.977],[34.023,-118.010]]
center=[sum(p[0] for p in coords)/4,sum(p[1] for p in coords)/4]
geom={'kind':'rectangle','cot_type':'u-d-r','uid':'rect-i642','is_mission_object':True,'mission_names':['M'],'coords':coords,'center':center,'closed':True,'raw_cot_i636':RECT,'name':'Rect moved','notes':'saved'}
# Return the same rectangle from Mission /cot with a different start vertex and winding.
rb=[coords[2],coords[1],coords[0],coords[3]]
READBACK=f'''<event uid="rect-i642" type="u-d-r" version="2.0" time="2026-09-04T05:00:00Z" start="2026-09-04T05:00:00Z" stale="2026-09-05T05:00:00Z"><point lat="{center[0]}" lon="{center[1]}"/><detail><link point="{rb[0][0]},{rb[0][1]},0"/><link point="{rb[1][0]},{rb[1][1]},0"/><link point="{rb[2][0]},{rb[2][1]},0"/><link point="{rb[3][0]},{rb[3][1]},0"/><contact callsign="Rect moved"/><remarks>saved</remarks><marti><dest mission="M"/></marti></detail></event>'''
with tempfile.TemporaryDirectory() as tmp:
 old_file=t.TAK_MAP_POPUP_EDITS_FILE; old_creator=t._i528_strict_creator; old_req=t._ots_mission_api_request; old_socket=t._send_cot_to_ots
 try:
  t.TAK_MAP_POPUP_EDITS_FILE=Path(tmp)/'popup_edits.json'
  t._i528_strict_creator=lambda:{'ok':True,'uid':'USER-UID','source':'test'}
  calls=[]
  def req(path,method='GET',body=None,headers=None,token='',public_host='',timeout=25):
   calls.append((method,path,body,token))
   if method in ('POST','PUT'):
    return {'ok':True,'status':200,'body':'','json':{}}
   return {'ok':True,'status':200,'body':READBACK,'json':{}}
  t._ots_mission_api_request=req
  t._send_cot_to_ots=lambda xml: (_ for _ in ()).throw(AssertionError('generic CoT socket must not be used by i642 Mission Shape save'))
  result=t.tak_map_popup_edit_update({'key':'datasync:rect-i642','source':'datasync','name':'Rect moved','notes':'saved','shape_geometry_i639':geom})
  assert result['ok'],result
  tx=result['shape_edit_i642']; assert tx['authoritative_mission_readback_confirmed'] is True,tx
  assert tx['transport']=='native-mission-cot-api' and tx['generic_cot_socket_commit_gate'] is False and tx['aggregate_data_sync_commit_gate'] is False,tx
  assert tx['missions']==['M'] and tx['event_uid']=='rect-i642',tx
  assert any(m in ('POST','PUT') and '/Marti/api/missions/M/cot?creatorUid=USER-UID' in p for m,p,_,_ in calls),calls
  assert any(m=='GET' and p.startswith('/Marti/api/missions/M/cot') for m,p,_,_ in calls),calls
  saved=t._load_popup_edits()['items']['datasync:rect-i642']; assert saved['shape_geometry_confirmed_i642'] is True and saved['shape_geometry_i639']['coords']==coords,saved
  # Explicitly prove the ring comparator accepts cyclic/reversed equivalent rings and rejects changed geometry.
  assert t._i642_ring_equal(coords,rb)
  bad=[list(x) for x in rb];bad[0][0]+=0.01;assert not t._i642_ring_equal(coords,bad)
 finally:
  t.TAK_MAP_POPUP_EDITS_FILE=old_file;t._i528_strict_creator=old_creator;t._ots_mission_api_request=old_req;t._send_cot_to_ots=old_socket
print('TAK Map i642 authoritative Mission Shape save backend contract passed')
