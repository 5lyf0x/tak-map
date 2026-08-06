#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
run_step(){ local label="$1" limit="$2"; shift 2; echo "[i618] ${label}"; timeout --foreground --signal=TERM --kill-after=20s "$limit" "$@"; }
run_step "release, docs, shared sizing, and protected hashes" 240s python3 scripts/test_release_i618.py
run_step "Python compilation" 300s python3 -m py_compile tak_dashboard.py \
  scripts/test_release_i618.py \
  scripts/test_context_panel_sizing_i618_browser.py \
  scripts/test_gateway_data_deferred_runtime_i618.py \
  scripts/test_gateway_data_dynamic_sources_i618.py \
  scripts/test_gateway_data_dynamic_sources_i618_browser.py \
  scripts/test_gateway_data_context_sidebar_i618_browser.py \
  scripts/test_gateway_data_full_startup_i618_browser.py \
  scripts/test_source_extension_drawing_eud_filter_i613.py
run_step "Shared package/sizing JavaScript syntax" 120s node --check assets/tak-map-package-i580.js
run_step "Gateway Data JavaScript syntax" 120s node --check assets/tak-map-gateway-data-v491.js
run_step "Context sidebar JavaScript syntax" 120s node --check assets/tak-map-context-sidebar-i572.js
run_step "ADS-B JavaScript syntax" 120s node --check assets/tak-map-adsb-sidebar-i610.js
run_step "Startup JavaScript syntax" 120s node --check assets/tak-map-startup-i553.js
run_step "Deferred manifest JSON" 120s python3 -c "import json; p=json.load(open('assets/tak-map-deferred-i553.json')); assert p['version']=='1.4.0-i618'; assert p['count']==len(p['scripts'])"
run_step "Installer shell syntax" 120s bash -n install.sh
run_step "Uninstaller shell syntax" 120s bash -n uninstall.sh
run_step "Authoritative deferred Gateway Data i618 contract" 120s python3 scripts/test_gateway_data_deferred_runtime_i618.py
run_step "Dynamic Source Extension i618 static contract" 120s python3 scripts/test_gateway_data_dynamic_sources_i618.py
run_step "Shared all-context dynamic sizing browser workflow" 300s python3 scripts/test_context_panel_sizing_i618_browser.py
run_step "Dynamic Source Extension i618 lifecycle browser workflow" 240s python3 scripts/test_gateway_data_dynamic_sources_i618_browser.py
run_step "Gateway Data context content/scroll/unit workflow" 300s python3 scripts/test_gateway_data_context_sidebar_i618_browser.py
run_step "Full deferred-startup dynamic MultiPolygon workflow" 300s python3 scripts/test_gateway_data_full_startup_i618_browser.py
run_step "Source Extension drawing/EUD suppression" 240s env PYTHONWARNINGS='ignore::SyntaxWarning' python3 scripts/test_source_extension_drawing_eud_filter_i613.py
run_step "Gateway Data large geometry workflow" 240s python3 scripts/test_gateway_data_geometry_i518_browser.py
run_step "Gateway Data AIS icon contract" 180s python3 scripts/test_gateway_data_ais_icons_i618.py
run_step "NWS Gateway Data style contract" 120s python3 scripts/test_nws_style_i519.py
run_step "ADS-B browser workflow" 300s python3 scripts/test_adsb_sidebar_i610_browser.py
run_step "i602 deletion identity regression" 600s env PYTHONWARNINGS='ignore::SyntaxWarning' python3 scripts/test_data_sync_deletion_identity_i602.py
echo "TAK Map 1.4.0 i618 shared context sizing, i617 curated Gateway Data, i613 EUD suppression, i612 deferred runtime, i611 Source Extensions, i610 ADS-B, and i602 Data Sync validation passed"
