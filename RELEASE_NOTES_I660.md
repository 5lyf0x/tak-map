# TAK Map v1.4.0-i660: Token Mesh interoperability candidate

This is a **test release**, not proof of TMS-FINAL 2.0 full conformance. Native XMS2 discovery and XTP3 encrypted transport are enabled following explicit mesh enrollment; XMS1 matching Mission bindings are required for data exchange. Group membership does not automatically grant Mission access. A persisted SQLite journal stores object history, baseline flags, tombstones and per-origin contiguous watermarks. Object heads use deterministic comparison, not a global master revision.

## Setup
Install with the existing root install.sh in a freshly extracted folder. Use the MESH card to create or join a group; use Join Mission (XMS1) on each device with the same Mission invitation. Network peer discovery uses UDP 42420, direct TCP 42421–42452; for ZeroTier/VPN where broadcast fails configure `TAK_MAP_MESH_PEER_TARGETS=192.0.2.10,192.0.2.11` as service environment (replace test IPs with your peer addresses). This variable is optional. Existing local and OTS features remain unchanged. Sensitive operations require both the TAK Map login and Dashboard administrator login via HTTPS. Mission tokens and group tokens are bearer secrets.

## Known limitations
- NO live Android↔Linux exchange or interoperability certification performed. The Python↔Python synthetic test is not a substitute. Encryption/security audit still required before use outside trusted LAN/overlay networks.
- Only CoT Point/Route/Area receive-side projection is implemented. FILE object payloads remain durable in the journal but do not automatically export into Local Data. Route/Area rendering relies on supported CoT coordinate attributes; some Android-native geometries may not render until mapped. Automatic publication of TAK Map local object edits to Token Mesh is not implemented.
- Optional PLI/chat/direct-sharing, journal compaction, authenticated administrative peer controls and full compliance tests not implemented.
- No automatic publication of received objects to OpenTAKServer, TAK Gateway, normal OTS Data Sync or external TAK services.
- QR image import requires browser BarcodeDetector support; manually paste the complete XTM1 token if not available.
- Protected credential files are owned by the service account with mode 0600, but Mission tokens reside in the access-restricted journal SQLite DB.

## Validation
Syntax, local protocol/unit tests and ZIP integrity verified at packaging time; live network deployment and Android pairing need operator-side testing.
