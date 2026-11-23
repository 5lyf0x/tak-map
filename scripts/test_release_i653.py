#!/usr/bin/env python3
import contextlib,io,os,runpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
assert (R/'VERSION').read_text().strip()=='1.4.0-i659'
with contextlib.redirect_stdout(io.StringIO()):
    ns=runpy.run_path(str(R/'tak_dashboard.py'),run_name='takmap_i653_contract')
assert ns['TAK_MAP_ITERATION']=='i659'
assert ns['tak_map_config']()['version']=='1.4.0-i659'
assert ns['tak_map_config']()['ndm_integration']['router']=='systemd-autostart-with-config'
page=ns['TAK_MAP_HTML']
assert page.count('id="takMapNDMDataBtnI652"')==1
assert page.count('takMapNDMDataLoaderI652')==1
assert 'tak-map-ndm-data-i652.js?v=1.4.0-i659' in page
assert 'takMapCertSetupLoaderI650' in page
assert 'takMapLiveSearchLoaderI650' in page
assert 'i659' in ns['TAK_MAP_LOGIN_HTML']
ndm=(R/'ndm_packages_i651.py').read_text()
assert 'TAK_MAP_NDM_MAX_UPLOAD_MB' in ndm and "'4096'" in ndm
assert 'No upload cap for existing' in ndm or 'NO file-size quota' in ndm or 'no file-size quota' in ndm.lower()
assert 'client_max_body_size 4096M;' in (R/'nginx/tak-map-https-9444.conf').read_text()
assert 'max_upload_bytes' in ns['Handler'].do_GET.__code__.co_consts.__repr__() or 'max_upload_bytes' in (R/'tak_dashboard.py').read_text()
manifest=json.loads((R/'assets/tak-map-deferred-i553.json').read_text())
assert manifest['version']=='1.4.0-i659' and manifest['count']==len(manifest['scripts'])
inst=(R/'install.sh').read_text()
assert 'tak-map-ndm-data-i652.js?install-check=i659' in inst
assert 'scripts/install-valhalla-i651.py' in inst
print('PASS: i653 release identity, NDM no-quota existing files, 4-GiB browser upload, retained modal and Valhalla')
