# TAK Map v1.4.0-i695 — Pending interface improvements

**Based on:** exact `tak-map-v1.4.0-i694.zip` source and approved combined i695 staged patch. **Scope:** UI reliability and readability, not a new weather data source.

## Included

1. **INFRASTRUCTURE header toggle:** The header Show/Hide switch is installed both for newly created cards and existing older in-page headers. Collapsing the card remains independent; master OFF hides 2D/3D graphics without deleting or disabling individual layers. Saved state retains `takmap.infra.visible.i694` for backward compatibility.
2. **Sidebar headers:** All 13 top-level sidebar card title families use matching Infrastructure typography, expanded and collapsed (Manrope/system-ui, 12px/800, .06em, uppercase). Badges and controls are excluded.
3. **Weather radar opacity:** Existing and new weather panels use the BASEMAP Soft Pill control, with percent label beside the track. The old radar range node and redundant styling are migrated/removed. Opacity changes update current and buffering 2D/3D radar alpha without reloading tiles and preserve the i691 preference key.
4. **Infrastructure object inspector:** GIS Attributes precede the action row; Zoom to Object, Copy Coordinates and Export Object remain functional at the bottom of the panel.
5. **Basemap Pre-cache:** Legacy automatic prefetch timers/queues and their UI were removed; normal on-demand basemap tiles, caching, user-imported basemaps and OFFLINE MAPS remain untouched.
6. **Infrastructure legibility:** Category headings use **Extended Divider / Manrope / weight 550 / 14px / .01em**. Individual layer names use **Clear Type / 12.5px / weight 750**, and displayed/available counts appear on the same first row with a 12px horizontal gap. Count text styling and dynamic computations remain unchanged.
7. **Version and browser cache bust:** HTML version labels and query strings updated to i695; installer checks modified runtime assets.

## Explicitly not included

**Phase 3 radar-history animation:** Planned separately, but mandatory provider history feasibility tests against real NOAA historical tiles remain unverified. This release does not claim historical playback. The i693 partial radar coverage issue also remains subject to live verification on the TAK Map host.

## Installation

Transfer the complete ZIP to `~/Downloads`. Extract into a fresh `~/Downloads/tak-map-v1.4.0-i695` source directory and run `sudo ./install.sh` there. Do not overwrite extracted i694 source. The installer should preserve `/var/lib/tak-map` data/configuration. Keep i694 as rollback until the installed GUI and live radar are verified.

## Remaining live checks

Confirm the master Infrastructure switch appears on already-existing cards, does not change individual layer toggles, sidebar title weights match expanded/collapsed, weather slider matches basemap track and does not reload radar tiles, details actions are at bottom, pre-cache controls do not reappear, and category/layer title readability at narrow widths. No production host was available to this build environment.
