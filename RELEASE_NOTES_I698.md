# TAK Map v1.4.0-i698 — Offline Maps 50-State Regions

## Changes
- Download Area dropdown: Current View, Draw Area, all 49 non-California states, and California split into Northern, Central, Southern. Searchable; 54 total entries.
- Countrywide fixed 52-polygon geographic catalog derived at build time from Basemap US counties. No runtime shapefile / shapely / geopandas dependency. California county groups: 31 North, 19 Central, 8 South; geographic divisions are practical county-defined groupings, not official state subdivisions.
- Region selection draws a temporary orange stroke; Current View and Draw Area retain original rectangle workflows.
- Server estimate and downloader share the same polygon-to-XYZ tile-span conversion, avoiding ocean/neighboring bounding-box tiles and handling Alaska/Hawaii multipolygons.
- Downloads exceeding 250,000 tiles (or `TAK_DASH_OFFLINE_DOWNLOAD_MAX_TILES`) become logical sub-batches within one user-facing map/MBTiles database, without a parent-map tile limit. Preserve pause/resume and cached successful tiles.
- A failed tile is tried up to four times total (initial plus 3 retries) and then recorded in an indexed `offline_failed_tiles_i698` manifest in the MBTiles file. Other tiles continue. Final incomplete maps offer Retry/Finish; Retry requests only missing coordinates, Finish As Is retains their manifest for later repair.
- Configured HTTP/HTTPS XYZ sources including Custom XML imports are eligible. No arbitrary provider blacklist. Provider terms, limits, authentication and network policies are not circumvented.
- Main action **Download**, not Create Offline Map; retained earlier downloaded packs and i697 radar controls.

## Compatibility
- Full source upgrade from exact i697. User data remains in `/var/lib/tak-map`; installer does not remove offline maps or overwrite environment choices.
- Download batches are sequential accounting partitions with shared one-file SQLite storage, rather than multiple finished MBTiles packages. Existing i697 partial MBTiles records can resume via the new path.
- Custom XML sources must supply an ordinary HTTP(S) XYZ URL template. Sources requiring unsupported proprietary APIs or provider authentication may fail; their failures are recoverable.
- Regions are for planning/offline coverage, not official property boundaries. Extreme-zoom downloads may be very large. Provider permission, available storage, and network bandwidth are the operator's responsibility.
- NDM elevation-to-Cesium terrain adapter is still pending separate dataset validation.

## Validation
See `VALIDATION_I698.md`. Live TAK server and real provider tests remain to be performed after install; offline fixture tests cannot prove third-party provider permissions or tile freshness.
