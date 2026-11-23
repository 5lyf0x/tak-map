# TAK Map v1.4.0-i682 source validation

Baseline: byte-verified i681 ZIP, extracted to a clean new versioned source folder. The previously verified Local Data source patch was applied against that archive and checked against the original staged files. Additional i682 work: fix blend mode visible-label selection, release identity and cache version, docs, and release regression tests.

## Passed in isolated build container

- `test_i682_local_data_persistence.py` — 9/9 tests (last-session full route, points/shapes, 30+ imports, 1,500+ features, targeted deletion, cold restart, failure handling and installer data-path check).
- `test_i680_local_data_recovery.py` — 5/5 tests.
- `test_i679_full_route_persistence.py` — 5/5 tests.
- `test_i681.py` — 5/5 tests (i681 features retained, current-version assertion updated).
- `test_i673.py` relevant release and basemap controls — 2/2 tests. The full legacy i673 suite was not completed within the build test window; do not count unexecuted tests as passed.
- `test_i682_release.py` — 3/3 tests.
- `node tests/test_i682_frontend_hydration.cjs` — 5/5 client state/visibility assertions.
- `python tests/test_i682_basemap_blend_browser.py` — real Chromium clicks for seven mode choices including lower options, visible button text, effective mode, selection and browser-persisted state.
- `python scripts/test_i677_basemap_layers_browser.py` — real Chromium managed-layer opacity, order and persisted preference checks.
- Python AST syntax, Node blend script syntax, Bash installer syntax — passed.

## Deployment validation not performed

This build environment has no direct access to the user's live TAK Map server or saved Local Data. Preserve an independent backup of `/var/lib/tak-map/tak_map_imports/` before upgrading. On the user's server, compare the actual saved object counts, IDs, names and full geometry before/after map refresh, backend restart and upgrade. A route already removed from earlier stores cannot automatically be reconstructed by this source-only persistence fix.

The benign MIL-STD catalog warning in isolated Python tests reflects missing `/usr/share/tak-server-dash/mil2525/icons.json` in this build environment.
