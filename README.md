# TAK Map v1.4.0 i618

i618 is the public 1.4.0 release built from i617. It introduces one shared content-aware sizing policy for all right-side contextual panels while preserving the validated Data Sync, ADS-B, Gateway Data, and Source Extension behavior.

## i618 changes

- Dynamically sizes ADS-B, Local Data, Data Sync, Gateway Data, and Source Extension context panels to the actual content.
- Keeps compact panels narrow while allowing long fields to expand within responsive bounds.
- Reserves themed scrollbar space so rows do not shift when scrolling appears.
- Prevents horizontal scrolling and wraps genuinely long values cleanly.
- Sizes dual panels independently and prevents ADS-B/context overlap.
- Mounts shared context panels above ordinary map controls while keeping true modals above them.
- Updates the public product version to `1.4.0` and the left-menu iteration to `i618`.
- Updates installation, release, troubleshooting, and context-panel documentation.

## Install

```bash
cd ~/Downloads
unzip -o tak-map-v1.4.0-i618.zip
cd ~/Downloads/tak-map-v618
chmod +x install.sh
sudo ./install.sh
cd ~/Downloads
```

After installation, close and reopen TAK Map and hard-refresh the page.

See `docs/CONTEXT-PANELS.md` for the shared sizing and scrollbar behavior.
