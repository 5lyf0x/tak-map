#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
server = (root / 'tak_dashboard.py').read_text(encoding='utf-8')
core = (root / 'assets' / 'tak-map-core-i553.js').read_text(encoding='utf-8')
startup = (root / 'assets' / 'tak-map-startup-i553.js').read_text(encoding='utf-8')
runtime = (root / 'assets' / 'tak-map-data-sync-access-i576.js').read_text(encoding='utf-8')
context = (root / 'assets' / 'tak-map-context-sidebar-i572.js').read_text(encoding='utf-8')
resolver = (root / 'assets' / 'tak-map-milstd2525c-i553.js').read_text(encoding='utf-8')
manifest = json.loads((root / 'assets' / 'tak-map-deferred-i553.json').read_text(encoding='utf-8'))
geofence_file = (root / 'assets' / 'tak-map-geofencing-v491.js').read_text(encoding='utf-8')
install = (root / 'install.sh').read_text(encoding='utf-8')

assert (root / 'VERSION').read_text().strip() == '1.3.0-i579'
assert startup.count('v=1.3.0-i579') == 3, startup.count('v=1.3.0-i579')
assert manifest['version'] == '1.3.0-i579'
assert manifest['count'] == len(manifest['scripts']) == 104

sidebar_perf = next(row['code'] for row in manifest['scripts'] if row.get('id') == 'takMapSidebarPerformanceLoaderV476')
iteration_guard = next(row['code'] for row in manifest['scripts'] if row.get('id') == 'takMapIterationGuardV519')
object_lifecycle = next(row['code'] for row in manifest['scripts'] if row.get('id') == 'takMapObjectLifecycleLoaderV486')
geofencing = next(row['code'] for row in manifest['scripts'] if row.get('id') == 'takMapGeofencingLoaderV491')
deferred_resolver = next(row['code'] for row in manifest['scripts'] if row.get('id') == 'takMapMilStd2525CLoaderI553')

assert "const VERSION='i579';" in sidebar_perf
assert "const V='i579';" in iteration_guard
assert "package:'i579'" in object_lifecycle
assert deferred_resolver == resolver

# Exact canonical identity must be checked before reviewed aliases in both SIDC
# and CoT paths. The alias tables remain present as fallbacks.
assert 'function exactCanonicalResultForSidc(value, source)' in resolver
sidc_exact = resolver.index('const exactCanonical = exactCanonicalResultForSidc(sidc, source);')
sidc_alias = resolver.index('REVIEWED_ALIASES_I553.by_sidc[sidc]', sidc_exact)
assert sidc_exact < sidc_alias
cot_exact = resolver.index("const exactCanonical = exactCanonicalResultForSidc(sidc, source + '-sidc');")
cot_alias = resolver.index('REVIEWED_ALIASES_I553.by_cot_type[cotType]', cot_exact)
assert cot_exact < cot_alias
assert 'canonicalPrecedenceI579: true' in resolver
assert 'exactCanonicalPrecedenceI579: true' in resolver
assert '(reviewedType.reviewedAlias || reviewedType.canonicalPrecedenceI579)' in resolver
assert 'friendly-ground-equipment-radar-vehicle' in resolver  # aliases were not deleted

# The all-collision executable regression test is part of the package.
collision_test = root / 'scripts' / 'test_icon_resolver_precedence_i579.js'
assert collision_test.is_file()
result = subprocess.run(
    ['node', str(collision_test)], cwd=root, check=True,
    text=True, capture_output=True,
)
summary = json.loads(result.stdout)
assert summary['exact_sidc_collisions_checked'] == 92
assert summary['exact_cot_collisions_checked'] == 92
assert summary['generic_sensor_file'] == 'friendly-ground-equipment-sensor.svg'
assert summary['specific_radar_file'] == 'friendly-ground-equipment-radar.svg'
assert summary['standalone_deferred_parity'] is True

# Preserve the validated i577/i578 controls and interaction behavior.
assert 'data-mission-edit-i576' in object_lifecycle
assert 'tak-mission-state-i576' in object_lifecycle
assert 'w.__takMapMissionRowStableI577' in object_lifecycle
assert "owner:'takMapObjectLifecycleLoaderV486'" in object_lifecycle
assert 'stableDomNodes:true' in object_lifecycle
assert '__takMapDsUpdateMissionRowFinalI576' in core
assert 'if(__takMapDsUpdateMissionRowFinalI576(oldEl,newEl))return;' in core
assert 'window.__takMapMissionRowStableI577' in core
assert "package:'i579'" in core

assert 'function mergeStatus(previous, incoming' in runtime
assert "authority === 'direct' || authority === 'action'" in runtime
assert "missionRowFinalPatch:'i577-missionrow-stable'" in runtime
assert "packageVersion:'i579'" in runtime

assert geofence_file == geofencing
assert "head.addEventListener('click'" in geofencing
assert "head.addEventListener('keydown'" in geofencing
assert "target.closest('.tak-gf-switch-v491,#takGfMasterV491')" in geofencing
assert 'MutationObserver' not in geofencing
assert '#sidebar .row:hover' not in context
assert '#sidebar .layer-button:hover,#sidebar button:hover,#sidebar .local-data-row:hover' in context

assert 'tak-map-data-sync-access-i576.js' in install
assert 'active i579 package route' in install
assert '# --- TAK Map i577 stable Mission rows and direct Geofences header behavior ---' in server
assert '# --- TAK Map i578 stable non-interactive sidebar row hover behavior ---' in server
assert '# --- TAK Map i579 exact canonical icon resolver precedence ---' in server
assert server.count("if __name__=='__main__':\n    main()") == 1

spec = importlib.util.spec_from_file_location('tak_i579_focused', root / 'tak_dashboard.py')
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
assert module.TAK_MAP_ITERATION == 'i579'
config = module.tak_map_config()
assert config['version'] == '1.3.0-i579'
assert config['confirmed_ui_corrections_i577']['mission_row_stable_dom_nodes'] is True
assert config['confirmed_ui_corrections_i578']['generic_sidebar_row_hover_removed'] is True
icon_cfg = config['icon_resolver_precedence_i579']
assert icon_cfg['exact_canonical_sidc_before_reviewed_alias'] is True
assert icon_cfg['cot_type_canonical_sidc_before_reviewed_alias'] is True
assert icon_cfg['reviewed_alias_fallback_preserved'] is True
assert icon_cfg['exact_collision_count'] == 92
assert icon_cfg['duplicate_sidc_catalog_unchanged'] is True
assert icon_cfg['initial_load_release_gate'] is True
assert config['startup_architecture_i579']['milstd2525c_resolver_cache_identity'] == '1.3.0-i579'
assert '/assets/runtime/tak-map-startup-i553.js?v=1.3.0-i579' in module.TAK_MAP_HTML
assert '/assets/runtime/tak-map-data-sync-access-i576.js?v=1.3.0-i579' in module.TAK_MAP_HTML
assert '/assets/runtime/tak-map-context-sidebar-i572.js?v=1.3.0-i579' in module.TAK_MAP_HTML

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

print('i579 focused icon precedence, Mission-row, Geofences, and sidebar checks passed')
