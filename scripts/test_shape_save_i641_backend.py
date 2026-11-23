#!/usr/bin/env python3
"""Backend persistence contract for TAK Map i641 Shape Save."""
from pathlib import Path
import tempfile,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import tak_dashboard as t
RECT='<event uid="rect-i641" type="u-d-r" version="2.0"><point lat="34" lon="-118"/><detail><link point="34.01,-118.02,0"/><link point="33.99,-118.00,0"/><link point="34.00,-117.98,0"/><link point="34.02,-118.01,0"/><contact callsign="Rect"/><remarks>old</remarks><marti><dest mission="M"/></marti></detail></event>'
coords=[[34.012,-118.023],[33.988,-118.001],[34.001,-117.977],[34.023,-118.010]]
geom={'kind':'rectangle','cot_type':'u-d-r','uid':'rect-i641','is_mission_object':True,'mission_names':['M'],'coords':coords,'center':[sum(p[0] for p in coords)/4,sum(p[1] for p in coords)/4],'closed':True,'raw_cot_i636':RECT,'name':'Rect moved','notes':'saved'}
with tempfile.TemporaryDirectory() as tmp:
 old_dir=t.TAK_MAP_OFFLINE_DIR;old_file=t.TAK_MAP_POPUP_EDITS_FILE;old_send=t._send_cot_to_ots
 try:
  t.TAK_MAP_OFFLINE_DIR=Path(tmp);t.TAK_MAP_POPUP_EDITS_FILE=Path(tmp)/'popup_edits.json';sent=[]
  t._send_cot_to_ots=lambda cot:(sent.append(cot) or {'ok':True,'transport':'test'})
  result=t.tak_map_popup_edit_update({'key':'datasync:rect-i641','source':'datasync','name':'Rect moved','notes':'saved','shape_geometry_i639':geom})
  assert result['ok'] and result['shape_edit_i639']['persisted_overlay'] is True,result
  assert result['shape_edit_i639']['readback_contract']=='data-sync-applies-persisted-shape-geometry'
  assert result['shape_edit_i639']['saved_uid']=='rect-i641' and result['shape_edit_i639']['saved_at']
  assert len(sent)==1
  saved=t._load_popup_edits()['items']['datasync:rect-i641']['shape_geometry_i639'];assert saved['coords']==coords and saved['uid']=='rect-i641'
  projected=t._apply_popup_edit({'uid':'rect-i641','type':'u-d-r','cot_type':'u-d-r','kind':'shape','name':'old','coords':[[1,1],[1,2],[2,2],[2,1]],'is_mission_object':True})
  assert projected['coords']==coords and projected['name']=='Rect moved' and projected['shape_edit_geometry_i639'] is True,projected
 finally:
  t.TAK_MAP_OFFLINE_DIR=old_dir;t.TAK_MAP_POPUP_EDITS_FILE=old_file;t._send_cot_to_ots=old_send
print('TAK Map i641 Shape Save persisted-overlay backend contract passed')
