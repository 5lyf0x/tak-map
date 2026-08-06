#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import tempfile

root = Path(__file__).resolve().parents[1]
server = (root / 'tak_dashboard.py').read_text(encoding='utf-8')
core = (root / 'assets' / 'tak-map-core-i553.js').read_text(encoding='utf-8')
startup = (root / 'assets' / 'tak-map-startup-i553.js').read_text(encoding='utf-8')
runtime = (root / 'assets' / 'tak-map-data-sync-access-i575.js').read_text(encoding='utf-8')
install = (root / 'install.sh').read_text(encoding='utf-8')

# Root causes: old cache key and missing authenticated response/delete context.
assert startup.count('v=1.3.0-i575') >= 3
assert 'v=1.3.0-i570' not in startup
assert 'TakMapMissionAccessI575.ingest(j)' in core
assert 'mission_access_i575' in core
assert 'data-mission-edit-i575' in core
assert 'refreshStatePreserved:true' in runtime
assert "parsed.path in ('/api/tak-map/data-sync'" in server
assert "'/api/tak-map/object-delete'" in server
assert 'stable_user_identity_scope' in server
assert 'delete_preflight_before_fence' in server
assert 'migrated_from' in server and "'i572'" in server

# Package wiring and browser cache busting.
assert 'tak-map-data-sync-access-i575.js' in install
assert 'tak-map-data-sync-access-i575.js' in server
assert (root / 'VERSION').read_text().strip() == '1.3.0-i575'

spec = importlib.util.spec_from_file_location('tak_i575_focused', root / 'tak_dashboard.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assert module.TAK_MAP_ITERATION == 'i575'
assert '/assets/runtime/tak-map-startup-i553.js?v=1.3.0-i575' in module.TAK_MAP_HTML
assert '/assets/runtime/tak-map-data-sync-access-i575.js?v=1.3.0-i575' in module.TAK_MAP_HTML
assert '/assets/runtime/tak-map-data-sync-access-i574.js' not in module.TAK_MAP_HTML

# Stable password scope remains valid across auth-mode changes for the same TAK UID.
with tempfile.TemporaryDirectory() as td:
    module._I575_MISSION_SECRET_ROOT = Path(td)
    s1 = {'auth_mode':'ots-user','username':'darktek','tak_uid':'TAKMAP-USER-ABC',
          'profile':{'tak_uid':'TAKMAP-USER-ABC','username':'darktek'}}
    s2 = {'auth_mode':'ots-admin','username':'darktek','tak_uid':'TAKMAP-USER-ABC',
          'profile':{'tak_uid':'TAKMAP-USER-ABC','username':'darktek'}}
    module._I575_REQUEST_CONTEXT.session = s1
    assert module._i572_store_password('MISSION-X', 'secret').get('ok')
    module._I575_REQUEST_CONTEXT.session = s2
    loaded = module._i572_load_password('MISSION-X')
    assert loaded.get('ok') and loaded.get('password') == 'secret'

    module._i572_set_protected('MISSION-X', True, s2)
    state = {'snapshot':{'ok':True,'missions':[{'name':'MISSION-X','passwordProtected':True}],
                         'objects':[],'mission_uids':[],'mission_content':[]},
             'in_flight':False,'last_error':'','last_success_epoch':1,'generation':1,
             'endpoint_timings':[],'acquisition_summary':{}}
    payload = module._i568_response_payload(state)
    rows = payload.get('mission_access_i575') or []
    assert rows and rows[0].get('unlocked') is True

    original_token = module._i564_mission_token
    original_creator = module._i528_strict_creator
    module._i564_mission_token = lambda *a, **k: {'ok':False,'status':428,
        'mission_password_required':True,'error':'locked'}
    module._i528_strict_creator = lambda: {'ok':True,'uid':'TAKMAP-USER-ABC'}
    result = module._tak_data_sync_delete_record({'object_id':'x','mission_name':'MISSION-X',
        'mission_delete_target':'uid','mission_delete_value':'P1'})
    assert result.get('http_status') == 428
    assert result.get('mission_password_required') is True
    assert result.get('publication_attempted') is False
    module._i564_mission_token = original_token
    module._i528_strict_creator = original_creator

print('i575 focused Mission access and delete checks passed')
