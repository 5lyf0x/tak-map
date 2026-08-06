# TAK Map i568 configuration notes

The i568 Data Sync worker is automatically enabled for authenticated OpenTAKServer sessions. No new operator configuration is required.

Default limits:

- 5-minute automatic Data Sync polling
- 6 parallel OTS requests
- 4-second discovery endpoint deadline
- 5-second Mission endpoint deadline
- 35-second overall refresh deadline
- 20 missions per refresh

Snapshots are isolated by authenticated user, authentication mode, and configured OTS origin. They are stored below the TAK Map data directory in `data_sync_snapshots_i568` and are preserved through service restarts and transient OTS failures.

The browser-facing Data Sync route never waits for the complete OTS acquisition. It returns the current snapshot or an explicit initial-refresh state.

## Context panels in 1.4.0 i618

Context-panel width is automatic and has no separate configuration switch. Compact records remain narrow, long source fields expand within responsive bounds, and simultaneous ADS-B/object panels are constrained to avoid overlap. See `CONTEXT-PANELS.md` for details.
