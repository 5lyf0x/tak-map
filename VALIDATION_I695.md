# TAK Map v1.4.0-i695 — Offline source/package validation

**Baseline:** exact `tak-map-v1.4.0-i694.zip` (SHA-256 `0b60630eb1d3ab9529e1abb68b7c7f58dcd6eec88bd0a5e6f3bab6781b731306`). Original i694 SHA256SUMS verified before editing.

## Source and compatibility

- **PASS:** Approved combined staged i695 patch applied to exact i694 files without fuzz or rejects.
- **PASS:** No existing i694 source files removed; modified and added filenames compared with baseline.
- **PASS:** Version marker, final HTTP-app config and HTML cache-busting set to i695.
- **PASS:** Installer deploys modified Infrastructure, weather and sidebar-theme assets, and checks them in its runtime gate.
- **PASS:** Existing Infrastructure layer choices, master visibility preference (`takmap.infra.visible.i694`), weather opacity/alert preference (`tak-map-native-weather-i691`) and NWS alerts were not migrated destructively.
- **PASS:** Normal basemap tiling, on-demand cache and OFFLINE MAPS preserved; obsolete automatic background Basemap Pre-cache code/UI removed.

## Automated tests

- **PASS:** Node.js syntax for active Infrastructure and weather JavaScript and all modified browser scripts.
- **PASS:** Python compilation of changed server and test scripts; original historic embedded-JavaScript escape warnings are nonfatal.
- **PASS:** `bash -n install.sh`.
- **PASS:** Eight i693 radar backend fixtures (retries, frames, provider errors, validity, concurrent fetches).
- **PASS:** i693 Chromium radar regression covering viewport tile recovery, frame handoff, alerts and 2D/3D.
- **PASS:** i694 Chromium UI regression covering sidebar ordering, Infrastructure master toggle, 12 Blend modes/outside dismissal and radar alpha without fetch.
- **PASS:** i695 Chromium UI regression at 820/400/340px verifies Extended Divider / Manrope 550/14px/.01em, Clear Type 12.5px/750, on-row 12px count spacing without overflow, action-buttons-after-attributes, legacy weather card slider migration and 2D/3D opacity without network fetch.
- **PASS:** Prior targeted i695 staging browser tests covered old Infrastructure header repair, category and detail layouts, and legacy Basemap Pre-cache removal.

## Source archive checks

- **PASS:** ZIP CRC.
- **PASS:** SHA256SUMS includes every source file exactly once and matches source and fresh extraction.
- **PASS:** Fresh extraction filenames, sizes and SHA-256 bytes match final packaged source.
- **PASS:** No new compiled cache, binaries, private outputs or generated test artifacts packaged.

## Limitations

- TAK Map was not installed on the user's server from this environment; real GIS and NOAA/NWS requests were not exercised.
- **Phase 3 radar animation is not in i695**: its separate plan requires a real-provider history feasibility probe, and no verified historical imagery was accessible here. Nothing in the UI claims the feature exists.
- Keep i694 available for rollback until the new master visibility switch, layering typography, radar slider, and Infrastructure actions are live-verified.
