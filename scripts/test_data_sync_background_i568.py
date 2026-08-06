#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
DASH = ROOT / 'tak_dashboard.py'

with tempfile.TemporaryDirectory(prefix='tak-map-i568-background-') as data_dir:
    os.environ['TAK_DASHBOARD_DATA_DIR'] = data_dir
    spec = importlib.util.spec_from_file_location('tak_dashboard_i568_background_test', DASH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)

    assert mod.TAK_MAP_ITERATION == 'i568'
    cfg = {'api_url':'https://ots.example.test', 'base_url':'https://ots.example.test', 'marti_url':'https://ots.example.test:8443'}
    sess = {'auth_mode':'ots-user', 'username':'darktek', 'callsign':'raptor', 'profile':{'username':'darktek'}}

    calls = []
    def fake_request(cfg_arg, sess_arg, url, timeout=10):
        calls.append((url, timeout, time.monotonic()))
        time.sleep(0.12)
        if url.endswith('/api/missions') or url.endswith('/Marti/api/missions'):
            return {'ok':True, 'status':200, 'body':[{'name':'ALPHA'},{'name':'BRAVO'}], 'error':''}
        if url.endswith('/contents'):
            mission = 'ALPHA' if '/ALPHA/' in url else 'BRAVO'
            return {'ok':True, 'status':200, 'body':[{'uid':mission+'-P1','name':mission+' Point','lat':35.0,'lon':-117.0,'type':'a-f-G'}], 'error':''}
        if url.endswith('/cot'):
            return {'ok':True, 'status':200, 'body':[], 'error':''}
        return {'ok':True, 'status':200, 'body':{}, 'error':''}

    mod._i568_request_json_before = fake_request
    started = time.monotonic()
    acquired = mod._i568_parallel_acquisition(cfg, sess)
    elapsed = time.monotonic() - started
    # 2 discovery calls + 6 mission calls at 0.12s each would be ~0.96s serial.
    # Bounded parallelism should complete materially faster.
    assert elapsed < 0.65, elapsed
    assert acquired['summary']['discovery_ok'] is True
    assert acquired['summary']['mission_count'] == 2
    assert acquired['summary']['mission_endpoint_count'] == 6
    assert acquired['summary']['max_workers'] == 6
    assert all(timeout <= 5 for _url, timeout, _at in calls)

    key = mod._i568_state_key(cfg, sess)
    state = mod._i568_state(key)
    initial = mod._i568_response_payload(state)
    assert initial['initial_ots_refresh_in_progress'] is True
    assert initial['message'] == 'Initial OTS refresh in progress'
    assert initial['data_sync_background_i568']['state'] == 'initial-refresh-in-progress'
    assert initial['data_sync_background_i568']['snapshot_available'] is False

    original_builder = mod._i568_build_snapshot
    def successful_builder(cfg_arg, sess_arg, token, reason):
        time.sleep(0.18)
        snapshot = {
            'ok':True, 'version':'i568',
            'objects':[{'uid':'ALPHA-P1','name':'ALPHA Point','lat':35.0,'lon':-117.0}],
            'missions':[{'name':'ALPHA'}], 'mission_content':[], 'mission_uids':[{'uid':'ALPHA-P1'}],
        }
        acquired = {'timings':[{'endpoint':'discovery:ots-api','ok':True,'duration_seconds':0.1}], 'summary':{'discovery_ok':True,'mission_count':1}}
        return snapshot, acquired
    mod._i568_build_snapshot = successful_builder
    scheduled, reason = mod._i568_schedule_refresh(key, cfg, sess, 'token', 'startup', force=True)
    assert scheduled is True and reason == 'scheduled'
    immediate = mod._i568_response_payload(state)
    assert immediate['initial_ots_refresh_in_progress'] is True
    assert immediate['data_sync_background_i568']['refreshing'] is True
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        ready = mod._i568_response_payload(state)
        if ready.get('objects'):
            break
        time.sleep(0.03)
    assert ready['objects'][0]['uid'] == 'ALPHA-P1'
    assert ready['data_sync_background_i568']['state'] == 'ready'
    persisted = mod._i568_snapshot_path(key)
    assert persisted.is_file()

    # A temporary refresh failure must preserve the last successful snapshot.
    def failing_builder(cfg_arg, sess_arg, token, reason):
        time.sleep(0.08)
        raise RuntimeError('temporary OTS failure')
    mod._i568_build_snapshot = failing_builder
    scheduled, _ = mod._i568_schedule_refresh(key, cfg, sess, 'token', 'manual', force=True)
    assert scheduled is True
    while time.monotonic() < deadline + 3:
        with mod._I568_STATE_LOCK:
            if not state.get('in_flight'):
                break
        time.sleep(0.03)
    stale = mod._i568_response_payload(state)
    assert stale['objects'][0]['uid'] == 'ALPHA-P1'
    assert stale['data_sync_background_i568']['state'] == 'stale-last-known-good'
    assert 'temporary OTS failure' in stale['data_sync_background_i568']['last_error']
    assert stale['data_sync_background_i568']['last_known_good_preserved'] is True

    mod._i568_build_snapshot = original_builder

    # Installer and browser controller invariants.
    installer = (ROOT/'install.sh').read_text()
    control = (ROOT/'assets/tak-map-data-sync-i553.js').read_text()
    core = (ROOT/'assets/tak-map-core-i553.js').read_text()
    startup = (ROOT/'assets/tak-map-startup-i553.js').read_text()
    assert 'data_sync_snapshots_i568' in installer
    assert 'atak-compatibility-aliases-i553.json' in installer
    assert 'install -m 0644 VERSION "$APP_DIR/VERSION"' in installer
    assert 'automaticPollMs:300000' in control
    assert 'minIntervalMs:300000' in control
    assert 'Initial OTS refresh in progress' in control
    assert 'setInterval(refreshDataSyncInterval,300000)' in core
    assert 'tak-map-data-sync-i553.js?v=1.3.0-i568' in startup

print('i568 background Data Sync worker, immediate snapshot response, LKG preservation, five-minute polling, and alias install invariants pass')
