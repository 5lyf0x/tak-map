#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
assert (ROOT/'VERSION').read_text().strip()=='1.4.0-i640'
ctx=(ROOT/'assets'/'tak-map-context-sidebar-i572.js').read_text()
pkg=(ROOT/'assets'/'tak-map-package-i580.js').read_text()
install=(ROOT/'install.sh').read_text()
dash=(ROOT/'tak_dashboard.py').read_text()
assert "const VERSION = 'i640'" in ctx
for token in [
    'authoritativeDraftI640:true','refreshProtectedDraftI640:true','dedicatedSaveCancelI640:true',
    'closeEditRemovedI640:true','categoryRowRemovedI640:true','rotationRowRemovedI640:true','normalWeightShapeNameI640:true',
    'state.shapeEdit.draft','state.shapeEdit.draftKey','reassertActiveShapeDraftI640','protectActiveShapeLayerI640',
    'tak-shape-edit-actions-i640','data-i640-shape-save','i640ShapeCancel',
    "button.textContent='Edit'","button.style.display=state.shapeEdit.active?'none':''",
    "if(/^(category|rotation)$/i.test(name)) row.remove()",
    'grid-template-columns:minmax(0,1fr) minmax(0,1fr)',
    '.tak-v322-title{font-weight:400!important}',
    'font-weight:400!important',
]: assert token in ctx, token
assert 'Close Edit' not in ctx
geom=ctx[ctx.index('function geometryRows'):ctx.index('function applySourcePresentation')]
assert "push('Width'" not in geom and "push('Height'" not in geom and "push('Rotation'" not in geom
assert "push('Area'" in geom and "push('Perimeter'" in geom
assert "const VERSION='i640'" in pkg and "const PACKAGE='1.4.0-i640'" in pkg and "const SIZING='i640'" in pkg
assert 'compactContextWidth:320' in pkg and 'contextScrollbarHidden:true' in pkg
assert 'install -m 0644 assets/tak-map-i636.js "$APP_DIR/assets/tak-map-i636.js"' in install
assert 'i640 runtime deployment gate' in install and 'i640 post-start runtime route validation' in install and 'install-check=i640' in install
assert "_I639_VERSION='i640'" in dash and "_I639_PACKAGE_VERSION='1.4.0-i640'" in dash
for token in ['_i639_validate_shape_geometry','_i639_patch_shape_raw_cot','shape_geometry_i639','canonical_tak_geometry','mission_membership_preserved']:
    assert token in dash,token
for token in ["'authoritative_edit_draft':True","'background_refresh_draft_protection':True","'close_edit_button':False","'category_panel_row':False","'rotation_panel_row':False","'save_cancel_layout':'50/50'"]:
    assert token in dash,token
for u in ['tak-map-context-sidebar-i572.js?v=1.4.0-i640','tak-map-package-i580.js?v=1.4.0-i640','tak-map-i636.js?v=1.4.0-i640']:
    assert u in dash,u
manifest=json.loads((ROOT/'assets'/'tak-map-deferred-i553.json').read_text())
assert manifest['version']=='1.4.0-i640' and manifest['count']==len(manifest['scripts'])
print('TAK Map i640 release contract passed')
