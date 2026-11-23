#!/usr/bin/env python3
"""TAK Map i643 live-validated native Mission Shape save contract."""
from pathlib import Path
import tempfile,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import tak_dashboard as t

UID='rect-i643'; MISSION='M'; CREATOR='TAKMAP-USER-TEST'
OLD='<event uid="rect-i643" type="u-d-r" version="2.0" time="2026-09-01T00:00:00Z"><point lat="34" lon="-118"/><detail><link point="34.01,-118.02,0"/><link point="33.99,-118.00,0"/><link point="34.00,-117.98,0"/><link point="34.02,-118.01,0"/><contact callsign="Rect"/><remarks>old</remarks><marti><dest mission="M"/></marti></detail></event>'
coords=[[34.012,-118.023],[33.988,-118.001],[34.001,-117.977],[34.023,-118.010]]
center=[sum(p[0] for p in coords)/4,sum(p[1] for p in coords)/4]
geom={'kind':'rectangle','cot_type':'u-d-r','uid':UID,'is_mission_object':True,'mission_names':[MISSION],'coords':coords,'center':center,'closed':True,'raw_cot_i636':OLD,'name':'Rect moved','notes':'saved'}
# Same rectangle, reversed/winding-shifted to prove order-independent native comparison.
rb=[coords[2],coords[1],coords[0],coords[3]]
NEW=f'''<event uid="{UID}" type="u-d-r" version="2.0" time="2026-09-04T05:21:08.654Z" start="2026-09-04T05:21:08.654Z" stale="2026-09-05T05:21:08.654Z"><point lat="{center[0]}" lon="{center[1]}"/><detail><link point="{rb[0][0]},{rb[0][1]},0"/><link point="{rb[1][0]},{rb[1][1]},0"/><link point="{rb[2][0]},{rb[2][1]},0"/><link point="{rb[3][0]},{rb[3][1]},0"/><contact callsign="Rect moved"/><remarks>saved</remarks><marti><dest mission="M"/></marti></detail></event>'''

with tempfile.TemporaryDirectory() as tmp:
    old_file=t.TAK_MAP_POPUP_EDITS_FILE
    old_creator=t._i528_strict_creator
    old_req=t._ots_mission_api_request
    old_send=t._i531_send_per_user_cot
    old_token=t._i642_mission_token
    old_generic=t._send_cot_to_ots
    try:
        t.TAK_MAP_POPUP_EDITS_FILE=Path(tmp)/'popup_edits.json'
        t._i528_strict_creator=lambda:{'ok':True,'uid':CREATOR,'source':'test'}
        t._i642_mission_token=lambda mission,creator:'STALE-TOKEN'
        sent=[]; calls=[]; global_gets={'n':0}
        def send(xml,event_uid=''):
            sent.append((xml,event_uid))
            assert event_uid==UID
            assert 'type="u-d-r"' in xml and f'uid="{UID}"' in xml
            assert 'type="a-' not in xml
            assert '<dest mission="M"' in xml or "mission=\"M\"" in xml
            return {'ok':False,'status':504,'event_uid':event_uid,'identity_mode':'per-user-enrolled-marti-certificate','client_uid':CREATOR,'point_uid_used_as_eud_identity':False,'ingest_confirmed':False,'error':'legacy same-UID DB diagnostic intentionally not authoritative'}
        def req(path,method='GET',body=None,headers=None,token='',public_host='',timeout=25):
            calls.append((method,path,body,token))
            assert not (('/cot' in path) and method in ('POST','PUT')), (method,path)
            if path.startswith('/Marti/api/cot/xml/'):
                global_gets['n']+=1
                # First read deliberately returns the old same-UID geometry. It must NOT satisfy commit.
                xml=OLD if global_gets['n']==1 else NEW
                return {'ok':True,'status':200,'body':xml,'json':{}}
            if '/contents?' in path and method=='PUT':
                # Live deployment behavior: stale/failed token may 401, tokenless cert request succeeds.
                if token: return {'ok':False,'status':401,'error':'HTTP 401'}
                return {'ok':True,'status':200,'body':'{}','json':{}}
            if path.startswith('/Marti/api/missions/M/cot') and method=='GET':
                if token: return {'ok':False,'status':401,'error':'HTTP 401'}
                return {'ok':True,'status':200,'body':NEW,'json':{}}
            return {'ok':False,'status':404,'error':'unexpected test path'}
        t._i531_send_per_user_cot=send
        t._ots_mission_api_request=req
        t._send_cot_to_ots=lambda *a,**k: (_ for _ in ()).throw(AssertionError('generic shared CoT sender must never be used by i643 Shape save'))

        result=t.tak_map_popup_edit_update({'key':'datasync:'+UID,'source':'datasync','name':'Rect moved','notes':'saved','shape_geometry_i639':geom})
        assert result['ok'],result
        tx=result['shape_edit_i643']
        assert tx['native_shape_contract'] is True and tx['native_shape_type']=='u-d-r',tx
        assert tx['shape_uid_used_as_eud_identity'] is False,tx
        assert tx['transport']=='per-user-certificate-authenticated-ssl-cot',tx
        assert tx['global_cot_geometry_commit_gate'] is True and tx['authoritative_global_readback_confirmed'] is True,tx
        assert tx['mission_contents_uid_association'] is True and tx['mission_contents_method']=='PUT',tx
        assert tx['mission_cot_write_endpoint_used'] is False and tx['mission_cot_get_readback_only'] is True,tx
        assert tx['authoritative_mission_readback_confirmed'] is True,tx
        assert tx['aggregate_data_sync_commit_gate'] is False and tx['generic_public_cot_uid_lookup_commit_gate'] is False,tx
        assert global_gets['n']>=2,global_gets # old same-UID row did not satisfy geometry gate
        assert len(sent)==1,sent
        content_calls=[c for c in calls if '/contents?' in c[1]]
        assert len(content_calls)==2 and content_calls[0][3]=='STALE-TOKEN' and content_calls[1][3]=='',content_calls
        assert any(c[0]=='GET' and c[1].startswith('/Marti/api/missions/M/cot') for c in calls),calls
        assert not any(c[0] in ('POST','PUT') and '/Marti/api/missions/M/cot' in c[1] for c in calls),calls
        saved=t._load_popup_edits()['items']['datasync:'+UID]
        assert saved['shape_geometry_confirmed_i643'] is True and saved['shape_geometry_i639']['coords']==coords,saved
        assert t._i642_ring_equal(coords,rb)
        bad=[list(x) for x in rb];bad[0][0]+=0.01;assert not t._i642_ring_equal(coords,bad)
    finally:
        t.TAK_MAP_POPUP_EDITS_FILE=old_file
        t._i528_strict_creator=old_creator
        t._ots_mission_api_request=old_req
        t._i531_send_per_user_cot=old_send
        t._i642_mission_token=old_token
        t._send_cot_to_ots=old_generic
print('TAK Map i643 native Mission Shape save backend contract passed')
