# TAK Map — i654 Route Creation Phase C source staging

**Status:** Packaged as TAK Map `v1.4.0-i654` from the validated `i653` baseline. Original i653 ZIP remains unchanged as rollback. No live Valhalla deployment test has been performed.

## Behavior implemented

- Exactly **two user-selectable drawing modes**: `Manual` and `Roads`. Mode changes govern subsequent route legs, not previously created legs.
- `Roads` mode uses locally registered NDM Valhalla graph routing via the existing same-origin `POST /api/tak-map/routing/resolve` endpoint, with an optional explicit `unrestricted: true` flag. This opts into supported graph-routing options `ignore_access`, `ignore_oneways`, `ignore_restrictions`, `use_tracks`, and `exclude_unpaved=false`, without imposing application-level road-class exclusions. Absent/unconnected graph edges remain unroutable; this is *not* assurance of legal/safe vehicle access.
- Local `POST /api/tak-map/routing/snap` endpoint queries loopback-only Valhalla `/locate` for the nearest graph road/track edge, without passing arbitrary network endpoints, and enforces session authentication and same-origin. The browser checks **20 screen pixels** at its current zoom; 20px is a point-placement limit, **not** a route length limit. Asynchronous hover preview draws a small circle at the candidate location; snapping is rejected outside that radius.
- Numbered draggable waypoint markers; moving one recalculates only affected route legs using cached unaffected resolved shapes. Network response races cannot overwrite newer leg edits. Undo and Clear preserve existing toolbar actions.
- Clicking an existing route leg inserts a waypoint at its clicked line position, recalculating the two replacement legs.
- Clicking a waypoint opens a compact adjacent context menu with **Manual** and **Copy Coords** (latitude, longitude decimal degrees, six decimal places). Manual toggles that *single waypoint* to freely draggable, without dragging its position back to the nearest road. Nearby Roads legs still follow graph geometry, with any endpoint connector explicitly shown **dashed gold**, and counted in route distance.
- Live cumulative distance (miles) plus **each sequential waypoint-to-waypoint leg** in a small HUD, recalculated on modifications.
- Unconnected road legs are marked as **red dashed failure indicators** with a warning and are **not** serialized as valid routes. Saving is refused while any leg is calculating or disconnected. Manual mode can be selected for a new segment, preserving the previously completed graph legs.
- On save the inherited GeoJSON import path receives the **full resolved LineString vertices**, not just the control points. Existing route fields, name prompt, upload, and cancel actions remain delegated to their existing implementations.

## Source files changed

- `ndm_valhalla_i651.py`: nearest-road lookup, optional unrestricted routing mode.
- `tak_dashboard.py`: runtime JS source mount and authenticated nearest-road endpoint, explicit pass-through of `unrestricted` on `/resolve`. Inserted after i652 wrappers, before main start.
- `assets/tak-map-route-editor-i654.js`: route UI, point/segment state, live snapping preview, editing, context menu, distance HUD, save guards.
- `scripts/test_route_snap_i654.py`: source API/edge-case tests.
- `scripts/test_route_editor_i654_browser.py`: headless interactive mocked Leaflet/Valhalla regression tests.

## Safety / limitations before release

1. The local Valhalla 3.6.3 runtime remains **operator-gated**, not automatically activated. Real, installed NDM navigation graph, healthy Valhalla service, actual host headroom and real curved road tests are still necessary. Browser tests mock the routing service and cannot replace these tests.
2. Manual control point connectors are explicitly marked; saved route geometry includes them. This is a *draft* editor; permanent editable control-point metadata/leg provenance for loaded saved routes needs a later import/export compatibility pass.
3. Road network completeness depends on the NDM graph, which does not necessarily include all off-road trails; unrestricted routing flags may still be limited by graph content or Valhalla version/configuration. Never interpret a calculated route as vehicle authorization.
4. Legacy i491 transient straight-line cursor preview is hidden in Roads mode; retained in Manual. The existing route panel, toolbar, point/shape drawing, mission and source packages are unchanged.
5. Run full browser/end-to-end tests against deployed TAK Map and NDM datasets after packaging. Preserve i653 as rollback; new package only when explicitly requested. Validate source archive, omit artifacts/private files, verify independent extraction and version identity.

## Staged validation

- Backend 6 unit cases for locate parsing, invalid coords, unavailability, opt-in unrestricted routing, and legacy routing behavior.
- Browser mock: Manual/Roads, 20px snapping, multiple waypoints, route-click insert, single waypoint Manual override, dragging, distance UI, save full shape, failed-leg no-save.
- Original i651 16-unit NDM tests, HTTP authorization tests, and release identity/installer contract tests retained.
- JavaScript and Python syntax checks passed. **No live Valhalla smoke test; installation on the target server remains unverified.**
