# TAK Map v1.4.0-i693 — Radar partial-coverage recovery

**Baseline:** Exact full source package `tak-map-v1.4.0-i692.zip`, SHA-256 `c32508802938428c38e3ccca313cc7b128f4d3ebaa109c0b29fadc47362ed997`. All persistent application data and existing TAK Map configuration remain in place. **This is the radar reliability release, not Phase 3 animation.**

## Changes

- **Isolated tile failures:** An individual NWS tile error no longer invalidates the global radar provider or its working tiles. Each backend tile attempts up to two bounded retries for transient errors before returning its own error. Concurrency remains capped at four upstream requests; the cache and same-origin authentication protections remain.
- **Observation frame selection:** The primary NWS ImageServer now attempts to query its image catalog for an actual `idp_validtime` rather than relying solely on the published range endpoint. If the catalog is unavailable, the range endpoint is used provisionally and the UI labels the frame time **unverified** rather than claiming exact observation parity.
- **Browser tile recovery:** Leaflet counts current requested tiles and retries failed individual image tiles with bounded delays (1.25 s, 3.4 s, 8 s). Progress displays `Radar loading`, `Radar recovering`, `Radar partial`, or `Radar ready` based on current viewport tile events. A valid transparent PNG is counted as a *loaded tile*, not as a provider error.
- **Frame stability:** A replacement 2D radar frame loads behind the prior layer. The prior frame remains visible until enough of the next frame loads, or it expires after a bounded ten-minute stale period. The replacement no longer wipes all working imagery immediately. 3D frame replacement also briefly retains the previous imagery layer while new tiles begin to load, but 3D tile-completeness counters remain limited.
- **Preserves:** Existing BASEMAP card, radar opacity and i691 localStorage preference key, existing NWS weather-alert endpoint, route interactions, map data, terrain and Blend/Tone controls. Old i692 endpoint and runtime assets remain installed for compatibility; the new browser uses i693 routes.

## API / runtime

- Authenticated `GET /api/tak-map/weather/radar/status-i693` — provider, selected frame, `frame_source` (`catalog_observation`, `time_range_provisional` or `latest_only`), partial-health fields, cache history, last success/error and native zoom.
- Authenticated `GET /api/tak-map/weather/radar/tile-i693/{z}/{x}/{y}.png?frame={token}` — same-origin PNG image; only fixed NWS upstream HTTPS host and validated XYZ coordinates, no arbitrary URLs or BBOX. Optional `attempt=1|2|3` is a retry cache-buster and is not forwarded as an upstream parameter.
- The unchanged NWS alert API remains `/api/tak-map/weather/alerts-i691`.

## Scope / known limitations

- **No live NOAA imagery parity claim.** Offline fixture and Chromium tests cannot establish that the offshore returns southwest of the Channel Islands precisely match radar.weather.gov; compare the same MRMS reflectivity product, frame timestamp and map bounds on the installed server. If NOAA catalog querying is blocked, i693 uses a provisionally labeled time-range timestamp, not an independently verified observation.
- NWS service imagery can be legitimately transparent (clear/no-data), and NWS viewer imagery may show a different selected product/time or reflectivity threshold. A successful PNG is not proof of precipitation and does not guarantee identical radar pixels to the viewer.
- Browser viewport counters are Leaflet 2D tile events; 3D Cesium tile counts are not equivalent. Recovery remains dependent on provider availability and upstream quotas.
- NOAA outages and repeated 503s may still result in missing or stale tiles. Status is designed to expose degradation, not to create or synthesize radar returns.
- **Not included:** Phase 3 historical playback/timeline, GOES clouds or other TAK Map changes. Plan Phase 3 as i694 only after installed i693 coverage checks.

## On-server validation

1. Download/transfer the ZIP to `~/Downloads` (there is no `~/Downloads/tak` directory). Extract into a fresh `~/Downloads/tak-map-v1.4.0-i693` directory and run `sudo ./install.sh`. Retain the i692 ZIP as rollback.
2. Hard refresh the browser (`Ctrl+Shift+R`). Enable Radar Reflectivity and NWS Weather Alerts. Confirm requests only target `/api/tak-map/weather/radar/tile-i693/` for radar imagery.
3. Zoom to the Channel Islands and compare with radar.weather.gov at identical bounds, product and observation time. Watch for `Radar partial` / recovery/ready in BASEMAP and check Network HTTP responses. Use `status-i693` while logged in to inspect `frame_source`, `recent_tile_errors`, and provider state.
4. Verify saved opacity, radar ON/OFF, current data/route interactions, weather alerts, 2D/3D switch and refreshed frames. Report any continuing gaps with timestamps and failed tile error codes.

## Offline validation

Focused backend mock tests (eight scenarios), Chromium 2D/3D fixture, Python/JS/installer syntax, ZIP CRC, fresh extraction and full source SHA-256 comparison are run as part of packaging. Actual NOAA tile requests cannot be tested in the build environment because outbound DNS is unavailable.
