#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import pathlib
import sys
import tempfile
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('tak_dashboard_i583_corroboration', ROOT / 'tak_dashboard.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader is not None
spec.loader.exec_module(mod)

assert mod.TAK_MAP_ITERATION == 'i583'
assert mod._I583_MEMBERSHIP_INTERVAL_SECONDS == 10
assert mod._I583_FULL_COT_INTERVAL_SECONDS == 20

snapshot_root = pathlib.Path(tempfile.mkdtemp(prefix='takmap-i583-snapshots-'))
mod._I568_SNAPSHOT_ROOT = snapshot_root
mod._I568_STATES.clear()

cfg = {'marti_url': 'https://ots.example:8443', 'api_url': 'https://ots.example'}
sess = {'auth_mode': 'ots-user', 'username': 'tester', 'profile': {'username': 'tester'}}
key = mod._i568_state_key(cfg, sess)

scenario = {
    'rows': [],
    'payload_complete': True,
    'cot': {},
}
publish_history = []


def marker(uid: str, mission: str) -> dict:
    offset = sum(ord(ch) for ch in uid) % 20
    return {
        'uid': uid,
        'event_uid': uid,
        'mission': mission,
        'mission_name': mission,
        'callsign': uid,
        'name': uid,
        'lat': 34.0 + offset / 1000,
        'lon': -118.0 - offset / 1000,
        'cot_type': 'a-f-G',
        'source': 'OpenTAKServer MissionUID i583 test',
        'kind': 'datasync',
        'is_mission_object': True,
    }


def uid_from_raw(raw):
    if isinstance(raw, str):
        return raw
    if isinstance(raw, dict):
        return str(raw.get('data') or raw.get('uid') or raw.get('event_uid') or '')
    return ''


def fake_build_snapshot(cfg, sess, token, reason):
    rows = [mod._i568_clone(row) for row in scenario['rows']]
    mission_uids = []
    objects = []
    for row in rows:
        mission = str(row.get('name') or '')
        if isinstance(row.get('uids'), list):
            for raw in row['uids']:
                uid = uid_from_raw(raw)
                if uid:
                    item = marker(uid, mission)
                    mission_uids.append(item)
                    objects.append(dict(item))
    payload = {'version': 3, 'type': 'Mission'}
    if scenario['payload_complete']:
        payload['data'] = mod._i568_clone(rows)
    discovery_url = cfg['marti_url'] + mod._I569_DISCOVERY_PATH
    acquired = {
        'responses': {
            discovery_url: {'ok': True, 'status': 200, 'json': payload, 'body': payload, 'error': ''},
        },
        'mission_names': [str(row.get('name') or '') for row in rows],
        'mission_rows': rows,
        'timings': [],
        'summary': {
            'version': 'i583', 'phase': 'discovery', 'discovery_ok': True,
            'mission_count': len(rows),
        },
    }
    snapshot = {
        'ok': True,
        'version': 'i583',
        'missions': rows,
        'mission_uids': mission_uids,
        'mission_content': [],
        'objects': objects,
    }
    return snapshot, acquired


def fake_call(cfg, sess, token, url, path, label, timeout):
    mission = path.split('/missions/', 1)[1].rsplit('/cot', 1)[0]
    from urllib.parse import unquote
    mission = unquote(mission)
    body = scenario['cot'].get(mission, '<events/>')
    result = {'ok': True, 'status': 200, 'body': body, 'json': {}, 'error': ''}
    timing = {'endpoint': label, 'url_path': path, 'ok': True, 'status': 200, 'duration_seconds': 0.001, 'error': ''}
    return url, result, timing


def fake_build_from_acquired(cfg, sess, acquired, previous=None, phase='enrichment'):
    out = mod._i568_clone(previous or {})
    rows = []
    for mission_row in acquired.get('mission_rows') or []:
        mission = str(mission_row.get('name') or '')
        path = '/Marti/api/missions/' + mission + '/cot'
        result = None
        for url, value in (acquired.get('responses') or {}).items():
            if str(url).endswith(path):
                result = value
                break
        if not result:
            continue
        body = result.get('body') or ''
        try:
            root = ET.fromstring(str(body))
            for event in root.iter():
                if str(event.tag).split('}')[-1].lower() == 'event' and event.attrib.get('uid'):
                    rows.append(marker(event.attrib['uid'], mission))
        except Exception:
            pass
    # Keep non-mission rows from the current snapshot; the i583 reconciler will
    # decide which prior mission rows remain authoritative.
    out['objects'] = [row for row in out.get('objects', []) if not (isinstance(row, dict) and row.get('mission'))] + rows
    out['mission_uids'] = [dict(row) for row in rows]
    out['version'] = 'i583'
    return out


mod._i568_build_snapshot = fake_build_snapshot
mod._i569_call = fake_call
mod._i570_build_from_acquired = fake_build_from_acquired
mod._i568_set_context = lambda token, sess: None
mod._i568_clear_context = lambda: None

original_publish = mod._i582_publish_state

def recording_publish(*args, **kwargs):
    snapshot = args[2]
    publish_history.append({
        'phase': args[4],
        'uids': sorted(row.get('uid') for row in snapshot.get('objects', []) if isinstance(row, dict) and row.get('uid')),
    })
    return original_publish(*args, **kwargs)

mod._i582_publish_state = recording_publish


def set_rows(definitions):
    scenario['rows'] = []
    for mission, uids_state in definitions:
        row = {'name': mission, 'passwordProtected': False, 'contents': []}
        if uids_state != 'MISSING':
            row['uids'] = uids_state
        scenario['rows'].append(row)


def cot_xml(uids):
    return '<events>' + ''.join(f'<event uid="{uid}" type="a-f-G"><point lat="34" lon="-118"/></event>' for uid in uids) + '</events>'


def run_worker(generation: int, full: bool, reason: str):
    publish_history.clear()
    state = mod._i568_state(key)
    with mod._I568_STATE_LOCK:
        state['generation'] = generation
        state['in_flight'] = True
        state['i581_requested_full'] = full
        state['i581_requested_mode'] = 'membership-and-full-cot' if full else 'membership-only'
    mod._i568_refresh_worker(key, cfg, sess, 'TOKEN', reason, generation)
    return mod._i568_state(key)

# Initial complete snapshot.
set_rows([('ALPHA', [{'data': 'A'}, {'data': 'B'}, {'data': 'C'}])])
scenario['cot'] = {'ALPHA': cot_xml(['A', 'B', 'C'])}
state = run_worker(1, True, 'initial')
assert {row['uid'] for row in state['snapshot']['objects']} == {'A', 'B', 'C'}

# Exact live regression: two points deleted, Manual Refresh, one remains. No
# intermediate or final publish may become empty.
set_rows([('ALPHA', [{'data': 'A'}])])
scenario['cot'] = {'ALPHA': cot_xml(['A'])}
state = run_worker(2, True, 'manual-partial-delete')
assert {row['uid'] for row in state['snapshot']['objects']} == {'A'}
assert publish_history and all(row['uids'] == ['A'] for row in publish_history), publish_history

# Successful response with missing uids is incomplete and cannot prune A.
set_rows([('ALPHA', 'MISSING')])
scenario['cot'] = {}
state = run_worker(3, False, 'missing-uids')
assert {row['uid'] for row in state['snapshot']['objects']} == {'A'}
assert state['snapshot']['data_sync_membership_corroboration_i582']['mission_decisions']['alpha'] == 'preserved-incomplete-membership'

# A temporary first empty read preserves A. The second complete empty read is
# sufficient corroboration when no full CoT request is in this worker.
set_rows([('ALPHA', [])])
state = run_worker(4, False, 'empty-first')
assert {row['uid'] for row in state['snapshot']['objects']} == {'A'}
state = run_worker(5, False, 'empty-second')
assert state['snapshot']['objects'] == []

# Restore A and record one empty membership-only candidate. A following
# Manual Refresh is the second complete read, but still must not publish an
# empty intermediate before its mandatory full /cot result.
set_rows([('ALPHA', [{'data': 'A'}])])
scenario['cot'] = {'ALPHA': cot_xml(['A'])}
state = run_worker(6, True, 'restore-before-second-read-manual')
set_rows([('ALPHA', [])])
state = run_worker(7, False, 'first-empty-before-manual')
assert {row['uid'] for row in state['snapshot']['objects']} == {'A'}
scenario['cot'] = {'ALPHA': '<events/>'}
state = run_worker(8, True, 'second-empty-manual')
assert publish_history[0]['uids'] == ['A'], publish_history
assert publish_history[-1]['uids'] == [], publish_history

# Restore A, then prove Manual Refresh keeps A visible while a first empty
# discovery is corrected by /cot.
set_rows([('ALPHA', [{'data': 'A'}])])
scenario['cot'] = {'ALPHA': cot_xml(['A'])}
state = run_worker(9, True, 'restore-a')
set_rows([('ALPHA', [])])
scenario['cot'] = {'ALPHA': cot_xml(['A'])}
state = run_worker(10, True, 'manual-empty-but-cot-has-a')
assert {row['uid'] for row in state['snapshot']['objects']} == {'A'}
assert publish_history[0]['uids'] == ['A'] and publish_history[-1]['uids'] == ['A'], publish_history

# A true all-deleted Mission is cleared after successful empty /cot, but only
# after the initial preserved membership publish.
set_rows([('ALPHA', [])])
scenario['cot'] = {'ALPHA': '<events/>'}
state = run_worker(11, True, 'manual-all-deleted')
assert publish_history[0]['uids'] == ['A'], publish_history
assert publish_history[-1]['uids'] == [], publish_history
assert state['snapshot']['objects'] == []

# Multi-mission isolation: ALPHA malformed membership is preserved while BETA's
# exact partial deletion is applied.
set_rows([('ALPHA', [{'data': 'A'}]), ('BETA', [{'data': 'X'}, {'data': 'Y'}])])
scenario['cot'] = {'ALPHA': cot_xml(['A']), 'BETA': cot_xml(['X', 'Y'])}
state = run_worker(12, True, 'seed-multi')
set_rows([('ALPHA', 'MISSING'), ('BETA', [{'data': 'X'}])])
scenario['cot'] = {}
state = run_worker(13, False, 'multi-isolation')
assert {row['uid'] for row in state['snapshot']['objects']} == {'A', 'X'}

# A structurally incomplete successful global discovery cannot erase missions.
scenario['payload_complete'] = False
set_rows([])
state = run_worker(14, False, 'global-incomplete-success')
assert {row['uid'] for row in state['snapshot']['objects']} == {'A', 'X'}
scenario['payload_complete'] = True

print('i583 incomplete-success, partial deletion, empty corroboration, manual refresh, and multi-mission isolation tests passed')
