# TAK Map v1.4.0-i688 — Local Validation Results

## Backend and regression

- **47 Python tests passed, 8 Python subtests passed**, across i679/i680 Local Data recovery and route persistence, i682/i683 release/persistence, and i685–i688 Infrastructure functionality.
- Eight pre-existing legacy SyntaxWarnings occur when compiling `tak_dashboard.py` from escaped sequences in giant HTML literals; they were present before i688, and were not test failures.
- New i688 tests cover additive SQLite schema migration, preservation of all original features and older provider metadata, filtered spatial queries before the 5,000-feature budget, persistent AND/OR rules, indexed search beyond viewport, category/layer eligibility, exact feature retrieval and point-symbol configuration.
- A separately seeded **50,000-feature** synthetic offline point dataset was queried with a rare numeric filter: **10 selected out of 50,000** in approximately **0.38 seconds**; one indexed search hit in approximately **0.04 seconds**. Data ingestion 1.82 seconds in test environment. This does not measure live GIS host or network speed.

## Browser checks

- Chromium **1280px and 390px** i688 UI checks passed: offline-only card and source isolation, expanded categories, viewport plus 50% query buffer, 5px line click area, original color plus red selection outline, click-only Object Details, all raw GIS attributes visible, per-layer symbol setting, filter dialog, global search, A→B→A pan race, and dropdown identity over background status polls.
- i687 backward-compatibility Chromium checks passed at both widths. i684 Route Details formatting, repeated Cancel Edit, saved-route selection/elevation panel and deselection browser checks passed.
- Local Data and route-related Python regression tests passed.

## Source/package quality gates

- JavaScript and Python syntax, installer `bash -n`, active `i688` HTML asset wiring and release version label checked.
- ZIP integrity, source-only file filtering, original baseline inventory preservation, fresh extraction byte-for-byte comparison and SHA-256 are validated separately as the final release archive is built.

## Not validated on the live server

- No installation on the user's TAK Map host.
- No direct live downloads from City of LA / County or other GIS providers during this build.
- No comprehensive 3D Cesium end-to-end test against the user's real GPU, terrain and large imported datasets.
- No guarantee of the same synthetic benchmark times on the user's machine.
