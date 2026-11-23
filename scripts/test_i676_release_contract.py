"""Full source release contract for TAK Map i676."""
from pathlib import Path
import contextlib,io,runpy,sys,warnings
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
assert (root/'VERSION').read_text().strip()=='1.4.0-i676'
with contextlib.redirect_stdout(io.StringIO()), warnings.catch_warnings():
    warnings.simplefilter('ignore',SyntaxWarning)
    ns=runpy.run_path(str(root/'tak_dashboard.py'),run_name='takmap_i676_release_contract')
assert ns['TAK_MAP_ITERATION']=='i676',ns['TAK_MAP_ITERATION']
assert ns['tak_map_config']()['version']=='1.4.0-i676'
assert 'iteration-chip">i676</span>' in ns['TAK_MAP_HTML']
assert 'tak-map-routing-dropdown-i675.js?v=1.4.0-i676' in ns['TAK_MAP_HTML']
hud=(root/'assets/tak-map-routing-dropdown-i675.js').read_text()
assert 'POSITION_KEY' in hud and 'localStorage.setItem(POSITION_KEY' in hud
assert 'takRouteDataGripI676' in hud and 'Reset Position' in hud
assert 'width:155px;height:25px' in hud
assert "host.style.display=on?'flex':'none'" in hud
assert '/api/tak-map/routing/activate-i675' in hud
route=(root/'assets/tak-map-route-editor-i654.js').read_text()
assert 'function buildSaveGeometry()' in route
assert 'route_fallback_leg_indices:prepared.fallbackIndices.join' in route
assert "const prepared=buildSaveGeometry()" in route
assert 'every((p,i)=>' in route and 'checkRoute' in route
assert 'route_control_point_count:controlCount' in route
assert 'function placeRouteMode()' in route and 'selector.style.top=' in route
assert "getResolvedSaveState().ready" in ns['_I500_ROUTE_UI'] # validity, not all routed readiness
assert "Road route not ready. Resolve disconnected legs" not in ns['_I500_ROUTE_UI']
assert '.tak-route-connector-note-i676' in ns['_I500_ROUTE_UI']
installer=(root/'install.sh').read_text()
for text in ('assets/tak-map-route-editor-i654.js','assets/tak-map-routing-dropdown-i675.js','tak_map_graph_switch_i675.py'):
    assert text in installer
assert 'rm -rf "$DATA_DIR/ndm"' not in installer
print('PASS: i676 identity, route geometry, draggable persisted HUD, mode placement, retained graph switching and installer')
