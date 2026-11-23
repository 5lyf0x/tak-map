# TAK Map v1.4.0-i692 — Same-origin weather radar reliability

**Baseline:** complete verified `tak-map-v1.4.0-i691.zip`. All existing TAK Map Local Data, route/point/shape stores, NDM datasets, imported GIS layers, credential settings, existing basemap catalogs, Gateway integrations and working i691 weather-alert path remain untouched.

## Fixed

- Replaces browser-to-nowCOAST WMS image requests (repeated `ERR_BLOCKED_BY_RESPONSE.NotSameOrigin`) with authenticated, same-origin radar tile requests served by the TAK Map backend. Browser Leaflet and Cesium use exactly the same XYZ tile service and tiles do not require browser access to NOAA origins.
- Replaces generic `/api/tak-map/weather/radar-i691` status with `/api/tak-map/weather/radar/status-i692`, publishing the selected provider, frame token, upstream observation time **only when known**, last successful tile fetch, service state, and sanitized error code.
- Primary NOAA/NWS provider: official time-enabled MRMS base reflectivity ImageServer (`/radar_base_reflectivity_time/ImageServer`); fallback: official latest-image MRMS base reflectivity MapServer (`/radar_base_reflectivity/MapServer`). Both have fixed HTTPS hostnames and fixed ArcGIS REST export paths. Automatically selects a complete provider/frame rather than mixing tiles from different providers.
- Native backend verifies upstream REST metadata, HTTP status, approved hostname, image MIME/PNG header and integrity, enforces 256×256 images and a 1.6 MB response cap, validates XYZ z/x/y, blocks redirects, limits upstream concurrency to four, and maintains a bounded memory-only LRU/TTL cache. Rendering beyond native zoom 10 upscales existing tiles rather than requesting excessive native detail.
- Radar tile errors are distinguished from metadata errors, and provider/frame changes rebuild only the radar layer. Refreshed frames do not require a full TAK Map reload. Alert and radar polling no longer share the same in-flight flag.
- Maintains existing WEATHER OVERLAYS card design and i691 browser settings key, including radar ON/OFF, NWS alerts, and user-set opacity (e.g. 94%). No redesign of BASEMAP, Blend/Tone, USGS Topo, custom basemap stack or Cesium terrain.
- Retains the i691 NWS alerts API and unchanged geometry/count semantics; no invented geometry or separate Gateway dependency.

## Scope and qualifications

- **Not a live NOAA verification.** Source compilation, fixture-driven service tests, browser stub integration and ZIP validation cannot prove that the real server can reach NWS radar endpoints, or that NOAA will return usable transparent imagery in your specific location. Installed-system testing is required.
- The provider's published time extent can be reported as an actual timestamp for the time-enabled source. The fallback *latest* service supplies no valid observation time; the refresh token is not presented as an observation timestamp.
- Diagnostic status displays `Radar unavailable` rather than incorrectly reporting `No precipitation` when the provider is unreachable. Transparent radar pixels are valid images.
- Radar animation and GOES are deferred. No generic configurable URL proxy, file archive or map-data migration was introduced.
- Browser radar tiles are read-only and authenticated. Existing weather alerts and tactical data work independently when radar is unavailable.

## API

- `GET /api/tak-map/weather/radar/status-i692`
- `GET /api/tak-map/weather/radar/tile-i692/{z}/{x}/{y}.png?frame=<server-issued-token>`

Both endpoints require the existing TAK Map authenticated session. The legacy i691 radar metadata endpoint remains implemented for compatibility but is not called by the i692 browser.

## Recommended live smoke test

1. Install i692 over i691 without deleting application data. Force reload TAK Map (Ctrl+Shift+R).
2. In BASEMAP, ensure weather alerts still work independently; enable Radar Reflectivity. Browser Network should show same-origin `/api/tak-map/weather/radar/tile-i692/...` and **no direct NOAA radar image requests**.
3. Verify a `200 image/png` radar tile at a known live precipitation area, plus correct transparent coverage when clear. The radar status displays its provider and, when known, frame time.
4. Confirm 2D/3D tile alignment, high-zoom map behavior, opacity persistence, weather ON/OFF independence and no route selection interference.
5. In the event of a failure, check `/api/tak-map/weather/radar/status-i692` while logged in and the service's `journalctl -u tak-map -n 100 --no-pager` output for a rate-limited `TAK Map radar i692` code. Do not disable browser security features.
