#!/usr/bin/env python3
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
assert (ROOT/'VERSION').read_text().strip()=='1.4.0-i641'
ctx=(ROOT/'assets'/'tak-map-context-sidebar-i572.js').read_text()
pkg=(ROOT/'assets'/'tak-map-package-i580.js').read_text()
install=(ROOT/'install.sh').read_text();dash=(ROOT/'tak_dashboard.py').read_text()
assert "const VERSION = 'i641'" in ctx
for token in [
 'verifiedSaveReadbackI641:true','persistentEditUntilExplicitExitI641:true','centerTranslationHandleI641:true','notesLastI641:true','largerSaveCancelTextI641:true',
 'shape-edit-i641-confirm','persisted_overlay','geometryMatchesI641','confirmSavedDraftI641','findReadbackObjectI641',
 "if(state.shapeEdit.active){reassertActiveShapeDraftI640();return;}",
 "if (state.shapeEdit.active) { state.suppressMapClickUntil=Date.now()+360; reassertActiveShapeDraftI640(); return false; }",
 "addHandleI639(center,'center',np=>translateToCenterI639(np))",
 'font-size:11.5px!important','table.appendChild(notesRow)',
]: assert token in ctx,token
assert 'Close Edit' not in ctx
assert "const VERSION='i641'" in pkg and "const PACKAGE='1.4.0-i641'" in pkg and "const SIZING='i641'" in pkg
assert 'i641 runtime deployment gate' in install and 'i641 post-start runtime route validation' in install and 'install-check=i641' in install
assert "_I639_VERSION='i641'" in dash and "_I639_PACKAGE_VERSION='1.4.0-i641'" in dash
for token in ["'notes_last_field':True","'center_translation_handle':True","'empty_map_click_keeps_edit_active':True","'save_requires_readback_confirmation':True","'persisted_overlay':True"]: assert token in dash,token
for u in ['tak-map-context-sidebar-i572.js?v=1.4.0-i641','tak-map-package-i580.js?v=1.4.0-i641','tak-map-i636.js?v=1.4.0-i641']: assert u in dash,u
manifest=json.loads((ROOT/'assets'/'tak-map-deferred-i553.json').read_text());assert manifest['version']=='1.4.0-i641' and manifest['count']==len(manifest['scripts'])
print('TAK Map i641 release contract passed')
