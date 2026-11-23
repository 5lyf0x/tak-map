# TAK Map v1.4.0-i689 — Infrastructure interaction and asset reliability

**Baseline:** v1.4.0-i688 · **Rollback:** v1.4.0-i688 · **Package:** Full source-only upgrade.

## Included changes

1. **Infrastructure minimum-zoom control:** Replaces the Windows/Chromium native popup with a TAK Map dark listbox. Uses a slim (~5 px) scrollbar, Manrope text, selected-row highlighting, scroll-to-current, auto-flip when near the window bottom, keyboard support (arrows, Home/End, Page Up/Down, Enter, Escape, Tab) and click-away dismissal. Existing per-layer `layer-minzoom` API and persisted values remain unchanged. Background status polling does not re-create the control.
2. **Safe delayed map initialization:** Infrastructure validates a candidate Leaflet map before registering listeners. A temporary `window.map` HTML element is ignored. On map replacement, old handlers are unbound before new ones are registered. Initial disabled/collapsed/offline layer hydration and search continue when the map becomes ready.
3. **More reliable Infrastructure feature selection:** Event ownership explicitly marks handled DOM clicks, preventing the same map click from immediately deselecting a feature. The invisible 5px-per-side line selection hit stroke is stacked behind visible geometry; per-feature hit identity distinguishes duplicate original IDs. Clicked features open the existing right-hand Object Details without hover tooltips. Selected lines retain configured color plus the existing 2px red outline.
4. **Point Icon Registry fallbacks:** Failed icon image requests show a colored circle fallback in Leaflet while retaining the point's click handler. Cesium point entities include a colored pickable fallback point behind selected registry artwork. Icon Registry picker thumbnails now request lazy-decoded images rather than eagerly loading large icon grids, reducing peak simultaneous image demand.
5. **Sidebar static asset delivery:** The i684 sidebar-order JS and uniform CSS now have explicit authenticated `/assets/runtime/` routes (plus compatible old URL aliases) with correct MIME types, no-store headers, nosniff and exact GET/HEAD content lengths. Missing sidebar runtime files return real HTTP 404 instead of falling through to the main HTML. i689 Infrastructure JS and CSS have equivalent explicit handlers.
6. **Token Mesh map validation:** Its browser-side map object refresh waits for a valid Leaflet map reference, avoiding the `addLayer is not a function` error when the DOM element is exposed before the Leaflet map exists. Existing Token Mesh storage and sync behavior are unchanged.

## Persistence and compatibility

- Infrastructure remains **offline-only**, with optional explicit user-initiated downloads and existing GIS import/export formats. No automatic online streaming is reintroduced.
- No Infrastructure database migration in i689. Existing downloaded/imported features, categories, filters, colors, icon references, minimum zooms, search index and user-owned Local Data are preserved.
- Keeps prior viewport+50% buffer, 5,000-feature display safeguard, indexed Infrastructure search, 36-inch sewer defaults and selected-object red outline.
- The Icon Registry backend was exercised using a known-good local icon and a small concurrent HTTP test; its full live reverse-proxy 502 behavior has **not** been reproduced or resolved against the user's server. Lazy loading and browser-side marker fallbacks mitigate failure without asserting backend repair.

## Release validation

- 50 Python regression tests + 28 subtests passed (Infrastructure, Local Data persistence/recovery, i689 HTTP routing).
- i689 Chromium mock-map regression passed at desktop 1280px and narrow 390px widths: delayed map publication, event ownership and deselection, registry fallback markup, 24-value styled zoom listbox and value persistence.
- Historical i688 and i687 Infrastructure browser tests passed independently at desktop and mobile widths.
- Real local HTTP handler verified GET and HEAD exact JS/CSS bytes, correct MIME, i689 HTML asset references, missing-sidebar-asset 404 and known icon rendering under small concurrent load.
- Code syntax, installer syntax, ZIP integrity, clean fresh extraction and byte-for-byte source equality performed at package handoff; see `VALIDATION_I689.md`.

**Live server verification is still required** for real imported-layer click targets with full Leaflet/Cesium, the user's HTTPS reverse proxy, and the production Icon Registry HTTP 502 reports.
