# TAK Map v1.4.0-i692 — Package and offline validation

## Source identity and scope

- Full source baseline: `tak-map-v1.4.0-i691.zip` (not a patch-only archive).
- New version: `1.4.0-i692`; exact iteration appended after i691 final handler and before blocking `__main__` entry.
- New module: `tak_map_radar_i692.py`; new client assets: `tak-map-weather-i692.js`, `tak-map-weather-i692.css`.
- Existing i691 NWS alerts API `/api/tak-map/weather/alerts-i691` preserved unchanged.
- Existing i691 localStorage key `tak-map-native-weather-i691` preserved, so weather toggles and opacity are not reset.
- No prior source files deleted. No changes to persistent TAK Map data locations or installer directory-migration rules.

## Offline tests (passed)

- `python3 -m py_compile` of `tak_map_radar_i692.py` and `tak_dashboard.py` (the latter emits preexisting warnings from old embedded JavaScript strings; compilation succeeds).
- `node --check` for `assets/tak-map-weather-i692.js`.
- `bash -n install.sh`.
- Python deterministic tests: **7 of 7 passed** in `scripts/test_weather_radar_i692.py`: XYZ/WebMercator coordinate bounds and route parsing; transparent and opaque valid PNG and invalid response rejection; fixed NOAA endpoints and blocked arbitrary URLs; primary metadata/observation frame/cached tile; metadata primary-failure to latest-image provider; corrupt upstream tile to alternate provider; and simultaneous same-tile single-flight deduplication.
- Headless Chromium fixture: **passed** in `scripts/test_weather_browser_i692.py` (same-origin radar URL, independent NWS alerts with unmapped geometry, opacity 94%, radar off while alerts on, and Cesium WebMercator URL imagery creation).
- Installer explicitly deploys radar Python backend and both new weather runtime assets, and checks both assets present after installation.

## Network limitation

This environment did **not** have resolvable outbound DNS for the live NOAA/NWS radar endpoints. The tests use deterministic NOAA-like fixtures and browser stubs; they do **not** establish that the user's installed server can fetch the official image service, or that real NOAA tiles have correct opacity, colors, valid times and map alignment. Live browser and actual host testing are required. The service is designed to expose sanitized provider errors if both sources remain unavailable.

## Archive integrity

**PASS** on the initial completed i692 archive and to be repeated after embedding this final validation note:

- Flat ZIP source root (extract with `-d tak-map-v1.4.0-i692`); no nested top-level source directory.
- ZIP `testzip()` returned no corrupt entries.
- `SHA256SUMS`: **6,204 / 6,204** source file hashes verified in a fresh extraction.
- Extracted files matched staged source byte-for-byte (**6,204 / 6,204**); no files missing or altered.
- No `.pyc`, `__pycache__`, private key files or output binaries in archive.
- Final archive identity and digest are provided in the package handoff after the last reproducible build and recheck.
