# Validation — TAK Map v1.4.0-i686

## Source-level and synthetic integration testing

- Python: four i686 backend tests passed, covering non-destructive database schema migration, validated color persistence, unchanged GIS export of more than 5,000 records, bounded online queries, and downloaded source color inheritance.
- Chromium: 1280 px and 390 px interactive Infrastructure smoke tests passed. Exercised four simultaneous origin-specific map layers, multi-open category state, 1.5x viewport bboxes, dateline/polar bounds, `visible / total stored` counters, persistent per-layer HEX style controls, immediate 3D material updates, master origin visibility, direct Object Details, and management tab switching without requerying or deselection.
- Existing i685 Infrastructure backend and browser smoke tests, i682 Local Data persistence, i680 recovery, i679 route persistence, and selected i683/i684 browser/regression test modules passed in the combined 31-test/8-subtest run.
- Dense SQLite synthetic point fixture, same machine: 5,001 stored -> 5,000 displayed in ~0.11 s; 50,000 stored -> 5,000 displayed in ~0.15 s; 250,000 stored -> 5,000 displayed in ~0.62 s. All reported the LIMITED state. These are local measurements, not real LA County provider throughput guarantees.
- `node --check` and Python compilation passed for i686 assets; complete application import reports iteration i686, only i686 infrastructure runtime JS/CSS and release config.

## Release gates

- Source-only ZIP CRC, file inventory, SHA-256, executable installer flag, full fresh-extraction byte-level comparison, and preservation of baseline archive files are validated during package construction.
- Installation, real third-party provider paging, and Cesium map performance on the user's TAK Map host were **not** tested. A production backup is recommended before installing.
