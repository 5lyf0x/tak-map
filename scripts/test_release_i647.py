#!/usr/bin/env python3
"""TAK Map i647 version/runtime/install contract and inherited i645 behavior."""
from pathlib import Path
import runpy,json
ROOT=Path(__file__).resolve().parents[1]
assert (ROOT/'VERSION').read_text().strip()=='1.4.0-i647'
installer=(ROOT/'install.sh').read_text()
for token in ('install -m 0644 assets/tak-map-gateway-config-i645.js','tak-map-gateway-config-i645.js?install-check=i647','TAK_MAP_GATEWAY_DATA_AUTH_MODE auto','TAK_MAP_REPLAY_AUTH_MODE certificate'):
    assert token in installer,token
ns=runpy.run_path(str(ROOT/'tak_dashboard.py'),run_name='release_i647_contract')
assert ns['TAK_MAP_ITERATION']=='i647'
cfg=ns['tak_map_config']()
assert cfg['version']=='1.4.0-i647' and cfg['tak_map_iteration']=='i647',cfg.get('version')
assert cfg['gateway_data_config_editor_i645']['replay_settings_unchanged']
assert cfg['gateway_optional_client_certificates_i644']['replay_default_auth']=='certificate'
assert cfg['shape_edit_i643']['native_shape_type_preserved']
assert 'takMapGatewayConfigLoaderI645' in ns['TAK_MAP_HTML']
assert 'tak-map-gateway-config-i645.js?v=1.4.0-i647' in ns['TAK_MAP_HTML']
for asset in ('tak-map-context-sidebar-i572.js','tak-map-package-i580.js','tak-map-i636.js'):
    assert asset+'?v=1.4.0-i647' in ns['TAK_MAP_HTML'],asset
assert 'i647' in ns['TAK_MAP_LOGIN_HTML']
manifest=json.loads((ROOT/'assets/tak-map-deferred-i553.json').read_text())
assert manifest['version']=='1.4.0-i647' and manifest['count']==len(manifest['scripts'])
for asset in ('tak-map-context-sidebar-i572.js','tak-map-package-i580.js'):
    assert 'i647' in (ROOT/'assets'/asset).read_text()
assert 'replay' in ns['_tak_gateway_connection_profile']('replay')['api_url'].lower()
print('PASS: i647 identity, runtime asset deployment, i645 Configure, i644 auth, i643 shape')
