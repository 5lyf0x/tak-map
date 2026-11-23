# TAK Map v1.4.0-i679 — Validation record

## Purpose
Correct canonical JSON truncation of long route geometry in i678, including both disk persistence and API read-back. No change to routing calculations, snapping, or route save verification.

## Automated checks performed (isolated workspace)
- **7 new release tests passed:** 1001-, 5000-, 20000-, 50001-vertex POST -> disk -> GET parity; long route edit (21010 -> 32005 vertices), reopen and revision change; 20000-vertex HTTP response with correct Content-Length; circular write refusal preserves existing data; legacy truncated imports preserved on next write; read-only audit detects damaged records without modifying them; blocking server startup remains after all release registrations.
- **Inherited route backend:** i659 saved-route in-place update, stale-revision safety, original point preservation — passed.
- **Inherited import:** i677 duplicate-filename import handler — passed.
- **Inherited browser:** i676 13-waypoint mixed-route save, edit and full read-back; i677 duplicate-filename read-back; i677 basemap opacity/reorder — passed.
- **Inherited graph activation:** i675 switch and rollback (4 tests) and HTTP activation — passed.
- **Inherited road snap:** i654 (6 tests) — passed.
- **Live process:** entrypoint script booted a local ephemeral HTTP server; unauthenticated road-index endpoint returned HTTP 401 as expected (no authentication bypass). The i679 import/POST/GET geometry tests used the real server functions and HTTP serializer with in-memory handlers.
- Python compilation, installer/uninstaller bash syntax, and relevant runtime JavaScript syntax — passed.

## Regression prevention
- Canonical `atomic_write_json` and `Handler._send_json` use `json_complete_dumps`; neither truncates nested arrays. The original `json_safe()` remains deliberately confined to compact diagnostics and other noncanonical excerpts.
- In-place route edit capacity is bounded at 32 MiB and 200,000 vertices, with existing coordinate validation and revision checks retained.
- Optional `tak_map_import_geometry_audit_i679.py` reads existing Local Data only; no automatic repair/deletion/migration is performed.
- The i678 release had an early blocking `main()` guard. i679 moves service startup to the file's end so all late handlers and version registration are effective under the real systemd ExecStart.
- Existing i678 source ZIP remains unmodified for rollback.

## Not verified
- Actual install/upgrade on the user's Ubuntu host and its real ~376-mile route, because server access and browser session state aren't available here.
- Any records already damaged in i678 are not reconstructible from their truncated disk representation alone. The source or separate untruncated backup is required.

## Archive
Source ZIP CRC, SHA-256 manifest parity, fresh unzip extraction comparison, executable installer permissions and no private key/certificate bundles will be verified for final handoff.
