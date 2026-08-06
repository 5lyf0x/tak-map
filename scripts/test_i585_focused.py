#!/usr/bin/env python3
from pathlib import Path
import ast,json
ROOT=Path(__file__).resolve().parents[1]
assert (ROOT/'VERSION').read_text().strip()=='1.3.0-i585'
server=(ROOT/'tak_dashboard.py').read_text()
ast.parse(server,filename='tak_dashboard.py')
for marker in (
 '# --- TAK Map i584 ATAK icon parity hotfix hf1: live delayed read-back + transport visual authority ---',
 '# --- TAK Map i584 ATAK icon parity hotfix hf2: persistent exact-UID transport authority ---',
 '# --- TAK Map i584 authoritative single-root civilian icon catalog hotfix hf1 ---',
 '# --- TAK Map i584 authoritative civilian icon catalog hotfix hf2: canonical color and cache correction ---',
 '# --- TAK Map i585 consolidated ATAK parity and authoritative civilian icon catalog ---'):
 assert marker in server,marker
assert server.count("if __name__=='__main__':\n    main()")==1
assert server.index('# --- TAK Map i585 consolidated ATAK parity')>server.index('# --- TAK Map i584 authoritative civilian icon catalog hotfix hf2')
for needle in (
 "_I585_VERSION = 'i585'",
 "cfg['version'] = '1.3.0-i585'",
 "'exact_uid_transport_authority_persists': True",
 "'generic_mission_rows_cannot_downgrade_symbol': True",
 "'canonical_pink_civilian_files': 38",
 "'canonical_blue_utility_files': 4",
 "'alternate_civilian_artwork': False",
 "'data_sync_poll_seconds': 5",
 "'membership_refresh_seconds': 10",
 "'full_cot_enrichment_seconds': 20",
 "TAK_MAP_ITERATION = _I585_VERSION"):
 assert needle in server,needle
assert "Path(os.environ.get('TAK_MAP_MIL_ROOT', '/usr/share/tak-server-dash/mil2525'))" in server
control=(ROOT/'assets/tak-map-data-sync-i553.js').read_text()
assert "const V='i585'" in control and 'automaticPollMs:5000' in control and "'i585-automatic-poll'" in control
assert 'TakMapDataSyncControlI585=api' in control
package=(ROOT/'assets/tak-map-package-i580.js').read_text()
assert "const VERSION='i585';" in package and "const PACKAGE='1.3.0-i585';" in package
manifest=json.loads((ROOT/'assets/tak-map-deferred-i553.json').read_text())
assert manifest['version']=='1.3.0-i585' and manifest['count']==len(manifest['scripts'])==104
resolver=(ROOT/'assets/tak-map-milstd2525c-i553.js').read_text()
assert next(x['code'] for x in manifest['scripts'] if x.get('id')=='takMapMilStd2525CLoaderI553')==resolver
assert 'i585-civilian-pink-v1' in resolver
icon=(ROOT/'assets/tak-map-icon-registry-i572.js').read_text()
assert '.svg?v=i585-civilian-pink-v1' in icon and 'atak-parity-friendly-civilian-' not in icon
assert 'POINT DROPPER' not in icon
startup=(ROOT/'assets/tak-map-startup-i553.js').read_text()
assert 'tak-map-deferred-i553.json?v=1.3.0-i585' in startup
install=(ROOT/'install.sh').read_text()
assert 'rm -f "$APP_DIR/assets/mil2525/icons.json"' in install
assert 'rm -rf "$APP_DIR/assets/mil2525/svg"' in install
print('i585 focused package, persistent symbol authority, canonical civilian color catalog, cache paths, cadence, and runtime wiring passed')
