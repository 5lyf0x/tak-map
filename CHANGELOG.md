# Changelog

## 1.4.0-i618

- Promotes TAK Map to public version 1.4.0 with iteration i618.
- Adds one shared content-aware width policy for ADS-B, Local Data, Data Sync, Gateway Data, dynamic Source Extension, and other shared context panels.
- Keeps compact panels narrow and expands long-content panels only as needed within responsive limits.
- Reserves the themed scrollbar gutter so content and headers do not shift when vertical scrolling becomes active.
- Prevents horizontal scrolling and wraps long source values cleanly.
- Preserves ADS-B left/right docking and prevents dual-panel overlap by sizing each panel independently within the map viewport.
- Keeps context panels above ordinary map controls and below true top-level modals.
- Updates product/version markers, cache keys, installation instructions, release notes, troubleshooting guidance, and context-panel documentation.

## 1.3.0-i617

- Mounts read-only Gateway Data context panels in a top-level overlay above the main map toolbar while preserving top-level modal priority.
- Adds a TAK Map-themed vertical scrollbar, fixed context header, responsive wider panel, and fully reachable long content.
- NWS affected areas now show three entries initially, use `Show all N areas`, render every parsed area when expanded, and change to `Show fewer`.
- USGS earthquake Review is labeled Status; Alert and Source program rows are removed.
- USGS title/location distances and Depth use regional units consistently.

## 1.3.0-i616

- Raises the read-only Gateway Data context panel above the main map toolbar while keeping top-level modals above it.
- Removes duplicate object titles from Gateway Data context content.
- Restricts NWS context content to source-provided alert fields, formats semicolon-delimited affected areas as a concise vertical list, and hides generated merge/geometry/internal-ID diagnostics.
- Replaces generated NIFC and USGS Details paragraphs with concise structured source fields.
- Expands NIFC `WF` and prescribed-fire codes to `Wildfire` and `Prescribed Fire`.
- Removes USGS distance-from-center and event-status fields.
- Preserves the i615 read-only/no-flicker context mode and all validated i614/i613/i612/i611/i610/i602 behavior.

## 1.3.0-i615

- Adds a dedicated read-only Gateway Data context mode rather than reusing Local Data shape editing UI.
- Removes Gateway Data edit/delete controls, style swatches, ownership warnings, Local Data labels, and animated edit-state accents.
- Uses friendly Gateway Data source names in the context header and updates selected details in place only when values change.
- Preserves all validated i614 geometry/context behavior and prior Source Extension, ADS-B, and Data Sync functionality.

## 1.3.0-i614

- Routes every Gateway Data point, line, polygon, and multi-geometry object into the existing right-side contextual details panel instead of a floating Leaflet popup.
- Adds subtle, non-animated Gateway Data selection emphasis and clears it cleanly with context/source/Replay lifecycle changes.
- Curates dynamic Source Extension details to important operator-facing values while hiding internal and low-value metadata.
- Preserves validated i613 Source Extension drawing/EUD suppression, i612 deferred runtime, i611 dynamic local-ingest controls, i610 ADS-B behavior, and protected i602 Data Sync behavior.

## 1.3.0-i613

- Suppresses live representative-point EUD markers for Source Extension `u-d-f` drawing events while retaining their authoritative Gateway Data line/polygon geometry.
- Excludes Source Extension data objects from the EUD device list without suppressing legitimate Point Source Extension records from the live CoT path.
- Preserves the validated i612 deferred Gateway Data runtime, dynamic source toggles, MultiPolygon rendering, i610 ADS-B behavior, and protected i602 Data Sync implementation.

# TAK Map changelog

## 1.3.0-i612

- Replaces the stale i523 Gateway Data implementation embedded in the deferred startup manifest with the exact current i612 runtime.
- Restores dynamic Source Extension discovery and MultiPolygon rendering through normal TAK Map startup.
- Changes the deferred manifest cache-busting version to i612.
- Adds full-startup manifest/browser regression coverage and an exact embedded-versus-external runtime parity check.
- Preserves i611 local Source Extension ingest behavior, i610 ADS-B behavior, and the protected i602 Data Sync runtime.


## 1.3.0-i611

- Adds dynamic TAK Gateway Source Extension discovery to the existing Gateway Data card.
- Adds per-extension TAK Map-local ingest toggles that default off for newly discovered sources.
- Clears disabled-source objects and skips future snapshots locally without changing the Source Extension state in TAK Gateway.
- Persists local ingest preferences by stable source key and restores them when a known source returns.
- Adds dynamic source labels, counts, geometry-aware icons, sorting, popup names, master visibility, Replay suppression, and add/remove reconciliation.
- Adds MultiLineString and MultiPolygon rendering support for dynamic Gateway Data sources.
- Preserves i610 ADS-B behavior and the protected i602 Data Sync runtime.


## 1.3.0-i610

- Dock the secondary ADS-B context panel in the bottom-right of the map viewport with the same 12-pixel edge inset as the primary bottom-left panel.
- Keep both ADS-B panels above the map toolbar and preserve all i609 ADS-B behavior.
- Preserve the validated i602 Data Sync backend and protected runtime files unchanged.

## 1.3.0-i608

- Opens live ADS-B aircraft details in a dedicated left-side panel above the map toolbar.
- Adds aircraft-panel pinning; a pinned aircraft remains live on the left while other objects use the normal right-side context panel and a second aircraft can open on the right.
- Keeps ADS-B interpolation state, tracked history, follow state, and pinned-panel data advancing through a background worker when the tab is inactive, then renders the current position on return.
- Adds Airplanes.live emitter category A7 as a high-confidence rotorcraft signal while preserving existing aircraft-type evidence.
- Uses the same resolved aircraft type for the sidebar Type chip and fixed-wing/rotorcraft map icon, including live reclassification.
- Preserves i607 full-history Save Trail behavior and the validated i602 Data Sync implementation without modification.

## 1.3.0-i607

- Added the validated ADS-B-specific right-sidebar renderer from the i606 live test patch.
- Raised the ADS-B contextual sidebar above the right-side toolbar.
- Preserved continuous full-history trail recording across Save Trail actions.
- Prevented the transient ADS-B trail from duplicating the already-saved Local Data route by rendering only the unsaved continuation after save.
- Preserved the i602 Data Sync implementation unchanged.
