#!/usr/bin/env python3
"""Inherited i644 Gateway/Replay behavior tested against i645 release identity."""
from pathlib import Path
import json, os, runpy
ROOT=Path(__file__).resolve().parents[1]
assert (ROOT/'VERSION').read_text().strip()=='1.4.0-i647'
assert 'TAK_MAP_GATEWAY_DATA_AUTH_MODE auto' in (ROOT/'install.sh').read_text()
assert 'TAK_MAP_REPLAY_AUTH_MODE certificate' in (ROOT/'install.sh').read_text()
ns=runpy.run_path(str(ROOT/'tak_dashboard.py'),run_name='release_i644_contract')
assert ns['TAK_MAP_ITERATION']=='i647'
cfg=ns['tak_map_config']()
assert cfg['version']=='1.4.0-i647' and cfg['tak_map_iteration']=='i647'
assert cfg['gateway_optional_client_certificates_i644']['replay_default_auth']=='certificate'
assert cfg['shape_edit_i643']['native_shape_type_preserved'] is True
assert "tak-map-context-sidebar-i572.js?v=1.4.0-i647" in ns['TAK_MAP_HTML']
assert "tak-map-package-i580.js?v=1.4.0-i647" in ns['TAK_MAP_HTML']
assert 'i647' in ns['TAK_MAP_LOGIN_HTML']
manifest=json.loads((ROOT/'assets/tak-map-deferred-i553.json').read_text())
assert manifest['version']=='1.4.0-i647' and manifest['count']==len(manifest['scripts'])
print('TAK Map i644 Gateway/Replay behavior retained under i647 release identity')
