"""i675 source/release contract for route save, styling, and non-destructive install."""
import contextlib
import io
import re
import sys
import runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
assert (ROOT/'VERSION').read_text().strip()=='1.4.0-i675'
with contextlib.redirect_stdout(io.StringIO()):
    ns=runpy.run_path(str(ROOT/'tak_dashboard.py'),run_name='takmap_i675_contract')
assert ns['tak_map_config']()['version']=='1.4.0-i675'
assert ns['TAK_MAP_ITERATION']=='i675'
assert ns['TAK_MAP_HTML'].count('tak-map-routing-dropdown-i675.js')==1
assert 'iteration-chip">i675</span>' in ns['TAK_MAP_HTML']
js=(ROOT/'assets/tak-map-routing-dropdown-i675.js').read_text()
assert 'width:155px' in js and 'height:25px' in js
assert 'r.top+18' in js and 'W.innerWidth-r.right+7' in js
assert "routeActive()" in js and 'currentRouteIsDirty()' in js
assert 'tak-route-data-prefix-i675' in js and 'tak-route-data-chevron-i675' in js
assert 'tak-route-data-option-i675' in js
assert "'/api/tak-map/routing/activate-i675'" in js
assert 'tak-soft-pill-i675' in js and '--tak-soft-pill-pct' in js
assert '.ms-chip.none' in js and '.ms-chip.online' in js
saved=(ROOT/'assets/tak-map-route-editor-i654.js').read_text()
assert 'let geometryVariance=!!saved&&!sameRoute(saved);' in saved
assert 'geometryVariance=geometryVariance||!sameRoute(checkRoute);' in saved
assert 'Route saved. Stored geometry was normalized' in saved
assert 'takmap_routing_dataset_id_i675' in saved
assert 'length_m:meters,length_km:meters/1000,length_miles:meters/METERS_PER_MILE' in saved
mvum=(ROOT/'assets/tak-map-mvum-i673.js').read_text()
assert 'bar.insertBefore(button' in mvum and 'v233UndoRoute' in mvum
inst=(ROOT/'install.sh').read_text()
for required in ('install -m 0644 tak_map_graph_switch_i675.py',
                 'install -m 0644 assets/tak-map-routing-dropdown-i675.js',
                 'route-graph-restart-i675',
                 'systemctl restart tak-map-valhalla.service',
                 'tak-map-routing-dropdown-i675.js \\\n'):
    assert required in inst,required
assert 'rm -rf "$DATA_DIR/ndm"' not in inst
assert (ROOT/'tak_map_graph_switch_i675.py').is_file()
print('PASS: i675 version, HUD, route-save nonblocking, styling, MVUM order, safe installer/runtime gate')
