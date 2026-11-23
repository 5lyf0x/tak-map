#!/usr/bin/env python3
import contextlib,io,os,runpy,tempfile,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
assert (ROOT/'VERSION').read_text().strip()=='1.4.0-i659'
assert 'tak-map-ndm-data-i652.js' in (ROOT/'install.sh').read_text()
with tempfile.TemporaryDirectory(prefix='i652-release-') as temp:
    os.environ['TAK_DASHBOARD_DATA_DIR']=temp
    with contextlib.redirect_stdout(io.StringIO()):
        d=runpy.run_path(str(ROOT/'tak_dashboard.py'),run_name='release_i652_contract')
    assert d['TAK_MAP_ITERATION']=='i659'
    assert d['tak_map_config']()['version']=='1.4.0-i659'
    assert d['tak_map_config']()['ndm_integration']['router']=='systemd-autostart-with-config'
    page=d['TAK_MAP_HTML']
    assert page.count('id="takMapNDMDataBtnI652"')==1
    assert page.count('takMapNDMDataLoaderI652')==1
    assert '?v=1.4.0-i659' in page
    assert 'i653-dev' not in page
    assert 'takMapCertSetupLoaderI650' in page
    assert 'takMapLiveSearchLoaderI650' in page
    assert 'i659' in d['TAK_MAP_LOGIN_HTML']
manifest=json.loads((ROOT/'assets/tak-map-deferred-i553.json').read_text())
assert manifest['version']=='1.4.0-i659'
assert manifest['count']==len(manifest['scripts'])
print('PASS: released i652 identity, NDM Tools modal and i651 NDM/Valhalla preservation')
