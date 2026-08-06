#!/usr/bin/env python3
"""Exercise i615 Gateway Data through the actual deferred startup loader and manifest entry."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = "https://takmap.test"
SOURCE_KEY = "source_extension:military-special-use-airspace"
STARTUP = (ROOT / "assets" / "tak-map-startup-i553.js").read_text()
REAL_MANIFEST = json.loads((ROOT / "assets" / "tak-map-deferred-i553.json").read_text())
GATEWAY_ROWS = [row for row in REAL_MANIFEST["scripts"] if row.get("id") == "takMapGatewayDataLoaderV476"]
assert len(GATEWAY_ROWS) == 1
RUNTIME_MANIFEST = json.dumps({"version": REAL_MANIFEST["version"], "count": 1, "scripts": GATEWAY_ROWS, "retired_startup_scripts": []})


def gateway_payload() -> dict:
    return {
        "ok": True,
        "api_version": "gateway-data-v1",
        "gateway_iteration": "i191",
        "full": True,
        "revision": 17,
        "generated_at": "2026-08-02T16:00:00Z",
        "source_registry": {
            "dynamic_source_discovery": True,
            "dynamic_source_prefix": "source_extension:",
            "source_extension_registry_version": "source-extension-registry-v1-i191",
        },
        "sources": {
            SOURCE_KEY: {
                "id": SOURCE_KEY,
                "source_key": SOURCE_KEY,
                "source_kind": "source_extension",
                "source_extension": True,
                "dynamic": True,
                "extension_id": "military-special-use-airspace",
                "label": "Military Special Use Airspace",
                "enabled": True,
                "state": "healthy",
                "count": 1,
                "logical_count": 1,
                "count_semantics": "objects",
                "geometry_types": ["Polygon", "MultiPolygon"],
            }
        },
        "objects": [{
            "type": "Feature",
            "id": "moa-multipolygon-1",
            "geometry": {
                "type": "MultiPolygon",
                "coordinates": [
                    [[[-77.12, 38.80], [-77.01, 38.80], [-77.01, 38.91], [-77.12, 38.91], [-77.12, 38.80]]],
                    [[[-76.96, 38.83], [-76.90, 38.83], [-76.90, 38.89], [-76.96, 38.89], [-76.96, 38.83]]],
                ],
            },
            "properties": {
                "uid": "moa-multipolygon-1",
                "source": SOURCE_KEY,
                "title": "Startup MOA MultiPolygon",
                "stale_at": "2099-01-01T00:00:00Z",
                "metadata": {"category": "Military Operations Area"},
            },
            "style": {"stroke": "#a7c636", "fill": "#a7c636", "fill_opacity": 0.2},
        }],
        "deleted_uids": [],
    }


FIXTURE = f"""<!doctype html><html><head><meta charset=\"utf-8\"><base href=\"{ORIGIN}/\"><style>
body{{background:#06090d;color:#e9f0f5;font-family:sans-serif}}#sidebar{{width:410px}}.panel{{display:block;border:1px solid #273642;padding:12px;margin:8px}}
</style></head><body><div id=\"takMapStartupStatusI553\"></div><aside id=\"sidebar\"><div class=\"panel\" data-collapse-key=\"adsbSettings\"><h2>ADS-B</h2></div><div class=\"panel\" id=\"satelliteTrackingPanelV409\"><h2>Satellite Tracking</h2></div></aside>
<script>
const __storageValues=new Map([[{json.dumps('takmap.gatewayData.ingest.' + SOURCE_KEY)},'1']]);
const localStorage={{getItem:k=>__storageValues.has(String(k))?__storageValues.get(String(k)):null,setItem:(k,v)=>__storageValues.set(String(k),String(v)),removeItem:k=>__storageValues.delete(String(k)),clear:()=>__storageValues.clear(),key:i=>Array.from(__storageValues.keys())[i]||null,get length(){{return __storageValues.size}}}};
window.__layers=[];window.__mapLayers=new Set();
class Emitter{{constructor(){{this.handlers={{}}}}on(t,f){{(this.handlers[t]||(this.handlers[t]=[])).push(f);return this}}off(t,f){{if(this.handlers[t])this.handlers[t]=this.handlers[t].filter(x=>x!==f);return this}}fire(t,e={{}}){{for(const f of (this.handlers[t]||[]).slice())f(Object.assign({{target:this}},e));return this}}}}
class Popup{{constructor(html,opts,owner){{this.html=html;this.options=opts||{{}};this.owner=owner;this.root=document.createElement('div');this.root.innerHTML='<a class=\"leaflet-popup-close-button\">×</a><div class=\"leaflet-popup-content\"></div>';this.root.querySelector('.leaflet-popup-content').innerHTML=html}}setContent(v){{this.html=v;this.root.querySelector('.leaflet-popup-content').innerHTML=v;return this}}getElement(){{return this.root}}setLatLng(){{return this}}openOn(){{return this}}}}
class Layer extends Emitter{{constructor(kind,data,options){{super();this.kind=kind;this.data=data;this.options=options||{{}};this.children=[];window.__layers.push(this)}}addTo(parent){{parent.addLayer(this);return this}}bindPopup(html,opts){{this.popup=new Popup(html,opts,this);return this}}getPopup(){{return this.popup||null}}setPopupContent(v){{if(this.popup)this.popup.setContent(v);return this}}setLatLng(v){{this.data=v;return this}}setIcon(v){{this.options.icon=v;return this}}setLatLngs(v){{this.data=v;return this}}setStyle(v){{this.options=Object.assign(this.options,v);return this}}getLatLng(){{return this.data}}getCenter(){{return Array.isArray(this.data&&this.data[0])?this.data[0]:this.data}}getBounds(){{return {{getCenter:()=>this.getCenter()}}}}}}
class Group extends Layer{{constructor(){{super('group',null,{{}})}}addLayer(x){{if(!this.children.includes(x))this.children.push(x);return this}}removeLayer(x){{this.children=this.children.filter(y=>y!==x);return this}}hasLayer(x){{return this.children.includes(x)}}clearLayers(){{this.children=[];return this}}}}
const events=new Emitter();window.map=Object.assign(events,{{_zoom:9,_popup:null,hasLayer:l=>window.__mapLayers.has(l),addLayer:l=>{{window.__mapLayers.add(l);return window.map}},removeLayer:l=>{{window.__mapLayers.delete(l);return window.map}},getZoom(){{return this._zoom}},closePopup(){{return this}},invalidateSize(){{return this}}}});window.takLeafletMap=window.map;
window.L={{map:()=>window.map,layerGroup:()=>new Group(),marker:(x,o)=>new Layer('marker',x,o),polyline:(x,o)=>new Layer('polyline',x,o),polygon:(x,o)=>new Layer('polygon',x,o),divIcon:o=>o,latLngBounds:()=>({{}}),DomEvent:{{stopPropagation(){{}},preventDefault(){{}}}}}};
window.__takMapCoreInitI553=async()=>{{document.documentElement.dataset.takMapShell='ready'}};
window.__takMapStartOptionalDataI553=()=>Promise.resolve();
window.__takMapStartDataSyncI553=()=>Promise.resolve();
</script><script src=\"/assets/runtime/tak-map-startup-i553.js?v=1.4.0-i618\"></script></body></html>"""


def main() -> int:
    chromium = next((shutil.which(name) for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable") if shutil.which(name)), None)
    if not chromium:
        raise SystemExit("Chromium is required")
    from playwright.sync_api import sync_playwright

    page_errors: list[str] = []
    console_errors: list[str] = []
    gateway_requests = 0

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=chromium, args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"])
        page = browser.new_page(viewport={"width": 1200, "height": 800})
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        def route_request(route):
            nonlocal gateway_requests
            parsed = urllib.parse.urlsplit(route.request.url)
            path = parsed.path
            if path == "/":
                route.fulfill(status=200, content_type="text/html; charset=utf-8", body=FIXTURE)
            elif path == "/assets/runtime/tak-map-startup-i553.js":
                route.fulfill(status=200, content_type="application/javascript; charset=utf-8", body=STARTUP)
            elif path == "/assets/runtime/tak-map-core-i553.js":
                route.fulfill(status=200, content_type="application/javascript; charset=utf-8", body="window.__takMapCoreInitI553=async()=>{document.documentElement.dataset.takMapShell='ready'};window.__takMapStartOptionalDataI553=()=>Promise.resolve();window.__takMapStartDataSyncI553=()=>Promise.resolve();")
            elif path == "/assets/runtime/tak-map-data-sync-i553.js":
                route.fulfill(status=200, content_type="application/javascript; charset=utf-8", body="window.__takMapDataSyncControlReadyI553=true;")
            elif path == "/assets/runtime/tak-map-deferred-i553.json":
                route.fulfill(status=200, content_type="application/json; charset=utf-8", body=RUNTIME_MANIFEST)
            elif path == "/api/tak-map/gateway-data/snapshot":
                gateway_requests += 1
                route.fulfill(status=200, content_type="application/json", body=json.dumps(gateway_payload()))
            else:
                route.fulfill(status=204, body="")

        page.route("**/*", route_request)
        page.set_content(FIXTURE, wait_until="domcontentloaded", timeout=20_000)
        page.wait_for_function("document.documentElement.dataset.takMapRuntime === 'ready'", timeout=20_000)
        page.wait_for_function("window.TakMapGatewayDataV476 && window.TakMapGatewayDataV476.diagnostics().revision === 17", timeout=20_000)
        page.wait_for_function("window.TakMapGatewayDataV476.diagnostics().objects === 1", timeout=10_000)
        result = page.evaluate(f"""() => {{
          const d=window.TakMapGatewayDataV476.diagnostics();
          const row=document.querySelector('[data-source="{SOURCE_KEY}"]');
          return {{version:d.version,dynamic:d.dynamicSourcesDiscovered,objects:d.objects,layers:d.layers,geometryRejected:d.geometryRejected,lastGeometryError:d.lastGeometryError,rowPresent:!!row,rowLabel:row&&row.querySelector('.source-label').textContent.trim(),rowChecked:!!(row&&row.querySelector('input')&&row.querySelector('input').checked),deferredFailed:window.TakMapStartupDiagnosticsI553.deferredFailed.slice(),runtime:document.documentElement.dataset.takMapRuntime}};
        }}""")
        browser.close()

    assert gateway_requests >= 1, gateway_requests
    assert result["runtime"] == "ready", result
    assert result["version"] == "i618", result
    assert result["dynamic"] == 1, result
    assert result["objects"] == 1 and result["layers"] == 1, result
    assert result["geometryRejected"] == 0 and not result["lastGeometryError"], result
    assert result["rowPresent"] and result["rowLabel"] == "Military Special Use Airspace" and result["rowChecked"], result
    assert result["deferredFailed"] == [], result
    assert not page_errors, page_errors
    assert not console_errors, console_errors
    print("TAK Map i618 actual deferred-startup dynamic Source Extension/MultiPolygon browser test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
