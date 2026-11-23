"""i662 source regression: real Mission lifecycle, status controls and sidebar."""
import base64
import pathlib
import sys
import tempfile
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from token_mesh_i660 import MeshStore,decode_invite,mission_invite_png
from token_mesh_transport_i660 import MeshTransport
class ReleaseI662Tests(unittest.TestCase):
 def test_mission_lifecycle_and_invitation(self):
  with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as other:
   a=MeshStore(td);b=MeshStore(other)
   with self.assertRaises(ValueError):a.create_mission('Before enrollment')
   invited=a.create('Field Mesh');b.join(invited['invite'])
   created=a.create_mission('Survey Ops')
   self.assertTrue(created['ok']);self.assertEqual(len(a.mission_list()),1)
   token=created['invite'];self.assertEqual(token,a.mission_invite(created['missionId']))
   m=decode_invite(token,'XMS1:')
   self.assertEqual(m['missionName'],'Survey Ops')
   self.assertEqual(m['missionId'],created['missionId'])
   self.assertEqual(len(base64.b64decode(m['key'],validate=True)),32)
   self.assertTrue(m['serverIdentity'].startswith('token-mesh:'))
   b.mission_join(token)
   self.assertEqual(a.mission_list()[0]['mission'],b.mission_list()[0]['mission'])
   if __import__('importlib').util.find_spec('qrcode'):
    qr=mission_invite_png('Survey Ops',token)
    self.assertTrue(qr.startswith(b'\x89PNG\r\n\x1a\n'))
 def test_persistent_pause_retains_enrollment_and_missions(self):
  with tempfile.TemporaryDirectory() as td:
   a=MeshStore(td);a.create('Station 1');mission=a.create_mission('Ops');uid=a.device_uid()
   a.set_mesh_enabled(False)
   b=MeshStore(td)
   self.assertFalse(b.mesh_enabled());self.assertEqual(b.device_uid(),uid)
   self.assertEqual(b.mission_list()[0]['mission'],mission['missionId'])
   self.assertIsNotNone(b.group())
   self.assertFalse(MeshTransport(b).status()['transportReady'])
   with self.assertRaises(ValueError):b.create_mission('Should not create while paused')
   with self.assertRaises(ValueError):b.mission_join(mission['invite'])
   b.set_mesh_enabled(True);self.assertTrue(MeshStore(td).mesh_enabled())
 def test_backend_rejects_bad_toggle_type(self):
  with tempfile.TemporaryDirectory() as td:
   a=MeshStore(td)
   for v in ('false',0,None,1):
    with self.assertRaises(ValueError):a.set_mesh_enabled(v)
 def test_final_card_and_apis(self):
  import tak_dashboard
  h=tak_dashboard.INDEX_HTML
  self.assertEqual(h.count('id="tokenMeshCardI660"'),1)
  self.assertEqual(h.count('id="meshSlateScriptI662"'),1)
  self.assertEqual(h.count('id="meshMapProjectionI662"'),1)
  self.assertNotIn('window.tokenMeshCreateI660=',h)
  self.assertIn('font-family:\'Manrope\'',h)
  self.assertIn('id="meshSwitchI662"',h)
  self.assertIn('id="meshMissionCreateI662"',h)
  self.assertIn('id="meshMissionJoinI662"',h)
  self.assertIn('id="meshMissionQRUploadI662"',h)
  self.assertIn("act('mission-create'",h)
  self.assertIn("act('mission-invite'",h)
  self.assertIn("act('control'",h)
  self.assertLess(h.index('id="gatewayDataPanelV476"'),h.index('id="tokenMeshCardI660"'))
  self.assertLess(h.index('id="tokenMeshCardI660"'),h.index('id="dataSyncPanelV476"'))
  self.assertIn('<h2>OTS DATA SYNC</h2>',h)
  self.assertEqual(tak_dashboard.tak_map_config()['version'],(ROOT/'VERSION').read_text().strip())
 def test_installer_installs_new_asset(self):
  text=(ROOT/'install.sh').read_text()
  self.assertIn('install -m 0644 assets/tak-map-token-mesh-i662.html',text)
  self.assertTrue((ROOT/'assets'/'tak-map-token-mesh-i662.html').exists())
if __name__=='__main__':unittest.main()
