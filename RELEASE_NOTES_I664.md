# TAK Map v1.4.0-i664 — AIS Details and MESH SYNC appearance

- Fix the actual Gateway Data AIS context popup renderer: parse raw combined AIS remarks and show every field as an independent two-column row, with a full-width Details section heading. All values are HTML-escaped; long values wrap without merging into adjacent fields.
- Match the MESH SYNC switch to other sidebar card toggles (green ON, gray OFF; 38×20) and remove its status-chip dot. Leave all other Mesh UI, networking, Missions and collapse behavior unchanged.
- Preserve existing AIS sources, Gateway Data TLS settings, persistent configuration and data. i663 source remains unchanged for rollback.
- Actual host/browser and live source testing are still required after installation; this release changes presentation only.
