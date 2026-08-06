#!/usr/bin/env python3
"""Regression: first click must pin object popups across representative Leaflet layers."""
from __future__ import annotations

import json
import sys
import os
import re
import runpy
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUB = (ROOT / "scripts" / "leaflet_stub_test.js").read_text()


def self_contained_html() -> str:
    ns = runpy.run_path(str(ROOT / "tak_dashboard.py"), run_name="tak_map_i493_first_click_browser")
    html = ns["TAK_MAP_HTML"]
    html = re.sub(
        r'<script src="https://unpkg\.com/leaflet@1\.9\.4/dist/leaflet\.js"></script>',
        "<script>" + STUB + "</script>",
        html,
        count=1,
    )
    html = re.sub(r'<link[^>]+unpkg\.com/leaflet@1\.9\.4/dist/leaflet\.css[^>]*>', "", html, count=1)
    pattern = re.compile(r'<script id="([^"]+)" src="/assets/runtime/([^"?]+)[^"]*"></script>')

    def inline_asset(match: re.Match[str]) -> str:
        asset = ROOT / "assets" / match.group(2)
        assert asset.exists(), asset
        return f'<script id="{match.group(1)}">\n{asset.read_text()}\n</script>'

    return pattern.sub(inline_asset, html)


def main() -> int:
    chromium = next(
        (name for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable") if shutil.which(name)),
        None,
    )
    if not chromium:
        print("SKIP: Chromium unavailable")
        return 0

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            executable_path=shutil.which(chromium),
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
        )
        page = browser.new_page()
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.set_content(self_contained_html(), wait_until="domcontentloaded", timeout=20_000)
        page.wait_for_function(
            "window.TakMapPopupLifecycleV463 && typeof TakMapPopupLifecycleV463.registerPopupLayer === 'function'",
            timeout=12_000,
        )

        result = page.evaluate(
            """async()=>{
              const m=L.map(document.createElement('div'));window.takLeafletMap=m;window.map=m;m.on('click',ev=>clearPinnedPopup(ev));
              function makePopupLayer(kind,index){
                const ll=[34+index*.001,-118-index*.001];
                let layer;
                if(kind==='marker')layer=L.marker(ll,{interactive:true});
                else if(kind==='circleMarker')layer=L.circleMarker(ll,{interactive:true});
                else if(kind==='polyline')layer=L.polyline([ll,[ll[0]+.002,ll[1]+.002]],{interactive:true});
                else if(kind==='polygon')layer=L.polygon([[ll,[ll[0]+.002,ll[1]],[ll[0]+.001,ll[1]+.002]]],{interactive:true});
                else layer=L.circle(ll,{interactive:true});
                layer.addTo(m);
                layer.bindPopup('<div class="feature-popup"><b>'+kind+'</b></div>');
                const popup=layer.getPopup();
                popup.options=popup.options||{};
                popup._source=layer;
                popup._open=false;
                popup._el=document.createElement('div');
                popup._el.className='leaflet-popup';
                popup.getElement=()=>popup._el;
                popup.isOpen=()=>popup._open;
                const originalFire=layer.fire.bind(layer);
                layer.openPopup=function(at){
                  popup._open=true;popup._source=layer;m._popup=popup;
                  originalFire('popupopen',{popup,latlng:at||L.latLng(ll)});
                  m.fire('popupopen',{popup});
                  return layer;
                };
                layer.closePopup=function(){
                  if(!popup._open)return layer;
                  popup._open=false;
                  originalFire('popupclose',{popup});
                  m.fire('popupclose',{popup});
                  if(m._popup===popup)m._popup=null;
                  return layer;
                };
                layer.isPopupOpen=()=>popup._open;
                // Representative object renderer behavior: click opens the popup.
                layer.on('click',ev=>layer.openPopup(ev&&ev.latlng));
                TakMapPopupLifecycleV463.registerPopupLayer(layer);
                return layer;
              }

              const kinds=['marker','circleMarker','polyline','polygon','circle'];
              const layers=kinds.map(makePopupLayer);
              const first=[];
              for(let i=0;i<layers.length;i++){
                const layer=layers[i],oe={};
                layer.fire('click',{latlng:L.latLng(34+i*.001,-118-i*.001),originalEvent:oe});
                // Simulate Leaflet propagation if the DOM event was not stopped.
                if(!oe._stopped)m.fire('click',{originalEvent:oe,sourceTarget:layer,propagatedFrom:layer});
                await new Promise(r=>setTimeout(r,25));
                first.push({
                  kind:kinds[i],
                  stopped:!!oe._stopped,
                  open:layer.isPopupOpen(),
                  pinned:window._takPinnedPopupLayer===layer,
                  objectMarker:!!oe.__takMapObjectPopupClick
                });
              }

              // Popup interactions must not bubble to the map popup-clear path.
              const current=layers[layers.length-1],root=current.getPopup().getElement();
              let bubbled=false;
              m.on('click',()=>{bubbled=true});
              root.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
              await new Promise(r=>setTimeout(r,10));
              const popupClickKeptOpen=current.isPopupOpen();
              const popupDomBubbled=bubbled;

              // A later genuine blank-map click still closes the pinned popup.
              await new Promise(r=>setTimeout(r,260));
              const guardRemaining=Number(window.__takMapObjectPopupClickUntil||0)-Date.now();
              const directCloseResult=clearPinnedPopup({originalEvent:{},sourceTarget:window.map});
              await new Promise(r=>setTimeout(r,10));
              const blankClosed=!current.isPopupOpen() && window._takPinnedPopupLayer===null;

              return {
                first,
                popupClickKeptOpen,
                popupDomBubbled,
                blankClosed,guardRemaining,directCloseResult,
                diagnostics:TakMapPopupLifecycleV463.diagnostics()
              };
            }"""
        )
        browser.close()

    assert all(item["stopped"] for item in result["first"]), result
    assert all(item["open"] for item in result["first"]), result
    assert all(item["pinned"] for item in result["first"]), result
    assert all(item["objectMarker"] for item in result["first"]), result
    assert result["popupClickKeptOpen"], result
    assert result["popupDomBubbled"] is False, result
    assert result["blankClosed"], result
    assert result["diagnostics"]["firstClickPinning"] is True, result
    assert result["diagnostics"]["firstClickGuards"] >= len(result["first"]), result
    fatal = [e for e in errors if any(t in e.lower() for t in ("maximum call stack", "out of memory", "too much recursion"))]
    assert not fatal, fatal
    print("TAK Map i493 first-click popup pinning browser test passed")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    code=main()
    try: sys.stdout.flush(); sys.stderr.flush()
    except Exception: pass
    os._exit(int(code or 0))
