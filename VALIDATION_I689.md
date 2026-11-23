# TAK Map v1.4.0-i689 — Validation

Source baseline: v1.4.0-i688. Scope: Infrastructure selection, themed min-zoom dropdown, authenticated sidebar static routing, Token Mesh map references, Icon Registry fallback/lazy loading.

## Completed checks

- `python -m py_compile tak_dashboard.py`: PASS (pre-existing embedded-JS Python `SyntaxWarning` messages do not block compilation).
- `node --check assets/tak-map-infrastructure-i689.js`: PASS.
- `node --check assets/tak-map-icon-registry-i572.js`: PASS.
- `bash -n install.sh`: PASS.
- Python regression tests covering i685/i686/i687/i688 infrastructure plus Local Data persistence/recovery and i689 assets/real HTTP routing: **50 passed, 28 subtests passed**.
- Direct HTTP server route checks with a test-authenticated TAK Map handler: GET and HEAD JS/CSS MIME and byte comparison PASS; legacy i684 URL aliases PASS; unknown sidebar asset 404 PASS; actual HTML script URL wiring PASS.
- One known-good bundled Icon Registry image: HTTP 200; 12 concurrent requests with 8 workers: all 200 in the local test handler. This does not establish reliability under the user's nginx/proxy/live load.
- i689 Chromium desktop (1280px) and mobile-width (390px) synthetic integration: map DOM-element startup => valid map recovery; one event binding; 5px line hit path; click ownership and blank-map deselection; selected original color/red outline; failed-icon fallback markup; themed custom listbox and keyboard dismissal; per-layer zoom mutation. PASS.
- Existing i688 and i687 Chromium regressions at desktop and mobile widths: PASS.
- Runtime `tak_dashboard` import and HTML/config version: i689, required sidebar/infrastructure runtime references present; old active i688 reference absent: PASS.

## Remaining production-only checks

- Actual deployed Leaflet SVG/Canvas and Cesium picks across user-imported geometry variants; in-container browser tests use a Leaflet contract mock.
- End-to-end nginx TLS authenticated route checks on the user's server.
- Icon Registry 502 root cause under production proxy/server load; local HTTP service can deliver bundled icons, and this release provides browser-side fallback and lower thumbnail request pressure.
- Real user-data performance with many overlapping dense geometries. No application data was available to this test environment.

## Packaging

ZIP hash, inventory count, clean extraction and preservation checks are recorded in the build handoff. The ZIP is a full source archive, not a patch; installation uses a new `tak-map-v1.4.0-i689/` directory and existing persistent data remains outside the source tree.
