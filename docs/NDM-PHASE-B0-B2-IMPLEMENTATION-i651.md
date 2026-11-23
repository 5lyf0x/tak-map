# TAK Map i651 — Phase B0–B2 implementation and verification

**Source-only staging, November 5, 2026.** Current released TAK Map `v1.4.0-i650` remains unchanged. This work does **not** activate Valhalla, create route geometry, import browser elevation, or build an i651 package.

## Implemented

- `ndm_packages_i651.py`: bounded, fail-closed format validators for `takrig.valhalla.region.v1` (Valhalla **3.6.3**) and `takrig.terrain.region.v1` (`takrig.terrain.sqlite.v1`). Explicit rejection of unsupported versions, unsafe ZIP/TAR paths, symlinks, duplicate names, encrypted members, oversized uploads, missing graph tiles, mismatched coverage indexes, SQLite corruption, wrong tile inventories, malformed zlib grids and invalid resolution metadata. Uses streaming reads and bounded grid decompression.
- Dataset catalog in `/var/lib/tak-map/ndm/catalog.json` or configured `TAK_MAP_NDM_DATA_DIR`, written atomically with restrictive permissions. Content-addressed dataset identifiers use the full SHA-256 of the source ZIP. Catalog entries distinguish `tak-map-import` and `ndm-external` ownership; external file paths remain private; datasets are not automatically activated. Dataset status becomes `unavailable` if the external file is moved or its size/mtime changes.
- Admin-only external discovery and registration restricted to fixed NDM roots. Defaults: `/var/lib/takrig-routing/ready` and `/var/lib/takrig-routing/terrain/ready`, plus only one nested directory. The client passes a discovery identifier, **never a filesystem path or URL**. Registration validates the entire source archive, including TAR/SQLite checks, and does not mutate NDM files.
- Admin-only raw ZIP import streamed to a random, TAK Map-owned quarantine path with disk preflight, file/member/expansion quotas, CRC validation, schema checks, immutable content-addressed storage, and atomic catalog commit. Failed/truncated imports remove quarantine data and do not appear in the catalog. If a prior power failure leaves a complete matching import folder but no catalog entry, the content can be safely reattached after SHA-256 verification. Imported source ZIPs are preserved with extracted contents for future B3/D adapters.
- Unregister detaches a catalog item without deleting files, including TAK Map-owned imports. There is intentionally no remote filesystem deletion API. Routing activation always fails closed until Phase A server-runtime measurements and Phase B3 tests pass.
- Installer places the `ndm_packages_i651.py` backend beside `tak_dashboard.py` and creates persistent NDM folders without recursive chown/deletion of existing catalog/imports. Nginx grants a larger (1536M) body only to `/api/tak-map/ndm/import`; existing 400M size limit remains for other locations. Body streaming avoids Nginx buffering an additional ZIP before forwarding.

## HTTP API contract (staged, not yet installed)

All endpoints require a TAK Map authenticated session; mutations require an administrator **and** same-origin `Origin` matching the public `Host` (including port). Missing/invalid origins fail closed.

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/tak-map/ndm/catalog` | Public-safe dataset metadata; no host file paths |
| GET | `/api/tak-map/ndm/status` | B0–B2 readiness; `router_state=disabled-phase-b3` |
| GET | `/api/tak-map/ndm/discover` | Admin-only list of allowlisted external package IDs |
| POST | `/api/tak-map/ndm/register-existing` | Admin same-origin `application/json` with `{ "discovery_id": "..." }` |
| POST | `/api/tak-map/ndm/import` | Admin same-origin **raw** `application/zip` stream with `Content-Length`; not `multipart/form-data` |
| POST | `/api/tak-map/ndm/activate` | `409 ACTIVATION_DISABLED` until B3 gate is met |
| DELETE | `/api/tak-map/ndm/datasets/{sha256}` | Admin same-origin detach; **files preserved** |

The browser elevation-import UI is intentionally unchanged; Phase D will add NDM selection to the existing modal. Route mode controls and snapping are Phase C. Neither capability is presented as live in B0–B2.

## Storage, upgrade and resource notes

- Defaults to `/var/lib/tak-map/ndm/{catalog.json,staging,imports}` under the existing persistent data directory.
- `TAK_MAP_NDM_EXISTING_ROOTS` accepts colon-separated administrator-configured **allowlisted directories**. Files in NDM-owned roots are **read-only**.
- `TAK_MAP_NDM_MAX_UPLOAD_MB` defaults to 1536 MiB, capped at 2048 MiB. Nginx's narrow 1536M cap must not be expanded globally. Source ZIPs and extracted contents can require roughly double the dataset size; quarantine and verification add temporary disk use. Preflight also reserves space.
- B2 keeps both extracted files and source ZIPs to support validation, rollback and future services. No auto-deletion of existing files on upgrade or uninstall.
- Routing graph describes only source features marked `applied_to_graph`; its off-road graph does **not** establish MVUM/BLM motorized travel legality.
- Terrain `vertical_datum=unknown` until the exact export provenance is verified. No fabricated datum is published.

## Validation results

| Test | Result |
|---|---|
| Real Utah Valhalla 3.6.3 ZIP, SHA-256 `393d3dff...` | Valid; 495 `.gph` graph tiles and 1,007 coverage tiles |
| Real Utah terrain ZIP, SHA-256 `824c6567...` | Valid; 119 native tiles and 357 overviews; all compressed grid sizes checked |
| Real Utah B2 import, dedicated isolated data directory | Both ZIPs imported, catalog persisted, extracted members and source ZIPs present, temp staging empty |
| Controlled validator/catalog/negative tests | 16 passed |
| Actual TAK Map handler auth/origin/import/status/delete tests | 4 passed |
| Python and installer shell syntax checks | Passed |

Full inherited TAK Map regression suite, live Nginx on target OS, live Valhalla routing, actual server disk/RAM/latency and existing-NDM root permissions **have not been tested** here. Those gates remain for B3/B4 and before any release or production enablement.
