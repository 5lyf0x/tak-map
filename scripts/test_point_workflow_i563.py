#!/usr/bin/env python3
from __future__ import annotations

import os

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / 'assets' / 'tak-map-icon-registry-i563.js').read_text(encoding='utf-8')

# Approved point sidebar information and shared editor.
for token in (
    'point-info-popup-i556', 'point-popup-stage-i556', 'point-popup-edit-i556',
    "popupRow('Affiliation'", "popupLocationRow(location)", "popupRow('Mission'",
    "popupRow('Source'", "popupRow('Added', added, 'point-popup-time-i563')",
    "popupRow('Updated', updated, 'point-popup-time-i563')", "popupSyncRow(sync)", "popupRow('Notes'",
    'function dateAgeText(value)', 'function elapsedAge(date)', 'function displayLocation(lat, lon)',
    'data-point-copy-location="1"', 'point-popup-sync-i563',
    "modal.id = 'takMapPointEditorI556'", 'Reset Changes', 'Save Changes',
    "window.openDataSyncItemEdit = sidebarEditor", "openEditor(objectUid(object), objectMission(object), 'datasync')",
    "window.openLocalPointEditI556", 'data-point-source="local"',
):
    assert token in JS, token
assert "popupRow(path ? 'Icon Path' : 'SIDC'" not in JS
assert "popupRow('UID'" not in JS
assert "function ensureOtsIdentity(force)" in JS
assert "Data Sync: OpenTAKServer" in JS
assert "/api/tak-map/ots/source-identity" in JS
assert 'rgba(255,111,46' not in JS
assert 'pointColorInput' not in JS
assert 'type="color"' not in JS

# Create Point stays inside the actual map viewport, not browser coordinates.
for token in (
    'function mapViewportRect()', "byId('map')", 'function positionCreatePanel()',
    'Math.max(rect.left + margin', 'Math.min(left, rect.right - measured.width - margin)',
    "window.addEventListener('resize', schedule", 'watchCreatePanelViewport()',
):
    assert token in JS, token

# The custom renderer must win before MIL fallback and be reasserted after the
# older deferred MIL runtime patches have finished.
assert "function customIconHtml(object)" in JS
assert "if (custom) return custom;" in JS
assert "window.mil2525IconHtml = authoritativeMilIconHtml" in JS
assert "window.dataSyncIcon = authoritativeDataSyncIcon" in JS
assert '[120,300,700,1200,2500,5200,8000]' in JS
assert "setInterval(reassert, 12000)" in JS
assert "redrawPointLayers('registry-ready')" in JS

# i563 moves point details/editing into one authoritative contextual sidebar.
for token in (
    "window.TakMapIconRegistryI563 = publicApiI563",
    "ensureCreatePanel,",
    "panel.dataset.takMapLoadedI563 = '1'",
    "window.TakMapContextSidebarI563",
    "controller.onPointEditorOpening",
    "controller.onPointEditorClosed",
    "controller.onPointSaved",
    "controller.bindObjectLayer",
):
    assert token in JS, token
assert 'confirm(' not in JS

spec = importlib.util.spec_from_file_location('tak_map_i563_point_test', ROOT / 'tak_dashboard.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader
spec.loader.exec_module(mod)

sample_path = '34ae1613-9645-4222-a9d2-e5f243dea2865/Animals/ant.png'
assert sample_path in mod._i555_registry_load()['by_path']

with tempfile.TemporaryDirectory(prefix='tak-i556-local-') as td:
    folder = Path(td)
    mod.TAK_MAP_IMPORT_DIR = folder
    mod.TAK_MAP_IMPORT_FILE = folder / 'imports.json'
    original = {
        'imports': [{
            'id': 'localset01',
            'name': 'Point Tool Objects',
            'uploaded': '2026-07-27T00:00:00Z',
            'features': [{
                'kind': 'point', 'geometry': 'point', 'name': 'Local Infantry',
                'lat': 34.1, 'lon': -118.2, 'coords': [[34.1, -118.2]],
                'source': 'TAK Map Point Tool i556',
                'properties': {
                    'name': 'Local Infantry', 'callsign': 'Local Infantry',
                    'notes': 'before', 'remarks': 'before',
                    'cot_type': 'a-f-G-U-C-I', 'type': 'a-f-G-U-C-I',
                    'sidc': 'SFGPUCI--------', 'icon_mode': 'milstd2525c',
                },
            }],
        }],
    }
    folder.mkdir(parents=True, exist_ok=True)
    mod.atomic_write_json(mod.TAK_MAP_IMPORT_FILE, original)

    record = mod._i556_find_local_point('localset01:0')
    assert record
    public = mod._i556_local_public(record)
    assert public['local_id'] == 'localset01:0'
    assert public['name'] == 'Local Infantry'
    assert public['symbol_locked'] is False

    payload = {
        'local_id': public['local_id'],
        'expected_fingerprint': public['fingerprint'],
        'name': 'Local Ant', 'notes': 'after',
        'lat': 34.234567, 'lon': -118.345678,
        'affiliation': 'hostile',
        'symbol': {'kind': 'custom', 'iconsetpath': sample_path},
    }
    reply, status = mod._i556_save_local_point(payload)
    assert status == 200 and reply['ok'], reply
    saved = reply['point']
    assert saved['name'] == 'Local Ant'
    assert saved['lat'] == 34.234567 and saved['lon'] == -118.345678
    assert saved['iconsetpath'] == sample_path
    assert saved['registered_custom_icon'] is True
    assert saved['symbol_locked'] is False
    assert saved['cot_type'] == 'a-h-G'

    raw = json.loads(mod.TAK_MAP_IMPORT_FILE.read_text())
    feature = raw['imports'][0]['features'][0]
    props = feature['properties']
    assert feature['coords'] == [[34.234567, -118.345678]]
    assert props['iconsetpath'] == sample_path
    assert props['icon_mode'] == 'custom-registry'
    assert props['cot_type'] == 'a-h-G'
    assert props['notes'] == 'after'

    stale = dict(payload)
    stale['name'] = 'Must Not Overwrite'
    stale_reply, stale_status = mod._i556_save_local_point(stale)
    assert stale_status == 409 and stale_reply['concurrent_edit'] is True
    raw_after = json.loads(mod.TAK_MAP_IMPORT_FILE.read_text())
    assert raw_after['imports'][0]['features'][0]['name'] == 'Local Ant'

print('i563 contextual point information/editor, Save Point reconstruction, custom renderer, and Local Data persistence checks passed')
sys.stdout.flush()
os._exit(0)
