# TAK Map v1.4.0-i693 — Validation report

Baseline: exact `tak-map-v1.4.0-i692.zip`, SHA-256 `c32508802938428c38e3ccca313cc7b128f4d3ebaa109c0b29fadc47362ed997`.

## Offline pass results

- **PASS** Baseline ZIP CRC and SHA256SUMS matched 6,204 source files.
- **PASS** No baseline source file deleted; only 6 expected original files changed and 7 new source/document/test files added.
- **PASS** Python compile (`tak_dashboard.py`, `tak_map_radar_i693.py`). Old source includes historical nonfatal escape-sequence warnings.
- **PASS** JavaScript syntax (`node --check assets/tak-map-weather-i693.js`).
- **PASS** Installer syntax (`bash -n install.sh`) and new i693 runtime asset deployment references.
- **PASS** Eight isolated backend fixture cases: catalog observation, catalog fallback labeling, intermittent 503, local retries/caching, valid transparent PNG, metadata outage retention, fixed-host/XYZ safeguards, single-flight.
- **PASS** Chromium fixture: tile error -> independent retry, 2D viewport loading/ready, retains old frame while new loads, swaps after threshold, 3D imagery, independent NWS alerts, persisted opacity.
- **PASS** i692 source remains retained as rollback in archive; i691 alerts and saved browser preference key remain unchanged.
- **PASS** ZIP integrity, SHA256SUMS and fresh extraction verified at package creation.

## Unverified live behavior

- **NOT TESTED** NOAA/NWS live radar exports and ImageServer catalog queries. Outbound DNS is unavailable from this build environment.
- **NOT TESTED** Pixel-level comparison with `radar.weather.gov` at matched reflectivity product, time and southern California bounds.
- **NOT TESTED** Deployment on user TAK Map host (browser fixture only).

The software distinguishes provisional time-extent timestamps from catalog-verified observation times. Clear/transparent tiles remain valid; provider errors can still occur. No guarantee of identical offshore echoes until tested with the same NWS observation and visualization settings.
