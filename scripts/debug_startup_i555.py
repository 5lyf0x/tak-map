#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import pathlib
import re
import sys
import time
from collections import Counter
from urllib.parse import parse_qs, urlparse

ROOT = pathlib.Path(__file__).resolve().parents[1]
DASH = ROOT / "tak_dashboard.py"

spec = importlib.util.spec_from_file_location("tak_dashboard_i555_startup_test", DASH)
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
icon_registry_js = (ROOT / "assets/tak-map-icon-registry-i555.js").read_text()
registry_summary = json.loads((ROOT / "assets/icon-registry/registry-summary.json").read_text())
registry_summary.update({"ok": True, "version": "i555"})
registry_manifest = json.loads((ROOT / "assets/icon-registry/icon-registry.json").read_text())
registry_icons_by_set = {}
for _icon in registry_manifest["icons"]:
    registry_icons_by_set.setdefault(_icon["iconset_uid"], []).append({k:v for k,v in _icon.items() if k not in {"sha256","internal_path"}})
registry_icon_by_path = {_icon["iconsetpath"]:_icon for _icon in registry_manifest["icons"]}

source_text = DASH.read_text()
main_marker = "if __name__=='__main__':\n    main()"
assert source_text.count(main_marker) == 1
assert source_text.rfind(main_marker) > source_text.rfind("# --- end TAK Map i555 read-only icon registry + registry-managed point symbols ---")
assert not source_text[source_text.rfind(main_marker) + len(main_marker):].strip()

# Static release budgets: the page must stay a shell rather than regaining the
# historical megabyte-scale inline runtime.
assert mod.TAK_MAP_ITERATION == "i555"
assert len(html.encode()) < 200_000, len(html.encode())
assert len(re.findall(r"<script\b", html, re.I)) == 2
assert all(not body.strip() for body in re.findall(r"<script[^>]*>(.*?)</script>", html, re.I | re.S))
assert "/assets/runtime/tak-map-startup-i553.js?v=1.3.0-i555" in html
assert "/assets/runtime/tak-map-icon-registry-i555.js?v=1.3.0-i555" in html
assert html.index("tak-map-startup-i553.js") < html.index("tak-map-icon-registry-i555.js")
assert "tak-map-icon-registry-i555.js" not in mod.TAK_MAP_LOGIN_HTML
assert len(core_js.encode()) < 750_000
assert manifest.get("version") == "1.3.0-i553"
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
assert "setInterval(refreshDataSyncInterval,10000)" in core_js  # ten-second Data Sync polling interval

v381 = next(row["code"] for row in manifest["scripts"] if row["id"].startswith("v381"))
boot = re.search(r"function boot\(\)\{(.*?)\}\s*if\(d\.readyState", v381, re.S)
assert boot, "v381 boot not found"
assert "loadIcons" not in boot.group(1)
assert "renderMilPicker" not in boot.group(1)
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
        {"uid": "DS-P10-UID", "mission_id": 7, "mission": "STARTUP-SMOKE", "callsign": "DS-P10", "lat": 35.1, "lon": -117.1, "cot_type": "a-f-G-E-W-H", "mission_cot_raw_type_i553": "a-f-G-E-W-H", "mission_cot_raw_iconset_path_i553": "COT_MAPPING_2525C/a-f/a-f-G-E-V-U-S", "data_sync_symbol_decision_i553": {"version": "i553", "authority": "event-type", "selected_cot_type": "a-f-G-E-W-H"}, "source": "OpenTAKServer Data Sync mission_uids"}
      ], "packages": []},
    "/api/tak-map/local-data": {"ok": True, "routes": [], "points": [], "shapes": []},
    "/api/tak-map/imported": {"ok": True, "imports": []},
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
}
requests: list[str] = []
request_times: list[tuple[str, float]] = []
page_errors: list[str] = []
console_errors: list[str] = []
svg_requests = 0

def tiny_svg() -> bytes:
    return b'<svg xmlns="http://www.w3.org/2000/svg" width="250" height="150" viewBox="0 0 5000 3000"><path d="M200 200h4600v2600H200z" fill="none" stroke="black" stroke-width="100"/></svg>'

print('DBG before playwright', flush=True)
with sync_playwright() as pw:
    print('DBG playwright opened', flush=True)
    print('DBG launching', flush=True)
    browser = pw.chromium.launch(headless=True, executable_path="/usr/bin/chromium", args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"])
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    cdp = page.context.new_cdp_session(page)
    cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
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
        if path == "/assets/runtime/tak-map-icon-registry-i555.js":
            return route.fulfill(status=200, content_type="application/javascript", body=icon_registry_js)
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
            return route.fulfill(status=200, content_type="application/json", body=json.dumps({"ok":True,"version":"i555","set_uid":set_uid,"icons":rows,"count":len(rows),"read_only":True}))
        if path == "/api/tak-map/icon-registry/icon":
            icon_path = (parse_qs(parsed.query).get("path") or [""])[0]
            row = registry_icon_by_path.get(icon_path)
            if not row:
                return route.fulfill(status=404, body="")
            return route.fulfill(status=200, content_type="image/png", body=(ROOT / "assets/icon-registry" / row["internal_path"]).read_bytes())
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
    print('DBG set content', flush=True)
    page.set_content(html.replace("<head>", "<head><base href=\"https://example.test/\">", 1), wait_until="domcontentloaded", timeout=20_000)
    print('DBG content done', flush=True)
    page.wait_for_function("document.documentElement.dataset.takMapShell === 'ready'", timeout=8_000)
    shell_seconds = time.perf_counter() - started
    frame_ms = page.evaluate("() => new Promise(resolve => { const s=performance.now(); requestAnimationFrame(() => resolve(performance.now()-s)); })")
    svg_before_runtime = svg_requests
    try:
        print('DBG shell ready', flush=True)
        page.wait_for_function("document.documentElement.dataset.takMapRuntime === 'ready'", timeout=35_000)
    except Exception:
        print(json.dumps({"page_errors": page_errors, "console_errors": console_errors, "requests_tail": requests[-80:], "diag": page.evaluate("() => ({shell:document.documentElement.dataset.takMapShell||'',runtime:document.documentElement.dataset.takMapRuntime||'',startup:window.TakMapStartupDiagnosticsI553&&window.TakMapStartupDiagnosticsI553.snapshot?window.TakMapStartupDiagnosticsI553.snapshot():null, body:(document.body&&document.body.innerText||'').slice(0,1000)})")}, indent=2), flush=True)
        raise
    runtime_seconds = time.perf_counter() - started
    print('DBG runtime ready', flush=True)
    page.wait_for_function("window.__takMapDataSyncControlReadyI553 === true", timeout=5_000)
    print('DBG before registry wait', flush=True)
    page.wait_for_function("window.TakMapIconRegistryI555 && window.TakMapIconRegistryI555.diagnostics().ready === true", timeout=8_000)
    page.wait_for_function("window.__takMapDataSyncStartupResultI553 && window.__takMapDataSyncStartupResultI553.rendered === true", timeout=8_000)
    page.wait_for_function("window.__takMapOptionalDataStartedI553 === true", timeout=5_000)
    page.evaluate("() => window.__takMapOptionalDataPromiseI553 || Promise.resolve()")
    page.wait_for_function("TakMapStartupDiagnosticsI553.initialDataReadyAt > 0", timeout=8_000)
    page.wait_for_function("window.__takMapMilStdRedrawI553 && window.__takMapMilStdRedrawI553.objectCount === 2", timeout=8_000)
    page.wait_for_timeout(700)
    print('DBG waits complete', flush=True)

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
      milstdRedraw: window.__takMapMilStdRedrawI553 || null,
      iconRegistry: window.TakMapIconRegistryI555 ? {version:window.TakMapIconRegistryI555.version, diagnostics:window.TakMapIconRegistryI555.diagnostics(), summary:window.TakMapIconRegistryI555.summary()} : null
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
    assert result["iteration"] == "i555"
    assert result["iconRegistry"] and result["iconRegistry"]["version"] == "i555", result
    assert result["iconRegistry"]["diagnostics"]["ready"] is True, result
    assert result["iconRegistry"]["summary"]["custom_set_count"] == 10, result
    assert result["iconRegistry"]["summary"]["custom_icon_count"] == 3742, result
    assert result["dataSyncStartup"]["missions"] == 1, result["dataSyncStartup"]
    assert result["dataSyncStartup"]["objects"] == 2, result["dataSyncStartup"]
    assert result["dataSyncStartup"]["rendered"] is True, result["dataSyncStartup"]
    assert result["missionCountText"] == "1 missions", result["missionCountText"]
    assert result["objectCountText"] == "2 objects", result["objectCountText"]
    assert result["dataSyncLayerCount"] >= 2, result["dataSyncLayerCount"]
    assert "friendly-emergency-construction.svg?v=i553" in result["dsP13Image"], result
    assert "friendly-ground-equipment-self-propelled-howitzer.svg?v=i553" in result["dsP10Image"], result
    assert result["milstdRedraw"]["objectCount"] == 2, result
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

    print('DBG before open picker', flush=True)
    page.evaluate("() => window.openMilPicker && window.openMilPicker()")
    page.wait_for_function("document.querySelectorAll('#milGrid img').length > 0", timeout=10_000)
    page.wait_for_timeout(300)
    print('DBG picker ready', flush=True)
    assert svg_requests > 0
    assert page.evaluate("document.querySelectorAll('#milGrid img').length") <= 360

    # Switch to one imported ATAK set only after startup and verify the exact
    # registry identity is preserved through the browser selection model.
    default_uid = "34ae1613-9645-4222-a9d2-e5f243dea2865"
    print('DBG fill', flush=True)
    page.fill('#milSearch', 'ant.png')
    print('DBG fill done', flush=True)
    print('DBG set click', flush=True)
    page.evaluate("uid => { const button=document.querySelector('#registrySetListI555 [data-set-uid=\"'+CSS.escape(uid)+'\"]'); if (!button) throw new Error('icon set button not found'); button.click(); }", default_uid)
    print('DBG set click done', flush=True)
    exact_custom_path = '34ae1613-9645-4222-a9d2-e5f243dea2865/Animals/ant.png'
    exact_custom_key = exact_custom_path + '|'
    exact_card = f'#milGrid [data-icon-key="{exact_custom_key}"]'
    print('DBG exact wait', flush=True)
    page.wait_for_function("key => !!document.querySelector('#milGrid [data-icon-key=\"'+CSS.escape(key)+'\"]')", arg=exact_custom_key, timeout=10_000)
    print('DBG exact found', flush=True)
    page.evaluate("key => { const card=document.querySelector('#milGrid [data-icon-key=\"'+CSS.escape(key)+'\"]'); if (!card) throw new Error('custom icon card not found'); card.click(); }", exact_custom_key)
    print('DBG exact click done', flush=True)
    selected_custom = page.evaluate("() => window.TakMapIconRegistryI555.selected()")
    assert selected_custom['kind'] == 'custom', selected_custom
    assert selected_custom['iconsetpath'] == exact_custom_path, selected_custom
    custom_img = page.get_attribute('#milGrid img', 'src')
    assert '/api/tak-map/icon-registry/icon?path=' in custom_img, custom_img
    assert '%2FAnimals%2Fant.png' in custom_img, custom_img
    assert not page_errors, page_errors
    print('DBG close', flush=True)
    browser.close()
    print('DBG closed', flush=True)

print(json.dumps({
    "ok": True,
    "version": "i555",
    "shell_seconds_cpu4x": round(shell_seconds, 3),
    "runtime_seconds_cpu4x": round(runtime_seconds, 3),
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
