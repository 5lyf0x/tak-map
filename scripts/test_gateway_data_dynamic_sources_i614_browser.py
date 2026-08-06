#!/usr/bin/env python3
"""Exercise i614 dynamic Source Extension discovery and TAK Map-local ingest toggles."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "assets" / "tak-map-gateway-data-v491.js"
ORIGIN = "https://takmap.test"


def feature(uid: str, source: str, geometry: dict, title: str) -> dict:
    return {
        "type": "Feature",
        "id": uid,
        "geometry": geometry,
        "properties": {
            "source": source,
            "title": title,
            "metadata": {"category": "test"},
            "stale_at": "2099-01-01T00:00:00Z",
        },
        "style": {"stroke": "#55c7e8", "fill": "#55c7e8", "fill_opacity": 0.2},
    }


def dynamic_row(source_id: str, label: str, geometry_types: list[str], count: int = 0) -> dict:
    key = f"source_extension:{source_id}"
    return {
        "id": key,
        "source_key": key,
        "source_kind": "source_extension",
        "dynamic": True,
        "source_extension": True,
        "extension_id": source_id,
        "label": label,
        "enabled": True,
        "state": "healthy",
        "message": "Source cycle completed.",
        "count": count,
        "logical_count": count,
        "count_semantics": "objects",
        "geometry_types": geometry_types,
    }


def payload(revision: int, *, include_alpha: bool = True, renamed: bool = False) -> dict:
    sources = {
        "usgs_earthquakes": {"id": "usgs_earthquakes", "label": "USGS Earthquakes", "enabled": True, "count": 0, "logical_count": 0},
        "nws_alerts": {"id": "nws_alerts", "label": "NWS Weather Alerts", "enabled": True, "count": 0, "logical_count": 0},
        "nifc_fire_perimeters": {"id": "nifc_fire_perimeters", "label": "NIFC Fire Perimeters", "enabled": True, "count": 0, "logical_count": 0},
        "nasa_firms": {"id": "nasa_firms", "label": "NASA FIRMS", "enabled": True, "count": 0, "logical_count": 0},
        "nhc_tropical": {"id": "nhc_tropical", "label": "NOAA NHC", "enabled": True, "count": 0, "logical_count": 0},
        "ais_vessels": {"id": "ais_vessels", "label": "AIS", "enabled": True, "count": 0, "logical_count": 0},
        "source_extension:line": dynamic_row("line", "Bravo Line Source", ["LineString"], 0),
        "source_extension:mixed": dynamic_row("mixed", "Charlie Mixed Source", ["Point", "Polygon"], 0),
        "source_extension:polygon": dynamic_row("polygon", "Delta Polygon Source", ["Polygon"], 0),
    }
    objects: list[dict] = []
    if include_alpha:
        label = "Alpha Renamed" if renamed else "Alpha Point Source"
        sources["source_extension:alpha"] = dynamic_row("alpha", label, ["Point"], 1)
        objects.append(feature("alpha-1", "source_extension:alpha", {"type": "Point", "coordinates": [-77.0, 38.9]}, "Alpha One"))
    return {
        "ok": True,
        "api_version": "gateway-data-v1",
        "full": True,
        "revision": revision,
        "generated_at": f"2026-08-02T15:{revision:02d}:00Z",
        "sources": sources,
        "source_registry": {
            "dynamic_source_discovery": True,
            "dynamic_source_prefix": "source_extension:",
            "source_extension_registry_version": "source-extension-registry-v1-i191",
        },
        "objects": objects,
        "deleted_uids": [],
    }


FIXTURE = f"""<!doctype html><html><head><meta charset=\"utf-8\"><base href=\"{ORIGIN}/\"><style>
body{{background:#06090d;color:#e9f0f5;font-family:sans-serif}}#sidebar{{width:410px}}.panel{{display:block;border:1px solid #273642;padding:12px;margin:8px}}
</style></head><body><aside id=\"sidebar\"><div class=\"panel\" data-collapse-key=\"adsbSettings\"><h2>ADS-B</h2></div><div class=\"panel\" id=\"satelliteTrackingPanelV409\"><h2>Satellite Tracking</h2></div></aside>
<script>
const __storageValues=new Map();
const localStorage={{getItem:k=>__storageValues.has(String(k))?__storageValues.get(String(k)):null,setItem:(k,v)=>__storageValues.set(String(k),String(v)),removeItem:k=>__storageValues.delete(String(k)),clear:()=>__storageValues.clear(),key:i=>Array.from(__storageValues.keys())[i]||null,get length(){{return __storageValues.size}}}};
window.__layers=[];window.__mapLayers=new Set();
class Emitter{{constructor(){{this.handlers={{}}}}on(t,f){{(this.handlers[t]||(this.handlers[t]=[])).push(f);return this}}off(t,f){{if(this.handlers[t])this.handlers[t]=this.handlers[t].filter(x=>x!==f);return this}}fire(t,e={{}}){{for(const f of (this.handlers[t]||[]).slice())f(Object.assign({{target:this}},e));return this}}}}
class Popup{{constructor(html,opts,owner){{this.html=html;this.options=opts||{{}};this.owner=owner;this.root=document.createElement('div');this.root.innerHTML='<a class=\"leaflet-popup-close-button\">×</a><div class=\"leaflet-popup-content\"></div>';this.root.querySelector('.leaflet-popup-content').innerHTML=html}}setContent(v){{this.html=v;this.root.querySelector('.leaflet-popup-content').innerHTML=v;return this}}getElement(){{return this.root}}setLatLng(){{return this}}openOn(){{return this}}}}
class Layer extends Emitter{{constructor(kind,data,options){{super();this.kind=kind;this.data=data;this.options=options||{{}};this.children=[];window.__layers.push(this)}}addTo(parent){{parent.addLayer(this);return this}}bindPopup(html,opts){{this.popup=new Popup(html,opts,this);return this}}getPopup(){{return this.popup||null}}setPopupContent(v){{if(this.popup)this.popup.setContent(v);return this}}setLatLng(v){{this.data=v;return this}}setIcon(v){{this.options.icon=v;return this}}setLatLngs(v){{this.data=v;return this}}setStyle(v){{this.options=Object.assign(this.options,v);return this}}getLatLng(){{return this.data}}getCenter(){{return Array.isArray(this.data&&this.data[0])?this.data[0]:this.data}}getBounds(){{return {{getCenter:()=>this.getCenter()}}}}}}
class Group extends Layer{{constructor(){{super('group',null,{{}})}}addLayer(x){{if(!this.children.includes(x))this.children.push(x);return this}}removeLayer(x){{this.children=this.children.filter(y=>y!==x);return this}}hasLayer(x){{return this.children.includes(x)}}clearLayers(){{this.children=[];return this}}}}
const events=new Emitter();window.map=Object.assign(events,{{_zoom:9,_popup:null,hasLayer:l=>window.__mapLayers.has(l),addLayer:l=>{{window.__mapLayers.add(l);return window.map}},removeLayer:l=>{{window.__mapLayers.delete(l);return window.map}},getZoom(){{return this._zoom}},closePopup(){{return this}},invalidateSize(){{return this}}}});
window.L={{layerGroup:()=>new Group(),marker:(x,o)=>new Layer('marker',x,o),polyline:(x,o)=>new Layer('polyline',x,o),polygon:(x,o)=>new Layer('polygon',x,o),divIcon:o=>o,latLngBounds:()=>({{}}),DomEvent:{{stopPropagation(){{}},preventDefault(){{}}}}}};
</script><script id=\"takMapGatewayDataLoaderV476\" src=\"/assets/runtime/tak-map-gateway-data-v491.js?v=1.3.0-i614\"></script></body></html>"""


def main() -> int:
    chromium = next((n for n in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable") if shutil.which(n)), None)
    if not chromium:
        raise SystemExit("Chromium is required")

    from playwright.sync_api import sync_playwright

    requests: list[str] = []
    response_number = {"value": 0}
    page_errors: list[str] = []

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=shutil.which(chromium), args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"])
        context = browser.new_context()
        page = context.new_page()
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        def route_request(route):
            parsed = urllib.parse.urlsplit(route.request.url)
            if parsed.path == "/":
                route.fulfill(status=200, content_type="text/html; charset=utf-8", body=FIXTURE)
                return
            if parsed.path == "/assets/runtime/tak-map-gateway-data-v491.js":
                route.fulfill(status=200, content_type="application/javascript; charset=utf-8", body=ASSET.read_text())
                return
            if parsed.path == "/api/tak-map/gateway-data/snapshot":
                requests.append(route.request.url)
                response_number["value"] += 1
                n = response_number["value"]
                if n <= 3:
                    body = payload(n)
                elif n == 4:
                    body = payload(4, include_alpha=False)
                else:
                    body = payload(n, include_alpha=True, renamed=True)
                route.fulfill(status=200, content_type="application/json", body=json.dumps(body, separators=(",", ":")))
                return
            route.fulfill(status=404, content_type="text/plain", body="not found")

        page.route("**/*", route_request)
        page.set_content(FIXTURE, wait_until="domcontentloaded")
        page.wait_for_function("window.TakMapGatewayDataV476 && window.TakMapGatewayDataV476.diagnostics().revision === 1", timeout=20000)

        initial = page.evaluate("""() => {
          const api=window.TakMapGatewayDataV476,d=api.diagnostics();
          const rows=[...document.querySelectorAll('#gatewayDataRowsV476 [data-dynamic-source="1"]')];
          const alpha=document.querySelector('[data-source="source_extension:alpha"]');
          return {
            objects:d.objects,layers:d.layers,dynamic:d.dynamicSourcesDiscovered,skipped:d.dynamicObjectsSkipped,
            labels:rows.map(x=>x.querySelector('.source-label').textContent.trim()),
            alphaChecked:alpha.querySelector('input').checked,
            alphaCount:alpha.querySelector('.source-count').textContent,
            alphaIcon:alpha.querySelector('.source-icon').className,
            lineIcon:document.querySelector('[data-source="source_extension:line"] .source-icon').className,
            polygonIcon:document.querySelector('[data-source="source_extension:polygon"] .source-icon').className,
            mixedIcon:document.querySelector('[data-source="source_extension:mixed"] .source-icon').className,
            stored:localStorage.getItem('takmap.gatewayData.ingest.source_extension:alpha')
          };
        }""")
        assert initial["objects"] == 0 and initial["layers"] == 0, initial
        assert initial["dynamic"] == 4 and initial["skipped"] >= 1, initial
        assert initial["alphaChecked"] is False and initial["alphaCount"] == "1", initial
        assert initial["stored"] is None, initial
        assert initial["labels"] == ["Alpha Point Source", "Bravo Line Source", "Charlie Mixed Source", "Delta Polygon Source"], initial
        assert "dot dynamic" in initial["alphaIcon"], initial
        assert "dynamic line" in initial["lineIcon"], initial
        assert "polygon dynamic" in initial["polygonIcon"], initial
        assert "dynamic mixed" in initial["mixedIcon"], initial

        page.eval_on_selector('[data-source="source_extension:alpha"] input', "el=>{el.checked=true;el.dispatchEvent(new Event('change',{bubbles:true}))}")
        page.wait_for_function("window.TakMapGatewayDataV476.diagnostics().revision === 2 && window.TakMapGatewayDataV476.diagnostics().objects === 1", timeout=20000)
        enabled = page.evaluate("""() => {
          const d=window.TakMapGatewayDataV476.diagnostics();
          const marker=window.__layers.find(x=>x.kind==='marker'&&x.__gatewayFeatureV476&&x.__gatewayFeatureV476.id==='alpha-1');
          const sourceLabel=marker&&marker.__gatewayFeatureV476&&marker.__gatewayFeatureV476.properties&&marker.__gatewayFeatureV476.properties.source;
          return {objects:d.objects,layers:d.layers,enabled:d.dynamicSourcesIngestEnabled,stored:localStorage.getItem('takmap.gatewayData.ingest.source_extension:alpha'),sourceLabel,mapGroups:window.__mapLayers.size,version:d.version,floating:d.floatingLeafletPopups};
        }""")
        assert enabled["objects"] == 1 and enabled["layers"] == 1 and enabled["enabled"] == 1, enabled
        assert enabled["stored"] == "1", enabled
        assert enabled["sourceLabel"] == "source_extension:alpha", enabled
        assert enabled["version"] == "i614" and enabled["floating"] is False, enabled
        assert enabled["mapGroups"] >= 1, enabled

        page.eval_on_selector('[data-source="source_extension:alpha"] input', "el=>{el.checked=false;el.dispatchEvent(new Event('change',{bubbles:true}))}")
        page.wait_for_function("window.TakMapGatewayDataV476.diagnostics().objects === 0 && window.TakMapGatewayDataV476.diagnostics().layers === 0")
        disabled = page.evaluate("""() => ({stored:localStorage.getItem('takmap.gatewayData.ingest.source_extension:alpha'), row:!!document.querySelector('[data-source="source_extension:alpha"]'), mapGroups:window.__mapLayers.size, d:window.TakMapGatewayDataV476.diagnostics()})""")
        assert disabled["stored"] == "0" and disabled["row"] is True, disabled
        assert disabled["d"]["dynamicObjectsCleared"] >= 1, disabled

        page.eval_on_selector('[data-source="source_extension:alpha"] input', "el=>{el.checked=true;el.dispatchEvent(new Event('change',{bubbles:true}))}")
        page.wait_for_function("window.TakMapGatewayDataV476.diagnostics().revision === 3 && window.TakMapGatewayDataV476.diagnostics().objects === 1", timeout=20000)

        page.evaluate("window.TakMapGatewayDataV476.refresh()")
        page.wait_for_function("window.TakMapGatewayDataV476.diagnostics().revision === 4", timeout=20000)
        removed = page.evaluate("""() => ({row:!!document.querySelector('[data-source="source_extension:alpha"]'), objects:window.TakMapGatewayDataV476.diagnostics().objects, stored:localStorage.getItem('takmap.gatewayData.ingest.source_extension:alpha')})""")
        assert removed == {"row": False, "objects": 0, "stored": "1"}, removed

        page.evaluate("window.TakMapGatewayDataV476.refresh()")
        page.wait_for_function("window.TakMapGatewayDataV476.diagnostics().revision >= 5 && window.TakMapGatewayDataV476.diagnostics().objects === 1", timeout=20000)
        returned = page.evaluate("""() => {const row=document.querySelector('[data-source="source_extension:alpha"]');return {label:row.querySelector('.source-label').textContent.trim(),checked:row.querySelector('input').checked,objects:window.TakMapGatewayDataV476.diagnostics().objects,stored:localStorage.getItem('takmap.gatewayData.ingest.source_extension:alpha')};}""")
        assert returned == {"label": "Alpha Renamed", "checked": True, "objects": 1, "stored": "1"}, returned

        # Master is display-only: it must hide the group without changing the dynamic ingest preference or object cache.
        page.eval_on_selector("#gatewayDataMasterV476", "el=>{el.checked=false;el.dispatchEvent(new Event('change',{bubbles:true}))}")
        master_off = page.evaluate("""() => ({objects:window.TakMapGatewayDataV476.diagnostics().objects,stored:localStorage.getItem('takmap.gatewayData.ingest.source_extension:alpha'),groups:window.__mapLayers.size})""")
        assert master_off["objects"] == 1 and master_off["stored"] == "1" and master_off["groups"] == 0, master_off

        page.eval_on_selector("#gatewayDataMasterV476", "el=>{el.checked=true;el.dispatchEvent(new Event('change',{bubbles:true}))}")
        page.evaluate("document.body.classList.add('replay-mode-v415'); window.TakMapGatewayDataV476.refresh()")
        page.wait_for_function("window.TakMapGatewayDataV476.diagnostics().revision >= 6 && window.TakMapGatewayDataV476.diagnostics().replaySuppressed === true", timeout=20000)
        replay = page.evaluate("""() => ({objects:window.TakMapGatewayDataV476.diagnostics().objects,stored:localStorage.getItem('takmap.gatewayData.ingest.source_extension:alpha'),groups:window.__mapLayers.size,inputDisabled:document.querySelector('[data-source="source_extension:alpha"] input').disabled})""")
        assert replay["objects"] == 1 and replay["stored"] == "1" and replay["groups"] == 0 and replay["inputDisabled"] is True, replay

        browser.close()

    assert not page_errors, page_errors
    assert len(requests) >= 6, requests
    assert all(url.startswith(ORIGIN + "/api/tak-map/gateway-data/snapshot?") for url in requests), requests
    print("TAK Map i614 dynamic Source Extension discovery/local-ingest browser test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
