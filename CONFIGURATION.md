## i693 native weather radar

The existing BASEMAP weather card uses the same saved browser preference key (`tak-map-native-weather-i691`). i693 adds a fixed-origin authenticated radar tile proxy and displays per-viewport coverage diagnostics. No user-supplied remote radar URL or new secret is required. See `RELEASE_NOTES_I693.md` for API and operational smoke checks.

## i690 status strip configuration

`TAK_MAP_LAN_INTERFACE` optionally selects a LAN interface if the host uses a nonstandard name. The LAN status endpoint reports a usable host private IPv4 link, not proven peer communication. `TAK_MAP_STATUS_TAK_CONFIGURED=1` optionally flags a custom OpenTAKServer config location when `opentakserver.service` is already enabled; the indicator remains hidden if the service is disabled. Status JS/CSS are explicitly deployed under `/opt/tak-map/assets/`. Existing data and database paths are unchanged.

## i689 Runtime assets and map readiness

TAK Map serves `/assets/runtime/tak-map-sidebar-order-i684.js`, `/assets/runtime/tak-map-sidebar-uniform-i684.css`, `/assets/runtime/tak-map-infrastructure-i689.js`, and the matching i689 CSS through explicit authenticated routes with correct MIME. Browser map consumers wait for a validated Leaflet map rather than assuming `window.map` is not an HTML element. No new environment variables or Infrastructure database migration.

## Infrastructure i688 — Offline-only configuration

`TAK_MAP_INFRA_DIR` (default `/var/lib/tak-map/infrastructure`) continues to store complete downloaded and imported GIS datasets. i688 makes an additive SQLite upgrade: `filter_spec`, `point_symbol_mode`, and `point_symbol_ref` columns on layers plus a derived `infra_fts_i688` search index. Historic online provider configurations remain stored but cannot stream into the map; authorized downloads require explicit user initiation. The offline renderer uses viewport +50%, max 5,000 displayed features per layer, per-layer minimum zoom and persistent filters. No new required environment variables or network services are introduced.

## Infrastructure i687

`TAK_MAP_INFRA_DIR` (default `/var/lib/tak-map/infrastructure`) retains downloaded GIS data and catalog state; the release adds `hidden_online`, `hidden_offline` and `min_zoom` columns without destructive migration. Online service count queries are optional; when unsupported, the map falls back to bounded provider paging.

# TAK Map i640 Shape editor configuration

No new operator configuration is required.

Shape editing uses the existing TAK Map / OpenTAKServer connection and authenticated Data Sync path. Mission-backed Shape saves remain server-authoritative: the existing UID and native TAK CoT shape type are preserved, and edited CoT is sent back to TAK Server without changing Mission membership.

During Edit mode TAK Map maintains one authoritative draft geometry for the selected Shape. Map geometry, vector handles, dynamic segment-distance labels, Center/Area/Perimeter values, and the Save payload all use this draft. Periodic Data Sync/background redraws are not allowed to replace the draft until Save or Cancel.

The Shape panel:

- labels the representative coordinate as **Center**;
- does not show Category, Width, Height, or Rotation rows;
- uses normal font weight for the Shape name;
- has no Close Edit button;
- uses equal-width Save and Cancel controls, with Delete Shape separately below;
- uses the TAK Map silver/gray visual theme for all Shape controls.

While Shape Edit is active, type-appropriate draggable vector handles are drawn on the map. Segment/dimension labels are shown only when the current zoom provides enough screen space. Distance and area formatting follows the browser/computer regional measurement system.

For OpenTAKServer 1.7.13, keep `ots-1.7.13-mission-delete-patch-v3` installed for the existing final-Mission-membership deletion behavior.

## TAK Gateway Data configuration (i645)

Sign in to TAK Map as administrator, open **Gateway Data → Configure**, select Gateway hostname/IP, protocol and port, and choose client authentication. Test Connection checks Gateway Data `health` and `capabilities` endpoints. Save writes `gateway_data_connection.json` in the TAK Map persistent data directory (normally `/var/lib/tak-map`) and reloads ingestion. This file overrides Gateway Data environment settings only; Replay remains independent. Certificate-free HTTP should only be used on a trusted LAN/VPN; certificate-free HTTPS requires Gateway server TLS verification. The Gateway must allow access in its own Configure Security settings.

## Staged NDM Data Tools modal (i652, not released)

The map Tools card uses the existing i651 NDM catalog and admin endpoints. Existing server files come from `TAK_MAP_NDM_EXISTING_ROOTS` (defaults to the NDM navigation and terrain ready directories). Uploaded ZIPs use `TAK_MAP_NDM_MAX_UPLOAD_MB` (default and maximum 4096 MiB, or 4 GiB); only the NDM upload API has a matching Nginx `client_max_body_size 4096M`. Existing NDM server-side ZIP registration has **no compressed file-size quota** and does not copy the original. Archive security and bounded decompression checks still apply. No dataset or routing service is activated by import or registration.

## Infrastructure Overlays (i685)

Persistent geospatial working data is stored at `/var/lib/tak-map/infrastructure/` (owned by the `takmap` service account). The optional server-side `TAK_MAP_INFRA_DIR` environment variable may relocate it to a writable persistent filesystem; keep its contents and permissions across upgrades. GIS import/export requires system Python `fiona` and `pyproj` (the i685 installer checks/installs these packages before modifying the live app). Online providers must use approved public HTTPS ArcGIS FeatureServer or MapServer layer URLs.

## Infrastructure Overlays i686

The persistent store remains `/var/lib/tak-map/infrastructure`, or `TAK_MAP_INFRA_DIR` if configured. The online and offline master display switches, i686 category open-state set, management tab, and prior sewer threshold are browser preferences. Per-layer `color` is saved in the infrastructure database after additive i685-to-i686 migration. Automatic viewport feature display is capped at 5,000 features per layer and queried within viewport plus 50% width/height (25% on each side). Manual download jobs retain their explicitly selected area and have no TAK Map speed cap.
