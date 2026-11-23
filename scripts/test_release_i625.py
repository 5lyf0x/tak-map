#!/usr/bin/env python3
"""Release/protected-baseline contract for TAK Map 1.4.0 i625."""
from pathlib import Path
import hashlib, json, runpy
ROOT=Path(__file__).resolve().parents[1]
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    assert (ROOT/'VERSION').read_text().strip()=='1.4.0-i625'
    manifest=json.loads((ROOT/'assets/tak-map-deferred-i553.json').read_text())
    assert manifest['version']=='1.4.0-i625'
    startup=(ROOT/'assets/tak-map-startup-i553.js').read_text()
    assert '/assets/runtime/tak-map-deferred-i553.json?v=1.4.0-i625' in startup
    dashboard=(ROOT/'tak_dashboard.py').read_text()
    for marker in ("_I625_PACKAGE_VERSION = '1.4.0-i625'","_I625_REPLAY_SCRIPT",'takMapIdentityGuardI625','replay_seek_i625','absoluteReplaySeekI625','stageReplayRowsThroughI625','replay_jump_i624','replay_period_identity_i623','context_panel_sizing_i620'):
        assert marker in dashboard,marker
    for rel,markers in {
      'README.md':['# TAK Map v1.4.0 i625','tak-map-v1.4.0-i625.zip','absolute-seek','Play resumes normally'],
      'docs/INSTALL.md':['1.4.0 i625','tak-map-v625'],
      'docs/RELEASES.md':['## 1.4.0-i625','absolute-seek/state reconstruction','## 1.4.0-i624'],
      'CHANGELOG.md':['## 1.4.0-i625','serialized absolute-seek','Play after Jump'],
    }.items():
        text=(ROOT/rel).read_text()
        for marker in markers: assert marker in text,(rel,marker)
    expected=json.loads((ROOT/'reports/i613-data-sync-protected-hashes.json').read_text())
    for rel,value in expected.items():
        if rel in ('assets/tak-map-context-sidebar-i572.js','tak_dashboard.py'): continue
        assert sha(ROOT/rel)==value,f'protected baseline changed: {rel}'
    ns=runpy.run_path(str(ROOT/'tak_dashboard.py'),run_name='tak_map_i625_release')
    html=str(ns['TAK_MAP_HTML'])
    assert html.count('id="v415ReplayModeIntegrationPatch"')==1
    assert html.count('id="takMapIdentityGuardI625"')==1
    assert "const V='i625',RELEASE='1.4.0'" in html
    assert "const V='i624',RELEASE='1.4.0'" not in html
    cfg=ns['tak_map_config']()
    assert cfg.get('version')=='1.3.0-i602'
    assert ns.get('TAK_MAP_ITERATION')=='i602'
    feature=cfg.get('replay_seek_i625') or {}
    for key in ('unified_absolute_seek','search_uses_full_state_reconstruction','seek_generation_serialization','atomic_state_commit','logical_period_end_separate_from_event_end','play_after_jump','preserve_last_valid_state_on_seek_error'):
        assert feature.get(key) is True,(key,feature)
    print('TAK Map 1.4.0 i625 release and protected-baseline contract passed')
    return 0
if __name__=='__main__': raise SystemExit(main())
