#!/usr/bin/env python3
from pathlib import Path
import json, runpy, tempfile, os
root=Path(__file__).resolve().parents[1]
assert (root/'VERSION').read_text().strip()=='1.4.0-i635'
start=(root/'assets/tak-map-startup-i553.js').read_text()
assert 'tak-map-deferred-i553.json?v=1.4.0-i635' in start
assert 'tak-map-core-i553.js?v=1.4.0-i635' in start
manifest=json.loads((root/'assets/tak-map-deferred-i553.json').read_text())
assert manifest.get('version')=='1.4.0-i635'
backend=(root/'tak_dashboard.py').read_text(); front=(root/'assets/tak-map-i635.js').read_text()
for token in [
    'tak_map_data_sync_associations_i635.json', '_i635_normalize_server_authoritative',
    'authoritative_membership_stamped_at_cot_acquisition', 'preexisting_non_destructive_backfill',
    'mission_delete_records_i635', 'multi_mission_delete', 'security_filter_before_backfill_and_merge',
    'takMapI635Loader', '/assets/runtime/tak-map-i635.js']:
    assert token in backend, token
assert "const V='i635'" in front
os.environ['TAK_DASHBOARD_DATA_DIR']=tempfile.mkdtemp(prefix='takmap-i635-')
ns=runpy.run_path(str(root/'tak_dashboard.py'),run_name='takmap_i635_test')
sess={'auth_mode':'ots-user','username':'alice'}
payload={
 'missions':[{'name':'Alpha'},{'name':'Bravo'},{'name':'Charlie'}],
 'mission_access_i599':[{'mission':'Alpha','unlocked':True,'locked':False},{'mission':'Bravo','unlocked':True,'locked':False},{'mission':'Charlie','unlocked':True,'locked':False}],
 'data_sync_reconciliation_i599':{'per_mission':{'Alpha':{'authoritative':True,'state':'ready'},'Bravo':{'authoritative':True,'state':'ready'},'Charlie':{'authoritative':True,'state':'ready'}}},
 'objects':[
   {'uid':'ABC','name':'One','mission':'Alpha','lat':1,'lon':2,'is_mission_object':True},
   {'uid':'ABC','name':'One','mission':'Bravo','lat':1,'lon':2,'is_mission_object':True},
   {'uid':'MAPPED','name':'Mapped','lat':3,'lon':4},
   {'uid':'OLDLOCAL','name':'Old local','lat':5,'lon':6},
   {'name':'Malformed'}],
 'mission_uids':[{'uid':'MAPPED','mission':'Charlie'}]
}
out=ns['_i635_normalize_server_authoritative'](payload,sess)
assert len(out['objects'])==3, out['objects']
by={o['uid']:o for o in out['objects']}
assert by['ABC']['mission_memberships']==['Alpha','Bravo']
assert len(by['ABC']['mission_delete_records_i635'])==2
assert by['MAPPED']['mission_memberships']==['Charlie']
assert by['OLDLOCAL']['association_scope']=='local_data' and by['OLDLOCAL']['local_data_association'] is True
assert out['data_sync_association_i635']['quarantined_unresolvable_count']==1
# Persisted migration backfill survives another response but cannot leak a now-inaccessible Mission.
p2={'missions':[{'name':'Alpha'},{'name':'Bravo'}], 'mission_access_i599':[{'mission':'Alpha','unlocked':True},{'mission':'Bravo','unlocked':True}], 'objects':[{'uid':'ABC','name':'One','lat':1,'lon':2}]}
o2=ns['_i635_normalize_server_authoritative'](p2,sess)
assert o2['objects'][0]['mission_memberships']==['Alpha','Bravo']
p3={'missions':[{'name':'Alpha'}], 'mission_access_i599':[{'mission':'Alpha','unlocked':True}], 'objects':[{'uid':'ABC','name':'One','lat':1,'lon':2}]}
o3=ns['_i635_normalize_server_authoritative'](p3,sess)
assert o3['objects'][0]['mission_memberships']==['Alpha']
# Acquisition boundary stamps Mission identity before downstream merge.
project=ns['_i599_project_cot']; g=project.__globals__
old_project=g['_i635_project_before']
g['_i635_project_before']=lambda acquired,cfg,mission: ({'ok':True},[{'uid':'ACQ1','name':'Acquired','lat':1,'lon':2}])
try:
    _,rows=project({}, {}, 'Mission Delta')
    assert rows[0]['mission_memberships']==['Mission Delta']
    assert rows[0]['mission_membership_authority_i635'].startswith('GET /Marti/api/missions')
finally:
    g['_i635_project_before']=old_project
# Multi-Mission delete invokes the inherited fully verified single-Mission pipeline once per membership.
delete=ns['_tak_data_sync_delete_record']; dg=delete.__globals__; old_delete=dg['_i635_delete_single_before']; calls=[]
def fake_delete(obj,host=''):
    calls.append(obj['mission_name'])
    return {'status':'deleted','mission_absence_confirmed':True,'object_id':obj.get('canonical_id')}
dg['_i635_delete_single_before']=fake_delete
obj={'canonical_id':'datasync:test','object_id':'test','uid':'ABC','mission_delete_records_i635':[{'mission':'Alpha','target':'uid','value':'ABC'},{'mission':'Bravo','target':'uid','value':'ABC'}]}
try:
    dr=delete(obj,'')
    assert dr['status']=='deleted' and calls==['Alpha','Bravo'] and dr['authoritative_readback_required'] is True
    calls.clear()
    def partial(obj,host=''):
        calls.append(obj['mission_name'])
        return {'status':'deleted','mission_absence_confirmed':True} if obj['mission_name']=='Alpha' else {'status':'failed','mission_absence_confirmed':False}
    dg['_i635_delete_single_before']=partial
    dr=delete(obj,'')
    assert dr['status']=='failed' and dr['partial'] is True and dr['deleted_missions']==['Alpha'] and dr['failed_missions']==['Bravo']
finally:
    dg['_i635_delete_single_before']=old_delete
assert 'takMapI635Loader' in ns['TAK_MAP_HTML'] and '1.4.0-i635' in ns['TAK_MAP_HTML']
assert ns['TAK_MAP_ITERATION']=='i635'
cfg=ns['tak_map_config']()
assert cfg['version']=='1.4.0-i635' and cfg['tak_map_iteration']=='i635'
assert cfg['server_authoritative_data_sync_i635']['multi_mission_delete'] is True
print('PASS i635 pre-existing association migration and multi-Mission delete contract')
