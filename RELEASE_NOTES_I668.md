# TAK Map v1.4.0-i668 — Release notes

## XTAK VEIL Phase 3

- Strict exact-ID VEIL display reconciliation across multiple nodes (validated ICAO24, MMSI, qualified APRS, typed stable Remote ID); preserves original node observations and displays source provenance in the VEIL popup.
- A Settings option to merge duplicate targets with TAK Map ADS-B and Gateway AIS is provided **disabled by default**. Cross-source suppression is conservative: only exact verified IDs with a visible, fresh native marker. Native data sources and settings are not changed. This feature remains experimental until live source verification.
- XTAK VEIL node **Details** shows connection, read-only health, and observation details when explicitly API subscribed and authenticated. Health information comes from VEIL r50 `/api/v1/health`, sanitized and limited; `Not reported` appears for unavailable fields. UDP-only and disabled nodes don't trigger authentication.
- Master toggle, four-gate automatic login rule, optional saved credentials, and UDP fallback stay unchanged.

## Route details

- The contextual sidebar for owned local saved routes shows **Edit | Delete** side by side in one equal-width row with the same existing edit and delete handlers.

## Compatibility and validation limits

- Maintains i667 Cesium route/shape/icon overlays, saved-route labels, i666 Phase 2 and i665 blank-page fix.
- Automated Python + JS broker/mock and Chromium page tests verify contracts, but live Pi/VEIL multi-node operation and physical ADS-B/Gateway AIS source interoperability require on-device confirmation.
- No application data or configuration is reset, no privileged VEIL remote management is introduced.
