# TAK Map v1.4.0-i672 — XTAK VEIL APRS icon parity & aircraft heading

- Bundles the **ten original SVG APRS artworks** from XTAK VEIL v0.4.0-r50 Node Map, unchanged, under `assets/veil-aprs-r50`.
- Ports r50's exact APRS category resolver (weather, digipeater, emergency, aircraft, marine, vehicle, portable, object, base, generic) using source APRS symbol information, with original station SSID fallback behavior. These are VEIL r50 **category icons**, not a 192-symbol APRS atlas. The Node Map itself uses those ten categories.
- Displays these original icons in TAK Map Leaflet and Cesium, with original icon pixel sizes (38 px for base/weather/digipeater; 40 px otherwise) and dark label styling.
- Carries `aprs_symbol` from VEIL UDP CoT as before, and preserves native r50 Live SA `identity.symbol`, `symbolTable`, and weather/object metadata in authenticated API snapshots/events. Duplicate selection may fill missing metadata from a fresh same-canonical-object observation without overriding an explicit winning symbol.
- VEIL ADS-B uses the original ADSBx silhouettes, white fill, **1 px black non-scaling stroke**, and retained 43.2 px display size. Aircraft rotation reads VEIL r50 `motion.courseDeg` and `tak.track.courseDeg` (and prior compatible fields); 0° is valid; last live heading is retained briefly when updates omit it. The existing 2D and 3D aircraft renderers share the visual SVG.
- Keeps source-specific AIS, Remote ID, built-in ADS-B, pairing, Range Rings, token mesh, saved objects, and installed configuration unchanged. No VEIL radio settings modified.
- Validation includes pure normalization, metadata selection, 2D/3D icon source parity, heading changes, and ZIP installation permissions. Live node testing should confirm final appearance.
