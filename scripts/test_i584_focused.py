#!/usr/bin/env python3
from pathlib import Path
import ast, importlib.util, json, subprocess, sys
root=Path(__file__).resolve().parents[1]
assert (root/'VERSION').read_text().strip()=='1.3.0-i584'
ast.parse((root/'tak_dashboard.py').read_text(),filename='tak_dashboard.py')
server=(root/'tak_dashboard.py').read_text()
for marker in (
 '# --- TAK Map i581 rapid Data Sync membership and CoT cadence ---',
 '# --- TAK Map i582 corroborated Data Sync membership pruning hotfix ---',
 '# --- TAK Map i583 optimistic Data Sync handoff and single-flight cadence ---',
 '# --- TAK Map i583 reversible Mission-marker hotfix hf1 ---',
 '# --- TAK Map i583 reversible Mission-marker hotfix hf4: login-time OTS marker token and query authentication ---',
 '# --- TAK Map i583 reversible Mission-marker hotfix hf5-r2: publication-complete delayed Mission indexing ---',
 '# --- TAK Map i583 reversible Mission-marker hotfix hf6: temporary generic duplicate suppression ---',
 '# --- TAK Map i584 integrated Mission-marker publication and handoff ---'):
    assert marker in server, marker
assert server.count("if __name__=='__main__':\n    main()")==1
assert server.index('# --- TAK Map i584 integrated Mission-marker publication and handoff ---') > server.index('# --- TAK Map i583 reversible Mission-marker hotfix hf6: temporary generic duplicate suppression ---')
assert 'reversible Mission-marker hotfix hf2' not in server
assert 'reversible Mission-marker hotfix hf3' not in server
assert 'hotfix hf5-r1' not in server
assert 'atak-symbology-transport-i580.json' in (root/'install.sh').read_text()
doc=(root/'docs/INSTALL.md').read_text()
assert 'tak-map-v1.3.0-i584.zip' in doc and 'cd ~/Downloads/tak-map-v584' in doc
assert 'rm -rf ~/Downloads/tak-map-v584' not in doc
result=subprocess.run(['node',str(root/'scripts/test_icon_resolver_precedence_i579.js')],cwd=root,check=True,text=True,capture_output=True)
summary=json.loads(result.stdout); assert summary['exact_sidc_collisions_checked']==92
spec=importlib.util.spec_from_file_location('tak_i584_focused',root/'tak_dashboard.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
assert m.TAK_MAP_ITERATION=='i584'
cfg=m.tak_map_config(); assert cfg['version']=='1.3.0-i584'
assert cfg['icon_resolver_precedence_i579']['exact_collision_count']==92
assert cfg['atak_symbology_transport_i580']['decision_counts']=={'generic':14,'keep':22,'replace':126}
release=cfg['data_sync_marker_publication_i584']
for key in ('uuid4_event_identity','point_not_eud_or_contact','creator_identity_separate_from_point_identity','point_name_preserved','latitude_longitude_preserved','hae_ce_le_preserved_when_available','milstd2525c_symbol_and_affiliation_preserved','login_time_flask_security_marker_token','oauth_bearer_not_used_for_marker_api','marker_write_plus_mission_association_completes_save','mission_cot_indexing_is_background_handoff','immediate_delete_metadata','single_visible_optimistic_marker','create_dialog_and_preview_close_after_association','temporary_generic_duplicates_suppressed','global_generic_symbol_unchanged'):
    assert release[key] is True,key
assert release['live_validated_stack']==['hf1','hf4','hf5-r2','hf6']
assert cfg['startup_architecture_i584']['package_version']=='i584'
assert cfg['startup_architecture_i584']['data_sync_poll_seconds']==5
bg=cfg['data_sync_background_i583']
assert bg['membership_interval_seconds']==10 and bg['full_cot_enrichment_interval_seconds']==20 and bg['browser_snapshot_poll_seconds']==5
control=(root/'assets/tak-map-data-sync-i553.js').read_text()
assert "const V='i584'" in control and 'minIntervalMs:4000' in control and 'automaticPollMs:5000' in control
assert 'function installAutomaticPoll()' in control and "'i584-automatic-poll'" in control
icon=(root/'assets/tak-map-icon-registry-i572.js').read_text()
assert 'function saveNewPoint()' in icon and 'pointNameInput' in icon and 'closeCreatePanel()' in icon
assert 'TAK Map i584 integrated marker handoff' in icon
assert 'TAK Map i584 integrated temporary duplicate suppression' in icon
assert "const VERSION = 'i584';" in icon
assert 'POINT DROPPER' not in icon
assert '/assets/runtime/tak-map-icon-registry-i572.js?v=1.3.0-i584' in m.TAK_MAP_HTML
assert '1.3.0-i583-hf' not in m.TAK_MAP_HTML
print('i584 focused package, integrated marker publication, point-not-contact, handoff, duplicate suppression, cadence, and symbology checks passed')
