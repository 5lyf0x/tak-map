# TAK Map v1.4.0-i658 — Reliable Roads routing UI and persistence

- Unify inline and browser-deferred Save Route dialog scripts to prevent the legacy handler from saving only clicked waypoints. The real route-save path uploads every snapped polyline coordinate and compares coordinates in the import response before clearing the editor.
- Restore a visible upper-right Roads/Manual mode selector (Roads remains the default), with route-tool visibility checks.
- Preview the next connected road segment between the last waypoint and the cursor, using the routing engine; show progress while routing and retain earlier completed segments. Manual mode previews a straight line.
- Expand the Route Distance panel upward, anchored at the bottom. Remove the short internal leg-list scrollbar; limit scrolling only to viewport height.
- Show unobtrusive per-leg mileage labels at distance-weighted midpoints along completed road geometry. Persist their positions in route GeoJSON metadata for import/reload display.
- Preserve the 20-screen-pixel snapping threshold, other legacy map features, NDM integration, existing user data and configuration. i657 stays the rollback source; no bundled routing graph or binary.
- Validation tests use Chromium with both production dialog script copies and the actual editor, plus ZIP fresh-extraction comparison. Live TAK Map and actual NDM/Valhalla route saving remain to be checked by operator.

