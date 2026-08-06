#!/usr/bin/env python3
"""Browser contract for i615 dedicated read-only Gateway Data context mode."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
GATEWAY_JS = (ROOT / "assets" / "tak-map-gateway-data-v491.js").read_text()
CONTEXT_JS = (ROOT / "assets" / "tak-map-context-sidebar-i572.js").read_text()
ORIGIN = "https://takmap.test"
SOURCE_KEY = "source_extension:restricted-airspace"


def payload() -> dict:
    source_meta = {
        "id": SOURCE_KEY,
        "source_key": SOURCE_KEY,
        "source_kind": "source_extension",
        "source_extension": True,
        "dynamic": True,
        "extension_id": "restricted-airspace",
        "label": "Restricted Airspace",
        "enabled": True,
        "state": "healthy",
        "count": 1,
        "logical_count": 1,
        "count_semantics": "objects",
        "geometry_types": ["MultiPolygon"],
    }
    return {
        "ok": True,
        "full": True,
        "revision": 615,
        "generated_at": "2026-08-06T00:31:13Z",
        "source_registry": {"dynamic_source_discovery": True},
        "sources": {SOURCE_KEY: source_meta},
        "objects": [
            {
                "type": "Feature",
                "id": "dynamic-polygon",
                "geometry": {
                    "type": "MultiPolygon",
                    "coordinates": [
                        [[[-117.8, 33.8], [-117.2, 33.8], [-117.2, 34.2], [-117.8, 34.2], [-117.8, 33.8]]],
                        [[[-116.9, 34.0], [-116.6, 34.0], [-116.6, 34.3], [-116.9, 34.3], [-116.9, 34.0]]],
                    ],
                },
                "properties": {
                    "uid": "dynamic-polygon",
                    "source": SOURCE_KEY,
                    "title": "DESERT MOA",
                    "event_time": "2026-08-06T00:31:12.423Z",
                    "stale_at": "2099-01-01T00:00:00Z",
                    "remarks": "Training airspace",
                    "metadata": {
                        "status": "Active",
                        "type_code": "MOA",
                        "controllingagency": "FAA",
                        "lower_desc": "5,000 FT MSL",
                        "upper_desc": "FL180",
                        "timesofuse": "Intermittent by NOTAM",
                        "objectid": "99123",
                        "globalid": "{internal-guid}",
                    },
                },
                "style": {"stroke": "#111111", "stroke_weight": 3, "fill": "#d5d7d8", "fill_opacity": 0.18},
            }
        ],
        "deleted_uids": [],
    }


FIXTURE = f"""<!doctype html><html><head><meta charset='utf-8'><base href='{ORIGIN}/'><style>
html,body{{margin:0;width:100%;height:100%;background:#071117;color:#e9f0f5}}#map{{position:relative;width:100%;height:100%}}.panel{{display:block}}
</style></head><body><aside id='sidebar'><div class='panel' data-collapse-key='adsbSettings'><h2>ADS-B</h2></div><div class='panel' id='satelliteTrackingPanelV409'><h2>Satellite</h2></div></aside><div id='map'></div>
<script>
const __storageValues=new Map([[{json.dumps('takmap.gatewayData.ingest.' + SOURCE_KEY)},'1']]);
const localStorage={{getItem:k=>__storageValues.has(String(k))?__storageValues.get(String(k)):null,setItem:(k,v)=>__storageValues.set(String(k),String(v)),removeItem:k=>__storageValues.delete(String(k)),clear:()=>__storageValues.clear(),key:i=>Array.from(__storageValues.keys())[i]||null,get length(){{return __storageValues.size}}}};
window.ResizeObserver=class{{constructor(cb){{this.cb=cb}}observe(){{}}disconnect(){{}}}};
window.__layers=[];window.__mapLayers=new Set();window.__bindPopupCalls=0;
window.lastDataSync={{objects:[]}};window.importedFeatures=()=>[];
class Emitter{{constructor(){{this.handlers={{}}}}on(t,f){{String(t).split(/\s+/).forEach(k=>(this.handlers[k]||(this.handlers[k]=[])).push(f));return this}}off(t,f){{String(t).split(/\s+/).forEach(k=>{{if(!this.handlers[k])return;this.handlers[k]=f?this.handlers[k].filter(x=>x!==f):[]}});return this}}fire(t,e={{}}){{for(const f of (this.handlers[t]||[]).slice())f(Object.assign({{target:this,sourceTarget:this}},e));return this}}}}
class Layer extends Emitter{{constructor(kind,data,options){{super();this.kind=kind;this.data=data;this.options=Object.assign({{}},options||{{}});this._icon=document.createElement('div');this._icon.className=(this.options.icon&&this.options.icon.className)||'';window.__layers.push(this)}}addTo(parent){{parent.addLayer(this);return this}}bindPopup(){{window.__bindPopupCalls++;return this}}unbindPopup(){{this.popup=null;return this}}getPopup(){{return this.popup||null}}setLatLng(v){{this.data=v;return this}}setIcon(v){{this.options.icon=v;this._icon.className=v&&v.className||'';return this}}setLatLngs(v){{this.data=v;return this}}setStyle(v){{this.options=Object.assign(this.options,v);this.lastStyle=Object.assign({{}},v);return this}}bringToFront(){{this.broughtToFront=true;return this}}setZIndexOffset(v){{this.zIndexOffset=v;return this}}getElement(){{return this._icon}}getLatLng(){{return Array.isArray(this.data)&&typeof this.data[0]==='number'?{{lat:this.data[0],lng:this.data[1]}}:this.data}}getBounds(){{const pts=[];const walk=v=>{{if(Array.isArray(v)&&v.length>=2&&Number.isFinite(Number(v[0]))&&Number.isFinite(Number(v[1])))pts.push(v);else if(Array.isArray(v))v.forEach(walk)}};walk(this.data);let lat=0,lng=0;pts.forEach(p=>{{lat+=Number(p[0]);lng+=Number(p[1])}});return {{getCenter:()=>({{lat:pts.length?lat/pts.length:0,lng:pts.length?lng/pts.length:0}}),contains:()=>true}}}}}}
class Group extends Layer{{constructor(){{super('group',null,{{}});this.children=[]}}addLayer(x){{if(!this.children.includes(x))this.children.push(x);return this}}removeLayer(x){{this.children=this.children.filter(y=>y!==x);return this}}hasLayer(x){{return this.children.includes(x)}}clearLayers(){{this.children=[];return this}}}}
const events=new Emitter();window.map=Object.assign(events,{{_zoom:8,hasLayer:l=>window.__mapLayers.has(l),addLayer:l=>{{window.__mapLayers.add(l);return window.map}},removeLayer:l=>{{window.__mapLayers.delete(l);return window.map}},getZoom(){{return this._zoom}},getContainer(){{return document.getElementById('map')}},getBounds(){{return {{contains:()=>true}}}},panTo(){{return this}},setView(){{return this}}}});window.takLeafletMap=window.map;
window.L={{layerGroup:()=>new Group(),marker:(x,o)=>new Layer('marker',x,o),polyline:(x,o)=>new Layer('polyline',x,o),polygon:(x,o)=>new Layer('polygon',x,o),divIcon:o=>o,DomEvent:{{stopPropagation(){{}},preventDefault(){{}},disableClickPropagation(){{}},disableScrollPropagation(){{}}}}}};
</script>
<script src='/assets/runtime/tak-map-context-sidebar-i572.js?v=1.3.0-i615'></script>
<script src='/assets/runtime/tak-map-gateway-data-v491.js?v=1.3.0-i615'></script>
</body></html>"""


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
                route.fulfill(status=200, content_type="application/javascript; charset=utf-8", body=CONTEXT_JS)
            elif path == "/assets/runtime/tak-map-gateway-data-v491.js":
                route.fulfill(status=200, content_type="application/javascript; charset=utf-8", body=GATEWAY_JS)
            elif path == "/api/tak-map/gateway-data/snapshot":
                route.fulfill(status=200, content_type="application/json", body=json.dumps(payload()))
            else:
                route.fulfill(status=204, body="")

        page.route("**/*", route_request)
        page.set_content(FIXTURE, wait_until="domcontentloaded", timeout=20_000)
        page.wait_for_function("window.TakMapGatewayDataV476 && window.TakMapGatewayDataV476.diagnostics().revision === 615", timeout=20_000)
        page.wait_for_function("window.TakMapContextSidebarI572 && window.TakMapContextSidebarI572.diagnostics().gatewayDataReadOnly === true", timeout=10_000)

        result = page.evaluate("""async () => {
          const layer=window.__layers.find(x=>x._takGatewayUid==='dynamic-polygon');
          const baseWeight=layer.options.weight, baseFill=layer.options.fillOpacity;
          layer.fire('click',{originalEvent:{stopPropagation(){},preventDefault(){}}});
          await new Promise(r=>setTimeout(r,60));
          const panel=document.getElementById('takMapContextSidebarI572');
          const body=document.getElementById('takMapContextSidebarBodyI572');
          const first=body.firstElementChild;
          const initialHtml=body.innerHTML;
          const initialText=body.textContent;
          const kicker=document.getElementById('takMapContextKickerI572').textContent;
          const title=document.getElementById('takMapContextTitleI572').textContent;
          const initialPanelMode=panel.dataset.contextMode||'';
          const initialPanelClass=panel.className;
          const initialContextDiagnostics=window.TakMapContextSidebarI572.diagnostics();
          const selectedWeight=layer.options.weight, selectedFill=layer.options.fillOpacity;
          const controls=body.querySelectorAll('details.popup-edit,.popup-edit,.tak-context-delete-row-i572,.tak-context-delete-unavailable-i572,[data-i556-point-edit],[data-i572-point-edit],[data-tak-i572-delete-current],input[type=color]').length;
          const animated=Array.from(body.querySelectorAll('*')).filter(el=>getComputedStyle(el).animationName!=='none').length;
          let mutations=0;const observer=new MutationObserver(rows=>{mutations+=rows.filter(x=>x.type==='childList').length});observer.observe(body,{childList:true,subtree:true});
          const before=window.TakMapGatewayDataV476.diagnostics();
          window.TakMapGatewayDataV476.refresh();
          await new Promise(r=>setTimeout(r,220));
          observer.disconnect();
          const after=window.TakMapGatewayDataV476.diagnostics();
          const sameNode=first===body.firstElementChild;
          const sameHtml=initialHtml===body.innerHTML;
          document.getElementById('takMapContextHideI572').click();
          await new Promise(r=>setTimeout(r,280));
          return {
            gatewayVersion:before.version,
            contextVersion:window.TakMapContextSidebarI572.version,
            contextDiagnostics:initialContextDiagnostics,
            gatewayDiagnostics:after,
            panelMode:initialPanelMode,
            panelClass:initialPanelClass,
            initialText,kicker,title,controls,animated,mutations,sameNode,sameHtml,
            selectedWeight,selectedFill,
            baseWeight,baseFill,
            panelClosed:panel.classList.contains('collapsed'),
            highlightCleared:layer.options.weight===baseWeight && layer.options.fillOpacity===baseFill,
            bindPopupCalls:window.__bindPopupCalls
          };
        }""")
        browser.close()

    assert result["gatewayVersion"] == "i615", result
    assert result["contextDiagnostics"]["gatewayDataReadOnly"] is True, result
    assert result["panelMode"] == "gateway-data-readonly", result
    assert "gateway-data-readonly-i615" in result["panelClass"], result
    assert result["kicker"] == "Gateway Data · Restricted Airspace", result
    assert result["title"] == "DESERT MOA", result
    for required in ("DESERT MOA", "Restricted Airspace", "Updated", "Geometry", "MultiPolygon", "Type", "MOA", "Agency", "FAA", "Training airspace"):
        assert required in result["initialText"], (required, result)
    for forbidden in ("Local Data", "Delete Shape", "Delete unavailable", "source-owned identity", "Edit"):
        assert forbidden not in result["initialText"], (forbidden, result)
    assert result["controls"] == 0, result
    assert result["animated"] == 0, result
    assert result["mutations"] == 0 and result["sameNode"] and result["sameHtml"], result
    assert result["gatewayDiagnostics"]["gatewayDataReadOnly"] is True, result
    assert result["gatewayDiagnostics"]["contextEditControls"] is False, result
    assert result["gatewayDiagnostics"]["contextDeleteControls"] is False, result
    assert result["gatewayDiagnostics"]["contextAnimatedAccents"] is False, result
    assert result["gatewayDiagnostics"]["contextFieldUpdates"] == 0, result
    assert result["gatewayDiagnostics"]["contextBodyRebuilds"] == 1, result
    assert result["bindPopupCalls"] == 0, result
    assert result["panelClosed"] and result["highlightCleared"], result
    assert not page_errors, page_errors
    assert not console_errors, console_errors
    print("TAK Map i615 dedicated read-only Gateway Data context browser test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
