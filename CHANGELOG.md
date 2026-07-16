# TAK Map v1.3.0 (i442)

## i442

- Removes the version badge from the top-left TAK MAP title.
- Keeps the release and iteration only in the sidebar footer as `v1.3.0` and `i442`.
- Adds a runtime guard so older scripts cannot overwrite the footer with stale `1.2.0` / `v409` values.
- Replaces Offline Maps browser-native zoom steppers with TAK Map-themed decrement and increment controls.
- Applies the approved Option A Tactical Rail design to the USGS Shaded Relief opacity slider.
- Preserves the v441 Replay popup lifecycle, Replay banner layout, buffering text, and Replay timeout fixes.

## v441

- Public release of TAK Map Replay Mode as version `v1.3.0`.
- Fixes Replay aircraft/object popups so closing and reopening works repeatedly during playback and while paused.
- Adds deterministic Replay popup state cleanup, map-level close handling, close-button fallback cleanup, stale-popup removal, and one active Replay popup at a time.
- Prevents legacy global popup-hover managers from attaching competing handlers to Replay markers.
- Moves the Replay Mode banner immediately to the right of the Live status bar, with responsive below-bar fallback when horizontal space is limited.
- Adds `v1.3.0` beside the TAK Map title and updates the sidebar footer iteration to `v441`.
- Preserves the 120-second Replay API timeout default, `Buffering playback...` text, period-selection behavior, progressive buffering, interpolation, and API-cap subdivision.
- Cleans public release artifacts and excludes runtime secrets, logs, caches, backup files, and environment-specific data.

# TAK Map Changelog


## v440

- Hotfixes Replay Mode object and aircraft popups after v439 removed the only effective marker click path.
- Keeps raw DOM `pointerdown`/`click` handlers removed, but adds exactly one explicit Leaflet marker `click` handler because TAK Map's global popup stabilizer intentionally removes Leaflet's default `bindPopup()` click handler.
- Stops marker clicks from bubbling to the map, opens the bound popup deterministically, and preserves repeated close/reopen behavior through marker movement and icon replacement.
- Extends Replay popup diagnostics with click, open-attempt, and handler-bind counters.

## v439

- Fixed Replay aircraft/object popups so they can be closed and reopened repeatedly while playback is running or paused.
- Removed competing raw DOM `pointerdown` and `click` popup handlers; Replay markers now use one stable Leaflet `bindPopup` interaction path.
- Preserved popup bindings across position and icon updates and added `getTakMapReplayPopupDiagnosticsV439()` for focused verification.
- Restored the approved Replay loading text to `Buffering playback...` and removed `Loading ahead in background…` from the active Replay UI.
- Raised the Replay API proxy default timeout from 20 seconds to 120 seconds, with a 300-second safety cap.
- Installer upgrades now migrate only the legacy `TAK_MAP_REPLAY_TIMEOUT=20` default to 120 seconds while preserving other operator-selected values.
- Replay certificate enrollment now writes the 120-second timeout so enrollment cannot reintroduce the old setting.

## v438

- Replay period field now displays **Select Period** immediately while period metadata loads.
- The temporary **Loading periods…** state appears only inside the opened period menu.
- Recorded Period menu receives the highest Replay dropdown stacking level.
- Playback Speed menu receives the second-highest stacking level and opens above transport controls.
- Preserves v435 Replay activation fix, custom graphite dropdowns, interpolation, API-cap splitting, and all existing Replay behavior.

## v433

- Combines Replay playback and buffer progress into one chamfered industrial rail: purple indicates loaded buffer and green indicates playback position.
- Changes the no-period buffer message to `Pending period selection.`
- Styles Replay period and speed dropdowns using the compact stacked B2 chamfered design.
- Centers and slightly enlarges Replay Back, Play/Pause, and Stop controls using the segmented C2 bright-alloy monochrome design.
- Preserves the v432 Replay 1,000-record API-cap subdivision fix, `recorded_at` scheduling, actual-event timeline bounds, and manual period selection.

# Changelog

## v435

- Fixed Replay Mode activation regression introduced in v434.
- Moved the custom Replay dropdown helper functions into the Replay integration scope so UI creation completes and `bindUi()` attaches the mode-toggle handlers.
- Preserves the v434 graphite custom dropdown menus and 0.8× transport controls.

## v434

- Reduced the entire centered Replay transport control assembly to 0.8× its v433 size, including the rail, buttons, padding, radii, separators, and icons.
- Replaced the browser-native opened Replay select menus with accessible custom graphite dropdown menus.
- Added dark graphite texture, readable light option text, and a purple active-selection accent while preserving the B2 Compact Stacked closed-field styling.
- Preserved all v433 Replay buffering, interpolation, manual period selection, and API-cap fixes.

## v432

- Fixed coordinated Replay aircraft freezes caused by silent Replay API truncation. TAK Map now requests 1,000 records per window and recursively subdivides capped dense windows until the complete interval is retrieved.
- Replay scheduling now uses TAK Gateway `recorded_at` as the authoritative timestamp, with embedded CoT `time` retained only as a fallback.
- Replay timeline start and end are trimmed to actual parsed event timestamps instead of storage chunk boundaries.
- Added a default **Select Period** item to the Replay period dropdown. Entering Replay Mode no longer automatically loads the most recent period.
- Preserves the normal v429 Replay render cadence; the unsuccessful v430 render-throttling experiment is not included.

## v429

- Restores the established TAK Map backend port `8092` used by v427 and earlier builds.
- Repairs stale TAK Map nginx upstreams that still proxy to unused port `8091`, preventing 502 Bad Gateway errors.
- Splits Replay aircraft tracks at CoT stale boundaries.
- Stops interpolation across long absences, range exits, landings, and later reappearances.
- Removes stale aircraft after their final valid point and recreates them at the first point of a later segment.
- Prevents tracked trails from drawing a line across separate aircraft segments.
- Preserves v427 progressive buffered loading and continuous playback timing.

## v424

- Uses a monotonic playback anchor so dropped frames cannot alter Replay speed.
- Keeps aircraft symbols at 0.75x while preserving 1x callsign label sizing.
- Updates aircraft heading once per replay second.
- Displays actual first and last recorded event times instead of chunk boundaries.
- Retains frame-based position interpolation and reduced per-frame icon rebuilding.

## v424

- Uses `requestAnimationFrame` for continuous Replay marker interpolation, with a controlled timer fallback.
- Smoothly interpolates aircraft heading/course between recorded positions while preserving exact recorded headings at event timestamps.
- Reuses Live Mode aircraft icon selection and military/government/civil classification for Replay aircraft.
- Renders Replay aircraft at approximately 0.75× the Live Mode icon size.
- Limits continuous frame work to position and heading changes; popup and control refreshes are throttled.
- Samples Replay trails independently from render frames to avoid excessive trail points.
- Resets playback timing when the browser tab visibility changes to prevent large resume jumps.

## v421

- Fixed Replay marker popup opening with an explicit Leaflet marker click handler.
- Replay popup content is refreshed whenever the popup opens.
- Replay marker icons are only replaced when their visible label changes, preserving stable interaction state during movement.
- Replay popups can be closed and reopened repeatedly.

## v420

- Moved Replay status, loading, connection, buffering, and error messages to a prominent status area directly beneath the Replay Mode heading.
- Fixed synchronized Replay visibility gaps by interpolating to the next recorded position before applying stale removal.
- CoT stale time now removes an untracked object only after its final known recorded location.
- Tracked objects still freeze at their final position with their trail preserved after stale time.

## v419

- Fixed Replay object popup lifecycle so popups reopen reliably after closing.
- Reworked Replay Track, Follow, and Clear Trail controls to use stable delegated event handling.
- Replay Track and Follow status lights now reflect persistent per-object state on every popup open.
- Suppressed `GeoChat.*` records from Replay map-object rendering.
- EUD Replay markers now prefer recorded CoT contact callsigns and fall back to UID only when no callsign is available.
- Limited Replay popup details to Callsign, Owner/operator, Aircraft type, Aircraft model, Coordinates, Altitude, Speed, Course, and Source.
- Updated Replay playback speeds to Real-time, 2x, 5x, 10x, 15x, 30x, and 50x.

## v418

- Replay objects now interpolate continuously between every consecutive recorded position.
- Untracked objects are removed exactly when their recorded CoT stale time is reached.
- Tracked stale objects remain at their last position with their trail preserved.
- Replay object markers are clickable and restore styled information popups with Track, Follow, and Clear Trail controls.

## v417

- Fixed Replay Mode basemap initialization by loading TAK Map basemap configuration before creating the replay tile layer.
- Fixed Replay basemap switching so the live Basemap selector replaces the active Replay tile layer.
- Added styled Replay tile-loading error feedback.
- Replaced the single Source dropdown with a multi-select checkbox list, Select All/Clear All controls, and per-source event counts.
- Replay period labels now use the browser regional date format with a compact time range.
- Internal package iteration advanced to `v417`.

## v416

- Added the TAK Map Replay Enrollment receiver at `/usr/local/sbin/tak-map-replay-enroll`.
- Supports automated SSH enrollment from TAK Gateway, secure certificate installation, environment updates, Replay API validation, service restart, and rollback on failure.
- Updated the Map Mode pill and lamp to green in Live Map and purple in Replay Mode.
- Preserved Replay tracking, following, playback, and read-only behavior from v415.

## v416

- Added TAK Gateway Replay API v1 server-side mutual-TLS proxy endpoints.
- Added the industrial Live Map / Replay Mode switch with confirmation dialogs.
- Replay Mode now replaces the live Leaflet map with a dedicated replay-only map and restores Live Map on exit.
- Added recorded-period loading, timeline seek, play/pause/stop, playback speeds, source filtering, and historical-data warnings.
- Added per-object Track, Follow, and Clear Trail popup controls with fixed labels and red/green status lamps.
- Supports multiple tracked objects, one followed object, bounded trails, and no trails by default.
- Added Replay certificate/environment configuration and `docs/REPLAY-MODE.md`.
- Replay data remains read-only and is never written to OpenTAKServer, Data Sync, or live CoT.

# Changelog

## v413

- Release label updated to `v1.2.0` for GitHub release packaging.
- Internal package iteration advanced to `v413`.
- No functional, UI, or behavior changes from v412.
- Added browser console diagnostic `getTakMapReleaseDiagnosticsV413()`.

## v412

- Satellite Tracking UI font sizing: matched action buttons, Enable Satellite Tracking, and Display Filter checkbox labels to the data-source dropdown text size.
- Moved the Satellite Tracking panel to directly below ADS-B in the left-side menu.
- Satellite Tracking now defaults collapsed on first load and remembers the user's last collapsed/expanded state across refreshes.
- Removed descriptive helper text from satellite category rows while keeping category counts right-aligned.
- Slightly reduced Satellite Tracking toggle/filter label text size.
- Added a horizontal separator below the satellite cache summary before Display Filters.
- Added browser console diagnostic `getTakMapSatelliteUiDiagnosticsV411()`.
- Preserved v1.1.0 release label; only the package iteration was advanced.
## v409
- Fixed ADS-B/Leaflet popup sizing so the content spans the popup width and the Track button is not cut off.
- Added browser console diagnostic `getTakMapAdsbPopupDiagnosticsV407()`.
- Preserved v1.1.0 release label; only the package iteration was advanced.

## v406
- Fixed Offline Maps manual area selection so dragging draws the download rectangle instead of panning the map.
- While the offline-area selector is active, map pan/zoom/keyboard/touch interactions are temporarily disabled and restored after selection.
- Added browser console diagnostic `getTakMapOfflineDrawDiagnosticsV406()`.

# v405

- Keeps release label `v1.1.0`; iteration marker is `v405`.
- Terrain Mode Local elevation coverage is now stroke-only visually: old orange v320 mesh primitives and newer gray v402 local DEM surface primitives are neutralized/hidden.
- Keeps local elevation sampling/decoded raster state active while preventing visual fill/mesh overlays; the boundary stroke remains the only coverage indicator.
- Adds console diagnostics: `getTakMapTerrainVisualDiagnosticsV405()` and manual cleanup helper `hideTakMapLocalDemVisualFillV405()`.
- Builds from v404 and preserves Live TAK menu removal, CoT Markers visibility fix, MIL-STD-2525 selector sizing, and Terrain Mode refresh fixes.

# v404

- Keeps release label `v1.1.0`; iteration marker is `v404`.
- Removes the visible `Live TAK` sidebar menu/panel from TAK Map.
- Keeps a hidden `liveRows` placeholder so existing live CoT layer state and refresh code can continue to run without UI breakage.
- Builds from v403 and preserves the CoT Markers visibility fix, MIL-STD-2525 selector sizing, and Terrain Mode/local DEM fixes.

# v403

- Keeps release label `v1.1.0`; iteration marker is `v403`.
- Renames the Live TAK control to `CoT Markers`.
- Fixes the CoT Markers toggle so turning it off hides all live CoT objects rendered through the TAK marker layer, including EUD/server GPS/webform/non-TAK CoT points, while preserving the separate ADS-B and Data Sync layers.
- Builds from stable v402 and preserves the Terrain Mode/local DEM and MIL-STD-2525 selector fixes.

# v402

- Keeps release label `v1.1.0`; iteration marker is `v402`.
- Enlarges the MIL-STD-2525C icon selector thumbnails slightly for easier selection.
- Keeps actual map marker/icon sizing unchanged.
- Builds from v401, preserving Terrain Mode local elevation fixes and stable stroke-only local elevation boundary behavior.

## v427

- Replaces fixed 30-minute Replay API windows with adaptive 5-minute fetch ranges.
- Recursively splits any saturated API range so event limits cannot silently truncate a playback window.
- Deduplicates overlapping range results and merges the selected recording into one globally sorted timeline before playback.
- Uses the CoT event timestamp as the authoritative Replay timeline time, falling back to `recorded_at` only when needed.
- Keeps a single monotonic playback clock and object state across all storage chunk boundaries.

