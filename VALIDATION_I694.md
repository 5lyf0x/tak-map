# TAK Map v1.4.0-i694 — Offline validation report

**Baseline:** exact i693 full-source ZIP (SHA-256 `ee4a0c68b5612ccfed25ee9a783d6e2dac7ce2a1022b70c8165e7190ec346ca9`), checksum-manifest verified on extraction.

## Source scope

- **PASS:** Combined staged UI patch applied without rejects to exact i693 files.
- **PASS:** No i693 baseline file removed; 13 modified baseline files and 3 added documentation/tests (including this validation file).
- **PASS:** i694 version marker and HTML cache-busting query strings verified, including altered runtime scripts.
- **PASS:** Existing i691 browser weather preference and infrastructure individual layer persistence keys preserved; new master visibility key `takmap.infra.visible.i694`.
- **PASS:** Active weather JavaScript/CSS has no legacy `takWeatherOpacityI691` or `--tak-weather-pct` slider selectors.
- **PASS:** Both VEIL sidebar position scripts honor the installed Infrastructure panel, eliminating the competing periodic reorder.

## Automated tests

- **PASS:** Python compilation (`tak_dashboard.py`, the i693 radar module, i693/i694 browser/backend regression scripts). Existing historical escape-sequence warnings are nonfatal and are not new i694 code.
- **PASS:** Node JavaScript syntax checks for all seven modified browser assets.
- **PASS:** `bash -n install.sh` and installer gate verifies edited basemap, infrastructure, VEIL and active weather runtime assets.
- **PASS:** Eight i693 backend radar unit fixtures covering frame catalogs, transparent pixels, cache, retries and errors.
- **PASS:** i693 Chromium weather regression (tile recovery, frame handoff, 2D/3D, alerts, opacity), updated to use the i694 slider ID.
- **PASS:** i694 Chromium UI fixture at desktop and narrow widths: Infrastructure placed between BASEMAP/VEIL, reorders healed, both VEIL place routines honor order, header Show/Hide independent of collapse and preserves layer selection; 12 Blend modes remain open and outside click closes; radar Soft Pill changes all 2D/3D alpha layers without new requests.

## Package checks

- Full ZIP CRC, package `SHA256SUMS`, fresh extraction file count and hashes validated when ZIP assembled.

## Live checks still required

- No installed TAK Map server was accessible from this environment; browser fixtures are synthetic and cannot prove production runtime stability.
- Verify actual sidebar order after load and VEIL refresh, infrastructure show/hide on real saved GIS layers, 2D/3D alpha controls and Blend interaction.
- The open i693 partial radar coverage concern still requires a live NOAA/NWS observation-matched comparison. Phase 3 radar animation remains planned, **not included**.

Retain i693 source and installed data for rollback. Extract i694 to a new `~/Downloads/tak-map-v1.4.0-i694` folder; do not overwrite old extracted versions.
