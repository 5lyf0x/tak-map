# TAK Map i652 staging — NDM Data in Tools

Status: **released i652; install on Linux server to use**. i651 remains the rollback baseline.

## Access

The existing map sidebar **Tools** card now shows **NDM Data** immediately following **Add Elevation Data** and before **Export All Data**. The existing browser-local elevation import dialog remains untouched.

The new NDM Data modal supports:

- **Existing on Server**: discover NDM navigation and terrain ZIPs under the already configured read-only NDM roots (by default `/var/lib/takrig-routing/ready/` and `/var/lib/takrig-routing/terrain/ready/`). Choose **Register** for each. This calls the existing `POST /api/tak-map/ndm/register-existing` with the server-issued discovery ID and never copies or alters the original ZIP.
- **Upload ZIP**: select an NDM routing or terrain ZIP from the browser and explicitly press **Import ZIP**. The UI posts the raw ZIP using `Content-Type: application/zip` to `POST /api/tak-map/ndm/import`. Upload progress is shown. The backend validates archive members, package manifests, Valhalla graph tiles or terrain SQLite grids, and ZIP integrity before catalog registration. Defaults to a 1.5 GiB backend upload limit; for larger already-present NDM ZIPs, **Existing on Server** avoids transfers and the upload quota.
- **Registered datasets**: lists persisted datasets, availability, source ownership (read-only NDM vs TAK Map import), type, region and file size.
- **Refresh datasets**: rescans source directories and fetches current catalog.

The UI depends only on the existing i651 APIs. Mutation requires login, administrator permission and same-origin enforcement; a signed-in nonadministrator sees a clear access warning and cannot register or upload. It does not request activation, graph preparation, or routing and cannot start Valhalla. Imported datasets remain available after service restart through the i651 catalog.

## Source integration

- `assets/tak-map-ndm-data-i652.js`: accessible modal, tabs, catalog and discovery views, raw ZIP XHR progress, safely escaped filenames and API failures.
- `tak_dashboard.py`: injects NDM Data button in the **effective** Tools-card HTML, loads the script, serves it from `/assets/runtime/tak-map-ndm-data-i652.js`.
- `install.sh`: installs asset and verifies file presence and runtime route on startup.
- `scripts/test_ndm_tools_modal_i652_browser.py`: browser tests covering in-card placement, existing registration, ZIP upload, permission handling, Escape closure and no route activation.
- `scripts/test_ndm_tools_modal_i652_backend.py`: effective runtime HTML, asset GET/HEAD, install and runtime gate checks.

## Live verification after future install

Sign in as a TAK Map administrator; open **Tools → NDM Data**; verify 14 available ZIPs (seven navigation and seven terrain for the currently installed states), register Utah routing and terrain, then refresh and verify both appear as available. Reopen the modal and restart TAK Map to confirm persistence. Do not start Valhalla until its separate controlled route smoke test.

The installed server has not been modified in this staging task. Full i652 source ZIP is the release deliverable.

## Next i653 registration / upload policy (staged)
- `Existing on Server` is read-only and has no ZIP file-size quota, including the large California navigation and terrain packages. The archive must still pass integrity/schema and bounded expansion checks.
- Browser `Upload ZIP` maximum is 4096 MiB (4 GiB); Nginx permits this **only** at `/api/tak-map/ndm/import`. The modal reads the cap from the authenticated catalog API.
