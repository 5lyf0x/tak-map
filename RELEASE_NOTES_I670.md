# TAK Map v1.4.0-i670 — Original ADSBx aircraft icons for XTAK VEIL

- Replaces the unsatisfactory i669 A3 target-ring art for VEIL ADS-B with authentic original aircraft silhouette SVG path geometry from ADS-B Exchange tar1090.
- Bundles **30 exact upstream SVG silhouettes**, including A319/A320/A321, A330/A350/A380, B737/B738/B739, C-130, F/A-18, several helicopters, regional/general-aviation/jet families, and unknown fallback.
- Includes **all 376 original ICAO type-code mappings** from the checked upstream markers.js; mapping to a shape not among the 30 bundled entries falls back to a broad original silhouette with explicit non-exact status. This is NOT the complete upstream 93-shape set.
- Type is selected from explicitly supplied/verified VEIL enrichment metadata, never from callsign guesses. Missing types use original ADSBx generic artwork.
- Category colors, live heading rotation, 2D/3D source parity, HAE altitude placement, and built-in ADS-B details/tracking panel remain as in i669.
- Vendor source at assets/vendor/adsbx, see NOTICE.md for GPL-2-or-later and third-party C-130 CC BY 4.0 credits. No proprietary Kendo assets bundled.
- No changes to VEIL node subscription, credentials, network transports, Range Rings, or existing saved content.
- Still requires real aircraft/VEIL-node and hardware terrain verification after installation.
