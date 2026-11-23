#!/usr/bin/env python3
"""Static final-HTML contract for i625 unified Replay absolute seek."""
from pathlib import Path
import runpy
ROOT=Path(__file__).resolve().parents[1]
def block(s,a,b): return s[s.index(a):s.index(b,s.index(a))]
def main():
    source=(ROOT/'tak_dashboard.py').read_text()
    absolute=block(source,'async function absoluteReplaySeekI625','async function ensureReplayStateThroughI624')
    for marker in ('++replay.seekGeneration','++replay.loadToken','stageReplayRowsThroughI625','replay.seeking=true','mergeReplayRows(staged.rows)','replay.loadedUntilMs','seekTo(targetMs)','loadReplayBackground(loadToken,replay.loadedUntilMs)'):
        assert marker in absolute,marker
    search=block(source,'async function jumpReplaySearchResultI621','function stepReplaySearchOccurrenceI621')
    assert 'absoluteReplaySeekI625(targetMs' in search
    assert 'targetMs-60000' not in search and 'targetMs+60000' not in search
    jump=block(source,'async function jumpReplayToI624','function goReplayJumpI624')
    assert 'absoluteReplaySeekI625(targetMs' in jump
    merge=block(source,'function mergeReplayRows','async function loadReplayBackground')
    assert 'replay.eventEndMs=' in merge and 'replay.endMs=replay.periodEndMs' in merge
    assert 'replay.startMs=replay.events[0].ms' not in merge
    render=block(source,'function renderAt(ms,force)','function seekTo(ms)')
    assert 'replay.periodEndMs' in render and 'if(ms>=terminal)pause()' in render
    play=block(source,'function play()','function pause')
    assert 'replay.seeking' in play and 'replay.currentMs>=terminal' in play
    rebuild=block(source,'function rebuildTo(ms)','function renderAt(ms,force)')
    assert 'const next=new Map()' in rebuild and 'replay.latest=next' in rebuild
    ns=runpy.run_path(str(ROOT/'tak_dashboard.py'),run_name='tak_map_i625_seek_static')
    html=str(ns['TAK_MAP_HTML'])
    for marker in ('absoluteReplaySeekI625','stageReplayRowsThroughI625','replaySeekI625',"timelineBounds:'selected-period'","const V='i635',RELEASE='1.4.0'"):
        assert marker in html,marker
    print('TAK Map i625 unified Replay seek final-HTML contract passed')
    return 0
if __name__=='__main__': raise SystemExit(main())
