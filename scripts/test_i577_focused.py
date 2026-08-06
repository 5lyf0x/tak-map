#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import json
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
server = (root / 'tak_dashboard.py').read_text(encoding='utf-8')
core = (root / 'assets' / 'tak-map-core-i553.js').read_text(encoding='utf-8')
startup = (root / 'assets' / 'tak-map-startup-i553.js').read_text(encoding='utf-8')
runtime = (root / 'assets' / 'tak-map-data-sync-access-i576.js').read_text(encoding='utf-8')
context = (root / 'assets' / 'tak-map-context-sidebar-i572.js').read_text(encoding='utf-8')
manifest = json.loads((root / 'assets' / 'tak-map-deferred-i553.json').read_text(encoding='utf-8'))
geofence_file = (root / 'assets' / 'tak-map-geofencing-v491.js').read_text(encoding='utf-8')
install = (root / 'install.sh').read_text(encoding='utf-8')

assert (root / 'VERSION').read_text().strip() == '1.3.0-i577'
assert startup.count('v=1.3.0-i577') == 3, startup.count('v=1.3.0-i577')
assert 'i576-geofence-header-direct-final1' not in startup
assert 'i576-missionrow-final1' not in startup
assert manifest['version'] == '1.3.0-i577'
assert manifest['count'] == len(manifest['scripts'])
sidebar_perf = next(row['code'] for row in manifest['scripts'] if row.get('id') == 'takMapSidebarPerformanceLoaderV476')
iteration_guard = next(row['code'] for row in manifest['scripts'] if row.get('id') == 'takMapIterationGuardV519')
assert "const VERSION='i577';" in sidebar_perf
assert "const V='i577';" in iteration_guard

object_lifecycle = next(row['code'] for row in manifest['scripts'] if row.get('id') == 'takMapObjectLifecycleLoaderV486')
geofencing = next(row['code'] for row in manifest['scripts'] if row.get('id') == 'takMapGeofencingLoaderV491')

# The final deferred renderer, not only the earlier core renderer, owns the
# authoritative Mission row controls.
assert 'data-mission-edit-i576' in object_lifecycle
assert 'tak-mission-state-i576' in object_lifecycle
assert 'w.__takMapMissionRowStableI577' in object_lifecycle
assert "owner:'takMapObjectLifecycleLoaderV486'" in object_lifecycle
assert 'stableDomNodes:true' in object_lifecycle

# Stable reconciler preserves the actual control nodes instead of replacing the
# whole Mission row innerHTML.
assert '__takMapDsUpdateMissionRowFinalI576' in core
assert 'if(__takMapDsUpdateMissionRowFinalI576(oldEl,newEl))return;' in core
assert 'window.__takMapMissionRowStableI577' in core

# Partial snapshots cannot erase a direct protected/unlocked result.
assert 'function mergeStatus(previous, incoming' in runtime
assert "authority === 'direct' || authority === 'action'" in runtime
assert "remember(mission, row, 'snapshot')" in runtime
assert "remember(mission, body, 'direct')" in runtime
assert "remember(mission, body, 'action')" in runtime
assert "missionRowFinalPatch:'i577-missionrow-stable'" in runtime

# Direct Geofences implementation: no observer/decorator, full header toggle,
# switch exclusion, keyboard support, persistence and silver chevron.
assert geofence_file == geofencing
assert "const applyCollapsed=(closed,persist)=>" in geofencing
assert "head.addEventListener('click'" in geofencing
assert "head.addEventListener('keydown'" in geofencing
assert "target.closest('.tak-gf-switch-v491,#takGfMasterV491')" in geofencing
assert "localStorage.setItem('takMapPanelCollapsed:geofences'" in geofencing
assert '.tak-gf-card-head-v491{min-height:46px;cursor:pointer;' in geofencing
assert '.tak-gf-collapse-v491{border:0;background:transparent;color:#b8c3cb;' in geofencing
assert 'MutationObserver' not in geofencing

# The final late-loaded context runtime no longer injects the light-gray header
# hover override. Normal controls keep their own hover styling.
late_hover = '#sidebar .panel h2:hover,#sidebar .subgroup-title:hover,#sidebar .datasync-section-title:hover,#sidebar .local-section-title:hover{background:rgba(203,210,216,.08)!important}'
assert late_hover not in context
assert ':hover' in context

assert 'tak-map-data-sync-access-i576.js' in install
assert '# --- temporary i576 direct Geofences header final correction ---' not in server
assert '# --- TAK Map i577 stable Mission rows and direct Geofences header behavior ---' in server
assert server.count("if __name__=='__main__':\n    main()") == 1

spec = importlib.util.spec_from_file_location('tak_i577_focused', root / 'tak_dashboard.py')
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
assert module.TAK_MAP_ITERATION == 'i577'
config = module.tak_map_config()
assert config['version'] == '1.3.0-i577'
assert config['confirmed_ui_corrections_i577']['mission_row_stable_dom_nodes'] is True
assert config['confirmed_ui_corrections_i577']['geofence_full_header_toggle'] is True
assert config['confirmed_ui_corrections_i577']['initial_load_release_gate'] is True
assert '/assets/runtime/tak-map-startup-i553.js?v=1.3.0-i577' in module.TAK_MAP_HTML
assert '/assets/runtime/tak-map-data-sync-access-i576.js?v=1.3.0-i577' in module.TAK_MAP_HTML
assert '/assets/runtime/tak-map-context-sidebar-i572.js?v=1.3.0-i577' in module.TAK_MAP_HTML

# Server-side protected Mission state remains tied to the authenticated session.
with tempfile.TemporaryDirectory() as td:
    module._I575_MISSION_SECRET_ROOT = Path(td)
    session = {
        'auth_mode': 'ots-user',
        'username': 'darktek',
        'tak_uid': 'TAKMAP-USER-ABC',
        'profile': {'tak_uid': 'TAKMAP-USER-ABC', 'username': 'darktek'},
    }
    module._I575_REQUEST_CONTEXT.session = session
    rows = module._i576_access_rows([
        {'name': 'PROTECTED-MISSION', 'passwordProtected': 'true'},
        {'name': 'OPEN-MISSION', 'passwordProtected': False},
    ], session)
    by_name = {row['mission']: row for row in rows}
    assert by_name['PROTECTED-MISSION']['protected'] is True
    assert by_name['PROTECTED-MISSION']['locked'] is True
    assert module._i572_store_password('PROTECTED-MISSION', 'secret', session).get('ok')
    unlocked = module._i576_access_status('PROTECTED-MISSION', session, True)
    assert unlocked['unlocked'] is True
    assert unlocked['credential_configured'] is True

print('i577 focused Mission-row and Geofences checks passed')
