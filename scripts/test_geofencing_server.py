#!/usr/bin/env python3
from __future__ import annotations
import json, os, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main():
    with tempfile.TemporaryDirectory(prefix='tak-map-gf-') as td:
        os.environ['TAK_DASHBOARD_DATA_DIR']=td
        import sys
        sys.path.insert(0,str(ROOT))
        import tak_dashboard as t

        shape={
            'object_id':'local-protected-shape','source_id':'local-protected-shape','local_id':'local-protected-shape','_local_id':'local-protected-shape','canonical_id':'local:local-protected-shape',
            'name':'Protected Area','kind':'shape','geometry':'polygon',
            'coords':[[34.0,-118.0],[34.0,-117.99],[34.01,-117.99],[34.0,-118.0]],
        }
        t.TAK_MAP_IMPORT_DIR.mkdir(parents=True,exist_ok=True)
        t.atomic_write_json(t.TAK_MAP_IMPORT_FILE,{'imports':[{'id':'gf-test-import','name':'GF Test','uploaded':'2026-07-19T00:00:00+00:00','features':[shape]}]})

        fence={
            'id':'gf-area-one','name':'Airport Perimeter','target_id':'local:local-protected-shape','target_source':'local','target_name':'Protected Area','kind':'shape',
            'geometry':{'type':'polygon','coordinates':[[-118.0,34.0],[-117.99,34.0],[-117.99,34.01],[-118.0,34.0]]},
            'monitored':['eud','adsb','local','datasync','gateway','satellite'],
            'triggers':{'enter':True,'exit':True,'dwell':True},'dwell_minutes':5,
            'altitude':{'mode':'band','min_ft':2000,'max_ft':12000},'enabled':True,
        }
        saved=t.tak_map_geofence_update({'action':'upsert','fence':fence})
        assert saved['ok'] and saved['fence']['triggers']['enter'] and saved['fence']['triggers']['exit']
        assert saved['fence']['altitude']['mode']=='band'
        assert t.TAK_MAP_GEOFENCE_FILE.exists()
        loaded=t.tak_map_geofences()
        assert loaded['rules']=={'confirmation_seconds':2,'rearm_seconds':10,'one_event_per_crossing':True,'stale_exit_events':False}
        assert len(loaded['fences'])==1

        blocked=t.tak_map_local_data_delete(['local-protected-shape'])
        assert blocked['ok'] is False, blocked
        assert blocked['protected_by_geofence']==['local:local-protected-shape'], blocked
        assert t.tak_map_imported()['imports'][0]['features'], blocked

        route={
            'id':'gf-route-one','name':'North Access Route','target_id':'datasync:route-stable','target_source':'datasync','target_name':'Route','kind':'route',
            'geometry':{'type':'route','coordinates':[[-118.1,34.0],[-117.9,34.0]]},
            'monitored':['eud','gateway'],'triggers':{'cross':True},'enabled':True,
        }
        assert t.tak_map_geofence_update({'action':'upsert','fence':route})['ok']
        ds=t.tak_map_object_delete(['datasync:route-stable'])
        assert ds['ok'] is False and ds['protected_by_geofence']==['datasync:route-stable'], ds

        assert t.tak_map_geofence_update({'action':'remove','id':'gf-area-one'})['removed'] is True
        deleted=t.tak_map_local_data_delete(['local-protected-shape'])
        assert deleted['ok'] and deleted['deleted_ids']==['local:local-protected-shape'], deleted

        config=t.tak_map_config()['geofencing']
        assert config['sidebar_design']=='Option A Operational Rows'
        assert config['event_window_design']=='Option C Dense Trigger Chips'
        assert config['collapse_control']=='minus_plus'
        assert config['boundary_confirmation_seconds']==2 and config['rearm_seconds']==10
        assert t.tak_map_config()['adsb']['type_filter_selected_accent']=='light_gray'
        print('TAK Map i491 geofencing server/persistence/protection test passed')
        print(json.dumps({'fences':len(t.tak_map_geofences()['fences']),'config':config},sort_keys=True))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
