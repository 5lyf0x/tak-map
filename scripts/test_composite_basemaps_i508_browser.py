#!/usr/bin/env python3
"""Real-browser regression test for i508 split composite Leaflet layers."""
from __future__ import annotations

import re
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "tak_dashboard.py").read_text(errors="replace")
MATCH = re.search(
    r"_I508_SPLIT_LAYER_UI\s*=\s*r'''(<script id=\"takMapSplitCompositeBasemapsV508\">.*?</script>)'''",
    SOURCE,
    flags=re.S,
)
assert MATCH, "i508 split-layer script was not found"
PATCH = MATCH.group(1)

STUB = r"""
<script>
window.__tileCalls=[];
window.__groups=[];
window.L={
  tileLayer:function(url,options){
    const layer={_url:url,options:options||{},events:{},on:function(name,fn){this.events[name]=fn;return this;},bringToBack:function(){this.back=true;return this;},bringToFront:function(){this.front=true;return this;}};
    window.__tileCalls.push(layer); return layer;
  },
  layerGroup:function(layers){
    const group={layers:layers,events:{},on:function(name,fn){this.events[name]=fn;return this;}};
    window.__groups.push(group); return group;
  }
};
window.takMapCreateOnlineLayerV476=function(b){return {legacy:true,url:b.url};};
window.takMapCreateOnlineLayerV465=window.takMapCreateOnlineLayerV476;
</script>
"""


def main() -> int:
    html = "<!doctype html><html><head>" + STUB + "</head><body>" + PATCH + "</body></html>"
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path="/usr/bin/chromium", args=["--no-sandbox"])
        page = browser.new_page()
        page.set_content(html, wait_until="domcontentloaded")
        result = page.evaluate(
            """
            () => {
              const composite={
                id:'tg-imagery-radar', clientComposition:true,
                baseUrl:'https://base.example/{z}/{y}/{x}.jpg',
                overlayUrl:'https://gateway.example:9443/tiles/overlay-noaa/{z}/{x}/{y}.png',
                overlayOpacity:0.9, overlayTileSize:256, overlayMaxNativeZoom:22,
                overlaySource:'noaa', serverCompositeUrl:'https://gateway.example:9443/tiles/esri-imagery-radar/{z}/{x}/{y}.png', minZoom:2, maxZoom:22, attribution:'Base provider'
              };
              const group=window.takMapCreateOnlineLayerV476(composite);
              const normal=window.takMapCreateOnlineLayerV476({id:'normal',url:'https://normal.example/{z}/{x}/{y}.png'});
              if(group.events.add) group.events.add();
              const failedTile={dataset:{},src:''};
              if(group.layers[1].events.tileerror) group.layers[1].events.tileerror({tile:failedTile,coords:{z:8,x:40,y:91}});
              return {
                groupCount:window.__groups.length,
                layerCount:group.layers && group.layers.length,
                baseUrl:group.layers && group.layers[0]._url,
                overlayUrl:group.layers && group.layers[1]._url,
                baseAttribution:group.layers && group.layers[0].options.attribution,
                overlayOpacity:group.layers && group.layers[1].options.opacity,
                overlayNativeZoom:group.layers && group.layers[1].options.maxNativeZoom,
                overlayCors:group.layers && group.layers[1].options.crossOrigin,
                baseBack:group.layers && group.layers[0].back,
                overlayFront:group.layers && group.layers[1].front,
                mode:group._takMapCompositeV508 && group._takMapCompositeV508.mode,
                serverFallback:group._takMapCompositeV508 && group._takMapCompositeV508.serverCompositeFallback,
                failedTileSrc:failedTile.src,
                normalLegacy:normal && normal.legacy,
                iteration:document.documentElement.dataset.takMapIteration,
                diagnostics:window.TakMapCompositePerformanceV508.diagnostics()
              };
            }
            """
        )
        browser.close()

    assert result["groupCount"] == 1, result
    assert result["layerCount"] == 2, result
    assert result["baseUrl"].startswith("https://base.example/"), result
    assert "/tiles/overlay-noaa/" in result["overlayUrl"], result
    assert result["baseAttribution"] == "Base provider", result
    assert abs(result["overlayOpacity"] - 0.9) < 0.001, result
    assert result["overlayNativeZoom"] == 22, result
    assert result["overlayCors"] is True, result
    assert result["baseBack"] is True and result["overlayFront"] is True, result
    assert result["mode"] == "direct-base-plus-gateway-overlay", result
    assert result["serverFallback"] is True, result
    assert result["failedTileSrc"].endswith("/tiles/esri-imagery-radar/8/40/91.png"), result
    assert result["normalLegacy"] is True, result
    assert result["iteration"] == "i508", result
    assert result["diagnostics"]["clientComposition"] is True, result
    assert result["diagnostics"]["takMapPythonProxy"] is False, result
    print("TAK Map i508 Chromium split-layer composite basemap test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
