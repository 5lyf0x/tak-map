#!/usr/bin/env python3
"""Tests authenticated storage isolation, revision conflicts and persistence."""
import sys,unittest,tempfile,json,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tak_map_user_basemap_i699 import BasemapPreferences,identity,normalize
class PreferenceTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.store=BasemapPreferences(self.tmp.name)
 def user(self,name,uid=''):
  return {'username':name,'auth_mode':'local-user','profile':{'tak_uid':uid}}
 def prefs(self,n):
  return {'order':['road','terrain','unavailable_import'], 'enabled':['terrain'], 'opacity':{'road':80},'blend':{'road':'multiply'},'tone':{'terrain':{'brightness':105,'contrast':115,'saturation':90}},'expanded':True, 'detail':{'road':{'strength':75,'threshold':65}} ,'n':n}
 def test_users_isolated(self):
  alice=self.user('Alice','UID-ALICE');bob=self.user('Bob','UID-BOB')
  saved=self.store.write(alice,0,self.prefs(1));self.assertEqual(saved['revision'],1)
  self.assertIsNone(self.store.read(bob)['preferences'])
  self.assertEqual(self.store.write(bob,0,self.prefs(2))['revision'],1)
  self.assertEqual(self.store.read(alice)['preferences']['blend']['road'],'multiply')
  self.assertNotEqual(identity(alice),identity(bob))
 def test_revision_conflict_not_overwritten(self):
  a=self.user('Alice','UID-ALICE');self.store.write(a,0,self.prefs(1))
  p=self.prefs(2);p['blend']['road']='screen'
  ok=self.store.write(a,1,p);self.assertTrue(ok['ok'])
  stale=self.store.write(a,1,self.prefs(1));self.assertTrue(stale['conflict'])
  self.assertEqual(self.store.read(a)['preferences']['blend']['road'],'screen')
 def test_atomic_file_and_reboot(self):
  a=self.user('Alice');self.store.write(a,0,self.prefs(1))
  p=Path(self.tmp.name)/'user_basemap_preferences_i699'/(identity(a)+'.json')
  self.assertEqual(os.stat(p).st_mode&0o777,0o600)
  self.assertEqual(BasemapPreferences(self.tmp.name).read(a)['preferences']['order'][-1],'unavailable_import')
 def test_validation(self):
  a=self.user('Alice')
  with self.assertRaises(ValueError):self.store.write(a,0,{'order':[]})
  with self.assertRaises(ValueError):self.store.write(a,False,self.prefs(1))
  data=normalize({'order':['a'],'enabled':['a'],'opacity':{'a':999},'blend':{'a':'bad'}})
  self.assertEqual(data['opacity']['a'],100);self.assertEqual(data['blend']['a'],'normal')
 def test_session_secrets_not_persisted(self):
  a={'username':'alice','auth_mode':'ots','password':'secretPW','token':'secretToken'}
  self.store.write(a,0,self.prefs(1))
  data=''.join(p.read_text() for p in (Path(self.tmp.name)/'user_basemap_preferences_i699').glob('*'))
  self.assertNotIn('secretPW',data);self.assertNotIn('secretToken',data);self.assertNotIn('alice',data)
if __name__=='__main__':unittest.main(verbosity=2)
