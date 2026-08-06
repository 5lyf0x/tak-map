#!/usr/bin/env python3
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]
assert (ROOT/'VERSION').read_text().strip()=='1.3.0-i589'
server=(ROOT/'tak_dashboard.py').read_text(errors='replace')
for marker in ('# --- TAK Map i585 consolidated ATAK parity and authoritative civilian icon catalog ---','# --- TAK Map i589 automated Configure OTS and manifest-based unenrollment ---'):assert marker in server,marker
assert server.index('# --- TAK Map i589 automated Configure OTS')>server.index('# --- TAK Map i585 consolidated ATAK parity')
for text in ("_I589_VERSION = 'i589'","cfg['version'] = '1.3.0-i589'","ots_enrollment_manifest_i587.json","Disabled OTS login but keeps connection details.","Disconnects and completely removes OTS enrollment.","2FA Code (optional)","def _i589_decode_opaque_transport(payload):","/api/tak-map/local-users/q589"):assert text in server,text
assert 'Connect this TAK Map server' not in server
ui=re.search(r"_I589_CONFIGURE_OTS_UI\s*=\s*r'''(.*?)'''\n\n    def _i589_patch_html",server,re.S).group(1)
assert ui.count('input data-x=')>=15
assert 'name="takmap_' not in ui and 'id="ots589User' not in ui
assert "function transport(confirmText){return {q:[" in ui
assert "type=\"password\"" not in ui.split('<div class="autofill-sink"',1)[0]
assert '.ots589 .check{' in ui and 'font-size:.69rem' in ui and 'text-transform:none' in ui
assert '.ots589 .field-title{' in ui and 'text-transform:none' in ui
for forbidden in ('autocomplete="username"','autocomplete="current-password"','autocomplete="one-time-code"','autocomplete="new-password"'):
    # These values may exist only inside the isolated off-screen autofill sink.
    visible=ui.replace('<input tabindex="-1" type="text" name="username" autocomplete="username"><input tabindex="-1" type="password" name="password" autocomplete="current-password">','')
    assert forbidden not in visible,forbidden
control=(ROOT/'assets/tak-map-data-sync-i553.js').read_text();assert "const V='i589'" in control and 'automaticPollMs:5000' in control and 'minIntervalMs:4000' in control and 'TakMapDataSyncControlI589=api' in control
package=(ROOT/'assets/tak-map-package-i580.js').read_text();assert "const VERSION='i589';" in package and "const PACKAGE='1.3.0-i589';" in package
manifest=json.loads((ROOT/'assets/tak-map-deferred-i553.json').read_text());assert manifest['version']=='1.3.0-i589' and manifest['count']==len(manifest['scripts'])==104
resolver=(ROOT/'assets/tak-map-milstd2525c-i553.js').read_text();assert 'i589-civilian-pink-v1' in resolver
icon=(ROOT/'assets/tak-map-icon-registry-i572.js').read_text();assert '.svg?v=i589-civilian-pink-v1' in icon and 'atak-parity-friendly-civilian-' not in icon
startup=(ROOT/'assets/tak-map-startup-i553.js').read_text();assert 'tak-map-deferred-i553.json?v=1.3.0-i589' in startup
assert server.count("if __name__=='__main__':\n    main()")==1
print('i589 package identity, opaque Configure OTS field/request transport, sentence-case modal styling, manifest migration, stable publication/symbology baseline, cache paths, cadence, and runtime wiring passed')
