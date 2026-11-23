#!/usr/bin/env python3
"""TAK Map i621 whole-recording Replay Search static integration contract."""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "tak_dashboard.py"

APPROVED = [
    "flight", "icao", "registration", "owner_operator", "aircraft_type",
    "aircraft_model", "eud_callsign", "eud_uid", "vessel_name", "ais_callsign",
]
BANNED = ["mmsi", "imo"]


def block(text: str, start: str, end: str) -> str:
    a = text.index(start)
    b = text.index(end, a)
    return text[a:b]


def main() -> int:
    assert (ROOT / "VERSION").read_text().strip() == "1.4.0-i621"
    manifest = json.loads((ROOT / "assets/tak-map-deferred-i553.json").read_text())
    assert manifest["version"] == "1.4.0-i621"
    startup = (ROOT / "assets/tak-map-startup-i553.js").read_text()
    assert "tak-map-deferred-i553.json?v=1.4.0-i621" in startup

    text = DASH.read_text()
    assert "allowed={'health','capabilities','periods','manifest','events','chunk','search','state'}" in text
    assert "replay/(health|capabilities|periods|manifest|events|chunk|search|state)" in text
    assert "Search recording" in text and "Entire selected period" in text
    assert "Flight, ICAO, tail, EUD, vessel" in text
    assert "Searching the entire selected recording" in text
    assert "No matching identities were found in this recording." in text
    assert "Ready to search the entire selected recording." in text

    # The browser query is explicitly scoped to the selected Replay period.
    assert "/api/tak-map/replay/search?period_id=" in text
    assert "&q=" in text and "&limit=50" in text

    diag_match = re.search(r"fields:\[(.*?)\],resultCount", text)
    assert diag_match, "Replay Search diagnostics field list missing"
    fields = re.findall(r"'([^']+)'", diag_match.group(1))
    assert fields == APPROVED, fields

    search_area = block(text, "function installReplaySearchUiI621()", "function bindUi(){")
    for field in APPROVED:
        assert field in search_area
    # MMSI and IMO may exist elsewhere in TAK Map, but they are not part of Replay Search extraction/UI.
    aliases = block(text, "function replaySearchAliasesI621", "function renderReplaySearchResultsI621")
    for banned in BANNED:
        assert banned not in aliases.lower()

    jump = block(text, "async function jumpReplaySearchResultI621", "function stepReplaySearchOccurrenceI621")
    assert "pause();" in jump
    assert "fetchReplayWindow" in jump
    assert "targetMs-60000" in jump and "targetMs+60000" in jump
    assert "replay.selectedSources.add" in jump
    assert "buildSourceChecks(true)" in jump
    assert "seekTo(event.ms)" in jump
    assert "replay.map.panTo" in jump
    assert "openReplayMarkerPopup" in jump
    assert "replay-search-hit-i621" in jump
    assert "toggleTrack(" not in jump
    assert "toggleFollow(" not in jump

    clear = block(text, "function clearReplay()", "function replayAircraftData")
    assert "resetReplaySearchI621(true)" in clear
    load = block(text, "async function loadSelectedPeriod()", "function parseRecord")
    assert "updateReplaySearchAvailabilityI621()" in load
    assert "Ready to search the entire selected recording." in load

    assert "_I620_VERSION = 'i621'" in text
    assert "_I620_PACKAGE_VERSION = '1.4.0-i621'" in text
    assert "ITERATION='i621',PACKAGE='1.4.0-i621'" in text
    print("TAK Map i621 whole-recording Replay Search integration contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
