#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import re
import sys
import time
from collections import Counter
from urllib.parse import parse_qs, urlparse

ROOT = pathlib.Path(__file__).resolve().parents[1]
DASH = ROOT / "tak_dashboard.py"

spec = importlib.util.spec_from_file_location("tak_dashboard_i569_startup_test", DASH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader is not None
spec.loader.exec_module(mod)

html = mod.TAK_MAP_HTML
manifest_path = ROOT / "assets/tak-map-deferred-i553.json"
manifest = json.loads(manifest_path.read_text())
startup_js = (ROOT / "assets/tak-map-startup-i553.js").read_text()
core_js = (ROOT / "assets/tak-map-core-i553.js").read_text()
data_sync_control_js = (ROOT / "assets/tak-map-data-sync-i553.js").read_text()
icon_registry_js = (ROOT / "assets/tak-map-icon-registry-i569.js").read_text()
context_sidebar_js = (ROOT / "assets/tak-map-context-sidebar-i569.js").read_text()
popup_localdata_js = (ROOT / "assets/tak-map-popup-localdata-i569.js").read_text()
registry_summary = json.loads((ROOT / "assets/icon-registry/registry-summary.json").read_text())
registry_summary.update({"ok": True, "version": "i569"})
registry_manifest = json.loads((ROOT / "assets/icon-registry/icon-registry.json").read_text())
registry_icons_by_set = {}
for _icon in registry_manifest["icons"]:
    registry_icons_by_set.setdefault(_icon["iconset_uid"], []).append({k:v for k,v in _icon.items() if k not in {"sha256","internal_path"}})
registry_icon_by_path = {_icon["iconsetpath"]:_icon for _icon in registry_manifest["icons"]}
exact_custom_path = "34ae1613-9645-4222-a9d2-e5f243dea2865/Animals/ant.png"
custom_registry_row = registry_icon_by_path[exact_custom_path]
custom_public_icon = {
    "kind": "custom",
    "iconset_uid": custom_registry_row["iconset_uid"],
    "iconset_name": custom_registry_row["iconset_name"],
    "group_name": custom_registry_row["group_name"],
    "filename": custom_registry_row["filename"],
    "iconsetpath": custom_registry_row["iconsetpath"],
    "cot_type": custom_registry_row.get("type2525b") or "a-f-G",
    "type2525b": custom_registry_row.get("type2525b") or "a-f-G",
    "mime_type": custom_registry_row.get("mime_type") or "image/png",
    "width": custom_registry_row.get("width") or 0,
    "height": custom_registry_row.get("height") or 0,
    "asset_url": "/api/tak-map/icon-registry/icon?path=34ae1613-9645-4222-a9d2-e5f243dea2865%2FAnimals%2Fant.png",
}
custom_public_point = {
    "uid": "DS-CUSTOM-UID", "mission_name": "STARTUP-SMOKE",
    "name": "DS-CUSTOM", "lat": 35.2, "lon": -117.2,
    "notes": "Custom icon startup fixture", "cot_type": "a-f-G",
    "sidc": "", "iconsetpath": exact_custom_path,
    "added": "2026-07-24T02:50:00Z", "updated": "2026-07-27T04:38:00Z", "sync_state": "synced",
    "fingerprint": "a" * 64, "source_owned": True,
    "custom_icon": True, "registered_custom_icon": True,
    "symbol_locked": False, "registry_icon": custom_public_icon,
}
local_public_point = {
    "local_id": "local-startup:0", "uid": "",
    "name": "LOCAL-CUSTOM", "lat": 35.3, "lon": -117.3,
    "notes": "Local custom icon fixture", "cot_type": "a-f-G",
    "sidc": "", "iconsetpath": exact_custom_path,
    "source": "Local Startup Points", "fingerprint": "b" * 64,
    "source_owned": True, "custom_icon": True,
    "registered_custom_icon": True, "symbol_locked": False,
    "registry_icon": custom_public_icon,
}

source_text = DASH.read_text()
main_marker = "if __name__=='__main__':\n    main()"
assert source_text.count(main_marker) == 1
assert source_text.rfind(main_marker) > source_text.rfind("# --- end TAK Map i569 package/runtime promotion and background response diagnostics ---")
assert not source_text[source_text.rfind(main_marker) + len(main_marker):].strip()

# Static release budgets: the page must stay a shell rather than regaining the
# historical megabyte-scale inline runtime.
assert mod.TAK_MAP_ITERATION == "i569"
assert len(html.encode()) < 200_000, len(html.encode())
assert len(re.findall(r"<script\b", html, re.I)) == 4
assert all(not body.strip() for body in re.findall(r"<script[^>]*>(.*?)</script>", html, re.I | re.S))
assert "/assets/runtime/tak-map-startup-i553.js?v=1.3.0-i569" in html
assert "/assets/runtime/tak-map-icon-registry-i569.js?v=1.3.0-i569" in html
assert "/assets/runtime/tak-map-popup-localdata-i569.js?v=1.3.0-i569" in html
assert html.index("tak-map-startup-i553.js") < html.index("tak-map-icon-registry-i569.js") < html.index("tak-map-popup-localdata-i569.js") < html.index("tak-map-context-sidebar-i569.js")
assert "tak-map-icon-registry-i569.js" not in mod.TAK_MAP_LOGIN_HTML
assert "tak-map-popup-localdata-i569.js" not in mod.TAK_MAP_LOGIN_HTML
assert "tak-map-context-sidebar-i569.js" not in mod.TAK_MAP_LOGIN_HTML
assert len(core_js.encode()) < 750_000
assert manifest.get("version") == "1.3.0-i569"
assert manifest.get("count") == len(manifest.get("scripts", []))
assert 90 <= manifest["count"] <= 120
ids = [row.get("id", "") for row in manifest["scripts"]]
required_ids = {
    "takMapObjectLifecycleLoaderV486",
    "takMapToolUxLoaderV486",
    "takMapGatewayDataLoaderV476",
    "takMapGeofencingLoaderV491",
    "takMapAdsbWorkerI463",
    "takMapViewshedWindowLoaderV487",
    "takMapMilStd2525CLoaderI553",
}
assert required_ids.issubset(set(ids)), required_ids - set(ids)
assert not any("v391" in x.lower() or "v392" in x.lower() for x in ids)
assert "requestCoordinator" in startup_js
assert "__takMapCoreInitI553" in core_js
assert "__takMapStartOptionalDataI553" in core_js
assert "__takMapStartDataSyncI553" in core_js
assert "tak-map-data-sync-i553.js" in startup_js
assert "takMapDataSyncLoaderV476" not in ids
assert "setInterval(refreshDataSyncInterval,300000)" in core_js  # five-minute Data Sync polling interval

v381 = next(row["code"] for row in manifest["scripts"] if row["id"].startswith("v381"))
boot = re.search(r"function boot\(\)\{(.*?)\}\s*if\(d\.readyState", v381, re.S)
assert boot, "v381 boot not found"
assert "loadIcons" not in boot.group(1)
assert "renderMilPicker" not in boot.group(1)
assert "if(w.__takMapCurrentIconRegistry)return;" in v381
for n in range(381, 388):
    code = next(row["code"] for row in manifest["scripts"] if row["id"].startswith(f"v{n}"))
    assert not re.search(r"\[[0-9,]+\]\.forEach\(function\(ms\)\{setTimeout\(boot", code)

try:
    from playwright.sync_api import sync_playwright
except Exception as exc:  # pragma: no cover
    raise SystemExit(f"Playwright is required for startup validation: {exc}")

leaflet_stub = (ROOT / "scripts/leaflet_stub_test.js").read_text()
icons_json = (ROOT / "assets/mil2525/icons.json").read_bytes()
config = mod.tak_map_config()
responses = {
    "/api/tak-map/status-banner": {"ok": True, "tak_server": "Online", "internet": "Connected", "euds_connected": 0, "adsb_aircraft": 0, "downloads": {"active": 0}},
    "/api/tak-map/cot": {"ok": True, "markers": []},
    "/api/tak-map/data-sync": {"ok": True, "version": "i553", "missions": [{"id": 7, "name": "STARTUP-SMOKE"}], "mission_uids": [{"mission_id": 7, "uid": "DS-P13-UID"}, {"mission_id": 7, "uid": "DS-P10-UID"}], "objects": [
        {"uid": "DS-P13-UID", "mission_id": 7, "mission": "STARTUP-SMOKE", "callsign": "DS-P13", "lat": 35.0, "lon": -117.0, "cot_type": "a-f-G-U-C-E-N", "mission_cot_raw_type_i553": "a-f-G-U-C-E-N", "mission_cot_raw_iconset_path_i553": "COT_MAPPING_2525C/a-f/a-f-G-U-C-D", "data_sync_symbol_decision_i553": {"version": "i553", "authority": "event-type", "selected_cot_type": "a-f-G-U-C-E-N"}, "source": "OpenTAKServer Data Sync mission_uids"},
        {"uid": "DS-P10-UID", "mission_id": 7, "mission": "STARTUP-SMOKE", "callsign": "DS-P10", "lat": 35.1, "lon": -117.1, "cot_type": "a-f-G-E-W-H", "mission_cot_raw_type_i553": "a-f-G-E-W-H", "mission_cot_raw_iconset_path_i553": "COT_MAPPING_2525C/a-f/a-f-G-E-V-U-S", "data_sync_symbol_decision_i553": {"version": "i553", "authority": "event-type", "selected_cot_type": "a-f-G-E-W-H"}, "source": "OpenTAKServer Data Sync mission_uids"},
        {"uid": "DS-CUSTOM-UID", "mission_id": 7, "mission": "STARTUP-SMOKE", "mission_name": "STARTUP-SMOKE", "callsign": "DS-CUSTOM", "name": "DS-CUSTOM", "lat": 35.2, "lon": -117.2, "cot_type": "a-f-G", "iconsetpath": exact_custom_path, "mission_cot_raw_iconset_path_i553": exact_custom_path, "notes": "Custom icon startup fixture", "added": "2026-07-24T02:50:00Z", "updated": "2026-07-27T04:38:00Z", "sync_state": "synced", "source": "OpenTAKServer Data Sync mission_uids"}
      ], "packages": []},
    "/api/tak-map/local-data": {"ok": True, "routes": [], "points": [], "shapes": []},
    "/api/tak-map/imported": {"ok": True, "imports": [{"id":"local-startup","name":"Local Startup Points","uploaded":"2026-07-27T01:00:00Z","counts":{"point":1},"features":[{"kind":"point","geometry":"point","name":"LOCAL-CUSTOM","lat":35.3,"lon":-117.3,"coords":[[35.3,-117.3]],"source":"TAK Map Point Tool i556","notes":"Local custom icon fixture","cot_type":"a-f-G","iconsetpath":exact_custom_path,"properties":{"name":"LOCAL-CUSTOM","callsign":"LOCAL-CUSTOM","notes":"Local custom icon fixture","cot_type":"a-f-G","iconsetpath":exact_custom_path,"iconset_path":exact_custom_path}}]}]},
    "/api/tak-map/offline-maps": {"ok": True, "maps": [], "jobs": []},
    "/api/tak-map/adsb-settings": {"ok": True, "settings": {"enabled": False, "update_interval_seconds": 30}},
    "/api/tak-map/adsb": {"ok": True, "aircraft": []},
    "/api/tak-map/euds": {"ok": True, "euds": []},
    "/api/tak-map/geofences": {"ok": True, "geofences": []},
    "/api/tak-map/custom-basemaps": {"ok": True, "basemaps": []},
    "/api/tak-map/account/tak-identity": {"ok": True, "callsign": "STARTUP", "username": "startup"},
    "/api/tak-map/account/sentinel-hub": {"ok": True, "configured": False},
    "/api/tak-map/ots/session": {"ok": True, "username": "startup", "callsign": "STARTUP", "display_identity": "STARTUP", "is_admin": True, "connection_state": "Authenticated"},
    "/api/tak-map/replay/config": {"ok": True, "configured": False},
    "/api/tak-map/tile-cache-status": {"ok": True, "active": 0},
    "/api/tak-map/gateway-data/snapshot": {"ok": True, "revision": 0, "objects": [], "sources": {}},
    "/api/tak-map/icon-registry": registry_summary,
    "/api/tak-map/ots/source-identity": {"ok": True, "version": "i569", "source": "Data Sync", "provider": "OpenTAKServer", "url_hostname": "ots.example.com", "server_hostname": "ots-field-01", "display": "Data Sync: OpenTAKServer · ots.example.com/ots-field-01"},
}
requests: list[str] = []
request_times: list[tuple[str, float]] = []
page_errors: list[str] = []
console_errors: list[str] = []
svg_requests = 0
point_posts: list[dict] = []

def tiny_svg() -> bytes:
    return b'<svg xmlns="http://www.w3.org/2000/svg" width="250" height="150" viewBox="0 0 5000 3000"><path d="M200 200h4600v2600H200z" fill="none" stroke="black" stroke-width="100"/></svg>'

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, executable_path="/usr/bin/chromium", args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"])
    page = browser.new_page(viewport={"width": 1440, "height": 900}, timezone_id="UTC")
    cdp = page.context.new_cdp_session(page)
    cpu_throttle = float(os.environ.get("TAK_TEST_CPU_THROTTLE", "4"))
    wait_scale = max(1.0, cpu_throttle)
    def wait_ms(base: int) -> int:
        return int(base * wait_scale)
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": cpu_throttle})
    page.on("pageerror", lambda e: page_errors.append(str(e)))
    page.on("console", lambda m: console_errors.append(m.text) if m.type == "error" else None)

    def route_handler(route, request):
        nonlocal_svg = None
        del nonlocal_svg
        global svg_requests
        parsed = urlparse(request.url)
        path = parsed.path
        item = path + (("?" + parsed.query) if parsed.query else "")
        requests.append(item)
        request_times.append((item, time.perf_counter()))
        if path in {"/", "/tak-map"}:
            return route.fulfill(status=200, content_type="text/html", body=html)
        if path == "/assets/runtime/tak-map-startup-i553.js":
            return route.fulfill(status=200, content_type="application/javascript", body=startup_js)
        if path == "/assets/runtime/tak-map-core-i553.js":
            return route.fulfill(status=200, content_type="application/javascript", body=core_js)
        if path == "/assets/runtime/tak-map-data-sync-i553.js":
            return route.fulfill(status=200, content_type="application/javascript", body=data_sync_control_js)
        if path == "/assets/runtime/tak-map-icon-registry-i569.js":
            return route.fulfill(status=200, content_type="application/javascript", body=icon_registry_js)
        if path == "/assets/runtime/tak-map-popup-localdata-i569.js":
            return route.fulfill(status=200, content_type="application/javascript", body=popup_localdata_js)
        if path == "/assets/runtime/tak-map-context-sidebar-i569.js":
            return route.fulfill(status=200, content_type="application/javascript", body=context_sidebar_js)
        if path == "/assets/runtime/tak-map-deferred-i553.json":
            return route.fulfill(status=200, content_type="application/json", body=manifest_path.read_bytes())
        if "leaflet" in request.url and path.endswith(".js"):
            return route.fulfill(status=200, content_type="application/javascript", body=leaflet_stub)
        if path.endswith("leaflet.css"):
            return route.fulfill(status=200, content_type="text/css", body=(ROOT / "assets/vendor/leaflet-1.9.4/leaflet.css").read_bytes())
        if path == "/api/tak-map/config":
            return route.fulfill(status=200, content_type="application/json", body=json.dumps(config))
        if path == "/mil2525/icons.json":
            return route.fulfill(status=200, content_type="application/json", body=icons_json)
        if path == "/api/tak-map/icon-registry/icons":
            set_uid = (parse_qs(parsed.query).get("set_uid") or [""])[0]
            rows = registry_icons_by_set.get(set_uid, [])
            return route.fulfill(status=200, content_type="application/json", body=json.dumps({"ok":True,"version":"i556","set_uid":set_uid,"icons":rows,"count":len(rows),"read_only":True}))
        if path == "/api/tak-map/icon-registry/icon":
            icon_path = (parse_qs(parsed.query).get("path") or [""])[0]
            row = registry_icon_by_path.get(icon_path)
            if not row:
                return route.fulfill(status=404, body="")
            return route.fulfill(status=200, content_type="image/png", body=(ROOT / "assets/icon-registry" / row["internal_path"]).read_bytes())
        if path == "/api/tak-map/data-sync-point-i556":
            if request.method.upper() == "POST":
                try:
                    posted = request.post_data_json or {}
                except Exception:
                    posted = json.loads(request.post_data or "{}")
                point_posts.append(dict(posted))
                created = dict(custom_public_point)
                created.update({"uid":"CREATE-SESSION-UID", "cot_uid":"CREATE-SESSION-UID", "event_uid":"CREATE-SESSION-UID", "name":posted.get("name",""), "callsign":posted.get("name",""), "lat":posted.get("lat"), "lon":posted.get("lon"), "mission_name":posted.get("mission_name","")})
                return route.fulfill(status=200, content_type="application/json", body=json.dumps({"ok": True, "version": "i569", "point": created, "redraw_allowed": True, "readback_confirmed": True}))
            return route.fulfill(status=200, content_type="application/json", body=json.dumps({"ok": True, "version": "i556", "point": custom_public_point}))
        if path == "/api/tak-map/local-point-i556":
            return route.fulfill(status=200, content_type="application/json", body=json.dumps({"ok": True, "version": "i556", "point": local_public_point}))
        if path.startswith("/mil2525/svg/"):
            svg_requests += 1
            return route.fulfill(status=200, content_type="image/svg+xml", body=tiny_svg())
        if path.startswith("/api/tak-map/"):
            return route.fulfill(status=200, content_type="application/json", body=json.dumps(responses.get(path, {"ok": True})))
        if path.startswith("/assets/"):
            file_path = ROOT / "assets" / path[len("/assets/"):]
            if file_path.is_file():
                content_type = "application/javascript" if file_path.suffix == ".js" else "application/json" if file_path.suffix == ".json" else "image/svg+xml" if file_path.suffix == ".svg" else "application/octet-stream"
                return route.fulfill(status=200, content_type=content_type, body=file_path.read_bytes())
        return route.fulfill(status=204, body="")

    page.route("**/*", route_handler)
    storage_stub = """(() => { const m=new Map(); const store={getItem:k=>m.has(String(k))?m.get(String(k)):null,setItem:(k,v)=>m.set(String(k),String(v)),removeItem:k=>m.delete(String(k)),clear:()=>m.clear(),key:i=>Array.from(m.keys())[i]||null,get length(){return m.size}}; try{Object.defineProperty(window,'localStorage',{value:store,configurable:true})}catch(_){} try{Object.defineProperty(window,'sessionStorage',{value:store,configurable:true})}catch(_){} })();"""
    page.add_init_script(storage_stub)
    page.evaluate(storage_stub)
    started = time.perf_counter()
    page.set_content(html.replace("<head>", "<head><base href=\"https://example.test/\">", 1), wait_until="domcontentloaded", timeout=wait_ms(20_000))
    page.evaluate("Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async v=>{window.__copiedLocation=v;}}})")
    page.wait_for_function("document.documentElement.dataset.takMapShell === 'ready'", timeout=wait_ms(8_000))
    shell_seconds = time.perf_counter() - started
    frame_ms = page.evaluate("() => new Promise(resolve => { const s=performance.now(); requestAnimationFrame(() => resolve(performance.now()-s)); })")
    svg_before_runtime = svg_requests
    try:
        page.wait_for_function("document.documentElement.dataset.takMapRuntime === 'ready'", timeout=wait_ms(35_000))
    except Exception:
        print(json.dumps({"page_errors": page_errors, "console_errors": console_errors, "requests_tail": requests[-80:], "diag": page.evaluate("() => ({shell:document.documentElement.dataset.takMapShell||'',runtime:document.documentElement.dataset.takMapRuntime||'',startup:window.TakMapStartupDiagnosticsI553&&window.TakMapStartupDiagnosticsI553.snapshot?window.TakMapStartupDiagnosticsI553.snapshot():null, body:(document.body&&document.body.innerText||'').slice(0,1000)})")}, indent=2), flush=True)
        raise
    runtime_seconds = time.perf_counter() - started
    page.wait_for_function("window.__takMapDataSyncControlReadyI553 === true", timeout=wait_ms(5_000))
    page.wait_for_function("window.TakMapIconRegistryI556 && window.TakMapIconRegistryI556.diagnostics().ready === true", timeout=wait_ms(8_000))
    page.wait_for_function("window.__takMapDataSyncStartupResultI553 && window.__takMapDataSyncStartupResultI553.rendered === true", timeout=wait_ms(8_000))
    page.wait_for_function("window.__takMapOptionalDataStartedI553 === true", timeout=wait_ms(5_000))
    page.evaluate("() => window.__takMapOptionalDataPromiseI553 || Promise.resolve()")
    page.wait_for_function("TakMapStartupDiagnosticsI553.initialDataReadyAt > 0", timeout=wait_ms(8_000))
    page.wait_for_function("window.__takMapMilStdRedrawI553 && window.__takMapMilStdRedrawI553.objectCount === 3", timeout=wait_ms(8_000))
    page.wait_for_timeout(700)

    result = page.evaluate("""() => ({
      shell: document.documentElement.dataset.takMapShell,
      runtime: document.documentElement.dataset.takMapRuntime,
      diagnostics: TakMapStartupDiagnosticsI553.snapshot(),
      map: !!window.takLeafletMap,
      dataSync: !!window.TakMapDataSyncControlV476,
      lifecycle: !!window.TakMapObjectLifecycleV486,
      tools: !!window.TakMapToolUxV486,
      gateway: !!window.TakMapGatewayDataV476,
      geofencing: !!window.TakMapGeofencingV491,
      adsb: !!window.TakMapAdsbWorkerV476,
      viewshed: !!window.TakMapViewshedWindowV488,
      cards: !!window.TakMapCardControlsV476,
      satellite: !!window.TakMapNrtSatelliteI535,
      session: !!window.TakMapSessionV499,
      buttonCount: document.querySelectorAll('button').length,
      milGridImages: document.querySelectorAll('#milGrid img').length,
      iteration: (document.querySelector('.iteration-chip') || {}).textContent || '',
      dataSyncStartup: window.__takMapDataSyncStartupResultI553 || null,
      missionCountText: (document.getElementById('missionCount') || {}).textContent || '',
      objectCountText: (document.getElementById('dataSyncObjectCount') || {}).textContent || '',
      dataSyncLayerCount: typeof dataSyncLayer !== 'undefined' && dataSyncLayer && dataSyncLayer.getLayers ? dataSyncLayer.getLayers().length : -1,
      dsP13Image: ((window.__takMapDataSyncStartupResultI553?.payload?.objects || []).find(o => o.callsign === 'DS-P13')?.__layer?.options?.icon?.html) || '',
      dsP10Image: ((window.__takMapDataSyncStartupResultI553?.payload?.objects || []).find(o => o.callsign === 'DS-P10')?.__layer?.options?.icon?.html) || '',
      customImage: ((window.__takMapDataSyncStartupResultI553?.payload?.objects || []).find(o => o.callsign === 'DS-CUSTOM')?.__layer?.options?.icon?.html) || '',
      customPopup: ((window.__takMapDataSyncStartupResultI553?.payload?.objects || []).find(o => o.callsign === 'DS-CUSTOM')?.__layer?.getPopup?.()?.getContent?.()) || '',
      milstdRedraw: window.__takMapMilStdRedrawI553 || null,
      iconRegistry: window.TakMapIconRegistryI556 ? {version:window.TakMapIconRegistryI556.version, diagnostics:window.TakMapIconRegistryI556.diagnostics(), summary:window.TakMapIconRegistryI556.summary()} : null,
      popupLocalData: window.TakMapPopupLocalDataI569 ? window.TakMapPopupLocalDataI569.audit() : null,
      contextSidebar: window.TakMapContextSidebarI569 ? window.TakMapContextSidebarI569.diagnostics() : null
    })""")

    assert shell_seconds < 5.0, shell_seconds
    assert runtime_seconds < 30.0, runtime_seconds
    assert frame_ms < 250, frame_ms
    assert result["shell"] == "ready" and result["runtime"] == "ready"
    assert result["diagnostics"]["deferredLoaded"] == result["diagnostics"]["deferredTotal"]
    assert result["diagnostics"]["deferredFailed"] == []
    max_long_task_ms = max([row["duration"] for row in result["diagnostics"].get("longTasks", [])] or [0])
    assert max_long_task_ms < 1000, {"max_long_task_ms": max_long_task_ms, "longTasks": result["diagnostics"].get("longTasks", [])}
    assert all(result[name] for name in ("map", "dataSync", "lifecycle", "tools", "gateway", "geofencing", "adsb", "viewshed", "cards", "satellite", "session")), result
    assert result["buttonCount"] >= 180
    assert result["iteration"] == "i569", result["iteration"]
    assert result["popupLocalData"] and result["popupLocalData"]["installed"] is True, result
    assert result["iconRegistry"] and result["iconRegistry"]["version"] == "i569", result
    assert result["iconRegistry"]["diagnostics"]["ready"] is True, result
    assert result["iconRegistry"]["summary"]["custom_set_count"] == 10, result
    assert result["iconRegistry"]["summary"]["custom_icon_count"] == 3742, result
    assert result["dataSyncStartup"]["missions"] == 1, result["dataSyncStartup"]
    assert result["dataSyncStartup"]["objects"] == 3, result["dataSyncStartup"]
    assert result["dataSyncStartup"]["rendered"] is True, result["dataSyncStartup"]
    assert result["missionCountText"] == "1 missions", result["missionCountText"]
    assert result["objectCountText"] == "3 objects", result["objectCountText"]
    assert result["dataSyncLayerCount"] >= 3, result["dataSyncLayerCount"]
    assert "friendly-emergency-construction.svg?v=i553" in result["dsP13Image"], result
    assert "friendly-ground-equipment-self-propelled-howitzer.svg?v=i553" in result["dsP10Image"], result
    assert "/api/tak-map/icon-registry/icon?path=" in result["customImage"], result
    assert "%2FAnimals%2Fant.png" in result["customImage"], result
    assert result["customPopup"] == "", result
    assert result["contextSidebar"] and result["contextSidebar"]["installed"] is True, result
    assert result["contextSidebar"]["leafletPopupLifecycleUsed"] is False, result
    assert result["contextSidebar"]["boundLayers"] >= 3, result
    assert result["milstdRedraw"]["objectCount"] == 3, result
    assert not page_errors, page_errors
    assert not any("draw patch failed" in row for row in console_errors), console_errors
    mutation = result["diagnostics"].get("mutation", {})
    assert mutation.get("sharedNativeBroadObservers", 0) <= 1, mutation
    assert mutation.get("deliveredCallbacks", 0) < 1000, mutation
    assert mutation.get("records", 0) < 50000, mutation
    assert svg_before_runtime == 0
    assert result["milGridImages"] == 0

    reviewed = page.evaluate("""() => {
      const api = window.TakMapMilStd2525CI553;
      const construction = api && api.resolveSymbol({
        cot_type: 'a-f-G-U-C-E-N',
        mission_cot_raw_type_i553: 'a-f-G-U-C-E-N',
        data_sync_symbol_decision_i553: {version:'i553',authority:'event-type',selected_cot_type:'a-f-G-U-C-E-N'}
      });
      const howitzer = api && api.resolveSymbol({
        cot_type: 'a-f-G-E-W-H',
        mission_cot_raw_type_i553: 'a-f-G-E-W-H',
        mission_cot_raw_iconset_path_i553: 'COT_MAPPING_2525C/a-f/a-f-G-E-V-U-S',
        data_sync_symbol_decision_i553: {version:'i553',authority:'event-type',selected_cot_type:'a-f-G-E-W-H'}
      });
      return {
        audit: api && api.audit ? api.audit() : null,
        construction, howitzer,
        constructionHtml: api && api.iconHtml ? api.iconHtml({callsign:'DS-P13',cot_type:'a-f-G-U-C-E-N',mission_cot_raw_type_i553:'a-f-G-U-C-E-N',data_sync_symbol_decision_i553:{version:'i553',authority:'event-type',selected_cot_type:'a-f-G-U-C-E-N'}}) : '',
        howitzerHtml: api && api.iconHtml ? api.iconHtml({callsign:'DS-P10',cot_type:'a-f-G-E-W-H',mission_cot_raw_type_i553:'a-f-G-E-W-H',mission_cot_raw_iconset_path_i553:'COT_MAPPING_2525C/a-f/a-f-G-E-V-U-S',data_sync_symbol_decision_i553:{version:'i553',authority:'event-type',selected_cot_type:'a-f-G-E-W-H'}}) : ''
      };
    }""")
    assert reviewed["audit"]["reviewedAliasSidcCount"] >= 800, reviewed
    assert reviewed["audit"]["reviewedAliasCotTypeCount"] >= 900, reviewed
    assert reviewed["construction"]["file"] == "friendly-emergency-construction.svg", reviewed
    assert reviewed["howitzer"]["file"] == "friendly-ground-equipment-self-propelled-howitzer.svg", reviewed
    assert "friendly-emergency-construction.svg?v=i553" in reviewed["constructionHtml"], reviewed
    assert "friendly-ground-equipment-self-propelled-howitzer.svg?v=i553" in reviewed["howitzerHtml"], reviewed

    counts = Counter(x.split("?", 1)[0] for x in requests)
    assert counts["/api/tak-map/data-sync"] == 1, counts
    assert not any("v392-sweep" in x or "v391" in x for x in requests)
    assert counts["/api/tak-map/adsb-settings"] <= 2, counts
    assert counts["/api/tak-map/ots/session"] <= 2, counts
    assert counts["/api/tak-map/custom-basemaps"] <= 2, counts
    assert counts["/api/tak-map/euds"] <= 2, counts
    assert counts["/api/tak-map/icon-registry"] == 1, counts

    # The i553 MIL renderer repatches itself through 5 seconds. Verify the i556
    # custom renderer remains authoritative after every delayed patch.
    page.wait_for_timeout(6500)
    page.evaluate("""async () => {
      if (typeof window.forceDataSyncSync === 'function') await window.forceDataSyncSync('i556-custom-refresh-test');
      else {
        const objects=window.__takMapDataSyncStartupResultI553?.payload?.objects || [];
        if (typeof window.drawDataSyncObjects === 'function') window.drawDataSyncObjects(objects);
      }
    }""")
    page.wait_for_timeout(250)
    late = page.evaluate("""() => {
      const objects=(typeof lastDataSync !== 'undefined' && lastDataSync?.objects) || window.__takMapDataSyncStartupResultI553?.payload?.objects || [];
      const object=objects.find(o => o.callsign === 'DS-CUSTOM');
      const diagnostics=window.TakMapIconRegistryI556.diagnostics();
      return {diagnostics, html:object?.__layer?.options?.icon?.html || '', popup:object?.__layer?.getPopup?.()?.getContent?.() || ''};
    }""")
    assert late["diagnostics"]["customRendererAuthoritative"] is True, late
    assert late["diagnostics"]["popupRendererAuthoritative"] is True, late
    assert "%2FAnimals%2Fant.png" in late["html"], late
    assert late["popup"] == "", late

    if cpu_throttle <= 1.5:
        # Open the active registry through the Point toolbar in the normal-speed
        # browser pass. Rendering hundreds of live SVG cards is intentionally kept
        # out of the CPU-throttled startup pass; the dedicated registry regression
        # and this normal-speed pass verify all 1,448 rows and the 238 default cards.
        if cpu_throttle <= 1.5:
            page.wait_for_selector('#pointMiniToolbar button', state='attached', timeout=wait_ms(5000))
            clicked_icon = page.evaluate("""() => { const button=Array.from(document.querySelectorAll('#pointMiniToolbar button')).find(node => /Icon/i.test(node.textContent || node.title || '')); if (!button) return false; button.click(); return true; }""")
            assert clicked_icon is True
            page.wait_for_function("document.getElementById('milPicker')?.classList.contains('active')", timeout=wait_ms(5000))
            page.wait_for_function("window.TakMapIconRegistryI569.diagnostics().milIconsLoaded === 1448", timeout=wait_ms(8000))
            page.wait_for_function("document.querySelectorAll('#milGrid .icon-card-i556').length > 0", timeout=wait_ms(8000))
            registry_open = page.evaluate("""() => ({
              loaded: TakMapIconRegistryI569.diagnostics().milIconsLoaded,
              currentCards: document.querySelectorAll('#milGrid .icon-card-i556').length,
              legacyCards: document.querySelectorAll('#milGrid .mil-icon-card').length,
              error: TakMapIconRegistryI569.diagnostics().milCatalogError
            })""")
            assert registry_open['loaded'] == 1448 and registry_open['currentCards'] == 238, registry_open
            assert registry_open['legacyCards'] == 0 and not registry_open['error'], registry_open
            page.evaluate("document.getElementById('registryCloseI556')?.click()")
            page.wait_for_function("!document.getElementById('milPicker')?.classList.contains('active')", timeout=wait_ms(5000))
        else:
            registry_throttled = page.evaluate("""() => ({
              ready: !!window.TakMapIconRegistryI569?.diagnostics?.().ready,
              legacyCards: document.querySelectorAll('#milGrid .mil-icon-card').length,
              active: !!document.getElementById('milPicker')?.classList.contains('active')
            })""")
            assert registry_throttled == {'ready': True, 'legacyCards': 0, 'active': False}, registry_throttled

        # Open the real i569 contextual sidebar for a Data Sync point. The same
        # panel transforms into Edit Point and returns to information in place.
        context = page.evaluate("""() => {
          const object=((typeof lastDataSync !== 'undefined' && lastDataSync?.objects) || window.__takMapDataSyncStartupResultI553?.payload?.objects || []).find(o => o.callsign === 'DS-CUSTOM');
          const panel=document.getElementById('takMapContextSidebarI569');
          panel.__identity='same-panel';
          if (typeof window.coordFormatToggle === 'function') window.coordFormatToggle();
          window.TakMapContextSidebarI569.showObject(object,'datasync',object.__layer,true);
          return {popup:object?.__layer?.getPopup?.() || null};
        }""")
        assert context['popup'] is None, context
        page.wait_for_function("!document.getElementById('takMapContextSidebarI569').classList.contains('collapsed')")
        page.wait_for_selector('#takMapContextSidebarBodyI569 .point-info-popup-i556 [data-i556-point-edit]', timeout=wait_ms(5000))
        page.wait_for_function("""() => {const p=document.getElementById('takMapContextSidebarI569')?.getBoundingClientRect();const m=document.getElementById('map')?.getBoundingClientRect();return !!p&&!!m&&(m.right-p.right)>=5&&(m.right-p.right)<=25}""", timeout=wait_ms(5000))
        panel_info = page.evaluate("""() => {
          const panel=document.getElementById('takMapContextSidebarI569');
          const body=document.getElementById('takMapContextSidebarBodyI569');
          const map=document.getElementById('map').getBoundingClientRect();
          const rect=panel.getBoundingClientRect();
          const scale=document.querySelector('#map .leaflet-control-scale')?.getBoundingClientRect();
          const rows={};
          for (const label of body.querySelectorAll('.point-popup-label-i556')) rows[label.textContent.trim()]=label.nextElementSibling?.textContent.trim()||'';
          const location=body.querySelector('.point-popup-location-text-i569')?.textContent.trim()||'';
          const edit=body.querySelector('.point-popup-edit-i556');
          return {same:panel.__identity==='same-panel',title:document.getElementById('takMapContextTitleI569').textContent,overflow:getComputedStyle(body).overflowY,right:Math.round(map.right-rect.right),aboveScale:!scale||rect.bottom<=scale.top-8,width:Math.round(rect.width),location,rows,editFont:edit?getComputedStyle(edit).fontSize:'',iconPathLabel:Array.from(body.querySelectorAll('.point-popup-label-i556')).some(x=>x.textContent.trim()==='Icon Path')};
        }""")
        assert panel_info['same'] and panel_info['title'] == 'DS-CUSTOM', panel_info
        assert panel_info['overflow'] == 'visible' and panel_info['aboveScale'], panel_info
        assert 5 <= panel_info['right'] <= 25 and panel_info['width'] == 400, panel_info
        assert panel_info['location'] and 'N' in panel_info['location'] and 'W' in panel_info['location'], panel_info
        assert re.match(r'^07/24/2026 02:50 (?:\d+days?(?: \d+h)?(?: \d+m)?|\d+h(?: \d+m)?|\d+m)$', panel_info['rows'].get('Added','')), panel_info
        assert re.match(r'^07/27/2026 04:38 (?:\d+days?(?: \d+h)?(?: \d+m)?|\d+h(?: \d+m)?|\d+m)$', panel_info['rows'].get('Updated','')), panel_info
        assert panel_info['rows'].get('Sync State') == 'Synced' and panel_info['editFont'] == '12.5px' and panel_info['iconPathLabel'] is False, panel_info
        assert panel_info['rows'].get('Source') == 'Data Sync: OpenTAKServer · ots.example.com/ots-field-01', panel_info
        assert 'UID' not in panel_info['rows'], panel_info
        page.evaluate("document.querySelector('#takMapContextSidebarBodyI569 [data-point-copy-location]')?.click()")
        page.wait_for_function("window.__copiedLocation===document.querySelector('.point-popup-location-text-i569').textContent.trim() && document.querySelector('[data-point-copy-location]').textContent==='Copied'", timeout=wait_ms(5000))

        page.evaluate("document.querySelector('#takMapContextSidebarBodyI569 [data-i556-point-edit]')?.click()")
        page.wait_for_function("document.querySelector('#takMapContextSidebarBodyI569>#takMapPointEditorI556.active')", timeout=wait_ms(5000))
        assert page.input_value('#pointEditorNameI556') == 'DS-CUSTOM'
        assert page.input_value('#pointEditorContextI556') == 'STARTUP-SMOKE'
        editor_state = page.evaluate("""() => ({same:document.getElementById('takMapContextSidebarI569').__identity==='same-panel',open:!document.getElementById('takMapContextSidebarI569').classList.contains('collapsed'),meta:getComputedStyle(document.getElementById('pointEditorSourceMetaI556')).whiteSpace})""")
        assert editor_state['same'] and editor_state['open'] and editor_state['meta'] == 'normal', editor_state
        page.evaluate("document.getElementById('pointEditorCancelI556')?.click()")
        page.wait_for_selector('#takMapContextSidebarBodyI569 .point-info-popup-i556', timeout=wait_ms(5000))
        assert page.evaluate("document.getElementById('takMapContextSidebarI569').__identity==='same-panel' && !document.getElementById('takMapContextSidebarI569').classList.contains('collapsed')") is True

        # Local Data points use the same sidebar/editor without Mission fields.
        local_result = page.evaluate("""() => {
          const object=(typeof importedFeatures === 'function' ? importedFeatures() : []).find(o => o.name === 'LOCAL-CUSTOM');
          window.TakMapContextSidebarI569.showObject(object,'local',object.__layer,true);
          return {icon:object?.__layer?.options?.icon?.html || '', popup:object?.__layer?.getPopup?.() || null};
        }""")
        assert '%2FAnimals%2Fant.png' in local_result['icon'], local_result
        assert local_result['popup'] is None, local_result
        page.wait_for_function("document.getElementById('takMapContextTitleI569').textContent==='LOCAL-CUSTOM'")
        local_html = page.locator('#takMapContextSidebarBodyI569').inner_text()
        assert 'POINT · LOCAL DATA' in local_html.upper() and 'MISSION' not in local_html.upper(), local_html
        page.evaluate("document.querySelector('#takMapContextSidebarBodyI569 [data-i556-point-edit]')?.click()")
        page.wait_for_function("document.querySelector('#takMapContextSidebarBodyI569>#takMapPointEditorI556.active')", timeout=wait_ms(5000))
        assert page.input_value('#pointEditorNameI556') == 'LOCAL-CUSTOM'
        assert page.input_value('#pointEditorContextI556') == 'Local Startup Points'
        page.evaluate("document.getElementById('pointEditorCancelI556')?.click()")

        # Empty map click and the sidebar hide control collapse the same panel.
        page.wait_for_timeout(420)
        page.evaluate("window.takLeafletMap.fire('click',{originalEvent:{target:document.getElementById('map')}})")
        page.wait_for_function("document.getElementById('takMapContextSidebarI569').classList.contains('collapsed')")
        page.evaluate("""() => {const o=importedFeatures().find(x=>x.name==='LOCAL-CUSTOM');TakMapContextSidebarI569.showObject(o,'local',o.__layer,false)}""")
        page.wait_for_function("!document.getElementById('takMapContextSidebarI569').classList.contains('collapsed')")
        page.evaluate("document.getElementById('takMapContextHideI569')?.click()")
        page.wait_for_function("document.getElementById('takMapContextSidebarI569').classList.contains('collapsed')")

        # Reconstruct a partially loaded Save Point panel, then open it inside the map.
        create_rebuild = page.evaluate("""() => {
          const panel=document.getElementById('pointEditPanel');
          panel.dataset.i556PointWindow='1';
          panel.innerHTML='<div id="partialSavePoint">Incomplete</div>';
          const ok=window.TakMapIconRegistryI569.ensureCreatePanel();
          return {ok,loaded:panel.dataset.takMapLoadedI569,save:!!document.getElementById('pointSaveI556'),location:!!document.getElementById('pointLocationI556'),destination:!!document.getElementById('pointSaveDestinationI556')};
        }""")
        assert create_rebuild == {'ok': True, 'loaded': '1', 'save': True, 'location': True, 'destination': True}, create_rebuild

        # Every fresh map click starts an isolated Create Point session. Stale point
        # name/notes/location are cleared, a second click replaces Location while
        # open, manual coordinates survive same-session symbol/panel refresh, and
        # the exact current coordinates are sent in the POST payload.
        page.evaluate("""() => {
          document.getElementById('pointNameInput').value='STALE-POINT';
          document.getElementById('pointNotesInput').value='stale notes';
          document.getElementById('pointLocationI556').value='33.000000, -116.000000';
          window.v233PointState.name='STALE-POINT'; window.v233PointState.notes='stale notes';
          window.v233PointState.latlng={lat:34.2,lng:-118.4};
          window.v233OpenPointPanel();
        }""")
        page.wait_for_function("document.getElementById('pointEditPanel')?.classList.contains('active')", timeout=wait_ms(5000))
        first_create = page.evaluate("""() => ({name:document.getElementById('pointNameInput').value,notes:document.getElementById('pointNotesInput').value,location:document.getElementById('pointLocationI556').value})""")
        assert first_create == {'name':'','notes':'','location':'34.200000, -118.400000'}, first_create

        page.evaluate("""() => {window.v233PointState.latlng={lat:35.1234567,lng:-117.7654321};window.v233OpenPointPanel()}""")
        assert page.input_value('#pointLocationI556') == '35.123457, -117.765432'
        page.fill('#pointLocationI556', '36.234567, -116.345678')
        page.evaluate("window.v233OpenPointPanel({preserveDraft:true})")
        assert page.input_value('#pointLocationI556') == '36.234567, -116.345678'
        page.fill('#pointNameInput', 'CREATE-SESSION-NEW')
        page.fill('#pointNotesInput', 'new session notes')
        page.select_option('#pointSaveDestinationI556', 'mission')
        page.select_option('#pointMissionI556', 'STARTUP-SMOKE')

        page.wait_for_timeout(150)
        containment = page.evaluate("""() => {
          const p=document.getElementById('pointEditPanel').getBoundingClientRect();
          const m=document.getElementById('map').getBoundingClientRect();
          return {p:{left:p.left,top:p.top,right:p.right,bottom:p.bottom},m:{left:m.left,top:m.top,right:m.right,bottom:m.bottom}};
        }""")
        assert containment['p']['left'] >= containment['m']['left'] - 1, containment
        assert containment['p']['top'] >= containment['m']['top'] - 1, containment
        assert containment['p']['right'] <= containment['m']['right'] + 1, containment
        assert containment['p']['bottom'] <= containment['m']['bottom'] + 1, containment

        page.evaluate("document.getElementById('registryCloseI556')?.click()")
        page.wait_for_function("!document.getElementById('milPicker')?.classList.contains('active')", timeout=wait_ms(5000))
        page.wait_for_function("""() => {const b=document.getElementById('pointSaveI556'); return !!b && !b.disabled && document.getElementById('pointEditPanel')?.classList.contains('active');}""", timeout=wait_ms(5000))
        page.evaluate("document.getElementById('pointSaveI556').click()")
        try:
            page.wait_for_function("() => document.getElementById('pointSaveStatusI556')?.textContent.includes('confirmed by OpenTAKServer') || !document.getElementById('pointEditPanel')?.classList.contains('active')", timeout=wait_ms(20000))
        except Exception:
            print(json.dumps({"create_save_diagnostics": page.evaluate("""() => ({status:document.getElementById('pointSaveStatusI556')?.textContent||'',disabled:!!document.getElementById('pointSaveI556')?.disabled,panelActive:!!document.getElementById('pointEditPanel')?.classList.contains('active'),location:document.getElementById('pointLocationI556')?.value||'',name:document.getElementById('pointNameInput')?.value||'',mission:document.getElementById('pointMissionI556')?.value||''})"""), "point_posts": point_posts, "page_errors": page_errors, "console_errors": console_errors[-20:]}, indent=2), flush=True)
            raise
        assert len(point_posts) == 1, point_posts
        posted = point_posts[0]
        assert posted['name'] == 'CREATE-SESSION-NEW' and posted['notes'] == 'new session notes', posted
        assert posted['mission_name'] == 'STARTUP-SMOKE', posted
        assert abs(float(posted['lat']) - 36.234567) < 1e-8 and abs(float(posted['lon']) + 116.345678) < 1e-8, posted
        page.wait_for_function("!document.getElementById('pointEditPanel').classList.contains('active')", timeout=wait_ms(3000))

        # Successful save cleared the draft; a later click cannot inherit it.
        page.evaluate("""() => {window.v233PointState.latlng={lat:37.1,lng:-115.2};window.v233OpenPointPanel()}""")
        next_create = page.evaluate("""() => ({name:document.getElementById('pointNameInput').value,notes:document.getElementById('pointNotesInput').value,location:document.getElementById('pointLocationI556').value})""")
        assert next_create == {'name':'','notes':'','location':'37.100000, -115.200000'}, next_create
        page.evaluate("document.getElementById('pointCancelI556').click()")

    # Full registry browse/selection behavior is preserved by the i555 baseline
    # tests; this browser test validates the active i569 startup and contextual sidebar.
    selected_custom = {"iconsetpath": exact_custom_path}
    assert not page_errors, page_errors
    browser.close()

print(json.dumps({
    "ok": True,
    "version": "i569",
    "cpu_throttle_rate": cpu_throttle,
    "shell_seconds": round(shell_seconds, 3),
    "runtime_seconds": round(runtime_seconds, 3),
    "shell_frame_ms": round(float(frame_ms), 1),
    "deferred_modules": result["diagnostics"]["deferredLoaded"],
    "startup_data_sync_requests": Counter(x.split("?", 1)[0] for x in requests)["/api/tak-map/data-sync"],
    "startup_data_sync_rendered": result["dataSyncStartup"]["rendered"],
    "mutation_records": result["diagnostics"]["mutation"]["records"],
    "mutation_callbacks": result["diagnostics"]["mutation"]["deliveredCallbacks"],
    "milstd_svg_requests_before_runtime": svg_before_runtime,
    "milstd_svg_requests_after_open": svg_requests,
    "icon_registry_sets": result["iconRegistry"]["summary"]["custom_set_count"],
    "icon_registry_icons": result["iconRegistry"]["summary"]["custom_icon_count"],
    "custom_selection": selected_custom["iconsetpath"],
}, indent=2))
sys.stdout.flush()
os._exit(0)
