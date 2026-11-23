"""i688 offline-only Infrastructure migration, filtering, indexing and data safety."""
import os, tempfile, unittest
from unittest.mock import patch
import tak_map_infrastructure_i687 as previous
import tak_map_infrastructure_i688 as infra

class I688Infrastructure(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.old=os.environ.get('TAK_MAP_INFRA_DIR')
  os.environ['TAK_MAP_INFRA_DIR']=self.tmp.name
  previous.catalog()  # Real i687 schema first
  with previous._db() as c:
   c.execute("INSERT INTO layers(id,category_id,name,mode,kind,enabled,color,min_zoom) VALUES('pipes','water','Trunk Pipes','offline','sewer',1,'#219acd',14)")
   c.execute("INSERT INTO layers(id,category_id,name,mode,kind,enabled) VALUES('sites','bridges','Bridges','offline','point',1)")
   c.execute("INSERT INTO layers(id,category_id,name,mode,kind,enabled) VALUES('online-x','water','Online X','online','point',1)")
   previous._write_features(c,'pipes',[
    {'type':'Feature','id':'main-100','geometry':{'type':'LineString','coordinates':[[-118,34],[-118.01,34.02]]},'properties':{'PIPE_DIAMETER':100,'NAME':'MAIN 100','ACTIVE':True,'FLOWS':0,'EMPTY':None}},
    {'type':'Feature','id':'main-12','geometry':{'type':'LineString','coordinates':[[-118,34],[-118.01,34.02]]},'properties':{'PIPE_DIAMETER':12,'NAME':'MAIN 12','ACTIVE':False}},
    {'type':'Feature','id':'main-48','geometry':{'type':'LineString','coordinates':[[-118,34],[-118.01,34.02]]},'properties':{'PIPE_DIAMETER':48,'NAME':'MAIN 48','ACTIVE':True}}])
   previous._write_features(c,'sites',[{'type':'Feature','id':'bridge-west','geometry':{'type':'Point','coordinates':[-118.3,34.2]},'properties':{'NAME':'Bridge Matched','SPEED':7,'REGION':'West'}}])
  infra.catalog()
 def tearDown(self):
  if self.old is None:os.environ.pop('TAK_MAP_INFRA_DIR',None)
  else:os.environ['TAK_MAP_INFRA_DIR']=self.old
  self.tmp.cleanup()
 def features(self):return infra.get_features('pipes','offline',[-119,33,-117,35],36,zoom=15)
 def test_migration_preserves_data_and_mode_visibility(self):
  c=infra.catalog();self.assertEqual(c['version'],'i688');self.assertFalse(c['online_rendering_enabled'])
  pipe=next(x for x in c['layers'] if x['id']=='pipes');self.assertEqual(pipe['color'],'#219acd');self.assertEqual(pipe['min_zoom'],14)
  self.assertEqual(pipe['point_symbol_mode'],'dot');self.assertEqual(pipe['feature_count'],3)
  self.assertEqual(infra.catalog()['layers'][0].keys().__contains__('filter_spec'),True)
  with patch.object(infra,'_query_online',side_effect=AssertionError('remote query')):
   with self.assertRaisesRegex(ValueError,'offline-only'):infra.get_features('online-x','online',[-119,33,-117,35])
  self.assertEqual(self.features()['loaded_count'],2)
  self.assertEqual(len(infra._all_features('pipes')[1]),3)
  infra.catalog();self.assertEqual(infra._all_features('pipes')[1][0]['id'],'main-100')
 def test_numeric_filter_multiple_rules_all_any_and_null(self):
  infra.mutate({'op':'layer-filter','id':'pipes','filter_spec':{'enabled':True,'mode':'all','rules':[
   {'field':'PIPE_DIAMETER','op':'>','value':'48','type':'number'},
   {'field':'ACTIVE','op':'=','value':'True','type':'text'}]}})
  self.assertEqual([x['id'] for x in self.features()['features']],['main-100'])
  self.assertEqual(infra.search_features('MAIN 48',minimum=36)['results'],[])
  rules=[{'field':'PIPE_DIAMETER','op':'between','value':'48','other':'100','type':'number'},
         {'field':'EMPTY','op':'empty'}]
  infra.mutate({'op':'layer-filter','id':'pipes','filter_spec':{'enabled':True,'mode':'any','rules':rules}})
  self.assertEqual(set(x['id'] for x in self.features()['features']),{'main-100','main-48'})
  self.assertEqual(len(infra._all_features('pipes')[1]),3)
 def test_search_all_data_respects_filters_category_and_min_zoom(self):
  hit=infra.search_features('Bridge Matched',minimum=36)
  self.assertEqual(hit['results'][0]['id'],'bridge-west')
  self.assertEqual(infra.feature_by_id('sites','bridge-west')['feature']['properties']['REGION'],'West')
  infra.mutate({'op':'category-hide','id':'bridges','mode':'offline','hidden':True})
  self.assertFalse(infra.search_features('Bridge Matched')['results'])
  infra.mutate({'op':'category-hide','id':'bridges','mode':'offline','hidden':False})
  self.assertTrue(infra.search_features('Bridge Matched')['results'])
  infra.mutate({'op':'layer-enable','id':'sites','enabled':False})
  self.assertFalse(infra.search_features('Bridge Matched')['results'])
  with self.assertRaises(ValueError):infra.feature_by_id('sites','bridge-west')
 def test_filter_error_validation_and_exact_selection(self):
  for spec in ({'enabled':True,'rules':[{'field':'SIZE','op':'javascript','value':'1'}]},
               {'enabled':True,'mode':'explode','rules':[]},
               {'enabled':True,'rules':[{'field':'','op':'=','value':'1'}]}):
   with self.assertRaises(ValueError):infra.mutate({'op':'layer-filter','id':'pipes','filter_spec':spec})
  infra.mutate({'op':'layer-filter','id':'pipes','filter_spec':{'enabled':True,'rules':[{'field':'PIPE_DIAMETER','op':'>=','value':'60'}]}})
  with self.assertRaisesRegex(ValueError,'filter'):infra.feature_by_id('pipes','main-48',36)
  self.assertEqual(infra.feature_by_id('pipes','main-100',36)['feature']['id'],'main-100')
 def test_symbol_identity_and_fields(self):
  self.assertIn('SPEED',infra.layer_fields('sites')['fields'])
  icon={'kind':'milstd2525c','sidc':'SFGPUCI----K---','label':'Test'}
  infra.mutate({'op':'layer-symbol','id':'sites','point_symbol_mode':'registry','point_symbol_ref':icon})
  self.assertEqual(next(x for x in infra.catalog()['layers'] if x['id']=='sites')['point_symbol_ref'],icon)
  with self.assertRaises(ValueError):infra.mutate({'op':'layer-symbol','id':'pipes','point_symbol_mode':'registry','point_symbol_ref':icon})
  infra.mutate({'op':'layer-symbol','id':'sites','point_symbol_mode':'dot'})
  self.assertIsNone(next(x for x in infra.catalog()['layers'] if x['id']=='sites')['point_symbol_ref'])
 def test_filtered_sampling_does_not_drop_rare_matches(self):
  with infra._db() as c:
   rows=[]
   for n in range(5500):
    rows.append({'type':'Feature','id':'s'+str(n),'geometry':{'type':'Point','coordinates':[-118.2+(n%30)/2000,34.1+(n//30)/2000]},'properties':{'SIZE':2,'NAME':'junk'}})
   rows.append({'type':'Feature','id':'rare','geometry':{'type':'Point','coordinates':[-118.2,34.1]},'properties':{'SIZE':100,'NAME':'Rare matching object'}})
   infra._write_features(c,'sites',rows)
  infra.mutate({'op':'layer-filter','id':'sites','filter_spec':{'enabled':True,'rules':[{'field':'SIZE','op':'>','value':'50'}]}})
  result=infra.get_features('sites','offline',[-119,33,-117,35],minimum=0)
  self.assertEqual(len(result['features']),1)
  self.assertEqual(result['features'][0]['id'],'rare')
  self.assertFalse(result['feature_cap_reached'])
  self.assertTrue(infra.search_features('Rare matching')['results'])
  self.assertEqual(len(infra._all_features('sites')[1]),5502)

if __name__=='__main__':unittest.main()
