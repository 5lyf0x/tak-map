# TAK Map i697 — validation scope

- Exact i696 full-source ZIP SHA256 and CRC verified before staging; all 6,227 original source paths retained.
- User-approved staged i697 patch applied with `patch --fuzz=0` and byte-compared against the expected changes.
- `tak_dashboard.py` Python compile; active radar history JS `node --check`; `install.sh` `bash -n`.
- i696 historical radar backend/browser, imported basemaps, existing weather and UI regressions rerun against i697 source.
- `scripts/test_i697_release.py`: 250k default with environment-override simulation, use of the same cap in download estimates and resume checks, stable radar API endpoints, asset cache-busting, and i697 version identity.
- Chromium regression `scripts/test_i697_slider_browser.py` checks actual radar timeline computed styling against the existing BASEMAP Soft Pill, including timeline filled-progress state.
- New SHA256SUMS created for full source, ZIP CRC and fresh extraction/byte-for-byte comparison performed.
- Host install, live NOAA imagery accuracy, actual 250k downloads and real GPU performance are **not** verified.
