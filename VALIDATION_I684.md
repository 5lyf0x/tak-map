# TAK Map i684 — Offline validation

## Scope
Baseline is the exact v1.4.0-i683 release ZIP. No direct live-host access; no installation or production-state mutation was performed.

## Passing regression tests
- Python unittest suites: i681/i682/i683 release and i679/i680/i682 Local Data persistence/recovery: **31 passed**.
- Chromium real component: Object Details route selection opens profile for a 1,625-point feature; non-route/deselect/X behavior correct.
- Chromium route edit: two Edit → Cancel cycles; first via the actual Cancel button, second via controller; numbered draft waypoint markers and draft distance labels removed, no late redraw.
- Chromium Route Details: no displayed Points row; seven route properties and user notes appear on separate text-safe lines.
- Chromium sidebar: matching neutral card background; heading and chip typography/geometry parity; VEIL/Mesh toggle alignment, both 1280px and 390px widths; Satellite Tracking precedes Offline Maps.
- Chromium elevation profile: default compact / 82px graph, extended reduced graph (188px), 35°+ hover details in feet, draggable header, X dismissal and selection rules.
- JavaScript node: client hydration/visibility (5 checks), MVUM native vector rendering/high-DPI/no full redraw, MVUM toolbar mount/late init, MVT edge rasterizer.
- Chromium Basemap Blend: seven mode selections including lower options, persistence and displayed labels.
- `node --check` for edited/new JavaScript; `python -m py_compile` for backend.

## Package gates
- No original i683 archive members removed.
- ZIP CRC, unique/safe member paths and clean-source screening validated.
- Fresh `unzip` extraction checked byte-for-byte against staged source, including executable `install.sh`.
- Current version identity i684 and loader cache tokens i684.
- Local Data catalog remains in original persistent location; no migrations, upgrades or cleanup performed during build.

## Known limitation
Offline tests use fixtures and mocked map APIs, not the real 10.10.10.101 production TAK Map instance or a live NDM server. Validate route editing cancellation and sidebar appearance after installation. Existing source contains pre-existing Python invalid-escape SyntaxWarnings; compilation still succeeds.
