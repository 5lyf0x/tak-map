# TAK Map v1.4.0-i663 — Mesh Sync card header and typography

- Keeps Command Slate and Manrope styling, the i662 Token Mesh transport, Mission controls, and persistence behavior unchanged.
- Increases the legibility of small Mesh Sync labels: Secure Peer Synchronization and Mission Access eyebrow labels, Mission joined count, Mission QR action, enrollment instructions, Mission item detail, peer/Mission/object metrics and their labels, and footnote text.
- Places the status chip and network-enable switch *inside* the MESH SYNC header, and adds an independently functioning collapse arrow **after** the switch at the far right.
- Exempts the Mesh card from generic sidebar auto-collapse/title reparenting, maintains the header DOM positions on refresh, and remembers the Mesh collapse setting locally (it does not affect networking).
- Keeps the separate toggle semantics: network pause preserves group keys and Mission journals. The collapse button changes the card view only; it never changes Mesh networking.
- No change to Gateway Data, OTS Data Sync, AIS, Mission synchronization protocol, map markers, or installed persistent data.
- This source release was tested with automated local checks; real host and TAK Rig/XTAK Data Sync live interoperability still require external testing.
