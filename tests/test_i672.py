"""i672 original VEIL r50 category/asset parity, Live SA metadata, and heading tests."""
from pathlib import Path
import hashlib, subprocess, time, unittest, sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tak_map_veil_aprs_i672 import aprs_symbol
from tak_map_veil_api_i666 import normalize_object

class VEILi672(unittest.TestCase):
 def base(self,service='aprs'):
  return {'objectId':('aprs:K6ABC-9' if service=='aprs' else 'adsb:ABC123'),
          'sourceService':service,'position':{'lat':34.2,'lon':-118.2},
          'positionTimestamp':int(time.time()*1000),'identity':{'callsign':'K6ABC-9'},
          'ttlSeconds':120,'objectType':'aprs_station'}
 def test_original_svg_bundled_exact(self):
  veil=Path('/mnt/data/_xtak_veil_r50/app/static/map-icons')
  local=ROOT/'assets/veil-aprs-r50'
  names=('base','vehicle','portable','digipeater','weather','aircraft','marine','object','emergency','generic')
  self.assertEqual(sorted(x.name for x in local.glob('*.svg')),sorted(f'aprs-{n}.svg' for n in names))
  for n in names:
   data=(local/f'aprs-{n}.svg').read_bytes();self.assertIn(b'<svg',data)
   # Reference source exists for build tests, but installed release is self-contained.
   if veil.exists():self.assertEqual(hashlib.sha256(data).digest(),hashlib.sha256((veil/f'aprs-{n}.svg').read_bytes()).digest())
 def test_symbol_normalization(self):
  p=aprs_symbol({'symbol':'>','symbolTable':'/','overlay':'A'}, {'weather':None}, 'aprs_station')
  self.assertEqual((p['symbolCode'],p['symbolTable'],p['overlay'],p['weather']),('>','/','A','false'))
  self.assertEqual(aprs_symbol(raw={'symbolCode':'_','weather':'true'})['weather'],'true')
  self.assertEqual(aprs_symbol(raw={'symbolCode':'<svg>'})['symbolCode'],'')
 def test_native_api_aprs(self):
  r=self.base();r['identity'].update(symbol='>',symbolTable='/',overlay='A');r['metadata']={'weather':None}
  obj=normalize_object('node-a',r)
  self.assertEqual(obj['aprs']['symbolCode'],'>');self.assertEqual(obj['aprs']['symbolTable'],'/')
  self.assertEqual(obj['aprs']['overlay'],'A');self.assertEqual(obj['aprs']['objectType'],'aprs_station')
  self.assertEqual(obj['canonicalKey'],'aprs:station:K6ABC-9')
 def test_native_api_weather(self):
  r=self.base();r['identity']['symbol']='_';r['metadata']={'weather':{'temp':70}}
  obj=normalize_object('node-a',r);self.assertEqual(obj['aprs']['weather'],'true')
 def test_udp_cot_preserves_r50_aprs_symbol_and_station_identity(self):
  import tempfile
  from test_veil_i665 import cot, NODES
  from tak_map_veil_i665 import VeilReceiver
  with tempfile.TemporaryDirectory() as folder:
   rx=VeilReceiver(folder)
   try:
    rx.nodes={NODES[0]['nodeId']:dict(NODES[0])};rx.settings({'enabled':True})
    content=cot(service='aprs',oid='aprs:K6ABC-9',aprs=True).replace(b'callsign="TEST"',b'callsign="K6ABC-9"')
    self.assertTrue(rx.ingest(content,NODES[0]['host']))
    item=rx.snapshot()['objects'][0]
    self.assertEqual(item['aprs']['symbolCode'],'_')
    self.assertEqual(item['aprs']['symbolTable'],'/')
    self.assertEqual(item['canonicalKey'],'aprs:station:K6ABC-9')
   finally:rx.stop()
 def test_native_api_aprs_object_owner(self):
  r=self.base();r['objectType']='aprs_object';r['identity'].update(objectName='TEST FIRE',symbol='#')
  obj=normalize_object('node-a',r)
  self.assertEqual(obj['canonicalKey'],'aprs:object:K6ABC-9:TEST FIRE')
 def test_heading_course_from_r50_motion(self):
  r=self.base('adsb_1090');r['motion']={'courseDeg':0,'speedMps':0};r['heading']=75
  obj=normalize_object('node-a',r)
  self.assertEqual(obj['heading'],0);self.assertEqual(obj['speedMps'],0)
  r['motion']={'courseDeg':225,'speedMps':33};self.assertEqual(normalize_object('node-a',r)['heading'],225)
  r['motion']={'courseDeg':None};r['tak']={'track':{'courseDeg':-90}}
  self.assertEqual(normalize_object('node-a',r)['heading'],270)
  r['motion']={'courseDeg':'nan'};r['tak']={};r['heading']=180
  self.assertEqual(normalize_object('node-a',r)['heading'],180)
 def test_frontend_broker_and_visual(self):
  r=subprocess.run(['node',str(ROOT/'tests/veil_i672_mock.cjs')],cwd=str(ROOT),capture_output=True,text=True,timeout=15)
  self.assertEqual(r.returncode,0,r.stdout+'\n'+r.stderr)
 def test_runtime_registered_and_install_mode(self):
  import tak_dashboard as d
  self.assertEqual(d.tak_map_config()['version'],'1.4.0-i674')
  html=d.TAK_MAP_HTML
  self.assertIn('tak-map-veil-aprs-i672.js?v=1.4.0-i674',html)
  self.assertLess(html.index('tak-map-veil-aprs-i672.js'),html.index('tak-map-veil-visual-i670.js?v=1.4.0-i674'))
  self.assertEqual(d._I672_APRS['/assets/runtime/veil-aprs-r50/aprs-vehicle.svg'],'aprs-vehicle.svg')
  self.assertTrue((ROOT/'install.sh').stat().st_mode & 0o111)
  self.assertIn('assets/veil-aprs-r50/aprs-*.svg',(ROOT/'install.sh').read_text())
 def test_static_runtime_svg_get(self):
  import io, tak_dashboard as d
  class Fake:
   def __init__(self):
    self.path='/assets/runtime/veil-aprs-r50/aprs-vehicle.svg?v=1.4.0-i674'
    self.command='GET';self.wfile=io.BytesIO();self.headers=[];self.status=None
   def send_response(self,status):self.status=status
   def send_header(self,key,value):self.headers.append((key,value))
   def end_headers(self):pass
  f=Fake();d._i672_get(f)
  self.assertEqual(f.status,200)
  self.assertIn(('Content-Type','image/svg+xml; charset=utf-8'),f.headers)
  self.assertEqual(f.wfile.getvalue(),(ROOT/'assets/veil-aprs-r50/aprs-vehicle.svg').read_bytes())

if __name__=='__main__':unittest.main()
