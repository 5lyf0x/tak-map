# TAK Map i690 — Local validation report

**Baseline:** `tak-map-v1.4.0-i689.zip`; target `tak-map-v1.4.0-i690.zip`.

## Completed checks

- Python 3 `py_compile tak_dashboard.py`, `node --check` for both i690 status JS and changed VEIL JS, and `bash -n install.sh`: **PASS**.
- Focused Python regression modules (`test_i681`, `test_i682_release`, `test_i683_release`, `test_i685_infrastructure`, `test_i686_infrastructure`, `test_i687_infrastructure`, `test_i688_infrastructure`, `test_i689_assets`, `test_i689_http_runtime`, `test_i690_status_backend`): **47 tests PASS**, approximately 10 seconds. Some installed upstream wrappers hold interpreter threads open; the test run itself reports OK.
- i690 Chromium DOM/interaction checks: **PASS** at widths 1440, 760 and 390. Confirms strip dimensions, order, optional TAK Server hidden, authoritative EUD UID dedup, compact VEIL summary and keyed rows, focus retention and Escape behavior, and collapsed-sidebar positioning.
- i689 browser regression: **PASS** at 1280 and 390 (Leaflet startup/replacement, Infrastructure clicks, Icon Registry fallback and themed zoom dropdown).
- i690 actual HTTP tests: **PASS** authenticated JS/CSS GET/HEAD exact bytes and MIME, LAN endpoint shape, app HTML injection, access denial.
- New status-strip installer install commands and required-runtime gate: **PASS** source audit and shell syntax.
- Existing older i688 browser test: exceeded the local timeout; **not counted as passed**. Full live-server / Cesium and real EUD/VEIL hardware testing were **not performed**.
- Historical tests that pinned the exact old version were updated to check the current i690 release, preserving feature assertions.

## Packaging checks

ZIP CRC, source retention, fresh extraction file hashes, version, executable installer and SHA256 recorded at package creation; see final handoff.
