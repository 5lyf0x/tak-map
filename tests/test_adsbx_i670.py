"""TAK Map i670: exact upstream ADSBx silhouettes, type preservation, served assets."""
import json, pathlib, subprocess, time, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]

class ADSBxI670(unittest.TestCase):
 def test_upstream_shape_and_mapping_metadata(self):
  shapes={}
  for row in (ROOT/'assets/vendor/adsbx/shapes.jsonl').read_text().splitlines():
   key,box,path=json.loads(row)
   self.assertNotIn(key,shapes);self.assertTrue(path.startswith(('m','M')));shapes[key]=path
  self.assertEqual(len(shapes),30)
  self.assertEqual(len((ROOT/'assets/vendor/adsbx/type-map.csv').read_text().split(',')),376)
  for k in ('a320','a321','b738','b739','a359','c130','f18','apache','blackhawk','unknown'):
   self.assertIn(k,shapes)
  self.assertIn('cecc076a15ea202446b7fce34704a451d87dcb49',(ROOT/'assets/vendor/adsbx/NOTICE.md').read_text())
  self.assertTrue((ROOT/'assets/vendor/adsbx/GPL-2.0.txt').is_file())
 def test_veil_real_type_from_api_metadata(self):
  from tak_map_veil_api_i666 import normalize_object
  ms=int(time.time()*1000)
  base={'objectId':'adsb:x123','sourceService':'adsb_1090','position':{'lat':34.2,'lon':-118.2},'positionTimestamp':ms,'identity':{'callsign':'ABC123','icao24':'A1B2C3'},'ttlSeconds':120}
  for category,source in [('tak',{'tak':{'enrichment':{'type_designator':'B738'}}}),('metadata',{'metadata':{'icao_type':'A320'}}),('identity',{'identity':{'callsign':'ABC123','icao24':'A1B2C3','aircraft_type':'H60'}})]:
   o=normalize_object('test-node',{**base,**source});self.assertIsNotNone(o)
   self.assertTrue(o['enrichment'].get('type_designator') or o['enrichment'].get('icao_type') or o['enrichment'].get('aircraft_type'),category)
 def test_installer_runtime_version_and_page(self):
  import tak_dashboard as d
  self.assertEqual(d.tak_map_config()['version'],'1.4.0-i674')
  self.assertEqual((ROOT/'VERSION').read_text().strip(),'1.4.0-i674')
  page=d.TAK_MAP_HTML
  self.assertIn('id="map"',page)
  self.assertIn('id="takVeilCardI665"',page)
  self.assertIn('/assets/runtime/tak-map-adsbx-i670.js?v=1.4.0-i674',page)
  self.assertIn('/assets/runtime/tak-map-veil-visual-i670.js?v=1.4.0-i674',page)
  self.assertNotIn("document.querySelectorAll('[data-tak-map-release]').forEach",page)
  for asset in ('tak-map-adsbx-i670.js','tak-map-veil-visual-i670.js'):
   self.assertIn('install -m 0644 assets/'+asset,(ROOT/'install.sh').read_text())
 def test_node_mappings_and_marker(self):
  r=subprocess.run(['node',str(ROOT/'tests/adsbx_type_mock_i670.cjs')],capture_output=True,text=True,timeout=20)
  self.assertEqual(r.returncode,0,r.stdout+'\n'+r.stderr)

if __name__=='__main__':unittest.main()
