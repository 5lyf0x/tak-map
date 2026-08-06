#!/usr/bin/env python3
"""Browser contract for i617 top-overlay, scrolling, and regional-unit Gateway Data contexts."""
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
        "revision": 617,
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
                        "Area: Western Antelope Valley Foothills; Eastern Antelope Valley Foothills; Antelope Valley; Apple and Lucerne Valleys; Coachella Valley; San Diego County Deserts; San Gorgonio Pass Near Banning; Northwest Plateau; Lake Havasu and Fort Mohave; Lake Mead - AZ side; Lake Mohave - AZ side; Hualapai Mountains; Northwest Deserts; Death Valley National Park; Western Mojave Desert; Eastern Mojave Desert, Including the Mojave National Preserve; Morongo Basin; Cadiz Basin; San Bernardino County-Upper Colorado River Valley; Owens Valley South; Owens Valley North; Esmeralda and Central Nye County; Lincoln County; Northeast Clark County; Western Clark and Southern Nye County; Las Vegas Valley; Southern Clark County; Lake Mead - NV side; Lake Mohave - NV side; Indian Wells Valley; Mojave Desert Slopes; Mojave Desert;",
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
                        "area": "Western Antelope Valley Foothills; Eastern Antelope Valley Foothills; Antelope Valley; Apple and Lucerne Valleys; Coachella Valley; San Diego County Deserts; San Gorgonio Pass Near Banning; Northwest Plateau; Lake Havasu and Fort Mohave; Lake Mead - AZ side; Lake Mohave - AZ side; Hualapai Mountains; Northwest Deserts; Death Valley National Park; Western Mojave Desert; Eastern Mojave Desert, Including the Mojave National Preserve; Morongo Basin; Cadiz Basin; San Bernardino County-Upper Colorado River Valley; Owens Valley South; Owens Valley North; Esmeralda and Central Nye County; Lincoln County; Northeast Clark County; Western Clark and Southern Nye County; Las Vegas Valley; Southern Clark County; Lake Mead - NV side; Lake Mohave - NV side; Indian Wells Valley; Mojave Desert Slopes; Mojave Desert;",
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
html,body{{margin:0;width:100%;height:100%;background:#071117;color:#e9f0f5}}#map{{position:relative;width:100%;height:100%}}.panel{{display:block}}#mainToolbar{{position:absolute;right:8px;top:60px;z-index:2147481000;width:45px;height:400px;background:#22333d}}#topModal{{position:fixed;inset:20px;display:none;z-index:2147483000;background:#111}}
</style></head><body><aside id='sidebar'><div class='panel' data-collapse-key='adsbSettings'><h2>ADS-B</h2></div><div class='panel' id='satelliteTrackingPanelV409'><h2>Satellite</h2></div></aside><div id='map'><div id='mainToolbar'></div></div><div id='topModal'></div>
<script>
const __storageValues=new Map();const localStorage={{getItem:k=>__storageValues.has(String(k))?__storageValues.get(String(k)):null,setItem:(k,v)=>__storageValues.set(String(k),String(v)),removeItem:k=>__storageValues.delete(String(k)),clear:()=>__storageValues.clear(),key:i=>Array.from(__storageValues.keys())[i]||null,get length(){{return __storageValues.size}}}};
window.ResizeObserver=class{{constructor(cb){{this.cb=cb}}observe(){{}}disconnect(){{}}}};window.__layers=[];window.__mapLayers=new Set();window.lastDataSync={{objects:[]}};window.importedFeatures=()=>[];
class Emitter{{constructor(){{this.handlers={{}}}}on(t,f){{String(t).split(/\s+/).forEach(k=>(this.handlers[k]||(this.handlers[k]=[])).push(f));return this}}off(t,f){{String(t).split(/\s+/).forEach(k=>{{if(!this.handlers[k])return;this.handlers[k]=f?this.handlers[k].filter(x=>x!==f):[]}});return this}}fire(t,e={{}}){{for(const f of (this.handlers[t]||[]).slice())f(Object.assign({{target:this,sourceTarget:this}},e));return this}}}}
class Layer extends Emitter{{constructor(kind,data,options){{super();this.kind=kind;this.data=data;this.options=Object.assign({{}},options||{{}});this._icon=document.createElement('div');this._icon.className=(this.options.icon&&this.options.icon.className)||'';window.__layers.push(this)}}addTo(parent){{parent.addLayer(this);return this}}unbindPopup(){{return this}}setLatLng(v){{this.data=v;return this}}setIcon(v){{this.options.icon=v;return this}}setLatLngs(v){{this.data=v;return this}}setStyle(v){{this.options=Object.assign(this.options,v);return this}}bringToFront(){{return this}}setZIndexOffset(v){{this.zIndexOffset=v;return this}}getElement(){{return this._icon}}getLatLng(){{return Array.isArray(this.data)&&typeof this.data[0]==='number'?{{lat:this.data[0],lng:this.data[1]}}:this.data}}getBounds(){{const pts=[];const walk=v=>{{if(Array.isArray(v)&&v.length>=2&&Number.isFinite(Number(v[0]))&&Number.isFinite(Number(v[1])))pts.push(v);else if(Array.isArray(v))v.forEach(walk)}};walk(this.data);let lat=0,lng=0;pts.forEach(p=>{{lat+=Number(p[0]);lng+=Number(p[1])}});return {{getCenter:()=>({{lat:pts.length?lat/pts.length:0,lng:pts.length?lng/pts.length:0}}),contains:()=>true}}}}}}
class Group extends Layer{{constructor(){{super('group',null,{{}});this.children=[]}}addLayer(x){{if(!this.children.includes(x))this.children.push(x);return this}}removeLayer(x){{this.children=this.children.filter(y=>y!==x);return this}}hasLayer(x){{return this.children.includes(x)}}clearLayers(){{this.children=[];return this}}}}
const events=new Emitter();window.map=Object.assign(events,{{_zoom:8,hasLayer:l=>window.__mapLayers.has(l),addLayer:l=>{{window.__mapLayers.add(l);return window.map}},removeLayer:l=>{{window.__mapLayers.delete(l);return window.map}},getZoom(){{return this._zoom}},getContainer(){{return document.getElementById('map')}},getBounds(){{return {{contains:()=>true}}}},panTo(){{return this}},setView(){{return this}}}});window.takLeafletMap=window.map;
window.L={{layerGroup:()=>new Group(),marker:(x,o)=>new Layer('marker',x,o),polyline:(x,o)=>new Layer('polyline',x,o),polygon:(x,o)=>new Layer('polygon',x,o),divIcon:o=>o,DomEvent:{{stopPropagation(){{}},preventDefault(){{}},disableClickPropagation(){{}},disableScrollPropagation(){{}}}}}};
</script><script src='/assets/runtime/tak-map-context-sidebar-i572.js?v=1.3.0-i617'></script><script src='/assets/runtime/tak-map-gateway-data-v491.js?v=1.3.0-i617'></script></body></html>"""


def main() -> int:
    chromium = next((shutil.which(n) for n in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable") if shutil.which(n)), None)
    if not chromium:
        raise SystemExit("Chromium is required")
    from playwright.sync_api import sync_playwright

    page_errors: list[str] = []
    console_errors: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=chromium, args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"])
        page = browser.new_page(viewport={"width": 1440, "height": 900}, locale="en-US")
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
        page.wait_for_function("window.TakMapGatewayDataV476 && window.TakMapGatewayDataV476.diagnostics().revision === 617", timeout=20_000)

        result = page.evaluate(r"""async () => {
          const wait=ms=>new Promise(r=>setTimeout(r,ms));
          const click=async uid=>{const layer=window.__layers.find(x=>x._takGatewayUid===uid);if(!layer)throw new Error('missing layer '+uid);layer.fire('click',{originalEvent:{stopPropagation(){},preventDefault(){}}});await wait(80);const body=document.getElementById('takMapContextSidebarBodyI572'),panel=document.getElementById('takMapContextSidebarI572'),toolbar=document.getElementById('mainToolbar'),modal=document.getElementById('topModal');return {text:body.textContent,html:body.innerHTML,h3:body.querySelectorAll('h3').length,parentIsBody:panel.parentNode===document.body,panelZ:Number(getComputedStyle(panel).zIndex),toolbarZ:Number(getComputedStyle(toolbar).zIndex),modalZ:Number(getComputedStyle(modal).zIndex),panelWidth:panel.getBoundingClientRect().width,title:document.getElementById('takMapContextTitleI572').textContent,kicker:document.getElementById('takMapContextKickerI572').textContent,scrollbarColor:getComputedStyle(body).scrollbarColor,scrollHeight:body.scrollHeight,clientHeight:body.clientHeight};};
          localStorage.setItem('takmap.units','imperial');
          const usgsImperial=await click('eq-1');
          const nws=await click('nws-1');
          const details=document.querySelector('.gateway-areas-more-i617');
          const collapsed={preview:document.querySelectorAll('.gateway-area-preview-i617 li').length,allLabel:document.querySelector('.gateway-areas-show-all-i617')?.textContent||'',fewerDisplay:getComputedStyle(document.querySelector('.gateway-areas-show-fewer-i617')).display};
          details.open=true;details.dispatchEvent(new Event('toggle'));await wait(30);
          const body=document.getElementById('takMapContextSidebarBodyI572');
          const expanded={total:document.querySelectorAll('.gateway-area-list-i617 li').length,rest:document.querySelectorAll('.gateway-area-rest-i617 li').length,allDisplay:getComputedStyle(document.querySelector('.gateway-areas-show-all-i617')).display,fewerText:document.querySelector('.gateway-areas-show-fewer-i617')?.textContent||'',fewerDisplay:getComputedStyle(document.querySelector('.gateway-areas-show-fewer-i617')).display,scrollHeight:body.scrollHeight,clientHeight:body.clientHeight};
          body.scrollTop=body.scrollHeight;await wait(20);expanded.scrollTop=body.scrollTop;expanded.reachedBottom=Math.abs((body.scrollTop+body.clientHeight)-body.scrollHeight)<3;
          details.open=false;details.dispatchEvent(new Event('toggle'));await wait(20);collapsed.afterCollapseAllDisplay=getComputedStyle(document.querySelector('.gateway-areas-show-all-i617')).display;collapsed.afterCollapseFewerDisplay=getComputedStyle(document.querySelector('.gateway-areas-show-fewer-i617')).display;
          localStorage.setItem('takmap.units','metric');
          const usgsMetric=await click('eq-1');
          const nifc=await click('nifc-1');
          return {version:window.TakMapGatewayDataV476.diagnostics().version,contextDiagnostics:window.TakMapContextSidebarI572.diagnostics(),usgsImperial,nws,collapsed,expanded,usgsMetric,nifc};
        }""")
        browser.close()

    assert result["version"] == "i617", result
    assert result["contextDiagnostics"]["gatewayTopOverlay"] is True, result
    assert result["contextDiagnostics"]["themedGatewayScrollbar"] is True, result
    assert result["contextDiagnostics"]["adaptiveGatewayWidth"] is True, result
    for panel in (result["usgsImperial"], result["nws"], result["usgsMetric"], result["nifc"]):
        assert panel["h3"] == 0, panel
        assert panel["parentIsBody"] is True, panel
        assert panel["panelZ"] > panel["toolbarZ"], panel
        assert panel["panelZ"] < panel["modalZ"], panel
        assert 430 <= panel["panelWidth"] <= 565, panel
        assert panel["kicker"].startswith("Gateway Data · "), panel
        assert panel["scrollbarColor"] not in ("auto", ""), panel

    usgs = result["usgsImperial"]
    for value in ("Magnitude", "4.2", "Location", "5 mi ESE of Cloverdale, CA", "Time", "Depth", "3.7 mi", "Status", "reviewed"):
        assert value in usgs["text"], (value, usgs)
    for forbidden in ("8 km ESE", "5.9 km", "Alert", "green", "Review", "Source program", "USGS Earthquake Hazards Program", "Event status", "411.6", "Details"):
        assert forbidden not in usgs["text"], (forbidden, usgs)
    assert "5 mi ESE of Cloverdale, CA" in usgs["title"], usgs

    metric = result["usgsMetric"]
    for value in ("8 km ESE of Cloverdale, CA", "5.9 km"):
        assert value in metric["text"] or value in metric["title"], (value, metric)
    for forbidden in ("5 mi ESE", "3.7 mi", "Alert", "Source program"):
        assert forbidden not in metric["text"] and forbidden not in metric["title"], (forbidden, metric)

    nws = result["nws"]
    assert result["collapsed"]["preview"] == 3, result
    assert result["collapsed"]["allLabel"] == "Show all 32 areas", result
    assert result["collapsed"]["fewerDisplay"] == "none", result
    assert result["expanded"]["total"] == 32 and result["expanded"]["rest"] == 29, result
    assert result["expanded"]["allDisplay"] == "none", result
    assert result["expanded"]["fewerText"] == "Show fewer" and result["expanded"]["fewerDisplay"] != "none", result
    assert result["expanded"]["scrollHeight"] > result["expanded"]["clientHeight"], result
    assert result["expanded"]["reachedBottom"] is True, result
    assert result["collapsed"]["afterCollapseAllDisplay"] != "none" and result["collapsed"]["afterCollapseFewerDisplay"] == "none", result
    for value in ("Affected areas", "Western Antelope Valley Foothills", "Mojave Desert", "Description", "Source-provided description.", "Instruction", "Drink plenty of fluids."):
        assert value in nws["html"], (value, nws)
    for forbidden in ("+29 more", "Merged NWS", "canonical NWS", "urn:oid", "Details"):
        assert forbidden not in nws["html"], (forbidden, nws)

    nifc = result["nifc"]
    for value in ("Incident", "Summit", "Type", "Wildfire", "Acres", "2,690", "Containment", "100%", "Discovered", "Source updated", "State", "US-CA"):
        assert value in nifc["text"], (value, nifc)
    for forbidden in ("Details", "WF"):
        assert forbidden not in nifc["text"], (forbidden, nifc)

    assert not page_errors, page_errors
    assert not console_errors, console_errors
    print("TAK Map i617 top-overlay, themed-scrollbar, NWS expansion, and regional USGS context browser test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
