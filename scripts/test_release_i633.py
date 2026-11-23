#!/usr/bin/env python3
"""Release/protected-baseline contract for TAK Map 1.4.0 i633."""
from pathlib import Path
import hashlib
import json
import os
import runpy
import tempfile

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    assert (ROOT / 'VERSION').read_text().strip() == '1.4.0-i633'
    manifest = json.loads((ROOT / 'assets/tak-map-deferred-i553.json').read_text())
    assert manifest['version'] == '1.4.0-i633'
    assert manifest['count'] == len(manifest['scripts'])
    startup = (ROOT / 'assets/tak-map-startup-i553.js').read_text()
    assert '/assets/runtime/tak-map-deferred-i553.json?v=1.4.0-i633' in startup
    adsb_asset=(ROOT/'assets/tak-map-adsb-v491.js').read_text()
    embedded_adsb=next(x['code'] for x in manifest['scripts'] if x.get('id')=='takMapAdsbWorkerI463')
    assert embedded_adsb == adsb_asset
    assert "u.searchParams.set('active','1')" in embedded_adsb
    assert "u.searchParams.set('client_id',cfg.clientId)" in embedded_adsb
    assert "u.searchParams.set('active','0')" in embedded_adsb
    owner=next(x['code'] for x in manifest['scripts'] if x.get('id')=='v320AdsbSingleOwnerPatch')
    sidebar_src=(ROOT/'assets/tak-map-adsb-sidebar-i610.js').read_text()
    sidebar_embedded=next(x['code'] for x in manifest['scripts'] if x.get('id')=='TakMapAdsbSidebarI610')
    assert sidebar_embedded==sidebar_src
    assert owner.count('scale(.75)') >= 3
    assert "img.style.transform=`rotate(${p.heading}deg) scale(.75)`" in sidebar_embedded

    dashboard = (ROOT / 'tak_dashboard.py').read_text()
    for marker in (
        "allowed={'health','capabilities','periods','manifest','events','chunk','search','state'}",
        "_I630_PACKAGE_VERSION = '1.4.0-i630'",
        "_I631_PACKAGE_VERSION = '1.4.0-i633'",
        "_I630_OTS_COMPATIBILITY_TARGET = '1.7.13'",
        "'https://10.10.10.2'",
        '_I630_REPLAY_SCRIPT' if '_I630_REPLAY_SCRIPT' in dashboard else '_I629_REPLAY_SCRIPT',
        'takMapIdentityGuardI630',
        'takMapConfigureOtsI630',
        'transport_pin_enabled',
        'default_truststore_password_used',
        'def _i630_mtls_probe',
        'ots_login_independent_of_data_sync_certificate_failure',
        'adsb_emergency_i629',
        'replay_maintenance_i628',
        'replay_state_i626',
        'replay_proxy_i627',
        'context_panel_sizing_i620',
        "_I631_ADSB_PRIMARY_RETRY_SECONDS = 600.0",
        "_I631_ADSB_ACTIVE_COALESCE_SECONDS = 0.5",
        "api.adsb.lol",
        "backend_auto_failover",
    ):
        assert marker in dashboard, marker

    for rel, markers in {
        'README.md': ['# TAK Map v1.4.0 i633', 'tak-map-v1.4.0-i633.zip', 'OpenTAKServer 1.7.13'],
        'docs/INSTALL.md': ['1.4.0 i633', 'tak-map-v633'],
        'docs/RELEASES.md': ['## 1.4.0-i633', 'OpenTAKServer 1.7.13', '## 1.4.0-i629'],
        'CHANGELOG.md': ['## 1.4.0-i633', 'OpenTAKServer 1.7.13', 'i629'],
    }.items():
        text = (ROOT / rel).read_text()
        for marker in markers:
            assert marker in text, (rel, marker)

    # i613 is the protected Data Sync baseline. i633 may modify the Python
    # composition layer and shared context sidebar, but every other protected
    # asset must stay byte-for-byte identical.
    expected = json.loads((ROOT / 'reports/i613-data-sync-protected-hashes.json').read_text())
    for rel, value in expected.items():
        if rel in ('assets/tak-map-context-sidebar-i572.js', 'tak_dashboard.py'):
            continue
        assert sha(ROOT / rel) == value, f'protected baseline changed: {rel}'

    os.environ['TAK_MAP_DATA_DIR'] = tempfile.mkdtemp(prefix='tak-map-i633-release-')
    os.environ['TAK_MAP_OTS_DEFAULT_SERVER'] = 'https://10.10.10.2'
    ns = runpy.run_path(str(ROOT / 'tak_dashboard.py'), run_name='tak_map_i633_release')
    assert ns['TAK_MAP_ITERATION'] == 'i633'
    html = str(ns['TAK_MAP_HTML'])
    assert html.count('id="v415ReplayModeIntegrationPatch"') == 1
    assert html.count('id="takMapIdentityGuardI630"') == 1
    assert 'id="takMapIdentityGuardI629"' not in html
    assert html.count('id="takMapConfigureOtsI630"') == 1
    assert "const V='i633',RELEASE='1.4.0'" in html
    assert "ITERATION='i633',PACKAGE='1.4.0-i633'" in html
    assert "ITERATION='i629'" not in html
    assert 'tak-map-v1.4.0-i633.zip' in html

    # Preserve the inherited i629 ADS-B emergency behavior in the final HTML.
    for marker in ('emergencyRaw', 'emergencyColorNodes', 'emergency:!!e.emergency', "e?.emergency?'emergency':'normal'", 'Emergency</b><span style="color:#FF0000'):
        assert marker in html, marker

    cfg = ns['tak_map_config']()
    assert cfg['version'] == '1.4.0-i633'
    assert cfg['tak_map_iteration'] == 'i633'
    assert (cfg.get('adsb') or {}).get('source_mode') == 'backend_auto_failover'
    feature = cfg.get('configure_ots_i630') or {}
    for key in (
        'strict_tls_required',
        'certificate_hostname_internal_pin_fallback',
        'managed_hosts_bootstrap',
        'managed_hosts_mapping_automatic',
        'managed_hosts_file_edit_performed_when_needed',
        'default_ots_truststore_password_attempted_when_needed',
        'admin_profile_required',
        'per_user_certificate_preflight',
        'marti_client_certificate_preflight',
        'ots_login_independent_of_data_sync_certificate_failure',
    ):
        assert feature.get(key) is True, (key, feature)
    assert feature.get('manual_hosts_file_edit_required') is False
    assert feature.get('hosts_file_edit_required_when_certificate_needs_dns_name') is True
    assert feature.get('secrets_persisted') is False
    assert feature.get('compatibility_target') == '1.7.13'
    assert feature.get('deployment_default_server') == 'https://10.10.10.2'
    assert feature.get('web_https_candidates') == [443, 8443]
    assert feature.get('standard_ports') == {
        'web_https': 443,
        'marti_https': 8443,
        'certificate_enrollment': 8446,
        'ssl_cot': 8089,
    }
    assert feature.get('truststore_endpoint') == '/api/truststore'
    assert feature.get('api_identity_endpoint') == '/api/me'
    assert feature.get('certificate_enrollment_endpoint') == '/Marti/api/tls/signClient/v2'

    adsb = cfg.get('adsb_emergency_i629') or {}
    for key in ('live_emergency_red', 'replay_emergency_red', 'gateway_emergency_metadata_preserved', 'gateway_red_style_preserved', 'normal_emergency_normal_refresh', 'replay_popup_emergency_indicator', 'stale_semantics_unchanged', 'i628_replay_jump_preserved'):
        assert adsb.get(key) is True, (key, adsb)

    print('TAK Map 1.4.0 i633 release, ADS-B failover, OTS 1.7.13 automation, and protected-baseline contract passed')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
