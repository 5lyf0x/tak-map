#!/usr/bin/env python3
from pathlib import Path
import copy, importlib.util, json, sys

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('tak_i567_route_order',ROOT/'tak_dashboard.py')
m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m; spec.loader.exec_module(m)

PATH='db450cbe-2fec-47fb-bd2b-ba2db89b035e/Incident Management/water point.png'
MISSION='I567-ROUTE-ORDER'
CUSTOM_UID='ATAK-WATER-POINT-I567'
SOF_UID='ATAK-SOF-I567'
raw_custom={
    'data':CUSTOM_UID,'mission_name':MISSION,'timestamp':'2026-07-27T12:00:00Z',
    'details':{'type':'a-n-G','callsign':'Water Point','iconsetPath':PATH,
               'location':{'lat':34.1,'lon':-117.2}},
}
custom_marker=m._normalize_tak_marker(raw_custom,'mission_uids','datasync')
assert custom_marker and custom_marker.get('uid')==CUSTOM_UID,custom_marker
# Simulate the old final object after legacy symbol fallback so the final authority
# must recover the raw custom path without changing object count or raw rows.
custom_marker.update({'cot_type':'a-n-G','sidc':'SNGP-----------','mil2525_file':'neutral-ground-generic.svg','mil2525_name':'neutral-ground-generic'})
objects=[custom_marker,{
    'uid':SOF_UID,'callsign':'DS-P09','lat':34.2,'lon':-117.3,'cot_type':'a-f-F-N-S','type':'a-f-F-N-S'
}]
for idx in range(7):
    objects.append({'uid':f'VISIBLE-{idx}','callsign':f'DS-X{idx}','lat':34.3+idx/1000,'lon':-117.4-idx/1000,
                    'cot_type':'a-f-G-U-C-I','type':'a-f-G-U-C-I'})
base={'ok':True,'objects':objects,'mission_uids':[raw_custom],'mission_name':MISSION}
raw_before=json.dumps(base['mission_uids'],sort_keys=True,separators=(',',':'))
uid_order=[m._i566_object_uid(row) for row in base['objects']]

# i567 must have removed both pre-augmentation i566 wrappers.
assert m.tak_map_data_sync is m._i566_data_sync_before
assert m._tak_fresh_data_sync_result is m._i566_fresh_before
assert m._i567_augment_base is m._i566_augment_before

out1=m._i512_augment_data_sync(copy.deepcopy(base),{}, {'username':'tester','auth_mode':'local'})
out2=m._i512_augment_data_sync(copy.deepcopy(base),{}, {'username':'tester','auth_mode':'local'})
assert len(out1.get('objects') or [])==len(objects)==9,out1
assert len(out2.get('objects') or [])==9,out2
assert [m._i566_object_uid(row) for row in out1['objects']]==uid_order
assert json.dumps(out1.get('mission_uids'),sort_keys=True,separators=(',',':'))==raw_before
assert json.dumps(out2.get('mission_uids'),sort_keys=True,separators=(',',':'))==raw_before

water=next(row for row in out1['objects'] if m._i566_object_uid(row)==CUSTOM_UID.casefold())
assert water.get('iconsetPath')==PATH,water
assert water.get('data_sync_current_iconset_path_i567')==PATH,water
for source in (water,water.get('properties') or {}):
    for key in ('sidc','SIDC','mil2525_file','mil2525_name','mil2525_label'):
        assert not source.get(key),(key,source.get(key),source)
sof=next(row for row in out1['objects'] if m._i566_object_uid(row)==SOF_UID.casefold())
assert sof.get('mil2525_file')=='friendly-ground-unit-special-forces.svg',sof
assert sof.get('sidc')=='SFGPUCCIS------',sof

# A defensive repeated final pass must remain idempotent, preserve count, and never
# create properties.properties nesting or response-size growth.
def has_nested_properties(value):
    if isinstance(value,dict):
        props=value.get('properties')
        if isinstance(props,dict) and isinstance(props.get('properties'),dict): return True
        return any(has_nested_properties(v) for v in value.values())
    if isinstance(value,list): return any(has_nested_properties(v) for v in value)
    return False
again=m._i567_finalize_payload(out1)
assert len(again.get('objects') or [])==9
assert not has_nested_properties(out1),out1
assert not has_nested_properties(again),again
size1=len(json.dumps(out1,sort_keys=True,separators=(',',':')))
size2=len(json.dumps(again,sort_keys=True,separators=(',',':')))
assert size2 <= size1 + 512,(size1,size2)
assert again['custom_icon_resolution_i567']['object_count_preserved'] is True
print('i567 final Data Sync ordering, object preservation, raw-row immutability, and idempotence checks passed')
