#!/usr/bin/env python3
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]
assert (ROOT/'VERSION').read_text().strip()=='1.4.0-i642'
ctx=(ROOT/'assets'/'tak-map-context-sidebar-i572.js').read_text()
pkg=(ROOT/'assets'/'tak-map-package-i580.js').read_text()
install=(ROOT/'install.sh').read_text();dash=(ROOT/'tak_dashboard.py').read_text()
assert "const VERSION = 'i642'" in ctx
for token in [
 'authoritativeMissionSaveI642:true','aggregateDataSyncCommitGateI642:false','ringOrderIndependentI642:true',
 'persistentEditUntilExplicitExitI641:true','centerTranslationHandleI641:true','notesLastI641:true','largerSaveCancelTextI641:true',
 "tx.authoritative_mission_readback_confirmed","mission-cot-readback-i642",'geometryMatchesI641',
 "if(state.shapeEdit.active){reassertActiveShapeDraftI640();return;}",
 "if (state.shapeEdit.active) { state.suppressMapClickUntil=Date.now()+360; reassertActiveShapeDraftI640(); return false; }",
 "addHandleI639(center,'center',np=>translateToCenterI639(np))",'font-size:11.5px!important','table.appendChild(notesRow)',
]: assert token in ctx,token
assert 'shape-edit-i641-confirm' not in ctx
assert 'Close Edit' not in ctx
assert "const VERSION='i642'" in pkg and "const PACKAGE='1.4.0-i642'" in pkg and "const SIZING='i642'" in pkg
assert 'i642 runtime deployment gate' in install and 'i642 post-start runtime route validation' in install and 'install-check=i642' in install
for token in ["_I642_VERSION='i642'","_I642_PACKAGE_VERSION='1.4.0-i642'","def _i642_ring_equal","def _i642_confirm_shape_mission","direct-mission-cot-readback-i642","native-mission-cot-api","generic_cot_socket_commit_gate':False","aggregate_data_sync_commit_gate':False","_i555_set_request_context(self)"]:
 assert token in dash,token
section=dash.split('# --- TAK Map 1.4.0-i642 authoritative Mission Shape save transaction ---',1)[1].split('# --- end TAK Map i642 authoritative Mission Shape save transaction ---',1)[0]
assert '_send_cot_to_ots(' not in section
assert "/Marti/api/missions/{mission_q}/cot?creatorUid={creator_q}" in section
for u in ['tak-map-context-sidebar-i572.js?v=1.4.0-i642','tak-map-package-i580.js?v=1.4.0-i642','tak-map-i636.js?v=1.4.0-i642']: assert u in dash,u
manifest=json.loads((ROOT/'assets'/'tak-map-deferred-i553.json').read_text());assert manifest['version']=='1.4.0-i642' and manifest['count']==len(manifest['scripts'])
print('TAK Map i642 release contract passed')
