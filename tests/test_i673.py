"""i673 route actions, NDM overlay/viewhed, basemap layering, and no-redraw regressions."""
import hashlib,io,os,pathlib,sqlite3,stat,subprocess,sys,tempfile,time,unittest,zipfile,zlib,array,json
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

class I673(unittest.TestCase):
 def test_release_and_runtime_routes(self):
  import tak_dashboard as d
  self.assertEqual((ROOT/'VERSION').read_text().strip(),'1.4.0-i683')
  self.assertEqual(d.tak_map_config()['version'],'1.4.0-i683')
  self.assertIn('tak-map-basemap-stack-i673.js',d.TAK_MAP_HTML)
  self.assertIn('tak-map-mvum-i673.js',d.TAK_MAP_HTML)
  self.assertEqual(d.TAK_MAP_HTML.count('</body></html>'),1)
  self.assertTrue((ROOT/'install.sh').stat().st_mode & stat.S_IXUSR)
  for asset in ('ndm_elevation_i673.py','assets/tak-map-basemap-stack-i673.js','assets/tak-map-mvum-i673.js','assets/tak-map-deferred-i553.json'):
   self.assertIn('install -m 0644 '+asset,(ROOT/'install.sh').read_text())
 def test_viewshed_source_persistence_and_routing(self):
  js=(ROOT/'takmap.js').read_text()
  for required in ("sampleElevationsNdmI673(points,opts)","value=\"NDM\"","if(requested==='NDM')","result=await sampleElevationsNdmI673(points,opts)","NDM terrain has incomplete or missing elevation cells",'Math.min(2,batches)'):
   self.assertIn(required,js)
  self.assertIn("sampleElevationsEsri(points,opts)",js)
  self.assertIn("sampleElevationsUsgs(points,opts)",js)
  self.assertIn("'Auto';",js)
  import json
  bundle=json.loads((ROOT/'assets/tak-map-deferred-i553.json').read_text())
  live=next(x['code'] for x in bundle['scripts'] if x['id']=='v282ViewshedRestore')
  self.assertIn('sampleElevationsNdmI673',live)
  self.assertIn('value="NDM"',live)
  self.assertIn("if(requested==='NDM')",live)
 def test_route_actions_are_atomic_with_undo(self):
  js=(ROOT/'assets/tak-map-route-editor-i654.js').read_text()
  for x in ('async function reverseRoute()','async function backToStart()','S.operationBusy','S.undoTransaction','commitTransaction(original','routeLegWithNavigation(last,first','Math.min(2,legs.length)','Reverse','Back to Start'):
   self.assertIn(x,js)
 def test_basemap_retained_layer_controls(self):
  js=(ROOT/'assets/tak-map-basemap-stack-i673.js').read_text()
  for x in ('input type="checkbox"','type="range"','data-base-opacity-i673','dragstart','drop','state.layers','setOpacity','keepBuffer:8','persist()'):
   self.assertIn(x,js)
  self.assertNotIn("map.off('move'",js)
 def test_mvum_cached_idle_rendering_and_mvt_parser(self):
  js=(ROOT/'assets/tak-map-mvum-i673.js').read_text()
  for x in ('MAX_CONCURRENT=6','MAX_CACHE=620','keepBuffer:10','updateWhenIdle:true','moveend zoomend resize','setTimeout(warmBuffer,320)','drawMvt','takMvumButtonI673','drawParentTile'):
   self.assertIn(x,js)
  self.assertNotIn('maxNativeZoom:16',js)
  self.assertNotIn('state.layer.redraw()',js)
  p=subprocess.run(['node',str(ROOT/'tests/mvum_tile_i673_mock.cjs')],capture_output=True,text=True,timeout=10)
  self.assertEqual(p.returncode,0,p.stdout+'\n'+p.stderr)
 def test_authenticated_asset_delivery(self):
  import tak_dashboard as d
  class Fake:
   path='/assets/runtime/tak-map-mvum-i673.js?v=1.4.0-i673';command='GET'
   def __init__(self):self.wfile=io.BytesIO();self.headers=[];self.status=None
   def send_response(self,s):self.status=s
   def send_header(self,k,v):self.headers.append((k,v))
   def end_headers(self):pass
  f=Fake()
  with patch.object(d,'_i651_authorize',return_value=True):d._i673_assets_get(f)
  self.assertEqual(f.status,200)
  self.assertEqual(f.wfile.getvalue(),(ROOT/'assets/tak-map-mvum-i673.js').read_bytes())
 def test_ndm_sample_native_sqlite(self):
  from ndm_elevation_i673 import Sampler,NdmElevationError
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d)
   zipfile_path=root/'az-elevation.zip'
   db=root/'source.sqlite'
   with sqlite3.connect(db) as conn:
    conn.execute('CREATE TABLE metadata(name TEXT,value TEXT)')
    conn.execute('INSERT INTO metadata VALUES(?,?)',('schema','takrig.terrain.sqlite.v1'))
    conn.execute('CREATE TABLE tiles(tile_id TEXT,west REAL,south REAL,east REAL,north REAL,rows INTEGER,cols INTEGER,encoding TEXT,data BLOB)')
    conn.execute('CREATE TABLE tile_overviews(tile_id TEXT,resolution_m REAL,west REAL,south REAL,east REAL,north REAL,rows INTEGER,cols INTEGER,encoding TEXT,data BLOB)')
    arr=array.array('h',[100,200,300,400]);conn.execute('INSERT INTO tiles VALUES(?,?,?,?,?,?,?,?,?)',('grid',-112.0,34.0,-111.0,35.0,2,2,'int16le+zlib',zlib.compress(arr.tobytes())))
    conn.commit()
   with zipfile.ZipFile(zipfile_path,'w',compression=zipfile.ZIP_DEFLATED) as z:z.write(db,'terrain.sqlite')
   sid=hashlib.sha256(zipfile_path.read_bytes()).hexdigest();st=zipfile_path.stat()
   public={'dataset_id':sid,'type':'terrain','available':True,'superseded':False,'resolution_m':30,'region':'AZ','bounds':[-112,34,-111,35],'source_size':st.st_size,'source_mtime_ns':st.st_mtime_ns}
   class Catalog:
    def listing(self):return [public]
    def _load(self):return {'datasets':{sid:{'zip_path':str(zipfile_path)}}}
   sampler=Sampler(Catalog(),root/'cache')
   sampler.coverage([-112,34,-111,35]);
   for i in range(80):
    if sampler.prepare(sampler.entries()[0])=='ready':break
    time.sleep(.03)
   self.assertEqual(sampler.prepare(sampler.entries()[0]),'ready',sampler.errors)
   data=sampler.sample([[35,-112],[35,-111],[34,-112],[34,-111],[34.5,-111.5]])
   self.assertTrue(data['complete']);self.assertEqual(data['valid'],5)
   self.assertEqual(data['elevations'],[100.0,200.0,300.0,400.0,250.0])
   self.assertFalse(sampler.sample([[35,-112],[35,-111],[34,-112],[34,-111],[34.5,-111.5],[35,-112.5]])['complete'])
 def test_context_route_controls_padded(self):
  js=(ROOT/'assets/tak-map-context-sidebar-i572.js').read_text()
  self.assertIn('padding:0 12px 12px',js)
  self.assertIn("eb.style.height='34px';db.style.height='34px';",js)

if __name__=='__main__':unittest.main()
