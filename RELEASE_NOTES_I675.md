# TAK Map v1.4.0-i675 — Regional Routing Selection and Route Save Corrections

Based on the validated v1.4.0-i674 source release. This package is full source only and preserves existing TAK Map, NDM, Gateway, VEIL, local-data and map configuration on installation.

## New and changed

- **Routing Data — Tactical HUD (approved Option 06):** Compact 155 × 25 px angular dropdown appears only while Route Creation is active. It is anchored to the upper-right map viewport, below the zoom/coordinates badge, in the user-specified area. The options open to the left, outside the vertical route toolbar.
- **Real routing package activation:** Uses already registered and validated Valhalla 3.6.3 NDM routing packages, including Arizona or US West. An administrator can select a ready package. The server verifies the local source archive, prepares its graph, atomically updates local graph configuration, restarts only `tak-map-valhalla.service`, and verifies service readiness. When activation fails during ordinary execution, the previous configuration is restored. No browser-supplied paths, URLs or arbitrary system actions are accepted. Active route drawing/editing blocks switching; existing saved routes are retained.
- **Non-blocking route save geometry variance:** A geometry difference between the calculated route and saved representation no longer causes the save operation to fail. The system still verifies that a valid route was actually persisted before declaring success. A discrepancy is reported as an informational message. Route geometry, control-point metadata and the measured drawn-path distance are sent to storage; the selected routing dataset ID is also recorded.
- **Executive Slate sidebar cards:** Tightens collapsed row dimensions and status chip styling to match established Geofences/Basemap presentation, including neutral Not Enrolled, amber Offline, green Connected on Mesh Sync. Preserve independent card toggle and collapse actions.
- **Soft Pill (approved Option 05):** Rounded 10 px opacity track and 16 px thumb for USGS shaded relief and stacked basemap opacity controls. Underlying opacity handling and per-source settings remain unchanged.
- **MVUM:** Always insert the text-only MVUM tool above Undo in the compact route toolbar without changing the read-only overlay's behavior.

## Activation boundaries and safety

- Graph switching is administrator-only, same-origin, and accepts only a SHA-256 identifier present in the validated local catalog.
- Only the local pinned Valhalla systemd service is restarted. Existing NDM packages, previous graphs, source files, and saved routes are never deleted by the switcher.
- The existing i651 `/api/tak-map/ndm/activate` operator-gated endpoint is unchanged. The new i675 endpoint is independently authorized and uses a fixed-argument root helper.
- Existing route snippets cannot be recalculated during a graph switch; route planning is available once the selected graph reports ready.
- Real installation on the user's server and actual live Valhalla routing with the ~5.1 GiB US West graph were not performed in the source-build environment. The rollback path was exercised with mocked service operations; the browser layout and management API were exercised in Chromium and local HTTP tests respectively.

## Test notes

- `scripts/test_i675_graph_switch.py`: successful graph activation, prior-graph restoration on failure, invalid input, simultaneous switch guard — PASS.
- `scripts/test_i675_http_activation.py`: login, admin, same-origin gates, browser JS asset, authorized 202 response — PASS.
- `scripts/test_i675_tactical_hud_browser.py`: at 1742 × 864, Tactical HUD measured x=1580, y=73, width=155, height=25; expanded menu clears right controls; responsive 1200 × 760; route-only visibility — PASS.
- `scripts/test_i675_release_contract.py`: release identity, route save, sidebar, Soft Pill, MVUM, installer contract — PASS.
- Inherited `scripts/test_ndm_i651.py`, `scripts/test_ndm_i651_backend.py`, `scripts/test_route_snap_i654.py`, `scripts/test_i659_route_update_backend.py` — PASS.
- Older i659 release-contract scripts that assert their historical version string verbatim should not be interpreted as current i675 release-identity tests. i675 release-contract tests replace those specific identity assertions.
