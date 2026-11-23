# TAK Map

**Current release: v1.5.0-i004** · Web-based TAK mapping, operational awareness, and offline navigation.

TAK Map brings live TAK objects, local and imported geographic data, offline basemaps, weather, infrastructure overlays, and route planning into a browser-based 2D/3D map. It integrates with OpenTAKServer, TAK Gateway, XTAK VEIL nodes, and locally prepared NDM routing/elevation data.

> **Release status:** i004 is a maintenance hotfix for i003 installation. The README describes functionality delivered across the current release series; individual integrations may require separate services, data packages, credentials, or operator configuration. Live operation depends on the installed host and connected data sources.

## Key capabilities

### Maps, layers, and terrain

- **2D and 3D mapping:** Interactive Leaflet 2D maps and Cesium terrain mode, with saved and imported routes, shapes, and relevant objects displayed across views.
- **Layer composition:** Enable multiple basemaps, reorder layers, and adjust per-layer opacity, Blend, Tone, and custom map-detail controls.
- **Saved per-user preferences:** Basemap enablement, ordering, opacity, Blend, and Tone persist on the TAK Map server by authenticated user (introduced in i699). Existing browser-only settings can be migrated explicitly.
- **Imported basemaps:** Custom source support, including configured XYZ sources and imported Custom XML sources where compatible.
- **Offline maps:** Download geographically selected areas as MBTiles, apply as basemaps, rename completed packs, send packs to EUDs, and manage existing maps. Imported maps support a TMS/XYZ tile-row setting.
- **Offline coverage selection:** Current View, Draw Area, 50 U.S. states, and separate North/Central/South California regions. Polygon-defined download areas are clipped to their boundaries.
- **Large download handling:** Downloads partition internally into bounded batches and produce one MBTiles file; the default per-batch tile limit is 250,000 tiles (configurable). Pause/resume, missing-tile retries, and Retry/Finish are supported.
- **Offline performance:** i003 added a read-only SQLite connection pool, cached map catalog lookup, smoother tile requests during panning, and scaling of the highest downloaded native zoom. i004 fixes installation of the required backend module.

Offline maps provide only the tiles and zoom detail actually downloaded. Upscaling beyond the highest available native zoom does **not** add terrain or imagery resolution. Source-provider licensing, authentication requirements, and available disk space still apply.

### Navigation, routes, and elevation

- **Route creation:** Manual and road-following routes, draggable waypoints, insertion on route lines, per-waypoint controls, distance summaries, and editable saved routes.
- **NDM / Valhalla integration:** Use operator-prepared, registered regional navigation graphs for road routing, with local graph selection and a movable Routing Data control.
- **Route geometry:** Save full resolved road geometries instead of retaining only waypoint anchors. Unresolved road legs remain explicit rather than silently fabricating connections.
- **Elevation profiles:** Compact and extended floating route profiles with position and steep-section inspection where supported by available elevation data.
- **MVUM overlays:** Motor Vehicle Use Map data can be shown for available navigation regions, with visibility controls.
- **Terrain-aware objects:** Saved/imported routes and shapes can display in 3D with their existing styling and visibility preferences.

**Requirements and limitations:** Road routing requires a compatible local Valhalla service and prepared NDM navigation data. A single continuous connected graph is needed for reliable routes crossing regional/state boundaries. Native NDM terrain geometry in Cesium is **not** presented here as a completed feature; it remains dependent on further data and datum integration.

### NOAA/NWS weather

- **Weather layers in BASEMAP:** Independent radar and National Weather Service alert controls, including saved visibility and opacity.
- **Radar:** NOAA/NWS MRMS-derived precipitation reflectivity through a same-origin proxy with cache and upstream recovery behavior for 2D/3D display.
- **Alerts:** NWS watch, warning, and advisory polygons with associated map interaction.
- **Radar timeline:** Historical-frame selection and Play/Pause/LIVE controls, subject to upstream frame availability and coverage.
- **Unified styling:** Weather opacity uses the same Soft Pill interaction as other basemap layers.

Radar is an online data source unless independently cached; historical coverage and frame availability depend on the upstream providers. Weather layers do not imply a fully offline forecast service.

### Infrastructure and local data

- **Infrastructure overlays:** Organized GIS layers with offline dataset use, optional source acquisition/import flows, per-layer visibility, colors, minimum zoom, and displayed/available feature counts.
- **GIS interactions:** Search and attribute filters, selectable point and line features, contextual details, copy coordinates, zoom to feature, and object export.
- **Viewport performance:** Bounded per-layer viewport rendering (5,000 features per layer in the i686 series) and data paging to avoid unnecessary full-dataset rendering.
- **Local Data:** Persist map points, routes, shapes, and imported geospatial datasets between sessions without the earlier silent import eviction or route-geometry truncation defects.
- **Icon Registry:** TAK tactical and custom symbol support, including point-symbol fallbacks where applicable.

Availability of individual infrastructure layers depends on imported local datasets and enabled sources. Display budgets do not intentionally delete underlying GIS data.

### Live tracking and TAK connectivity

- **OpenTAKServer:** User login/certificate integration, live TAK objects, Missions/Data Sync, native shape editing, and authorized Mission association.
- **TAK Gateway:** ADS-B/AIS ingestion and separate Replay integration, with independently configurable client-certificate policies for Gateway Data and Replay.
- **Replay:** Recorded periods, time-based Jump and Search, reconstructed state, and navigation to indexed aircraft, vessel, and EUD appearances when supported by the Gateway.
- **XTAK VEIL:** Node discovery/status, optional authenticated API snapshot/WebSocket sync, and compatible UDP CoT ingest; multiple receiver observations can retain node provenance.
- **Aviation and maritime awareness:** ADS-B aircraft silhouettes and operator details, AIS vessel symbols, selected-object emphasis, and live map search.
- **APRS and tactical symbols:** VEIL APRS symbol mapping and Icon Registry-backed map artwork where data is available.
- **Operational status strip:** Compact EUD, VEIL, Downloads, LAN, and Internet status, with TAK status when configured.
- **Map tools:** Range Rings, object selection, saved map interactions, and associated operator controls.

Connected services can be independently unavailable. Their cards, authentication, and data visibility do not mean the associated remote service or feed is installed automatically.

## What's new in v1.5.0

| Release | Highlights |
| --- | --- |
| **i004** | Fixes failed service startup after i003 by installing the bundled `tak_map_offline_perf_i003.py` module before backend startup. |
| **i003** | Pooled read-only SQLite MBTiles serving, faster catalog lookup, smoother offline pan/zoom, safe tile caching, and imported TMS/XYZ row selection. |
| **i002** | Restores reliable startup population of saved Offline Maps and the completed-pack Rename action. |
| **i001** | Rename completed offline maps; natural alphabetical sorting; scrollable 600px map list; consistent sidebar version identity. |

### Major additions from the late v1.4.0 series

- **i699:** State/area offline downloads, large bounded download jobs, improved Offline Maps UI, and server-side per-user basemap preferences.
- **i696–i698:** Historical radar timeline, radar interface refinements, offline download limits, and terrain/interface corrections.
- **i691–i695:** Native BASEMAP weather controls, MRMS radar proxy, NWS alerts, reliability improvements, and Infrastructure sidebar refinements.
- **i690:** Operational status strip for EUDs, VEIL, downloads, LAN, and Internet.

Detailed retained release notes are available in [the i690–i699 release-note files](https://github.com/5lyf0x/tak-map/tree/main), along with `CHANGELOG.md` and `docs/RELEASES.md`. Older standalone release-note and validation files have been removed from the current branch; historical changes remain accessible in Git history.

## Installation and upgrade

TAK Map is intended for installation on its supported Linux host using the included installer. For **v1.5.0-i004**, extract the complete release ZIP into a **new** versioned directory:

```bash
cd ~/Downloads
unzip -o tak-map-v1.5.0-i004.zip -d tak-map-v1.5.0-i004
cd tak-map-v1.5.0-i004
sudo ./install.sh
```

Do **not** overlay a previously extracted release directory. Keep the last working release package available for rollback. The installer is intended to retain existing configuration and data in `/var/lib/tak-map`; back up critical data and `/etc/tak-map.env` before upgrades.

**i004 specifically:** If the i003 installation failed because `tak_map_offline_perf_i003.py` was not copied to `/opt/tak-map/`, i004 installs that module as part of the normal installation. No map-pack re-download or map-data reset is required for this fix.

## Configuration and integrations

Integrations are configured independently. Relevant local documentation includes:

- [Gateway Data configuration](docs/GATEWAY-DATA-CONFIG-MODAL.md) for connection and authentication options.
- [Optional Gateway certificates](docs/GATEWAY-DATA-OPTIONAL-CERTIFICATE.md) for Gateway Data versus Replay policies.
- [Replay mode](docs/REPLAY-MODE.md) for recording playback and search.
- [Release history](docs/RELEASES.md) and [changelog](CHANGELOG.md) for previous changes.

Server-hosted preferences are scoped to the authenticated user and the particular TAK Map server; they do not automatically synchronize between independent servers. Routing graphs, elevation packages, GIS downloads, data-provider connections, and VEIL/Gateway services must be supplied or configured separately as needed.

## Known boundaries

- Native NDM-to-Cesium terrain-mesh integration is not claimed as complete.
- Offline basemaps do not make online radar, alerts, tracking services, or remote TAK/Gateway APIs available offline.
- A cross-state road route requires a compatible, connected navigation graph; simply registering multiple separate region packages does not create one.
- Installed behavior and external-data coverage should be checked on the actual TAK Map host; source-side validation is not a substitute for live service verification.

## Version

**TAK Map 1.5.0 — iteration i004**

This README describes the repository's current release and its accumulated user-facing capabilities rather than serving as a per-iteration validation log.
