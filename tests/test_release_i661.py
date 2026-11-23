"""Source-level smoke checks for the i661 sidebar and AIS detail corrections."""
import pathlib
import sys
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

class ReleaseI661Tests(unittest.TestCase):
    def test_final_sidebar_assembly(self):
        import tak_dashboard
        html=tak_dashboard.INDEX_HTML
        self.assertEqual(html.count('id="tokenMeshCardI660"'),1)
        self.assertEqual(html.count('class="ms-title">MESH SYNC'),1)
        self.assertEqual(html.count('<h2>OTS DATA SYNC'),1)
        a,b,c=(html.index('id="'+x+'"') for x in ('gatewayDataPanelV476','tokenMeshCardI660','dataSyncPanelV476'))
        self.assertLess(a,b)
        self.assertLess(b,c)
        self.assertIn('id="meshCreateI662"',html)
        self.assertIn('id="meshJoinI662"',html)
        self.assertIn('Not enrolled',html)
        self.assertEqual(tak_dashboard.tak_map_config()['version'],(ROOT/'VERSION').read_text().strip())
    def test_ais_formatter_present_and_escaped(self):
        script=(ROOT/'assets'/'tak-map-gateway-data-v491.js').read_text()
        self.assertIn('function aisDetailsHtml(value)',script)
        self.assertIn('esc(match[2].trim())',script)
        self.assertIn("if(p.source==='ais_vessels')add('Details',aisDetailsHtml(remarks),true)",script)
    def test_installer_includes_fragment_after_assets_directory(self):
        script=(ROOT/'install.sh').read_text()
        self.assertLess(script.index('mkdir -p "$APP_DIR/assets"'),script.index('install -m 0644 assets/tak-map-token-mesh-i661.html'))
        self.assertTrue((ROOT/'assets'/'tak-map-token-mesh-i661.html').is_file())

if __name__=='__main__':unittest.main()
