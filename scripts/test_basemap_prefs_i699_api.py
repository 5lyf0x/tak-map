#!/usr/bin/env python3
"""Authenticated i699 HTTP handler paths, data isolation and conflict status."""
import sys,tempfile
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import tak_dashboard as d
from tak_map_user_basemap_i699 import BasemapPreferences
class Fake:
 def __init__(self,user='alice',auth=True):
  self.path='/api/tak-map/basemap-stack-i699';self.user=user;self.auth=auth;self.result=None
 def _tak_map_auth_ok(self):return self.auth
 def _tak_map_session(self):return {'username':self.user,'auth_mode':'local-user'}
 def _send_json(self,reply,status=200,headers=None):self.result=(status,reply);return self.result
 def _require_tak_map_login(self):self.result=(401,{});return self.result
with tempfile.TemporaryDirectory() as tmp:
 d._USER_BASEMAP_I699=BasemapPreferences(tmp)
 a=Fake();b=Fake('bob')
 assert d._i699_basemap_get(a)[1]['preferences'] is None
 assert d._i699_basemap_get(Fake(auth=False))[0]==401
 original=d._read_json_body
 try:
  d._read_json_body=lambda handler:{'revision':0,'preferences':{'order':['road'],'enabled':['road'],'blend':{'road':'multiply'}}}
  assert d._i699_basemap_post(a)[0]==200
  assert d._i699_basemap_get(b)[1]['preferences'] is None
  assert d._i699_basemap_post(a)[0]==409
  assert d._i699_basemap_get(a)[1]['preferences']['blend']['road']=='multiply'
  assert d._i699_basemap_post(Fake(auth=False))[0]==401
 finally:d._read_json_body=original
 print('PASS authenticated GET/POST + server data isolation + conflict 409 + unauthorized 401')
