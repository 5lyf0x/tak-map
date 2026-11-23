"""i683 package invariants: version, feature assets, and upgrade-safety gates."""
from pathlib import Path
import ast
import unittest
ROOT=Path(__file__).resolve().parents[1]
class ReleaseI683(unittest.TestCase):
 def test_version_and_loader_cache(self):
  import tak_dashboard as d
  self.assertEqual((ROOT/'VERSION').read_text().strip(),'1.4.0-i690')
  self.assertEqual(d.TAK_MAP_ITERATION,'i690')
  self.assertEqual(d.tak_map_config()['version'],'1.4.0-i690')
  self.assertEqual(d.TAK_MAP_HTML.count('</body></html>'),1)
  for filename in ('tak-map-mvum-i673.js','tak-map-route-elevation-i681.js','tak-map-basemap-stack-i673.js'):
   self.assertIn(filename+'?v=1.4.0-i690',d.TAK_MAP_HTML)
 def test_editor_real_geometry_and_strict_visibility(self):
  js=(ROOT/'assets/tak-map-route-elevation-i681.js').read_text()
  for s in ('function fromPopup(evt)', 'function closePopup(evt)', 'function syncLifecycle()',
   'S.mode===\'saved\'&&!S.selectedRouteKey', 'function savedRoute(id)',
   'function renderRunMarkers(', "data-tak-elev-route", 'Math.abs(angle)>=35',
   "const POSITION_KEY='tak-map-elevation-i683-position'", 'takElevHeaderDistanceI683',
   'takElevDragI683', 'takElevRunTipI683', "setView('extended')"):
   self.assertIn(s,js)
  self.assertIn('/api/tak-map/ndm/elevation/sample',js)
  self.assertNotIn('Math.random()',js)
 def test_mvum_vector_fallback_without_layer_flashing(self):
  js=(ROOT/'assets/tak-map-mvum-i673.js').read_text()
  for text in ('drawParentTile', 'function ensureButton()', 'MutationObserver(', 'devicePixelRatio'):
   self.assertIn(text,js)
  self.assertNotIn('state.layer.redraw()',js)
 def test_install_is_source_safe(self):
  sh=(ROOT/'install.sh').read_text()
  for a in ('assets/tak-map-route-elevation-i681.js','assets/tak-map-mvum-i673.js','VERSION'):
   self.assertIn('install -m 0644 '+a,sh)
  self.assertNotIn('rm -rf "$DATA_DIR"',sh)
  self.assertTrue((ROOT/'RELEASE_NOTES_I683.md').is_file())
  t=ast.parse((ROOT/'tak_dashboard.py').read_text())
  mains=[i for i,n in enumerate(t.body) if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and isinstance(n.test.left,ast.Name) and n.test.left.id=='__name__']
  self.assertEqual(mains,[len(t.body)-1])
if __name__=='__main__':unittest.main()
