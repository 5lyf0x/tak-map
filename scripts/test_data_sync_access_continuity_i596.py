#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, os, pathlib, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
os.environ['TAK_MAP_DATA_DIR'] = tempfile.mkdtemp(prefix='tak-map-i596-access-')
os.environ['TAK_MAP_MIL_ROOT'] = str(ROOT / 'assets/mil2525')
os.environ['TAK_MAP_TEST_SKIP_ADSB_WARMUP'] = '1'
spec = importlib.util.spec_from_file_location('tak_dashboard_i596_access', ROOT / 'tak_dashboard.py')
mod = importlib.util.module_from_spec(spec); sys.modules[spec.name] = mod; spec.loader.exec_module(mod)
assert mod.tak_map_config()['version'] == '1.3.0-i598'

mission = 'PROTECTED-ALPHA'
unlocked = {'mission': mission, 'protected': True, 'password_protected': True, 'unlocked': True, 'locked': False}
locked = {'mission': mission, 'protected': True, 'password_protected': True, 'unlocked': False, 'locked': True}

# Reproduce i595: the current-generation array exists but is empty, while the
# final security filter has produced the authoritative older array.
def before_unlocked(payload, state, sess=None):
    return ({'ok': True, 'missions': [], 'objects': [], 'packages': [], 'mission_content': [],
             'mission_access_i595': [], 'mission_access_i594': [unlocked]}, 200)
mod._i596_filter_before = before_unlocked
out, status = mod._i594_filter_security_view({}, {}, {})
assert status == 200
assert out['mission_access_i596'][0]['mission'] == mission
assert out['mission_access_i595'][0]['mission'] == mission
assert out['missions'][0]['name'] == mission
assert out['missions'][0]['metadata_only'] is True
assert out['mission_access_i596'][0]['refreshing_contents_i596'] is True
assert out['data_sync_transition_i596']['refreshing_contents'] is True

# Locked Missions remain visible without exposing content.
def before_locked(payload, state, sess=None):
    return ({'ok': True, 'locked': True, 'requires_mission_password': True,
             'missions': [], 'objects': [], 'packages': [], 'mission_content': [],
             'mission_access_i595': [], 'mission_access_i594': [locked]}, 200)
mod._i596_filter_before = before_locked
out, status = mod._i594_filter_security_view({}, {}, {})
assert status == 200
assert out['missions'][0]['name'] == mission
assert out['missions'][0]['locked'] is True
assert out['mission_access_i596'][0]['refreshing_contents_i596'] is False
assert out['objects'] == [] and out['packages'] == []

# Once the authoritative Mission row and objects arrive, refreshing clears.
def before_ready(payload, state, sess=None):
    return ({'ok': True, 'missions': [{'name': mission, 'passwordProtected': True}],
             'objects': [{'mission_name': mission, 'uid': 'POINT-1'}], 'packages': [], 'mission_content': [],
             'mission_access_i595': [], 'mission_access_i594': [unlocked]}, 200)
mod._i596_filter_before = before_ready
out, status = mod._i594_filter_security_view({}, {}, {})
assert status == 200
assert len(out['missions']) == 1
assert out['mission_access_i596'][0]['refreshing_contents_i596'] is False
assert out['objects'][0]['uid'] == 'POINT-1'
print('i596 Data Sync access continuity backend regression passed')
