#!/usr/bin/env python3
from pathlib import Path
import ast, json
ROOT=Path(__file__).resolve().parents[1]
assert (ROOT/'VERSION').read_text().strip()=='1.3.0-i587'
server=(ROOT/'tak_dashboard.py').read_text()
ast.parse(server,filename='tak_dashboard.py')
for marker in (
 '# --- TAK Map i585 consolidated ATAK parity and authoritative civilian icon catalog ---',
 '# --- TAK Map i587 automated Configure OTS and manifest-based unenrollment ---'):
 assert marker in server, marker
assert server.count("if __name__=='__main__':\n    main()")==1
assert server.index('# --- TAK Map i587 automated Configure OTS')>server.index('# --- TAK Map i585 consolidated ATAK parity')
for needle in (
 "_I587_VERSION = 'i587'",
 "cfg['version'] = '1.3.0-i587'",
 "'minimum_initial_fields': ['server_address', 'administrator_username', 'administrator_password']",
 "'full_functionality_defaults_checked': True",
 "'manifest_scoped_cleanup_only': True",
 "'remote_revocation_when_advertised': True",
 "'passwords_never_persisted': True",
 "'browser_autofill_suppressed': True",
 "'password_manager_opt_out_attributes': True",
 "'sensitive_fields_readonly_until_user_interaction': True",
 "'request_secrets_cleared_after_each_request': True",
 "'modal_credentials_cleared_on_close': True",
 "_I587_LEGACY_ENROLLMENT_MANIFEST_FILES = (DATA_DIR / 'ots_enrollment_manifest_i586.json',)",
 "Disabled OTS login but keeps connection details.",
 "Disconnects and completely removes OTS enrollment.",
 "TAK_MAP_ITERATION = _I587_VERSION"):
 assert needle in server,needle
assert 'atakatak' not in server[server.index('# --- TAK Map i587 automated Configure OTS'):]
assert 'autocomplete="username"' not in server[server.index('# --- TAK Map i587 automated Configure OTS'):]
assert 'autocomplete="current-password"' not in server[server.index('# --- TAK Map i587 automated Configure OTS'):]
assert 'autocomplete="one-time-code"' not in server[server.index('# --- TAK Map i587 automated Configure OTS'):]
assert 'autocomplete="new-password"' not in server[server.index('# --- TAK Map i587 automated Configure OTS'):]
assert server.count('data-i587-no-autofill="true"') >= 15
assert "function clearRequestSecrets(){clearValues(['ots587Pass','ots587Otp','ots587TrustPass'])}" in server
assert "function clearModalCredentials(){clearValues(['ots587User','ots587Pass','ots587Otp','ots587TrustPass','ots587LocalUser','ots587LocalCallsign','ots587LocalPassword'])}" in server
control=(ROOT/'assets/tak-map-data-sync-i553.js').read_text()
assert "const V='i587'" in control and 'automaticPollMs:5000' in control and "'i587-automatic-poll'" in control
assert 'TakMapDataSyncControlI587=api' in control
package=(ROOT/'assets/tak-map-package-i580.js').read_text()
assert "const VERSION='i587';" in package and "const PACKAGE='1.3.0-i587';" in package
assert 'TakMapPackageI587=' in package
manifest=json.loads((ROOT/'assets/tak-map-deferred-i553.json').read_text())
assert manifest['version']=='1.3.0-i587' and manifest['count']==len(manifest['scripts'])==104
resolver=(ROOT/'assets/tak-map-milstd2525c-i553.js').read_text()
assert next(x['code'] for x in manifest['scripts'] if x.get('id')=='takMapMilStd2525CLoaderI553')==resolver
assert 'i587-civilian-pink-v1' in resolver
icon=(ROOT/'assets/tak-map-icon-registry-i572.js').read_text()
assert '.svg?v=i587-civilian-pink-v1' in icon and 'atak-parity-friendly-civilian-' not in icon
assert 'POINT DROPPER' not in icon
startup=(ROOT/'assets/tak-map-startup-i553.js').read_text()
assert 'tak-map-deferred-i553.json?v=1.3.0-i587' in startup
install=(ROOT/'install.sh').read_text()
assert 'mission_unlock_users_i575' in install and 'data_sync_transport_authority_i584_hf2' in install and 'ots_trust' in install
assert 'rm -f "$APP_DIR/assets/mil2525/icons.json"' in install
assert 'rm -rf "$APP_DIR/assets/mil2525/svg"' in install
print('i587 package identity, Configure OTS autofill suppression, manifest migration/Unenroll, i585 baseline, cache paths, cadence, and runtime wiring passed')
