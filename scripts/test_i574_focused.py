#!/usr/bin/env python3
from pathlib import Path
import importlib.util

root = Path(__file__).resolve().parents[1]
server = (root / 'tak_dashboard.py').read_text(encoding='utf-8')
core = (root / 'assets' / 'tak-map-core-i553.js').read_text(encoding='utf-8')
runtime = (root / 'assets' / 'tak-map-data-sync-access-i574.js').read_text(encoding='utf-8')
install = (root / 'install.sh').read_text(encoding='utf-8')

# Root cause correction: controls are in the authoritative renderer, not an after-render decorator.
assert 'tak-mission-card-i574' in core
assert 'data-mission-key=' in core
assert 'data-mission-edit-i574' in core
assert 'TakMapMissionAccessI574.peek' in core
assert "if(el.dataset&&el.dataset.missionKey)return 'mission|'" in core
assert 'decorateMissionRows' not in runtime
assert 'installRenderWrapper' not in runtime
assert 'MutationObserver' not in runtime

# Approved Mission-row geometry and dialog wording.
assert 'font-size:10px!important' in runtime
assert 'height:24px!important' in runtime
assert '<h2>Mission Password</h2>' in runtime
assert '>Clear Password</button>' in runtime
assert '>Cancel</button>' in runtime
assert '>Save Password</button>' in runtime
assert 'grid-template-columns:repeat(3,minmax(0,1fr))' in runtime
assert 'height:36px' in runtime

# Queued sidebar visual corrections.
assert 'scrollbar-color:#7f8d97' in runtime
assert '.sidebar .panel>h2:hover' in runtime
assert '#adsbMenuHostV316 .adsb-stepper-buttons button' in runtime
assert 'dark-silver' in server

# Package/server wiring.
assert 'tak-map-data-sync-access-i574.js' in install
assert 'tak-map-data-sync-access-i574.js' in server
assert "TAK_MAP_ITERATION = 'i574'" in server
assert (root / 'VERSION').read_text().strip() == '1.3.0-i574'

spec = importlib.util.spec_from_file_location('tak_i574_focused', root / 'tak_dashboard.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
cfg = module.tak_map_config()
assert cfg['version'] == '1.3.0-i574'
assert cfg['tak_map_iteration'] == 'i574'
assert module.TAK_MAP_ITERATION == 'i574'
assert cfg['protected_mission_access_i574']['authoritative_mission_row_html'] is True
assert cfg['protected_mission_access_i574']['post_render_decoration_removed'] is True
assert cfg['sidebar_visual_polish_i574']['sidebar_scrollbar'] == 'silver'
assert cfg['sidebar_visual_polish_i574']['adsb_stepper_color'] == 'dark-silver'
html = module.TAK_MAP_HTML
assert '/assets/runtime/tak-map-data-sync-access-i574.js?v=1.3.0-i574' in html
assert '/assets/runtime/tak-map-data-sync-access-i573.js' not in html
print('i574 focused Mission-row and sidebar UI checks passed')
