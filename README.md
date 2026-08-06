# TAK Map v1.4.0 i620

i620 is the corrective public 1.4.0 package built from i618. It fixes the left-sidebar release/iteration display and makes NIFC context panels size to their actual content without changing the other validated contextual panels.

## i620 correction

- Removes the stale deferred sidebar owner that forced the displayed iteration back to `i602`.
- Makes the server-rendered `i620` identity authoritative before first paint and coerces delayed legacy writes without visible flicker.
- Preserves the NIFC content-aware width correction from the prior package.

## i620 changes

- Shows `1.4.0` and `i620` in the left-sidebar version panel from the first rendered frame.
- Adds an authoritative identity guard so delayed legacy startup hooks cannot make the sidebar flicker between older versions.
- Sizes NIFC Fire Perimeter context panels from their visible labels and values, expanding only when longer NIFC content requires it.
- Keeps NWS, ADS-B, Local Data, Data Sync, other Gateway Data, and Source Extension panel behavior unchanged.
- Preserves stable scrollbar gutters, fixed headers, responsive bounds, and no horizontal scrolling.

## Install

```bash
cd ~/Downloads
unzip -o tak-map-v1.4.0-i620.zip
cd ~/Downloads/tak-map-v620
chmod +x install.sh
sudo ./install.sh
cd ~/Downloads
```

After installation, close and reopen TAK Map and hard-refresh the page.

See `docs/CONTEXT-PANELS.md` for the shared sizing and scrollbar behavior.
