# TAK Map v1.4.0-i682 — Local Data reliability and Basemap Blend dropdown

Source baseline: exact v1.4.0-i681 source archive. This package does not reconstruct data already removed by earlier versions; it protects the saved state currently present on disk and makes later reloads faithful to that state.

## Changes

1. **Local Data persistence:** The canonical imports store is authoritative. Preserve complete import collections and full route/shape coordinates without silent 30-import, 1,500-feature or shapefile 1,000-feature truncation. Reject unsupported/oversized new uploads without modifying existing data. Atomic catalog writes are verified by full readback.
2. **Loading and error handling:** An unreadable previously initialized catalog returns an explicit error instead of a successful empty collection. The browser retains its last good rendered data on failed loads, rejects stale/out-of-order load results and avoids hiding saved points merely because they are near route endpoints.
3. **Object identity and deletion:** Preserve stable IDs from saved data, and perform targeted local deletion with readback verification. Return compact mutation responses instead of trying to JSON-serialize large or recursive object catalogs.
4. **Basemap Blend:** Updating the blend mode also updates the button's visible value and title. All lower dropdown entries, including Terrain Relief and Contour Emphasis, are covered. When custom-mode options keep the popover open, retain the selected list's scroll position.
5. **Upgrade safety:** Uses the established `/var/lib/tak-map/tak_map_imports/` storage; does not clear existing catalog or browser preferences during installation. No new data migration.

## Validation and remaining limits

- Offline Python Local Data tests: persisted routes/points/shapes across reload, large collections, stable IDs, targeted deletion, safe failure behavior, legacy compatibility.
- Frontend Node checks: safe API refresh and object visibility.
- Headless Chromium: real clicks on scrollable lower blend modes, visible label, effective Leaflet mode, and persisted settings/reopen.
- Syntax, archive integrity, fresh source comparison and release metadata are verified during package creation.
- **Not live-tested on your TAK Map server.** Before upgrading, keep an independent backup of `/var/lib/tak-map/tak_map_imports/`. Verify counts, IDs and geometry before/after startup on the target system. The existing `tak-map-v1.4.0-i681.zip` is the rollback source.
