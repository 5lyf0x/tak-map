# TAK Map v1.5.0-i001 — release notes

**Scope:** Offline Map Packs and correct version display, based solely on v1.4.0-i699.

- Rename completed downloaded and imported MBTiles packs directly in the Offline Map Packs list (Save, Cancel, Enter, Escape, visible errors).
- New names immediately re-sort the display alphabetically, case-insensitively with natural numbers. Internal data order, stable IDs and stored file paths do not change.
- Offline Map Packs list has a 600px maximum height with internal scrolling; other sidebar sections are not resized.
- Rename changes catalog name/timestamp only, invalidates old outgoing EUD package references for next Send, and preserves original MBTiles metadata, map bytes, download/retry state, and transfer history.
- Catalog saves preserve all existing entries, including more than 80 packs. Catalog writes are atomic, and mutations share the same in-process lock.
- Sidebar footer shows TAK Map 1.5.0 and iteration i001, including after browser startup/async rendering. Version marker, API, cache keys, and `VERSION` agree.

## Install and rollback

Extract this full-source ZIP into a **new** `tak-map-v1.5.0-i001/` folder and run `sudo ./install.sh`. Do not overlay the old extracted i699 source tree. Installer does not delete `/var/lib/tak-map` or stored map files. Keep `tak-map-v1.4.0-i699.zip` unchanged for rollback.

## Validation scope

Static syntax and isolated filesystem/browser checks can be performed before handoff. No claim of deployment, field use, or real TAK server results is made until tested on the operator's host.
