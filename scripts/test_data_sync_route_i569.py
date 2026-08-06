#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
import pathlib
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
DASH = ROOT / 'tak_dashboard.py'

with tempfile.TemporaryDirectory(prefix='tak-map-i569-route-') as data_dir:
    os.environ['TAK_DASHBOARD_DATA_DIR'] = data_dir
    spec = importlib.util.spec_from_file_location('tak_dashboard_i569_route_test', DASH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)

    cfg = {
        'enabled': True,
        'login_enabled': True,
        'api_url': 'https://ots.route.test',
        'base_url': 'https://ots.route.test',
        'marti_url': 'https://ots.route.test:8443',
    }
    sess = {
        'auth_mode': 'ots-user',
        'username': 'route-user',
        'callsign': 'ROUTE',
        'profile': {'username': 'route-user'},
    }
    mod._i509_load_ots_config = lambda: dict(cfg)

    class FakeHandler(mod.Handler):
        def __init__(self, path: str):
            self.path = path
            self.sent = None
        def _tak_map_auth_ok(self): return True
        def _tak_map_session(self): return dict(sess)
        def _tak_map_token(self): return 'test-session-token'
        def _require_tak_map_login(self):
            raise AssertionError('unexpected login requirement')
        def _send_json(self, payload, status=200, headers=None):
            self.sent = (payload, status, headers)
            return payload

    build_calls = []
    def successful_builder(cfg_arg, sess_arg, token, reason):
        build_calls.append((reason, time.monotonic()))
        time.sleep(0.22)
        return ({
            'ok': True,
            'version': 'i569',
            'objects': [{'uid': 'ROUTE-P1', 'callsign': 'ROUTE-P1', 'lat': 34.1, 'lon': -117.2}],
            'missions': [{'name': 'ROUTE-MISSION'}],
            'mission_content': [],
            'mission_uids': [{'uid': 'ROUTE-P1'}],
        }, {
            'timings': [{'endpoint': 'mission:ROUTE-MISSION:cot', 'ok': True, 'duration_seconds': 0.1}],
            'summary': {'version': 'i569', 'discovery_ok': True, 'mission_count': 1},
        })
    mod._i568_build_snapshot = successful_builder

    first = FakeHandler('/api/tak-map/data-sync?reason=startup')
    started = time.monotonic()
    payload = first.do_GET()
    elapsed = time.monotonic() - started
    assert elapsed < 0.10, elapsed
    assert payload['message'] == 'Initial OTS refresh in progress', payload
    assert payload['initial_ots_refresh_in_progress'] is True
    assert payload['data_sync_background_i569']['browser_route_blocks_on_ots'] is False

    key = mod._i568_state_key(cfg, sess)
    state = mod._i568_state(key)
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        with mod._I568_STATE_LOCK:
            if state.get('snapshot') and not state.get('in_flight'):
                break
        time.sleep(0.02)
    else:
        raise AssertionError('background worker did not publish the initial snapshot')

    second = FakeHandler('/api/tak-map/data-sync?reason=interval')
    started = time.monotonic()
    ready = second.do_GET()
    elapsed = time.monotonic() - started
    assert elapsed < 0.10, elapsed
    assert [row['uid'] for row in ready['objects']] == ['ROUTE-P1']
    assert ready['data_sync_background_i569']['state'] == 'ready'

    # Manual force schedules work but returns the last-known-good snapshot immediately.
    def failing_builder(cfg_arg, sess_arg, token, reason):
        build_calls.append((reason, time.monotonic()))
        time.sleep(0.20)
        raise RuntimeError('temporary mission endpoint failure')
    mod._i568_build_snapshot = failing_builder
    forced = FakeHandler('/api/tak-map/data-sync?force=1&reason=manual')
    started = time.monotonic()
    during = forced.do_GET()
    elapsed = time.monotonic() - started
    assert elapsed < 0.10, elapsed
    assert [row['uid'] for row in during['objects']] == ['ROUTE-P1']
    assert during['data_sync_background_i569']['state'] == 'refreshing-last-known-good'

    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        with mod._I568_STATE_LOCK:
            if not state.get('in_flight'):
                break
        time.sleep(0.02)
    after = FakeHandler('/api/tak-map/data-sync?reason=interval').do_GET()
    assert [row['uid'] for row in after['objects']] == ['ROUTE-P1']
    assert after['data_sync_background_i569']['state'] == 'stale-last-known-good'
    assert 'temporary mission endpoint failure' in after['data_sync_background_i569']['last_error']
    assert len(build_calls) == 2, build_calls

print('i569 browser-facing Data Sync route returns immediately, publishes background snapshots, and preserves LKG through forced refresh failures')
