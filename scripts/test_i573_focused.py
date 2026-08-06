#!/usr/bin/env python3
from pathlib import Path
import importlib.util, re, sys

root = Path(__file__).resolve().parents[1]
server = (root / 'tak_dashboard.py').read_text(encoding='utf-8')
runtime = (root / 'assets' / 'tak-map-data-sync-access-i573.js').read_text(encoding='utf-8')
install = (root / 'install.sh').read_text(encoding='utf-8')

assert "explicit protected-Mission credential management" in server
assert "/api/tak-map/data-sync-mission-access-i573" in server
assert "mission_access_i573" in server
assert "publication_attempted'] = False" in server
assert "automatic_prompt_removed': True" in server
assert "persistent_encrypted_server_storage': True" in server
assert 'tak-map-data-sync-access-i573.js' in install

assert 'tak-mission-edit-i573' in runtime
assert "'Unlocked' : 'Locked'" in runtime
assert 'Clear Stored Password' in runtime
assert 'legacyAutomaticPromptDisabled:true' in runtime
assert 'Mission is locked. Use Edit beside' in runtime
assert 'localStorage' not in runtime and 'sessionStorage' not in runtime
assert 'backdrop-filter' not in runtime
assert 'promptPassword' not in runtime
assert "ensureUnlocked: async mission" in runtime

spec = importlib.util.spec_from_file_location('tak_i573_focused', root / 'tak_dashboard.py')
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
cfg = module.tak_map_config()
assert cfg['version'] == '1.3.0-i573'
assert cfg['tak_map_iteration'] == 'i573'
assert module.TAK_MAP_ITERATION == 'i573'
assert cfg['protected_mission_access_i573']['explicit_mission_row_edit'] is True
assert cfg['protected_mission_access_i573']['locked_publication_blocked_before_cot'] is True
scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)', module.TAK_MAP_HTML, re.I)
assert '/assets/runtime/tak-map-data-sync-access-i573.js?v=1.3.0-i573' in scripts
assert not any('tak-map-data-sync-unlock-i572.js' in src for src in scripts)
assert scripts[-1] == '/assets/runtime/tak-map-data-sync-access-i573.js?v=1.3.0-i573'
print('i573 focused Mission credential workflow checks passed')
