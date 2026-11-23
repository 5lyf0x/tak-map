# TAK Map v1.5.0-i003 — Offline map performance

**Baseline:** validated full-source v1.5.0-i002 ZIP, preserved untouched as rollback. This is a focused release: offline map lookup, zoom/pan, imported row schemes, cache behavior and normal version identity updates.

## Operator changes

- Offline MBTiles maps should begin loading new tiles while the map is panned, rather than only after panning stops.
- The highest downloaded zoom level may be scaled up to higher map zooms without additional imagery detail.
- In **OFFLINE MAPS**, imported maps display a **Tile rows** selector (TMS default; XYZ only for imports that store XYZ rows). This changes catalog interpretation, not map content. Downloaded TAK Map packs always remain TMS.
- Ordinary successful completed tiles receive private browser caching with a content revision; missing and still-updating tiles use `private, no-store`.
- Multiple selected basemaps retain their existing order and Blend, Tone and opacity settings; custom per-pixel Blend work is rate-limited to smooth long pans.
- Sidebar footer, API and `VERSION` consistently display **1.5.0 / i003**.

## Data safety and scope

The installer leaves `/var/lib/tak-map` intact. Viewing tiles never rewrites the existing catalog or modifies an MBTiles file. Existing Offline Map Packs, Rename, Apply, Send, Delete, scrolling and auto-population are preserved. There is no automatic online fallback or new source service. Do not overwrite the previous extracted source folder.

## Installation

```bash
cd ~/Downloads
unzip -o tak-map-v1.5.0-i003.zip -d tak-map-v1.5.0-i003
cd tak-map-v1.5.0-i003
sudo ./install.sh
```

## Verification scope

Synthetic map fixtures, authenticated route/row-scheme tests, browser card controls and tile-layer configuration, and inherited offline map/stack behavior were checked before packaging. Live server pan/zoom speed and real-device behavior were **not** measured or installed by this handoff. See `VALIDATION_I003.md` and the external `TAK-Map-v1.5.0-i003-VALIDATION.txt` handoff report.
