# TAK Map v1.4.0-i699 — Release Notes

Last v1.4.0 iteration. Next sequential release: v1.5.0-i001 (not built).

## User-facing fixes
- Offline Maps **Basemap Source** dropdown retrieves its source list after authenticated startup even when the card initializes before the main configuration.
- Offline Maps uses the selected Command Slate layout: area first, basemap source, optional pack name, zoom range, tile estimate, Preview Max and Download. The West/East/South/North numeric readout and duplicate DOWNLOAD heading are hidden. No header icon, dropdown chevrons, or action-button icons.
- Preferences for **BASEMAP LAYERS** are stored on the TAK Map server **per authenticated user**: order, enablement, opacity, Blend, Tone, and custom pixel controls. Server-side atomic revisions reject conflicting stale writes. Imported sources temporarily missing from the catalog retain their original saved positions/settings.
- Previous browser-only settings are **not automatically assigned to a new account**, to prevent inadvertently copying another user's preferences. If a user has no server-side settings, an explicit one-click migration button appears in BASEMAP LAYERS.

## Data and migration
- New private files under `/var/lib/tak-map/user_basemap_preferences_i699/`, keyed by a non-reversible stable identity digest, with mode 0600.
- No edits to saved imports, existing offline packs, NDM elevation packages or radar data.
- Preferences sync among browser sessions/devices on the **same** TAK Map server; cross-server synchronization requires separate work.

## Verification boundary
Offline source and user-prefs HTTP behaviors tested with controlled fixtures. Live server, HTTPS account roaming, and extended map use have not been tested in this workspace.
