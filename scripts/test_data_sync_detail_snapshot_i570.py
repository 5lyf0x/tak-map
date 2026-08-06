#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, os, pathlib, sys, tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='tak-map-i570-detail-') as td:
    os.environ['TAK_DASHBOARD_DATA_DIR']=td
    spec=importlib.util.spec_from_file_location('tak_dashboard_i570_detail',ROOT/'tak_dashboard.py')
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;assert spec.loader;spec.loader.exec_module(m)
    cfg={'api_url':'https://ots.test','base_url':'https://ots.test','marti_url':'https://ots.test:8443'}
    sess={'auth_mode':'ots-user','username':'darktek','callsign':'raptor','tak_uid':'ANDROID-darktek','profile':{'username':'darktek','tak_uid':'ANDROID-darktek'}}
    m._i509_load_ots_config=lambda:cfg
    m._i568_set_context('SESSION',sess)
    try:
        key=m._i568_state_key(cfg,sess)
        state=m._i568_state(key)
        point={'uid':'DS-P10','event_uid':'DS-P10','mission':'Mission One','mission_name':'Mission One','name':'DS-P10','callsign':'DS-P10','lat':34.1001,'lon':-117.2002,'cot_type':'a-f-G-E-V-A','kind':'datasync'}
        with m._I568_STATE_LOCK:
            state['snapshot']={'ok':True,'version':'i570','objects':[point],'mission_uids':[dict(point)]}
            state['in_flight']=True
        def forbidden(*args,**kwargs):
            raise AssertionError('point detail attempted a synchronous Data Sync acquisition')
        m._tak_fresh_data_sync_result=forbidden
        m._i568_build_snapshot=forbidden
        row=m._i555_find_point('DS-P10','Mission One',True)
        assert row and row['lat']==34.1001,row
        assert m._i555_find_point('MISSING','Mission One',True) is None
        assert m.tak_map_config()['data_sync_background_i570']['point_detail_snapshot_only'] is True
    finally:
        m._i568_clear_context()
print('i570 point detail reads the per-user background snapshot without synchronous refresh')
