# TAK Map v1.4.0-i681 — Route elevation and 2D/3D continuity

Based on i680, retaining its verified recovery of existing Local Data and i679 long-route persistence.

## Implemented
1. MVUM button is reinserted above Undo when the route toolbar DOM is replaced. Only one button/status pair and one map move listener are maintained; red MVUM overlay behavior from i678 is preserved.
2. 2D → 3D transfers the map focal point and its ground scale to a Cesium `lookAt` target (rather than treating the camera's oblique position as the map center). 3D → 2D picks the terrain/ellipsoid position below the viewport center and converts 3D ground meters/pixel to Leaflet zoom. Terrain-relative altitude uses the current sampled terrain height (bounded terrain query with fallback) and camera range; 2D has no physical altitude field. Actual camera parity needs an on-server terrain test.
3. Live route elevation panel samples the full snapped/manual polyline, not just route waypoints. It starts after two points, refreshes during edits and solved-leg changes, and includes a separate Profile button for saved routes in Local Data. Distance-spaced NDM terrain API calls are asynchronous, cancellable and batched (512 points). Adapt to the declared DEM resolution, cap at 40,000 samples on very long routes, show data gaps instead of synthetic elevations, and provide a map-linked hover indicator with distance, elevation and grade.
4. The profile is a floating collapsible panel centered on the *map viewport* 20px above its lower edge. It responds to Leaflet/Cesium viewport resize and sidebar state. Route files and existing saved data are never modified by profile computation.

## Notes / limits
- A registered NDM terrain dataset covering the route is required for an actual profile; no elevation means a clear unavailable status, not a fabricated flat line. Preparing NDM terrain cache may delay the initial profile. Overlapping datasets have unverified vertical datums and are not mixed with external sources.
- Ascent/descent and grade reflect samples at the available DEM resolution, not a survey-grade road-surface profile. AGL is not stored in Leaflet; scale equivalence is a ground-footprint approximation.
- i680 Local Data fallback remains in place. Custom map source HTTP 502 failures from the user's console are unrelated and not corrected in this release.
- No live access to the user's server is available for end-to-end validation. Preserve the existing `/root/tak-map-recovery-i679/` backup before installing.
