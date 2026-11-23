#!/usr/bin/env python3
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]
assert (ROOT/'VERSION').read_text().strip()=='1.4.0-i659'
ctx=(ROOT/'assets'/'tak-map-context-sidebar-i572.js').read_text()
pkg=(ROOT/'assets'/'tak-map-package-i580.js').read_text()
install=(ROOT/'install.sh').read_text(); dash=(ROOT/'tak_dashboard.py').read_text()
assert "const VERSION = 'i654'" in ctx
for token in [
 'nativeShapeSaveI643:true','globalNativeShapeReadbackI643:true','missionContentsUidAssociationI643:true','missionCotGetOnlyI643:true',
 'authoritativeMissionSaveI642:true','aggregateDataSyncCommitGateI642:false','ringOrderIndependentI642:true',
 'persistentEditUntilExplicitExitI641:true','centerTranslationHandleI641:true','notesLastI641:true','largerSaveCancelTextI641:true',
 "result.shape_edit_i643||result.shape_edit_i642","authoritative_global_readback_confirmed",'native-shape-global-mission-readback-i643',
 "if(state.shapeEdit.active){reassertActiveShapeDraftI640();return;}",
 "if (state.shapeEdit.active) { state.suppressMapClickUntil=Date.now()+360; reassertActiveShapeDraftI640(); return false; }",
 "addHandleI639(center,'center',np=>translateToCenterI639(np))",'font-size:11.5px!important','table.appendChild(notesRow)',
]: assert token in ctx,token
assert 'Close Edit' not in ctx
assert "const VERSION='i654'" in pkg and "const PACKAGE='1.4.0-i654'" in pkg and "const SIZING='i654'" in pkg
assert 'i654 runtime deployment gate' in install and 'i659 post-start runtime route validation' in install and 'install-check=i659' in install
for token in [
 "_I643_VERSION='i643'","_I643_PACKAGE_VERSION='1.4.0-i643'","def _i643_native_shape_contract","def _i643_wait_global_shape",
 "'/Marti/api/cot/xml/'","def _i643_associate_shape_uid","/contents?creatorUid=","{'uids':[_i643_text(uid)]}",
 "def _i643_confirm_shape_mission","mission-cot-get-native-shape-readback-i643","per-user-certificate-authenticated-ssl-cot",
 "mission_cot_write_endpoint_used':False","global_cot_geometry_commit_gate':True","mission_contents_uid_association':True",
 "generic_public_cot_uid_lookup_commit_gate':False","aggregate_data_sync_commit_gate':False","_i555_set_request_context(self)",
]: assert token in dash,token
section=dash.split('# --- TAK Map 1.4.0-i643 validated native Mission Shape publication transaction ---',1)[1].split('# --- end TAK Map i643 validated native Mission Shape publication transaction ---',1)[0]
assert '_send_cot_to_ots(' not in section
assert '_i642_send_shape_mission(' not in section
assert "_i531_send_per_user_cot(xml,uid)" in section
assert "method='PUT'" in section and '/contents?creatorUid=' in section
assert "primary=f'/Marti/api/missions/{mission_q}/cot'" in section and "method='GET'" in section
assert "for method in ('POST','PUT')" not in section
for u in ['tak-map-context-sidebar-i572.js?v=1.4.0-i643','tak-map-package-i580.js?v=1.4.0-i643','tak-map-i636.js?v=1.4.0-i643']: assert u in dash,u  # inherited i643 patch source
import runpy
served=runpy.run_path(str(ROOT/'tak_dashboard.py'), run_name='tak_map_i644_inherited_shape_contract')['TAK_MAP_HTML']
for u in ['tak-map-context-sidebar-i572.js?v=1.4.0-i659','tak-map-package-i580.js?v=1.4.0-i659','tak-map-i636.js?v=1.4.0-i659']: assert u in served,u
manifest=json.loads((ROOT/'assets'/'tak-map-deferred-i553.json').read_text()); assert manifest['version']=='1.4.0-i659' and manifest['count']==len(manifest['scripts'])
print('TAK Map i643 Shape compatibility and i650 release contract passed')
