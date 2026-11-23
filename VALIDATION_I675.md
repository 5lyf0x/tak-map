# TAK Map v1.4.0-i675 — source-release validation

- i674 original archive source comparisons: no removed files; only the i675 functionality and release files changed.
- `scripts/test_i675_graph_switch.py`: 4 tests passed (activate, rollback, input protection, overlapping jobs).
- `scripts/test_i675_http_activation.py`: login, admin, same-origin, runtime asset, authorized activation passed.
- `scripts/test_i675_tactical_hud_browser.py`: Chromium layout passed at 1742×864 and 1200×760; collapsed selector exactly 155×25 px at x=1580, y=73 in reference layout; expanded menu clears route toolbar; hidden when route inactive.
- `scripts/test_i675_release_contract.py`: version, runtime assets, nonblocking save, styling, MVUM order, installer deployment passed.
- Existing NDM backend, catalog, route snapping and route-update regression tests passed.
- `node --check` passed on four relevant JS modules; `python -m py_compile` passed on dashboard and routing modules; `bash -n` passed for both installation scripts.
- Older test scripts may have historical version-pinned assertions (e.g., i659); not treated as i675 release identity.
- ZIP CRC, clean fresh-extraction comparison, source SHA-256, and executable modes are reverified after final archive creation.
- Actual 5 GiB US West graph activation, on-server systemd restart, live Valhalla route calculation, and full production browser integration still require deployment testing; no live host access is available here.
