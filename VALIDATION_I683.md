# TAK Map v1.4.0-i683 — Offline release validation

**Baseline:** complete, unmodified `tak-map-v1.4.0-i682.zip` release source plus two targeted i682 hotfix patches and the approved i683 elevation profile UI/lifecycle. The existing TAK Map data and configuration paths are unchanged. This is a source archive, not an installed server or compiled application binary.

## Implemented features

- MVUM toolbar auto-creation and replacement after route-toolbar reconstruction; vector fallback tile reprojection, consistent line weight, no full-layer redraw after tile errors, HiDPI.
- Route Elevation compact default: 580px floating viewport-constrained draggable panel, 82px chart, thin color key, route distance in the right header, Expand and Close controls independent of the drag handle.
- Extended elevation: six metrics, five elevation ticks, detailed graph, terrain-quality metadata, full-route and steep-detail views.
- Real NDM terrain-derived 15°/25°/35° grading, numbered contiguous ≥35° slope runs, popup details in feet with grade, direction, elevation change and route mile; marker clicks zoom the extended profile into the corresponding run.
- Route lifecycle: only show during Route Creation/editing or explicit selection of a saved route; auto-close on exit/deselect/non-route object; X hides entire panel and dismissal persists until the next deliberate interaction/session.
- Preserve every i682 Local Data session-persistence and Basemap Blend selection fix.

## Offline validation performed

- Python package, persistence and regression suites: **39 passed** (`tests.test_i683_release`, `tests.test_i681`, `tests.test_i682_release`, `tests.test_i682_local_data_persistence`, `tests.test_i680_local_data_recovery`, `tests.test_i679_full_route_persistence`, `tests.test_i673`).
- Chromium integration (`test_i683_elevation_profile_browser.py`): compact default, half-height graph, popup run lengths in feet, click-to-detail, grab/grabbing drag, save position, route-only selection state, X behavior, viewport boundary clamps: **passed**.
- Chromium legacy elevation regression (`test_elevation_profile_ui_browser.py`): close X, exit/new session, saved route, 45° grading and 40,000-sample performance: **passed**.
- Chromium lower Basemap Blend selections (`test_i682_basemap_blend_browser.py`): seven selections including lower custom modes, label/render/persistence: **passed**.
- Node MVUM (`test_mvum_button.cjs`, `mvum_rendering_regression.cjs`): toolbar lifecycle, vector reprojection, no raster amplification, redraw restraint: **passed**.
- Node Local Data hydration (`test_i682_frontend_hydration.cjs`): **five checks passed**.
- Python AST, Node syntax of modified JS, Bash syntax of installer: **passed**.
- ZIP integrity, fresh extraction, full member bytewise comparison and exclusion of temporary outputs: checked during final packaging.

## Limitations

- No SSH/live deployment to the TAK server, no access to the user's actual elevation tiles, and no real on-host route selections or NDM network traffic. Observed field behavior may differ from the browser mocks; confirm with a real saved route after installation.
- Short steep runs require sufficient DEM resolution. The angle calculation is an estimated terrain grade, not a surveyed or legally drivable trail grade.
- The initial saved position is viewport-constrained. The browser profile position preference is not written to the server and survives normal closing/reopening in that browser.
- Back up `/var/lib/tak-map/tak_map_imports/` before an upgrade. No storage migration or destructive cleanup is included.
