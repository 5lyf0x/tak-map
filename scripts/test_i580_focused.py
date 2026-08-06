#!/usr/bin/env python3
from pathlib import Path
import ast, importlib.util, json, subprocess, sys
root=Path(__file__).resolve().parents[1]
assert (root/'VERSION').read_text().strip()=='1.3.0-i580'
ast.parse((root/'tak_dashboard.py').read_text(),filename='tak_dashboard.py')
server=(root/'tak_dashboard.py').read_text()
assert '# --- TAK Map i579 exact canonical icon resolver precedence ---' in server
assert '# --- TAK Map i580 reviewed ATAK transport symbology ---' in server
assert server.count("if __name__=='__main__':\n    main()")==1
assert 'atak-symbology-transport-i580.json' in (root/'install.sh').read_text()
assert 'tak-map-v1.3.0-i580.zip' in (root/'docs/INSTALL.md').read_text()
assert 'cd tak-map-v580' in (root/'docs/INSTALL.md').read_text()
assert 'rm -rf ~/Downloads/tak-map-v580' not in (root/'docs/INSTALL.md').read_text()
result=subprocess.run(['node',str(root/'scripts/test_icon_resolver_precedence_i579.js')],cwd=root,check=True,text=True,capture_output=True)
summary=json.loads(result.stdout)
assert summary['exact_sidc_collisions_checked']==92
spec=importlib.util.spec_from_file_location('tak_i580_focused',root/'tak_dashboard.py')
m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
assert m.TAK_MAP_ITERATION=='i580'
cfg=m.tak_map_config(); assert cfg['version']=='1.3.0-i580'
assert cfg['icon_resolver_precedence_i579']['exact_collision_count']==92
assert cfg['atak_symbology_transport_i580']['decision_counts']=={'generic':14,'keep':22,'replace':126}
assert cfg['startup_architecture_i580']['package_version']=='i580'
print('i580 focused package, resolver-preservation, and ATAK symbology checks passed')
