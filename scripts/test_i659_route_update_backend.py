#!/usr/bin/env python3
"""Exercise actual final i659 server update function with an isolated Local Data file."""
import ast, json, threading, tempfile, sys
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]
tree=ast.parse((ROOT/'tak_dashboard.py').read_text())
functions=['_i659_route_revision','_i659_update_route','_clean_props','_feature_name',
  '_geojson_positions_to_latlon','_geojson_line_to_latlon','_parse_geojson_obj','_import_summary']
nodes=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in functions]
assert {n.name for n in nodes}==set(functions)
namespace={'json':json,'datetime':datetime,'timezone':timezone,'_coerce_float':lambda x:float(x) if x is not None else None,'_TAK_LOCAL_OBJECT_LOCK':threading.RLock()}
namespace['json_complete_dumps']=lambda data,**kwargs:json.dumps(data,**kwargs)  # exact JSON, never diagnostic truncation
exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),str(ROOT/'tak_dashboard.py'),'exec'),namespace)
with tempfile.TemporaryDirectory() as tmp:
 registry=Path(tmp)/'imports.json';namespace['TAK_MAP_IMPORT_FILE']=registry;namespace['TAK_MAP_IMPORT_DIR']=Path(tmp)
 namespace['load_json_file']=lambda p,default:json.loads(Path(p).read_text()) if Path(p).exists() else default
 namespace['atomic_write_json']=lambda p,data:Path(p).write_text(json.dumps(data))
 namespace['_tak_migrate_local_data_ids']=lambda persist:None
 namespace['tak_map_imported']=lambda:{'ok':True,'imports':namespace['load_json_file'](registry,{'imports':[]})['imports']}
 route={'kind':'route','geometry':'route','name':'Saved Road Route','object_id':'local-abc-123456789',
    'coords':[[34,-118],[34.1,-118.1],[34.2,-118.2]],'lat':34,'lon':-118,
    'properties':{'name':'Saved Road Route','color':'#ff6f2e'}}
 other={'kind':'point','name':'Preserved Point','object_id':'local-other-123456','lat':32,'lon':-110,'coords':[[32,-110]]}
 stored={'imports':[{'id':'imp-001','name':'saved.geojson','features':[route,other],'counts':{'route':1,'point':1,'shape':0,'other':0}}]}
 registry.write_text(json.dumps(stored))
 revision=namespace['_i659_route_revision'](route)
 payload={'import_id':'imp-001','object_id':'local-abc-123456789','expected_revision':revision,
   'feature':{'type':'Feature','geometry':{'type':'LineString','coordinates':[[-118,34],[-118.06,34.06],[-118.12,34.11],[-118.2,34.2]]},
     'properties':{'name':'Edited Road Route','kind':'route','color':'#11aabb',
       'route_control_point_count':2,'route_cp_0':'34.000000,-118.000000,roads','route_cp_1':'34.200000,-118.200000,roads'}}}
 result,status=namespace['_i659_update_route'](payload)
 assert status==200 and result['ok'],(status,result)
 after=json.loads(registry.read_text())['imports'][0]
 assert len(after['features'])==2 and after['features'][1]==other
 updated=after['features'][0]
 assert updated['object_id']==route['object_id']
 assert updated['name']=='Edited Road Route' and len(updated['coords'])==4
 assert updated['properties']['route_cp_0']==payload['feature']['properties']['route_cp_0']
 assert after['counts']['route']==1 and after['counts']['point']==1
 saved_text=registry.read_text()
 result,status=namespace['_i659_update_route'](payload)
 assert status==409 and not result['ok'] and registry.read_text()==saved_text
 rejected=json.loads(json.dumps(payload));rejected['expected_revision']=namespace['_i659_route_revision'](updated)
 rejected['feature']['geometry']['coordinates'][1]=[-118,94]
 result,status=namespace['_i659_update_route'](rejected)
 assert status==400 and registry.read_text()==saved_text,(status,result)
 rejected=json.loads(json.dumps(payload));rejected['expected_revision']=namespace['_i659_route_revision'](updated)
 rejected['object_id']='local-unrelated-object'
 result,status=namespace['_i659_update_route'](rejected)
 assert status==404 and registry.read_text()==saved_text,(status,result)
print('PASS: i659 in-place update, preserved IDs/other features, lossless geometry, stale edit rejection, invalid data rejection')
