# TAK Map v1.4.0-i671 — VEIL aircraft styling and Range Rings

- XTAK VEIL ADS-B uses authentic i670 tar1090 silhouettes, solid white fill, 2 px black non-scaling stroke, and 20% larger 2D/3D icons, retaining heading rotation and anchors. Other service icon sizes unchanged.
- Range Rings label direction is now multi-select N, NE, E, SE, S, SW, W, NW; existing stored single-direction values migrate on read and chosen directions persist in prior key.
- Range Rings color picker gains a clickable Choose control using native showPicker where supported.
- Range Rings map-center selection uses a black crosshair cursor and supports Escape to cancel, both restoring normal map cursor.
- XTAK VEIL APRS node-map artwork parity is **not implemented**: authoritative VEIL Node Map icon assets/source were not available in this build environment. Existing generic APRS marker is unchanged rather than shipping guessed symbols.
- Live node/map and browser verification remains necessary.
