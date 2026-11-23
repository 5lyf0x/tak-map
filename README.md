# TAK Map v1.5.0-i004 — Offline Performance Installer Hotfix

This maintenance release fixes **the failed backend startup after an i003 installation**. The i003 offline performance module existed in the source archive but the installer did not copy it into `/opt/tak-map/`, resulting in a missing Python module when the service started. The i004 installer installs `tak_map_offline_perf_i003.py` **before** copying the backend and restarting the TAK Map service.

- **Fix:** Deploy the bundled `tak_map_offline_perf_i003.py` with permission `0644` on every full installation or upgrade, including a server that failed during i003 installation.
- **Release identity:** Show `TAK Map 1.5.0 / i004` in the left sidebar and report `1.5.0-i004` in the configuration API and `VERSION` file.
- **Unchanged:** i003's pooled read-only SQLite tile serving, catalog caching, panning and zoom behavior, MBTiles TMS/XYZ support, offline map management and security controls. No re-download, migration or application data reset is required.

### Installation

```bash
cd ~/Downloads
unzip -o tak-map-v1.5.0-i004.zip -d tak-map-v1.5.0-i004
cd tak-map-v1.5.0-i004
sudo ./install.sh
```

Extract to a **fresh versioned source directory**, not over the i003 source folder. The installer preserves `/var/lib/tak-map` and existing configuration. Retain the unchanged i003 archive as the baseline; if i003 failed to start on this host, the previously working i002 archive is the practical rollback release. See `RELEASE_NOTES_I004.md` and `VALIDATION_I004.md`.

---

# TAK Map v1.5.0-i003 — Offline Map Performance

This release improves **offline MBTiles panning, zooming, and tile delivery**. It upgrades the previous complete `v1.5.0-i002` source package in place without changing stored map files, names, IDs or download history. Keep the original `tak-map-v1.5.0-i002.zip` as the rollback package.

### Changes in i003

- **Faster tile serving:** In-memory read-only catalog lookup and a thread-safe SQLite connection pool (3 connections per map, 12 globally by default) replace repeated JSON parsing and open/close operations for every tile.
- **Continuous panning:** Offline tiles request while moving (`updateWhenIdle:false`, 200 ms update interval). Retained tile buffers are reduced to 3 ordinary tiles / 2 custom pixel Blend tiles; online sources retain their prior behavior.
- **Zoom behavior:** The map upscales the highest native downloaded tile level instead of making requests for higher native tiles that the MBTiles file does not contain. Native min/max zoom metadata is retained; upscaled tiles are not additional resolution.
- **Missing areas and cache safety:** Missing tiles now return 404 with private no-store caching, so resumed downloads are not hidden by stale negative cache entries. Successful completed tiles are browser-cacheable privately with a content-generation URL, while active/partial tiles are not cached persistently.
- **TMS / XYZ row handling:** Downloaded packs use standard TMS rows. Imported maps default to standard TMS unless their MBTiles metadata explicitly declares `tms` or `xyz`; imported cards now offer a **Tile rows: TMS / XYZ** selector for safe operator correction. The selection changes catalog metadata only, never the MBTiles file.
- **Multi-layer behavior:** Reuse unchanged layer instances, invalidate changed generations, limit heavy custom pixel-blend work, cancel unloaded custom tiles, and retain saved Blend, Tone, opacity, per-user order and enabled layers.
- **Version/footer:** `VERSION`, API version, bottom-left sidebar, static asset cache IDs, and release documents identify `1.5.0-i003`.

**Preserved:** Offline Maps auto-population, Rename, Apply, Send, Delete, natural alphabetical sorting, the 600px scrolling list, map IDs/filenames and EUD packaging. Server catalog and tile files are never cleaned or rewritten in the tile request path. All tile routes remain authenticated; no online map fallback is introduced.

### Install on the TAK Map Linux host

```bash
cd ~/Downloads
unzip -o tak-map-v1.5.0-i003.zip -d tak-map-v1.5.0-i003
cd tak-map-v1.5.0-i003
sudo ./install.sh
```

Extract into a **new versioned directory**. Do not overlay the source tree for a prior release. The existing `/var/lib/tak-map` data directory is preserved. Restart the browser tab or hard-refresh after installation. See `RELEASE_NOTES_I003.md` and `VALIDATION_I003.md`.

---

## TAK Map v1.5.0-i002 — Offline Maps startup corrections

This is a focused maintenance update to **v1.5.0-i001**. Completed Offline Map Packs now show the **Rename** action alongside Apply, Send, and Delete even when the core map scripts load asynchronously. Saved offline maps are also fetched and rendered on startup—**Refresh Offline Maps** is no longer required merely to populate an existing list. The Rename controls reconnect after relevant startup events and avoid duplicates across subsequent renders.

The bottom-left sidebar continues to show **TAK Map 1.5.0 / i002**. No map data, MBTiles content, identifiers, paths, history, or authentication rules are changed. The existing i001 alphabetical sorting and 600px scrollable map list remain intact.

**Install:** Extract `tak-map-v1.5.0-i002.zip` into a **new** `~/Downloads/tak-map-v1.5.0-i002/` directory and run `sudo ./install.sh` there. Do not overlay older extracted source directories. Keep the original v1.5.0-i001 ZIP unchanged for rollback. See `RELEASE_NOTES_I002.md` and `VALIDATION_I002.md`.

## TAK Map v1.5.0-i001 — Offline Map Packs

The Offline Map Packs list now supports **Rename** for completed downloaded and imported MBTiles maps. Each card offers an inline name editor with **Save**, **Cancel**, **Enter**, and **Escape**, with actionable errors. The list is sorted by **case-insensitive natural alphabetical order** (for example, Map 2 before Map 10), and scrolls inside a **600px maximum-height** viewport without expanding the rest of Offline Maps. Renaming updates the map's catalog display name and the active offline basemap label without changing its stable ID, MBTiles file, actual filename/path, tiles, download/retry state, or history. A previously generated EUD package reference is invalidated so a subsequent Send regenerates the package under the new name; old already-sent packages and embedded MBTiles metadata remain unchanged.

The **bottom-left sidebar footer** now displays **TAK Map 1.5.0 / i001**. Old i621 and i665 identity writers are reconciled with the final release rather than being allowed to revert the footer. Catalog writes no longer silently truncate the saved pack index at 80 records; existing application data remains in place.

Install from a freshly extracted `~/Downloads/tak-map-v1.5.0-i001` directory using `sudo ./install.sh`. Do not extract over an older source directory. Preserve `tak-map-v1.4.0-i699.zip` as rollback. No TAK Map server data migration is required. See `RELEASE_NOTES_I001.md` and `VALIDATION_I001.md` for this release.

## TAK Map v1.4.0-i699 full-source update

Offline Maps now offers a searchable **Download Area** dropdown containing Current View, Draw Area, and all 50 states (California as three county-aligned regions instead of a single statewide entry). Selecting a state or California region displays its boundary outline; downloaded XYZ tiles are clipped to geographic polygons rather than rectangular bounds. Internal jobs automatically partition downloads into batches of at most `TAK_DASH_OFFLINE_DOWNLOAD_MAX_TILES` tiles (250,000 by default) while producing **one unified MBTiles offline map**. The parent map's progress, pause/resume, failed-tile manifest and recovery options remain available. Each failed tile receives its initial attempt plus three retries; on terminal failure, other tiles continue downloading. Incomplete packs display **Retry/Finish**, which retries only missing tiles or accepts the incomplete map while retaining its failure manifest. All configured HTTP(S) XYZ basemaps, including imported Custom XML sources, are available without an application-level provider blacklist; provider usage terms and authentication requirements still apply. The primary action is now **Download**.

Install from a fresh `~/Downloads/tak-map-v1.4.0-i699` extraction using `sudo ./install.sh`. No `~/Downloads/tak` subfolder. Keep v1.4.0-i698 as rollback. Existing offline map files and application data are preserved by the installer. See `RELEASE_NOTES_I699.md` and `VALIDATION_I699.md`. Native NDM-to-Cesium terrain rendering remains a separate pending milestone.

## TAK Map v1.4.0-i697 full-source update

Built from the exact validated v1.4.0-i696 source. Radar history timeline now uses the canonical BASEMAP LAYERS opacity Soft Pill track and thumb, and the default maximum for a single Offline Maps download increases from 20,000 to **250,000 tiles**. The original safety checks, storage format, pause/resume, and concurrency settings remain intact. The download cap remains configurable using `TAK_DASH_OFFLINE_DOWNLOAD_MAX_TILES` in `/etc/tak-map.env`; an existing explicit environment value takes precedence over the new default. Verify bulk downloading is permitted by the chosen tile provider and ensure adequate disk space. See `RELEASE_NOTES_I697.md` and `VALIDATION_I697.md`.

Install from a fresh `~/Downloads/tak-map-v1.4.0-i697` extraction using `sudo ./install.sh`, preserving existing application data and configuration. Retain v1.4.0-i696 as your rollback release.

## TAK Map v1.4.0-i696 full-source update

Includes NOAA historical radar Play/Pause/timeline/LIVE controls, reliable 2D radar handoff, imported basemap synchronization and 2D source warnings, MVUM toolbar recovery, bottom-mounted elevation cursor mileage, persistent-ID Local Data editor fix, full legacy basemap pre-cache removal, and High-only/smoother Local terrain. **Actual NDM terrain geometry remains gated on a real NDM data/datum check.** See `RELEASE_NOTES_I696.md` and `VALIDATION_I696.md`.

Install from a clean `~/Downloads/tak-map-v1.4.0-i696` extraction with `sudo ./install.sh`; do not install over a prior extracted folder. Keep i695 as rollback; application data and environment configurations are retained by the installer.

## TAK Map v1.4.0-i695 update

This source package applies the queued post-i694 interface corrections: repair the existing INFRASTRUCTURE header Show/Hide control, unify all top-level sidebar header typography, migrate radar opacity to the canonical BASEMAP Soft Pill even on existing panels, move Infrastructure object action buttons below GIS attributes, remove obsolete Basemap Pre-cache background prefetching/UI, and apply the selected Extended Divider headings (Manrope 550, 14px, .01em) plus Clear Type layer names (12.5px/750) with inline counts and a 12px gap. See `RELEASE_NOTES_I695.md` and `VALIDATION_I695.md`.

Extract into a fresh `~/Downloads/tak-map-v1.4.0-i695` folder from a ZIP downloaded to `~/Downloads`, then run `sudo ./install.sh`. **Do not** extract over i694. Existing GIS data, layer choices, routes, and saved preferences must be preserved. Retain i694 as rollback until the UI is checked on the live server.

Phase 3 historical radar animation is separately planned and is not implemented in this package because the mandatory live NOAA historical-frame feasibility checks have not been completed.

## TAK Map v1.4.0-i694 update

This release applies the approved staged BASEMAP and Infrastructure user-interface corrections on top of i693, without changing radar APIs or saved map datasets. See `RELEASE_NOTES_I694.md` and `VALIDATION_I694.md`.

Extract into a new `~/Downloads/tak-map-v1.4.0-i694/` directory and run `sudo ./install.sh` from that directory. The archive is intended to be downloaded directly into `~/Downloads`; there is no TAK subfolder. Retain the i693 package for rollback until field validation.

## TAK Map v1.4.0-i693 update

This source release improves radar tile recovery, partial-coverage visibility, and frame selection. See `RELEASE_NOTES_I693.md` and `VALIDATION_I693.md`. Install from a fresh `~/Downloads/tak-map-v1.4.0-i693/` extraction. Preserve all persistent TAK Map data; do not delete or overwrite the previously extracted i692 source.

## TAK Map v1.4.0-i692 update

Same-origin NOAA/NWS MRMS radar tile proxy, provider fallback, bounded memory cache, 2D/3D imagery, and explicit tile/provider diagnostics. Existing i691 NWS weather alerts and browser weather preferences are preserved. See `RELEASE_NOTES_I692.md` and `VALIDATION_I692.md`.

## TAK Map v1.4.0-i691 update

Independent native NOAA nowCOAST MRMS radar and NWS alert overlays in BASEMAP with persisted enable/opacity controls and safe upstream caching. Optional USGS Shaded Relief controls removed; elevation/NDM terrain features remain. See `RELEASE_NOTES_I691.md` and `VALIDATION_I691.md`.

## TAK Map v1.4.0-i690 update

Integrated 28px status strip (EUDs / VEIL / Downloads / LAN / Internet; conditional TAK), authoritative EUD counts, compact stable VEIL dropdown, LAN host-interface health, and compatibility-safe DOM updates. See `RELEASE_NOTES_I690.md` and `VALIDATION_I690.md`.

## TAK Map v1.4.0-i689 update

Infrastructure interaction and static asset reliability: authenticated i684 sidebar JS/CSS routes, themed per-layer minimum-zoom dropdown, validated Leaflet map readiness in Infrastructure and Token Mesh, stable Infrastructure click handling, and Icon Registry point fallbacks/lazy thumbnails. See `RELEASE_NOTES_I689.md` and `VALIDATION_I689.md`.

## TAK Map v1.4.0-i688 update

Offline-only Infrastructure with direct-click red-outline selection, 5px line picking, all GIS attributes visible, TAK Icon Registry point symbols, viewport loading recovery, persistent attribute filters and indexed offline map search. See `RELEASE_NOTES_I688.md` and `VALIDATION_I688.md`. Existing GIS and Local Data are preserved.

## TAK Map v1.4.0-i687 update

See `RELEASE_NOTES_I687.md` and `VALIDATION_I687.md`. Existing infrastructure and Local Data stores remain separate and persistent. The City of Los Angeles Sewer Structures source is available under Water & Wastewater / Online, disabled by default.

## TAK Map v1.4.0-i686 update

Infrastructure Overlays now supports simultaneous Online + Offline display, 1.5× viewport buffers, 5,000 per-layer display budgets, progressively streamed ArcGIS feature pages, user-selected per-layer persistent colors, visible/stored counters, and multi-expand categories. Existing datasets and exports are not truncated. See `RELEASE_NOTES_I686.md` and `VALIDATION_I686.md`.

> **i685:** Infrastructure Overlays with online/offline modes, 14 categories, GIS downloads/import/export, 36-inch sewer filtering, hover details and sidebar collapsed typography fix. See `RELEASE_NOTES_I685.md`.

> **i684:** Reliable route-selection elevation display, clean route-edit cancellation, compact Extended profile, uniform sidebar cards/chips/toggles, and Satellite Tracking above Offline Maps. See `RELEASE_NOTES_I684.md`.

> **i683:** Floating draggable compact/extended elevation profile with route-only visibility, 35°+ steep-run hover details in feet, reliable X close and MVUM rendering/visibility fixes. See `RELEASE_NOTES_I683.md`.

> **i682:** Persist all saved Local Data routes, points and shapes between sessions without silent eviction, truncation or destructive refresh; correct Basemap Blend mode button labels. See `RELEASE_NOTES_I682.md`.

> **i681:** Restore MVUM button reliably; preserve map focal point and scale across 2D/3D; full-route live NDM elevation profile, 20px above map bottom. See `RELEASE_NOTES_I681.md`.

> **i680:** Restore Local Data visibility when enriched API response JSON fails, without modifying saved points or routes. See `RELEASE_NOTES_I680.md`.

# TAK Map v1.4.0-i685

> **i679:** Corrected truncation of long saved-route geometry in canonical JSON and API responses. See `RELEASE_NOTES_I679.md`.

# TAK Map v1.4.0-i679

Regional road overlay, route-input exclusivity and canonical per-layer Blend/Tone controls. See RELEASE_NOTES_I678.md.

# TAK Map v1.4.0-i677

See [i676 release notes](RELEASE_NOTES_I676.md) for complete-route saving with unresolved Valhalla legs, draggable Routing Data Tactical HUD and the routing-mode overlay placement correction.

# TAK Map v1.4.0-i675

See [i675 release notes](RELEASE_NOTES_I675.md) for regional graph selection and route tool improvements.

See [i674 release notes](RELEASE_NOTES_I673.md) for NDM navigation-network MVUM overlay, viewshed elevation integration, route tools, and stacked basemaps.

See [i672 release notes](RELEASE_NOTES_I672.md) for VEIL APRS parity and aircraft rotation corrections.

# TAK Map v1.4.0-i670

See [i670 release notes](RELEASE_NOTES_I670.md) for ADSBx aircraft marker artwork and type matching.

# TAK Map v1.4.0-i669

See [i669 release notes](RELEASE_NOTES_I669.md) for VEIL ADS-B and Range Rings changes.

# TAK Map v1.4.0-i668

## i668 — XTAK VEIL Phase 3, diagnostics, route actions

- Strict canonical emitter matching for VEIL observations from multiple subscribed receivers. Merge verified matching VEIL targets for display while retaining per-node provenance; separate unrelated or ambiguously identified objects.
- Operator-controlled experimental cross-source dedup with native ADS-B and Gateway AIS. **OFF by default**; native layers remain independently controlled.
- Read-only VEIL node health and receiver observations in the existing node Details modal using an active Phase 2 API session. No new login requests, no remote management actions, no raw credentials in browser.
- Compact saved local-route contextual actions: side-by-side **Edit** and **Delete** buttons, with original edit/delete handlers and confirmation intact.
- Preserves i667 Cesium terrain routes/shapes/custom icons, i666 API sync, and i665 blank-page repair. No data migrations or configuration reset.

# TAK Map v1.4.0-i667

## i667 — Terrain routes/shapes, custom icon parity, sidebar route editing

- Cesium Terrain Mode now renders saved/imported/Data Sync routes and shapes in a separate, terrain-aware overlay with original route colors and shape fill/outline styling, including line styles and visibility preferences.
- Selected ATAK custom icons retain their actual Icon Registry image across Leaflet 2D and Cesium 3D, rather than being replaced by generic affiliation symbols.
- Editable saved local routes gain an Edit Route button in the contextual details sidebar, using the existing version-checked route editor.
- Corrected Icon Registry modal grid width, 2D custom-icon priority and saved-route offscreen label suppression from the i666 field repair.
- In terrain view, saved route endpoint name/total labels follow the camera and stay hidden when the endpoint is outside the viewport.
- Preserves i666 VEIL Phase 2, original UDP ingest, token mesh, local data and NWS popup behavior without data migration.

# TAK Map v1.4.0-i666 (previous release)

## i666 — XTAK VEIL Phase 2 and saved-route labels

- Authenticated, operator-opt-in VEIL API sync: snapshot plus WebSocket updates, reconnect/recovery, backend-only credentials. Configured UDP-only nodes do not prompt for authentication.
- Automatic API login modal only if VEIL is enabled, node is explicitly API-subscribed, its API identity is reachable, and reauthentication is confirmed necessary after attempted silent recovery.
- Preserves existing i665 UDP CoT node receiver and node discovery; API pairing does not auto-configure VEIL CoT unicast output.
- Compact VEIL and MESH SYNC collapsible card headers, text-only VEIL LIVE DATA category labels.
- Saved-route endpoint name and total distance visible at zoom 11+, single straight leader line; individual segment distances remain in route create/edit mode.
- Includes confirmed i665 root-DOM/version-only white-screen fix. All active runtime references use i666 cache version.
- VEIL API HTTP and WebSocket traffic on a trusted LAN is **not encrypted**. Only explicitly opted-in remembered credentials are saved as owner-only (0600) on this host.

# TAK Map v1.4.0-i665 (previous release)

## i665 — XTAK VEIL Phase 1 and NWS warning layout

- Adds the XTAK VEIL card between BASEMAP and GEOFENCES, with real multi-node LAN discovery and manual add, persistent node settings, local UDP CoT reception, live map observations and per-service status. Configure each VEIL node CoT UDP unicast to the TAK Map host LAN IP and port 6970 (default); see RELEASE_NOTES_I665.md for limits.
- Condenses NWS warning popups with full-width, independently scrollable Description and map-viewport height limits; removes the Instruction row.
- Synchronizes active release identity/footer to v1.4.0-i665. Existing i664 features and stored data are retained.

## i664 — AIS structured Details and Mesh cosmetics

- Gateway Data → AIS read-only context panel now splits AIS Vessel Name, MMSI, Vessel Type, Watchlist, Speed, Course, Heading, Navigation Status, Observed, Distance, and Source into separate aligned full-width label/value rows under Details; it no longer squeezes all details inside a single narrow value cell.
- MESH SYNC switch now matches the other cards: 38×20, green active track/knob, gray inactive track/knob. Removes the leading status dot. All Mesh controls, placement, status logic and persistence remain unchanged.
- No change to AIS ingest, Gateway authorization or Token Mesh protocol; i663 source ZIP is retained as rollback.

## i663 — MESH SYNC header and readable labels

- Compact Command Slate / Manrope Mesh card keeps title, status chip, network toggle, and collapse arrow together in that order. The arrow is at the far right.
- Collapse only affects card visibility and is saved in the browser; the toggle independently pauses or resumes network traffic without deleting group or Mission journals.
- Increase the tiny Mission/mesh helper, counters, joined status, Mission QR, and empty-state label sizes.
- Retains i662 Mesh backend, Mission creation, and all Gateway/OTS integrations.


## i655 — Route readiness and NDM registration

- Repairs early Leaflet-map initialization that prevented the existing floating-toolbar Route tool from showing its selector; places Manual/Roads at the top right of the map.
- Roads is the default route mode. Displays **Preparing road network…** while routing initializes and a clear unavailable notice if the service cannot start.
- Enables local Valhalla systemd automatic startup with TAK Map **only when an operator-prepared, compatible graph configuration already exists**; does not start a public routing port or delete graph data.
- Background NDM registration detects replaced or newly built ZIP packages (about once per minute), validates their content, and retains earlier entries as history; the NDM Data modal supports safe Unregister for inactive entries and a Show history switch.
- Graph limits remain explicit: the current engine selects one regional graph, so crossing CA/AZ (or other state boundaries) requires a single jointly built, connected multi-state NDM navigation graph. Switching between separate state TAR archives cannot safely guarantee a continuous Valhalla route, and **automatic cross-state routing is not delivered by i655**.
- All existing map data, credentials, configuration, region ZIPs, and rollback i654 source are preserved.

## i654 route creation

- Two modes: Manual and Roads, with 20px live snapping preview on the locally registered NDM Valhalla graph.
- Draggable waypoints, click-to-insert on existing route lines, per-waypoint Manual and Copy Coords menu.
- Live total and per-waypoint distance, explicit failed road connections, and saving all resolved geometry vertices.
- Requires separate local Valhalla 3.6.3 service activation after live host validation; the installer does not activate it automatically.
- Preserves i653 source ZIP as rollback baseline and all installed data/configuration.

## i650 certificate management, AIS icon fallback and live map search

- Restores the **Cert Setup** button alongside Account, with CA status, fingerprint and certificate download; administrator-only certificate generation is gated behind explicit confirmations. Opening Cert Setup never regenerates certificates.
- Gateway AIS retains registry-backed 48×48 MIL-STD-2525C tactical symbols. Unknown/failed vessel SVGs fall back to an existing registered maritime asset containing a visible ship symbol rather than a blank neutral square.
- General map search indexes currently displayed live ADS-B aircraft and Gateway AIS vessels. Searches callsigns, ICAO, registration and owner/operator for aircraft, and name, MMSI, callsign and class for vessels. Selecting a result focuses and opens the existing details panel. Hidden, removed and Replay-suppressed objects are excluded.
- Includes updated runtime assets in installer checks, preserves the working Gateway/Replay settings and prior app data, and retains i649 as the rollback baseline.

## i649 registry-only tactical symbols

- All tactical CoT/SIDC symbols use reviewed MIL-STD-2525C artwork through the TAK icon registry, with existing registered generic symbols for unknown types instead of synthesized line-art X/frame markers.
- AIS vessels use neutral sea-surface MIL-STD icons regardless of reported subtype. Correct parent/generic fallback protects new vessel types and conflicting SIDC metadata while retaining 48×48 map symbols.
- The catalog readiness event refreshes Gateway markers; no unregistered AIS PNG fallback is used for Gateway tactical objects.
- Selected AIS remains red-glowing and selected ADS-B white-glowing; ordinary tactical symbols have no drop shadows. i648 is the rollback baseline.

## i648 MIL-STD-2525C shadows

- AIS vessels with CoT/SIDC metadata continue using the general 48×48 MIL-STD-2525C renderer (not forced into small PNG icons).
- Unselected MIL-STD-2525C markers no longer have drop shadows: removed shared CSS and embedded gray blur effects from 972 SVG symbols. Preserve thin-outline filters and symbol appearance.
- Selected AIS retains a red outer-marker glow; selected ADS-B retains its white highlight. The small native ship PNG remains a fallback for AIS without tactical-symbol metadata.

## i647 map selection highlights and aircraft metadata

- AIS vessels with no tactical metadata use their approved 64×64 ship art at a 12×12 map size. AIS vessels with CoT/SIDC metadata use the 48×48 MIL-STD-2525C renderer. Only selected AIS markers have a red drop shadow; normal AIS markers are shadow-free.
- Selected ADS-B aircraft receive a white drop shadow, cleared when selection closes or changes.
- The ADS-B Identification panel always includes Owner / Operator, displaying Not reported when absent.

## TAK Gateway Data Configure modal

- A **Configure** button appears next to **Refresh** on the Gateway Data card.
- Administrators can set Gateway host/IP, HTTP/HTTPS port, authentication mode, TLS verification and on-host certificate/key paths without editing `/etc/tak-map.env`.
- **Test Connection** checks Gateway Data health and capabilities; **Save** stores an atomic, mode-0600 connection override in TAK Map's persistent data directory.
- HTTP:8090 certificate-free connections are intended for trusted LAN/VPN only; HTTPS:9443 verifies the Gateway server certificate when no client certificate is used.
- The Gateway must independently permit the requested access in Configure Security. Replay, TAK Map account enrollment, Mission/Data Sync, and previous application data are not changed.
- See `docs/GATEWAY-DATA-CONFIG-MODAL.md` for details.

## i644 optional TAK Gateway client certificates + Replay compatibility

- Gateway Data now supports `auto` (default), `none`, and `certificate` authentication modes, independently from Replay.
- Certificate-free Gateway Data can use trusted LAN/VPN HTTP:8090 or HTTPS:9443 with strict server-certificate verification.
- Replay remains HTTPS:9443 and defaults to certificate mode. Opt-in certificate-free Replay retains the same Replay period IDs, search, manifest, events, state, compressed chunk payloads, and browser session authentication.
- Certificate-authenticated enrollment remains supported, and upgrades preserve `/etc/tak-map.env`, credentials, current data, and existing OpenTAKServer CoT/Mission/Data Sync behavior.
- See `docs/GATEWAY-DATA-OPTIONAL-CERTIFICATE.md` and `docs/REPLAY-MODE.md` for operator configuration.
- Retains all validated i643 native Mission Shape Save behavior unchanged.

## i656 lossless snapped-route saving

The Route editor now saves the entire resolved road geometry instead of only the anchor waypoints. Existing i655 routing and NDM behavior remains unchanged.

## i657 saved route geometry

The existing Save Route dialog now delegates to the Roads editor so snapped road curves, waypoint metadata, and dialog fields are stored together.

## i658 route creation

Roads mode previews connected road segments before placing waypoints, saves full snapped geometry and displays each leg distance on the map. The single Save Route dialog implementation is shared by inline and deferred runtimes.

## Installation

```bash
cd ~/Downloads
unzip -o tak-map-v1.4.0-i663.zip -d tak-map-v1.4.0-i663
cd tak-map-v1.4.0-i663
sudo ./install.sh
```

## i643 validated native Mission Shape Save

i643 replaces the failed i642 Mission `/cot` write assumption with the exact native TAK Shape workflow proven live against OpenTAKServer 1.7.13.

- Edited Shapes remain their original native TAK drawing CoT objects (`u-d-*`; for example rectangles remain `u-d-r`) with the same Shape UID. They are never converted into an EUD/self-position event or a generic center point.
- The edited native Shape is transmitted over TAK Map's authenticated per-user certificate SSL CoT connection.
- Save then verifies the edited geometry globally through `GET /Marti/api/cot/xml/<uid>/all`; historical same-UID rows are not sufficient.
- After native CoT ingest is confirmed, the same UID is associated/refreshed in each existing Mission with `PUT /Marti/api/missions/<mission>/contents` and JSON `{"uids":["<shape uid>"]}`.
- Mission `/cot` is GET/read-back only. i643 forbids Shape publication through POST/PUT Mission `/cot`.
- Save exits Edit mode only after every Mission returns the same UID, same native `u-d-*` type, and matching edited geometry.
- Rectangle/polygon geometry comparison remains independent of cyclic starting vertex and winding direction.
- Failed transport, global ingest, Mission association, or Mission read-back leaves Edit mode active with the draft intact and returns the exact failed stage.
- The i641/i642 editor UX remains: in-place fields, draggable type-aware vectors, edit-only center translation handle, dynamic map-side segment dimensions, Notes last, half-width Save/Cancel, empty-map clicks preserve editing, and silver/gray TAK Map controls.

OpenTAKServer 1.7.13 deployments must retain the Mission-delete patch v3 used by the current server-authoritative Mission deletion contract.



### Certificate setup control (staged for next iteration)

The TAK Map header will expose **Cert Setup** beside Account. Its default actions display the current HTTPS/CA status and let a signed-in user download `/ca-cert.crt`. Verify the fingerprint shown in TAK Map against the certificate on the trusted Linux server before importing the CA into Windows' trusted-root store. A separate advanced action allows an administrator to explicitly generate or regenerate certificates, with required confirmation; simply opening the window never changes certificates.

The Cert Setup workflow is for the browser-to-TAK-Map HTTPS certificate and is independent of Gateway Data client-certificate authentication. Chrome's `ERR_CERT_AUTHORITY_INVALID` is not resolved merely by adding the button; the correct CA must be trusted and the server certificate must cover the URL's hostname/IP.

### General map search (next staged iteration)

The general map search includes currently displayed live ADS-B aircraft and Gateway AIS vessel markers. Search by aircraft callsign, ICAO hex, registration or owner/operator, and by vessel name, MMSI, callsign or class. Selecting a result centers the map and opens the existing details panel. Objects hidden by source toggles, removed from live marker layers, or suppressed during Replay are not indexed. The separate Mission/Data Sync search remains unchanged.
