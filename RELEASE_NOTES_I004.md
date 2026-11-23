# TAK Map v1.5.0-i004 — Offline Map Backend Installer Repair

**Baseline:** the original, SHA-256-validated v1.5.0-i003 source ZIP; archived i003 remains untouched. This is an installer correction, not an offline tile-engine redesign.

## Changes

- The i003 source correctly bundled `tak_map_offline_perf_i003.py` and imported it from `tak_dashboard.py`, but `install.sh` omitted the step copying it to `/opt/tak-map/`. The service therefore could exit during startup with `ModuleNotFoundError`.
- Install the bundled module at `/opt/tak-map/tak_map_offline_perf_i003.py` (permissions `0644`) **before** `tak_dashboard.py` is installed and `tak-map.service` restarts.
- Advance `VERSION`, configuration API, sidebar release/iteration, login HTML, cache identifiers, and package documentation to **1.5.0-i004**.
- Continue using the previously validated i003 tile-serving behavior, import row-scheme endpoint, zoom/pan settings, catalog logic, and browser assets unchanged.

## Preserved

Existing MBTiles files, offline map names/IDs, download and retry history, imported map row selections, Rename/Apply/Send/Delete controls, authentication and config data remain untouched. No data migration or re-download is required. The installer does not clear `/var/lib/tak-map`.

## Install

```bash
cd ~/Downloads
unzip -o tak-map-v1.5.0-i004.zip -d tak-map-v1.5.0-i004
cd tak-map-v1.5.0-i004
sudo ./install.sh
```

A previously failed i003 install may be repaired directly by installing the full i004 package. Keep i003 unchanged as the source baseline; i002 is the last known functional rollback if i003 never launched on the target host. This package was validated in isolated source and simulated-install tests, **not** installed on the production host.
