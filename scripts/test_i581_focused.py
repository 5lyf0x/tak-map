#!/usr/bin/env python3
from pathlib import Path
import ast, importlib.util, json, subprocess, sys
root=Path(__file__).resolve().parents[1]
assert (root/'VERSION').read_text().strip()=='1.3.0-i581'
ast.parse((root/'tak_dashboard.py').read_text(),filename='tak_dashboard.py')
server=(root/'tak_dashboard.py').read_text()
assert '# --- TAK Map i580 reviewed ATAK transport symbology ---' in server
assert '# --- TAK Map i581 rapid Data Sync membership and CoT cadence ---' in server
assert server.count("if __name__=='__main__':\n    main()")==1
assert 'atak-symbology-transport-i580.json' in (root/'install.sh').read_text()
assert 'tak-map-v1.3.0-i581.zip' in (root/'docs/INSTALL.md').read_text()
assert 'cd ~/Downloads/tak-map-v581' in (root/'docs/INSTALL.md').read_text()
assert 'rm -rf ~/Downloads/tak-map-v581' not in (root/'docs/INSTALL.md').read_text()
result=subprocess.run(['node',str(root/'scripts/test_icon_resolver_precedence_i579.js')],cwd=root,check=True,text=True,capture_output=True)
summary=json.loads(result.stdout)
assert summary['exact_sidc_collisions_checked']==92
spec=importlib.util.spec_from_file_location('tak_i581_focused',root/'tak_dashboard.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
assert m.TAK_MAP_ITERATION=='i581'
cfg=m.tak_map_config(); assert cfg['version']=='1.3.0-i581'
assert cfg['icon_resolver_precedence_i579']['exact_collision_count']==92
assert cfg['atak_symbology_transport_i580']['decision_counts']=={'generic':14,'keep':22,'replace':126}
assert cfg['startup_architecture_i581']['package_version']=='i581'
assert cfg['data_sync_background_i581']['membership_interval_seconds']==10
assert cfg['data_sync_background_i581']['full_cot_enrichment_interval_seconds']==20
assert cfg['data_sync_background_i581']['manual_refresh_forces_membership_and_full_cot'] is True
control=(root/'assets/tak-map-data-sync-i553.js').read_text()
assert 'minIntervalMs:4000' in control and 'automaticPollMs:5000' in control
print('i581 focused package, symbology preservation, and Data Sync cadence checks passed')
