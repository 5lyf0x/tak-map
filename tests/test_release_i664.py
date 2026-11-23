"""i664: regression for MESH SYNC switch cosmetics and real AIS detail rows."""
from pathlib import Path
import re,sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
class I664(unittest.TestCase):
 def test_assembled_page(self):
  import tak_dashboard
  page=tak_dashboard.INDEX_HTML
  self.assertIn(tak_dashboard.tak_map_config()['version'],('1.4.0-i664','1.4.0-i665','1.4.0-i666','1.4.0-i667','1.4.0-i668','1.4.0-i669','1.4.0-i670','1.4.0-i671','1.4.0-i672','1.4.0-i673','1.4.0-i674'))
  self.assertEqual((ROOT/'VERSION').read_text().strip(),tak_dashboard.tak_map_config()['version'])
  self.assertEqual(page.count('id="tokenMeshCardI660"'),1)
  self.assertLess(page.index('id="gatewayDataPanelV476"'),page.index('id="tokenMeshCardI660"'))
  self.assertLess(page.index('id="tokenMeshCardI660"'),page.index('id="dataSyncPanelV476"'))
  self.assertIn('<h2>OTS DATA SYNC</h2>',page)
  header=page.split('id="meshHeaderI663"',1)[1].split('</h2>',1)[0]
  fields=['MESH SYNC','id="tokenMeshStateI660"','id="meshSwitchI662"','id="meshCollapseI663"']
  self.assertEqual(sorted(header.index(x) for x in fields),[header.index(x) for x in fields])
 def test_mesh_changes_only_css(self):
  old=(ROOT/'assets/tak-map-token-mesh-i663.html').read_text()
  new=(ROOT/'assets/tak-map-token-mesh-i664.html').read_text()
  oldscript=old.split('<script id="meshSlateScriptI662">',1)[1]
  newscript=new.split('<script id="meshSlateScriptI662">',1)[1]
  new_behavior=newscript.split(' // i666: match standard sidebar behavior',1)[1].split(" try{setCollapsed(localStorage.getItem(COLLAPSE_KEY)==='1')}",1)[0]
  self.assertIn("header.addEventListener('click'",new_behavior)
  self.assertIn("header.addEventListener('keydown'",new_behavior)
  self.assertIn("event.target.closest('button,input,label')",new_behavior)
  self.assertIn('setCollapsed(!card.classList.contains',new_behavior)
  self.assertIn('ms-chip::before{content:none;display:none}',new)
  self.assertIn('width:38px;height:20px;',new)
  self.assertIn('background:#39d98a;',new)
  self.assertIn('background:#91a2ad;',new)
  self.assertIn('id="meshCollapseI663"',new)
  self.assertIn('assets/tak-map-token-mesh-i664.html',(ROOT/'install.sh').read_text())
 def test_ais_actual_renderer(self):
  script=(ROOT/'assets/tak-map-gateway-data-v491.js').read_text()
  self.assertIn('function aisDetailsHtml(value)',script)
  self.assertIn('esc(match[2].trim())',script)
  self.assertIn('gateway-ais-details-heading-i664',script)
  self.assertIn('gateway-ais-details-label-i664',script)
  self.assertIn('gateway-ais-details-value-i664',script)
  self.assertIn("if(p.source==='ais_vessels')add('Details',aisDetailsHtml(remarks),true)",script)
  self.assertIn("(p.source==='ais_vessels'&&row.label==='Details'&&row.html)?row.value",script)
  self.assertNotIn('gateway-ais-detail-line-i661',script)
  self.assertIn('install -m 0644 assets/tak-map-gateway-data-v491.js',(ROOT/'install.sh').read_text())
if __name__=='__main__':unittest.main()
