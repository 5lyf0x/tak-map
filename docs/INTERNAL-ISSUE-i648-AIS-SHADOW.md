# AIS shadow correction (staged for next build)

In i647, `pointIcon(feature)` invoked `milPointIcon(feature)` before testing the AIS source. AIS features carrying CoT/SIDC metadata therefore took the generic 48x48 MIL marker path, whose `.tak-icon-wrap` inherited a global black drop shadow.

The staged change checks `src === "ais_vessels"` first, uses the established 12x12 `ais-civil.png` or `ais-law.png` asset and transparent wrapper, and preserves selected-only red glow. The non-AIS MIL path is unchanged.

This is **not** a release package. Version identity and i647 ZIP remain untouched until a new build is explicitly requested.
