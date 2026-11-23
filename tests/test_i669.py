"""i669: real contract checks for geodesic rings, VEIL visuals and release wiring."""
from pathlib import Path
import math, subprocess, unittest, json
ROOT=Path(__file__).resolve().parents[1]
class I669(unittest.TestCase):
    def test_version_and_required_assets(self):
        self.assertEqual((ROOT/'VERSION').read_text().strip(),'1.4.0-i674')
        import tak_dashboard as t
        self.assertEqual(t.tak_map_config()['version'],'1.4.0-i674')
        self.assertIn("ITERATION='i674'",t.TAK_MAP_HTML)
        for x in ('id="floatingMapToolbar"','id="takVeilCardI665"','id="map"',
                  '/assets/runtime/tak-map-range-rings-i669.js?v=1.4.0-i674',
                  '/assets/runtime/tak-map-adsbx-i670.js?v=1.4.0-i674'):
            self.assertIn(x,t.TAK_MAP_HTML)
        self.assertNotIn("document.querySelectorAll('[data-tak-map-release]').forEach",t.TAK_MAP_HTML)
    def test_installer_asset_contract(self):
        s=(ROOT/'install.sh').read_text()
        for x in ('tak-map-range-rings-i669.js','tak-map-range-rings-icon-i669.svg','tak-map-veil-visual-i669.js'):
            self.assertIn('install -m 0644 assets/'+x,s)
            self.assertTrue((ROOT/'assets'/x).is_file())
        self.assertIn('BASEMAP',(ROOT/'assets/tak-map-veil-i666.js').read_text().upper())
    def test_discovery_http_and_admin(self):
        js=(ROOT/'assets/tak-map-veil-i666.js').read_text()
        self.assertIn("await api('discover',{})",js)
        self.assertNotIn("await api('discover');",js)
        t=(ROOT/'tak_dashboard.py').read_text()
        self.assertIn('def _veil_admin_authorized_i668(handler):',t)
        self.assertIn("session.get('is_admin') is True",t)
        self.assertIn('if not _veil_admin_authorized_i668(self)',t)
        self.assertIn('watchSidebarOrder()',js)
        self.assertNotIn("card.insertAdjacentElement('afterend',geo)",js)
    def test_actual_deferred_adsb_panel_wired(self):
        manifest=json.loads((ROOT/'assets/tak-map-deferred-i553.json').read_text())
        self.assertEqual(manifest['version'],'1.4.0-i670')
        copies=[x['code'] for x in manifest['scripts'] if x['id']=='TakMapAdsbSidebarI610']
        self.assertEqual(len(copies),1)
        self.assertEqual(copies[0],(ROOT/'assets/tak-map-adsb-sidebar-i610.js').read_text())
        self.assertIn('openExternalI669',copies[0])
        self.assertIn('1.4.0-i670',(ROOT/'assets/tak-map-startup-i553.js').read_text())
    def test_node_behaviors(self):
        result=subprocess.run(['node',str(ROOT/'tests/visual_rings_mock_i669.cjs')],capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stdout+'\n'+result.stderr)

if __name__=='__main__':unittest.main()
