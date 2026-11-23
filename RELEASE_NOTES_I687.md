# TAK Map v1.4.0-i687 — Infrastructure category, zoom, provider and selection updates

Baseline: **v1.4.0-i686**. This is a full source release, not a hotfix. Existing Local Data, infrastructure GIS data, categories, downloads and configuration remain on their persistent storage paths. No destructive data migration is performed.

## Changes

1. **Mode-specific category removal**: `Remove from Online` and `Remove from Offline` act independently; restores are scoped to the active management mode. Built-in and user-created categories can be hidden without deleting data. Shared names and independent online/offline layers are retained. Legacy i686 `categories.hidden` is copied into the two new visibility flags exactly once.
2. **Minimum map zoom per layer**: `Always` or z0–z22, persisted in the infrastructure SQLite catalog. Existing built-in LA County sewer manholes and the new City of Los Angeles sewer structures default to **z14+**. The threshold disables viewport display queries and drawing, **not** offline downloads or GIS exports. Existing unrelated GIS layers retain `Always` unless changed by the user.
3. **New built-in GIS layer**: **Sewer Structures — City of Los Angeles** (`lacity-sewer-structures`), the City of Los Angeles Bureau of Engineering `Master_sewer_external/MapServer/0`. Disabled by default to avoid unexpected heavy queries; enable in Water & Wastewater / Online when needed. Includes sewer structures beyond maintenance holes; the Object Details panel exposes `MH_DESCRIPTION` and `MH_TYPE` where the provider publishes them.
4. **Dense-point distribution**: where provider feature counts support it and exceed the 5,000-feature viewport+50% budget, subdivide the requested region into a 4x4 geographic grid; distribute initial requests and redistribute unused budget to populated cells. Where count queries are unavailable, fall back to progressive page retrieval, respecting bounded request/page budgets. Previous full downloads and imports remain complete.
5. **Accurate status reporting**: `LIMIT REACHED` now denotes the 5,000-feature cap on the buffered working set, `PARTIAL` denotes incomplete provider paging, and `SIMPLIFIED` denotes display geometry simplification. All are independent of the smaller count shown for actual viewport-visible objects.
6. **No Infrastructure hover tooltips**: removed Leaflet tooltip binding and Cesium pointer-move/hover elements. Single-click still highlights a feature and opens existing right-hand Object Details in both Online and Offline modes. Other TAK Map tooltips remain unaffected.

## Preserved functionality

All 14 built-in infrastructure category definitions, user-defined categories, simultaneous Online/Offline map layers, persistent per-layer colors, viewport +50% loading, 5,000-feature interactive layer budget, 36-inch sewer-main diameter filter, GIS downloads/import/export, and the i682–i686 Local Data, MVUM, basemap and route/elevation corrections remain present.

## Important limitations

- Public ArcGIS REST services may have provider rate limits, access restrictions, partial data, and varying service support for feature counts or ordered paging. TAK Map does not impose a download bandwidth cap; provider limits remain respected.
- City of Los Angeles sewer structures include more than maintenance holes and should not be interpreted as a complete underground network map.
- Feature sampling when the 5,000-feature display cap is exceeded represents the working map view, not all provider records. Use geographic download/export for complete data.
- Full live querying against the City's GIS endpoint and Cesium behavior on the user's live TAK Map installation have **not** been validated by this release's local tests.

## Storage migration and rollback

The additive SQLite migration creates `categories.hidden_online`, `categories.hidden_offline` and `layers.min_zoom` if missing. On first upgrade, preexisting category hidden state is copied into both new mode flags; subsequent startups do not overwrite user changes. The legacy `hidden` column is retained. The prior release i686 is retained as the source rollback version; before installing, back up `/var/lib/tak-map/infrastructure/` and `/var/lib/tak-map/tak_map_imports/`. Downgrading the application preserves the extra columns, but i686 will interpret its old shared `hidden` flag rather than the new mode-specific flags.
