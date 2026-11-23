# TAK Map v1.4.0-i699 — Source/Offline Validation

Base: exact v1.4.0-i698 full-source ZIP, SHA256 695f78828d6323dfbd49c41e5dcd9915fb8db41455594be0c796b3d2006a211f.

## Included i699 changes
- Asynchronous authenticated Offline Maps source-catalog refresh (staged i699 fix).
- Command Slate style Offline Maps card, no visible W/E/S/N coordinates, no header icon, no redundant Download heading, both dropdowns with consistent typography and no chevrons, Preview Max and Download labels without icons.
- Authenticated server-owned per-user basemap preferences for order, opacity, enabled layers, Blend, Tone, custom detail controls and stack expansion. Atomic 0600 files in DATA_DIR and optimistic revisions. No client-supplied user-identity trust. Explicit optional migration from legacy unscoped browser storage, not automatic cross-user reuse.
- Preserve temporarily unavailable imported source IDs/settings in saved preferences while removing missing source imagery; reorder after catalog arrives.
- Release badge, config, VERSION and HTML asset cache tags are v1.4.0-i699.

## Focused test results
- `scripts/test_basemap_prefs_i699.py`: 5 unit cases PASS.
- `scripts/test_basemap_prefs_i699_api.py`: authenticated GET/POST, user isolation, 409 conflict, 401 unauthenticated PASS.
- `scripts/test_basemap_prefs_i699_browser.py`: browser restore, conflict reload, missing basemap retention, no silent writeback PASS.
- `scripts/test_offline_i698.py`: 4 existing downloader tests PASS.
- `scripts/test_offline_i698_browser.py`: 54 choices, polygon clip, batching/recovery PASS.
- `scripts/test_offline_card_i699_browser.py`: new layout, labels, missing coordinate removal, no icons/chevrons, async catalog and import refresh PASS.
- `scripts/test_i696_imported_basemap_stack_browser.py`: imported catalog and settings regression PASS after updating expected missing-entry retention for i699 design.
- `scripts/test_radar_history_i696_browser.py`: 11 behavior checks PASS.
- `scripts/test_weather_browser_i693.py`: 2D/3D and radar weather checks PASS.
- Syntax: Python AST for backend/store, Node syntax for both changed runtime JS files, `bash -n install.sh` PASS.
- Full manifest, ZIP integrity, and extraction verification in separate delivery report.

## Known boundaries
- Actual TAK server account sessions, browser roaming to a second physical device, and large downloads are not live tested here.
- Cross-server preference roaming/Token Mesh is not implemented.
- A user with only legacy unscoped localStorage settings must explicitly select “Import this browser’s previous settings” under BASEMAP LAYERS on first login, avoiding accidental cross-user migration.
- NDM-to-Cesium terrain geometry remains pending for v1.5 development.
- Existing Python SyntaxWarnings for old embedded JavaScript regular expressions are unrelated and nonfatal.
