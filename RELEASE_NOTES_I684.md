# TAK Map v1.4.0-i684 — Route reliability and sidebar parity

Baseline: full v1.4.0-i683 source package. No new database schema or Local Data migration.

## Route editor and elevation

- Object Details route selection sends a selection event to the elevation component; selecting a route automatically opens the compact profile unless dismissed in that selection session. Non-route selection, closing details, or deselecting closes it.
- Canceling a saved route edit invalidates pending snap/resolve callbacks, clears transient waypoint markers, labels, draft lines, hit targets and menu, and exits edit mode without modifying saved geometry. In-place save behavior remains unchanged.
- Route Details hides the displayed POINTS row for Route objects only. Notes metadata is presented on separate lines with safe text nodes; saved payload is untouched.
- Extended profile chart height reduced from 250px to 188px (164px on narrow layouts), metrics padding tightened. Compact remains 82px. Switching Compact/Extended and clicking steep-run numbers re-docks bottom-center with 24px margin. Drag behavior remains available.

## Sidebar

- XTAK VEIL and Mesh Sync top-level card backgrounds match the standard sidebar cards. Heading and status-chip typography/geometry are harmonized. Semantic toggle colors remain.
- VEIL header right-hand chevron slot now uses the same fixed 24px footprint as Mesh Sync, minimizing toggle alignment drift.
- Satellite Tracking is placed immediately above Offline Maps in the sidebar; settings and functionality are unchanged.

## Upgrade cautions

- As with previous releases, preserve a copy of `/var/lib/tak-map/tak_map_imports/` before installation.
- The source-only ZIP deliberately excludes credentials, keystores, Python bytecode and build artifacts.
- Changes validated offline with Python, Node and Chromium regression tests; **not deployed/tested on the live TAK Map host**.
