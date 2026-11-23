# TAK Map v1.4.0-i678 — Release notes

Built from unchanged i677 full source rollback baseline.

## Improvements
- Route Creation captures clicks over NWS warnings and other unrelated features, while retaining route point and segment editing. Object selections restore after exiting the tool.
- MVUM: red overlay from z10 through map-supported zoom; z10 composites four z11 tiles; missing intermediate zoom tiles fall back to the appropriate z11 parent, and higher zoom scales native z16 detail; visible requests precede bounded speculative viewport+50% buffer; retry transient failures and cancel stale work.
- Basemap Layers: one canonical Soft Pill implementation, no old periodic styling timer; only drag grip can reorder; up/down controls removed. 50/50 Blend/Tone buttons open floating anchored menus without list reflow; 12 modes and persistent per-layer tone.
- Custom Map Details, Terrain Relief, Contour Emphasis process actual raster pixel data. **They require cross-origin pixel access** to the selected tile provider. If CORS/pixel access is prohibited, the mode reports an error and cannot render that source. No tile-server proxy or bypass was introduced. These are approximate visual algorithms, not semantic road/contour extraction.
- Road/trail names: optional admin-triggered source index from an existing **readable** regional OSM PBF; sqlite FTS search through existing sidebar. The index is never automatically built. An on-server `osmium` CLI, sufficient free disk, and authorized read access to the PBF are required. The index has not been built against the actual US West source here.

## Preserved compatibility
- Existing main Basemap dropdown remains, because it still drives 3D, Replay, Offline mapping and publishing. This is a functional dependency, not a second transparency implementation.
- No changes to NDM source data/graph files, map data, saved routes, import identities, or graph activation.
- Basemap Blend/Tone CSS effects are for Leaflet 2D; not claimed to be equivalent in 3D Cesium.

## Follow-up live verification
- Test ESRI/USGS raster source headers to establish whether custom pixel modes are usable with each provider. Do not treat synthetic tile tests as provider approval.
- On a live authorized NDM host, build the optional road/trail index and verify real names, available storage, and appropriate graph routability classification.
- Test z10→z17 MVUM on the actual Valhalla graph (including z12–13), and route clicks inside an active NWS polygon.
