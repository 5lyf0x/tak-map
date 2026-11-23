# TAK Map v1.4.0-i661 — sidebar and AIS detail corrections

- Restores and explicitly positions the **MESH SYNC** card between Gateway Data and OTS Data Sync. Enrollment controls remain visible before joining a group, with **Not enrolled** status.
- Renames the existing **Data Sync** sidebar card to **OTS DATA SYNC** (label-only; existing OTS functionality unchanged).
- Splits AIS vessel remarks into individually wrapped, escaped field lines in the Gateway Data context Details section; non-AIS remarks remain unchanged.
- Corrects the README current-version heading and download/extraction example to i661.
- Preserves the i660 Token Mesh protocol, encrypted transport, journal, and all existing installation data. This package does not certify Android↔Linux Token Mesh interoperability or add mesh functionality beyond i660.
