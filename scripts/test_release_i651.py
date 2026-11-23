#!/usr/bin/env python3
"""TAK Map i651 B0–B3 runtime, installer and version contract."""
import contextlib,io,os,runpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
assert (ROOT/'VERSION').read_text().strip()=='1.4.0-i659'
s=(ROOT/'install.sh').read_text()
for token in ('scripts/install-valhalla-i651.py','ndm_packages_i651.py','ndm_valhalla_i651.py','ndm_ctl_i651.py','tak-map-valhalla.service',
              'systemctl enable tak-map-valhalla.service','Valhalla 3.6.3 auto-start enabled'):
    assert token in s,token
assert s.index('python3 scripts/install-valhalla-i651.py')<s.index('cp tak_dashboard.py "$APP_DIR/tak_dashboard.py"')
with contextlib.redirect_stdout(io.StringIO()):
    ns=runpy.run_path(str(ROOT/'tak_dashboard.py'),run_name='release_i651_contract')
assert ns['TAK_MAP_ITERATION']=='i659'
assert ns['tak_map_config']()['version']=='1.4.0-i659'
assert ns['tak_map_config']()['ndm_integration']['router']=='systemd-autostart-with-config'
assert 'mapCertSetupBtn' not in '' or ns['TAK_MAP_HTML'] # inherited, not modified
for attr in ('_i651_get','_i651_post','_i651_delete'):
    assert callable(ns[attr]),attr
assert 'takMapCertSetupLoaderI650' in ns['TAK_MAP_HTML']
assert 'takMapLiveSearchLoaderI650' in ns['TAK_MAP_HTML']
assert 'tak-map-live-search-i650.js?v=1.4.0-i659' in ns['TAK_MAP_HTML']
assert 'i659' in ns['TAK_MAP_LOGIN_HTML']
for config in ('nginx/tak-map-https-9444.conf','nginx/tak-map-https-9444.conf.example'):
    conf=(ROOT/config).read_text()
    assert 'location = /api/tak-map/ndm/import' in conf
    assert 'client_max_body_size 4096M;' in conf
    assert 'client_max_body_size 400M;' in conf
    assert 'proxy_set_header Host $http_host' in conf
manifest=json.loads((ROOT/'assets/tak-map-deferred-i553.json').read_text())
assert manifest['version']=='1.4.0-i659' and manifest['count']==len(manifest['scripts'])
print('PASS: i651 identity, NDM endpoints, Valhalla installer/service, retained i650 assets')
