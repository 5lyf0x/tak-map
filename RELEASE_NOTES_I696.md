# TAK Map v1.4.0-i696 — NOAA radar history, 2D basemap reliability, terrain fidelity

**Release date:** November 13, 2026. **Base:** exact validated v1.4.0-i695 full-source archive. **Rollback:** i695 full release.

## Changes

1. **NOAA/NWS MRMS radar-history playback:** Historical observations in existing BASEMAP → WEATHER OVERLAYS → Radar Reflectivity, with Play/Pause, step, first/last, timeline scrub, 30m/1h/2h/4h windows, Loop, 1×/2×/4× and LIVE. Off by default; radar ON state/opacity settings retained. History is backed by fixed-host NOAA ImageServer records strictly inside its current time extent. Near-simultaneous regional raster records are grouped into nominal five-minute observation bins, without inventing times. Authentication, fixed-provider URL, issued frame IDs and bounded cache protect historical tile requests. History is suppressed (LIVE only) if fewer than three actual observations are available. Actual historical mosaic correctness and motion still require verification against NOAA on a server with access to real precipitation.
2. **Radar stability and overlay preservation:** Retain last-good 2D radar image while replacement is incomplete, recover unexpectedly removed 2D radar imagery even when NOAA metadata is unavailable; Cesium historical imagery no longer retires visible old frames solely due to a seven-second timer. Weather alerts remain independent.
3. **2D basemap visibility and imported catalog:** Registered XML basemaps are synchronized into BASEMAP LAYERS without reimporting, order/enable/opacity/settings retained; cached tiles are refreshed on provider URL/TMS/zoom changes; visible warning appears on repeated 2D tile errors. No speculative 3D basemap-stack rework.
4. **MVUM/route editor:** Native MVUM mini-toolbar button survives recreation and works at zoom 9 with composite native zoom-11 vector tiles. Compact route elevation hover mileage follows the cursor in a strip BELOW the graph.
5. **Local Data point editor:** Persistent `local-…` IDs resolve correctly, with legacy ID fallback, duplicate protection and stable save identity; fixes “Local Data point not found” despite visible marker.
6. **Local terrain quality / smooth 3D:** High-only for imported Local DEM elevation, independent Streamed quality preference. Coverage-based tile refinement to source spacing, NODATA safeguards, remove redundant legacy DEM mesh rebuilds, adaptive High SSE while camera moves, minimize Cesium basemap reloads, preserve independent imagery overlays.
7. **Permanent Basemap Pre-cache removal:** Remove old background prefetch engine/UI; preserve on-demand basemap tile loading and user-managed OFFLINE MAPS.
8. Version identity bumped to i696; all runtime asset query strings cache-busted, installer includes history module and controls. Application data/configuration stay in their existing persistent locations.

## Explicit limits

- **NDM is not yet a Cesium terrain source in this release.** This package includes read-only `scripts/ndm_terrain_readonly_verification_i696.py`; actual prepared NDM SQLite schema, vertical datum, and real terrain-tile geometry must be verified on the host before exposing an NDM Terrain option. No false claim of NDM elevation in 3D.
- NOAA historical catalog, time-specific exports and changing regional PNG bytes were verified in a prior read-only probe on the user's host (six of six PNG exports succeeded). That probe does not prove timestamp-accurate moving mosaic imagery. **Live history correctness, real Cesium/GPU performance, partial DEM NODATA behavior, user-specific tile URLs and service restart were not tested in the package-builder environment.**
- 2D stack z-index works correctly in isolated browser tests; real-world reported top-layer invisibility might also reflect a failed upstream tile source, opacity 0 or Blend settings. New tile status warnings improve diagnosis, but no unverified root-cause claim is made.

## Installation

Download this source ZIP to the TAK server `~/Downloads` and run, in that directory:

```bash
unzip -q tak-map-v1.4.0-i696.zip -d tak-map-v1.4.0-i696
cd tak-map-v1.4.0-i696
sudo ./install.sh
```

Always extract to a **fresh** i696 folder, not over a previous release. Retain `tak-map-v1.4.0-i695.zip` as rollback. Never clear `/var/lib/tak-map`, `/etc/tak-map.env` or existing maps/routes/imports during upgrade.
