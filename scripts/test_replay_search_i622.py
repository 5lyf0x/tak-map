#!/usr/bin/env python3
"""TAK Map i622 whole-recording Replay Search final served-HTML contract."""
from pathlib import Path
import json
import re
import runpy

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / 'tak_dashboard.py'

APPROVED = [
    'flight', 'icao', 'registration', 'owner_operator', 'aircraft_type',
    'aircraft_model', 'eud_callsign', 'eud_uid', 'vessel_name', 'ais_callsign',
]
BANNED = ['mmsi', 'imo']


def block(text: str, start: str, end: str) -> str:
    a = text.index(start)
    b = text.index(end, a)
    return text[a:b]


def main() -> int:
    assert (ROOT / 'VERSION').read_text().strip() == '1.4.0-i622'
    manifest = json.loads((ROOT / 'assets/tak-map-deferred-i553.json').read_text())
    assert manifest['version'] == '1.4.0-i622'
    startup = (ROOT / 'assets/tak-map-startup-i553.js').read_text()
    assert 'tak-map-deferred-i553.json?v=1.4.0-i622' in startup

    source = DASH.read_text()
    assert "allowed={'health','capabilities','periods','manifest','events','chunk','search','state'}" in source
    assert 'replay/(health|capabilities|periods|manifest|events|chunk|search|state)' in source
    assert '/api/tak-map/replay/search?period_id=' in source
    assert 'Search recording' in source and 'Entire selected period' in source
    assert 'Searching the entire selected recording' in source
    assert 'No matching identities were found in this recording.' in source
    assert "_I622_PACKAGE_VERSION = '1.4.0-i622'" in source
    assert 'final served-HTML/runtime correction' in source

    aliases = block(source, 'function replaySearchAliasesI621', 'function renderReplaySearchResultsI621')
    for field in APPROVED:
        assert field in aliases, field
    for banned in BANNED:
        assert banned not in aliases.lower(), banned

    jump = block(source, 'async function jumpReplaySearchResultI621', 'function stepReplaySearchOccurrenceI621')
    for marker in ('pause();', 'fetchReplayWindow', 'targetMs-60000', 'targetMs+60000',
                   'replay.selectedSources.add', 'buildSourceChecks(true)', 'seekTo(event.ms)',
                   'replay.map.panTo', 'openReplayMarkerPopup', 'replay-search-hit-i621'):
        assert marker in jump, marker
    assert 'toggleTrack(' not in jump and 'toggleFollow(' not in jump

    # Critical i622 regression gate: execute the packaged dashboard and inspect the
    # final document actually served after every historical HTML finalizer ran.
    ns = runpy.run_path(str(DASH), run_name='tak_map_i622_final_html_contract')
    html = str(ns.get('TAK_MAP_HTML') or '')
    assert html.count('id="v415ReplayModeIntegrationPatch"') == 1
    assert html.count('id="takMapIdentityGuardI622"') == 1
    assert 'id="takMapIdentityGuardI620"' not in html
    for marker in (
        'replayPeriodV415', 'replaySearchI621', 'replaySearchInputI621',
        'replaySearchButtonI621', 'Search recording', 'Entire selected period',
        '/api/tak-map/replay/search?period_id=', "const V='i622',RELEASE='1.4.0'",
    ):
        assert marker in html, marker
    cfg = ns['tak_map_config']()
    assert cfg.get('version') == '1.3.0-i602'
    assert ns.get('TAK_MAP_ITERATION') == 'i602'
    replay_cfg = cfg.get('replay_search_i622') or {}
    assert replay_cfg.get('final_served_html_guard') is True
    assert replay_cfg.get('search_fields') == APPROVED

    print('TAK Map i622 Replay Search final served-HTML contract passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
