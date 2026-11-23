# TAK Map v1.4.0-i676 — Complete Route Save and Floating Routing Controls

Based directly on full-source v1.4.0-i675. This release changes route-editor and viewport presentation behavior only; i675 regional graph discovery, administrator-only activation, rollback and all existing NDM packages are preserved.

## Changes

### Save the entire trail even when Valhalla cannot resolve individual legs
- The Save Route dialog and underlying route editor no longer require **every** leg to report `ready` before a route can be saved.
- Construct one ordered GeoJSON LineString that includes **every clicked control waypoint**, the full shape for each successfully routed leg, and explicit direct/manual connectors between the endpoints of unresolved or pending legs. These connectors are **not claimed to follow actual roads or trails**.
- Preserve route control-point modes, per-leg geometry boundaries, routing dataset identity, original waypoint order, colors, notes, categories, and the source routing modes. Record unresolved leg indices/count in route metadata. Saved routes can be reopened for editing with these sections distinguishable from routed legs.
- Calculate displayed saved distance from the complete persisted geometry, including direct connectors; this is a geometry distance, **not** a claim of actual drivable distance through unresolved legs.
- Before clearing the editor or declaring success, read the stored route back and verify **every vertex in order** within coordinate-rounding tolerance. A server-truncated or missing saved route is a failure and leaves the entire editable trail intact.
- The dialog warns non-blockingly when direct connectors are present. No route segments are deleted to make Save work.

### Floating Tactical HUD Routing Data selector
- Retains Option 06 styling and total closed-control dimensions of **155 × 25 px**, including a narrow dedicated drag grip.
- Drag within the map viewport, or focus the grip and use arrow keys. Clamp on resize so the control stays on-screen and the package menu can open to a usable side.
- Save viewport-relative placement using browser `localStorage` and restore when Route Creation opens, on browser revisit/refresh, and after TAK Map server reboot (same browser profile/origin). This is **not** cross-device synchronization.
- **Reset Position** in the dropdown restores its safe upper-right default. Selector remains visible only while the Route Creation tool is active.
- i675 graph catalog/activation API and its security boundaries are unchanged; a graph cannot switch while a route is being edited.

### Routing mode visibility
- Position **Manual / Roads / Road network status** in the map viewport below the TAK Map header, no longer obscured by the header. Reposition on viewport resize.

## Scope and safety
- Existing map data, saved routes, NDM regional/state PBFs and graphs, certificates, Gateway/VEIL settings, and i675 rollback source are not removed or overwritten by the source package.
- When Valhalla cannot resolve an isolated leg, the connector is straight between its saved waypoints; users should review the indicated segment before navigating it.
- **Actual server install, NDM/Valhalla integration, live network and real user route were not exercised** in the packaging environment. The completed browser test used mocked routing/import HTTP responses; graph switching tests used controlled service fixtures.

## Validation
- Chromium i676 test: 13 waypoints / 12 legs / 3 unresolved: full save, read-back, route reopen/edit and resave; deliberate truncated server read-back refused without discarding editor — PASS.
- Chromium i676 test: routing-mode control below header, Tactical HUD drag, persistent-position state, reset, 155 × 25 px size and narrower-viewport clamping — PASS.
- i675 graph-switch controlled tests (4), i675 administrator/login/same-origin HTTP test, i654 route snap tests (6), i659 in-place route update backend test, and i676 release-contract test — PASS.
- Legacy unrelated test requiring an unavailable MIL-STD catalog fixture was not counted as passing; the older i659 browser test exceeded the execution timeout in this environment.
- Source syntax, installer syntax, source ZIP integrity, generated SHA256SUMS, executable mode and fresh extraction/source comparison verified for this release.
