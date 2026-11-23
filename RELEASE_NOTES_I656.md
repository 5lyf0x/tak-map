# TAK Map v1.4.0-i656 — Lossless snapped-route save

- Fix: Save Route now writes the full calculated Roads polyline directly as a GeoJSON LineString, rather than temporarily replacing the editable clicked-waypoints list for legacy save handlers.
- Retain intermediate vertices, curves and turns; preserve the route name, notes, color, style, movement and waypoint/segment metadata.
- Successful upload refreshes saved routes and exits the editor. Failed upload leaves the route editable. A rejected/disconnected leg remains unsavable.
- Retain i655's Roads-default UI, 20px preview, active graph startup, NDM registration and status management. No changes to Valhalla activation, NDM graph files, authentication or user data.
- Live service and save/readback must be verified after installation; browser tests use a simulated routing backend.

