#!/usr/bin/env python3
"""TAK Map i624 Replay Jump to Date / Time final served-HTML contract."""
from pathlib import Path
import runpy
import re

ROOT=Path(__file__).resolve().parents[1]


def main()->int:
    source=(ROOT/'tak_dashboard.py').read_text()
    for marker in (
        "_I624_PACKAGE_VERSION = '1.4.0-i624'",
        'function installReplayJumpUiI624',
        'function ensureReplayStateThroughI624',
        'function jumpReplayToI624',
        'function stepReplayJumpI624',
        'replayJumpDateI624', 'replayJumpTimeI624', 'replayJumpGoI624',
        '−1 min', '+1 min', "step=\"1\"",
        "stateReconstruction:'contiguous-prefix-plus-lookahead'",
        "gateway_required_iteration': 'i194'",
    ):
        assert marker in source, marker
    ensure=source[source.index('async function ensureReplayStateThroughI624'):source.index('async function jumpReplayToI624')]
    for marker in ('replay.loadedUntilMs','fetchReplayWindow','mergeReplayRows','targetMs+120000','5*60*1000','updateBufferUi'):
        assert marker in ensure, marker
    jump=source[source.index('async function jumpReplayToI624'):source.index('function goReplayJumpI624')]
    for marker in ('pause();','ensureReplayStateThroughI624(targetMs)','seekTo(targetMs)','Replay remains paused'):
        assert marker in jump, marker
    render=source[source.index('function renderAt(ms,force)'):source.index('function seekTo(ms)')]
    assert 'syncReplayJumpFieldsI624(ms,false)' in render
    search=source[source.index('async function jumpReplaySearchResultI621'):source.index('function stepReplaySearchOccurrenceI621')]
    assert 'seekTo(event.ms)' in search  # renderAt synchronization covers search/occurrence jumps.

    ns=runpy.run_path(str(ROOT/'tak_dashboard.py'),run_name='tak_map_i624_jump_contract')
    html=str(ns['TAK_MAP_HTML'])
    assert html.count('id="v415ReplayModeIntegrationPatch"')==1
    assert html.count('id="takMapIdentityGuardI624"')==1
    for marker in ('replayJumpI624','replayJumpDateI624','replayJumpTimeI624','replayJumpGoI624','Jump to date / time','−1 min','+1 min','ensureReplayStateThroughI624'):
        assert marker in html, marker
    assert '1.4.0-i624' in html and "const V='i624',RELEASE='1.4.0'" in html
    cfg=ns['tak_map_config']()
    feature=cfg.get('replay_jump_i624') or {}
    assert feature.get('date_time_seconds_precision') is True
    assert feature.get('outside_current_buffer') is True
    assert feature.get('state_reconstruction')=='contiguous-prefix-plus-lookahead'
    assert feature.get('minus_plus_one_minute') is True
    print('TAK Map i624 Replay Jump final served-HTML contract passed')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
