"""i663 Mesh Sync header and legibility regression tests."""
from pathlib import Path
import sys, unittest, re
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
class ReleaseI663Tests(unittest.TestCase):
 def test_assembled_card_structure(self):
  import tak_dashboard
  page=tak_dashboard.INDEX_HTML
  self.assertRegex(tak_dashboard.tak_map_config()['version'],r'^1\.4\.0-i(?:663|664|665|666|667|668|669|670|671|672|673|674)$')
  self.assertEqual(page.count('id="tokenMeshCardI660"'),1)
  self.assertEqual(page.count('id="meshHeaderI663"'),1)
  self.assertEqual(page.count('id="meshCollapseI663"'),1)
  self.assertEqual(page.count('id="meshSwitchI662"'),1)
  self.assertEqual(page.count('id="tokenMeshStateI660"'),1)
  self.assertIn('data-manual-collapse="true" data-collapsible-ready="1"',page)
  header=page.split('id="meshHeaderI663"',1)[1].split('</h2>',1)[0]
  labels=['MESH SYNC','id="tokenMeshStateI660"','id="meshSwitchI662"','id="meshCollapseI663"']
  self.assertEqual(sorted(header.index(x) for x in labels),[header.index(x) for x in labels])
  self.assertIn('id="meshBodyI663"',page)
  self.assertLess(page.index('id="gatewayDataPanelV476"'),page.index('id="tokenMeshCardI660"'))
  self.assertLess(page.index('id="tokenMeshCardI660"'),page.index('id="dataSyncPanelV476"'))
  self.assertIn('<h2>OTS DATA SYNC</h2>',page)
 def test_collision_proof_collapse(self):
  s=(ROOT/'assets/tak-map-token-mesh-i663.html').read_text()
  self.assertIn('data-skip-auto-collapsible="true"',s)
  self.assertIn("COLLAPSE_KEY='takMapPanelCollapsed:mesh-sync'",s)
  self.assertIn("event.stopPropagation();setCollapsed(!card.classList.contains('collapsed'))",s)
  self.assertIn("event.preventDefault();event.stopPropagation();if(!latest)return;",s)
  self.assertIn("arrow.setAttribute('aria-expanded',String(!collapsed))",s)
  self.assertIn("#tokenMeshCardI660.collapsed .ms-body{display:none!important}",s)
 def test_readability_and_assets(self):
  s=(ROOT/'assets/tak-map-token-mesh-i663.html').read_text()
  for css,minimum in (('ms-eyebrow',9.5),('ms-mission-cap',9.5),('ms-count',9.5),('ms-empty',11.5),('ms-footnote',10.5),('ms-metric small',10.5)):
   r=re.search(r'\.'+re.escape(css)+r'\{[^}]*font-size:([\d.]+)px',s)
   self.assertIsNotNone(r,css)
   self.assertGreaterEqual(float(r.group(1)),minimum,css)
  self.assertIn(".ms-link{font:700 11px 'Manrope'",s)
  self.assertIn('assets/tak-map-token-mesh-i663.html',(ROOT/'install.sh').read_text())
  self.assertRegex((ROOT/'VERSION').read_text().strip(),r'^1\.4\.0-i(?:663|664|665|666|667|668|669|670|671|672|673|674)$')
if __name__=='__main__':unittest.main()
