# TAK Map v1.4.0-i697 — Radar history timeline and Offline Maps capacity

**Release date:** November 13, 2026. **Base:** exact v1.4.0-i696 validated full-source archive. **Rollback:** v1.4.0-i696.

## Included changes

1. **Radar history time slider:** Replace the browser-default timeline appearance with the existing BASEMAP LAYERS Soft Pill style, including the same round thumb, track size, filled-progress track, keyboard accessibility, and responsive layout. Position on the timeline updates the filled progress indicator; all i696 history windows, playback controls, opacity controls and radar frame APIs are preserved.
2. **Offline maps:** Increase the default `TAK_DASH_OFFLINE_DOWNLOAD_MAX_TILES` from 20,000 to **250,000**. Existing per-job tile-count estimate and resume checks use this value automatically. Continue to enforce concurrency bounds and persist downloads in the established offline storage. Override remains available in `/etc/tak-map.env` and **takes precedence** if already set. Large downloads require adequate storage and tile-provider permission.
3. **Version identity:** Update version, runtime cache-busting, sidebar badge and API-reported iteration to i697. Keep i696 feature-specific asset filenames and history API route names intentionally unchanged for compatibility.

## Retained and known limitations

- All v1.4.0-i696 features are retained. NDM data still does not provide a verified Cesium 3D terrain source; this release does not pretend otherwise.
- i697 has no host-side installation or live GPU validation from this build environment. NOAA's time-specific historical mosaic correctness still needs visual verification on the TAK server.
- Higher download caps do not bypass source-specific access policies, throttling, bandwidth, memory or disk constraints. The 250,000 cap is a maximum, not a recommendation to download all tiles at once.

## Installation

Download the ZIP to `~/Downloads` on the TAK host. Extract into a new folder (never over i696):

```bash
cd ~/Downloads
unzip -q tak-map-v1.4.0-i697.zip -d tak-map-v1.4.0-i697
cd tak-map-v1.4.0-i697
sudo ./install.sh
```

Do not remove `/var/lib/tak-map`, `/etc/tak-map.env`, imported datasets, offline MBTiles, points or routes. Retain the full i696 ZIP for rollback.
