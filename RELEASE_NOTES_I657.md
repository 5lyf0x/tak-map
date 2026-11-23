# TAK Map v1.4.0-i657 — Snapped route save dialog integration

- Fix the existing **Save Route** modal so its Save button uploads the full Roads-mode snapped polyline instead of only the clicked waypoints. This addresses a legacy save handler taking back control after the newer route editor initializes.
- Preserve the route name, category, selected color, notes, distance, control-point metadata and full road geometry. Route reload continues through the existing GeoJSON import/display path.
- Keep the editor and modal open if an upload fails; block saving while a road leg is still disconnected or calculating.
- Maintain i656 Manual/Roads modes, 20px snapping, drag editing, NDM registration and Valhalla configuration. This release does not change graph data or automatic routing startup.
- Normal in-place installation retains existing configuration, credentials, downloaded navigation and elevation, saved routes, and persistent data; i656 source remains the rollback baseline.
- Validation in this environment uses the actual browser dialog with a mocked local routing response and upload. Live server route save/readback must still be confirmed after installation.

