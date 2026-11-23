#!/usr/bin/env python3
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]
assert (ROOT/'VERSION').read_text().strip()=='1.4.0-i638'
ctx=(ROOT/'assets'/'tak-map-context-sidebar-i572.js').read_text()
pkg=(ROOT/'assets'/'tak-map-package-i580.js').read_text()
install=(ROOT/'install.sh').read_text()
dash=(ROOT/'tak_dashboard.py').read_text()
assert "const VERSION = 'i638'" in ctx
for token in ['stableShapeInfoI638:true','localizedGeometryI638:true','missionSourceAttributionI638:true','tak-shape-edit-toggle-i638','formatAreaMeters','measurementSystem()']:
    assert token in ctx, token
assert "const VERSION='i638'" in pkg and "compactContextWidth:320" in pkg and 'contextScrollbarHidden:true' in pkg
assert 'install -m 0644 assets/tak-map-i636.js "$APP_DIR/assets/tak-map-i636.js"' in install
assert 'i638 runtime deployment gate' in install and 'i638 post-start runtime route validation' in install
assert "_I638_PACKAGE_VERSION='1.4.0-i638'" in dash
for u in ['tak-map-context-sidebar-i572.js?v=1.4.0-i638','tak-map-package-i580.js?v=1.4.0-i638','tak-map-i636.js?v=1.4.0-i638']:
    assert u in dash, u
manifest=json.loads((ROOT/'assets'/'tak-map-deferred-i553.json').read_text())
assert manifest['version']=='1.4.0-i638' and manifest['count']==len(manifest['scripts'])
print('TAK Map i638 release contract passed')
