# TAK Map v1.4.0-i690 — Integrated status strip

Baseline: v1.4.0-i689. Source-only package; existing `/var/lib/tak-map` application data is not altered by the status-strip changes.

## What's new

- Relocated the status bar into the 28-pixel strip at the top of the map viewport, below the 58-pixel main header. Map viewport positioning is retained; no floating status pill over the map.
- New status order: **EUDs → VEIL → Downloads → LAN → Internet** with generous horizontal spacing and a horizontal-scroll fallback at narrow widths. **TAK Server** is appended only if both configured and enabled. ADS-B was removed from the status bar only; tracking is unchanged.
- EUD count and details use the same authenticated, `online=1` endpoint snapshot, with UID deduplication and independent error/stale state. Legacy map-marker-derived counts cannot overwrite the new bar.
- Compact 274px VEIL dropdown (maximum height 222px) includes receiving and subscribed nodes, deduplicated by node ID. It consumes notifications from the existing VEIL refresh rather than starting a second VEIL request loop; row identity, scroll, and keyboard focus are preserved on updates. Selecting a node invokes the existing VEIL Node Details UI.
- Downloads and Internet indicators mirror existing status signals; LAN receives a new authenticated `/api/tak-map/status-network-i690` health endpoint. LAN **Available** means a usable private IPv4 interface, **not** confirmed peer communication. The endpoint intentionally does not scan other devices. Optional `TAK_MAP_LAN_INTERFACE` sets the inspected host interface.
- TAK Server appears only when the local `opentakserver.service` is enabled **and** a standard configuration file is present. For custom deployments outside standard config locations, optional `TAK_MAP_STATUS_TAK_CONFIGURED=1` enables recognition of a configured service; this flag alone cannot make a disabled service appear enabled.
- Fixed legacy status DOM compatibility through a hidden legacy container. The new strip mounts once and updates text/dots/individual keyed rows in place, without altering map data, selection, tools, or renderer lifecycle.
- Authenticated JS/CSS routes under `/assets/runtime/` with correct MIME, no-store and missing-file 404 behavior. Installer explicitly deploys and verifies both new assets.

## Notes and limits

- LAN status checks the TAK Map **server host** network, not the browser computer's NIC. Peer reachability is not inferred from EUD count.
- The i690 status bar did **not** add a new server-side EUD subscription or VEIL API poll. EUD snapshot refresh runs every 10 seconds and LAN every 30 seconds; browser timers pause while the page is hidden.
- Real server service configuration, a wide range of imported GIS layers, and live Cesium behavior still require installation-time verification.
- Existing `/var/lib/tak-map/infrastructure/` and `/var/lib/tak-map/tak_map_imports/` must be preserved; back them up before upgrades.

Rollback source version: v1.4.0-i689.
