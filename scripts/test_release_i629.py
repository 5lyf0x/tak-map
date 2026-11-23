#!/usr/bin/env python3
"""Release/protected-baseline contract for TAK Map 1.4.0 i629."""
from pathlib import Path
import hashlib, json, runpy
ROOT=Path(__file__).resolve().parents[1]
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    assert (ROOT/'VERSION').read_text().strip()=='1.4.0-i629'
    manifest=json.loads((ROOT/'assets/tak-map-deferred-i553.json').read_text())
    assert manifest['version']=='1.4.0-i629'
    startup=(ROOT/'assets/tak-map-startup-i553.js').read_text()
    assert '/assets/runtime/tak-map-deferred-i553.json?v=1.4.0-i629' in startup
    dashboard=(ROOT/'tak_dashboard.py').read_text()
    for marker in (
      "allowed={'health','capabilities','periods','manifest','events','chunk','search','state'}",
      "_I629_PACKAGE_VERSION = '1.4.0-i629'",'_I629_REPLAY_SCRIPT','takMapIdentityGuardI629',
      'adsb_emergency_i629','emergencyColorNodes','normal_emergency_normal_refresh',
      'replay_maintenance_i628','replay_state_i626','replay_proxy_i627','context_panel_sizing_i620'):
        assert marker in dashboard,marker
    for rel,markers in {
      'README.md':['# TAK Map v1.4.0 i629','tak-map-v1.4.0-i629.zip','ADS-B emergency visual preservation'],
      'docs/INSTALL.md':['1.4.0 i629','tak-map-v629'],
      'docs/RELEASES.md':['## 1.4.0-i629','ADS-B emergency status','## 1.4.0-i628'],
      'CHANGELOG.md':['## 1.4.0-i629','render red','i628'],
    }.items():
        text=(ROOT/rel).read_text()
        for marker in markers: assert marker in text,(rel,marker)
    expected=json.loads((ROOT/'reports/i613-data-sync-protected-hashes.json').read_text())
    for rel,value in expected.items():
        if rel in ('assets/tak-map-context-sidebar-i572.js','tak_dashboard.py'): continue
        assert sha(ROOT/rel)==value,f'protected baseline changed: {rel}'
    ns=runpy.run_path(str(ROOT/'tak_dashboard.py'),run_name='tak_map_i629_release')
    html=str(ns['TAK_MAP_HTML'])
    assert html.count('id="v415ReplayModeIntegrationPatch"')==1
    assert html.count('id="takMapIdentityGuardI629"')==1
    assert "const V='i629',RELEASE='1.4.0'" in html
    for marker in ('emergencyRaw','emergencyColorNodes','emergency:!!e.emergency',"e?.emergency?'emergency':'normal'",'Emergency</b><span style="color:#FF0000'):
        assert marker in html,marker
    cfg=ns['tak_map_config']()
    feature=cfg.get('adsb_emergency_i629') or {}
    for key in ('live_emergency_red','replay_emergency_red','gateway_emergency_metadata_preserved','gateway_red_style_preserved','normal_emergency_normal_refresh','replay_popup_emergency_indicator','stale_semantics_unchanged','i628_replay_jump_preserved'):
        assert feature.get(key) is True,(key,feature)
    print('TAK Map 1.4.0 i629 release and protected-baseline contract passed')
    return 0
if __name__=='__main__': raise SystemExit(main())
