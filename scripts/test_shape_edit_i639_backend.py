#!/usr/bin/env python3
"""Backend contract for i639 native Shape geometry persistence."""
from pathlib import Path
import tempfile, xml.etree.ElementTree as ET, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import tak_dashboard as t

RECT='''<?xml version="1.0" encoding="UTF-8"?>
<event access="Undefined" how="h-e" stale="2026-09-03T14:06:34.877Z" start="2026-09-02T14:06:32.217Z" time="2026-09-02T14:06:34.877Z" type="u-d-r" uid="d9d9f0c2-696b-472d-95ed-29a705537a69" version="2.0"><point ce="9999999.0" hae="473.563" lat="34.2060116" le="9999999.0" lon="-118.72761"/><detail><link point="34.21028794604995,-118.75832320362926" custom="keep-a"/><link point="34.18305784557117,-118.71324111471124"/><link point="34.201731109450755,-118.69689581442177"/><link point="34.22896713330185,-118.74198259098516"/><__shapeExtras cpvis="true" editable="true"/><remarks>old notes</remarks><archive/><strokeColor value="-256"/><strokeWeight value="3.0"/><strokeStyle value="solid"/><fillColor value="16776960"/><creator callsign="slyfox" time="2026-06-25T01:47:49.237Z" type="a-f-G-U-C-R-V-G" uid="ANDROID-20ce457f78ce778e"/><labels_on value="false"/><tog enabled="0"/><precisionlocation altsrc="SRTM1"/><contact callsign="Rectangle 3"/><marti><dest mission="1-40TH RECON"/></marti></detail></event>'''
coords=[[34.211,-118.759],[34.182,-118.712],[34.200,-118.695],[34.229,-118.742]]
geom={
  'kind':'rectangle','cot_type':'u-d-r','uid':'d9d9f0c2-696b-472d-95ed-29a705537a69',
  'is_mission_object':True,'mission_names':['1-40TH RECON'],'coords':coords,
  'center':[sum(p[0] for p in coords)/4,sum(p[1] for p in coords)/4],
  'closed':True,'raw_cot_i636':RECT,'name':'Rectangle 3 Edited','notes':'edited notes'
}
patched,xml=t._i639_patch_shape_raw_cot(geom)
root=ET.fromstring(xml.encode())
assert root.attrib['uid']==geom['uid'] and root.attrib['type']=='u-d-r'
links=[n for n in root.iter() if t._i636_local_name(n.tag)=='link' and n.attrib.get('point')]
assert len(links)==4 and links[0].attrib.get('custom')=='keep-a'
for node,p in zip(links,coords):
    bits=node.attrib['point'].split(',')
    assert abs(float(bits[0])-p[0])<1e-7 and abs(float(bits[1])-p[1])<1e-7
assert t._i636_find_first(root,'strokeColor').attrib['value']=='-256'
assert t._i636_find_first(root,'creator').attrib['uid']=='ANDROID-20ce457f78ce778e'
assert t._i636_find_first(root,'precisionlocation').attrib['altsrc']=='SRTM1'
assert t._i636_find_first(root,'contact').attrib['callsign']=='Rectangle 3 Edited'
assert (t._i636_find_first(root,'remarks').text or '')=='edited notes'
assert t._i636_find_first(root,'dest').attrib['mission']=='1-40TH RECON'

# Native ellipse edits change only geometry/name/remarks while retaining nested KML style/detail metadata.
ELL='''<event uid="ellipse-i639" type="u-d-c-e" version="2.0"><point lat="34" lon="-118" hae="0"/><detail><shape><ellipse major="100" minor="50" angle="30"/><link uid="ellipse-i639.Style" type="b-x-KmlStyle" relation="p-c"><Style><LineStyle><color>ff00ff00</color><width>3</width></LineStyle></Style></link></shape><strokeColor value="-16711936"/><creator uid="creator-1" callsign="Creator"/><contact callsign="Ellipse"/><remarks>old</remarks><marti><dest mission="M"/></marti></detail></event>'''
eg={'kind':'ellipse','cot_type':'u-d-c-e','uid':'ellipse-i639','is_mission_object':True,'mission_names':['M'],'coords':[], 'center':[34.001,-118.002],'major_m':120,'minor_m':65,'angle_deg':47,'raw_cot_i636':ELL,'name':'Ellipse Edited','notes':'ellipse notes'}
eg2,exml=t._i639_patch_shape_raw_cot(eg); er=ET.fromstring(exml.encode()); ee=t._i636_find_first(er,'ellipse')
assert abs(float(ee.attrib['major'])-120)<1e-6 and abs(float(ee.attrib['minor'])-65)<1e-6 and abs(float(ee.attrib['angle'])-47)<1e-6
style_link=next(n for n in er.iter() if t._i636_local_name(n.tag)=='link' and n.attrib.get('uid')=='ellipse-i639.Style')
assert style_link.attrib['relation']=='p-c' and t._i636_find_first(er,'creator').attrib['uid']=='creator-1' and t._i636_find_first(er,'dest').attrib['mission']=='M'

# Exercise the current public popup update wrapper without touching the real host state.
# i643 must preserve the i639 raw-CoT patch while using native Shape SSL ingest,
# Mission /contents UID association, and Mission /cot GET-only verification.
with tempfile.TemporaryDirectory() as tmp:
    old_dir=t.TAK_MAP_OFFLINE_DIR; old_file=t.TAK_MAP_POPUP_EDITS_FILE; old_creator=t._i528_strict_creator; old_req=t._ots_mission_api_request; old_send=t._i531_send_per_user_cot; old_generic=t._send_cot_to_ots; old_token=t._i642_mission_token
    try:
        t.TAK_MAP_OFFLINE_DIR=Path(tmp)
        t.TAK_MAP_POPUP_EDITS_FILE=Path(tmp)/'popup_edits.json'
        t._i528_strict_creator=lambda:{'ok':True,'uid':'USER-UID','source':'test'}
        t._i642_mission_token=lambda mission,creator:''
        sent=[]
        def fake_send(cot,event_uid=''):
            sent.append(cot)
            return {'ok':True,'status':202,'event_uid':event_uid,'identity_mode':'per-user-enrolled-marti-certificate','client_uid':'USER-UID'}
        def fake_req(path,method='GET',body=None,headers=None,token='',public_host='',timeout=25):
            assert not (method in ('POST','PUT') and '/cot' in path),(method,path)
            if method=='PUT' and '/contents?' in path:
                return {'ok':True,'status':200,'body':'{}','json':{}}
            if method=='GET' and ('/Marti/api/cot/xml/' in path or '/Marti/api/missions/' in path and '/cot' in path):
                return {'ok':True,'status':200,'body':sent[-1] if sent else xml,'json':{}}
            return {'ok':False,'status':404,'error':'unexpected test path'}
        t._i531_send_per_user_cot=fake_send
        t._ots_mission_api_request=fake_req
        t._send_cot_to_ots=lambda cot: (_ for _ in ()).throw(AssertionError('generic CoT socket must not be used'))
        result=t.tak_map_popup_edit_update({'key':'datasync:'+geom['uid'],'source':'datasync','name':'Rectangle 3 Edited','notes':'edited notes','shape_geometry_i639':geom})
        assert result.get('ok') and result['shape_edit_i639']['server_cot_updated'] and len(sent)==1, result
        assert result['shape_edit_i643']['authoritative_global_readback_confirmed'] is True,result
        assert result['shape_edit_i643']['authoritative_mission_readback_confirmed'] is True,result
        saved=t._load_popup_edits()['items']['datasync:'+geom['uid']]['shape_geometry_i639']
        assert saved['uid']==geom['uid'] and len(saved['coords'])==4 and saved['raw_cot_i636']
        projected=t._apply_popup_edit({'uid':geom['uid'],'name':'Rectangle 3','type':'u-d-r','cot_type':'u-d-r','kind':'shape','is_mission_object':True})
        assert projected['coords']==coords and projected['shape_edit_geometry_i639'] is True
        assert projected['name']=='Rectangle 3 Edited'
    finally:
        t.TAK_MAP_OFFLINE_DIR=old_dir; t.TAK_MAP_POPUP_EDITS_FILE=old_file; t._i528_strict_creator=old_creator; t._ots_mission_api_request=old_req; t._i531_send_per_user_cot=old_send; t._send_cot_to_ots=old_generic; t._i642_mission_token=old_token

# Safety: rectangle topology/identity mismatch is rejected.
bad=dict(geom); bad['coords']=coords[:3]
try: t._i639_validate_shape_geometry(bad)
except ValueError: pass
else: raise AssertionError('three-corner rectangle accepted')
bad=dict(geom); bad['uid']='changed'
try: t._i639_patch_shape_raw_cot(bad)
except ValueError: pass
else: raise AssertionError('UID change accepted')
print('TAK Map i639 Shape backend edit contract passed')
