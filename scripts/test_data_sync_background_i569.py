#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, os, pathlib, sys, tempfile, time
ROOT=pathlib.Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='tak-map-i569-background-') as td:
    os.environ['TAK_DASHBOARD_DATA_DIR']=td
    spec=importlib.util.spec_from_file_location('tak_dashboard_i569_background',ROOT/'tak_dashboard.py')
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;assert spec.loader;spec.loader.exec_module(m)
    assert m.TAK_MAP_ITERATION=='i569'
    cfg={'api_url':'https://ots.test','base_url':'https://ots.test','marti_url':'https://ots.test:8443'}
    sess={'auth_mode':'ots-user','username':'u','callsign':'U','profile':{'username':'u'}}
    key=m._i568_state_key(cfg,sess); state=m._i568_state(key)
    initial=m._i568_response_payload(state)
    assert initial['version']=='i569' and initial['initial_ots_refresh_in_progress'] is True
    assert initial['data_sync_background_i569']['state']=='initial-refresh-in-progress'
    def good(cfg_arg,sess_arg,token,reason):
        time.sleep(.12)
        return ({'ok':True,'version':'i569','objects':[{'uid':'P1','lat':1,'lon':2}],'missions':[{'name':'M'}],'mission_content':[],'mission_uids':[{'uid':'P1'}],'data_sync_background_worker_i569':{'version':'i569'}},{'timings':[],'summary':{'version':'i569','discovery_ok':True,'mission_count':1}})
    m._i568_build_snapshot=good
    ok,why=m._i568_schedule_refresh(key,cfg,sess,'TOKEN','startup',force=True);assert ok and why=='scheduled'
    immediate=m._i568_response_payload(state);assert immediate['initial_ots_refresh_in_progress'] is True
    deadline=time.monotonic()+3
    while time.monotonic()<deadline:
        ready=m._i568_response_payload(state)
        if ready.get('objects'): break
        time.sleep(.02)
    assert ready['objects'][0]['uid']=='P1'
    assert ready['data_sync_background_i569']['state']=='ready'
    assert m._i568_snapshot_path(key).is_file()
    def bad(*args,**kwargs):
        time.sleep(.05);raise RuntimeError('temporary OTS failure')
    m._i568_build_snapshot=bad
    ok,_=m._i568_schedule_refresh(key,cfg,sess,'TOKEN','manual',force=True);assert ok
    while time.monotonic()<deadline+3:
        with m._I568_STATE_LOCK:
            if not state.get('in_flight'): break
        time.sleep(.02)
    stale=m._i568_response_payload(state)
    assert stale['objects'][0]['uid']=='P1'
    assert stale['data_sync_background_i569']['state']=='stale-last-known-good'
    assert 'temporary OTS failure' in stale['data_sync_background_i569']['last_error']
    control=(ROOT/'assets/tak-map-data-sync-i553.js').read_text(); core=(ROOT/'assets/tak-map-core-i553.js').read_text(); startup=(ROOT/'assets/tak-map-startup-i553.js').read_text(); installer=(ROOT/'install.sh').read_text()
    assert "const V='i569'" in control and 'automaticPollMs:300000' in control and 'minIntervalMs:300000' in control
    assert 'data_sync_background_i569' in control and 'Initial OTS refresh in progress' in control
    assert 'setInterval(refreshDataSyncInterval,300000)' in core
    assert 'tak-map-data-sync-i553.js?v=1.3.0-i569' in startup
    assert 'tak-map-icon-registry-i569.js' in installer and 'atak-compatibility-aliases-i553.json' in installer
print('i569 immediate background state, LKG preservation, five-minute polling, and install invariants passed')
