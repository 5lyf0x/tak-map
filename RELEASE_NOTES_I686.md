# TAK Map v1.4.0-i686 — Infrastructure Overlays: Mixed Modes and Display Budget

**Baseline:** v1.4.0-i685. All prior TAK Map feature assets, Local Data, route geometry, NDM, MVUM, VEIL, and existing infrastructure storage are preserved; this package contains source code only.

## New behavior

- **Management tab is not map visibility:** Online and Offline GIS layers can remain visible and clickable simultaneously. Online and Offline master visibility controls are independent; turning Online off prevents online provider fetches. Switching the management tab neither clears rendered layers nor dismisses a selected infrastructure object.
- **Multiple expanded categories:** expand or collapse any combination of the 14 built-in and custom Infrastructure categories. The new persisted array of category IDs migrates the i685 one-open localStorage key without deleting old preferences.
- **Geographic rendering:** automatic layer fetches use a bounding area 1.5× the current viewport width and height, centered on the map (25% beyond each edge). Dateline-crossing areas are split into valid WGS84 queries. Each source has an independent, cancelable request generation and spatial cache. Manual download areas continue to use the user's explicitly selected bounds.
- **Display budget:** at most 5,000 individual GIS features are rendered per layer across the buffered query area; this cap is enforced in the map query endpoint and the browser. Dense offline layers use deterministic spatial/fid-hash sampling and explicit `LIMITED—zoom in` status, not unbounded full-data rendering. Complex geometries are simplified for drawing only; source geometry is unchanged in storage. The 5,000-feature limit **never applies** to manual region downloads, imports, stored data, or full GIS dataset exports.
- **Progressive online rendering:** ArcGIS GeoJSON pages (up to 500 features at a time from the interactive card) display incrementally. Obsolete requests are aborted in the browser, provider pages are bounded, and active layers are tracked independently. Failed providers are distinguished from limited data.
- **Counts:** Online rows show the number of individual features drawn in the unpadded viewport. Offline rows show `visible / total stored`, with the stored denominator unaffected by interactive sewer diameter filters. During incomplete loads, error/partial/limited states are disclosed.
- **Independent layer colors:** source-specific color swatch and Reset action; six-digit HEX validation and persistence in an additive `layers.color` database column. The original online source and a downloaded offline derivative can be styled independently. Changes update already-rendered 2D/3D map objects without new provider requests.
- **Existing interactions retained:** hover tooltips, single-click right-side Object Details, raw GIS attributes, export actions, 36-inch default sewer filter, downloads/imports/exports (GeoPackage, GeoJSON, zipped Shapefile, KML/KMZ), provider URLs and route editing isolation.

## Installation, storage and rollback

The installer adds the i686 backend module and UI assets while retaining older release files for compatibility. The application's existing `/var/lib/tak-map/infrastructure/infrastructure.sqlite3` database is upgraded **additively** when opened; tables, categories, saved layers and features are not dropped. Upgrades preserve user-selected downloads, custom categories, and original saved local map objects. For rollback retain the prior i685 source ZIP and a copy of `/var/lib/tak-map/infrastructure` and `/var/lib/tak-map/tak_map_imports`.

## Scope and limitations

- **Provider support:** ArcGIS REST FeatureServer/MapServer GeoJSON feature queries; other protocol connectors (OGC WFS/API Features) and administrative-region download presets remain future work. Source availability, service support for paging, and coverage depend on each provider.
- **Partial data:** a capped layer is labeled limited, not represented as geographically complete. The deterministic capped subset is an interactive overview, not a spatially exhaustive index. Zoom in for more individual objects. Offscreen but buffered objects are not counted as viewport-visible.
- **3D:** the existing basic Cesium point/line/polygon renderer is retained with independent layer colors, but live terrain deployment needs verification. Geometry complexity limits apply to interactive drawing, not stored data.
- **No live server connection:** validation used synthetic GIS fixtures, SQLite stores and Chromium tests; real provider speed, changes to third-party schemas, and the deployed TAK Map server need on-host verification.
- **Total resource load:** the 5,000 cap is per layer, not a single global cap across all simultaneously enabled layers. Users should still disable unneeded dense layers when experiencing low-memory devices.

## Acceptance checks

New i686 tests cover i685-to-i686 persistent database migration, per-layer colors, downloaded child color independence, a 5,001-feature dense dataset with a complete untruncated export, bounded ArcGIS requests, and desktop/mobile Chromium multi-open categories, mixed-source rendering, 1.5× bounds, date-line split, preserved selection on tab switching, tooltip/details, viewport counters, 2D/3D recoloring, and master origin switches. Dense SQLite benchmarks cover 5,001, 50,000, and 250,000 stored features. See `VALIDATION_I686.md`.
