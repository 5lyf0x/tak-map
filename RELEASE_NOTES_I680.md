# TAK Map v1.4.0-i680 — Restore visibility of existing Local Data

Based on i679 without modifying previously installed data.

## Critical correction
- Fix `/api/tak-map/imported` HTTP 500 when i679's enriched Local Data response exceeds JSON serialization recursion limits. If normal enrichment fails, serve the complete saved imports from canonical `imports.json` without truncation or writing to disk. Do **not** report an empty list for an unreadable file.
- Preserve all saved point/route geometries and existing object/import IDs. Route revision hashes for saved routes are computed in the response to retain edit protections.
- Recovery responses include an explicit `local_data_recovery_i680` indicator and a response header; they do not claim presentation enrichment succeeded. Normal response behavior remains unchanged when serialization succeeds.
- Guard basemap Tone initialization for dynamically registered basemaps (fixes JavaScript TypeError reading `brightness`), without restoring old slider code.

## Data protection
- Installer does not overwrite, migrate, clean, or restore `/var/lib/tak-map/tak_map_imports`.
- The existing i679 full-fidelity route storage and long-route editing fixes remain intact.
- Retain i679 source for rollback but do not roll back or reimport data as part of this update.

## Live verification
After install and sign-in, confirm Local Data shows the 24 points and 6 routes already verified on disk, and check a long saved route can reopen. If the recovery marker is present, it indicates that nonessential enrichment was skipped to keep canonical records accessible; report it for a subsequent focused fix. Actual host records could not be tested in this isolated build.
