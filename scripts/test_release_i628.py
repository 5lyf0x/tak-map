#!/usr/bin/env python3
"""Release/protected-baseline contract for TAK Map 1.4.0 i628."""
from pathlib import Path
import hashlib, json, runpy
ROOT=Path(__file__).resolve().parents[1]
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    assert (ROOT/'VERSION').read_text().strip()=='1.4.0-i628'
    manifest=json.loads((ROOT/'assets/tak-map-deferred-i553.json').read_text())
    assert manifest['version']=='1.4.0-i628'
    startup=(ROOT/'assets/tak-map-startup-i553.js').read_text()
    assert '/assets/runtime/tak-map-deferred-i553.json?v=1.4.0-i628' in startup
    dashboard=(ROOT/'tak_dashboard.py').read_text()
    for marker in (
      "allowed={'health','capabilities','periods','manifest','events','chunk','search','state'}",
      "_I628_PACKAGE_VERSION = '1.4.0-i628'",'_I628_REPLAY_SCRIPT','takMapIdentityGuardI628',
      'replay_maintenance_i628','replayPeriodIdsI628','refreshSelectedReplayPeriodI628','fetchReplayStateI626',
      'Replay state index preparing','replay_state_i626','replay_proxy_i627','context_panel_sizing_i620'):
        assert marker in dashboard,marker
    for rel,markers in {
      'README.md':['# TAK Map v1.4.0 i628','tak-map-v1.4.0-i628.zip','Replay maintenance-aware','TAK Gateway i196'],
      'docs/INSTALL.md':['1.4.0 i628','tak-map-v628'],
      'docs/RELEASES.md':['## 1.4.0-i628','state index preparing','## 1.4.0-i627'],
      'CHANGELOG.md':['## 1.4.0-i628','Replay maintenance-aware','i627'],
    }.items():
        text=(ROOT/rel).read_text()
        for marker in markers: assert marker in text,(rel,marker)
    expected=json.loads((ROOT/'reports/i613-data-sync-protected-hashes.json').read_text())
    for rel,value in expected.items():
        if rel in ('assets/tak-map-context-sidebar-i572.js','tak_dashboard.py'): continue
        assert sha(ROOT/rel)==value,f'protected baseline changed: {rel}'
    ns=runpy.run_path(str(ROOT/'tak_dashboard.py'),run_name='tak_map_i628_release')
    html=str(ns['TAK_MAP_HTML'])
    assert html.count('id="v415ReplayModeIntegrationPatch"')==1
    assert html.count('id="takMapIdentityGuardI628"')==1
    assert "const V='i628',RELEASE='1.4.0'" in html
    cfg=ns['tak_map_config']()
    assert cfg.get('version')=='1.3.0-i602'
    assert ns.get('TAK_MAP_ITERATION')=='i602'
    feature=cfg.get('replay_maintenance_i628') or {}
    for key in ('nonfatal_state_index_preparing','requested_jump_time_preserved','period_refresh_on_not_found_once','safe_alias_or_unique_overlap_remap','never_cross_recordings_silently','i627_state_proxy_preserved','live_map_unchanged'):
        assert feature.get(key) is True,(key,feature)
    print('TAK Map 1.4.0 i628 release and protected-baseline contract passed')
    return 0
if __name__=='__main__': raise SystemExit(main())
