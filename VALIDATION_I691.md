# TAK Map v1.4.0-i691 — Build validation

## Source baseline

- Source package: `tak-map-v1.4.0-i690(1).zip` from user's Library.
- New iteration: `1.4.0-i691`.
- Source added: `assets/tak-map-weather-i691.js`, `assets/tak-map-weather-i691.css`, release notes and this validation report.
- Source changed: `tak_dashboard.py`, `takmap.js`, `assets/tak-map-basemap-stack-i673.js`, `install.sh`, `VERSION`, `README.md`.

## Passed offline checks

- Python `py_compile` for `tak_dashboard.py` — pass (pre-existing historical JS-in-Python deprecation warnings are emitted by parser, not a new syntax fault).
- `node --check` for `takmap.js`, `assets/tak-map-basemap-stack-i673.js`, `assets/tak-map-weather-i691.js` — pass.
- `bash -n install.sh` — pass.
- Module load: reports version `1.4.0-i691` — pass. i537 emits an unrelated asset warning in this test container because the host `/usr/share/tak-server-dash/mil2525/icons.json` is absent.
- Rendered `TAK_MAP_HTML` inspected with an HTML parser: neither `reliefOverlayToggle`, `reliefOpacity`, `reliefOverlayButtonV506`, nor `.relief-controls` remain as DOM elements — pass.
- New JS/CSS references in generated HTML — pass.
- Synthetic upstream fixture: NOAA WMS GetCapabilities parser detects MRMS layer and advertised time — pass.
- Synthetic upstream fixture: NWS geometryless alert preserved without invented polygon — pass.
- Installer includes both new weather assets and required-asset installation gate — pass.
- ZIP test CRC, unique names, version marker, source-byte comparison, fresh extraction and byte-comparison — pass.

## Not certified in this environment

- Live weather provider request/response behavior, remote WMS tile rendering/CORS, and timing metadata.
- Real Leaflet and Cesium map interactions in the user's installed browser.
- End-to-end real terrain, map route editing, alert polygon click isolation, and server reboot/rollback.
- No actual installed TAK Map data/configuration is present here. Installer's data preservation is inherited from the i690 source and not exercise-tested on the host.

## Known phase deferrals

- NOAA radar time animation and GOES satellite layer are out of scope.
- 3D alert attributes are rendered through the default Cesium GeoJSON entity path, not an i691-specific details popup.

**Release classification:** source-built and offline validated; deployment/live-provider acceptance testing remains required.
