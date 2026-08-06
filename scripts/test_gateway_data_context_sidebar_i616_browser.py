#!/usr/bin/env python3
"""Browser contract for i616 curated read-only Gateway Data contexts."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
GATEWAY_JS = (ROOT / "assets" / "tak-map-gateway-data-v491.js").read_text()
CONTEXT_JS = (ROOT / "assets" / "tak-map-context-sidebar-i572.js").read_text()
ORIGIN = "https://takmap.test"


def payload() -> dict:
    return {
        "ok": True,
        "full": True,
        "revision": 616,
        "generated_at": "2026-08-06T10:55:25Z",
        "source_registry": {"dynamic_source_discovery": True},
        "sources": {
            "usgs_earthquakes": {"enabled": True, "label": "USGS Earthquakes", "count": 1},
            "nws_alerts": {"enabled": True, "label": "NWS Weather Alerts", "count": 1},
            "nifc_fire_perimeters": {"enabled": True, "label": "NIFC Fire Perimeters", "count": 1},
        },
        "objects": [
            {
                "type": "Feature",
                "id": "eq-1",
                "geometry": {"type": "Point", "coordinates": [-123.02, 38.82]},
                "properties": {
                    "uid": "eq-1",
                    "source": "usgs_earthquakes",
                    "title": "USGS M4.2 8 km ESE of Cloverdale, CA",
                    "event_time": "2026-07-29T02:40:00Z",
                    "stale_at": "2099-01-01T00:00:00Z",
                    "remarks": "\n".join([
                        "USGS Earthquake",
                        "Magnitude: 4.2",
                        "Location: 8 km ESE of Cloverdale, CA",
                        "Time: 2026-07-29T02:40:00Z",
                        "Depth: 5.9 km",
                        "Distance: 411.6 mi",
                        "Alert: green",
                        "Status: reviewed",
                        "Event status: active",
                        "Source: USGS Earthquake Hazards Program",
                    ]),
                    "metadata": {"magnitude": "4.2", "depth_km": "5.9"},
                },
            },
            {
                "type": "Feature",
                "id": "nws-1",
                "geometry": {"type": "Polygon", "coordinates": [[[-118.4, 34.2], [-117.9, 34.2], [-117.9, 34.7], [-118.4, 34.7], [-118.4, 34.2]]]},
                "properties": {
                    "uid": "nws-1",
                    "source": "nws_alerts",
                    "title": "NWS Extreme Heat Warning",
                    "event_time": "2026-08-06T10:55:25Z",
                    "stale_at": "2099-01-01T00:00:00Z",
                    "remarks": "\n".join([
                        "Merged NWS Weather Alerts: 5",
                        "Coverage: canonical NWS boundaries with one-owner shared seams",
                        "Underlying display areas (internal boundaries omitted)",
                        "NWS Weather Alert: Extreme Heat Warning",
                        "CAP severity: Severe",
                        "Urgency/Certainty: Expected/Likely",
                        "Area: Western Antelope Valley Foothills; Eastern Antelope Valley Foothills; Antelope Valley; Apple and Lucerne Valleys; Coachella Valley;",
                        "Effective: 2026-08-06T11:00:00Z",
                        "Expires: 2026-08-07T20:00:00Z",
                        "Headline: Dangerously hot conditions are expected.",
                        "Description: Source-provided description.",
                        "Instruction: Drink plenty of fluids.",
                        "Source: National Weather Service api.weather.gov",
                        "urn:oid:internal-alert-id",
                    ]),
                    "metadata": {
                        "event": "Extreme Heat Warning",
                        "rank_label": "Warning",
                        "area": "Western Antelope Valley Foothills; Eastern Antelope Valley Foothills; Antelope Valley; Apple and Lucerne Valleys; Coachella Valley;",
                        "effective": "2026-08-06T11:00:00Z",
                        "expires": "2026-08-07T20:00:00Z",
                        "headline": "Dangerously hot conditions are expected.",
                        "description": "Source-provided description.",
                        "instruction": "Drink plenty of fluids.",
                        "urgency": "Expected",
                        "certainty": "Likely",
                    },
                },
                "style": {"stroke": "#ff0000", "stroke_weight": 3, "fill": "#ff0000", "fill_opacity": 0.18},
            },
            {
                "type": "Feature",
                "id": "nifc-1",
                "geometry": {"type": "Polygon", "coordinates": [[[-116.4, 37.1], [-116.1, 37.1], [-116.1, 37.4], [-116.4, 37.4], [-116.4, 37.1]]]},
                "properties": {
                    "uid": "nifc-1",
                    "source": "nifc_fire_perimeters",
                    "title": "NIFC Wildfire: Summit",
                    "event_time": "2026-08-06T10:03:20Z",
                    "stale_at": "2099-01-01T00:00:00Z",
                    "remarks": "\n".join([
                        "NIFC Fire Perimeter Incident: Summit",
                        "Type: Wildfire",
                        "Acres: 2690.0",
                        "Contained: 100%",
                        "Updated: 2026-07-23T23:25:37Z",
                        "Discovered: 2026-07-10T19:48:05Z",
                        "State: US-CA",
                        "Distance from center: 39.3 mi",
                        "Source: 2026 NIFS; WFIGS Current Interagency Fire Perimeters",
                    ]),
                    "metadata": {"incident_name": "Summit", "incident_type": "WF", "acres": "2690.00"},
                },
                "style": {"stroke": "#ff0000", "stroke_weight": 3, "fill": "#ff0000", "fill_opacity": 0.18},
            },
        ],
        "deleted_uids": [],
    }


FIXTURE = f"""<!doctype html><html><head><meta charset='utf-8'><base href='{ORIGIN}/'><style>
html,body{{margin:0;width:100%;height:100%;background:#071117;color:#e9f0f5}}#map{{position:relative;width:100%;height:100%}}.panel{{display:block}}#mainToolbar{{position:absolute;right:8px;top:60px;z-index:9000;width:45px;height:400px;background:#22333d}}
</style></head><body><aside id='sidebar'><div class='panel' data-collapse-key='adsbSettings'><h2>ADS-B</h2></div><div class='panel' id='satelliteTrackingPanelV409'><h2>Satellite</h2></div></aside><div id='map'><div id='mainToolbar'></div></div>
<script>
const __storageValues=new Map();const localStorage={{getItem:k=>__storageValues.has(String(k))?__storageValues.get(String(k)):null,setItem:(k,v)=>__storageValues.set(String(k),String(v)),removeItem:k=>__storageValues.delete(String(k)),clear:()=>__storageValues.clear(),key:i=>Array.from(__storageValues.keys())[i]||null,get length(){{return __storageValues.size}}}};
window.ResizeObserver=class{{constructor(cb){{this.cb=cb}}observe(){{}}disconnect(){{}}}};window.__layers=[];window.__mapLayers=new Set();window.lastDataSync={{objects:[]}};window.importedFeatures=()=>[];
class Emitter{{constructor(){{this.handlers={{}}}}on(t,f){{String(t).split(/\s+/).forEach(k=>(this.handlers[k]||(this.handlers[k]=[])).push(f));return this}}off(t,f){{String(t).split(/\s+/).forEach(k=>{{if(!this.handlers[k])return;this.handlers[k]=f?this.handlers[k].filter(x=>x!==f):[]}});return this}}fire(t,e={{}}){{for(const f of (this.handlers[t]||[]).slice())f(Object.assign({{target:this,sourceTarget:this}},e));return this}}}}
class Layer extends Emitter{{constructor(kind,data,options){{super();this.kind=kind;this.data=data;this.options=Object.assign({{}},options||{{}});this._icon=document.createElement('div');this._icon.className=(this.options.icon&&this.options.icon.className)||'';window.__layers.push(this)}}addTo(parent){{parent.addLayer(this);return this}}unbindPopup(){{return this}}setLatLng(v){{this.data=v;return this}}setIcon(v){{this.options.icon=v;return this}}setLatLngs(v){{this.data=v;return this}}setStyle(v){{this.options=Object.assign(this.options,v);return this}}bringToFront(){{return this}}setZIndexOffset(v){{this.zIndexOffset=v;return this}}getElement(){{return this._icon}}getLatLng(){{return Array.isArray(this.data)&&typeof this.data[0]==='number'?{{lat:this.data[0],lng:this.data[1]}}:this.data}}getBounds(){{const pts=[];const walk=v=>{{if(Array.isArray(v)&&v.length>=2&&Number.isFinite(Number(v[0]))&&Number.isFinite(Number(v[1])))pts.push(v);else if(Array.isArray(v))v.forEach(walk)}};walk(this.data);let lat=0,lng=0;pts.forEach(p=>{{lat+=Number(p[0]);lng+=Number(p[1])}});return {{getCenter:()=>({{lat:pts.length?lat/pts.length:0,lng:pts.length?lng/pts.length:0}}),contains:()=>true}}}}}}
class Group extends Layer{{constructor(){{super('group',null,{{}});this.children=[]}}addLayer(x){{if(!this.children.includes(x))this.children.push(x);return this}}removeLayer(x){{this.children=this.children.filter(y=>y!==x);return this}}hasLayer(x){{return this.children.includes(x)}}clearLayers(){{this.children=[];return this}}}}
const events=new Emitter();window.map=Object.assign(events,{{_zoom:8,hasLayer:l=>window.__mapLayers.has(l),addLayer:l=>{{window.__mapLayers.add(l);return window.map}},removeLayer:l=>{{window.__mapLayers.delete(l);return window.map}},getZoom(){{return this._zoom}},getContainer(){{return document.getElementById('map')}},getBounds(){{return {{contains:()=>true}}}},panTo(){{return this}},setView(){{return this}}}});window.takLeafletMap=window.map;
window.L={{layerGroup:()=>new Group(),marker:(x,o)=>new Layer('marker',x,o),polyline:(x,o)=>new Layer('polyline',x,o),polygon:(x,o)=>new Layer('polygon',x,o),divIcon:o=>o,DomEvent:{{stopPropagation(){{}},preventDefault(){{}},disableClickPropagation(){{}},disableScrollPropagation(){{}}}}}};
</script><script src='/assets/runtime/tak-map-context-sidebar-i572.js?v=1.3.0-i616'></script><script src='/assets/runtime/tak-map-gateway-data-v491.js?v=1.3.0-i616'></script></body></html>"""


def main() -> int:
    chromium = next((shutil.which(n) for n in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable") if shutil.which(n)), None)
    if not chromium:
        raise SystemExit("Chromium is required")
    from playwright.sync_api import sync_playwright

    page_errors: list[str] = []
    console_errors: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=chromium, args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"])
        page = browser.new_page(viewport={"width": 1280, "height": 820})
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        def route_request(route):
            path = urllib.parse.urlsplit(route.request.url).path
            if path == "/assets/runtime/tak-map-context-sidebar-i572.js":
                route.fulfill(status=200, content_type="application/javascript", body=CONTEXT_JS)
            elif path == "/assets/runtime/tak-map-gateway-data-v491.js":
                route.fulfill(status=200, content_type="application/javascript", body=GATEWAY_JS)
            elif path == "/api/tak-map/gateway-data/snapshot":
                route.fulfill(status=200, content_type="application/json", body=json.dumps(payload()))
            else:
                route.fulfill(status=204, body="")

        page.route("**/*", route_request)
        page.set_content(FIXTURE, wait_until="domcontentloaded", timeout=20_000)
        page.wait_for_function("window.TakMapGatewayDataV476 && window.TakMapGatewayDataV476.diagnostics().revision === 616", timeout=20_000)

        result = page.evaluate("""async () => {
          const click=async uid=>{const layer=window.__layers.find(x=>x._takGatewayUid===uid);layer.fire('click',{originalEvent:{stopPropagation(){},preventDefault(){}}});await new Promise(r=>setTimeout(r,50));const body=document.getElementById('takMapContextSidebarBodyI572'),panel=document.getElementById('takMapContextSidebarI572');return {text:body.textContent,html:body.innerHTML,h3:body.querySelectorAll('h3').length,panelZ:Number(getComputedStyle(panel).zIndex),toolbarZ:Number(getComputedStyle(document.getElementById('mainToolbar')).zIndex),title:document.getElementById('takMapContextTitleI572').textContent,kicker:document.getElementById('takMapContextKickerI572').textContent,mainAreas:body.querySelectorAll('.gateway-areas-i616 > .gateway-area-list-i616 > li').length,moreText:body.querySelector('.gateway-areas-more-i616 > summary')?.textContent||'',allAreas:body.querySelectorAll('.gateway-areas-more-i616 .gateway-area-list-i616 li').length};};
          return {version:window.TakMapGatewayDataV476.diagnostics().version,usgs:await click('eq-1'),nws:await click('nws-1'),nifc:await click('nifc-1')};
        }""")
        browser.close()

    assert result["version"] == "i616", result
    for panel in (result["usgs"], result["nws"], result["nifc"]):
        assert panel["h3"] == 0, panel
        assert panel["panelZ"] > panel["toolbarZ"], panel
        assert panel["kicker"].startswith("Gateway Data · "), panel

    usgs = result["usgs"]
    for value in ("Magnitude", "4.2", "Location", "8 km ESE of Cloverdale, CA", "Time", "Depth", "5.9 km", "Alert", "green", "Review", "reviewed"):
        assert value in usgs["text"], (value, usgs)
    for forbidden in ("Details", "411.6", "Event status", "active"):
        assert forbidden not in usgs["text"], (forbidden, usgs)

    nws = result["nws"]
    assert nws["mainAreas"] == 3 and nws["allAreas"] == 2 and nws["moreText"] == "+2 more", nws
    for value in ("Affected areas", "Western Antelope Valley Foothills", "Description", "Source-provided description.", "Instruction", "Drink plenty of fluids."):
        assert value in nws["text"], (value, nws)
    for forbidden in ("Merged NWS", "canonical NWS", "urn:oid", "Details"):
        assert forbidden not in nws["text"], (forbidden, nws)

    nifc = result["nifc"]
    for value in ("Incident", "Summit", "Type", "Wildfire", "Acres", "2,690", "Containment", "100%", "Discovered", "Source updated", "State", "US-CA"):
        assert value in nifc["text"], (value, nifc)
    for forbidden in ("Details", "WF"):
        assert forbidden not in nifc["text"], (forbidden, nifc)

    assert not page_errors, page_errors
    assert not console_errors, console_errors
    print("TAK Map i616 curated Gateway Data context browser test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
