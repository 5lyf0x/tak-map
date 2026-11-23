#!/usr/bin/env python3
"""Release/protected-baseline contract for TAK Map 1.4.0 i626."""
from pathlib import Path
import hashlib, json, runpy
ROOT=Path(__file__).resolve().parents[1]
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    assert (ROOT/'VERSION').read_text().strip()=='1.4.0-i626'
    manifest=json.loads((ROOT/'assets/tak-map-deferred-i553.json').read_text())
    assert manifest['version']=='1.4.0-i626'
    startup=(ROOT/'assets/tak-map-startup-i553.js').read_text()
    assert '/assets/runtime/tak-map-deferred-i553.json?v=1.4.0-i626' in startup
    dashboard=(ROOT/'tak_dashboard.py').read_text()
    for marker in ("_I626_PACKAGE_VERSION = '1.4.0-i626'","_I626_REPLAY_SCRIPT",'takMapIdentityGuardI626','replay_state_i626','absoluteReplaySeekI625','stageReplayRowsThroughI625','fetchReplayStateI626','setReplaySeekingUiI626','replay_jump_i624','replay_period_identity_i623','context_panel_sizing_i620'):
        assert marker in dashboard,marker
    for rel,markers in {
      'README.md':['# TAK Map v1.4.0 i626','tak-map-v1.4.0-i626.zip','state-at-time','transport controls'],
      'docs/INSTALL.md':['1.4.0 i626','tak-map-v626'],
      'docs/RELEASES.md':['## 1.4.0-i626','checkpoint/state-at-time','## 1.4.0-i625'],
      'CHANGELOG.md':['## 1.4.0-i626','checkpoint-backed Replay state-at-time','Locks Replay transport'],
    }.items():
        text=(ROOT/rel).read_text()
        for marker in markers: assert marker in text,(rel,marker)
    expected=json.loads((ROOT/'reports/i613-data-sync-protected-hashes.json').read_text())
    for rel,value in expected.items():
        if rel in ('assets/tak-map-context-sidebar-i572.js','tak_dashboard.py'): continue
        assert sha(ROOT/rel)==value,f'protected baseline changed: {rel}'
    ns=runpy.run_path(str(ROOT/'tak_dashboard.py'),run_name='tak_map_i626_release')
    html=str(ns['TAK_MAP_HTML'])
    assert html.count('id="v415ReplayModeIntegrationPatch"')==1
    assert html.count('id="takMapIdentityGuardI626"')==1
    assert "const V='i626',RELEASE='1.4.0'" in html
    assert "const V='i624',RELEASE='1.4.0'" not in html
    cfg=ns['tak_map_config']()
    assert cfg.get('version')=='1.3.0-i602'
    assert ns.get('TAK_MAP_ITERATION')=='i602'
    feature=cfg.get('replay_state_i626') or {}
    for key in ('gateway_state_at_time','persistent_gateway_checkpoints','transport_locked_while_seeking','bounded_long_distance_seek','multi_day_period_labels_show_both_dates','preserve_previous_state_on_seek_error'):
        assert feature.get(key) is True,(key,feature)
    print('TAK Map 1.4.0 i626 release and protected-baseline contract passed')
    return 0
if __name__=='__main__': raise SystemExit(main())
