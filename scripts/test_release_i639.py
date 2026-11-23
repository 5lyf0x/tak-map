#!/usr/bin/env python3
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]
assert (ROOT/'VERSION').read_text().strip()=='1.4.0-i639'
ctx=(ROOT/'assets'/'tak-map-context-sidebar-i572.js').read_text()
pkg=(ROOT/'assets'/'tak-map-package-i580.js').read_text()
install=(ROOT/'install.sh').read_text()
dash=(ROOT/'tak_dashboard.py').read_text()
assert "const VERSION = 'i639'" in ctx
for token in [
    'inPlaceShapeEditI639:true','geometryHandlesI639:true','dynamicSegmentLabelsI639:true',
    'silverShapeButtonsI639:true','centerLabelI639:true','panelWidthHeightRemovedI639:true',
    'tak-shape-edit-toggle-i639','tak-shape-vector-i639','tak-shape-distance-i639',
    "label.textContent='Center'",'refreshDistanceLabelsI639','rectangleDragI639','setEllipseGeometryI639',
    "setHeader('Edit Shape','')",
]: assert token in ctx, token
# Width/Height remain recognized only as legacy rows to remove; the new geometry output does not emit them.
geom=ctx[ctx.index('function geometryRows'):ctx.index('function applySourcePresentation')]
assert "push('Width'" not in geom and "push('Height'" not in geom, geom[:500]
assert "push('Area'" in geom and "push('Perimeter'" in geom
assert 'background:rgba(126,39,36' not in ctx[ctx.index('/* i639 Shape editor'):ctx.index('/* i572 source-safe contextual deletion states.')]
assert "const VERSION='i639'" in pkg and "const PACKAGE='1.4.0-i639'" in pkg and 'compactContextWidth:320' in pkg and 'contextScrollbarHidden:true' in pkg
assert 'install -m 0644 assets/tak-map-i636.js "$APP_DIR/assets/tak-map-i636.js"' in install
assert 'i639 runtime deployment gate' in install and 'i639 post-start runtime route validation' in install
assert 'install-check=i639' in install
assert "_I639_PACKAGE_VERSION='1.4.0-i639'" in dash
for token in ['_i639_validate_shape_geometry','_i639_patch_shape_raw_cot','shape_geometry_i639','canonical_tak_geometry','mission_membership_preserved']:
    assert token in dash, token
for u in ['tak-map-context-sidebar-i572.js?v=1.4.0-i639','tak-map-package-i580.js?v=1.4.0-i639','tak-map-i636.js?v=1.4.0-i639']:
    assert u in dash, u
manifest=json.loads((ROOT/'assets'/'tak-map-deferred-i553.json').read_text())
assert manifest['version']=='1.4.0-i639' and manifest['count']==len(manifest['scripts'])
print('TAK Map i639 release contract passed')
