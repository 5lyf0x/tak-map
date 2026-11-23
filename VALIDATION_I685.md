# i685 source validation

## Release checks

- Source-only extraction from validated i684 archive, modified in a new i685 stage without overwriting earlier packages.
- `python -m py_compile tak_dashboard.py tak_map_infrastructure_i685.py` — pass (legacy inline-JS escape warnings may be emitted).
- `node --check` on modified i675 routing stylesheet script and new i685 Infrastructure UI — pass.
- `bash -n install.sh` — pass.
- Offline synthetic Infrastructure tests: built-in catalog, create/hide/restore category, 36-inch sewer filters including millimeters, spatial filtering, 5 GIS export/import round trips, interrupted download and resumption, preservation of prior offline dataset, and private URL rejection.
- Chromium tests: i675 stylesheet loaded *after* i684 uniform styles; headers equal across collapsed/expanded states; infrastructure sidebar placement, categories, 48-inch tooltip, direct Object Details selection, online/offline switching; desktop 1280px and mobile 390px.
- Prior i682-i684 regression suites: Local Data persistence, route editing cancel, Object Details, saved-route elevation, MVUM/basemap tests.
- ZIP CRC, fresh extraction and byte comparison, source-file inventory, checksum: recorded at package handoff.

## Deployment limits

No live TAK Map host, internet GIS API transfer, 3D Cesium scene, or real application-data migration test was available in this build environment. Install and validate on a backed-up deployment; don't claim provider live availability from synthetic tests alone.

## Final i685 qualification

- 22 automated Python regression tests passed (4 parameterized subtests additional).
- Infrastructure Chromium interaction tests passed at 1280px and 390px width.
- Download cancellation concurrency safeguard tested during an in-flight provider response: canceled staging was not promoted to a completed dataset.
- Browser JS syntax and shell installer syntax validated.
- Packaging integrity and file-for-file extraction results recorded in handoff.
