#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, io, json, os, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SERVER=ROOT/'tak_dashboard.py'

def load_module(tmp:Path):
    os.environ['TAK_DASHBOARD_DATA_DIR']=str(tmp)
    spec=importlib.util.spec_from_file_location('tak_dashboard_object_lifecycle_test',SERVER)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def main()->int:
    with tempfile.TemporaryDirectory(prefix='tak-map-object-life-') as td:
        m=load_module(Path(td))
        m.TAK_MAP_IMPORT_DIR.mkdir(parents=True,exist_ok=True)
        original=[
            {'kind':'point','name':'duplicate','lat':34.1,'lon':-118.1},
            {'kind':'point','name':'duplicate','lat':34.1,'lon':-118.1},
            {'kind':'route','name':'route','coords':[[34.2,-118.2],[34.3,-118.3]]},
            {'kind':'shape','name':'shape','coords':[[34.4,-118.4],[34.4,-118.5],[34.5,-118.5]]},
            {'kind':'point','name':'last','lat':34.6,'lon':-118.6},
        ]
        m.atomic_write_json(m.TAK_MAP_IMPORT_FILE,{'imports':[{'id':'imp-a','name':'objects.geojson','features':original}]})
        migrated=m.tak_map_imported();features=migrated['imports'][0]['features'];ids=[x['canonical_id'] for x in features]
        assert len(ids)==5 and len(set(ids))==5 and all(x.startswith('local:local-') for x in ids),ids
        assert ids==[x['canonical_id'] for x in m.tak_map_imported()['imports'][0]['features']]
        stored=json.loads(m.TAK_MAP_IMPORT_FILE.read_text())['imports'][0]['features']
        assert all(x.get('object_id') and x.get('canonical_id') for x in stored)
        assert all(x.get('legacy_local_id','').startswith('imp-a:') for x in stored)

        # Point Marker, coordinate save, and drawing tools all post GeoJSON to this import endpoint.
        uploaded_geojson={
            'type':'FeatureCollection',
            'features':[
                {'type':'Feature','geometry':{'type':'Point','coordinates':[-118.7,34.7]},'properties':{'name':'Tool Point','kind':'point'}},
                {'type':'Feature','geometry':{'type':'LineString','coordinates':[[-118.8,34.8],[-118.9,34.9]]},'properties':{'name':'Tool Route','kind':'route'}},
                {'type':'Feature','geometry':{'type':'Polygon','coordinates':[[[-118.1,34.1],[-118.2,34.1],[-118.2,34.2],[-118.1,34.1]]]},'properties':{'name':'Tool Shape','kind':'shape'}},
            ],
        }
        boundary='----takmapobjectlifecycletest'
        payload=json.dumps(uploaded_geojson).encode()
        body=(
            f'--{boundary}\r\n'
            'Content-Disposition: form-data; name="files"; filename="tools.geojson"\r\n'
            'Content-Type: application/geo+json\r\n\r\n'
        ).encode()+payload+f'\r\n--{boundary}--\r\n'.encode()
        class UploadHandler:
            headers={'Content-Type':f'multipart/form-data; boundary={boundary}','Content-Length':str(len(body))}
            rfile=io.BytesIO(body)
            def _send_json(self,data,status=200):
                self.data=data;self.status=status;return data
        uploader=UploadHandler();upload_result=m.handle_tak_map_import_upload(uploader)
        assert uploader.status==200 and upload_result['ok'],upload_result
        uploaded=upload_result['added'][0]['features']
        assert [x['object_kind'] for x in uploaded]==['point','route','shape'],uploaded
        assert len({x['canonical_id'] for x in uploaded})==3 and all(x['canonical_id'].startswith('local:local-') for x in uploaded),uploaded

        middle=m.tak_map_local_data_delete([ids[2]])
        assert middle['deleted_ids']==[ids[2]] and middle['not_found_ids']==[] and middle['unsupported_ids']==[],middle
        remaining=[x['canonical_id'] for x in m.tak_map_imported()['imports'][0]['features']]
        assert remaining==[ids[0],ids[1],ids[3],ids[4]],remaining
        stale_index=m.tak_map_local_data_delete(['imp-a:2'])
        assert stale_index['deleted_ids']==[] and 'imp-a:2' in stale_index['not_found_ids'],stale_index
        assert [x['canonical_id'] for x in m.tak_map_imported()['imports'][0]['features']]==remaining
        # Duplicate names and coordinates remain independently addressable.
        first=m.tak_map_local_data_delete([ids[0]])
        assert first['deleted_ids']==[ids[0]],first
        selected=m._selected_local_data_features([ids[1],ids[3]])
        assert [x['canonical_id'] for x in selected]==[ids[1],ids[3]],selected
        last=m.tak_map_local_data_delete([ids[4]])
        assert last['deleted_ids']==[ids[4]],last
        not_found=m.tak_map_local_data_delete([ids[2]])
        assert not_found['deleted_ids']==[] and ids[2] in not_found['not_found_ids'],not_found
        persisted=[x['canonical_id'] for x in m.tak_map_imported()['imports'][0]['features']]
        assert persisted==[ids[1],ids[3]],persisted

        candidates=m._popup_edit_key_candidates({'canonical_id':ids[1],'name':'duplicate','lat':34.1,'lon':-118.1,'source':'Local Data'})
        assert candidates[0]==ids[1],candidates

        raw={
            'missions':[{'id':7,'name':'Alpha'}],
            'mission_uids':[{'mission_id':7,'uid':'UID-POINT-1'}],
            'mission_content':[{'id':11,'hash':'HASH-ROUTE-1','filename':'route.zip'}],
            'mission_content_mission':[{'mission_id':7,'content_id':11}],
            'objects':[
                {'kind':'datasync','geometry':'point','uid':'UID-POINT-1','name':'Point'},
                {'kind':'route','geometry':'route','id':'route.zip','name':'Route','coords':[[1,2],[3,4]]},
                {'kind':'shape','geometry':'shape','name':'No owner','coords':[[1,2],[1,3],[2,3]]},
            ],
        }
        normalized=m._tak_enrich_data_sync_result(raw)
        point,route,unsupported=normalized['objects']
        assert point['delete_supported'] and point['mission_delete_target']=='uid' and point['mission_delete_value']=='UID-POINT-1',point
        assert route['delete_supported'] and route['mission_delete_target']=='hash' and route['mission_delete_value']=='HASH-ROUTE-1',route
        assert unsupported['delete_supported'] is False and not unsupported.get('canonical_id'),unsupported

        multi_raw={
            'missions':[{'id':7,'name':'Alpha'},{'id':8,'name':'Bravo'}],
            'mission_uids':[{'mission_id':7,'uid':'UID-MULTI'},{'mission_id':8,'uid':'UID-MULTI'}],
            'objects':[{'kind':'point','uid':'UID-MULTI','name':'Ambiguous'}],
        }
        multi=m._tak_enrich_data_sync_result(multi_raw)['objects'][0]
        assert multi.get('canonical_id','').startswith('datasync:datasync-'),multi
        assert multi['delete_supported'] is False and 'multiple missions' in multi['delete_unavailable_reason'],multi
        explicit_raw=dict(multi_raw);explicit_raw['objects']=[{'kind':'point','uid':'UID-MULTI','name':'Explicit','mission_name':'Bravo'}]
        explicit=m._tak_enrich_data_sync_result(explicit_raw)['objects'][0]
        assert explicit['delete_supported'] and explicit['mission_name']=='Bravo' and explicit['mission_delete_target']=='uid',explicit
        moved_raw={'missions':[{'id':9,'name':'Charlie'}],'mission_uids':[{'mission_id':9,'uid':'UID-MULTI'}],'objects':[{'kind':'point','uid':'UID-MULTI'}]}
        moved=m._tak_enrich_data_sync_result(moved_raw)['objects'][0]
        assert moved['canonical_id']==multi['canonical_id'],(multi,moved)

        called=[]
        m._mission_publish_creator_uid=lambda preferred_uid='': {'ok':True,'uid':'CREATOR-1'}
        def fake_request(path,method='GET',body=None,headers=None,token='',public_host='',timeout=25):
            called.append({'path':path,'method':method,'headers':headers or {}})
            return {'ok':True,'status':200,'json':{}}
        m._ots_mission_api_request=fake_request
        deleted=m._tak_data_sync_delete_record(point)
        assert deleted['status']=='deleted',deleted
        assert called[-1]['method']=='DELETE' and '/Marti/api/missions/Alpha/contents?' in called[-1]['path'],called
        assert 'creatorUid=CREATOR-1' in called[-1]['path'] and 'uid=UID-POINT-1' in called[-1]['path'],called
        assert called[-1]['headers']['User-Agent'].startswith('iTAK/'),called

        # Consolidated endpoint resolves server-owned objects and returns exact status arrays.
        m._tak_fresh_data_sync_result=lambda: normalized
        local_left=ids[1]
        combined=m.tak_map_object_delete([local_left,point['canonical_id'],unsupported.get('canonical_id') or 'unsupported-object'])
        assert local_left in combined['deleted_ids'] and point['canonical_id'] in combined['deleted_ids'],combined
        assert 'unsupported-object' in combined['unsupported_ids'],combined
        assert combined['failed_ids']==[],combined

        lifecycle_cfg=m.tak_map_config()['object_lifecycle']
        assert lifecycle_cfg['persistent_local_ids'] and lifecycle_cfg['mission_api_delete'] and lifecycle_cfg['per_object_hide'] is False,lifecycle_cfg
        assert lifecycle_cfg['future_visibility_scope']==['points','routes','shapes'],lifecycle_cfg
        assert 'takMapObjectLifecycleLoaderV486' in m.TAK_MAP_HTML
        assert '/assets/runtime/tak-map-object-lifecycle-v491.js' in m.TAK_MAP_HTML
        assert 'id="toolClearHidden"' not in m.TAK_MAP_HTML
        print('Object lifecycle server migration, stable deletion, Mission API ownership, and consolidated delete tests passed')
        print(json.dumps({'initial_ids':ids,'remaining_after_tests':[x['canonical_id'] for x in m.tak_map_imported().get('imports',[{'features':[]}])[0].get('features',[]) ] if m.tak_map_imported().get('imports') else [],'mission_delete_path':called[-1]['path']},sort_keys=True))
    return 0

if __name__=='__main__':raise SystemExit(main())
