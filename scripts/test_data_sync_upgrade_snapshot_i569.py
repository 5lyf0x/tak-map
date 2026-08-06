#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, json, os, pathlib, sys, tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='tak-map-i569-upgrade-') as td:
    os.environ['TAK_DASHBOARD_DATA_DIR']=td
    spec=importlib.util.spec_from_file_location('tak_dashboard_i569_upgrade',ROOT/'tak_dashboard.py')
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;assert spec.loader;spec.loader.exec_module(m)
    cfg={'api_url':'https://ots.test','marti_url':'https://ots.test:8443'}
    sess={'auth_mode':'ots-user','username':'darktek','profile':{'username':'darktek'}}
    key=m._i568_state_key(cfg,sess)
    path=m._i568_snapshot_path(key);path.parent.mkdir(parents=True,exist_ok=True)

    path.write_text(json.dumps({'version':'i568','last_success_epoch':123,'generation':1,'snapshot':{'ok':True,'version':'i568','objects':[],'missions':[],'mission_uids':[]}}))
    m._I568_STATES.clear();state=m._i568_state(key)
    assert state['snapshot'] is None,state
    assert state['last_success_epoch']==0,state
    assert 'Discarded the failed empty i568 snapshot' in state['last_error'],state

    path.write_text(json.dumps({'version':'i568','last_success_epoch':123,'generation':2,'snapshot':{'ok':True,'version':'i568','objects':[{'uid':'OLD'}],'missions':[{'name':'M'}],'mission_uids':[{'uid':'OLD'}]}}))
    m._I568_STATES.clear();state=m._i568_state(key)
    assert state['snapshot']['objects'][0]['uid']=='OLD',state
    assert state['last_success_epoch']==0,state
    assert 'preserved pre-i569 snapshot' in state['last_error'],state

    path.write_text(json.dumps({'version':'i569','last_success_epoch':456,'generation':3,'snapshot':{'ok':True,'version':'i569','objects':[{'uid':'NEW'}],'data_sync_background_worker_i569':{'version':'i569'}}}))
    m._I568_STATES.clear();state=m._i568_state(key)
    assert state['snapshot']['objects'][0]['uid']=='NEW',state
    assert state['last_success_epoch']==456,state
print('i569 upgrade invalidates failed empty i568 snapshots and preserves nonempty LKG data')
