#!/usr/bin/env python3
"""Exercise lossless large NWS rings and per-object geometry error isolation."""
from __future__ import annotations

import json
import math
from pathlib import Path
import shutil
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "assets" / "tak-map-gateway-data-v491.js"
ORIGIN = "https://takmap.test"


def ring(count: int, center_lon: float, center_lat: float, radius: float) -> list[list[float]]:
    assert count >= 4
    points: list[list[float]] = []
    unique = count - 1
    for index in range(unique):
        angle = 2.0 * math.pi * index / unique
        points.append([
            round(center_lon + radius * math.cos(angle), 8),
            round(center_lat + radius * math.sin(angle), 8),
        ])
    points.append(points[0][:])
    return points


def feature(uid: str, geometry: dict, title: str) -> dict:
    return {
        "type": "Feature",
        "id": uid,
        "geometry": geometry,
        "properties": {
            "source": "nws_alerts",
            "title": title,
            "metadata": {"event": title},
            "stale_at": "2099-01-01T00:00:00Z",
        },
        "style": {"stroke": "#FFA500", "fill": "#FFA500", "stroke_weight": 4},
    }


def main() -> int:
    chromium = next((name for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable") if shutil.which(name)), None)
    if not chromium:
        raise SystemExit("Chromium is required")

    malformed = [[-118.0, 34.0], [-117.9, 34.0], [-117.9, 34.1], [-118.0, 34.0], [".", "."]]
    payload = {
        "ok": True,
        "full": True,
        "revision": 518,
        "generated_at": "2026-07-22T22:00:00Z",
        "sources": {"nws_alerts": {"enabled": True, "count": 5, "logical_count": 5}},
        "objects": [
            feature("nws-large-4737", {"type": "Polygon", "coordinates": [ring(4737, -118.0, 34.0, 0.8)]}, "NWS 4737"),
            feature("nws-invalid", {"type": "Polygon", "coordinates": [malformed]}, "NWS malformed sentinel"),
            feature("nws-large-2036", {"type": "Polygon", "coordinates": [ring(2036, -117.0, 34.0, 0.5)]}, "NWS 2036"),
            feature("nws-large-1460", {"type": "Polygon", "coordinates": [ring(1460, -116.0, 34.0, 0.3)]}, "NWS 1460"),
            feature("nws-after-invalid", {"type": "Point", "coordinates": [-115.5, 34.2]}, "NWS object after malformed polygon"),
        ],
        "deleted_uids": [],
    }

    fixture = f"""<!doctype html><html><head><meta charset=\"utf-8\"><base href=\"{ORIGIN}/\"></head><body>
<aside id=\"sidebar\"><div class=\"panel\" data-collapse-key=\"adsbSettings\"><h2>ADS-B</h2></div><div class=\"panel\"><h2>Data Sync</h2></div></aside>
<script>
window.__layers=[];window.__gatewayErrors=[];
const originalError=console.error.bind(console);console.error=(...args)=>{{if(String(args[0]||'').includes('Gateway Data'))window.__gatewayErrors.push(args[1]||{{message:String(args[0]||'')}});originalError(...args)}};
class Emitter{{constructor(){{this.handlers={{}}}}on(t,f){{(this.handlers[t]||(this.handlers[t]=[])).push(f);return this}}off(){{return this}}fire(t,e={{}}){{for(const f of (this.handlers[t]||[]))f(Object.assign({{target:this}},e));return this}}}}
class Layer extends Emitter{{constructor(kind,data,options){{super();this.kind=kind;this.data=data;this.options=options||{{}};this.children=[];window.__layers.push(this)}}addTo(parent){{parent.addLayer(this);return this}}bindPopup(){{return this}}setPopupContent(){{return this}}getPopup(){{return null}}setLatLng(v){{this.data=v;return this}}setIcon(v){{this.options.icon=v;return this}}setLatLngs(v){{this.data=v;return this}}setStyle(v){{this.options=Object.assign(this.options,v);return this}}getLatLng(){{return this.data}}getCenter(){{return Array.isArray(this.data&&this.data[0])?this.data[0]:this.data}}getBounds(){{return {{getCenter:()=>this.getCenter()}}}}}}
class Group extends Layer{{constructor(){{super('group',null,{{}})}}addLayer(layer){{if(!this.children.includes(layer))this.children.push(layer);return this}}removeLayer(layer){{this.children=this.children.filter(x=>x!==layer);return this}}hasLayer(layer){{return this.children.includes(layer)}}}}
const mapLayers=new Set();const events=new Emitter();window.map=Object.assign(events,{{_zoom:9,hasLayer:l=>mapLayers.has(l),addLayer:l=>{{mapLayers.add(l);return window.map}},removeLayer:l=>{{mapLayers.delete(l);return window.map}},getZoom(){{return this._zoom}},closePopup(){{return this}},invalidateSize(){{return this}}}});
function validateLatLng(value){{if(!Array.isArray(value))throw new Error('not array');const pair=value.length>=2&&!Array.isArray(value[0])&&!Array.isArray(value[1]);if(pair){{const lat=Number(value[0]),lon=Number(value[1]);if(!Number.isFinite(lat)||!Number.isFinite(lon))throw new Error('Invalid LatLng object: ('+value[0]+', '+value[1]+')');return}}for(const item of value)validateLatLng(item)}}
window.L={{layerGroup:()=>new Group(),marker:(data,options)=>{{validateLatLng(data);return new Layer('marker',data,options)}},polyline:(data,options)=>{{validateLatLng(data);return new Layer('polyline',data,options)}},polygon:(data,options)=>{{validateLatLng(data);return new Layer('polygon',data,options)}},divIcon:options=>options,latLngBounds:()=>({{}}),DomEvent:{{stopPropagation(){{}},preventDefault(){{}}}}}};
</script>
<script src=\"/assets/runtime/tak-map-gateway-data-v491.js?v=1.3.0-i523\"></script>
</body></html>"""

    from playwright.sync_api import sync_playwright

    requests: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=shutil.which(chromium), args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"])
        page = browser.new_page()
        page_errors: list[str] = []
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        def route_request(route):
            parsed = urllib.parse.urlsplit(route.request.url)
            if parsed.path == "/assets/runtime/tak-map-gateway-data-v491.js":
                route.fulfill(status=200, content_type="application/javascript; charset=utf-8", body=ASSET.read_text())
            elif parsed.path == "/api/tak-map/gateway-data/snapshot":
                requests.append(route.request.url)
                route.fulfill(status=200, content_type="application/json", body=json.dumps(payload, separators=(",", ":")))
            else:
                route.fulfill(status=404, content_type="text/plain", body="not found")

        page.route("**/*", route_request)
        page.set_content(fixture, wait_until="domcontentloaded")
        page.wait_for_function("window.TakMapGatewayDataV476 && window.TakMapGatewayDataV476.diagnostics().revision === 518", timeout=20000)
        result = page.evaluate("""() => {
          const diagnostics=window.TakMapGatewayDataV476.diagnostics();
          const polygons=window.__layers.filter(x=>x.kind==='polygon');
          const point=window.__layers.find(x=>x.kind==='marker'&&Array.isArray(x.data)&&x.data[0]===34.2&&x.data[1]===-115.5);
          return {
            diagnostics,
            polygonLengths:polygons.map(x=>Array.isArray(x.data[0])&&Array.isArray(x.data[0][0])?x.data[0].length:x.data.length).sort((a,b)=>b-a),
            pointAfterInvalid:!!point,
            errors:window.__gatewayErrors,
          };
        }""")
        browser.close()

    diagnostics = result["diagnostics"]
    assert not page_errors, page_errors
    assert result["polygonLengths"] == [4737, 2036, 1460], result
    assert result["pointAfterInvalid"] is True, result
    assert diagnostics["connected"] is True
    assert diagnostics["objects"] == 4
    assert diagnostics["layers"] == 4
    assert diagnostics["geometryRejected"] == 1
    assert diagnostics["renderErrors"] == 0
    assert diagnostics["largeRingsRendered"] == 3
    assert diagnostics["maxRingVertices"] == 4737
    assert diagnostics["geometryErrorsIsolated"] is True
    assert diagnostics["largePolygonSupport"] is True
    detail = diagnostics["lastGeometryError"]
    assert detail["source"] == "nws_alerts"
    assert detail["uid"] == "nws-invalid"
    assert detail["title"] == "NWS malformed sentinel"
    assert detail["ringIndex"] == 0
    assert detail["vertexIndex"] == 4
    assert detail["coordinate"] == [".", "."]
    assert requests, "worker did not request Gateway Data"

    print("Gateway Data i518 large-ring and per-object isolation browser test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
