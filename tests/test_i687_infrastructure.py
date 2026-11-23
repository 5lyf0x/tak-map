"""i687 mode-specific categories, min zoom, City source, and cap reasons."""
import os
import tempfile
import unittest
from pathlib import Path
import tak_map_infrastructure_i687 as infra
import tak_map_infrastructure_i686 as previous

class I687Infrastructure(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.prior=os.environ.get('TAK_MAP_INFRA_DIR')
  os.environ['TAK_MAP_INFRA_DIR']=self.tmp.name
 def tearDown(self):
  if self.prior is None:os.environ.pop('TAK_MAP_INFRA_DIR',None)
  else:os.environ['TAK_MAP_INFRA_DIR']=self.prior
  self.tmp.cleanup()
 def layer(self,key):return next(x for x in infra.catalog()['layers'] if x['id']==key)
 def category(self,key):return next(x for x in infra.catalog()['categories'] if x['id']==key)
 def test_legacy_migration_once_and_city_provider(self):
  previous.catalog()
  previous.mutate({'op':'category-hide','id':'water','hidden':True})
  previous.mutate({'op':'layer-color','id':'lacounty-sewer-manholes','color':'#ff1122'})
  previous.mutate({'op':'layer-enable','id':'lacounty-sewer-manholes','enabled':True})
  with previous._db() as c:
   c.execute("INSERT INTO layers(id,category_id,name,mode,enabled,kind) VALUES('stored','water','Stored','offline',1,'point')")
   previous._write_features(c,'stored',[{'type':'Feature','id':'a','geometry':{'type':'Point','coordinates':[-118.5,34.5]},'properties':{'Diameter':40}}])
  state=infra.catalog();self.assertEqual(state['version'],'i687')
  self.assertTrue(self.category('water')['hidden_online'])
  self.assertTrue(self.category('water')['hidden_offline'])
  self.assertEqual(self.layer('lacounty-sewer-manholes')['color'],'#ff1122')
  self.assertEqual(self.layer('lacounty-sewer-manholes')['min_zoom'],14)
  self.assertEqual(self.layer('lacounty-sewer-manholes')['enabled'],1)
  city=self.layer('lacity-sewer-structures')
  self.assertEqual(city['mode'],'online');self.assertEqual(city['category_id'],'water')
  self.assertEqual(city['min_zoom'],14);self.assertEqual(city['enabled'],0)
  self.assertIn('/MapServer/0',city['url'])
  infra.mutate({'op':'category-hide','id':'water','mode':'online','hidden':False})
  self.assertFalse(self.category('water')['hidden_online'])
  self.assertTrue(self.category('water')['hidden_offline'])
  self.assertEqual(infra.get_features('stored','offline',[-119,34,-118,35],0)['loaded_count'],1)
  infra.catalog();self.assertEqual(len([l for l in infra.catalog()['layers'] if l['id']=='lacity-sewer-structures']),1)
  self.assertFalse(self.category('water')['hidden_online'])
  self.assertTrue(self.category('water')['hidden_offline'])
 def test_hide_requires_mode_preserves_other_mode_and_custom(self):
  infra.catalog()
  for bad in (None,'both',''):
   with self.assertRaises(ValueError):infra.mutate({'op':'category-hide','id':'water','mode':bad,'hidden':True})
  custom=infra.mutate({'op':'category-create','name':'My Utilities'})
  key=next(x['id'] for x in custom['categories'] if x['label']=='My Utilities')
  infra.mutate({'op':'category-hide','id':key,'mode':'offline','hidden':True})
  self.assertFalse(self.category(key)['hidden_online'])
  self.assertTrue(self.category(key)['hidden_offline'])
  infra.mutate({'op':'category-hide','id':key,'mode':'offline','hidden':False})
  self.assertFalse(self.category(key)['hidden_offline'])
 def test_layer_zoom_validation_and_persistence(self):
  infra.catalog()
  for item in ('14',-1,23,14.3,True,{'zoom':14}):
   with self.assertRaises(ValueError):infra.mutate({'op':'layer-minzoom','id':'lacounty-sewer-manholes','min_zoom':item})
  infra.mutate({'op':'layer-minzoom','id':'lacounty-sewer-manholes','min_zoom':17})
  self.assertEqual(self.layer('lacounty-sewer-manholes')['min_zoom'],17)
  infra.catalog();self.assertEqual(self.layer('lacounty-sewer-manholes')['min_zoom'],17)
  infra.mutate({'op':'layer-minzoom','id':'lacounty-sewer-manholes','min_zoom':None})
  self.assertIsNone(self.layer('lacounty-sewer-manholes')['min_zoom'])
  infra.mutate({'op':'layer-minzoom','id':'lacity-sewer-structures','min_zoom':21})
  infra.catalog();self.assertEqual(self.layer('lacity-sewer-structures')['min_zoom'],21)
 def test_below_min_zoom_protects_online_provider_and_offline_data(self):
  infra.catalog()
  from unittest.mock import patch
  with patch.object(infra,'_query_online',side_effect=AssertionError('provider contacted')):
   result=infra.get_features('lacounty-sewer-manholes','online',[-119,34,-118,35],zoom=13)
   self.assertEqual(result['features'],[])
   self.assertTrue(result['below_min_zoom'])
  with patch.object(infra,'build_opener',side_effect=AssertionError('provider contacted')):
   count=infra.get_count('lacounty-sewer-manholes','online',[-119,34,-118,35],zoom=13)
   self.assertTrue(count['below_min_zoom']);self.assertEqual(count['count'],0)
  # Export and downloads are not subject to display zoom restriction.
  offline=infra.mutate({'op':'category-create','name':'Other'});
  self.assertEqual(self.layer('lacounty-sewer-manholes')['min_zoom'],14)
 def test_distinct_geometry_and_feature_status(self):
  p={'type':'Feature','id':'one','geometry':{'type':'LineString','coordinates':[[float(x)/1000-119,34] for x in range(600)]},'properties':{}}
  src={'name':'Geometry Test','mode':'offline'}
  r=infra._pack_view_features([p],src,[-120,33,-118,35]);self.assertFalse(r['feature_cap_reached']);self.assertTrue(r['geometry_simplified']);self.assertFalse(r['limited'])
  p={'type':'Feature','id':'single','geometry':{'type':'Point','coordinates':[-118.5,34.5]},'properties':{}}
  r=infra._pack_view_features([p],src,[-120,33,-118,35],True)
  self.assertTrue(r['feature_cap_reached']);self.assertTrue(r['limited']);self.assertFalse(r['geometry_simplified'])

if __name__=='__main__':unittest.main()
