# TAK Map i653 — NDM Existing Registration and Upload Limits (Staged)

**Status:** Released source correction in i653 (live server installation not yet verified).

## Failure mechanism

In i652, `Catalog.register_existing()` called `_register()` then `inspect_zip()`; `inspect_zip()` rejected any existing NDM ZIP exceeding `MAX_ZIP_BYTES`, the same quota used for browser uploads (default 1536 MiB). This incorrectly rejected California's large NDM navigation archive without uploading a byte. The old combined message (`ZIP missing or exceeds import quota`) also hid whether file discovery, permissions, or size caused failure. The separate inflated ZIP maximum (3200 MiB) and 5,000-member count could also reject larger state packages even without an upload.

## i653 policy and implementation

- `Existing on Server`: no **compressed ZIP file-size** cap; only registered NDM discovery tokens from configured roots are accepted. ZIPs are inspected and SHA-256 hashed in place, then cataloged without copying/moving/extracting them. Preserves NDM ownership, original file modification times, and the operator-gated Valhalla service.
- Browser `Upload ZIP`: hard ceiling 4 GiB (4096 MiB), matching Python backend `TAK_MAP_NDM_MAX_UPLOAD_MB` default/maximum, the modal client preflight and the Nginx **exact** import location `client_max_body_size 4096M`. API `GET /api/tak-map/ndm/catalog` supplies `max_upload_bytes` so the modal honors locally configured smaller limits.
- General site upload maximum remains 400M; HTTPS certificate configuration, Gateway/Replay and Valhalla activation are unchanged.
- Archived data security limits remain: no symlinks, traversal, duplicate paths or TAR special entries; ZIP CRC, manifest schema, SQLite grid integrity and routing graph validation. Broader safe bounds of 100,000 ZIP entries and 64 GiB *expanded member data* accommodate large NDM state packages; these are integrity/resource safeguards, **not an existing-file upload quota**.
- Uploaded ZIPs must pass free-disk checks before streaming and again before expansion and source-copy promotion. The browser's previous fixed 30-minute upload timer is removed for up-to-4-GiB transfers.
- Existing-file errors distinguish missing or inaccessible ZIPs from upload size problems. If a California terrain archive fails for another reason (e.g. actual schema or permissions), the backend will present that reason instead of attributing it to the upload quota.
- Versioned i653 script query for immutable browser caches: `/assets/runtime/tak-map-ndm-data-i652.js?v=1.4.0-i653` so the updated UI is fetched after upgrade; the old i652 DOM IDs and global entrypoint remain compatible.

## Validation

- Controlled synthetic valid sparse ZIP **greater than 5 GiB** registers via `Catalog.register_existing()` without copying; same-size browser uploads are rejected by quota before reading.
- 4 GiB exact accepted by size-policy check, 4 GiB + 1 byte rejected; small ZIP still uploads and registers.
- California-scale 5,050-plus ZIP members pass the revised validator; directory/ZIP integrity checks remain covered by inherited tests.
- Chromium: accepts simulated 3 GiB upload, refuses >4 GiB, does not time out at 30 minutes, and lists a 5 GiB package for on-server registration.
- Both real uploaded Utah ZIPs still pass full routing and terrain validator; isolated Nginx `nginx -t` accepts the 4096M location override.
- Live California navigation and terrain packages are **not mounted in this environment**. After building and installing i653, repeat their registration and inspect any remaining format-specific error.

**Never change** the existing release i652 ZIP or TAK Map/NDM live data as part of staging.
