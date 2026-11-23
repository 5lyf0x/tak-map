# TAK Map v1.4.0-i677 — validation record

Build baseline: TAK Map v1.4.0-i676 full source. Release: v1.4.0-i677.

## Verified during source build

- `scripts/test_i677_release_contract.py`: PASS, checks published version, served assets/cache-busting, unique route import ID, Leaflet pane z-index contracts.
- `scripts/test_i677_import_backend.py`: PASS, actual local Python import handler accepts two GeoJSON routes with same name, assigns distinct IDs, retains complete stored geometry.
- `scripts/test_i677_route_duplicate_browser.py`: PASS, Chromium duplicate-name saves verified by returned ID; newest truncated route rejected despite older complete same-name record; missing ID fails closed and keeps editable route.
- `scripts/test_i677_basemap_layers_browser.py`: PASS, controlled Chromium mock tile panes verify top opacity 100% and 0%, 50% alpha blending, reorder/toggle and persisted preferences. This is not a live online ESRI tile test.
- `scripts/test_i676_browser.py`: PASS, 13-point route with unresolved Valhalla legs saves complete, truncated readback rejected, route edit/resave, draggable HUD and placement tests.
- `scripts/test_i675_graph_switch.py`: PASS (4 tests), rollback and active graph selection.
- `scripts/test_i675_http_activation.py`: PASS, authenticated dataset listing, admin-only same-origin graph activation.
- `scripts/test_i659_route_update_backend.py`: PASS, in-place edit geometry preservation and revision safeguards.
- `scripts/test_route_snap_i654.py`: PASS (6 tests), route snap basics.
- Syntax: `bash -n install.sh`, `node --check` for shipped route editor, basemap stack, core and dropdown JavaScript, Python compile of server and routing-switch module: PASS.

## Legacy or live checks not claimed

- An older i675 fixed-position Tactical HUD browser test no longer matches i676's approved draggable design; it was superseded by `test_i676_browser.py`.
- A long-running older browser regression exceeded the tool execution limit; no full historic-suite PASS is claimed.
- The model environment does not have the server's optional MIL-STD icon catalog fixture.
- Production TAK Map installation, live ESRI tile availability and the user's original trail are not tested here. Live confirmation is required.

## Source/archive integrity

- Source-only release; no generated Python bytecode/caches, private keys, keystores or application-data backups.
- ZIP CRC, `SHA256SUMS`, permission-preserving fresh `unzip` extraction and source manifest comparison are required before release.
