## 1.5.0-i004 — Offline performance installer startup hotfix

- Copy `tak_map_offline_perf_i003.py` into `/opt/tak-map/` with read-only permissions before restarting the service. This fixes the missing-module startup failure in the i003 installer.
- Advance the package `VERSION`, configuration API, left-sidebar version/footer, asset cache identifiers, and installation documentation to `1.5.0-i004`.
- Preserve the full i003 offline tile engine and all existing offline-map/MBTiles data, identifiers, download states, and settings. No unrelated changes.

## 1.5.0-i003 — Offline tile performance and map-row correctness

- Reuse bounded, read-only SQLite connections and a stat-invalidated immutable catalog registry to avoid repeated open/parse work on hot offline tile requests.
- Request offline tiles during continuous panning with a 200 ms interval and smaller retained buffers; keep online layer defaults and preserve per-user stacking, Blend/Tone and opacity.
- Respect native offline zoom limits, use upscaling for higher view zooms and carry source-generation tokens into tile URLs.
- Change missing/partial tile HTTP caching to private no-store; cache successful completed tiles privately and avoid stale 404s after retry/resume.
- Enforce an explicit TMS/XYZ row convention per imported pack, with authenticated catalog-only selector and trusted MBTiles metadata. Do not guess a second row when the requested tile is missing.
- Bound custom pixel Blend work to one tile per browser animation frame and cancel unloaded work.
- Identify the build as 1.5.0-i003 in the left-sidebar footer, server config, source archive and documentation. Preserve i002 map management and saved MBTiles data.

## 1.5.0-i002 — Offline Maps startup and Rename visibility

- Reattach the Offline Map Packs card decoration after asynchronous map core initialization so completed packs expose Rename reliably.
- Render saved offline maps automatically during initial startup and after optional-data refresh; manual Refresh is no longer needed to populate existing saved maps.
- Prevent duplicate Rename controls and retry notes on subsequent lifecycle events and list redraws.
- Advance sidebar footer, API version, cache marker, installation/archive identity to 1.5.0-i002; preserve i001 implementation and saved map data.

## 1.5.0-i001 — Offline Map Packs rename, sorting and footer identity

- Add an authenticated inline Rename action for completed downloaded/imported Offline Map Packs, with Save/Cancel/Enter/Escape and meaningful errors.
- Sort displayed packs case-insensitively and naturally, without mutating catalog order; limit the pack list viewport to 600px and scroll within it.
- Preserve map IDs, MBTiles file/path/content, retry metadata and history; regenerate outgoing EUD package names only on subsequent Send.
- Remove the old 80-record catalog truncation and serialize catalog mutations to avoid losing records on rename/update.
- Advance the left sidebar footer, runtime API/version, archive and install documentation to TAK Map 1.5.0-i001 while neutralizing stale i621/i665 footer updates.
- Preserve existing datasets and i699 rollback package. Live server validation remains outstanding.

## v1.4.0-i699 (2026-11-13)

- Offline Maps: fetch authenticated basemap source catalog after startup, recover empty source dropdown, and refresh after imported XML changes.
- Offline Maps: Command Slate card fields, no West/East/South/North coordinate readout, no header icon, matching dropdown typography, no dropdown chevrons, Preview Max and Download buttons without icons.
- Per-user basemap stack: server-authoritative stable account preferences for ordering, visibility, opacity, Blend/Tone and custom detail settings, revision-conflict protection and durable atomic persistence.
- Previous browser-only basemap settings may be imported explicitly under the authenticated account; no cross-user automatic migration.
- Next development series after i699: v1.5.0-i001.

## v1.4.0-i698 — U.S. state offline download regions and reliable single-pack recovery (2026-11-13)

- One searchable Download Area selector: Current View, Draw Area, 49 states, and Northern/Central/Southern California = 54 selections.
- Built-in geographic boundaries, map stroke preview and polygon-clipped XYZ tile selection; Alaska and Hawaii supported.
- Automatic internal splits above 250,000 tiles, still stored as one MBTiles map with one user-facing status and durable internal batch manifest.
- Initial tile request plus up to three retries; continue on exhausted failures and preserve missing-tile coordinates within MBTiles.
- Retry/Finish recovery actions, targeted missing-tile re-download and Finish As Is without losing recovery data.
- All configured URL-template basemaps eligible, including persisted Custom XML imports; no provider blacklist or whole-map tile cap.
- Offline Maps action renamed **Download**. Preserve i697 radar, basemap, Local Data and terrain improvements.

## v1.4.0-i697 — Radar history Soft Pill and Offline Maps 250k default (2026-11-13)

- Apply canonical basemap opacity Soft Pill track/thumb to the separate radar history timeline. Preserve historical frame timestamps, scrubbing, playback and radar opacity slider.
- Increase the default maximum for a single offline map download from 20,000 to 250,000 tiles. Preserve existing environment override, estimate, range validation, resumable jobs, concurrency and MBTiles storage.
- Bump runtime iteration/version and cache-bust all application assets. Preserve i696 historical radar endpoints and registered data.

## v1.4.0-i696 — Radar history and terrain/2D reliability (2026-11-13)

- Authenticated NOAA MRMS historical frame catalog and bounded tile proxy; UI Play/Pause, timeline, step, speed, windows, Loop, LIVE. Last-good retained and no synthetic frames.
- Radar swap/reattach hardening, 2D imported basemap list sync and tile-source failure warnings.
- MVUM button in Route Creation and zoom-9 composite vector overlay; bottom-of-chart cursor mileage.
- Local Data persistent point-ID edit; permanent automatic Basemap Pre-cache feature/code removal.
- Local High-only DEM quality and 3D camera-motion performance/imagery-overlay fixes; NDM prepared terrain remains verification-gated.

## v1.4.0-i695 — Infrastructure and BASEMAP interface follow-through (2026-11-13)

- Infrastructure header upgrade repairs missing Show/Hide switch on pre-existing cards; switch remains independent of collapse and GIS layer selections.
- Sidebar card titles use consistent Infrastructure-style typography, expanded or collapsed.
- Radar opacity uses shared BASEMAP Soft Pill with old weather controls migrated, saved opacity preserved, and no imagery refetch on slider movement.
- Infrastructure GIS detail actions appear after the last GIS attribute.
- Retired legacy automatic Basemap Pre-cache/background tile fetching while preserving normal on-demand tiles and OFFLINE MAPS.
- Infrastructure categories use Extended Divider / Manrope 550 14px 0.01em; layer names use Clear Type 12.5px 750; dynamic object counts appear beside names at a 12px gap with their existing font/format.
- Release identity and runtime cache-busting incremented to i695. No new NOAA history playback in this UI release.

## v1.4.0-i694 — BASEMAP and Infrastructure UI reliability

- Apply the same Soft Pill opacity control to Radar Reflectivity as to basemap layers, with direct 2D/3D alpha updates, preserved percent and persistence, and no tile reloads or layer recreation during dragging.
- Preserve the Blend dropdown while selecting any available mode, with immediate application/selection highlight; dismiss on outside click or Escape.
- Permanently reposition Infrastructure immediately after BASEMAP and before VEIL with a resilient selector, sidebar mutation repair and existing probe; correct both VEIL scripts so their own recurring order repair respects Infrastructure instead of fighting it.
- Add a saved green-ON/gray-OFF Infrastructure visibility toggle in the card header that independently hides/restores Leaflet/Cesium features without changing individual layer settings or collapsing the panel.
- Refresh version and browser asset cache markers. Radar partial-coverage fixes from i693 and NWS alerts remain unchanged. Phase 3 radar animation is not included.

## v1.4.0-i693 — radar tile coverage, partial-status and stable frames

- Radar refresh selects a catalog-backed NWS observation where available, and explicitly labels time-range fallback timestamps as provisional.
- Per-tile server retries and bounded concurrency no longer invalidate healthy radar tiles because of two failures.
- Browser retries individual failed XYZ tiles, reports viewport tile progress/partial coverage, and preserves prior radar imagery while a new frame begins loading.
- Reuses existing NOAA authenticated same-origin proxy and unchanged NWS alerts/settings, including persisted opacity and basemap.
- Phase 3 radar history/animation remains separate; i693 is radar reliability only.

## v1.4.0-i692 — 2026-11-12

- Replaced direct browser cross-origin weather radar WMS loading with authenticated server-side NOAA/NWS tile proxy and provider fallback, with 2D/3D tile parity and bounded cache; existing NWS alerts preserved.
- See `RELEASE_NOTES_I692.md` and `VALIDATION_I692.md`.

## v1.4.0-i690

- Integrated status indicators above the map, ordered EUDs / VEIL / Downloads / LAN / Internet with conditional TAK Server; removed ADS-B from the status bar only.
- One authoritative online EUD snapshot for count and dropdown; VEIL node details from existing subscription state, no extra VEIL polling.
- Stable keyed dropdown DOM and scroll/focus preservation, LAN health endpoint, safe asset delivery and installer checks.
- Preserves existing map, Infrastructure, routing, VEIL and Token Mesh functionality.

## v1.4.0-i689

- Authenticated sidebar i684 JS/CSS runtime asset serving fixed (HTML-as-JS 200 regression).
- Infrastructure startup now validates real Leaflet instances; line/point selection event ownership and duplicate feature IDs hardened.
- Themed, slender-scrollbar per-layer minimum-zoom listbox replaces Windows-native dropdown.
- Token Mesh browser refresh uses validated map reference.
- Icon Registry lazy thumbnail decoding and point marker fallback when icon assets fail to load.
- Added real HTTP-handler and Chromium regression tests. No changes to existing application data paths.

## 1.4.0-i688 — Offline Infrastructure reliability and indexed GIS search

- Offline-only Infrastructure card with explicit GIS downloads and non-destructive saved data; 5px line hit, original layer color plus red 2px selection outline, reliable deselection.
- Cold-start hydration, atomic viewport loading with stale-request cancellation/retries, dropdown controls stable during polling, Object Details padding and always-visible GIS attributes.
- Persistent per-point-layer TAK Icon Registry symbols, multi-rule per-layer attribute filters before 5,000-feature display sampling, indexed whole-dataset Infrastructure search through the existing sidebar.
- See `RELEASE_NOTES_I688.md` and `VALIDATION_I688.md`.

## 1.4.0-i687 — Mode-specific Infrastructure and City sewer structures

- Mode-specific category hiding/restoration; per-layer minimum zoom, default manhole z14; City of Los Angeles SewerStructures built-in; geographic distribution; status accuracy; remove Infrastructure hover tooltip.

## 1.4.0-i686 — Infrastructure source/view limits and mixed rendering

Infrastructure Overlays now supports simultaneous Online + Offline display, 1.5× viewport buffers, 5,000 per-layer display budgets, progressively streamed ArcGIS feature pages, user-selected per-layer persistent colors, visible/stored counters, and multi-expand categories. Existing datasets and exports are not truncated. See `RELEASE_NOTES_I686.md` and `VALIDATION_I686.md`.

## v1.4.0-i685 — Infrastructure overlays and collapsed-heading parity
- Add a separate Infrastructure card with a 14-category shared catalog in Online and Offline modes, user categories and GIS source management.
- ArcGIS REST viewport queries; offline geographic downloads with resumable staging and no TAK Map speed cap; independent indexed storage and GIS import/export.
- Large sewer mains 36 in+ filter, Leaflet/Cesium display, hover tooltips and direct right-hand Object Details selection.
- Correct i675 collapsed font overrides and Mesh Sync header/chip parity; explicitly install i684 sidebar styles that previous install.sh omitted.
- Preserve i684 routes, Local Data, NDM, VEIL and Token Mesh; no migration of existing stores. Live server/provider tests pending.

## v1.4.0-i684 — Route interaction reliability and sidebar parity
- Selecting a saved route via Object Details opens the elevation profile; selection/deselection and X dismissal are respected.
- Cancel Route Edit invalidates in-flight routing requests and removes stranded waypoint handles, draft labels, and hit layers without changing saved geometry.
- Route Details removes only the Points display row, formats route properties on independent lines, and preserves user-entered notes and route geometry.
- Extended elevation metrics have reduced dead space, and chart height is 188 px (down from 250 px); view switches bottom-center with 24 px margin.
- Sidebar card surfaces, title typography and status chips are standardized. VEIL toggle/header uses fixed trailing slots for consistent alignment.
- Satellite Tracking precedes Offline Maps; no features/settings are recreated or reset.
- All i683 MVUM/Local Data/basemap fixes and persisted data locations are preserved.

## v1.4.0-i683 — Floating route elevation, steep-run hover details and MVUM fixes
- Default compact floating Route Elevation profile (82px graph), with Route Distance aligned to the right side of the draggable title header, thin grade legend and an Expand control for the approved detailed profile.
- Header supports grab/grabbing cursor, bounded pointer/keyboard dragging, saved position and viewport re-clamping. Expand and Close remain separate from the drag handle.
- Display the elevation panel only during Route Creation, a selected route or an edited route; automatically hide on route exit/deselection or non-route selection. X fully closes, and dismissal remains until intentional reopening or a new session.
- Color terrain slopes by angle (under 15°, 15–25°, 25–35°, ≥35°); group contiguous steep samples into numbered markers. Hover/focus shows each run's distance in feet, maximum angle, direction, change in elevation and route mile; clicking opens extended steep detail. Terrain values come from NDM, never simulated by the app.
- Restore MVUM button independently of early Leaflet initialization and toolbar replacement. Render parent fallback from vector features rather than magnified raster tiles, maintain narrow strokes and high-DPI clarity, and eliminate failure-triggered global overlay redraw flicker.
- Preserve all i682 Local Data reliability and Basemap Blend fixes; no database changes or migration. Not validated against a live deployed server.

## v1.4.0-i682 — Local Data session integrity and Basemap Blend label correction
- Retain the complete saved set of Local Data routes, points and shapes across reload and restart; remove silent import eviction and feature truncation; verify storage writes and stable object IDs.
- Treat unreadable existing catalogs and API failures as explicit errors, preserving last successfully loaded objects rather than displaying an empty authoritative state.
- Make selected object deletion and route updates return compact, JSON-serializable acknowledgements with canonical readback checks.
- Update the Basemap Blend dropdown visible label immediately when selecting every blend option, including lower custom raster modes; preserve the scroll position for custom controls.
- Preserve established Local Data storage and basemap preferences on installation; no destructive migration. Live deployment verification remains required.

## v1.4.0-i681 — MVUM, 2D/3D continuity, route elevation
- Repair MVUM toolbar button after route toolbar is recreated; no duplicate map handlers or global redraw polling.
- Preserve the ground focal point and approximate ground scale when toggling Leaflet/Cesium. Use Cesium look-at target for 2D→3D and pick center-screen terrain for 3D→2D. Elevation is terrain-relative where terrain height is available.
- Add a live full-route elevation profile for creating/editing routes, and a Profile action on saved routes. Distance-spaced NDM DEM sampling follows every curved resolved segment. Missing terrain stays a visible gap; no waypoint-only profiles or fabricated samples. Floating panel is horizontally centered in the actual map viewport, 20px from its lower edge.
- Preserve i680 read-only Local Data response recovery and i679 complete-route persistence; no migration or saved-data modifications.

## v1.4.0-i680 — Local Data response recovery
- Recover the full, read-only canonical Local Data response if optional enrichment cannot be serialized; preserve all existing route coordinates and identifiers.
- Guard missing Basemap Tone defaults for newly loaded basemap providers.
- Keep route persistence and existing data untouched.

## v1.4.0-i679 — Full-length route persistence
- Eliminate 1,000-vertex truncation in canonical Local Data and HTTP JSON; preserve full routes and edit parity up to 200,000 vertices within 32 MiB.
- Keep save verification strict; add read-only legacy truncation audit, full import/disk/API/reopen test coverage, and preserve i678 for rollback.

## 1.4.0-i678 — Nov 10, 2026
- Exclusive Route Creation pointer handling over unrelated map objects, including NWS alert polygons.
- MVUM red (#E53935) at z10+, visible tile priority, stale-buffer pruning, retries and per-side 50% viewport prefetch.
- Canonical Soft Pill opacity styling; grip-only reordering; removed old arrow and periodic re-styler.
- Equal-width floating Blend and Tone menus; nine CSS blend modes; three CORS-gated pixel-processed cartographic modes; per-layer saved settings.
- Explicit, authenticated regional OSM road/trail name-index build and sidebar search when index is available.

## 1.4.0-i677 — Nov 10, 2026
- Fix route save verification: bind to server-created import ID rather than ambiguous filenames; preserve strict full-geometry read-back, existing route edits and editor-on-failure.
- Correct 2D managed basemap tile stacking, legacy raster masking and optional relief overlay pane; keep layer ordering and Soft Pill opacity settings.

## 1.4.0-i676

- Preserve every clicked route waypoint and all resolved road geometry during save; unresolved connections become explicit direct connectors rather than blocking or truncating the trail.
- Verify every vertex in the stored route before declaring save success. Failed verification retains the entire editable route.
- Add compact, draggable Tactical HUD Routing Data selector with browser-persistent viewport-relative placement, reset and keyboard adjustment.
- Move Manual/Roads route controls below TAK Map header into map viewport.

## 1.4.0-i675

- Add 155 × 25 px Tactical HUD routing graph selector in map viewport during route creation; authenticated actual switching of registered Valhalla 3.6.3 graphs with rollback on failure.
- Make saved-route geometry variance informational instead of a blocking error while retaining stored-route verification.
- Match collapsed sidebar card styling, implement Soft Pill opacity sliders, and keep MVUM directly above Undo.
- Preserve i674 rollback, server configuration, NDM packages, graph data, and existing saved routes.

## 1.4.0-i674

- Replace Tools Export All Data with encrypted selective Backup/Restore (13 independent categories).
- Add secure admin-controlled archive creation, verification, selective restore, credential and offline package preservation.
- Add guarded offline maintenance restore for Mesh Sync and Data Sync journals.
- Preserve i673 rollback and existing TAK Map application data during installation.

## 1.4.0-i673

- Route distance panel: Reverse (direction-aware routed leg revalidation) and Back to Start (append NDM/Valhalla navigated return leg); both support undo, atomic updates, and safe failures.
- Local route details: compact Edit/Delete buttons with 12 px edge padding.
- MVUM: text-only first route toolbar button toggles buffered and cached NDM active-Valhalla navigation graph geometry via authenticated read-only vector tiles. This is not the USDA legal MVUM dataset.
- Viewshed elevation: NDM registered terrain.sqlite Auto-priority sampling using read-only derived cache, full sample coverage checks, and safe Esri/USGS fallback.
- BASEMAP: collapsible, multi-select checkbox list with independent opacity sliders and drag reorder; retain Leaflet layers and persist settings.
- Installer: deploys i673 NDM elevation module, overlay and basemap runtime assets; retains executable permissions and old release sources untouched.
- Validation: offline targeted tests and Chromium basemap smoke PASS; NDM live server, terrain and Valhalla tile integration NOT tested in this environment.

## 1.4.0-i672

- XTAK VEIL APRS icon parity with original Node Map r50 ten-icon artwork and category resolver; preserve API/UDP symbol data through deduplication.
- VEIL aircraft heading/course normalization with 0° support; white aircraft fill and 1 px black stroke (down from 2 px).
- Correct executable installer file mode preserved in ZIP.

## v1.4.0-i671
- VEIL ADS-B white aircraft silhouettes with 2 px black stroke, aircraft icons scaled by 20%.
- Range Rings multi-direction labels, color picker trigger and map center crosshair.
- VEIL Node Map APRS artwork integration pending authoritative upstream assets.

## v1.4.0-i670
- Replace XTAK VEIL generic/A3 ADS-B marker with bundled original ADS-B Exchange tar1090 aircraft silhouette paths and upstream ICAO designator mapping; use validated type fields, fallback only when shape/type unavailable.
- Preserve military/civilian/government/unknown color, heading rotation, and shared ADS-B details panel in Leaflet and Cesium, without altering VEIL API/UDP sync or Range Rings.
- Preserve original 30 silhouette paths and 376 type mappings in vendor data, with GPL/third-party credits.
- Update version/cache identity and add browser-level and mapping regression checks.

## v1.4.0-i669
- VEIL Phase 1/2/3 repairs, A3 ADS-B target rings/color/heading + shared ADS-B details in 2D and 3D; multi-set terrain-aware geodesic Range Rings and sidebar order correction.

## v1.4.0-i668 — XTAK VEIL Phase 3

- Canonical validated ICAO24/MMSI/APRS/typed Remote ID identity envelope is retained from UDP and authenticated Live SA observations. Independent observations remain source-owned; browser chooses a single display representative for verified duplicate VEIL targets.
- VEIL dedup is on by default within VEIL; optional cross-source native ADS-B/Gateway AIS marker suppression is off by default and requires an actually visible, recent native marker. Uncertain IDs are never merged.
- Add a compact read-only node health panel gated on master ON, explicit subscription, reachable node, and existing authorized API token; 22-second bounded cached fetch, no health-triggered login, raw private network/config removed.
- Saved editable local routes now show equal-width Edit | Delete buttons in the same row; unchanged callbacks and confirmation.
- Update runtime version, cache busting, assets, regression tests, and source manifest for i668; preserve all earlier terrain / Token Mesh / Gateway / NWS fixes.

# TAK Map changelog

## 1.4.0-i667

- Render saved, imported and Data Sync routes and supported shapes above Cesium streamed/local terrain in managed overlays with viewport-aware geometry.
- Preserve saved route stroke and shape color, fill, opacity, thickness and dashed styles where supported.
- Honor explicitly selected custom ATAK icons in both 2D and Terrain Mode rather than generic affiliation symbols.
- Add Edit Route to the contextual sidebar for verified source-owned local saved routes, reusing the existing route editor.
- Fix Icon Registry full-width grid, 2D custom-icon image precedence, and offscreen saved-route label suppression.
- Show compact route name/total label at visible saved route endpoints in 3D with a plain line leader (zoom z11+).
- Preserve the i665 root-DOM fix, i666 VEIL Phase 2, existing saved data and source settings.

# TAK Map v1.4.0-i666 — VEIL authenticated sync and compact saved-route labels

- **Hotfix included:** constrain release marker text updates to the real version UI, never the `<html>` root (the confirmed i665 blank-page cause); update runtime/cache/footer identity to i666.
- **XTAK VEIL Phase 2:** explicit optional node API pairing, bearer-authenticated Live SA snapshot and WebSocket stream, bounded replay/catch-up, UDP CoT fallback, opt-in local credential persistence, guarded four-condition automatic login prompting (global ON, subscribed, reachable, authorization required). Existing i665 nodes remain unsubscribed until explicitly paired.
- **Sidebar:** make the entire MESH SYNC and XTAK VEIL header clickable and keyboard collapsible, independent of their switches; match standard sidebar header typography; remove icons from VEIL LIVE DATA labels only.
- **Saved routes:** at z11+ show a compact endpoint callout with route name above total distance, offset from the line with a plain leader. Preserve individual leg measurements during create/edit and all stored geometry.
- **Installer:** include the new standalone standard-library VEIL API module, JS and CSS; preserve previous application data, node configuration and secrets. Source ZIP remains free of runtime secrets.
- **Limits:** Cross-node/other-source dedup and remote VEIL configuration remain deferred; actual physical VEIL-node integration requires live validation.

# TAK Map v1.4.0-i665 — XTAK VEIL receiver and viewport-safe NWS details

- Functional Phase 1 VEIL local node discovery and multi-node UDP CoT reception, persistent node settings, map overlays and status. Includes standard VEIL card and approved discovery/modal UI.
- NWS alert popup contains long Description in full-width internally scrollable field and clamps overall height to map viewport; removes Instruction.
- Fix release/footer iteration to i665; preserves i664 rollback source, application data, Gateway/Token Mesh settings.
- See `RELEASE_NOTES_I665.md` for limitations and operator setup.

# TAK Map v1.4.0-i664 — AIS Details alignment and MESH SYNC cosmetics

- AIS Gateway context Details section uses full-width native label/value grid rows for every parsed AIS field instead of an unstructured blob in the right column. Source strings are escaped. No changes to other Gateway sources or AIS ingest.
- MESH SYNC status chip no longer displays its leading bullet, and the ON/OFF toggle matches the existing gray/green sidebar switch style. Preserve all layout, controls and state logic.
- i663 remains untouched as the rollback baseline; update does not remove persistent app data or modify Gateway connections.

# TAK Map v1.4.0-i663 — Mesh Sync header alignment and text legibility

- Keep MESH SYNC header in one row: title, connection-status chip, network ON/OFF toggle, and independent collapse arrow at far right.
- Prevent auto-collapse logic from relocating header controls. Persist the Mesh card collapse state separately from persistent Mesh networking state.
- Increase small labels, Mission actions, joined count, enrollment guidance and metrics by one typography step.
- Preserve all i662 Token Mesh/Mission backend behavior, OTS Data Sync, Gateway Data, and saved application data.

# TAK Map v1.4.0-i660 — Token Mesh synchronization candidate

- Added separate persistent Token Mesh v2.0 Mission journal, XTM1 creation/join/leave, XMS1 Mission invitation binding, QR creation/image export and manual join.
- Added server-owned XMS2 encrypted UDP discovery and XTP3 v3 authenticated encrypted TCP peer sessions with Mission-gated bidirectional journal reconciliation, checkpoint handling and tombstones.
- Added independent MESH sidebar and read-only on-map projection of received CoT Point/Route/Area payloads with visible Mesh provenance. No automatic OTS/TAK Gateway bridge.
- Local Python-to-Python bidirectional sync and protocol tests pass. **NOT Android cross-app certified:** TAK Rig and XTAK Data Sync byte-level/device tests have not run. Advanced native editing/publication, FILE transfer, route semantics and all TMS-FINAL acceptance checks are not yet complete. Do not equate local success with production readiness.
- Preserves existing i659 route-editing functionality, saved data and installation layout; i659 remains rollback.

# TAK Map v1.4.0-i659 — Saved-route and waypoint editing

- Add **Edit Route** inside the existing popup for saved imported routes. Keep the normal Route tool and Roads snapping; preserve all original route geometry when reopening, with individually editable control waypoints.
- Drag existing waypoints, click any route leg to insert a waypoint, and use a very compact bold waypoint menu (Manual, Copy Coordinates, Delete; ~4px padding). Recalculate only changed road legs and update segment distances/labels.
- When editing a saved route, offer **Save Changes**, **Save as New Route**, and **Cancel**. Save Changes updates the same canonical Local Data object ID; Save as New Route opens the standard name/color/category/notes dialog and retains the original. Cancel discards changes.
- Store original control points and per-leg geometry indices in route metadata so a reload restores editing handles without replacing the snapped route with straight lines. For older i658 saved routes without control-point metadata, reconstruct approximate controls along their intact saved geometry; verify placement before saving alterations.
- Validate update requests through authenticated route-only endpoint with stable-ID matching, data integrity checks, atomic writes and a stale-edit revision guard. Never replace unrelated imports or local objects.
- Retain i658 live route preview, road snapping, on-map distances, Roads/Manual selector, NDM graph activation, user configuration and existing data. The i658 source package remains rollback.
- Browser tests simulate actual production route save modal and popups; backend tests use a real stored import registry and verify stable IDs, revisions, rejection paths and integrity. Live deployment and graph routing need operator confirmation.

# TAK Map v1.4.0-i658 — Reliable Roads routing UI and persistence

- Unify inline and browser-deferred Save Route dialog scripts to prevent the legacy handler from saving only clicked waypoints. The real route-save path uploads every snapped polyline coordinate and compares coordinates in the import response before clearing the editor.
- Restore a visible upper-right Roads/Manual mode selector (Roads remains the default), with route-tool visibility checks.
- Preview the next connected road segment between the last waypoint and the cursor, using the routing engine; show progress while routing and retain earlier completed segments. Manual mode previews a straight line.
- Expand the Route Distance panel upward, anchored at the bottom. Remove the short internal leg-list scrollbar; limit scrolling only to viewport height.
- Show unobtrusive per-leg mileage labels at distance-weighted midpoints along completed road geometry. Persist their positions in route GeoJSON metadata for import/reload display.
- Preserve the 20-screen-pixel snapping threshold, other legacy map features, NDM integration, existing user data and configuration. i657 stays the rollback source; no bundled routing graph or binary.
- Validation tests use Chromium with both production dialog script copies and the actual editor, plus ZIP fresh-extraction comparison. Live TAK Map and actual NDM/Valhalla route saving remain to be checked by operator.

# TAK Map v1.4.0-i657 — Snapped route save dialog integration

- Fix the existing **Save Route** modal so its Save button uploads the full Roads-mode snapped polyline instead of only the clicked waypoints. This addresses a legacy save handler taking back control after the newer route editor initializes.
- Preserve the route name, category, selected color, notes, distance, control-point metadata and full road geometry. Route reload continues through the existing GeoJSON import/display path.
- Keep the editor and modal open if an upload fails; block saving while a road leg is still disconnected or calculating.
- Maintain i656 Manual/Roads modes, 20px snapping, drag editing, NDM registration and Valhalla configuration. This release does not change graph data or automatic routing startup.
- Normal in-place installation retains existing configuration, credentials, downloaded navigation and elevation, saved routes, and persistent data; i656 source remains the rollback baseline.
- Validation in this environment uses the actual browser dialog with a mocked local routing response and upload. Live server route save/readback must still be confirmed after installation.

# TAK Map v1.4.0-i656 — Lossless snapped-route save

- Fix: Save Route now writes the full calculated Roads polyline directly as a GeoJSON LineString, rather than temporarily replacing the editable clicked-waypoints list for legacy save handlers.
- Retain intermediate vertices, curves and turns; preserve the route name, notes, color, style, movement and waypoint/segment metadata.
- Successful upload refreshes saved routes and exits the editor. Failed upload leaves the route editable. A rejected/disconnected leg remains unsavable.
- Retain i655's Roads-default UI, 20px preview, active graph startup, NDM registration and status management. No changes to Valhalla activation, NDM graph files, authentication or user data.
- Live service and save/readback must be verified after installation; browser tests use a simulated routing backend.

# TAK Map v1.4.0-i655 — Routing readiness and dataset lifecycle

- Delayed-map initialization repair; top-right Manual/Roads selector; Roads default with routing readiness status.
- Safe localhost-only Valhalla autostart when a prepared graph exists; explicit missing-coverage handling.
- Background NDM rebuilt-ZIP registration, superseded/history status, safe Unregister controls.
- Multi-state seamless routing remains blocked until NDM produces a connected shared graph across state boundaries.
- Preserves i654 rollback, data, credentials, and files.

# TAK Map v1.4.0-i654 — Interactive NDM route snapping and waypoint editing

- Add two route modes (Manual and Roads), 20-pixel cursor snapping preview and closest-road lookup via loopback Valhalla.
- Support dragging waypoints, inserting a waypoint by clicking a route line, and a compact per-waypoint Manual / Copy Coords menu.
- Show live total route distance and per-leg distances; mark disconnected roads and prevent saving incomplete routes.
- Preserve resolved polyline vertices when saving, with mixed Manual/Roads legs and clearly distinguished manual connectors.
- Deploy the new JavaScript as a required runtime asset and verify the asset route after service restart.
- Preserve the i653 application, existing NDM graph/terrain packages, configuration and credentials. Local Valhalla activation stays operator-gated until host tests.

# TAK Map v1.4.0-i653 — NDM registration limits and 4 GiB imports

- **Existing on Server:** remove the browser-upload file-size quota from read-only registration of discovered NDM ZIPs (including large California navigation packages). Preserve source archives; validate ZIP structure and hash without copying them.
- **Upload ZIP:** increase the browser/server limit to 4 GiB (4096 MiB); use a dedicated Nginx import location and frontend size policy without raising unrelated upload limits.
- Increase bounded archive member-count/expanded-data safety thresholds for large NDM state datasets while retaining path, symlink, integrity and invalid-schema protections.
- Improve quota/missing-file messages and remove the fixed browser-upload timeout. NDM modal remains in Tools with the existing i652 asset identifiers and refreshed i653 cache query.
- Preserve the Valhalla 3.6.3 local service integration, existing datasets and settings; registration does not activate routing. California terrain files with a nonconforming or legacy schema still require format-specific validation.

## Next TAK Map i653 — NDM registration and 4 GiB ZIP upload repair (staged, not packaged)

- Fixes i652 `ZIP missing or exceeds import quota`: **Existing on Server** registration no longer applies browser file-size quota to any NDM routing or terrain ZIP already on the server. Original NDM archives remain read-only, unchanged, and are never reuploaded or duplicated.
- Raises **Upload ZIP** limit from 1.5 GiB to **4 GiB (4096 MiB)**, including backend, narrow Nginx endpoint, and browser preflight. Preserves 400M upload limit on unrelated endpoints and prevents fixed 30-minute browser upload timeout.
- Keeps ZIP path/symlink safety, bounded extraction/CRC/SQLite and graph checks, authorization, no-Valhalla-start, and free-disk checks. Broadens archive member/expanded-data safety ceilings to accommodate large NDM states; these are integrity safeguards, not an existing-file upload quota.
- Reports distinct file-missing, permission, excessive-upload and insufficient-disk errors, and exposes the configured upload cap through the catalog API for the modal.
- Only source staging; i652 release/rollback ZIP unchanged.

# TAK Map v1.4.0-i652 — NDM Data Tools modal

- Adds **Tools → NDM Data** next to Add Elevation Data, opening an administrator-controlled navigation/elevation dataset modal.
- Existing on Server: discover/read-only-register NDM navigation and terrain ZIP packages without duplicating or modifying source archives.
- Upload ZIP: upload and validate local NDM packages through existing i651 secure APIs, with file size checks and progress indication.
- Shows registered datasets, availability, state/region, and source ownership; supports refresh and duplicate detection.
- Preserves existing Add Elevation Data (browser-local terrain), TAK Map data/configuration, all i651 NDM catalog and Valhalla runtime functionality. Neither import nor registration starts Valhalla.
- Valhalla routing service remains operator-gated/disabled until live routing checks. Snapping editor and NDM terrain sampling remain later development stages.

## Next iteration i652 — staged, not released (Tools-card NDM Data)

- Add **NDM Data** inside the existing Tools card, following Add Elevation Data. Open a modal with Existing on Server and Upload ZIP tabs for both NDM navigation and terrain packages, plus a persistent registered-dataset list.
- Use the existing i651 authenticated NDM catalog, discovery, registration and raw ZIP import APIs. Read-only registration never modifies or duplicates original NDM ZIPs; imports show progress and are administrator-only.
- Keep Valhalla service activation separate and disabled. Preserve all existing browser-local elevation importing, route behavior, i651 release identity and data.
- Add focused Chromium/UI, backend asset-routing, installer and regression tests. No i652 ZIP built.

# TAK Map v1.4.0-i651 — NDM backend integration test release

- Adds bounded Utah-compatible NDM Valhalla routing and terrain ZIP inspection, SHA-256 catalog, authenticated admin-only imports and read-only existing-dataset registration. User-created imports persist outside /opt/tak-map; imports never delete external NDM data.
- Adds operator-gated Valhalla 3.6.3 local routing adapter and CLI to select an active config for controlled service smoke tests. Generated config is limited to localhost 127.0.0.1:18882 and an integrity-verified graph tar. HTTP routing returns connected decoded polyline geometry; failed routes never become straight segments.
- Installer provisions official pinned-SHA-256 Valhalla 3.6.3 native Linux wheel on x86-64/ARM64 (glibc 2.28+) under `/opt/tak-map/vendor/valhalla-3.6.3/` **before changing TAK Map**. Online PyPI access required; unsupported/failed installs abort safely. The separate service is installed disabled pending real graph validation on target host.
- NDM catalog API is available to authenticated clients; mutations require administrator and exact same-origin browser request; NDM uploader isolated in Nginx to 1536M. Existing 400M general upload limit remains.
- Does NOT add route snapping to the editor or NDM import to the browser elevation modal yet. Those remain phases C and D.
- Keeps i650 as rollback release and preserves existing HTTPS certificates, Gateway/Replay config, Missions, local elevation and application data.

# TAK Map changelog

## 1.4.0-i650

- Restore visible **Cert Setup** next to Account with CA status, fingerprint, and current CA download. Protect certificate generation/regeneration behind administrator-only, same-origin POST and explicit confirmation; legacy unprotected certificate generation is retired. Existing certificate trust is not changed automatically.
- Remove empty-square AIS fallback: neutral sea-surface vessel symbols use registered artwork with visible maritime glyphs, including unknown vessel types and failed specific SVG loads. Preserve 48×48 MIL-STD registry rendering and selected-only AIS red glow.
- Extend existing general map search to currently displayed live ADS-B and AIS objects, with callsign, registration, ICAO, owner/operator, vessel name, MMSI and class matching; results focus and open existing object detail panels. Hidden, removed, and Replay-suppressed objects are excluded.
- Synchronize Gateway standalone and deferred render paths; deploy the two new runtime modules and preserve prior configuration, Replay, application data, and i649 rollback.

## Next iteration — staged (not released)

- Extends the **general map search** to currently rendered ADS-B aircraft and visible Gateway AIS vessels (not hidden, removed, or Replay-suppressed records). Searches callsign, ICAO/hex, registration, owner/operator, vessel name, MMSI, and class; a result centers the map and opens the existing object details panel. Refreshes the index as live markers change, without altering Data Sync search.
- Prevents blank green Gateway AIS markers: rejects empty generic sea-surface artwork as a vessel classification and retries failed neutral maritime SVGs through the registered civil-vessel symbol, not a synthetic or blank icon.
- Restores a visible **Cert Setup** button beside Account in the TAK Map header, after earlier account-layout cleanup removed both the control and its modal.
- Opens an authenticated HTTPS certificate status/download modal, showing the SHA-256 CA fingerprint and download link without modifying existing certificates.
- Restricts certificate generation/regeneration to signed-in administrators with a same-origin JSON request and explicit typed confirmation. Retires the obsolete unprotected generation URL.
- Adds a dedicated runtime asset, installation and runtime-gate checks, and Chromium/backend validation. The released i649 package remains untouched.

## 1.4.0-i649

- Make the TAK icon registry and bundled MIL-STD-2525C catalog authoritative for all tactical CoT/SIDC markers, including Gateway AIS, CoT markers, and Data Sync. Remove legacy generated frame/X line-art tactical fallbacks from active rendering paths.
- Resolve Gateway AIS objects universally as neutral sea-surface MIL-STD symbols. Use recognized vessel subtype/parent symbols when available, or the reviewed generic neutral maritime symbol for unsupported/unknown types; prevent stale ground SIDCs from overriding AIS identity.
- Maintain general 48×48 tactical symbol rendering; defer/refresh Gateway tactical markers until the symbol catalog is ready. Keep non-tactical custom icons unchanged.
- Preserve no-drop-shadow default for all normal MIL-STD-2525C symbols, selected AIS red glow and selected ADS-B white glow, and all prior authentication, user state, Replay, Data Sync, ADS-B and native Shape behavior.
- i648 is retained as the validated rollback release.

## 1.4.0-i648

- Retain the general MIL-STD-2525C tactical-symbol renderer for AIS vessels carrying CoT/SIDC metadata; preserve the existing 48×48 symbol footprint.
- Remove inherited black drop shadows from **all normal MIL-STD-2525C map icons**, including AIS, CoT and Data Sync, at both the original stylesheet and deferred runtime styling layers. Also remove the built-in gray shadow layer from 972 of the 1,448 bundled tactical SVGs; retain 476 thin-outline filters that are not shadows.
- Preserve red AIS selection-only glow on the selected Leaflet marker (not on the tactical symbol image). Preserve the ADS-B white selected highlight and AIS PNG fallback when MIL metadata is absent.

## 1.4.0-i647

- AIS: default map markers have **no drop shadow**; the approved ship art remains in 64×64 PNG assets, rendered at 12×12. Only the selected AIS marker receives a **red** drop shadow.
- ADS-B: only aircraft selected in the details sidebar receive a **white** drop shadow. Highlights follow left/right pinned selection, disappear when deselected/closed, and reapply after map refresh.
- ADS-B Identification: **Owner / Operator** is always displayed, with **Not reported** when metadata is missing; accepts alternate owner/operator field names without inferring from callsign.
- Preserves i646 configuration and rollback baseline, Gateway connection and Replay separation, saved data, native Shape editing, and all prior features.

## 1.4.0-i646

- Replaces Gateway AIS civil/law point icons with the approved dark ship silhouette on a mint-green tile, stored as two 64×64 PNG files. AIS markers render at 12×12 pixels on the map; the AIS sidebar icon renders at 20×20.
- Preserves the incoming `Host` header including `:9444` in the Nginx proxy (`$http_host`), fixing the Gateway Configure "Same-origin request required" error without weakening origin checking.
- Retains the i645 Gateway Configure feature and the separate Replay certificate policy; installs over previous TAK Map releases without removing existing state/configuration.

## 1.4.0-i645

- Adds administrator-only **Configure** beside **Refresh** on the Gateway Data card, opening an in-app connection configuration modal.
- Configures Gateway host, port, HTTP/HTTPS, client-certificate mode (`none`/`auto`/`certificate`), HTTPS server trust, and existing certificate/key file paths.
- Adds backend settings read/save and Test Connection endpoints. Saved Gateway Data overrides survive restarts, use 0600 permissions, and do not modify Replay authentication or TAK Gateway security policy.
- Connects the Gateway snapshot proxy to the persisted endpoint, with fresh reload/ingestion on save. Adds installation and runtime validation for the modal asset.
- Preserves i644 as the rollback baseline; retains prior native Shape, Data Sync, Replay, and OTS behavior.

## 1.4.0-i644

- Enables Gateway Data connection modes `auto`/`none`/`certificate`; existing complete certificates stay enabled in auto mode. Incomplete enrollment fails closed.
- Separates Gateway Data TLS/authentication from Replay API TLS/authentication; allows no-client-cert HTTP on trusted LAN or server-verified HTTPS.
- Retains Replay client-certificate default, with opt-in certificate-free HTTPS only when Gateway policy permits; preserves Replay period, event, manifest, chunk/gzip, search, state, seek, and playback semantics.
- Keeps existing TAK Map user sessions, enrollment assistant, Data Sync/OTS credentials, and i643 native Shape Save behavior; adds focused independent connection-mode tests.


## 1.4.0-i643

- Replaces i642's unsupported Mission `/cot` POST/PUT Shape write with the native TAK workflow validated live against OpenTAKServer 1.7.13.
- Preserves every edited object as its native `u-d-*` Shape CoT with the same UID; Shape objects are not converted into EUD/self-position events or center-point surrogates.
- Sends the edited native Shape through the authenticated per-user certificate SSL CoT transport, then requires matching geometry from global `GET /Marti/api/cot/xml/<uid>/all`.
- Associates/refreshes the same Shape UID in each existing Mission with `PUT /Marti/api/missions/<mission>/contents` using `{"uids":[...]}`.
- Uses Mission `/cot` as authoritative GET/read-back only; POST/PUT Mission `/cot` is forbidden by the i643 release contract.
- Save succeeds only after global native geometry verification plus exact same-UID/same-type Mission geometry verification. Historical same-UID `public.cot` existence and aggregate Data Sync snapshots are not commit gates.
- Handles stale/rejected Mission tokens by retrying the live-validated Mission contents/read-back flow under the authenticated per-user certificate without a token.
- Preserves the existing compact Shape editor, center translation handle, explicit Save/Cancel semantics, dynamic dimensions, regional units, and TAK-compatible metadata/geometry behavior.

## 1.4.0-i642

- Fixes Mission-backed Shape Save by replacing generic CoT socket/old-UID database verification with an authenticated native Mission `/cot` update and direct same-UID Mission `/cot` read-back.
- Save exits Edit mode only after the affected Mission(s) return geometry matching the visible draft.
- Rectangle/polygon verification ignores cyclic starting vertex and winding direction while retaining coordinate tolerance.
- Removes asynchronous aggregate Data Sync snapshots from the Shape Save commit gate; Data Sync refreshes only after authoritative Mission confirmation.
- Preserves UID, Mission membership, native TAK CoT type, style/detail metadata, and the i641 edit/center-handle UI behavior.

## 1.4.0-i641

- Shape Edit now remains active until explicit Save or Cancel; empty-map clicks, offscreen movement, and object clicks no longer discard an active draft.
- Added a dedicated center translation handle for every supported Shape type. Dragging it moves the whole Shape without changing dimensions/orientation and updates Center live.
- Shape Save now keeps draft protection active, persists the exact visible draft, and verifies a same-UID Data Sync read-back before exiting for Mission-backed Shapes. Failed verification leaves the draft on screen.
- Notes is the final Shape detail/edit field. Save/Cancel remain 50/50 with slightly larger labels.

## 1.4.0-i640

- Fixes the i639 Shape resize state regression where editable handles could detach from the rendered stroke and the Shape could snap back during background/Data Sync refresh.
- Adds one authoritative in-memory edit draft shared by the rendered Shape, handles, dynamic distance labels, computed measurements, and Save payload.
- Re-applies the active draft to replacement map layers during periodic redraws instead of accepting persisted/original geometry while Edit mode is active.
- Makes Shape Save a dedicated action that persists the visible draft and exits only on success; failed saves remain non-destructive and visible. Cancel restores the exact pre-edit geometry snapshot.
- Removes Close Edit. Save and Cancel are equal half-width actions; Delete Shape remains a separate full-width action.
- Removes Category and Rotation from Shape details, retains Center instead of Lat/Lon, and uses normal font weight for the Shape name.
- Preserves i639 type-aware geometry handles, dynamic map-side dimensions, silver/gray TAK Map controls, canonical TAK CoT geometry, UID, Mission membership, source attribution, style/detail metadata, and backward compatibility.

## 1.4.0-i639

- Reworks Shape Edit into a compact in-place editor; Name, Center, and Notes replace their displayed values rather than creating a second form.
- Keeps Category read-only as `shape`, removes the duplicate header name, and relabels Lat/Lon as Center.
- Removes Width/Height from the Shape panel and adds zoom/space-aware regional-unit distance annotations between map geometry vectors.
- Adds draggable rectangle corner, polygon/freehand vertex, circle radius, and ellipse major/minor geometry handles with live map/measurement updates.
- Uses the TAK Map silver/gray theme for all Shape actions and tightens Edit/Delete spacing.
- Preserves canonical TAK CoT shape types, UID, Mission membership, style/detail metadata, and backward-compatible readers while updating Mission-backed geometry through TAK Server.


## 1.4.0-i638

- Fixes the confirmed Shape context flicker root cause: unchanged 2.5-second background scans no longer replace the selected sidebar DOM.
- Adds an explicit stable Shape Edit button and hides the unreliable native details/summary trigger.
- Corrects Mission-backed Shape source attribution to Data Sync / Mission instead of Local Data.
- Standardizes normal context-panel width at ~320 px, removes the reserved right scrollbar gutter, uses a full-width dark body, and aligns Edit/Delete to one centerline.
- Adds localized geometric measurements for rectangles, circles, ellipses, polygons, open shapes, and routes.
- Fixes installation of `tak-map-i636.js` and adds runtime deployment/route integrity gates.
- Preserves i636 canonical TAK shape compatibility and OTS Mission-delete v3 compatibility.

# TAK Maps 1.4.0-i637

- Fixes the Shape popup Edit control flicker/jump seen with rectangles and circles in i636.
- Makes the compact Edit summary styling authoritative from first render instead of periodically repairing inline element styles.
- Removes popup Edit mutations from the inherited v324 700 ms maintenance loop, Local Data rerender wrapper, and MutationObserver.
- Removes popup Edit mutations from the inherited v348 one-second maintenance loop and UI MutationObserver while preserving its unrelated draw-menu/save-dialog maintenance.
- Keeps the existing Edit Data fields and behavior unchanged; resize/rotation editing is intentionally deferred to the next shape-editing iteration.
- Preserves i636 TAK-compatible shape parsing/serialization, OTS Mission association/deletion semantics, ADS-B behavior, and OTS configuration.

# TAK Maps 1.4.0-i636

- Added type-aware canonical TAK shape parsing before generic route/link inference.
- Added Mission `/cot` rendering for `u-d-r`, `u-d-p`, `u-d-f`, `u-d-f-m`, `u-d-c-c`, `u-d-c-e`, vehicle-shape families, range circles, bullseyes, and compatible future link-based `u-d-*` shapes.
- Added backward-compatible readers for TAK Maps v345 `__shape/shape/polyline/vertex` payloads, embedded `takmap_shape` GeoJSON, and legacy duplicate closing vertices.
- Preserves raw server CoT and known/unknown detail metadata on read; no automatic destructive rewrite.
- New rectangles publish as `u-d-r` with exactly four unique corners.
- New polygons publish as `u-d-p` without a duplicate closing link.
- Circles and ellipses now publish native TAK ellipse geometry instead of sampled `u-d-f` polygons.
- Data Sync shape rendering now respects stroke/fill/weight/dash metadata and distinguishes open freeforms from closed areas.
- Fixed Data Sync deletion readback so `mission_name=NULL` MissionUID history does not count as an active Mission association.
- Enforced Mission-only scope for server-backed user map objects; unassociated OTS rows are treated as orphan server state rather than server-side Local Data.
- Added i636 regression coverage using the real `Rectangle 3` `u-d-r` payload from `1-40TH RECON`.

# TAK Maps 1.4.0-i635

- Corrects i634 Mission association handling by stamping authoritative Mission ownership at each Mission `/cot` acquisition boundary before canonicalization.
- Adds a non-destructive pre-existing-object backfill: objects found in authoritative Mission snapshots inherit those Mission memberships; legitimate older objects with no Mission membership are preserved as Local Data instead of being hidden for missing new metadata.
- Persists repaired association records per authenticated user and never restores a Mission membership that is not currently accessible to that user.
- Collapses duplicate UID rows only after memberships are known, retaining one canonical object with many-to-many Mission membership.
- Replaces the inherited single-Mission deletion assumption with per-Mission deletion records for canonical multi-Mission objects.
- Uses the inherited ATAK-style Mission token/delete/fence pipeline for each membership and requires bounded Mission `/cot` absence confirmation before a per-Mission delete is counted successful.
- Treats partial multi-Mission deletion as a failure and preserves/report remaining server state instead of claiming the entire canonical object was deleted.
- Preserves i634 per-user card persistence and AIS rendering changes, i633 ADS-B stability/cadence, i631 ADSB.lol fallback, and i630 OTS 1.7.13 automation.

## 1.4.0-i633

- Fixes refresh-synchronized ADS-B aircraft icon pulsing by preserving `scale(.75)` and `transform-origin:50% 50%` in every live marker heading writer, including the actually served deferred v320 owner and sidebar interpolation path.
- Replaces the interval-length ADS-B backend response cache with a 0.5-second concurrent-client coalescing window, so a configured 5-second update interval produces a fresh provider request on the next normal poll instead of an effective ~10-second cadence.
- Adds served/deferred-runtime regression coverage that rejects rotate-only ADS-B image transforms and verifies source/runtime sidebar parity.
- Preserves airplanes.live primary, ADSB.lol fallback, valid-empty semantics, 10-minute airplanes.live recovery, strict ADS-B OFF network silence, i632 lease behavior, and i630 OpenTAKServer 1.7.13 automation.

## 1.4.0-i632

- Fixes the i631 live ADS-B regression by synchronizing the deferred runtime manifest with the corrected ADS-B worker that TAK Map actually executes in the browser.
- Enabled ADS-B polls now carry a stable per-tab `client_id` plus `active=1`, allowing the backend to query the configured provider chain.
- ADS-B OFF and Replay stop send the matching network-silent `active=0` lease revocation immediately; no health check, recovery probe, tracked-aircraft lookup, primary request, or fallback request may start afterward.
- Adds release coverage that asserts the deferred manifest's ADS-B worker is byte-for-byte synchronized with `assets/tak-map-adsb-v491.js` and a browser test that observes `active=1` polling followed by `active=0` revocation.
- Preserves i631 airplanes.live primary / ADSB.lol fallback behavior, valid-empty semantics, and 10-minute airplanes.live recovery cadence, plus the validated i630 OpenTAKServer 1.7.13 automation.

## 1.4.0-i631

- Keeps airplanes.live as the primary ADS-B provider and adds transparent ADSB.lol fallback using the compatible v2 point/radius schema.
- Treats transport, TLS, timeout, non-2xx HTTP, invalid JSON, and unrecognized-response failures as provider failures; a valid empty aircraft array remains a successful response.
- After primary failure, uses the fallback provider without re-probing airplanes.live until 10 minutes have elapsed; a successful recovery probe automatically restores airplanes.live as primary.
- Moves provider selection entirely into the TAK Map backend; no provider/fallback status, controls, or labels are added to the user interface.
- Enforces a hard ADS-B OFF network gate: only the enabled ADS-B worker can authorize upstream ADS-B I/O, and internal health/status or legacy paths are cache-only. Each browser worker uses an invisible backend activity lease; OFF/Replay stop revokes it immediately so a primary request already finishing cannot start a fallback request afterward. The inherited background collector is disabled.
- Preserves i630 OpenTAKServer 1.7.13 authentication automation and i629 ADS-B emergency live/Replay behavior.

## 1.4.0-i630

- Automated Configure OTS for the user's OpenTAKServer 1.7.13 deployment at `10.10.10.2`.
- Added a privileged, bounded TAK Map-managed `/etc/hosts` block so IP-entered OTS servers with DNS-only SAN/CN certificates work automatically without disabling TLS verification; reconfiguration replaces stale TAK Map mappings and uninstall/unenroll removes only that managed block.
- Added automatic fallback to the documented OTS default truststore password only when needed; no enrollment credentials or truststore password are persisted.
- Added full pre-enable checks for OTS administrator authentication, `/api/me`, per-user `:8446` certificate enrollment, Marti client-certificate HTTPS, and SSL CoT `:8089`.
- Decoupled OTS login success from Data Sync certificate provisioning failure while keeping Data Sync disabled until its per-user certificate validates.
- Preserved i629 ADS-B emergency visualization and prior Replay/Data Sync behavior.

## 1.4.0-i628

- Adds Replay maintenance-aware Jump handling for TAK Gateway i196.
- Keeps the requested Jump timestamp and previous valid map state when Gateway reports that the state checkpoint index is still preparing.
- Refreshes Recorded Periods once after `period_not_found` and safely remaps the selected logical recording through stable aliases or a unique strict overlap match before retrying.
- Preserves i627 `/state` proxy forwarding, i626 checkpoint long-jump transport locking, and protected i602 Data Sync behavior.

## 1.4.0-i627

- Fixes TAK Map Replay `/state` proxy forwarding by adding `state` to the real backend allowlist.
- Corrects the `Unsupported Replay API endpoint.` error seen when i626 Jump/Search attempted to use TAK Gateway i195 state-at-time checkpoints.
- Adds a real backend HTTP-handler regression that proves `/api/tak-map/replay/state` is forwarded to Gateway rather than rejected locally.
- Preserves all i626 checkpoint/state-at-time, transport-lock, atomic-commit, and protected i602 Data Sync behavior.

## 1.4.0-i626

- Adds checkpoint-backed Replay state-at-time seeking through TAK Gateway i195.
- Replaces multi-day forward reconstruction in thousands of 5-minute browser windows with nearest-checkpoint plus bounded delta reconstruction.
- Locks Replay transport/timeline/Search/Jump navigation while an absolute seek is pending and hard-blocks Play from the stale pre-seek clock.
- Atomically commits the complete target state and preserves the previous valid state on errors or superseded seeks.
- Shows both start and end dates for multi-day Recorded Period labels.
- Preserves i625 aircraft-state atomicity, i624 date/time controls, i623 stable period identity, and protected i602 Data Sync behavior.

## 1.4.0-i625

- Unified Replay Search, date/time Jump, ±1 minute, and out-of-buffer timeline seeks through one serialized absolute-seek/state-reconstruction path.
- Stages target Replay data before committing map state so incomplete, failed, or superseded seeks do not blank aircraft.
- Separates the selected recording end, contiguous buffer boundary, and latest loaded event timestamp.
- Restores Play after Jump and allows playback to advance through sparse intervals until the actual period end.
- Preserves TAK Gateway i194 stable period/search behavior and the protected i602 Data Sync backend.

## 1.4.0-i624

- Adds Replay `Jump to date / time` controls directly below Recorded Period with native date input, seconds-precision time input, and Go.
- Adds `-1 min` and `+1 min` precision navigation while respecting the selected period boundaries.
- Keeps the fields synchronized with timeline scrubbing and Replay Search/occurrence jumps.
- Reconstructs the contiguous Replay state through out-of-buffer targets and adds a short look-ahead for normal interpolation before seeking.
- Keeps playback paused after a jump and leaves Live Map unchanged.
- Adds final-served-HTML and headless-browser release gates for control placement, period bounds, seconds precision, timeline synchronization, and minute stepping.

## 1.4.0-i623

- Uses TAK Gateway i194 stable period identities for whole-recording search.
- Keeps legacy start/end-derived Replay period IDs compatible with older Gateway responses.
- Refreshes a selected recording's end boundary from search responses so matches in newly grown recording data can be targeted correctly.
- Preserves the i622 final-served Replay Search delivery and protected i602 Data Sync backend boundaries.

## 1.4.0-i622

- Fixes the i621 finalization defect that omitted the Replay/Search integration from TAK Map's final served HTML even though the source implementation was present.
- Reinstalls the authoritative Replay runtime after every historical HTML finalizer and updates its release identity to 1.4.0 / i622.
- Adds final-render and headless-browser release gates that verify Search Recording is actually delivered, positioned below Recorded Period, and enabled after a Replay period is selected.
- Added whole-recording Replay Search backed by the TAK Gateway persistent Replay identity index.
- Search scope is limited to ADS-B flight/callsign, ICAO/hex, registration, owner/operator, aircraft type/model, EUD callsign/UID, vessel name, and AIS callsign.
- Search results can seek to indexed appearances outside the current browser buffer, automatically load the matching time window, enable the matching source, center/highlight the object, and navigate previous/next appearances without enabling Track/Follow.

# Changelog

## 1.4.0-i629

- Fixes ADS-B emergency visualization so emergency aircraft render red in both live viewing and Replay.
- Preserves Gateway emergency metadata/red CoT styling through Replay normalization and forces icon refresh when emergency state changes.
- Adds dedicated red fixed-wing/helicopter assets for civilian, government, and military ADS-B classes.
- Leaves Replay stale semantics and i628 Jump/checkpoint behavior unchanged.

## 1.4.0-i620

- Removed the stale deferred sidebar owner that forced the iteration back to `i602`; the server-rendered i620 identity is now authoritative before first paint.

- Corrects the left-sidebar public version to `1.4.0` and advances the displayed iteration to `i620`.
- Installs an early mutation guard that prevents delayed legacy scripts from visibly replacing the authoritative sidebar identity.
- Gives NIFC Fire Perimeter context panels a source-specific content-aware width, expanding only when their visible content requires it.
- Leaves all other contextual-panel widths and validated i618 behavior unchanged.
- Updates cache keys, package metadata, validation, and installation documentation.

## 1.4.0-i618

- Promotes TAK Map to public version 1.4.0 with iteration i618.
- Adds one shared content-aware width policy for ADS-B, Local Data, Data Sync, Gateway Data, dynamic Source Extension, and other shared context panels.
- Keeps compact panels narrow and expands long-content panels only as needed within responsive limits.
- Reserves the themed scrollbar gutter so content and headers do not shift when vertical scrolling becomes active.
- Prevents horizontal scrolling and wraps long source values cleanly.
- Preserves ADS-B left/right docking and prevents dual-panel overlap by sizing each panel independently within the map viewport.
- Keeps context panels above ordinary map controls and below true top-level modals.
- Updates product/version markers, cache keys, installation instructions, release notes, troubleshooting guidance, and context-panel documentation.

## 1.3.0-i617

- Mounts read-only Gateway Data context panels in a top-level overlay above the main map toolbar while preserving top-level modal priority.
- Adds a TAK Map-themed vertical scrollbar, fixed context header, responsive wider panel, and fully reachable long content.
- NWS affected areas now show three entries initially, use `Show all N areas`, render every parsed area when expanded, and change to `Show fewer`.
- USGS earthquake Review is labeled Status; Alert and Source program rows are removed.
- USGS title/location distances and Depth use regional units consistently.

## 1.3.0-i616

- Raises the read-only Gateway Data context panel above the main map toolbar while keeping top-level modals above it.
- Removes duplicate object titles from Gateway Data context content.
- Restricts NWS context content to source-provided alert fields, formats semicolon-delimited affected areas as a concise vertical list, and hides generated merge/geometry/internal-ID diagnostics.
- Replaces generated NIFC and USGS Details paragraphs with concise structured source fields.
- Expands NIFC `WF` and prescribed-fire codes to `Wildfire` and `Prescribed Fire`.
- Removes USGS distance-from-center and event-status fields.
- Preserves the i615 read-only/no-flicker context mode and all validated i614/i613/i612/i611/i610/i602 behavior.

## 1.3.0-i615

- Adds a dedicated read-only Gateway Data context mode rather than reusing Local Data shape editing UI.
- Removes Gateway Data edit/delete controls, style swatches, ownership warnings, Local Data labels, and animated edit-state accents.
- Uses friendly Gateway Data source names in the context header and updates selected details in place only when values change.
- Preserves all validated i614 geometry/context behavior and prior Source Extension, ADS-B, and Data Sync functionality.

## 1.3.0-i614

- Routes every Gateway Data point, line, polygon, and multi-geometry object into the existing right-side contextual details panel instead of a floating Leaflet popup.
- Adds subtle, non-animated Gateway Data selection emphasis and clears it cleanly with context/source/Replay lifecycle changes.
- Curates dynamic Source Extension details to important operator-facing values while hiding internal and low-value metadata.
- Preserves validated i613 Source Extension drawing/EUD suppression, i612 deferred runtime, i611 dynamic local-ingest controls, i610 ADS-B behavior, and protected i602 Data Sync behavior.

## 1.3.0-i613

- Suppresses live representative-point EUD markers for Source Extension `u-d-f` drawing events while retaining their authoritative Gateway Data line/polygon geometry.
- Excludes Source Extension data objects from the EUD device list without suppressing legitimate Point Source Extension records from the live CoT path.
- Preserves the validated i612 deferred Gateway Data runtime, dynamic source toggles, MultiPolygon rendering, i610 ADS-B behavior, and protected i602 Data Sync implementation.

# TAK Map changelog

## 1.3.0-i612

- Replaces the stale i523 Gateway Data implementation embedded in the deferred startup manifest with the exact current i612 runtime.
- Restores dynamic Source Extension discovery and MultiPolygon rendering through normal TAK Map startup.
- Changes the deferred manifest cache-busting version to i612.
- Adds full-startup manifest/browser regression coverage and an exact embedded-versus-external runtime parity check.
- Preserves i611 local Source Extension ingest behavior, i610 ADS-B behavior, and the protected i602 Data Sync runtime.


## 1.3.0-i611

- Adds dynamic TAK Gateway Source Extension discovery to the existing Gateway Data card.
- Adds per-extension TAK Map-local ingest toggles that default off for newly discovered sources.
- Clears disabled-source objects and skips future snapshots locally without changing the Source Extension state in TAK Gateway.
- Persists local ingest preferences by stable source key and restores them when a known source returns.
- Adds dynamic source labels, counts, geometry-aware icons, sorting, popup names, master visibility, Replay suppression, and add/remove reconciliation.
- Adds MultiLineString and MultiPolygon rendering support for dynamic Gateway Data sources.
- Preserves i610 ADS-B behavior and the protected i602 Data Sync runtime.


## 1.3.0-i610

- Dock the secondary ADS-B context panel in the bottom-right of the map viewport with the same 12-pixel edge inset as the primary bottom-left panel.
- Keep both ADS-B panels above the map toolbar and preserve all i609 ADS-B behavior.
- Preserve the validated i602 Data Sync backend and protected runtime files unchanged.

## 1.3.0-i608

- Opens live ADS-B aircraft details in a dedicated left-side panel above the map toolbar.
- Adds aircraft-panel pinning; a pinned aircraft remains live on the left while other objects use the normal right-side context panel and a second aircraft can open on the right.
- Keeps ADS-B interpolation state, tracked history, follow state, and pinned-panel data advancing through a background worker when the tab is inactive, then renders the current position on return.
- Adds Airplanes.live emitter category A7 as a high-confidence rotorcraft signal while preserving existing aircraft-type evidence.
- Uses the same resolved aircraft type for the sidebar Type chip and fixed-wing/rotorcraft map icon, including live reclassification.
- Preserves i607 full-history Save Trail behavior and the validated i602 Data Sync implementation without modification.

## 1.3.0-i607

- Added the validated ADS-B-specific right-sidebar renderer from the i606 live test patch.
- Raised the ADS-B contextual sidebar above the right-side toolbar.
- Preserved continuous full-history trail recording across Save Trail actions.
- Prevented the transient ADS-B trail from duplicating the already-saved Local Data route by rendering only the unsaved continuation after save.
- Preserved the i602 Data Sync implementation unchanged.
