import pathlib,re,unittest,subprocess
P=pathlib.Path(__file__).resolve().parents[1]
class NextRelease(unittest.TestCase):
 def test_aircraft_visual_styling_and_scale(self):
  v=(P/'assets/tak-map-veil-visual-i670.js').read_text()
  self.assertIn('fill="#ffffff" stroke="#000000" stroke-width="1"',v)
  self.assertIn("o?.service==='adsb'?43.2:o?.service==='aprs'?44:36",v)
  self.assertIn('vector-effect="non-scaling-stroke"',v)
  self.assertIn('const degree=heading(o)??0',v)
  self.assertIn('iconSize:[iconPx,iconPx]',(P/'assets/tak-map-veil-i666.js').read_text())
  self.assertIn('width:aprsPixels||iconPx,height:aprsPixels||iconPx',(P/'assets/tak-map-veil-phase3-i668.js').read_text())
 def test_ring_multiselection_and_legacy_migration(self):
  s=(P/'assets/tak-map-range-rings-i669.js').read_text()
  self.assertIn('labelPositions:',s)
  self.assertIn('x.labelPosition',s)
  self.assertIn("[...document.querySelectorAll('#trPositionsI671 input:checked')]",s)
  for bearing in ['NE:45','SE:135','SW:225','NW:315']:self.assertIn(bearing,s)
  self.assertIn('showPicker',s);self.assertIn('choiceCleanup',s)
  self.assertIn('crosshair',s);self.assertIn("e.key==='Escape'",s)
 def test_versions(self):
  self.assertEqual((P/'VERSION').read_text().strip(),'1.4.0-i674')
  self.assertIn("TAK_MAP_ITERATION='i674'",(P/'tak_dashboard.py').read_text())
  self.assertIn('XTAK VEIL APRS', (P/'RELEASE_NOTES_I671.md').read_text())
if __name__=='__main__':unittest.main()
