# TAK Map v1.4.0-i659 — Saved-route and waypoint editing

- Add **Edit Route** inside the existing popup for saved imported routes. Keep the normal Route tool and Roads snapping; preserve all original route geometry when reopening, with individually editable control waypoints.
- Drag existing waypoints, click any route leg to insert a waypoint, and use a very compact bold waypoint menu (Manual, Copy Coordinates, Delete; ~4px padding). Recalculate only changed road legs and update segment distances/labels.
- When editing a saved route, offer **Save Changes**, **Save as New Route**, and **Cancel**. Save Changes updates the same canonical Local Data object ID; Save as New Route opens the standard name/color/category/notes dialog and retains the original. Cancel discards changes.
- Store original control points and per-leg geometry indices in route metadata so a reload restores editing handles without replacing the snapped route with straight lines. For older i658 saved routes without control-point metadata, reconstruct approximate controls along their intact saved geometry; verify placement before saving alterations.
- Validate update requests through authenticated route-only endpoint with stable-ID matching, data integrity checks, atomic writes and a stale-edit revision guard. Never replace unrelated imports or local objects.
- Retain i658 live route preview, road snapping, on-map distances, Roads/Manual selector, NDM graph activation, user configuration and existing data. The i658 source package remains rollback.
- Browser tests simulate actual production route save modal and popups; backend tests use a real stored import registry and verify stable IDs, revisions, rejection paths and integrity. Live deployment and graph routing need operator confirmation.
