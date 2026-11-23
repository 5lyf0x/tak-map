# TAK Map i003 — Source regression suite

`python3 scripts/test_offline_perf_i003.py` covers authenticated GET tile requests, TMS/XYZ orientation, imported override, partial tile resume, missing/invalid zoom, concurrent pooled reads, catalog invalidation and file hash preservation.

`python3 scripts/test_offline_perf_i003_browser.py` covers actual core map entries, native zoom/generation URLs, imported Tile rows selection/save, and the offline-vs-online Leaflet pan/buffer settings.

The inherited source tests remain present: `scripts/test_offline_pack_i001.py`, `scripts/test_offline_pack_i001_browser.py`, `scripts/test_offline_pack_i002_startup.py`, `scripts/test_offline_i698.py`, `scripts/test_offline_i698_browser.py`, `scripts/test_offline_card_i699_browser.py`, `scripts/test_basemap_prefs_i699.py`, `scripts/test_basemap_prefs_i699_api.py`, `scripts/test_basemap_prefs_i699_browser.py`.

Synthetic comparison performed outside the source release: 200 serial tile lookups on one fixture; i002 reopened SQLite/reparsed catalog 200/200, i003 opened once/parsed once. The comparison does not represent real-device or network latency.
