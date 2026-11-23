"""i681 release-focused tests. Run without a live TAK server or modifying saved data."""
import ast
import re
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class I681(unittest.TestCase):
    def test_version_and_release_registration(self):
        self.assertEqual((ROOT/'VERSION').read_text().strip(),'1.4.0-i690')
        script=(ROOT/'tak_dashboard.py').read_text()
        tree=ast.parse(script)
        mains=[i for i,n in enumerate(tree.body) if isinstance(n,ast.If) and isinstance(n.test,ast.Compare) and isinstance(n.test.left,ast.Name) and n.test.left.id=='__name__']
        self.assertEqual(mains,[len(tree.body)-1])
        self.assertIn("TAK_MAP_ITERATION='i681'",script)
        self.assertIn('_i680_read_only_import_response',script)
        self.assertIn('tak-map-route-elevation-i681.js?v=1.4.0-i681',script)
        self.assertIn("'/api/tak-map/ndm/elevation/sample'",script)
    def test_mvum_toolbar_self_heals(self):
        js=(ROOT/'assets/tak-map-mvum-i673.js').read_text()
        self.assertIn('function ensureButton()',js)
        self.assertIn('MutationObserver(records=>',js)
        self.assertIn('queueMicrotask(install)',js)
        self.assertNotIn('if(state.map)return true',js)
        self.assertIn("state.map!==m",js)
        self.assertIn('#E53935',js)
        self.assertIn('Math.max(10,Math.min(16',js)
        self.assertIn('bar.insertBefore(button',js)
    def test_camera_focal_point_and_scale(self):
        js=(ROOT/'assets/tak-map-core-i553.js').read_text()
        for term in ('function terrain2DMetersPerPixel()', 'function terrain3DCenterGroundAt(', 'scene.globe.pick(ray,scene)',
                     'function terrain3DGroundScale(', 'camera.lookAt(target,new C.HeadingPitchRange(',
                     'C.Cartographic.fromCartesian(center)', 'terrain3DViewEpochI681++',
                     'terrainGroundHeightAt(initialCenter)', 'map.setView([lat,lon]', 'sampleTerrainMostDetailed'):
            self.assertIn(term,js)
        self.assertNotIn('map.setView([lat,lon],map.getZoom()',js)
    def test_live_elevation_full_geometry_and_saved_route_access(self):
        route=(ROOT/'assets/tak-map-route-editor-i654.js').read_text()
        core=(ROOT/'assets/tak-map-core-i553.js').read_text()
        js=(ROOT/'assets/tak-map-route-elevation-i681.js').read_text()
        for term in ('S.fullShape=fullShape', 'tak-map-route-geometry-i681'):
            self.assertIn(term,route)
        self.assertIn('data-tak-elev-route',core)
        for term in ('s.fullShape()', 'function samplePolyline(path,spacing)', 'step=Math.max(spacing,total/Math.max(1,maxSamples-1))', 'const count=Math.max(2,Math.ceil(total/step)+1)', 'out.push({lat:a.lat+(b.lat-a.lat)*t,lng:a.lng+(b.lng-a.lng)*t,d})',
                     '/api/tak-map/ndm/elevation/sample','/api/tak-map/ndm/elevation/coverage',
                     'Array.isArray(result.elevations)', 'result.elevations.map(v=>v==null?null',
                     'function movePanel(x,y)', 'const POSITION_KEY=',
                     'function savedRoute(id)', 'function hover(e)', 'AbortController', 'cache:new Map()'):
            self.assertIn(term,js)
        self.assertIn('tak-map-route-elevation-i681.js', (ROOT/'install.sh').read_text())
    def test_no_new_data_migration(self):
        change=(ROOT/'RELEASE_NOTES_I681.md').read_text().lower()
        self.assertIn('never modified',change)
        self.assertIn('i680',change)
if __name__=='__main__':unittest.main()
