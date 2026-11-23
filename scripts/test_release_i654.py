#!/usr/bin/env python3
"""i654 release identity, installed runtime, unchanged Valhalla safety gates."""
import contextlib, io, json, runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
assert (ROOT/'VERSION').read_text().strip()=='1.4.0-i659'
with contextlib.redirect_stdout(io.StringIO()):
    mod=runpy.run_path(str(ROOT/'tak_dashboard.py'), run_name='takmap_i654_release_contract')
assert mod['TAK_MAP_ITERATION']=='i659'
assert mod['tak_map_config']()['version']=='1.4.0-i659'
html=mod['TAK_MAP_HTML']
assert html.count('id="takMapRouteEditorI654"')==1
assert '/assets/runtime/tak-map-route-editor-i654.js?v=1.4.0-i659' in html
assert '/api/tak-map/routing/resolve' in (ROOT/'tak_dashboard.py').read_text()
assert '/api/tak-map/routing/snap' in (ROOT/'tak_dashboard.py').read_text()
inst=(ROOT/'install.sh').read_text()
assert 'install -m 0644 assets/tak-map-route-editor-i654.js "$APP_DIR/assets/tak-map-route-editor-i654.js"' in inst
assert 'tak-map-route-editor-i654.js?install-check=i659' in inst
assert '  tak-map-route-editor-i654.js \
' in inst
assert 'systemctl enable tak-map-valhalla.service' in inst
assert (ROOT/'assets/tak-map-route-editor-i654.js').is_file()
manifest=json.loads((ROOT/'assets/tak-map-deferred-i553.json').read_text())
assert manifest['version']=='1.4.0-i659' and manifest['count']==len(manifest['scripts'])
print('PASS: i654 release identity, route editor deployment, Valhalla conditional autostart enabled')
