# TAK Map v1.4.0-i698 — Offline Maps validation

## Source baseline
- Original full-source ZIP: `tak-map-v1.4.0-i697.zip`.
- i697 runtime, radar, basemap stack and existing application data formats retained.
- Added `tak_map_offline_regions_i698.py`, `tak_map_offline_downloader_i698.py`, `assets/tak-map-offline-us-regions-i698.json`, `assets/tak-map-offline-maps-i698.js`, `assets/tak-map-offline-maps-i698.css`.
- Added build-only region generator and offline-map Python/Chromium regressions.

## Validation passed offline
- 52 geographic choices = 49 whole states + 3 mutually exclusive, complete California county groupings; 54 total dropdown selections including Current View and Draw Area.
- Geographic boundary data derived from Basemap US counties via a **build-time only** script; no GIS dependency at runtime. All 52 region IDs produce nonzero tiles at z5, and Alaska's eastern and western antimeridian sides are represented.
- Polygon tile span rasterization excludes bounding-box neighbors; tested against geometric intersections in random Arizona/California/Alaska/Hawaii/New York samples.
- One MBTiles file per logical parent, compressed internal batch accounting capped at `TAK_DASH_OFFLINE_DOWNLOAD_MAX_TILES` (default 250,000), with durable SQL batch manifest.
- Initial attempt plus three tile retries, continuing other tiles after failure. Missing coordinates are stored in `offline_failed_tiles_i698` in the MBTiles. Targeted retries fetch only failed tiles; successful ones are not refetched.
- Retry/Finish accepts incomplete map or selectively retries without overwriting the original total tile count/batch count; existing partials can be resumed.
- Imported Custom XML HTTP(S) XYZ templates included as eligible sources; no application-level provider blacklist.
- Chromium browser fixture: 54 selections, search, California/Alaska outline selection, Current View outline suppression, Download action, batch estimate, incomplete recovery control, and no uncaught errors.
- i696 radar history backend (14 cases), radar Chromium UI, imported basemap Chromium UI, and i693 weather Chromium tests all pass.
- Python compile for new modules and `tak_dashboard.py`; Node syntax for UI module; Bash syntax for `install.sh`.

## Limits and live test obligations
- Actual configured upstream basemap provider policy, authentication, download capacity and outages are not controlled by this software. No provider restrictions are bypassed.
- Offline tests simulate tile HTTP responses. Actual high-volume state downloads (including larger-than-250k internal partitions), disk-space pressure, live failed-tile recovery, and in-service upgrade are NOT yet tested on the user's server.
- Geographical outlines are simplified county/state boundaries for offline coverage, not legal survey boundaries. Exact California regional groupings are documented in the source generator.
- NDM-to-Cesium actual terrain geometry is not included; it still requires real NDM dataset and vertical datum verification.
