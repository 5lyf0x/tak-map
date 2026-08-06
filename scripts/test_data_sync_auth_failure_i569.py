#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, os, pathlib, sys, tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='tak-map-i569-auth-failure-') as td:
    os.environ['TAK_DASHBOARD_DATA_DIR']=td
    spec=importlib.util.spec_from_file_location('tak_dashboard_i569_auth_failure',ROOT/'tak_dashboard.py')
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;assert spec.loader;spec.loader.exec_module(m)
    cfg={'api_url':'https://ots.test','base_url':'https://ots.test','marti_url':'https://ots.test:8443'}
    sess={'auth_mode':'ots-user','username':'u','profile':{'username':'u'}}
    def denied(path,**kwargs):
        return {'ok':False,'status':428,'body':'','json':{},'error':'Per-user certificate unavailable','identity_mode':'per-user-enrolled-marti-certificate'}
    m._i569_mission_request=denied
    m._i568_set_context('TOKEN',sess)
    try:
        try: m._i568_build_snapshot(cfg,sess,'TOKEN','test')
        except RuntimeError as exc: message=str(exc)
        else: raise AssertionError('authentication failure was promoted as a snapshot')
    finally: m._i568_clear_context()
    assert 'Mission discovery did not complete successfully' in message or 'authentication failed' in message,message
print('i569 authentication failure cannot become a successful empty snapshot')
