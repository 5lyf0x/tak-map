"""i686 infrastructure bounded display, additive catalog colors and offline data fidelity."""
import json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import tak_map_infrastructure_i686 as infra

def point(i,x=-118.5,y=34.5):
 return {'type':'Feature','id':str(i),'geometry':{'type':'Point','coordinates':[x,y]},'properties':{'id':i}}

class I686Infrastructure(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.old=os.environ.get('TAK_MAP_INFRA_DIR');os.environ['TAK_MAP_INFRA_DIR']=self.tmp.name
 def tearDown(self):
  if self.old is None:os.environ.pop('TAK_MAP_INFRA_DIR',None)
  else:os.environ['TAK_MAP_INFRA_DIR']=self.old
  self.tmp.cleanup()
 def test_additive_color_migration_preserves_existing_dataset(self):
  # Create a real i685 database before opening the i686 module.
  import tak_map_infrastructure_i685 as old
  old.catalog()
  with old._db() as c:
   c.execute("INSERT INTO layers(id,category_id,name,mode,kind,enabled) VALUES('existing','water','Original','offline','point',1)")
   old._write_features(c,'existing',[point('original')])
  state=infra.catalog();self.assertEqual(state['version'],'i686')
  layer=next(x for x in state['layers'] if x['id']=='existing');self.assertEqual(layer['color'],'')
  state=infra.mutate({'op':'layer-color','id':'existing','color':'#AAbbCC'})
  self.assertEqual(next(x for x in state['layers'] if x['id']=='existing')['color'],'#aabbcc')
  for v in ('red','#123','#001122ff','"><svg>'):
   with self.assertRaises(ValueError):infra.mutate({'op':'layer-color','id':'existing','color':v})
  with self.assertRaises(ValueError):infra.mutate({'op':'layer-color','id':'missing','color':'#112233'})
  self.assertEqual(infra.get_features('existing','offline',[-119,34,-118,35],0)['loaded_count'],1)
  infra.mutate({'op':'layer-color','id':'existing','color':''})
  self.assertEqual(next(x for x in infra.catalog()['layers'] if x['id']=='existing')['color'],'')
 def test_offline_dense_budget_and_export_complete(self):
  infra.catalog()
  with infra._db() as c:
   c.execute("INSERT INTO layers(id,category_id,name,mode,kind,enabled) VALUES('manholes','water','Manholes','offline','point',1)")
   # About 51 per grid cell; scattered so sampling is spatially balanced.
   for start in range(0,5101,250):
    data=[point(i,-119+(i%101)/101,34+(i//101)/51) for i in range(start,min(5101,start+250))]
    infra._write_features(c,'manholes',data)
  x=infra.get_features('manholes','offline',[-119,34,-118,35],0)
  self.assertLessEqual(len(x['features']),5000)
  self.assertTrue(x['limited'],x)
  self.assertEqual(x['total_stored'],5101)
  self.assertTrue(len(x['features'])>1000)
  self.assertEqual(infra.catalog()['layers'][0].get('feature_count') is not None,True)
  exported=infra.export_dataset('manholes','geojson')
  self.assertEqual(len(json.loads(exported.read_text())['features']),5101)
 def test_online_query_bounded_and_partial(self):
  calls=[]
  def fake(source,bbox,offset=0,count=1000):
   calls.append((bbox,offset,count))
   return {'features':[point(i) for i in range(offset,offset+count)]}
  with patch.object(infra,'_query_online',side_effect=fake):
   x=infra.get_features('lacounty-sewer-manholes','online',[-119,34,-118,35],0)
  self.assertEqual(x['loaded_count'],5000)
  self.assertTrue(x['limited'])
  self.assertTrue(len(calls)<=6,calls)
  self.assertTrue(all(c<=1000 for _,_,c in calls))
  self.assertEqual(x['source_status'],'limited')
 def test_download_child_inherits_color_but_separates_identity(self):
  infra.mutate({'op':'layer-color','id':'lacounty-sewer-mains','color':'#123abc'})
  with infra._db() as c:
   c.execute("INSERT INTO jobs(id,source_id,layer_id,bbox,status,created,updated) VALUES('xyz','lacounty-sewer-mains','staging-xyz','[-119,34,-118,35]','running','now','now')")
   infra._write_features(c,'staging-xyz',[point('x')])
   infra._rename_download(c,{'id':'xyz','source_id':'lacounty-sewer-mains','layer_id':'staging-xyz','bbox':'[-119,34,-118,35]'})
  layer=next(x for x in infra.catalog()['layers'] if x['id']=='offline-xyz')
  self.assertEqual(layer['color'],'#123abc')
  infra.mutate({'op':'layer-color','id':'offline-xyz','color':'#ff0000'})
  self.assertEqual(next(x for x in infra.catalog()['layers'] if x['id']=='lacounty-sewer-mains')['color'],'#123abc')

if __name__=='__main__':unittest.main()
