# TAK Map v1.4.0-i691 — BASEMAP native weather

Based on the complete i690 source archive. No reset/migration of TAK Map Local Data, routes, imports, basemap catalog, NDM assets, or Gateway configuration.

- WEATHER OVERLAYS added beneath the existing BASEMAP layer controls. NOAA nowCOAST MRMS radar reflectivity and National Weather Service alert polygons have independent switches, radar opacity and freshness/error messaging. Defaults off until enabled; settings persist in browser local storage.
- A fixed-host, authenticated, read-only backend proxy exposes NWS GeoJSON alerts and NOAA WMS capabilities; the server caches provider payloads for 90 / 120 seconds respectively, uses bounded downloads, and fails with an explicit 503 if the provider is unavailable. Radar tiles use NOAA directly; no arbitrary-URL proxy or mass tile downloads.
- Leaflet radar raster sits in its own noninteractive pane above raster basemaps and below tactical markers. Alert geometries appear in their own pane and support details. Alerts with no GeoJSON geometry are counted but not mapped.
- Cesium 3D supports WMS radar imagery and GeoJSON alert geometry on a best-effort basis, and preserves overlay preferences on 2D/3D switches. Terrain and baseline 3D renderer are unchanged. NOAA/NWS feeds and 3D compatibility must still be validated on the real installed system.
- Removed the legacy stand-alone USGS Shaded Relief overlay control and renderer, without removing ordinary selectable basemap entries, viewshed elevation, NDM terrain, or 3D terrain.
- Preserves the BASEMAP stacked layer order/opacity, Blend/Tone and custom basemap manager.

## Limitations and follow-up

- Radar animation and optional GOES imagery are not implemented in i691.
- Provider HTTP, WMS credentials/CORS, live radar tile alignment, and real 3D UI can only be certified during a networked installed-server/browser test. No claim of live end-to-end testing is made here.
- Alerts with no polygon geometry are reported as unmapped. Cesium alert entity details do not use the same popup as Leaflet.
- Weather alert polygons are supplemental situational awareness, not an emergency notification or warning guarantee.
