#!/usr/bin/env python3
from pathlib import Path
import importlib.util
import tempfile

root = Path(__file__).resolve().parents[1]
server = (root / 'tak_dashboard.py').read_text(encoding='utf-8')
core = (root / 'assets' / 'tak-map-core-i553.js').read_text(encoding='utf-8')
startup = (root / 'assets' / 'tak-map-startup-i553.js').read_text(encoding='utf-8')
runtime = (root / 'assets' / 'tak-map-data-sync-access-i576.js').read_text(encoding='utf-8')
manifest = (root / 'assets' / 'tak-map-deferred-i553.json').read_text(encoding='utf-8')
install = (root / 'install.sh').read_text(encoding='utf-8')

assert (root / 'VERSION').read_text().strip() == '1.3.0-i576'
assert startup.count('v=1.3.0-i576') >= 3
assert 'v=1.3.0-i575' not in startup
assert '"version":"1.3.0-i576"' in manifest
assert 'TakMapMissionAccessI576.ingest(j)' in core
assert 'mission_access_i576' in core
assert 'data-mission-edit-i576' in core
assert 'truthy(m.passwordProtected)' in core
assert 'primeStatuses' in runtime
assert 'refreshAfterUnlock' in runtime
assert 'mission-access-discovery-i576' in runtime
assert 'mission-access-followup-i576' in runtime
assert "mission-unlocked-enrichment-i576" in runtime
assert 'postRenderDecorator:false' in runtime
assert 'tak-map-data-sync-access-i576.js' in install
assert 'raw_discovery_access_state' in server
assert 'authenticated_worker_session' in server
assert 'atak_created_point_fallback_replaced_after_unlock' in server

spec = importlib.util.spec_from_file_location('tak_i576_focused', root / 'tak_dashboard.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assert module.TAK_MAP_ITERATION == 'i576'
assert '/assets/runtime/tak-map-startup-i553.js?v=1.3.0-i576' in module.TAK_MAP_HTML
assert '/assets/runtime/tak-map-data-sync-access-i576.js?v=1.3.0-i576' in module.TAK_MAP_HTML
assert '/assets/runtime/tak-map-data-sync-access-i575.js' not in module.TAK_MAP_HTML

# Raw OTS passwordProtected values must create a locked authoritative row even
# when represented as a string and before any password has been stored.
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
    assert by_name['PROTECTED-MISSION']['unlocked'] is False
    assert by_name['OPEN-MISSION']['protected'] is False
    assert by_name['OPEN-MISSION']['known'] is True

    assert module._i572_store_password('PROTECTED-MISSION', 'secret', session).get('ok')
    unlocked = module._i576_access_status('PROTECTED-MISSION', session, True)
    assert unlocked['protected'] is True
    assert unlocked['unlocked'] is True
    assert unlocked['credential_configured'] is True

print('i576 focused Mission row and post-unlock enrichment checks passed')
