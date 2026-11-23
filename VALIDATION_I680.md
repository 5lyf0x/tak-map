# TAK Map v1.4.0-i680 — Validation record

## User incident
- i679 on Ubuntu returns HTTP 500 from `GET /api/tak-map/imported`: `JSON response serialization failed: maximum recursion depth exceeded`.
- User verified disk `/var/lib/tak-map/tak_map_imports/imports.json`: valid JSON, 30 import records, 24 points, 6 routes, max nesting depth 6. A separate data backup exists at `/root/tak-map-recovery-i679/tak_map_imports/`.
- This release avoids any changes to that stored data and preserves full route geometry.

## Implementation
- Maintain the normal enriched API response path when serializable. If an import GET response fails to serialize, safely read canonical `imports.json` into a new Python object, compute route edit revision hashes in memory where IDs exist, and serve all import records and coordinates, reporting `local_data_recovery_i680` and an `X-TAK-Map-Local-Data-Fallback` response header.
- Never turn a missing, unreadable, or invalid canonical file into an empty success response. No migration/write/delete/reimport performed by recovery.
- Guard uninitialized basemap Tone state for newly registered layers; no old slider code is reintroduced.
- Preserve full-fidelity i679 `atomic_write_json()` and route API serializer (no 1,000-element cutoff), and retain live error diagnostics.

## Verified in isolated build
- i680 recovery: 5 focused tests passed, including synthetic recursion failure -> 30 recovered imports, 24 points, 6 routes, 5,001-vertex route parity and unchanged source bytes; normal complete response; invalid canonical file returns 500; unrelated endpoint unaffected.
- i679 full route persistence: 5 tests passed (including >50,000 vertices and long-route editing).
- i679 startup and damage audit: 2 tests passed.
- Python source compiled; basemap JavaScript syntax (`node --check`) and installer/uninstaller syntax (`bash -n`) passed.
- Package ZIP integrity and full clean extraction SHA-256 comparison performed at package handoff.

## Not verified
- Real 30-record user file and logged-in browser on the user's Ubuntu server are not available in this build environment. Actual post-install Local Data visibility remains to be checked on that host.
- Actual ESRI/USGS tile service errors (HTTP 502) shown in the browser console are unrelated and not addressed here.

## Safety
- i679 source/package are preserved as rollback sources; i680 doesn't roll back application or restore/overwrite saved imports.
