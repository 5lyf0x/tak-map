# TAK Map v1.4.0-i678 validation record

## Tests performed in isolated workspace
- Python syntax: `tak_dashboard.py`, `road_search_i678.py` passed; legacy embedded inline JavaScript strings produce pre-existing invalid escape SyntaxWarnings.
- JavaScript syntax: canonical Basemap, MVUM, route exclusivity, road search, routing dropdown, route editor passed `node --check`.
- Installer: `bash -n install.sh` passed.
- Chromium with mocked 2D map: canonical Soft Pill on initial checkbox toggles; grip-only dragging; 50/50 Blend/Tone controls; floating popover overlays rather than expanding; twelve modes and custom parameter controls; per-layer tone; synthetic custom raster processing all passed.
- Chromium with mocked overlay: click on simulated NWS polygon routes exactly one waypoint, unrelated popup click blocked, route point control retained, normal interaction restored when route tool exits.
- Chromium with mocked Valhalla MVT: z10 through z16 tile handling/child composition and z12 failure fallback to z11 passed; z16 native detail retained and maxZoom=24 configured; red stroke code verified.
- Python fixture index: explicit job and road/trail SQLite FTS5 name/ref query passed.
- Existing regression tests: i675 graph-switch and rollback (4), i654 route snap (6), i677 duplicate-name route browser, i676 13-waypoint mixed route browser, i677 real import backend, and i675 HTTP activation passed.

## Not verified in this environment
- Actual ESRI/USGS cross-origin pixel processing and the respective data licenses. Custom modes **require CORS permission**, otherwise will report unusable on that source. Actual test was synthetic only.
- Actual US West 3+GiB OSM source indexing, `osmium export` on the user's host, runtime storage/resource limits, and index completion. Index is explicitly initiated and is not prebuilt.
- Real NWS alert / AIS / VEIL overlays with the live server, actual Valhalla z10-z17+ tile responses and network load, and full Chromium integration with live TAK Map login.
- 3D Cesium parity for custom raster blends (not claimed; 2D only).

## Retained compatibility
- Primary Basemap dropdown remains because 3D, Replay, offline and publishing reference its selection semantics. It does not own a separate opacity slider.
- No NDM PBF/graph modifications or unauthorized downloads.
- i677 source remains separate and unmodified.

## Archive verification
See final delivery metadata for SHA-256 and file count. ZIP CRC, source checksum manifest and clean extraction comparison verified separately.
