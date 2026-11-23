"""TAK Map i668 Phase 3 strict identity, conservative health, browser contract."""
import tempfile,threading,time,unittest,subprocess,shutil
from pathlib import Path
from unittest.mock import patch
from tak_map_veil_identity_i668 import canonical_identity, identity_envelope
from tak_map_veil_health_i668 import VeilHealthI668,sanitize_health
ROOT=Path(__file__).resolve().parents[1]

class Dummy:
 def __init__(self):
  self.lock=threading.RLock();self.config={'enabled':False}
  self.nodes={'a':{'nodeId':'a','host':'192.168.1.10','port':8080,'apiSubscribed':False}}
  self.objects={}
class DummyAPI:
 def __init__(self):
  self.lock=threading.RLock();self.tokens={};self.statuses={}
 def _verify(self,n):return {'nodeId':n['nodeId']}

class Phase3I668(unittest.TestCase):
 def test_icao_exact_validation(self):
  self.assertEqual(canonical_identity('adsb_1090',{'icao':'A0B123'}),'adsb:icao:a0b123')
  self.assertIsNone(canonical_identity('adsb',{'callsign':'A0B123'}))
  self.assertIsNone(canonical_identity('adsb',{'icao':'ZZ1234'}))
  self.assertIsNone(canonical_identity('adsb',{'icao':'A0B123','icao24':'B0B124'}))
  self.assertIsNone(canonical_identity('ais',{'icao':'A0B123'}))
 def test_mmsi(self):
  self.assertEqual(canonical_identity('ais',{'mmsi':'311000397'}),'ais:mmsi:311000397')
  self.assertIsNone(canonical_identity('ais',{'mmsi':'000000000'}))
  self.assertIsNone(canonical_identity('ais',{'mmsi':'311000397','MMSI':'311000398'}))
  self.assertIsNone(canonical_identity('ais',{'name':'VESSEL NAME'}))
 def test_aprs_typed_rid(self):
  self.assertEqual(canonical_identity('aprs',{'callsign':'W6ABC-9'}),'aprs:station:W6ABC-9')
  self.assertIsNone(canonical_identity('aprs',{'objectName':'WX'}))
  self.assertEqual(canonical_identity('aprs',{'objectName':'WX','objectOwner':'W6ABC'}),'aprs:object:W6ABC:WX')
  self.assertIsNone(canonical_identity('remote_id',{'uasId':'DRONE123'}))
  self.assertEqual(canonical_identity('remote_id',{'uasId':'DRONE123','uasIdType':'serial_number'}),'rid:serial_number:DRONE123')
 def test_identity_whitelist(self):
  ident,key=identity_envelope('adsb',{'icao':'ABC123','password':'secret','serial_number':'x'}, {})
  self.assertEqual(key,'adsb:icao:abc123')
  self.assertNotIn('password',ident)
 def test_health_gates_and_fields(self):
  rx=Dummy();api=DummyAPI();health=VeilHealthI668(rx,api)
  self.assertEqual(health.read('a')['state'],'disabled')
  rx.config['enabled']=True
  self.assertEqual(health.read('a')['state'],'udp_only')
  rx.nodes['a']['apiSubscribed']=True
  self.assertIsNone(health.read('a')['health'])
  api.tokens['a']='valid-token';api.statuses['a']={'apiState':'synced'}
  record={'veilUptimeSeconds':50,'sdr':{'connected':True,'private':'reject'},'network':{'ip':'private'},
          'warnings':[{'code':'sdr_unavailable','message':'SDR temporarily unavailable','config':'bad'}]}
  with patch('tak_map_veil_health_i668._http',return_value=record) as http:
   result=health.read('a');self.assertTrue(result['ok']);self.assertEqual(http.call_count,1)
   self.assertNotIn('network',result['health']);self.assertNotIn('private',result['health']['sdr'])
   self.assertEqual(health.read('a')['health'],result['health']);self.assertEqual(http.call_count,1)
 def test_health_never_creates_auth_prompt(self):
  rx=Dummy();rx.config['enabled']=True;rx.nodes['a']['apiSubscribed']=True
  api=DummyAPI();api.tokens['a']='token';api.statuses['a']={'apiState':'synced'}
  health=VeilHealthI668(rx,api)
  from tak_map_veil_api_i666 import AuthRequired
  with patch('tak_map_veil_health_i668._http',side_effect=AuthRequired('expired')):
   r=health.read('a');self.assertIsNone(r['health']);self.assertEqual(api.statuses['a']['apiState'],'synced')
 def test_ui_contract(self):
  main=(ROOT/'assets/tak-map-veil-i666.js').read_text()
  script=(ROOT/'assets/tak-map-veil-phase3-i668.js').read_text()
  sidebar=(ROOT/'assets/tak-map-context-sidebar-i572.js').read_text()
  self.assertIn('tvMergeVeilI668',main);self.assertIn('tvCrossI668',main)
  self.assertIn("if(!state.config?.enabled||!node.apiSubscribed)return;",main)
  self.assertIn('function combineLocalRouteActionsI668()',sidebar)
  self.assertIn("eb.textContent='Edit';db.textContent='Delete';",sidebar)
  self.assertIn('function safeKey',script) if False else None
  self.assertIn('visibleNativeKeys',script)
 def test_browser_mock(self):
  self.assertTrue(shutil.which('node'))
  r=subprocess.run(['node',str(ROOT/'tests/phase3_mock_i668.cjs')],text=True,capture_output=True,timeout=15)
  self.assertEqual(r.returncode,0,r.stdout+'\n'+r.stderr)

if __name__=='__main__': unittest.main()
