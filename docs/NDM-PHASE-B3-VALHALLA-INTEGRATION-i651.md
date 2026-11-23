# TAK Map i651 — NDM B0–B3 validation and operator testing

**Purpose:** Backend integration checkpoint. This release does not expose route-snapping controls in the map editor or add NDM elevation to the existing elevation modal. Those remain Phases C and D.

## Release components

- `ndm_packages_i651.py`: checks registered NDM Utah-compatible navigation/terrain ZIPs, creates a persistent content-addressed catalog and supports admin-only raw ZIP import and read-only discovery of existing NDM packages. Uploaded copies live under `/var/lib/tak-map/ndm/imports`; external NDM packages are never changed by TAK Map. Unregister never deletes files.
- `ndm_valhalla_i651.py`: selects a registered routing dataset, verifies graph ZIP SHA-256 and graph TAR integrity, prepares a sanitized Valhalla 3.6.3 config under `/var/lib/tak-map/ndm/prepared`, and delegates bounded route requests only to localhost on `127.0.0.1:18882`. Road and off-road modes share Valhalla auto costing; the latter supplies `use_tracks: 1.0` but **does not establish a legally accessible 4WD route**. Failed routing never fabricates straight-line geometry.
- `scripts/install-valhalla-i651.py`: runs early in `install.sh`; downloads an official pinned-hash native Linux x86-64 or ARM64 `pyvalhalla` 3.6.3 wheel from PyPI, extracts the complete wheel including bundled shared libraries into `/opt/tak-map/vendor/valhalla-3.6.3/`, validates the executable version, and leaves system Python/system Valhalla untouched. Internet access to PyPI is needed for a first install. Unsupported CPU/OS or failed checksum aborts installation **before** replacing the existing TAK Map app.
- `tak-map-valhalla.service`: installed as a dedicated systemd service and **disabled by default**. Do not start it until the Utah graph has been prepared, the active configuration deliberately selected, and host RAM/CPU/latency safety tests performed. This initial release refuses remote activation (`409 ACTIVATION_OPERATOR_GATED`).

## Native wheel identity

Pinned `pyvalhalla` **3.6.3** built distributions for Linux glibc 2.28+:

- x86-64: `e123720983ce570f340c3ef78289098bf647deba68d56143571384a5aa874868`
- ARM64: `b3e60b2b474c9e27e3303b964d54603a249ca952ae5100e3a8d361107d1c329d`

Source: https://pypi.org/project/pyvalhalla/3.6.3/ and https://valhalla.github.io/valhalla/start/installation/

**Runtime uncertainty:** Only controlled installer fixtures were available here; the native upstream wheel could not be downloaded/executed in this working container. Installation and live graph routing must be verified on the target Linux server. If the first native runtime check fails, the installer stops rather than silently substituting a different Valhalla version.

## Authenticated API

| Endpoint | Permission | Behavior |
|---|---|---|
| `GET /api/tak-map/ndm/catalog` | Authenticated session | Public-safe dataset descriptors (no filesystem paths) |
| `GET /api/tak-map/ndm/status` | Authenticated session | Native binary/service readiness and dataset count |
| `GET /api/tak-map/ndm/discover` | Administrator | Opaque IDs of files under approved NDM roots |
| `POST /api/tak-map/ndm/register-existing` | Admin + same-origin | JSON `discovery_id`; external ZIP never modified |
| `POST /api/tak-map/ndm/import` | Admin + same-origin | Raw `application/zip` with Content-Length; quarantined validated upload |
| `POST /api/tak-map/ndm/prepare` | Admin + same-origin | JSON `dataset_id`; generates verified graph/config only |
| `POST /api/tak-map/ndm/activate` | Admin + same-origin | Returns 409 until live server safety gate; no remote service starts |
| `POST /api/tak-map/routing/resolve` | Authenticated + same-origin | JSON `locations:[{lat,lon},...]`, `mode:roads\|offroad`; requires a running local router |
| `DELETE /api/tak-map/ndm/datasets/<sha256>` | Admin + same-origin | Detaches only, never deletes source files |

All 5xx errors and service-down statuses must be investigated before enabling the service. Nginx raises upload size only for exact `/api/tak-map/ndm/import`; ordinary TAK Map remains limited to 400M.

## Utah Phase A/B validation

Observed on original ZIPs supplied by the user:

| Dataset | SHA-256 | Validation |
|---|---|---|
| Utah routing | `393d3dff0bf22500a3d8298474b0fab29265ad4645b267bd939a46296bf5e301` | 495 `.gph` graph tiles and 1007 coverage tiles |
| Utah terrain | `824c6567467f97a30e0aefcfec35d443104a8d3d08ee51fdac81ccfaf3103a74` | 119 native elevation grids + 357 overviews; database/schema checks |

The both ZIPs imported successfully to an isolated catalog. Graph preparation verified an unpacked **308,961,280-byte** TAR and generated `127.0.0.1:18882` config with no NDM build-path references.

## Live-server test gates before Valhalla activation

1. Verify architecture, free RAM and disk; verify downloaded executable reports **3.6.3**. Do not assume 32-bit ARM builds work.
2. Register existing Utah NDM ZIPs where possible, or import a copy into TAK Map's managed catalog. Inspect storage pressure after import.
3. Prepare Utah graph; explicitly select the reviewed configuration for the service (the API currently prepares but does not auto-start it; use the local `ndm_ctl_i651.py --select-for-live-test <SHA256> --confirm I-UNDERSTAND-LIVE-TEST` command to stage active config).
4. Measure Valhalla cold startup/RSS, disk, CPU; prove a paved Salt Lake City route and an off-road Moab track route from the original coverage. Confirm connected geometry, snapped endpoints and no-route errors.
5. Check Gateway Data, Replay, Missions, map icons/search, local elevation, and restart/rollback preservation. Leave the routing service disabled if resource budget or graph version cannot be confirmed.

**Datum:** NDM Utah terrain ZIP has no explicit vertical datum; this release deliberately keeps `vertical_datum=unknown` and does not yet sample terrain.
