# TAK Map v1.5.0-i002 — validation scope

- Source base: immutable validated v1.5.0-i001 ZIP.
- Two-file fix: `assets/tak-map-core-i553.js`, `assets/tak-map-offline-maps-i698.js` from previously staged patch, applied at zero fuzz.
- Version identity and release documentation updated to i002; all persistent offline map data formats remain unchanged.
- Execute `scripts/test_offline_pack_i002_startup.py` to check the real renderer and card module against a late-loading core browser fixture.
- Execute `scripts/test_offline_pack_i001.py` and `scripts/test_offline_pack_i001_browser.py` to check inherited Rename/sort/footer functionality.
- Packaging/ZIP checksum and field-deployment results are reported separately by the build handoff.
