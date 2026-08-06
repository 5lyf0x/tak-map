#!/usr/bin/env python3
"""Verify i491 Viewshed default placement, stability, and header dragging."""
from __future__ import annotations

import json
import re
import runpy
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUB = (ROOT / "scripts" / "leaflet_stub_test.js").read_text()


def self_contained_html() -> str:
    ns = runpy.run_path(str(ROOT / "tak_dashboard.py"), run_name="tak_map_i491_viewshed_browser")
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

    html = self_contained_html()
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            executable_path=shutil.which(chromium),
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
        )
        page = browser.new_page(viewport={"width": 1400, "height": 900})
        page_errors: list[str] = []
        page.on("pageerror", lambda error: page_errors.append(str(error)))

        page.evaluate("""()=>{
          function makeStorage(){const data=Object.create(null);return {getItem:k=>Object.prototype.hasOwnProperty.call(data,String(k))?data[String(k)]:null,setItem:(k,v)=>{data[String(k)]=String(v)},removeItem:k=>{delete data[String(k)]},clear:()=>{for(const k of Object.keys(data))delete data[k]},key:i=>Object.keys(data)[i]||null,get length(){return Object.keys(data).length}}}
          Object.defineProperty(window,'localStorage',{value:makeStorage(),configurable:true});
          Object.defineProperty(window,'sessionStorage',{value:makeStorage(),configurable:true});
        }""")
        page.set_content(html, wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_function(
            "document.readyState === 'complete' && document.getElementById('toolViewshed')",
            timeout=15_000,
        )
        page.wait_for_timeout(7_000)
        page.evaluate(
            """()=>{
              sessionStorage.clear();
              localStorage.setItem('takmap.viewshed.modulePos',JSON.stringify({left:20,top:700}));
            }"""
        )

        page.click("#toolViewshed")

        def snapshot() -> dict:
            return page.evaluate(
                """()=>{
                  const panel=document.getElementById('viewshedModule');
                  const toolbar=document.getElementById('floatingMapToolbar');
                  const p=panel.getBoundingClientRect(), t=toolbar.getBoundingClientRect();
                  return {
                    panel:{left:p.left,top:p.top,right:p.right,bottom:p.bottom,width:p.width,height:p.height},
                    toolbar:{left:t.left,top:t.top,right:t.right,bottom:t.bottom,width:t.width,height:t.height},
                    gap:t.left-p.right,
                    topDelta:p.top-t.top,
                    active:panel.classList.contains('active'),
                    visibility:getComputedStyle(panel).visibility,
                    display:getComputedStyle(panel).display,
                    stableOpen:panel.dataset.viewshedStableOpen||'',
                    userPosition:panel.dataset.viewshedUserPosition||'',
                    sessionPosition:sessionStorage.getItem('takmap.viewshed.modulePos.i491'),
                    oldLocalPosition:localStorage.getItem('takmap.viewshed.modulePos')
                  };
                }"""
            )

        samples = [snapshot()]
        previous_ms = 0
        for total_ms in (50, 300, 1_000, 3_000):
            page.wait_for_timeout(total_ms - previous_ms)
            samples.append(snapshot())
            previous_ms = total_ms

        first = samples[0]
        assert first["active"] and first["display"] != "none" and first["visibility"] == "visible", samples
        assert 8 <= first["gap"] <= 16, samples
        assert abs(first["topDelta"]) <= 2, samples
        assert first["panel"]["left"] > 100, samples  # old localStorage position must be ignored
        assert first["stableOpen"] == "1", samples
        assert all(abs(sample["panel"]["left"] - first["panel"]["left"]) <= 1 for sample in samples), samples
        assert all(abs(sample["panel"]["top"] - first["panel"]["top"]) <= 1 for sample in samples), samples

        page.evaluate(
            """()=>{
              const marker=document.createElement('div'); marker.id='viewshedPositionMutationTest';
              document.body.appendChild(marker); marker.className='changed'; marker.remove();
              document.getElementById('sidebar')?.classList.toggle('test-refresh');
              document.getElementById('sidebar')?.classList.toggle('test-refresh');
              window.dispatchEvent(new Event('resize'));
            }"""
        )
        page.wait_for_timeout(1_000)
        after_refresh = snapshot()
        assert abs(after_refresh["panel"]["left"] - first["panel"]["left"]) <= 1, (samples, after_refresh)
        assert abs(after_refresh["panel"]["top"] - first["panel"]["top"]) <= 1, (samples, after_refresh)

        header = page.locator("#viewshedModule .viewshed-head")
        box = header.bounding_box()
        assert box, "Viewshed header missing"
        start_x = box["x"] + box["width"] * 0.45
        start_y = box["y"] + box["height"] * 0.5
        page.mouse.move(start_x, start_y)
        page.mouse.down()
        page.mouse.move(start_x - 110, start_y + 45, steps=8)
        page.mouse.up()
        page.wait_for_timeout(250)
        dragged = snapshot()
        assert dragged["panel"]["left"] < first["panel"]["left"] - 70, (first, dragged)
        assert dragged["panel"]["top"] > first["panel"]["top"] + 25, (first, dragged)
        assert dragged["userPosition"] == "1", dragged
        assert dragged["sessionPosition"], dragged

        page.evaluate(
            """()=>{
              const body=document.body; body.classList.add('viewshed-refresh-test'); body.classList.remove('viewshed-refresh-test');
              window.dispatchEvent(new Event('resize'));
            }"""
        )
        page.wait_for_timeout(2_500)
        after_drag_wait = snapshot()
        assert abs(after_drag_wait["panel"]["left"] - dragged["panel"]["left"]) <= 1, (dragged, after_drag_wait)
        assert abs(after_drag_wait["panel"]["top"] - dragged["panel"]["top"]) <= 1, (dragged, after_drag_wait)

        page.evaluate("window.toggleViewshedModule(false)")
        page.wait_for_timeout(100)
        page.evaluate("window.toggleViewshedModule(true)")
        page.wait_for_timeout(1_000)
        reopened = snapshot()
        assert abs(reopened["panel"]["left"] - dragged["panel"]["left"]) <= 1, (dragged, reopened)
        assert abs(reopened["panel"]["top"] - dragged["panel"]["top"]) <= 1, (dragged, reopened)
        assert reopened["userPosition"] == "1", reopened

        browser.close()

    fatal = [
        error
        for error in page_errors
        if any(token in error.lower() for token in ("maximum call stack", "out of memory", "too much recursion"))
    ]
    assert not fatal, fatal
    result = {
        "initial": first,
        "samples": samples,
        "after_refresh": after_refresh,
        "dragged": dragged,
        "after_drag_wait": after_drag_wait,
        "reopened": reopened,
    }
    print("Viewshed i491 stable placement/drag browser test passed")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
