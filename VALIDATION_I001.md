# TAK Map v1.5.0-i001 — source release validation

**Base:** exact validated `tak-map-v1.4.0-i699.zip` (34,882,328 bytes, SHA-256 `b2f74c066f58486dac85c408126499dc6f6b02d802564163dd5823632d62ac66`). The original i699 ZIP remains unchanged.

## Included scope

- Completed downloaded/imported Offline Map Packs: inline Rename / Save / Cancel / Enter / Escape and authenticated `POST /api/tak-map/offline-rename-i001`.
- Natural, case-insensitive alphabetical pack list sorting; 600px maximum list height with internal scrolling.
- Non-destructive catalog rename, preserved MBTiles bytes/IDs/paths/download/retry/history, refreshed outgoing EUD filename only on new packaging.
- Preserve all existing map catalog entries (removed the previous `maps[-80:]` truncation); serialized catalog mutation operations using one reentrant lock, retaining atomic writes.
- Footer version `TAK Map 1.5.0` and iteration `i001` in actual rendered HTML, compatible with earlier i630/i665 footer guards. API/config/cache keys and VERSION agree.

## Checks completed

- Python AST parse and Python import of full backend: PASS (existing nonfatal legacy Python `SyntaxWarning` patterns suppressed for test invocations).
- Node `--check` for changed core and Offline Maps JS; Bash `-n` installer: PASS.
- `scripts/test_offline_pack_i001.py`: PASS: synthetic on-disk catalog with 89 then 101 records, no lost records, imported and downloaded eligibility, incomplete-status rejection, input validation, no MBTiles mutation, regenerated EUD name and ZIP content, concurrent catalog upserts, authorized/unauthorized Handler HTTP route and rendered footer/config.
- `scripts/test_offline_pack_i001_browser.py`: PASS in local Chromium: final release footer guard before/after legacy mutation, case-insensitive natural sorting, completed-only Rename, 600px CSS, Save, Escape, Enter, client validation and server error display.
- Existing `scripts/test_offline_i698.py`: 4 of 4 PASS (state boundaries, tiling, retry manifest).
- Existing `scripts/test_offline_i698_browser.py`: PASS (54 selections, Alaska/California, internal batching, Retry/Finish).
- Existing `scripts/test_offline_card_i699_browser.py`: PASS (Command Slate card, asynchronously loaded source dropdown, imported source refresh, no redundant controls).

## Limitations

- No actual TAK Map host/production account authentication, remote TAK/EUD delivery, large-volume real downloads, or field deployment was performed.
- Local Chromium tests use browser fixtures with the real production functions and release scripts; they are not a full live-server end-to-end test.
- Missing external `/usr/share/tak-server-dash/mil2525/icons.json` in the isolated build container produces a nonfatal baseline catalog warning during Python import; no icon assets were modified.
- Archive integrity, checksum manifest, and fresh-extraction comparison are recorded separately in the delivery validation report after packaging.
