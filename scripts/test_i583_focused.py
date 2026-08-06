#!/usr/bin/env python3
from pathlib import Path
import ast, importlib.util, json, subprocess, sys
root=Path(__file__).resolve().parents[1]
assert (root/'VERSION').read_text().strip()=='1.3.0-i583'
ast.parse((root/'tak_dashboard.py').read_text(),filename='tak_dashboard.py')
server=(root/'tak_dashboard.py').read_text()
for marker in (
 '# --- TAK Map i581 rapid Data Sync membership and CoT cadence ---',
 '# --- TAK Map i582 corroborated Data Sync membership pruning hotfix ---',
 '# --- TAK Map i583 optimistic Data Sync handoff and single-flight cadence ---'):
    assert marker in server, marker
assert server.index('# --- TAK Map i583 optimistic Data Sync handoff and single-flight cadence ---') > server.index('# --- TAK Map i582 corroborated Data Sync membership pruning hotfix ---')
assert server.count("if __name__=='__main__':\n    main()")==1
assert 'atak-symbology-transport-i580.json' in (root/'install.sh').read_text()
doc=(root/'docs/INSTALL.md').read_text()
assert 'tak-map-v1.3.0-i583.zip' in doc and 'cd ~/Downloads/tak-map-v583' in doc
assert 'rm -rf ~/Downloads/tak-map-v583' not in doc
result=subprocess.run(['node',str(root/'scripts/test_icon_resolver_precedence_i579.js')],cwd=root,check=True,text=True,capture_output=True)
summary=json.loads(result.stdout); assert summary['exact_sidc_collisions_checked']==92
spec=importlib.util.spec_from_file_location('tak_i583_focused',root/'tak_dashboard.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
assert m.TAK_MAP_ITERATION=='i583'
cfg=m.tak_map_config(); assert cfg['version']=='1.3.0-i583'
assert cfg['icon_resolver_precedence_i579']['exact_collision_count']==92
assert cfg['atak_symbology_transport_i580']['decision_counts']=={'generic':14,'keep':22,'replace':126}
assert cfg['startup_architecture_i583']['package_version']=='i583'
bg=cfg['data_sync_background_i583']
assert bg['membership_interval_seconds']==10 and bg['full_cot_enrichment_interval_seconds']==20 and bg['browser_snapshot_poll_seconds']==5
for key in ('persistent_per_user_optimistic_rows','exact_uid_canonical_handoff','partial_rows_cannot_downgrade_known_symbol','older_snapshots_cannot_remove_pending_create','separate_single_flight_pending_membership_and_full','recursive_forced_full_chain_prevented','incomplete_success_never_authorizes_pruning','nonempty_to_zero_requires_cot_or_second_complete_read','manual_refresh_preserves_current_snapshot_until_corroborated','per_mission_failure_isolation'):
    assert bg[key] is True,key
control=(root/'assets/tak-map-data-sync-i553.js').read_text()
assert "const V='i583'" in control and 'minIntervalMs:4000' in control and 'automaticPollMs:5000' in control
assert 'function installAutomaticPoll()' in control and "'i583-automatic-poll'" in control
print('i583 focused package, symbology preservation, corroboration, optimistic handoff, scheduler, and browser cadence checks passed')
