# TAK Map v324

- Release label remains `v1.1.0`; iteration marker is `v324`.
- Hardens rendered iteration display so active runtime patch constants report v324 instead of older patch numbers.
- Adds `/api/tak-map/import` GET alias behavior for TAK Map local imports under TAK Map session auth.
- Preserves the v323 Viewshed wrapper-recursion fix.
- Fixes ADS-B Option C aircraft popup spacing while preserving the current working X close button.
- Preserves approved ADS-B tracking distance label styling.
- Strengthens Data Sync and Local Data popup Edit/Edit Data button sizing so edit controls stay content-width.
- Prunes stale Local Data selection/hidden state against actual current local IDs to reduce shape/list state drift.

# TAK Map v323

- Release label remains `v1.1.0`; iteration marker is `v323`.
- Replaces the recursive Viewshed wrapper chain with a direct owner toggle path and rebinds the toolbar button so the Viewshed module opens without stack overflow.
- Applies Option C / Data Sheet Pro styling to ADS-B aircraft info popups while keeping aircraft map labels unchanged.
- Corrects ADS-B aircraft popup field layout so Speed and Model are separate adjacent fields, with Altitude and Heading paired together.
- Fixes view popup Edit button width so it only spans its text/content.
- Formats Added timestamps in point/route/shape popups to local browser date/time with 24-hour hours and minutes only.
- Adjusts the ADS-B status-bar dropdown to auto-size to displayed data and avoid the normal horizontal scrollbar.

# TAK Map v322

- Release label remains `v1.1.0`; iteration marker is `v322`.
- Locks in the current ADS-B aircraft label design while adjusting aircraft info popup layout to show Speed / Model and pair Heading with Altitude.
- Fixes ADS-B track distance label background width so it spans the full text.
- Reapplies Option C / Data Sheet Pro styling across Data Sync and Local Data point, route, and shape popups in both view and edit paths, including legacy popup fallback styling.
- Local Data menus update immediately after ADS-B track route save/delete and local-data popup deletes; removes the manual Refresh local data button.

## v321

- Release label remains `v1.1.0`; iteration marker is `v321`.
- Applies the selected Option C / Data Sheet Pro styling to Data Sync and Local Data point, route, and shape popups.
- Keeps popups compact while increasing width, row spacing, and font size for better legibility.
- Keeps the working close button, edit controls, combined Lat/Lon field, and Save / Cancel / Delete handling from v320.

## v320
- Kept release label at v1.1.0 and updated iteration to v320.
- Removed the ADS-B Save Filter button and made ADS-B menu/filter changes autosave/apply on refresh.
- Fixed ADS-B class filters so disabled classes are immediately redrawn/removed instead of only stopping future updates.
- Restyled point, route, shape, local data, and Data Sync point popups to a compact ADS-B-style layout with working close/edit actions.
- Compact local data and Data Sync edit popups by removing Type/Asset fields, combining Lat/Lon, and fixing Save, Cancel, and Delete handling.
- Tightened drawing tool submenu sizing and disabled map panning during shape creation.
- Improved Terrain Mode Local elevation handling with coverage borders, local mesh refresh hooks, and a movable/lower default terrain control panel.


## v318
- Polished ADS-B aircraft popup with a professional compact layout.
- Added Speed and Owner/Op to ADS-B aircraft popups, plus heading when available.
- Tightened ADS-B aircraft label chip sizing around callsign text.

## v302
- Kept release label at v1.1.0 and updated iteration to v302.
- Started stabilization cleanup build process: removed duplicate legacy ADS-B tracking scripts from the rendered TAK Map page and replaced them with a single current ADS-B tracking controller.
- Centralized runtime iteration/product display updates for the TAK Map page.
- Restored ADS-B tracking ownership through one path for Track button state, live distance, route recording, and Save ADS-B Track dialog.
- Preserved current terrain, elevation, viewshed, Data Sync, local data, ADS-B no-blink marker rendering, and status table behavior.

## v293
- Kept release label at v1.1.0 and updated iteration to v293.
- Added Add Elevation Data import progress/status bar for direct HGT, DTED, and GeoTIFF/COG imports.
- Added individual Remove controls for locally indexed elevation files.
- Renamed the toolbar label from 3D Terrain to Terrain Mode.
- Redesigned the Terrain Mode interface as a compact themed control panel with Quality and Elevation Source selectors.
- Added Terrain Mode elevation source selector for Streamed vs Local elevation lookup/sampling.
- Updated ADS-B aircraft status table to close on outside click and toggle closed from the ADS-B status button.

## v289
- Kept release label at v1.1.0 and updated iteration to v289.
- Fixed Tools → Add Elevation Data by exporting and rebinding the local elevation dialog opener so the button opens reliably.
- Hardened Viewshed window placement so saved/offscreen positions are clamped back into the visible viewport on open, resize, and restore.


## v286
- Restored ADS-B Aircraft indicator/list in the status bar.
- Moved ADS-B popup Track, Aircraft Type, and capitalized Class display into the authoritative popup content path so the Track button persists between hover/click/refresh.
- Kept ADS-B popup close X removed; popups close by clicking elsewhere or another object.
- Constrained the Track button inside the ADS-B aircraft popup layout.

# TAK Map Changelog

## v283
- Release label remains v1.1.0.
- Added deeper ADS-B/runtime cleanup after v280 validation found remaining legacy ADS-B server/proxy functions in the served page.
- Removed base ADS-B auto-start calls from map initialization.
- Replaced legacy server-proxy ADS-B refresh/scheduler and base marker redraw path with inert stubs so only the current client-only Airplanes.live module owns ADS-B.
- ADS-B remains disabled by default and controlled only from the ADS-B menu.
- Removed ADS-B from the top status dropdown/banner path.
- Added runtime form/label hygiene for duplicate IDs and unassociated labels.
- Removed duplicate EUD dropdown polling intervals from older patch blocks.
- Preserved current drawing, Save Shape, Viewshed, Terrain, Local Data, Data Sync, Cert Setup, and client-only ADS-B functionality.

## v279
- Fixed repeated ADS-B menu controls by rebuilding ADS-B as a single-owner menu and suppressing legacy ADS-B UI paths.

# v278

- Kept release label `v1.1.0`; iteration is `v278`.
- Added a hard ADS-B legacy cleanup pass to keep ADS-B inert until explicitly enabled.
- Added an early timer tracker and final cleanup that cancels legacy ADS-B timers/timeouts/workers and removes ADS-B map-move handlers where identifiable.
- Restored a stable global `togglePanelCollapse` handler to stop panel expand/collapse errors.
- Rebuilt the ADS-B menu as a single authoritative compact block and removed duplicate v270/v275 center controls.
- ADS-B remains client-only Airplanes.live and disabled by default on page load.
- Removed/hidden visible ADS-B Test/Refresh controls and kept interval changes live.
- Kept ADS-B Center Source options as Manual, Select Center, and Follow Map Center.
- Kept ADS-B no-glow icon styling and compact opaque popup styling.
- Preserved ADS-B worker/diff rendering only after user enables ADS-B.
- Kept Save Shape as the single drawing metadata dialog and kept Shape Options closed on load.
- Kept global ADS-B-style numeric steppers and compact drawing submenu styling.
- Renamed the elevation tool button to Add Elevation Data and expanded file accept filters for HGT, GeoTIFF, and DTED files. Full GeoTIFF/DTED terrain sampling parser support remains limited/pending.

### v284
- Kept release label at v1.1.0 and updated iteration to v284.
- Limited ADS-B popup changes only: close X now force-closes popups and ADS-B Class values display as Govt, Military, Civil, or Unknown.

## v316
- Restored ADS-B menu controls removed during route finalization: Enable/Disable ADS-B toggle, Follow Map Center, combined Center Lat/Lon field, filters, Save Filter, and Refresh ADS-B.
- Restored ADS-B status item in the top status bar.
- Restored Viewshed button in the main floating toolbar.
- Kept v314/v315 route/startup fix and single ADS-B owner behavior.
