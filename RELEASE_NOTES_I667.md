# TAK Map v1.4.0-i667 — Release notes

## Terrain Mode

- Saved/imported GPX/GeoJSON and Data Sync routes and supported polygons render through a separate managed Cesium overlay collection. Paths intersecting the visible view are not discarded solely because their centroid is offscreen.
- Streamed terrain uses ground-clamped geometry. Local DEM uses sampled elevation plus modest clearance above the custom terrain mesh where coverage exists, and falls back to ground clamping where elevation samples are unavailable. Rendered vertices are bounded by terrain quality budgets.
- Saved route name and total distance appear only when endpoints are visible at zoom z11+ and within the configured 3D camera distance, with a straight plain leader line. Editing stays in the normal 2D route editor.
- For supported polygon shape geometry, stroke and fill render separately, respecting stored colors, thickness, dashed style, fill enabled, and opacity. Complex multi-ring holes and 3D extrusions remain outside this release.

## Sidebar and symbols

- Adds Edit Route above Delete Route for owned local saved routes with verified revision identity. Existing route edit/save/cancel logic is reused. Remote/Data Sync routes remain read-only unless separately authorized.
- Uses the same authoritative Icon Registry selected asset for 2D and 3D custom markers, independently of CoT affiliation.
- Includes i666 field corrections to registry grid width, 2D custom-icon priority, and saved-route offscreen label suppression.

## Compatibility and test scope

- Preserves VEIL Phase 2, Token Mesh, Gateway Data, NWS alerts and application data without migration.
- Offline tests verify renderer logic and browser DOM; physical local DEMs, live VEIL nodes and heterogeneous ATAK custom icon sets require on-device verification.
- Existing installed configuration and data are not reset; previous i666 archive remains unchanged.
