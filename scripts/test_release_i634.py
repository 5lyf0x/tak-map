#!/usr/bin/env python3
from pathlib import Path
import json,re,sys,runpy,tempfile,os
root=Path(__file__).resolve().parents[1]
assert (root/'VERSION').read_text().strip()=='1.4.0-i634'
js=(root/'assets/tak-map-gateway-data-v491.js').read_text()
assert "width:14,height:14,variant:'law'" in js and "width:10,height:11,variant:'civil'" in js
assert '.gateway-data-marker-v491.gateway-data-ais-native-v523 img{display:block;max-width:none;max-height:none;transform:none!important;transform-origin:center!important;filter:none!important}' in js
assert '.gateway-data-selected-i614.gateway-data-ais-native-v523 img{filter:none!important}' in js
m=json.loads((root/'assets/tak-map-deferred-i553.json').read_text())
g=[x for x in m['scripts'] if x['id']=='takMapGatewayDataLoaderV476']
assert len(g)==1 and g[0]['code']==js
start=(root/'assets/tak-map-startup-i553.js').read_text(); assert 'tak-map-deferred-i553.json?v=1.4.0-i634' in start
backend=(root/'tak_dashboard.py').read_text(); front=(root/'assets/tak-map-i634.js').read_text()
for token in ['tak_map_card_states_i634.json','_i634_normalize_server_authoritative','security_filter_before_canonical_merge','/api/tak-map/card-states','takMapI634Loader']:
    assert token in backend, token
for token in ['takmap.geofence.master','takmap.adsb.localDisabled','takmap.dataSync.disabled','takmap.gatewayData.master','takMapSatellitePrefsV409','Search all Mission objects']:
    assert token in front, token
# Import module under isolated data dir and unit-test normalization + per-user card persistence.
os.environ['TAK_DASHBOARD_DATA_DIR']=tempfile.mkdtemp(prefix='takmap-i634-')
ns=runpy.run_path(str(root/'tak_dashboard.py'),run_name='takmap_i634_test')
payload={'objects':[{'uid':'ABC','name':'One','mission':'Alpha'},{'uid':'ABC','name':'One','mission':'Bravo'},{'uid':'ORPHAN','name':'Bad'}], 'mission_uids':[]}
out=ns['_i634_normalize_server_authoritative'](payload)
assert len(out['objects'])==1, out['objects']
assert out['objects'][0]['mission_memberships']==['Alpha','Bravo']
assert out['data_sync_association_i634']['quarantined_unassociated_objects']==1
s1={'auth_mode':'ots-user','username':'alice'}; s2={'auth_mode':'ots-user','username':'bob'}
ns['_i634_save_card_state'](s1,'geofencing',False); ns['_i634_save_card_state'](s2,'geofencing',True)
assert ns['_i634_card_states_for'](s1)['geofencing'] is False
assert ns['_i634_card_states_for'](s2)['geofencing'] is True
print('PASS i634 focused release contract')
