"""Functional i667 Cesium view contract tests via isolated Node mock."""
import shutil, subprocess, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class TerrainI667(unittest.TestCase):
 def test_cesium_paths(self):
  self.assertTrue(shutil.which('node'),'Node required for terrain JS fixtures')
  p=subprocess.run(['node',str(ROOT/'tests/terrain_mock_i667.cjs')],capture_output=True,text=True,timeout=18)
  self.assertEqual(p.returncode,0,p.stderr+'\n'+p.stdout)
  self.assertIn('PASS',p.stdout)
 def test_source_has_full_and_scoped_fix(self):
  source=(ROOT/'assets/tak-map-core-i553.js').read_text()
  self.assertIn('function terrainOverlayStoreI667()',source)
  self.assertIn('function terrainDrawSavedLabelsI667(force)',source)
  self.assertIn('function terrainBillboardImage(o)',source)
  self.assertIn('terrainResetLabelsI667()',source)
  self.assertIn('terrainDrawSavedLabelsI667(true)',source)
  self.assertIn('terrainStyleI667(o||{color}',source)
 def test_icon_registry_and_routes_field_repair(self):
  icons=(ROOT/'assets/tak-map-icon-registry-i572.js').read_text()
  routes=(ROOT/'assets/tak-map-route-editor-i654.js').read_text()
  self.assertIn('grid-template-columns:minmax(0,1fr)!important;',icons)
  self.assertIn('A user-selected custom icon outranks',icons)
  self.assertIn('ep.x<0||ep.y<0||ep.x>visibleSize.x',routes)
 def test_sidebar_edit_action_source_owned(self):
  sidebar=(ROOT/'assets/tak-map-context-sidebar-i572.js').read_text()
  self.assertIn('function appendRouteEditActionI667()',sidebar)
  self.assertIn("state.selected.source!=='local'",sidebar)
  self.assertIn('route_revision_i659',sidebar)
  self.assertIn('window.takRouteEditorI654',sidebar)
  self.assertIn('Edit Route',sidebar)
