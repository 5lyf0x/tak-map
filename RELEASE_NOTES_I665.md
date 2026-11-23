# TAK Map v1.4.0-i665 — VEIL live receiver and compact NWS details

**Build basis:** v1.4.0-i664 (untouched rollback release). Source-only update; application configuration, maps, journals, Gateway trust settings, and data files are preserved on normal install.

## What's new

- **XTAK VEIL Phase 1 (functional):** adds a dedicated card between BASEMAP and GEOFENCES, independently enabled/collapsed with the approved gray/green switch, and a white radar SVG for Discover and Scan LAN.
- **Node management:** LAN `_xtak-sensor._tcp` mDNS discovery using `avahi-browse`; verifies node identity against public VEIL `GET /api/v1/discovery`; supports multi-checkbox selection and batch Add Selected (N), manual IP/`.local` verification, persistent node records, and removal.
- **Live CoT reception:** local TAK Map service listens for configured VEIL nodes' UDP unicast CoT (port 6970 by default), accepts bounded VEIL r50 `<xtak_veil>` metadata and supported ADS-B `adsb_1090`, AIS, APRS, and Remote ID observations. Checks sender node ID and configured private address (not cryptographically authenticated), rejects malformed/old/duplicate/out-of-order packets, and removes expired observations.
- **Map and status:** distinct VEIL marker layer with source/node details and APRS weather symbol fallback; counts by source, receiving/waiting/disabled state and last packet, visibility switches and settings; UI refreshes without requiring a reload. VEIL never automatically publishes to Gateway, OTS Data Sync or Token Mesh.
- **NWS Weather Alerts context:** removes Instruction, moves Description into full-width labeled field with a slim dark scrollbar capped to `min(180px,25% of map viewport height)`; constrains the overall context panel within the actual map viewport. A runtime fallback covers cached legacy NWS popup scripts.
- **Release identity:** backend/config, sidebar iteration marker, active assets and release docs reflect **v1.4.0-i665**. Active footer version is enforced even if a legacy cached module writes an old iteration.

## Required operator setup / limitations

- Enable **XTAK VEIL** in TAK Map, discover or add nodes, and **configure each VEIL node separately** to send UDP CoT **unicast** to the TAK Map host's reachable LAN IP and configured UDP port (default **6970**). Discovery and manual adding do not configure the node's outbound CoT connection automatically. Permit the chosen UDP port on the TAK Map host firewall. This local data path needs neither ZeroTier nor internet.
- mDNS discovery requires `avahi-browse` (`avahi-utils`). Installer attempts to supply it if missing; if unavailable, use manual Add Node. Node verify requires a reachable private IPv4 or `.local` address and an exposed public HTTP discovery endpoint (default port 8080).
- Phase 1 CoT UDP is **not authenticated encryption**. Sender node ID/IP checks are best-effort provenance only. Use a trusted local network; encrypted authenticated Live SA API/WS support is a **future Phase 2**, not part of i665.
- Phase 2 missing: authenticated Live SA snapshots/WebSocket catch-up, exact node-side stale-state lifecycle after reconnect. Phase 3 missing: cross-source dedup with built-in ADS-B/Gateway AIS, richer node health and automatic control of VEIL CoT destination. VEIL objects remain an independent overlay.
- Browser/backend and simulated multi-node CoT tests were performed; real VEIL hardware, multi-host firewall, and live LAN tests **not performed** in this build environment. No claim of deployed Android/VEIL interoperability certification.
