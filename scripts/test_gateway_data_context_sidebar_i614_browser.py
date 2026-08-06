#!/usr/bin/env python3
"""Browser contract for i614 Gateway Data contextual-sidebar rendering and subtle selection."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / "assets" / "tak-map-gateway-data-v491.js").read_text()
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
        "count": 3,
        "logical_count": 3,
        "count_semantics": "objects",
        "geometry_types": ["Point", "LineString", "MultiPolygon"],
    }
    common = {
        "source": SOURCE_KEY,
        "event_time": "2026-08-02T16:31:12.423Z",
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
            "source_extension_registry_version": "internal-registry-v1",
            "raw_json_path": "$.features[0]",
        },
    }
    return {
        "ok": True,
        "full": True,
        "revision": 614,
        "generated_at": "2026-08-02T16:31:13Z",
        "source_registry": {"dynamic_source_discovery": True},
        "sources": {
            SOURCE_KEY: source_meta,
            "usgs_earthquakes": {"id": "usgs_earthquakes", "label": "USGS Earthquakes", "enabled": True},
        },
        "objects": [
            {
                "type": "Feature",
                "id": "dynamic-point",
                "geometry": {"type": "Point", "coordinates": [-117.2, 34.1]},
                "properties": dict(common, uid="dynamic-point", title="Control Point"),
                "style": {"stroke": "#00a7d6", "fill": "#00a7d6", "fill_opacity": 0.2},
            },
            {
                "type": "Feature",
                "id": "dynamic-line",
                "geometry": {"type": "LineString", "coordinates": [[-117.5, 34.0], [-117.0, 34.4]]},
                "properties": dict(common, uid="dynamic-line", title="Airspace Boundary"),
                "style": {"stroke": "#111111", "stroke_weight": 3},
            },
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
                "properties": dict(common, uid="dynamic-polygon", title="DESERT MOA"),
                "style": {"stroke": "#111111", "stroke_weight": 3, "fill": "#d5d7d8", "fill_opacity": 0.18},
            },
            {
                "type": "Feature",
                "id": "quake-1",
                "geometry": {"type": "Point", "coordinates": [-118.2, 34.0]},
                "properties": {
                    "uid": "quake-1",
                    "source": "usgs_earthquakes",
                    "title": "M 3.1 earthquake",
                    "stale_at": "2099-01-01T00:00:00Z",
                    "metadata": {"magnitude": 3.1, "depth_km": 7.4},
                },
            },
        ],
        "deleted_uids": [],
    }


FIXTURE = f"""<!doctype html><html><head><meta charset='utf-8'><base href='{ORIGIN}/'><style>
body{{background:#071117;color:#e9f0f5}}#sidebar{{width:390px}}.panel{{display:block}}
#takMapContextSidebarI572{{position:fixed;right:12px;top:90px;width:340px;background:#0b151e}}#takMapContextSidebarI572.collapsed{{display:none}}
</style></head><body>
<aside id='sidebar'><div class='panel' data-collapse-key='adsbSettings'><h2>ADS-B</h2></div><div class='panel' id='satelliteTrackingPanelV409'><h2>Satellite</h2></div></aside>
<div id='map'></div><aside id='takMapContextSidebarI572' class='collapsed'><div id='takMapContextSidebarBodyI572'></div></aside>
<script>
const __storageValues=new Map([[{json.dumps('takmap.gatewayData.ingest.' + SOURCE_KEY)},'1']]);
const localStorage={{getItem:k=>__storageValues.has(String(k))?__storageValues.get(String(k)):null,setItem:(k,v)=>__storageValues.set(String(k),String(v)),removeItem:k=>__storageValues.delete(String(k)),clear:()=>__storageValues.clear(),key:i=>Array.from(__storageValues.keys())[i]||null,get length(){{return __storageValues.size}}}};
window.__layers=[];window.__mapLayers=new Set();window.__bindPopupCalls=0;window.__contextShows=[];
class Emitter{{constructor(){{this.handlers={{}}}}on(t,f){{(this.handlers[t]||(this.handlers[t]=[])).push(f);return this}}off(t,f){{if(!this.handlers[t])return this;this.handlers[t]=f?this.handlers[t].filter(x=>x!==f):[];return this}}fire(t,e={{}}){{for(const f of (this.handlers[t]||[]).slice())f(Object.assign({{target:this,sourceTarget:this}},e));return this}}}}
class Layer extends Emitter{{constructor(kind,data,options){{super();this.kind=kind;this.data=data;this.options=Object.assign({{}},options||{{}});this._icon=document.createElement('div');this._icon.className=(this.options.icon&&this.options.icon.className)||'';window.__layers.push(this)}}addTo(parent){{parent.addLayer(this);return this}}bindPopup(){{window.__bindPopupCalls++;return this}}unbindPopup(){{this.popup=null;return this}}getPopup(){{return this.popup||null}}setLatLng(v){{this.data=v;return this}}setIcon(v){{this.options.icon=v;this._icon.className=v&&v.className||'';return this}}setLatLngs(v){{this.data=v;return this}}setStyle(v){{this.options=Object.assign(this.options,v);this.lastStyle=Object.assign({{}},v);return this}}bringToFront(){{this.broughtToFront=true;return this}}setZIndexOffset(v){{this.zIndexOffset=v;return this}}getElement(){{return this._icon}}getLatLng(){{return Array.isArray(this.data)&&typeof this.data[0]==='number'?{{lat:this.data[0],lng:this.data[1]}}:this.data}}getCenter(){{const c=this.getBounds().getCenter();return c}}getBounds(){{const pts=[];const walk=v=>{{if(Array.isArray(v)&&v.length>=2&&Number.isFinite(Number(v[0]))&&Number.isFinite(Number(v[1])))pts.push(v);else if(Array.isArray(v))v.forEach(walk)}};walk(this.data);let lat=0,lng=0;pts.forEach(p=>{{lat+=Number(p[0]);lng+=Number(p[1])}});return {{getCenter:()=>({{lat:pts.length?lat/pts.length:0,lng:pts.length?lng/pts.length:0}})}}}}}}
class Group extends Layer{{constructor(){{super('group',null,{{}});this.children=[]}}addLayer(x){{if(!this.children.includes(x))this.children.push(x);return this}}removeLayer(x){{this.children=this.children.filter(y=>y!==x);return this}}hasLayer(x){{return this.children.includes(x)}}clearLayers(){{this.children=[];return this}}}}
const events=new Emitter();window.map=Object.assign(events,{{_zoom:8,hasLayer:l=>window.__mapLayers.has(l),addLayer:l=>{{window.__mapLayers.add(l);return window.map}},removeLayer:l=>{{window.__mapLayers.delete(l);return window.map}},getZoom(){{return this._zoom}},getContainer(){{return document.getElementById('map')}},getBounds(){{return {{contains:()=>true}}}},panTo(){{return this}},setView(){{return this}}}});window.takLeafletMap=window.map;
window.L={{layerGroup:()=>new Group(),marker:(x,o)=>new Layer('marker',x,o),polyline:(x,o)=>new Layer('polyline',x,o),polygon:(x,o)=>new Layer('polygon',x,o),divIcon:o=>o,DomEvent:{{stopPropagation(){{}},preventDefault(){{}}}}}};
window.TakMapContextSidebarI572={{
  version:'i572',
  showObject(object,source,layer,center){{const panel=document.getElementById('takMapContextSidebarI572'),body=document.getElementById('takMapContextSidebarBodyI572');panel.classList.remove('collapsed');body.innerHTML=layer.__takMapI570InfoHtml||'';window.__contextShows.push({{object,source,center}})}},
  hide(){{document.getElementById('takMapContextSidebarI572').classList.add('collapsed');document.getElementById('takMapContextSidebarBodyI572').innerHTML=''}},
  diagnostics(){{return {{selectedKey:window.__contextShows.length?'gateway-data:'+window.__contextShows.at(-1).object.id:''}}}}
}};
</script><script src='/assets/runtime/tak-map-gateway-data-v491.js'></script></body></html>"""


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
            if path == "/assets/runtime/tak-map-gateway-data-v491.js":
                route.fulfill(status=200, content_type="application/javascript; charset=utf-8", body=JS)
            elif path == "/api/tak-map/gateway-data/snapshot":
                route.fulfill(status=200, content_type="application/json", body=json.dumps(payload()))
            else:
                route.fulfill(status=204, body="")

        page.route("**/*", route_request)
        page.set_content(FIXTURE, wait_until="domcontentloaded", timeout=20_000)
        page.wait_for_function("window.TakMapGatewayDataV476 && window.TakMapGatewayDataV476.diagnostics().revision === 614", timeout=20_000)
        page.wait_for_function("window.TakMapGatewayDataV476.diagnostics().objects === 4", timeout=10_000)

        result = page.evaluate("""async () => {
          const find=uid=>window.__layers.find(x=>x._takGatewayUid===uid);
          const polygon=find('dynamic-polygon'), line=find('dynamic-line'), point=find('dynamic-point'), quake=find('quake-1');
          const baseWeight=polygon.options.weight,baseFill=polygon.options.fillOpacity;
          polygon.fire('click',{originalEvent:{stopPropagation(){},preventDefault(){}}});
          await new Promise(r=>setTimeout(r,30));
          const body=document.getElementById('takMapContextSidebarBodyI572').textContent;
          const html=document.getElementById('takMapContextSidebarBodyI572').innerHTML;
          const selectedWeight=polygon.options.weight,selectedFill=polygon.options.fillOpacity;
          const d1=window.TakMapGatewayDataV476.diagnostics();
          line.fire('click',{originalEvent:{stopPropagation(){},preventDefault(){}}});
          await new Promise(r=>setTimeout(r,20));
          const polygonRestored=polygon.options.weight===baseWeight && polygon.options.fillOpacity===baseFill;
          point.fire('click',{originalEvent:{stopPropagation(){},preventDefault(){}}});
          await new Promise(r=>setTimeout(r,20));
          const pointSelected=point.getElement().classList.contains('gateway-data-selected-i614') && point.zIndexOffset===690;
          quake.fire('click',{originalEvent:{stopPropagation(){},preventDefault(){}}});
          await new Promise(r=>setTimeout(r,20));
          const builtInText=document.getElementById('takMapContextSidebarBodyI572').textContent;
          polygon.fire('click',{originalEvent:{stopPropagation(){},preventDefault(){}}});
          await new Promise(r=>setTimeout(r,20));
          const dynamicRow=document.querySelector('[data-source="source_extension:restricted-airspace"] input');
          dynamicRow.checked=false;dynamicRow.dispatchEvent(new Event('change',{bubbles:true}));
          await new Promise(r=>setTimeout(r,30));
          const d2=window.TakMapGatewayDataV476.diagnostics();
          return {
            bindPopupCalls:window.__bindPopupCalls,
            contextShows:window.__contextShows.length,
            panelOpen:!document.getElementById('takMapContextSidebarI572').classList.contains('collapsed'),
            body,html,builtInText,baseWeight,selectedWeight,baseFill,selectedFill,polygonRestored,pointSelected,
            version:d1.version,contextPanelUsed:d1.contextPanelUsed,floating:d1.floatingLeafletPopups,curated:d1.dynamicContextCurated,
            selections:d2.contextSelections,activeAfterDisable:d2.activeContextUid,objectsAfterDisable:d2.objects,
            panelClosedAfterDisable:document.getElementById('takMapContextSidebarI572').classList.contains('collapsed')
          };
        }""")
        browser.close()

    assert result["version"] == "i614", result
    assert result["bindPopupCalls"] == 0, result
    assert result["contextPanelUsed"] and not result["floating"] and result["curated"], result
    assert result["contextShows"] >= 4 and result["selections"] >= 4, result
    for text in ("DESERT MOA", "Restricted Airspace", "Updated", "Geometry", "MultiPolygon", "Type", "MOA", "Agency", "FAA", "Lower limit", "Upper limit", "Schedule", "Training airspace"):
        assert text in result["body"], (text, result)
    for hidden in ("99123", "internal-guid", "internal-registry-v1", "raw_json_path", "objectid", "globalid"):
        assert hidden not in result["body"] and hidden not in result["html"], (hidden, result)
    assert "Magnitude" in result["builtInText"] and "3.1" in result["builtInText"], result
    assert result["selectedWeight"] > result["baseWeight"] and result["selectedWeight"] - result["baseWeight"] <= 1, result
    assert result["selectedFill"] > result["baseFill"] and result["selectedFill"] - result["baseFill"] < 0.05, result
    assert result["polygonRestored"] and result["pointSelected"], result
    assert result["objectsAfterDisable"] == 1, result
    assert result["activeAfterDisable"] == "" and result["panelClosedAfterDisable"], result
    assert not page_errors, page_errors
    assert not console_errors, console_errors
    print("TAK Map i614 Gateway Data contextual-sidebar browser test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
