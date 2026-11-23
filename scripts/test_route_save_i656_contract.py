#!/usr/bin/env python3
"""i657: install and source save geometry contract."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
js=(root/'assets/tak-map-route-editor-i654.js').read_text()
assert 'S.saveResolvedRoute=saveResolvedRoute' in js
assert 'S.getResolvedSaveState=resolvedSaveState' in js
assert 'W.TakMapRouteUiV500.open' in js
assert "const coordinates=shape.map(p=>[Number(p.lng),Number(p.lat)])" in js
assert "fetch('/api/tak-map/import'" in js
assert "takmap_route_editor:'resolved-line-v1'" in js
assert 's.points=all' not in js
installer=(root/'install.sh').read_text()
assert 'install -m 0644 assets/tak-map-route-editor-i654.js' in installer
assert 'tak-map-route-editor-i654.js?install-check=i659' in installer
assert (root/'VERSION').read_text().strip()=='1.4.0-i659'
print('PASS: i657 delegated resolved-route save, installer runtime asset, and version identity')
