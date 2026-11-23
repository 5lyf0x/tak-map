# TAK Map v1.4.0-i679 — Long route persistence correction

Based on the unchanged **v1.4.0-i678** rollback source.

## Corrected
- **Canonical Local Data storage:** saved routes are now serialized without a 1,000-element array cutoff or a `...truncated...` marker. Serializing a circular/invalid object aborts a write instead of silently shortening the route. Atomic writes use separate temporary files.
- **API responses:** import POST/read-back GET and other JSON endpoints return complete coordinate arrays, not diagnostic excerpts. Existing route-save verification remains enabled and checks the actual imported route by unique ID.
- **Existing saved route edits:** raise the bounded edit limit to 200,000 geometry vertices and 32 MiB so long routes can be reopened and updated. Still validate coordinates and reject invalid/oversized requests.
- **Legacy damage audit:** optional read-only `tak_map_import_geometry_audit_i679.py` identifies records damaged by the old serializer. It does **not** delete or repair them, and the installer does not modify any existing saved routes.

## Unchanged
The diagnostic `json_safe()` function is retained for explicitly bounded logs and identifiers, where a short preview is intentional; it is no longer used by canonical app JSON persistence or HTTP response serialization. This is a purposeful separation, not a parallel user-facing route-saving implementation.

All i678 route creation, MVUM, NDM routing, Basemap Blend/Tone, and road/trail search features are otherwise retained.

## Live-server verification needed
Test saving and reopening the user's original 376-mile trail, including every waypoint and resolved geometry section. The archived source tests cannot reproduce access to the live server or retrieve the user's unsaved browser editor state.

Existing records with `...truncated...` cannot be restored from the damaged `imports.json` alone. Recover them from an intact client-side backup, original GeoJSON, or other prior backups if available. No automatic destructive repair is performed.
