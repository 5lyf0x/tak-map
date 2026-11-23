# TAK Map v1.4.0-i677 — Exact Route Save Identity and Basemap Stack Visibility

Built from the full i676 source; i676 remains the rollback package. No data migration or background reprocessing is required.

## Fix 1 — Route saving and verification

- The new local route import's unique `added[].id` returned by `POST /api/tak-map/import` is the ONLY identifier used to verify its `GET /api/tak-map/imported` read-back; no filename fallback.
- Existing saved route updates remain pinned to their import and object identifiers, with the original revision-protected endpoint unchanged.
- A bounded read-back retry accommodates short storage visibility delays without silently reuploading or accepting a different record.
- Verify all persisted vertices and order (within existing coordinate-rounding tolerance), including waypoints and direct connectors for unresolved Valhalla legs. A true missing/truncated route continues to fail visibly and leaves the editor intact.
- Error messages identify the new import ID when available, to distinguish a genuine persistence failure from a same-name collision. No existing route is deleted or overwritten.

## Fix 2 — Basemap stacking and transparency

- Raise the dedicated managed basemap pane from z=190 to z=220, ABOVE Leaflet's ordinary raster tile pane (z=200) and BELOW vector overlay panes (z>=400).
- Remove stray legacy single-basemap raster from the map when the managed stack takes control; do not remove unrelated external/offline map sources.
- Keep the first enabled layer in sidebar order visibly above lower layers. Preserve per-layer checkboxes, opacity percentages, reorder actions and existing browser-persisted settings.
- Place separately enabled shaded relief in its own z=230 pane above the blended basemaps, below vectors. The relief's own opacity remains independent.
- Bust cached runtime asset URLs for i677. No change to the approved Soft Pill slider design or 3D terrain source selection.

## Validation and limitation

- The actual Python import handler was exercised using two same-named route uploads; unique IDs and complete route geometry confirmed.
- Chromium tests verified repeat saves by ID, full geometry, truncation rejection and retention of the editor, plus mock pane color/opacity/reordering/toggle behavior.
- Inherited route, graph selection and security checks are retained. Actual server installation, online ESRI tile acquisition, and the user's original trail were **not** exercised here and need a live check.
