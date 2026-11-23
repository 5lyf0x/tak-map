# TAK Map v1.4.0-i683 — Floating elevation profile and MVUM reliability

Baseline: exact TAK Map v1.4.0-i682 source ZIP. This release preserves the existing install paths, Local Data catalog and configuration.

## Elevation profile

- Default **Compact** mode is a draggable 580px floating panel, with an 82px graph, slim grade-color legend above the chart, header Route Distance at the right and Expand / X controls.
- **Extended** mode retains the full set of metrics (distance, ascent, descent, elevation limits, maximum slope and ≥35° distance in feet), five elevation levels, a larger chart, a full-route / steep-detail selector and terrain source/quality context.
- All elevation and slope calculations operate on real NDM terrain samples along the complete resolved polyline; no simulated heights. Degrees are slope *angles*, not percentages (35° ≈ 70% grade). Very short steep sections may not be detectable with coarse elevation tiles.
- Contiguous sampled intervals with |slope| ≥35° are numbered. Hover or focus a number to see run length in **feet**, slope angle, uphill/downhill direction, elevation change and route-mile position. Click to open Extended view focused on that run. Small samples are grouped using the existing terrain-quality window to avoid misleading single-sample spikes.
- Drag from the header title/Route Distance region (grab/grabbing); both pointer and keyboard dragging clamp to screen bounds and persist browser position. Action buttons are not part of the drag handle.
- Visibility strictly follows Route Creation, saved-route selection or edit. Closing Route Creation, deselecting a route or selecting a non-route object hides the panel. The X button hides the entire panel; it does not simply collapse the chart. Explicit Profile activation can reopen it.

## MVUM overlay

- Make MVUM appear above Undo regardless of Leaflet initialization order and rebuild when the Route Creation toolbar is replaced, without duplicates.
- Render lower-detail fallback edges as vector geometry instead of stretched raster canvases, keeping line weight stable at higher zoom and supporting HiDPI rendering.
- Do not trigger a global grid redraw when a single tile request fails, preventing the observed zoom flashing.

## Upgrade and validation

- Preserves i682 route/point/shape persistence, selection identities, import limits and Basemap Blend dropdown corrections.
- No changes to `/var/lib/tak-map/tak_map_imports/`, no schema migration, and no data cleanup. Back up this folder before upgrading.
- Offline browser and Python/Node regression checks cover route-only visibility, drag interactions, hotfix rendering, saved-route data and existing upgrades. Source ZIP integrity and bytewise fresh-extraction verification are recorded in `VALIDATION_I683.md`.
- **Not tested on the user's live 10.10.10.101 server.** Actual NDM route geometry quality and package upgrade behavior need on-host validation.
