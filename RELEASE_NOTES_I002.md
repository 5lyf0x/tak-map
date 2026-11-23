# TAK Map v1.5.0-i002 — Offline Maps startup correction

**Baseline:** validated v1.5.0-i001 full source, preserved untouched. **Scope:** two startup/interface defects only, plus normal version and documentation updates.

- A late-loading map core now triggers reconnection of the existing Offline Map Packs Rename control. All completed downloaded/imported packs show Rename even when the Offline Maps module loads first.
- Saved Offline Maps are now fetched **and rendered** on page startup, and the optional-data loader also requests a redraw. Manual Refresh remains available but is not needed just to see existing packs.
- Repeated shell/optional-data notifications and redraws are idempotent: no duplicate Rename buttons or retry notes.
- The bottom-left sidebar shows TAK Map **1.5.0 / i002** and canonical server API/config/version agree.
- No changes to offline map records, MBTiles bytes, tile download jobs, map IDs, names/history or EUD packages. The i001 Rename endpoint and controls, natural sorting and 600px scrolling remain intact.

## Installation

Download `tak-map-v1.5.0-i002.zip` into `~/Downloads`; extract into a **new** `tak-map-v1.5.0-i002/` folder and run `sudo ./install.sh`. Existing `/var/lib/tak-map` data remains in place. Keep `tak-map-v1.5.0-i001.zip` as rollback.

## Verification limitations

Source syntax, regression fixtures, ZIP integrity, checksum manifest and fresh-extraction parity can be validated before handoff. Live server/account-specific startup and production deployment have not been performed.
