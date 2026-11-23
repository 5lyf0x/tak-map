# TAK Map v1.4.0-i694 — BASEMAP + Infrastructure controls

**Baseline:** exact `tak-map-v1.4.0-i693.zip`; combined UI patch applied cleanly.

## Changes

1. Radar Reflectivity uses the same Soft Pill track/thumb, percent label, and input behavior as BASEMAP layer transparency. The weather-specific range CSS is removed. Opacity updates the current and buffering Leaflet radar frames and current/retiring Cesium radar layers without reissuing tile requests; the existing i691 saved preference key is preserved.
2. Blend dropdown remains open after selecting any mode, including custom modes; selecting a mode updates the live basemap, label, selected item, and saved preference without closing or losing scroll position. Outside click and Escape dismiss the menu; switches to a different popup retain their existing behavior.
3. INFRASTRUCTURE card stays directly after BASEMAP LAYERS and before XTAK VEIL even if other sidebar scripts insert or reorder cards. Both legacy and active VEIL placement scripts now place VEIL after Infrastructure when present, eliminating their previous conflicting periodic reorder. Detects the basemap panel by its real control IDs instead of an obsolete title string; a direct-child MutationObserver and periodic probe restore ordering without re-creating panels.
4. INFRASTRUCTURE receives an independent Show/Hide switch in the header (default ON, green ON/gray OFF). OFF clears 2D and 3D infrastructure graphics and cancels in-flight viewport fetches, while preserving all individual layer selections and stored GIS data; ON reloads enabled layers. State persists using `takmap.infra.visible.i694`. Header collapse continues to use existing state key `takmap.infra.collapsed.i685`.
5. Version, source docs and runtime asset query strings increment to i694. The installer verifies all modified runtime assets.

## Unchanged

- i693 NWS radar source, tile proxy, frame selection, partial-status and tile recovery logic.
- NWS weather alerts, saved map points/routes/shapes, top status strip, basemap stack, local GIS storage, 3D terrain, routing, token mesh, VEIL, NDM and Gateway.
- Existing persisted map preferences, except the newly introduced dedicated Infrastructure master switch key.

## Excluded

Phase 3 radar history and animation were planned separately and are **not** implemented in this UI maintenance release.

## Upgrade / rollback

Place the ZIP in `~/Downloads`, extract into a fresh `~/Downloads/tak-map-v1.4.0-i694` folder, then run `sudo ./install.sh` within it. Keep the complete i693 ZIP until live browser validation passes. This environment cannot install or live-test your host.
