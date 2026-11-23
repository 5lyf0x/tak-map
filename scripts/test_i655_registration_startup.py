#!/usr/bin/env python3
"""i655 source checks: NDM rebuild synchronization, registration history, autostart safety."""
from pathlib import Path
import tempfile,sys,os,zipfile,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'scripts'))
from ndm_packages_i651 import Catalog, NDMError
from test_ndm_i651 import make_routing

with tempfile.TemporaryDirectory() as tmp:
    base=Path(tmp)
    ready=base/'ready';ready.mkdir()
    package=ready/'takrig-routing-ut-valhalla-3.6.3.zip'
    make_routing(package)
    catalog=Catalog(base/'catalog',external_roots=[ready])
    result=catalog.sync_existing()
    assert len(result['added'])==1 and not result['errors'],result
    old=result['added'][0]
    assert catalog.listing()[0]['status']=='Available'
    assert not catalog.sync_existing()['added'],'Repeated refresh should not revalidate unchanged ZIP'
    # Replace the NDM archive at exactly the same path with another complete valid ZIP.
    with zipfile.ZipFile(package,'a') as z:z.writestr('ndm-rebuild-metadata.txt','new-build')
    now=time.time()+2
    os.utime(package,(now,now))
    result=catalog.sync_existing()
    assert len(result['added'])==1 and result['added'][0]!=old,result
    rows={x['dataset_id']:x for x in catalog.listing()}
    assert rows[old]['superseded'] and rows[old]['status']=='Superseded',rows[old]
    assert rows[result['added'][0]]['status']=='Available'
    catalog.unregister(old)
    assert package.is_file(),'Unregister must never remove NDM source files'
    # Active graph cannot be unregistered; preserve installed service during replacements.
    from ndm_packages_i651 import _LOCK
    with _LOCK:
        data=catalog._load()
        data['datasets'][result['added'][0]]['active']=True
        catalog._save(data)
    try:catalog.unregister(result['added'][0]);raise AssertionError('Active graph was unregistered')
    except NDMError:pass

installer=(ROOT/'install.sh').read_text()
assert 'WantedBy=tak-map.service' in installer
assert 'ConditionPathExists=$DATA_DIR/ndm/active/valhalla.json' in installer
assert 'systemctl enable tak-map-valhalla.service' in installer
assert 'systemctl start tak-map-valhalla.service' in installer
# Region-boundary guard never fabricates a link between separate state archives.
import contextlib,io,runpy
with contextlib.redirect_stdout(io.StringIO()):
    ns=runpy.run_path(str(ROOT/'tak_dashboard.py'),run_name='i655_bounds_test')
fn=ns['_i655_check_active_graph_bounds']
class Synthetic:
    def listing(self):
        return [{'type':'routing','active':True,'bounds':[-115,31,-109,38]}]
fn.__globals__['_i651_catalog']=Synthetic()
fn([{'lat':35.0,'lon':-112.0}])
try:
    fn([{'lat':35,'lon':-112},{'lat':35,'lon':-122}])
    raise AssertionError('Cross-state route must reject missing connected graph')
except Exception as e:
    assert 'multi-state navigation graph' in str(e),e

print('PASS: automatic NDM refresh, superseded history, source preservation, active-graph guard, conditional service autostart')
