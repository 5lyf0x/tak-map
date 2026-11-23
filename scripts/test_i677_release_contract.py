"""i677 source/config/HTML wiring, fail-closed exact import ID and pane contract."""
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
assert (root/'VERSION').read_text().strip()=='1.4.0-i677'
src=(root/'assets/tak-map-route-editor-i654.js').read_text()
assert 'result.added' in src and 'savedImportId' in src
assert "item.name===safe+'.geojson'&&item.id" in src
assert "String(item?.id||'')===savedImportId" in src
assert 'sameRoute(stored)' in src
assert 'item.name===safe' not in src[src.index('// i677:'):src.index('const sameRoute=')].replace("item.name===safe+'.geojson'&&item.id",'')
stack=(root/'assets/tak-map-basemap-stack-i673.js').read_text()
assert "style.zIndex='220'" in stack
assert "state.map.removeLayer(baseLayer)" in stack
assert 'setOpacity' in stack and 'setZIndex' in stack
main=(root/'takmap.js').read_text()
assert 'takBasemapReliefI677' in main and "style.zIndex='230'" in main
install=(root/'install.sh').read_text()
assert 'assets/tak-map-basemap-stack-i673.js' in install and 'assets/tak-map-route-editor-i654.js' in install and 'tak_dashboard.py' in install
sys.path.insert(0,str(root))
import tak_dashboard as t
assert t.TAK_MAP_ITERATION=='i677' and t.tak_map_config()['version']=='1.4.0-i677'
assert 'tak-map-basemap-stack-i673.js?v=1.4.0-i677' in t.TAK_MAP_HTML
assert "pane:'takBasemapReliefI677'" in (root/'assets/tak-map-core-i553.js').read_text(), 'installed core relief overlay missing pane'
assert 'assets/tak-map-core-i553.js' in install
assert 'tak-map-route-editor-i654.js?v=1.4.0-i677' in t.TAK_MAP_HTML
assert 'iteration-chip">i676' not in t.TAK_MAP_HTML
print('PASS i677 version, shipped assets, runtime cache-bust, exact new import ID, managed z220, relief z230')
