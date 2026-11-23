# TAK Map v1.4.0-i673 — Route Tools, NDM Network, Elevation Viewshed and Basemap Blending

## Changes

1. **Route Details**: Edit and Delete controls are compact (34 px) with 12 px horizontal and lower padding.
2. **Route Distance**: **Reverse** reorders controls/legs and revalidates road-routed legs in bounded parallel requests (one-way geometry may not be traversable backward). **Back to Start** adds the origin as the last waypoint and resolves only the return leg through the installed NDM/Valhalla router. Both operations are atomic; failures leave the existing route unchanged. Undo restores the prior state.
3. **MVUM**: text-only first Route toolbar button toggles the **active NDM Valhalla 3.6.3 navigation graph** as an overlay in the Leaflet 2D map, not Forest Service MVUM legal road designations. Requests spatial tiles for the current viewport plus 50% per side, caches up to 240 tile responses, uses 2 concurrent backend requests and Leaflet retained GridLayer canvas geometry, checks coverage only after the map stops moving, with a 300 ms debounce. Map movement must never recalculate route legs or rebuild all navigation geometry. Available detail may vary with graph, zoom and Valhalla's tile-service configuration. Registered but **inactive** graph datasets are not automatically merged; activating or switching graphs is never performed by MVUM.
4. **NDM Viewshed**: Auto priority is registered NDM elevation first, then Esri, then USGS. Explicit NDM selection is available. Samples registered `terrain.sqlite` in ZIP via read-only TAK Map-owned cache, bounded input batches and a maximum of 2 active browser requests. Requires **complete sample coverage** before using NDM; otherwise the complete analysis falls back to a single existing provider, with no blind blending of datums or nodata substituted as zero. Large registered terrain archives may require initial background cache preparation, so first analysis can use a fallback until NDM is ready. No original NDM files are modified.
5. **Multibasemap blending**: users can expand/collapse the BASEMAP LAYERS list, check multiple basemaps, adjust per-layer opacity 0–100%, and reorder sources via drag/drop or up/down buttons. The lowest selected layer stays fully opaque by default (user may override); selected order, opacity and collapsed state are saved in browser localStorage. Leaflet tile layers are retained between pans and zooms. The 3D terrain Cesium base imagery remains single-source in this iteration.

## Validated locally

- 116 regression tests (including 8 i673 tests) passed.
- NDM synthetic 2x2 native terrain.sqlite interpolation, invalid coverage and sampling tests passed.
- Valhalla Mapbox Vector Tile edge parser synthetic geometry test passed.
- Chromium basemap selection, two-layer opacity, collapse and retained-layer smoke test passed.
- JavaScript syntax, Python import/syntax, Bash syntax and package integrity validated.
- 2D frontend feature wiring and authenticated runtime JS delivery tests passed.

## Not validated against live equipment

- NDM / Valhalla server graph tile output, authenticated network transport, terrain source permission and geographic accuracy in an actual terrain archive, and route editing against installed data.
- The Valhalla `/tile` interface is BETA, and graph/service configuration can limit road-class coverage. MVUM reports lack of ready router; data availability on a specific live installation is not guaranteed.
- GPS datums across registered NDM terrain sets are not declared; no mixed-source elevations are combined in an analysis.
- Full deployed-browser NDM route/view and real saved-geometry regression test remains to be performed by the user.

## Safe upgrade

- Source release is `tak-map-v1.4.0-i673.zip`, fresh flat-root extraction into `~/Downloads/tak/tak-map-v1.4.0-i673`, then `sudo ./install.sh`.
- Retains existing user data, NDM registrations and source folders. Keep i672 source and ZIP for rollback.
