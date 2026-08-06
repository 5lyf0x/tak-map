#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / 'tak_dashboard.py'
RUNTIME = (ROOT / 'assets' / 'tak-map-milstd2525c-i538.js').read_text(encoding='utf-8')

assert 'new MutationObserver' not in RUNTIME, 'whole-document observer returned'
assert "forceDataSyncSync('i538-symbol-catalog-loaded')" not in RUNTIME
assert "dispatchEvent(new CustomEvent('takmap:milstd-catalog-ready'" in RUNTIME

spec = importlib.util.spec_from_file_location('tak_dashboard_i538_test', DASH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)

# A /cot or /euds cache miss must not synchronously invoke Data Sync.
calls = {'count': 0}
original = mod.tak_map_data_sync
def counted():
    calls['count'] += 1
    return original()
mod.tak_map_data_sync = counted
mod._I537_REQUEST_CONTEXT.identity_key = 'startup-test-user'
mod._I537_MISSION_UID_CACHE.pop('startup-test-user', None)
assert mod._i537_cached_mission_uids() == set()
assert calls['count'] == 0, calls

# Generic CoT symbol fallback is cached rather than scanning the catalog per marker.
mod._I538_SIDC_ICON_CACHE.clear()
first = mod._i537_icon_for_sidc('SFGPU----------')
assert 'SFGPU----------' in mod._I538_SIDC_ICON_CACHE
start = time.perf_counter()
for _ in range(20000):
    assert mod._i537_icon_for_sidc('SFGPU----------') is first
elapsed = time.perf_counter() - start
assert elapsed < 0.35, elapsed

# Final HTML loads only the startup-safe runtime.
assert 'takMapMilStd2525CLoaderI538' in mod.TAK_MAP_HTML
assert 'takMapMilStd2525CLoaderI537' not in mod.TAK_MAP_HTML
assert mod.TAK_MAP_ITERATION == 'i538'
print(f'i538 startup hotfix tests passed; 20k cached generic SIDC lookups in {elapsed:.4f}s')
