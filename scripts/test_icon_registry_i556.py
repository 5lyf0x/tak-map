#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_DIR = ROOT / 'assets' / 'icon-registry'
MANIFEST_PATH = REGISTRY_DIR / 'icon-registry.json'


def load_module():
    spec = importlib.util.spec_from_file_location('tak_map_i556_registry_test', ROOT / 'tak_dashboard.py')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader
    spec.loader.exec_module(module)
    return module


manifest = json.loads(MANIFEST_PATH.read_text(encoding='utf-8'))
assert manifest['schema_version'] == 1
assert manifest['tak_map_version'] == '1.3.0-i556'
assert manifest['read_only'] is True
assert manifest['milstd2525c']['authoritative'] is True
assert manifest['custom_set_count'] == 10
assert manifest['custom_icon_count'] == 3742
assert len(manifest['sets']) == 10
assert len(manifest['icons']) == 3742
assert {row['name'] for row in manifest['sets']} == {
    'Default', 'Public Safety Air', 'FalconView', 'OSM', 'GeoOps',
    'Generic Icons', 'Incident Management Icons', 'Responder Icons',
    'Google', 'FEMA Icons',
}
assert all(row['uid'] != 'Unknown-Iconset' for row in manifest['sets'])
assert all(row['iconset_uid'] != 'Unknown-Iconset' for row in manifest['icons'])
assert manifest['excluded_sets'] == [{
    'uid': 'Unknown-Iconset',
    'name': 'Unnamed Icon Set',
    'reason': 'OTS Leaflet web-map marker; not an ATAK icon set',
}]

paths = [row['iconsetpath'] for row in manifest['icons']]
assert len(paths) == len(set(paths)) == 3742
for row in manifest['icons']:
    expected = f"{row['iconset_uid']}/{row['group_name']}/{row['filename']}"
    assert row['iconsetpath'] == expected, (row['iconsetpath'], expected)
    asset = REGISTRY_DIR / row['internal_path']
    assert asset.is_file(), asset
    digest = hashlib.sha256(asset.read_bytes()).hexdigest()
    assert digest == row['sha256'], (row['iconsetpath'], digest, row['sha256'])
    assert asset.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'), asset

m = load_module()
assert m.TAK_MAP_ITERATION == 'i556'
cfg = m.tak_map_config()
assert cfg['version'] == '1.3.0-i556'
assert cfg['tak_map_iteration'] == 'i556'
assert cfg['icon_registry']['read_only'] is True
assert cfg['icon_registry']['custom_set_count'] == 10
assert cfg['icon_registry']['custom_icon_count'] == 3742
assert cfg['startup_architecture_i556']['i553_shell_first_runtime_preserved'] is True
assert cfg['startup_architecture_i556']['icon_registry_plugin_non_blocking'] is True

summary = m._i555_registry_summary()
assert summary['ok'] and summary['read_only']
assert summary['custom_set_count'] == 10
assert summary['custom_icon_count'] == 3742
assert summary['atak_iconsetpath_identity'] == 'icon-set UID/group/filename'

sample_path = '34ae1613-9645-4222-a9d2-e5f243dea2865/Animals/ant.png'
cache = m._i555_registry_load()
assert sample_path in cache['by_path']
sample = cache['by_path'][sample_path]
public = m._i555_public_icon(sample)
assert public['kind'] == 'custom'
assert public['iconsetpath'] == sample_path
assert public['asset_url'].endswith('path=34ae1613-9645-4222-a9d2-e5f243dea2865%2FAnimals%2Fant.png')
assert 'sha256' not in public and 'internal_path' not in public
assert m._i555_custom_fallback_type(sample, 'friendly') == 'a-f-G'
assert m._i555_custom_fallback_type(sample, 'hostile') == 'a-h-G'
assert m._i555_custom_fallback_type({}, 'neutral') == 'a-n-G'

feature = {
    'type': 'Feature',
    'uid': 'ATAK-CUSTOM-POINT-01',
    'event_uid': 'ATAK-CUSTOM-POINT-01',
    'cot_uid': 'ATAK-CUSTOM-POINT-01',
    'geometry': {'type': 'Point', 'coordinates': [-118.1, 34.1]},
    'properties': {
        'uid': 'ATAK-CUSTOM-POINT-01',
        'event_uid': 'ATAK-CUSTOM-POINT-01',
        'cot_uid': 'ATAK-CUSTOM-POINT-01',
        'preserve_event_uid_i555': True,
        'name': 'Custom Ant',
        'callsign': 'Custom Ant',
        'cot_type': 'a-h-G',
        'iconsetpath': sample_path,
        'iconset_path': sample_path,
        'icon_mode': 'custom-registry',
    },
}
assert m._i526_native_point_uid(feature) == 'ATAK-CUSTOM-POINT-01'
invalid = json.loads(json.dumps(feature))
invalid['properties']['uid'] = invalid['properties']['event_uid'] = invalid['properties']['cot_uid'] = 'bad uid with spaces'
invalid['uid'] = invalid['event_uid'] = invalid['cot_uid'] = 'bad uid with spaces'
assert m._i526_native_point_uid(invalid) != 'bad uid with spaces'

built = m._i526_point_xml(feature, 'REGISTRY-TEST', 'ANDROID-test')
assert built['ok'], built
assert built['uid'] == 'ATAK-CUSTOM-POINT-01'
assert built['cot_type'] == 'a-h-G'
assert built['version'] == 'i555'
assert built['icon_registry'] == 'read-only-i555'
root = ET.fromstring(built['xml'])
assert root.attrib['uid'] == 'ATAK-CUSTOM-POINT-01'
assert root.attrib['type'] == 'a-h-G'
detail = root.find('detail')
assert detail is not None
usericon = detail.find('usericon')
assert usericon is not None and usericon.attrib['iconsetpath'] == sample_path
meta = detail.find('takmap_point')
assert meta is not None
assert meta.attrib['version'] == 'i555'
assert meta.attrib['iconRegistry'] == 'read-only-i555'
assert meta.attrib['symbolMode'] == 'custom-registry'
assert meta.attrib['registryManagedCustomIcon'] == 'true'
assert meta.attrib['iconsetUid'] == '34ae1613-9645-4222-a9d2-e5f243dea2865'
assert meta.attrib['iconGroup'] == 'Animals'
assert meta.attrib['iconFilename'] == 'ant.png'

html = m.TAK_MAP_HTML
assert len(html.encode()) < 200_000
assert len(re.findall(r'<script\b', html, re.I)) == 2
scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)', html, re.I)
assert scripts == [
    '/assets/runtime/tak-map-startup-i553.js?v=1.3.0-i556',
    '/assets/runtime/tak-map-icon-registry-i556.js?v=1.3.0-i556',
]
assert html.index('tak-map-startup-i553.js') < html.index('tak-map-icon-registry-i556.js')
plugin_tag = re.search(r'<script[^>]*id=["\']takMapIconRegistryI556["\'][^>]*>', html, re.I)
assert plugin_tag and re.search(r'\bdefer\b', plugin_tag.group(0), re.I)
assert 'tak-map-icon-registry-i556.js' not in m.TAK_MAP_LOGIN_HTML
plugin_source = (ROOT / 'assets' / 'tak-map-icon-registry-i556.js').read_text(encoding='utf-8')
assert 'data-i556-point-edit="1"' in plugin_source
assert "document.addEventListener('click', handlePopupPointEdit, true)" in plugin_source
assert 'onclick="openDataSyncPointEditI556' not in plugin_source

source = (ROOT / 'tak_dashboard.py').read_text(encoding='utf-8')
main_marker = "if __name__=='__main__':\n    main()"
assert source.count(main_marker) == 1
assert source.rfind(main_marker) > source.rfind('# --- end TAK Map i556 corrective point popup/editor/runtime patch ---')
assert not source[source.rfind(main_marker) + len(main_marker):].strip()

install = (ROOT / 'install.sh').read_text(encoding='utf-8')
assert 'tak-map-icon-registry-i556.js' in install
assert 'ICON_REGISTRY_ASSET_DIR="/usr/share/tak-server-dash/icon-registry"' in install
assert 'cp -a assets/icon-registry/. "$ICON_REGISTRY_ASSET_DIR"/' in install
assert 'tak-map-icon-registry-i*.js' in install
uninstall = (ROOT / 'uninstall.sh').read_text(encoding='utf-8')
assert 'rm -rf /usr/share/tak-server-dash/icon-registry' in uninstall

print(json.dumps({
    'ok': True,
    'version': 'i556',
    'custom_sets': len(manifest['sets']),
    'custom_icons': len(manifest['icons']),
    'sha256_assets_verified': len(manifest['icons']),
    'unknown_leaflet_set_excluded': True,
    'exact_atak_iconsetpath_verified': sample_path,
    'map_shell_scripts': scripts,
}, indent=2))
