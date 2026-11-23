# TAK Map i696 — offline validation

**Basis:** fresh extraction of exact i695 source ZIP; application changes applied from individually zero-fuzz-validated staged patches, with new i696 NOAA history backend and browser controller. No installed TAK Map server or real GPU was accessible from this builder.

- `scripts/test_radar_history_i696.py`: 14 targeted strict catalog/window/opaque ID/tile/cache regression assertions PASS.
- `scripts/test_radar_history_i696_browser.py`: headless Chromium Play/Pause, buffering, timeline, step, speed/loop, LIVE, narrow layout, ON/OFF checks PASS.
- `scripts/test_weather_radar_i693.py`: 8 legacy live NOAA proxy tests PASS.
- `scripts/test_weather_browser_i693.py` and `scripts/test_weather_browser_i692.py`: headless UI/alerts/2D/3D regression PASS (i693 fixture updated to emit real Leaflet `load` after tile batch as required for safe frame handoff).
- `scripts/test_i696_imported_basemap_stack_browser.py`: 8 imported basemap catalog scenarios PASS.
- 2D basemap/radar combined browser regression: layer z-order, provider URL changes, tile failure alerts, weather overlay isolation and last-good recovery PASS.
- `scripts/test_ui_i695.py`: Infrastructure typography/detail actions, radar slider legacy migration PASS (outdated pre-cache-source presence assertion removed for i696).
- `scripts/test_tool_ux_v486_browser.py`: route/measure tool interactions PASS.
- Python AST syntax, active JavaScript Node syntax, install.sh syntax, ZIP CRC and SHA256SUMS, clean extraction comparison to be finalized at packaging.

**Release gates pending on user's server:** actual NOAA history frame-to-mosaic correspondence and precipitation motion vs NOAA; user's 2D basemap tile endpoints; GPU/3D flyover performance; real NDM SQLite data/datum; service startup smoke check.
