# TAK Map v1.4.0-i676 validation record

Source base: v1.4.0-i675 ZIP (unchanged rollback baseline).

- `python scripts/test_i676_browser.py`: PASS (Chromium end-to-end simulated import/route-save, route-edit/resave, truncation rejection, floating selector, mode below header, viewport clamping)
- `python scripts/test_i676_release_contract.py`: PASS
- `python scripts/test_i675_graph_switch.py`: 4 PASS
- `python scripts/test_i675_http_activation.py`: PASS
- `python scripts/test_route_snap_i654.py`: 6 PASS
- `python scripts/test_i659_route_update_backend.py`: PASS
- `node --check assets/tak-map-route-editor-i654.js`: PASS
- `node --check assets/tak-map-routing-dropdown-i675.js`: PASS
- `bash -n install.sh`: PASS
- `python -m py_compile tak_dashboard.py`: PASS (existing SyntaxWarnings from old embedded JavaScript strings are non-fatal)
- `unzip -t`: VERIFIED at archive finalization
- Fresh extraction hash and mode comparison against source: VERIFIED at archive finalization
- Live installation and 5.1 GiB Valhalla graph switching: NOT PERFORMED in this environment
- Legacy i659 browser test: EXCEEDED EXECUTION TIMEOUT (not counted as passing)
- Legacy i673 MIL-STD test: dependent asset `icons.json` not available (not counted as passing)
