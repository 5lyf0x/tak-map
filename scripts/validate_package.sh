#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
run_step(){ local label="$1" limit="$2"; shift 2; echo "[i659] ${label}"; timeout --foreground --signal=TERM --kill-after=20s "$limit" "$@"; }
run_step "i656 release identity / installer contract" 180s python3 scripts/test_release_i654.py
run_step "i655 NDM refresh and conditional autostart" 180s python3 scripts/test_i655_registration_startup.py
run_step "i655 delayed map readiness and Roads default" 180s python3 scripts/test_i655_delayed_map_browser.py
run_step "i654 Valhalla nearest-road backend" 180s env PYTHONWARNINGS='ignore::SyntaxWarning' python3 scripts/test_route_snap_i654.py
run_step "i657 direct resolved-route save contract" 120s python3 scripts/test_route_save_i656_contract.py
run_step "i657 actual Save Route dialog and snapping regression" 240s python3 scripts/test_i657_route_save_dialog_browser.py
run_step "i659 saved-route editor and production popup interactions" 240s python3 scripts/test_i659_saved_route_editor_browser.py
run_step "i659 safe in-place route update backend" 180s env PYTHONWARNINGS='ignore::SyntaxWarning' python3 scripts/test_i659_route_update_backend.py
run_step "i658 production deferred/inline save, live preview, selector recovery and per-leg labels" 240s python3 scripts/test_i658_production_route_browser.py
run_step "i656 lossless snapped-route save and editor" 240s python3 scripts/test_route_editor_i654_browser.py
run_step "i654 route editor JavaScript syntax" 120s node --check assets/tak-map-route-editor-i654.js
run_step "i653 retained NDM quota fixes under i654" 180s env PYTHONWARNINGS='ignore::SyntaxWarning' python3 scripts/test_release_i653.py
run_step "i652 Tools-card NDM modal retained release contract" 180s env PYTHONWARNINGS='ignore::SyntaxWarning' python3 scripts/test_release_i652.py
run_step "i653 NDM server-side no-quota and 4 GiB upload contracts" 180s env PYTHONWARNINGS='ignore::SyntaxWarning' python3 scripts/test_ndm_limits_i653.py
run_step "i653 NDM 4 GiB upload Chromium behavior" 180s python3 scripts/test_ndm_limits_i653_browser.py
run_step "i651 NDM and Valhalla new backend tests" 180s env PYTHONWARNINGS='ignore::SyntaxWarning' python3 scripts/test_ndm_i651.py
run_step "i652 Tools-card NDM modal effective HTML and asset route" 180s env PYTHONWARNINGS='ignore::SyntaxWarning' python3 scripts/test_ndm_tools_modal_i652_backend.py
run_step "i652 Tools-card NDM modal Chromium interaction" 180s python3 scripts/test_ndm_tools_modal_i652_browser.py
run_step "i652 NDM modal JavaScript syntax" 120s node --check assets/tak-map-ndm-data-i652.js
run_step "i651 NDM HTTP auth and catalog routes" 180s env PYTHONWARNINGS='ignore::SyntaxWarning' python3 scripts/test_ndm_i651_backend.py
run_step "i651 native Valhalla installer pinned-wheel security" 120s python3 scripts/test_valhalla_installer_i651.py
run_step "i651 release/install/API identity" 180s env PYTHONWARNINGS='ignore::SyntaxWarning' python3 scripts/test_release_i651.py
run_step "i650 inherited release/runtime/install contract" 120s python3 scripts/test_release_i650.py
run_step "i649 retained AIS artwork and Nginx origin proxy" 120s python3 scripts/test_ais_artwork_and_nginx_i649.py
run_step "i650 inherited shadow and owner source contracts" 120s python3 scripts/test_selection_shadows_i650.py
run_step "i648 inherited ADS-B selection and owner browser regression" 180s python3 scripts/test_adsb_sidebar_i647_browser.py
run_step "i648 MIL-STD-2525C renderer and AIS priority" 120s node scripts/test_milstd2525c_no_shadow_i648.cjs
run_step "i648 MIL-STD-2525C SVG and Chromium shadow checks" 240s python3 scripts/test_milstd2525c_no_shadow_i648_browser.py
run_step "i649 registry-only tactical symbology (source and deferred)" 120s node scripts/test_registry_only_tactical_i649.cjs
run_step "i649 universal AIS neutral classification" 120s node scripts/test_gateway_ais_universal_i649.cjs
run_step "i649 Gateway AIS neutral symbols" 120s node scripts/test_gateway_ais_neutral_symbols_next.cjs
run_step "i650 AIS blank tactical icon fallback contract" 120s node scripts/test_ais_blank_fallback_i650.cjs
run_step "i650 Cert Setup backend security" 180s env PYTHONWARNINGS='ignore::SyntaxWarning' python3 scripts/test_cert_setup_i650_backend.py
run_step "i650 Cert Setup browser UI" 180s python3 scripts/test_cert_setup_i650_browser.py
run_step "i650 live map search backend asset routing" 180s env PYTHONWARNINGS='ignore::SyntaxWarning' python3 scripts/test_general_map_live_search_i650_backend.py
run_step "i650 live map search Chromium integration" 180s python3 scripts/test_general_map_live_search_i650_browser.py
run_step "i643 inherited Shape release contract" 120s python3 scripts/test_release_i643.py
run_step "i643 native Shape Save + center translation + persistent edit browser regression" 240s python3 scripts/test_shape_context_i643_browser.py
run_step "i643 native Mission Shape transport/association/read-back backend contract" 180s env PYTHONWARNINGS='ignore::SyntaxWarning' python3 scripts/test_shape_save_i643_backend.py
run_step "i639 native Shape raw CoT/UID/Mission/style preservation under i643 transaction" 180s env PYTHONWARNINGS='ignore::SyntaxWarning' python3 scripts/test_shape_edit_i639_backend.py
run_step "canonical TAK shape codec + legacy readers + exact Mission delete readback + Mission-only server invariant" 300s env PYTHONWARNINGS='ignore::SyntaxWarning' python3 scripts/test_release_i636.py
run_step "browser shape rendering: closed/open geometry + TAK style" 240s python3 scripts/test_shape_renderer_i636_browser.py
run_step "persistent per-user card states inherited from i635" 240s python3 scripts/test_card_state_i636_browser.py
run_step "ADS-B i633 failover/cadence/hard-OFF inherited regression" 240s env PYTHONWARNINGS='ignore::SyntaxWarning' python3 scripts/test_adsb_failover_i637_inherited.py
run_step "OTS 1.7.13 configure/login/trust inherited regression" 300s env PYTHONWARNINGS='ignore::SyntaxWarning' python3 scripts/test_configure_ots_i637_inherited.py
run_step "Data Sync exact deletion identity inherited regression" 600s env PYTHONWARNINGS='ignore::SyntaxWarning' python3 scripts/test_data_sync_deletion_identity_i602.py
run_step "Gateway Data + Replay optional certificate authentication" 180s python3 scripts/test_gateway_optional_certificate.py
run_step "i645 Gateway Configure backend" 180s python3 scripts/test_gateway_config_i645.py
run_step "i645 Gateway Configure UI" 180s python3 scripts/test_gateway_config_i645_browser.py
run_step "backend Python compilation" 300s env PYTHONWARNINGS='ignore::SyntaxWarning' python3 -m py_compile tak_dashboard.py scripts/test_release_i643.py scripts/test_gateway_optional_certificate.py scripts/test_shape_context_i643_browser.py scripts/test_shape_save_i643_backend.py scripts/test_shape_edit_i639_backend.py
run_step "context runtime JavaScript syntax" 120s node --check assets/tak-map-context-sidebar-i572.js
run_step "context sizing/package JavaScript syntax" 120s node --check assets/tak-map-package-i580.js
run_step "i636 shape runtime JavaScript syntax" 120s node --check assets/tak-map-i636.js
run_step "i645 Gateway Configure JavaScript syntax" 120s node --check assets/tak-map-gateway-config-i645.js
run_step "i650 Cert Setup JavaScript syntax" 120s node --check assets/tak-map-cert-setup-i650.js
run_step "i650 general live search JavaScript syntax" 120s node --check assets/tak-map-live-search-i650.js
run_step "i650 live ADS-B sidebar JavaScript syntax" 120s node --check assets/tak-map-adsb-sidebar-i610.js
run_step "i650 Gateway Data JavaScript syntax" 120s node --check assets/tak-map-gateway-data-v491.js
run_step "startup JavaScript syntax" 120s node --check assets/tak-map-startup-i553.js
run_step "deferred manifest identity/count" 120s python3 -c "import json; p=json.load(open('assets/tak-map-deferred-i553.json')); assert p['version']=='1.4.0-i659'; assert p['count']==len(p['scripts'])"
run_step "installer shell syntax" 120s bash -n install.sh
run_step "uninstaller shell syntax" 120s bash -n uninstall.sh
echo "TAK Map 1.4.0-i659 validation passed"
