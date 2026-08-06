#!/usr/bin/env python3
"""Load the real generated TAK Map page and guard against the i479/i480 UI regression."""
from __future__ import annotations

import json
import os
import re
import runpy
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUB = (ROOT / "scripts" / "leaflet_stub_test.js").read_text()


def self_contained_html() -> str:
    ns = runpy.run_path(str(ROOT / "tak_dashboard.py"), run_name="tak_map_i491_full_page_browser")
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
        page = browser.new_page()
        page_errors: list[str] = []
        page.on("pageerror", lambda error: page_errors.append(str(error)))

        page.set_content(html, wait_until="domcontentloaded", timeout=20_000)
        page.wait_for_function(
            "window.TakMapToolUxV486 && window.TakMapObjectLifecycleV486 && document.readyState === 'complete'",
            timeout=12_000,
        )
        page.wait_for_timeout(7_000)

        result = page.evaluate(
            """async()=>{
              const nextFrame=()=>new Promise(resolve=>requestAnimationFrame(()=>resolve(true)));
              const frameOk=await Promise.race([nextFrame(),new Promise(resolve=>setTimeout(()=>resolve(false),1000))]);
              const labels=Array.from(document.querySelectorAll('#localDataRows button')).map(b=>(b.innerText||b.textContent||'').replace(/\s+/g,' ').trim());
              const requiredIds=['toolSelectArea','toolMove','toolCoords','toolMeasure','toolPointDropper','toolDraw','toolRoute','toolFit','toolViewshed','tool3d','selectionFitBtn','selectionExportBtn','selectionDeleteBtn','selectionClearBtn','localDataHeaderEnableV486'];
              return {
                ready:document.readyState,
                frameOk,
                totalButtons:document.querySelectorAll('button').length,
                sidebarButtons:document.querySelectorAll('#sidebar button').length,
                toolbarButtons:document.querySelectorAll('#floatingToolbarDock button').length,
                missingRequiredIds:requiredIds.filter(id=>!document.getElementById(id)),
                localButtons:labels,
                routeCancel:(document.querySelector('.tak-route-cancel-v491')?.innerText||'').trim(),
                toolUx:TakMapToolUxV486.diagnostics(),
                lifecycle:TakMapObjectLifecycleV486.diagnostics(),
                geofenceEventWindowPresent:!!document.getElementById('takGeofenceEventsV491'),
                accountControlPresent:!!document.getElementById('takMapAccountBtnV511'),
                legacyTakClientModalPresent:!!document.getElementById('takClientModal')
              };
            }"""
        )
        browser.close()

    assert result["ready"] == "complete", result
    assert result["frameOk"], result
    assert result["totalButtons"] >= 205, result
    assert result["geofenceEventWindowPresent"] is False, result
    assert result["accountControlPresent"] is True, result
    assert result["legacyTakClientModalPresent"] is False, result
    assert result["sidebarButtons"] >= 110, result
    assert result["toolbarButtons"] == 43, result
    assert not result["missingRequiredIds"], result
    for label in ("+ Add Point", "+ Add Route", "+ Add Shape"):
        assert label in result["localButtons"], result
    assert result["localButtons"].count("Unselect All") == 3, result
    assert result["routeCancel"] == "Cancel Route", result
    assert result["toolUx"]["documentWideObserver"] is False, result
    assert result["toolUx"]["classAttributeObserver"] is False, result
    assert result["lifecycle"]["documentWideObserver"] is False, result
    assert result["lifecycle"]["startupSidebarRerenders"] is False, result
    assert result["lifecycle"]["startupLocalControlRenderCount"] == 1, result

    fatal = [
        error
        for error in page_errors
        if any(token in error.lower() for token in ("maximum call stack", "out of memory", "too much recursion"))
    ]
    assert not fatal, fatal
    print("Full generated TAK Map i508 responsiveness/menu browser test passed")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
