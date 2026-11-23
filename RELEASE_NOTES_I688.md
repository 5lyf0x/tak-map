# TAK Map v1.4.0-i688 — Offline Infrastructure reliability, inspection, filtering and search

**Baseline:** v1.4.0-i687. **Type:** full source release. **Rollback:** i687.

## Implemented changes — all 11 approved work groups

1. **Offline-only Infrastructure.** A single category tree replaces both Online/Offline tabs. No automatic online feature streaming or provider requests during normal map operation. Existing imported and downloaded offline datasets remain separate from Local Data. Explicit, user-initiated GIS downloads and all existing import/export formats remain available; former online provider definitions are retained as download sources rather than deleted.
2. **5-pixel line picking tolerance.** Leaflet line objects have invisible, interactive 5px additional tolerance beyond each visible stroke edge; Cesium line picking uses a separate broader hit line. The displayed line thickness is not changed.
3. **Correct line selection.** A 2px red outline surrounds the line's configured color instead of replacing it with white. Blank-map clicks, another selection, and closing Object Details clear the outline. Hover tooltips remain disabled.
4. **Reliable cold-start hydration.** Enabled and eligible offline layers load after both map and Infrastructure configuration are ready, even when the card starts collapsed. No checkbox toggle cycle is needed.
5. **Object Details spacing.** Infrastructure details use 12px horizontal padding, more consistent vertical rhythm, and wrapping of long GIS values and controls in the existing right-hand pane.
6. **Uncollapsed GIS attributes.** All source GIS attributes, including zero, false, null and nested values, are displayed immediately, with escaped text and no hidden disclosure list.
7. **Point symbols.** Each point layer can retain its circle dot or choose a symbol from the existing TAK Icon Registry. The infrastructure picker uses a dedicated selection target and does not change ordinary point-editor state; the stored reference is shared by Leaflet and Cesium with circle fallback when unavailable.
8. **UI controls survive background refresh.** The five-second job/status poll updates only job and counter elements; it does not reconstruct category controls, dismiss an open dropdown, or collapse other categories.
9. **Reliable panning.** Immutable per-layer committed viewport snapshots, cancellation/stale-request guards, bounded retries and replacement-after-load protect layers from disappearing when the map is moved quickly. The viewport plus 50% spatial buffer, min zoom, per-layer color and 5,000-feature display cap are preserved.
10. **Attribute filters.** Persistent per-offline-layer multi-rule ALL/ANY filters support numeric, text, date and empty-value comparisons (`=`, `!=`, `>`, `>=`, `<`, `<=`, contains, does-not-contain, starts/ends with, between and is empty/not empty). Filters apply before display sampling and to search/exact selection; unfiltered GIS storage and ordinary exports remain complete. The existing 36-inch sewer-main filter remains compatible.
11. **Global Infrastructure search.** The existing left sidebar search now includes enabled, visible-category, filter-eligible offline infrastructure records throughout saved datasets, not just the current viewport. The backend uses a derived SQLite FTS5 index where supported. Selecting a hit pans/zooms to its feature and opens Object Details without an online query.

## Preservation and migration

The Infrastructure SQLite database adds `layers.filter_spec`, `layers.point_symbol_mode` and `layers.point_symbol_ref` columns and creates a rebuildable search index. **No existing GIS features, layers, categories, old provider definitions, Local Data, route geometry or application configuration are deleted.** Previous upgrades retain their columns and data. The original i687 source package remains the rollback baseline; back up `/var/lib/tak-map/infrastructure/` and `/var/lib/tak-map/tak_map_imports/` before deploying.

## Performance and limitations

- The 5,000-feature cap applies to per-layer interactive rendering only; it does not truncate downloads, stored GIS data, search coverage or ordinary exports.
- Synthetic local benchmark: a 50,000-feature offline point layer with a rare attribute filter yielded 10 qualifying features in 0.38 seconds and a matching indexed search in 0.04 seconds. These are test-environment measurements, **not** live server performance figures.
- The first indexed search after upgrading a large existing database may require a one-time FTS backfill. Provider availability and GIS export dependencies vary by environment.
- i688 has not been deployed or validated against the user's running server. In particular, actual live server disk performance, all provider download flows and end-to-end Cesium UI behavior still need production verification.

See `VALIDATION_I688.md` and `tests/test_i688_infrastructure.py` / `tests/test_i688_infrastructure_browser.py`.
