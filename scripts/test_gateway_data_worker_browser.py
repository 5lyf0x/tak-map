#!/usr/bin/env python3
"""Exercise i491 Gateway Data startup retry, popups, labels, card, and NHC labels."""
from __future__ import annotations

import json
from pathlib import Path
import re
import runpy
import shutil
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "assets" / "tak-map-gateway-data-v491.js"
ORIGIN = "https://takmap.test"


def extract_card(html: str) -> str:
    start = html.index('<div class="panel gateway-data-v491"')
    token_re = re.compile(r"</?div\b", re.I)
    depth = 0
    for match in token_re.finditer(html, start):
        if html.startswith("</", match.start()):
            depth -= 1
            if depth == 0:
                close = html.find(">", match.start())
                if close >= 0:
                    return html[start : close + 1]
        else:
            depth += 1
    raise AssertionError("could not extract generated Gateway Data card")


def extract_core_collapsible(html: str) -> str:
    source = html
    if "function sectionIdFromTitle" not in source:
        source = (ROOT / "assets" / "tak-map-core-i541.js").read_text()
    start = source.index("function sectionIdFromTitle")
    end = source.index("async function init", start)
    return source[start:end]


def feature(uid: str, source: str, geometry: dict, metadata: dict, title: str, style: dict | None = None, remarks: str = "") -> dict:
    return {
        "type": "Feature",
        "id": uid,
        "geometry": geometry,
        "properties": {"source": source, "title": title, "metadata": metadata, "remarks": remarks, "stale_at": "2099-01-01T00:00:00Z"},
        "style": style or {},
        "revision": 7,
    }


def main() -> int:
    chromium = next((n for n in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable") if shutil.which(n)), None)
    if not chromium:
        raise SystemExit("Chromium is required")

    ns = runpy.run_path(str(ROOT / "tak_dashboard.py"), run_name="tak_map_i491_browser_fixture")
    html = ns["TAK_MAP_HTML"]
    card = extract_card(html)
    core_collapsible = extract_core_collapsible(html)

    fixture = f"""<!doctype html><html><head><meta charset="utf-8"><base href="{ORIGIN}/"><style>
body{{background:#06090d;color:#e9f0f5;font-family:sans-serif}}#sidebar{{width:396px}}.panel{{display:block;border:1px solid #273642;padding:12px;margin:8px}}.panel.collapsed .panel-body{{display:none}}
</style></head><body data-test-result="pending"><aside id="sidebar"><div class="panel" data-collapse-key="adsbSettings"><h2>ADS-B</h2></div>{card}<div class="panel" id="satelliteTrackingPanelV409"><h2>Satellite Tracking</h2></div></aside><pre id="result">pending</pre>
<script>
window.esc=s=>String(s);window.__testLayers=[];
class Emitter{{constructor(){{this.handlers={{}}}}on(t,f){{(this.handlers[t]||(this.handlers[t]=[])).push(f);return this}}off(t,f){{if(!this.handlers[t])return this;this.handlers[t]=this.handlers[t].filter(x=>x!==f);return this}}fire(t,e={{}}){{for(const f of (this.handlers[t]||[]).slice())f(Object.assign({{target:this}},e));return this}}}}
class FakePopup{{constructor(html,opts,owner){{this.html=html;this.options=Object.assign({{}},opts);this.owner=owner;this.latlng=null;this.root=document.createElement('div');this.root.innerHTML='<a class="leaflet-popup-close-button">×</a><div class="leaflet-popup-content"></div>';this.root.querySelector('.leaflet-popup-content').innerHTML=html}}setContent(h){{this.html=h;this.root.querySelector('.leaflet-popup-content').innerHTML=h;return this}}setLatLng(ll){{this.latlng=ll;return this}}getElement(){{return this.root}}openOn(m){{m._popup=this;m.fire('popupopen',{{popup:this}});this.owner.fire('popupopen',{{popup:this}});return this}}remove(){{if(window.map._popup===this)window.map.closePopup(this)}}}}
class Layer extends Emitter{{constructor(kind,data,opts){{super();this.kind=kind;this.data=data;this.options=opts||{{}};this.children=[];window.__testLayers.push(this)}}addTo(parent){{parent.addLayer(this);return this}}bindPopup(html,opts){{this.popup=new FakePopup(html,opts,this);return this}}getPopup(){{return this.popup||null}}setPopupContent(html){{this.popup&&this.popup.setContent(html);return this}}setLatLng(v){{this.data=v;return this}}setIcon(v){{this.options.icon=v;return this}}setLatLngs(v){{this.data=v;return this}}setStyle(v){{this.options=Object.assign(this.options,v);return this}}getLatLng(){{return this.data}}getCenter(){{return Array.isArray(this.data[0])?this.data[0]:this.data}}getBounds(){{return {{getCenter:()=>this.getCenter()}}}}}}
class Group extends Layer{{constructor(){{super('group',null,{{}})}}addLayer(x){{if(!this.children.includes(x))this.children.push(x);return this}}removeLayer(x){{this.children=this.children.filter(y=>y!==x);return this}}hasLayer(x){{return this.children.includes(x)}}}}
const mapLayers=new Set();const mapEvents=new Emitter();
window.map=Object.assign(mapEvents,{{_zoom:9,_popup:null,hasLayer:l=>mapLayers.has(l),addLayer:l=>{{mapLayers.add(l);return window.map}},removeLayer:l=>{{mapLayers.delete(l);return window.map}},getZoom(){{return this._zoom}},setZoom(z){{this._zoom=z;this.fire('zoomend');return this}},setView(){{window.__setViewCalls=(window.__setViewCalls||0)+1;return this}},fitBounds(){{window.__fitBoundsCalls=(window.__fitBoundsCalls||0)+1;return this}},closePopup(p){{const target=p||this._popup;if(!target)return this;this._popup=null;this.fire('popupclose',{{popup:target}});target.owner&&target.owner.fire('popupclose',{{popup:target}});return this}},invalidateSize(){{}}}});
window.L={{layerGroup:()=>new Group(),marker:(x,o)=>new Layer('marker',x,o),polyline:(x,o)=>new Layer('polyline',x,o),polygon:(x,o)=>new Layer('polygon',x,o),divIcon:o=>o,latLngBounds:()=>({{}}),DomEvent:{{stopPropagation:e=>e&&e.stopPropagation&&e.stopPropagation(),preventDefault:e=>e&&e.preventDefault&&e.preventDefault()}}}};
{core_collapsible}
makeMenuCollapsible();
</script><script id="takMapGatewayDataLoaderV476" src="/assets/runtime/tak-map-gateway-data-v491.js?v=1.3.0-i491"></script>
<script>
(function check(){{const started=Date.now();const timer=setInterval(()=>{{const api=window.TakMapGatewayDataV476,d=api&&api.diagnostics();if(d&&d.connected&&d.revision===7){{
 if(!window.__refreshTriggered){{window.__refreshTriggered=true;api.refresh();return}}if(d.networkDispatches<4||d.fullResponses<2)return;
 const panel=document.getElementById('gatewayDataPanelV476'),gatewayChip=document.getElementById('gatewayDataTotalV476'),gatewayHeaderCount=gatewayChip?.textContent||'',gatewayChipStyle=getComputedStyle(gatewayChip),gatewayChipMatches=gatewayChip.classList.contains('gateway-chip')&&gatewayChipStyle.fontWeight==='900'&&gatewayChipStyle.textTransform==='uppercase'&&parseFloat(gatewayChipStyle.fontSize)<12&&gatewayChipStyle.borderRadius==='999px',body=document.getElementById('gatewayDataBodyV476'),header=document.getElementById('gatewayDataHeaderV476'),master=document.getElementById('gatewayDataMasterV476'),title=header.querySelector('h2'),chevron=document.getElementById('gatewayDataChevronV476');
 const collapsed=()=>panel.classList.contains('is-collapsed')&&body.hidden&&body.style.display==='none';const expanded=()=>!panel.classList.contains('is-collapsed')&&!body.hidden&&body.style.display!=='none';title.click();const c1=collapsed();title.click();const e1=expanded();header.click();const c2=collapsed();header.click();const e2=expanded();chevron.click();const c3=collapsed();chevron.click();const e3=expanded();const before=panel.classList.contains('is-collapsed');master.click();const masterIndependent=panel.classList.contains('is-collapsed')===before;master.click();
 const eq=window.__testLayers.find(x=>x.kind==='marker'&&String(x.options?.icon?.html||'').includes('earthquake'));const nifc=window.__testLayers.find(x=>x.kind==='polygon'&&Number(x.options?.weight)===1.5);const nhcLabels=window.__testLayers.filter(x=>x.kind==='marker'&&String(x.options?.icon?.className||'').includes('gateway-nhc-forecast-label-v491'));const micro=window.__testLayers.filter(x=>x.kind==='marker'&&String(x.options?.icon?.className||'').includes('gateway-micro-label-v491'));const aisMicro=micro.filter(x=>String(x.options?.icon?.html||'').includes('VESSEL'));
 const hoverBefore=api.diagnostics().popupOpens;eq.fire('mouseover',{{latlng:[34.21,-118.31]}});const noHoverPopup=api.diagnostics().popupOpens===hoverBefore;
 const click=[34.25,-118.25];eq.fire('click',{{latlng:click,originalEvent:{{stopPropagation(){{}},preventDefault(){{}}}}}});const opened=api.diagnostics();const popupAtClick=window.map._popup&&window.map._popup.latlng===click;const noRecenter=(window.__setViewCalls||0)===0&&(window.__fitBoundsCalls||0)===0;const labelHidden=opened.activePopupUid==='eq1'&&opened.microLabelsHiddenForPopup===1;const eqHtml=window.map._popup&&window.map._popup.html||'';const canonicalPopup=eqHtml.includes('feature-popup')&&eqHtml.includes('class="kvp gateway-popup-kvp-v491"');const earthquakeClean=!/Event ID|Updated|Felt reports|https?:\/\//i.test(eqHtml);const styleText=document.getElementById('takMapGatewayDataStyleV476').textContent;const themedScrollbar=getComputedStyle(document.documentElement).getPropertyValue('--never-used')===''&&styleText.includes('scrollbar-color:#ff6f2e');const singleScrollOwner=styleText.includes('.gateway-data-popup-v491 .leaflet-popup-content')&&styleText.includes('overflow-y:auto!important')&&styleText.includes('.gateway-data-popup-v491 .gateway-popup-kvp-v491')&&styleText.includes('overflow:visible!important');
 window.map.fire('click',{{latlng:[0,0]}});const closed=api.diagnostics();const labelRestored=closed.activePopupUid===''&&closed.microLabelsVisible===3;
 const fireClick=[34.15,-118.45];nifc.fire('click',{{latlng:fireClick,originalEvent:{{stopPropagation(){{}},preventDefault(){{}}}}}});const nifcPopup=api.diagnostics().activePopupUid==='fire1'&&window.map._popup&&window.map._popup.latlng===fireClick&&nifc.options.bubblingMouseEvents===false;window.map.fire('click',{{latlng:[0,0]}});
 const nhc=window.__testLayers.find(x=>x.kind==='marker'&&String(x.options?.icon?.html||'').includes('viewBox="0 0 26 26"'));nhc.fire('click',{{latlng:[20,-70],originalEvent:{{stopPropagation(){{}},preventDefault(){{}}}}}});const nhcHtml=window.map._popup&&window.map._popup.html||'';const nhcClean=!/Product|Distance from center|Public advisory|https?:\/\//i.test(nhcHtml);window.map.fire('click',{{latlng:[0,0]}});
 window.map._zoom=7;window.map.fire('zoomend');const hiddenAt7=api.diagnostics().microLabelsVisible===0;window.map._zoom=8;window.map.fire('zoomend');const visibleAt8=api.diagnostics().microLabelsVisible===3;
 const pass=gatewayHeaderCount==='4 ITEMS'&&gatewayChipMatches&&d.startupRetries===2&&d.connectedAfterStartupRetry===true&&d.endpointAbsolute&&d.lastHttpStatus===200&&d.card.cardVisible&&c1&&e1&&c2&&e2&&c3&&e3&&masterIndependent&&!!eq&&!!nifc&&d.nhcStormCount===1&&d.nhcForecastLabels===3&&nhcLabels.length===3&&micro.length===3&&aisMicro.length===0&&d.microLabelsNoAis===true&&noHoverPopup&&popupAtClick&&noRecenter&&labelHidden&&labelRestored&&nifcPopup&&canonicalPopup&&earthquakeClean&&nhcClean&&themedScrollbar&&singleScrollOwner&&d.popupSingleScrollOwner===true&&hiddenAt7&&visibleAt8&&d.popupAutoPan===false&&d.popupClickOnly===true&&d.popupCanonicalStyle===true&&d.popupThemedScrollbar===true&&d.pathClickBubblingDisabled===true;
 document.body.dataset.testResult=pass?'pass':'fail';document.getElementById('result').textContent=JSON.stringify({{d,gatewayHeaderCount,gatewayChipMatches,gatewayChipFontWeight:gatewayChipStyle.fontWeight,gatewayChipFontSize:gatewayChipStyle.fontSize,c1,e1,c2,e2,c3,e3,masterIndependent,micro:micro.map(x=>x.options.icon.html),nhcLabels:nhcLabels.map(x=>x.options.icon.html),noHoverPopup,popupAtClick,noRecenter,labelHidden,labelRestored,nifcPopup,canonicalPopup,earthquakeClean,nhcClean,themedScrollbar,singleScrollOwner,hiddenAt7,visibleAt8}});clearInterval(timer)
 }}else if(Date.now()-started>14000){{document.body.dataset.testResult='timeout';document.getElementById('result').textContent=JSON.stringify(d||{{missing:true}});clearInterval(timer)}}}},50)}})();
</script></body></html>"""

    payload = {
        "ok": True, "full": True, "revision": 7, "generated_at": "2026-07-18T03:00:00Z",
        "_tak_map_proxy": {"ssl_context_reused": True},
        "sources": {
            "usgs_earthquakes": {"enabled": True, "count": 1, "logical_count": 1},
            "nws_alerts": {"enabled": True, "count": 0, "logical_count": 0},
            "nifc_fire_perimeters": {"enabled": True, "count": 1, "logical_count": 1},
            "nasa_firms": {"enabled": True, "count": 0, "logical_count": 0},
            "nhc_tropical": {"enabled": True, "count": 4, "logical_count": 1, "count_semantics": "storms"},
            "ais_vessels": {"enabled": True, "count": 1, "logical_count": 1},
        },
        "objects": [
            feature("eq1", "usgs_earthquakes", {"type": "Point", "coordinates": [-118.3, 34.2]}, {"magnitude": "3.9", "depth_km": "7.2", "event_id": "abc", "updated_at": "today"}, "M3.9 Earthquake", remarks="Event ID: abc\nUpdated: today\nFelt reports: 2\nhttps://example.test/event\nUseful earthquake detail"),
            feature("fire1", "nifc_fire_perimeters", {"type": "Polygon", "coordinates": [[[-118.5,34.1],[-118.4,34.1],[-118.4,34.2],[-118.5,34.1]]]}, {"incident_name": "Summit", "incident_type": "Wildfire"}, "Summit", {"stroke": "#FF0000", "stroke_weight": 3}),
            feature("storm-center", "nhc_tropical", {"type": "Point", "coordinates": [-70.0,20.0]}, {"storm_id": "AL012026", "product": "center", "classification": "Hurricane", "storm_name": "Alberto"}, "Hurricane Alberto", remarks="Product: center\nDistance from center: 20 mi\nPublic advisory: active\nhttps://example.test/nhc\nWind threshold detail"),
            feature("storm-crossbar-24", "nhc_tropical", {"type": "LineString", "coordinates": [[-69.4,20.7],[-68.6,21.3]]}, {"storm_id": "AL012026", "product": "forecast-cone-segment", "forecast_hour": "24"}, "24h", {"stroke": "#111111", "stroke_weight": 2}),
            feature("storm-crossbar-48", "nhc_tropical", {"type": "LineString", "coordinates": [[-68.3,21.6],[-67.3,22.4]]}, {"storm_id": "AL012026", "product": "forecast-cone-segment", "forecast_hour": "48"}, "48h", {"stroke": "#111111", "stroke_weight": 2}),
            feature("storm-crossbar-72", "nhc_tropical", {"type": "LineString", "coordinates": [[-66.9,22.4],[-65.5,23.6]]}, {"storm_id": "AL012026", "product": "forecast-cone-segment", "forecast_hour": "72"}, "72h", {"stroke": "#111111", "stroke_weight": 2}),
            feature("ais1", "ais_vessels", {"type": "Point", "coordinates": [-118.2,34.0]}, {"vessel_name": "VESSEL ONE", "mmsi": "123"}, "VESSEL ONE"),
        ], "deleted_uids": [],
    }

    requests: list[str] = []
    from playwright.sync_api import sync_playwright
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
                if len(requests) <= 2:
                    route.fulfill(status=502, content_type="application/json", body=json.dumps({"ok": False, "error": "Gateway Data API proxy failed: <urlopen error connection refused>", "error_class": "URLError", "error_detail": "connection refused"}))
                else:
                    route.fulfill(status=200, content_type="application/json", body=json.dumps(payload, separators=(",", ":")))
            else:
                route.fulfill(status=404, content_type="text/plain", body="not found")
        page.route("**/*", route_request)
        page.set_content(fixture, wait_until="domcontentloaded")
        page.wait_for_function("document.body.dataset.testResult !== 'pending'", timeout=16000)
        result = page.get_attribute("body", "data-test-result")
        diagnostics_text = page.text_content("#result") or ""
        browser.close()

    if result != "pass":
        raise AssertionError(f"result={result}: {diagnostics_text}; page errors={page_errors}")
    if page_errors:
        raise AssertionError(page_errors)
    if len(requests) < 4:
        raise AssertionError(f"too few requests: {requests}")
    first = urllib.parse.urlsplit(requests[0])
    query = urllib.parse.parse_qs(first.query)
    assert query.get("since_revision") == ["0"] and query.get("manual") == ["1"]
    assert requests[0].startswith(ORIGIN + "/api/tak-map/gateway-data/snapshot?")
    print("Gateway Data i491 startup-retry/popup/micro-label browser test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
