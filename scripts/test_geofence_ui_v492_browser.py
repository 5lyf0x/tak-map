#!/usr/bin/env python3
"""Regression coverage for i493 Geofence card placement and floating-window refinements."""
from __future__ import annotations

import os
import sys
import re
import runpy
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUB = (ROOT / "scripts" / "leaflet_stub_test.js").read_text()


def self_contained_html() -> str:
    with tempfile.TemporaryDirectory(prefix="tak-gf-ui-v493-") as td:
        previous = os.environ.get("TAK_DASHBOARD_DATA_DIR")
        os.environ["TAK_DASHBOARD_DATA_DIR"] = td
        try:
            namespace = runpy.run_path(str(ROOT / "tak_dashboard.py"), run_name="tak_map_geofence_ui_v493")
        finally:
            if previous is None:
                os.environ.pop("TAK_DASHBOARD_DATA_DIR", None)
            else:
                os.environ["TAK_DASHBOARD_DATA_DIR"] = previous
    html = namespace["TAK_MAP_HTML"]
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


def panel_order(page) -> list[str]:
    return page.evaluate(
        """()=>Array.from(document.querySelectorAll('#sidebar > .panel')).map(p=>(p.querySelector('h2')?.textContent||'').replace(/\\s+/g,' ').trim())"""
    )


def assert_adjacent_order(order: list[str]) -> None:
    base = next(i for i, name in enumerate(order) if name.lower().startswith("basemap"))
    geofence = next(i for i, name in enumerate(order) if name.lower().startswith("geofences"))
    adsb = next(i for i, name in enumerate(order) if name.lower().startswith("ads-b"))
    assert (base + 1, geofence + 1) == (geofence, adsb), order


def main() -> int:
    chromium = next(
        (name for name in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable") if shutil.which(name)),
        None,
    )
    if not chromium:
        print("SKIP: Chromium unavailable")
        return 0

    from playwright.sync_api import sync_playwright

    errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
            executable_path=shutil.which(chromium),
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
        )
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.set_default_timeout(8_000)
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.set_content(self_contained_html(), wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_function(
            "window.TakMapGeofencingV491 && document.getElementById('geofencePanelV491')",
            timeout=20_000,
        )
        page.wait_for_timeout(1_000)

        # With zero fences, the floating alert window must not exist.
        assert page.locator("#takGeofenceEventsV491").count() == 0
        assert "Compact event list" not in page.locator("body").inner_text()
        assert_adjacent_order(panel_order(page))

        page.evaluate(
            """()=>{
              window.__gfUiStore=[];
              window.fetch=async(url,init={})=>{
                const u=String(url||'');
                if(!u.includes('/api/tak-map/geofences'))return new Response('{}',{status:404});
                if(String(init.method||'GET').toUpperCase()==='POST'){
                  const body=JSON.parse(init.body||'{}');
                  if(body.action==='upsert'){
                    const i=window.__gfUiStore.findIndex(x=>x.id===body.fence.id);
                    if(i>=0)window.__gfUiStore[i]=body.fence;else window.__gfUiStore.push(body.fence);
                    return new Response(JSON.stringify({ok:true,fence:body.fence,fences:window.__gfUiStore}),{status:200,headers:{'Content-Type':'application/json'}});
                  }
                  if(body.action==='remove'){
                    window.__gfUiStore=window.__gfUiStore.filter(x=>x.id!==body.id);
                    return new Response(JSON.stringify({ok:true,removed:true,fences:window.__gfUiStore}),{status:200,headers:{'Content-Type':'application/json'}});
                  }
                }
                return new Response(JSON.stringify({ok:true,fences:window.__gfUiStore}),{status:200,headers:{'Content-Type':'application/json'}});
              };
            }"""
        )
        page.evaluate(
            """()=>TakMapGeofencingV491.save({
              id:'gf-ui-v493',name:'UI Test Fence',target_id:'local:local-ui-v492',target_source:'local',target_name:'UI Test Shape',
              kind:'shape',geometry:{type:'polygon',coordinates:[[-118,34],[-117.99,34],[-117.99,34.01],[-118,34.01],[-118,34]]},
              monitored:['adsb','eud'],triggers:{enter:true,exit:true,dwell:false,cross:false},dwell_minutes:5,
              altitude:{mode:'none',min_ft:null,max_ft:null},enabled:true
            })"""
        )
        page.wait_for_selector("#takGeofenceEventsV491")

        window = page.locator("#takGeofenceEventsV491")
        assert window.locator('[data-gf-resize="top"]').count() == 1
        assert window.locator('[data-gf-resize="bottom"]').count() == 1
        assert "Compact event list" not in window.inner_text()
        diag = page.evaluate("TakMapGeofencingV491.diagnostics()")
        assert diag["eventWindowConditional"] is True
        assert diag["eventWindowSubtitle"] is False
        assert diag["heightResizeOnly"] is True
        assert diag["topBottomResizeGrips"] is True
        assert diag["sidebarPlacement"] == "Basemap > Geofences > ADS-B"

        before = window.bounding_box()
        assert before
        top_grip = window.locator('[data-gf-resize="top"]')
        top_box = top_grip.bounding_box()
        assert top_box
        page.mouse.move(top_box["x"] + top_box["width"] / 2, top_box["y"] + 3)
        page.mouse.down()
        page.mouse.move(top_box["x"] + top_box["width"] / 2, top_box["y"] - 70, steps=8)
        page.mouse.up()
        after_top = window.bounding_box()
        assert after_top
        assert abs(after_top["width"] - before["width"]) < 1.5, (before, after_top)
        assert after_top["height"] > before["height"] + 45, (before, after_top)
        assert abs((after_top["y"] + after_top["height"]) - (before["y"] + before["height"])) < 2.5, (before, after_top)

        bottom_grip = window.locator('[data-gf-resize="bottom"]')
        bottom_box = bottom_grip.bounding_box()
        assert bottom_box
        page.mouse.move(bottom_box["x"] + bottom_box["width"] / 2, bottom_box["y"] + 3)
        page.mouse.down()
        page.mouse.move(bottom_box["x"] + bottom_box["width"] / 2, bottom_box["y"] - 40, steps=6)
        page.mouse.up()
        after_bottom = window.bounding_box()
        assert after_bottom
        assert abs(after_bottom["width"] - after_top["width"]) < 1.5, (after_top, after_bottom)
        assert after_bottom["height"] < after_top["height"] - 20, (after_top, after_bottom)
        assert abs(after_bottom["y"] - after_top["y"]) < 2.5, (after_top, after_bottom)
        # Minimize hides both grips; restore returns to the resized height.
        page.locator("#takGfEventMinV491").click()
        assert page.locator('[data-gf-resize="top"]').evaluate("el=>getComputedStyle(el).display") == "none"
        assert page.locator('[data-gf-resize="bottom"]').evaluate("el=>getComputedStyle(el).display") == "none"
        page.locator("#takGfEventMinV491").click()
        restored = window.bounding_box()
        assert restored and abs(restored["height"] - after_bottom["height"]) < 3, (restored, after_bottom)

        # Reordering attempts are repaired on the next render/load.
        page.evaluate("document.getElementById('sidebar').appendChild(document.getElementById('geofencePanelV491'))")
        assert not (panel_order(page).index("Geofences") + 1 == next(i for i,n in enumerate(panel_order(page)) if n.startswith("ADS-B")))
        page.evaluate("TakMapGeofencingV491.load()")
        page.wait_for_timeout(250)
        assert_adjacent_order(panel_order(page))

        page.evaluate("TakMapGeofencingV491.remove('gf-ui-v493')")
        page.wait_for_function("!document.getElementById('takGeofenceEventsV491')")
        assert page.locator("#takGeofenceEventsV491").count() == 0
        browser.close()

    fatal = [e for e in errors if any(token in e.lower() for token in ("maximum call stack", "out of memory", "too much recursion"))]
    assert not fatal, fatal
    print("TAK Map i493 conditional Geofence alert window, card order, and height-resize browser test passed")
    return 0


if __name__ == "__main__":
    code=main()
    try: sys.stdout.flush(); sys.stderr.flush()
    except Exception: pass
    os._exit(int(code or 0))
