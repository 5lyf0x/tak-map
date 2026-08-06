#!/usr/bin/env python3
"""Validate i491 stable Data Sync summary, content-sized chips, and Satellite card order."""
from __future__ import annotations

import json
import re
import runpy
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUB = (ROOT / "scripts" / "leaflet_stub_test.js").read_text()


def self_contained_html() -> str:
    ns = runpy.run_path(str(ROOT / "tak_dashboard.py"), run_name="tak_map_i491_header_stability")
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

    errors: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            executable_path=shutil.which(chromium),
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
        )
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.set_content(self_contained_html(), wait_until="domcontentloaded", timeout=25_000)
        page.wait_for_function(
            "window.TakMapCardControlsV477 && window.TakMapGatewayDataV476 && document.readyState === 'complete'",
            timeout=20_000,
        )
        page.wait_for_timeout(6_000)

        initial = page.evaluate(
            """()=>{
              const duplicateObject={canonical_id:'datasync:UID-ONE',uid:'UID-ONE',name:'Shared Item',kind:'point'};
              lastDataSync={
                missions:[{name:'Mission Alpha',id:'MIS-A'},{name:'Mission Alpha',id:'MIS-A'}],
                objects:[duplicateObject,Object.assign({},duplicateObject)],
                packages:[{hash:'HASH-PACKAGE-ONE',filename:'Package One.zip'},{hash:'HASH-PACKAGE-ONE',filename:'Package One.zip'}]
              };
              TakMapCardControlsV477.refresh();
              const chip=document.getElementById('dataSyncHeaderCountV486');
              const gateway=document.getElementById('gatewayDataTotalV476');
              const sidebar=document.getElementById('sidebar');
              const sat=document.getElementById('satelliteTrackingPanelV409')||document.getElementById('satelliteTrackingPanelV408');
              const title=p=>String(p?.querySelector(':scope > h2,.gateway-heading h2')?.textContent||'').trim();
              return {
                text:chip?.textContent||'',
                chipRect:chip?{left:chip.getBoundingClientRect().left,right:chip.getBoundingClientRect().right,width:chip.getBoundingClientRect().width}:null,
                gatewayRect:gateway?{left:gateway.getBoundingClientRect().left,right:gateway.getBoundingClientRect().right,width:gateway.getBoundingClientRect().width,scrollWidth:gateway.scrollWidth,text:gateway.textContent}:null,
                diagnostics:TakMapCardControlsV477.diagnostics(),
                panelOrder:Array.from(sidebar.children).filter(x=>x.classList?.contains('panel')).map(title),
                satId:sat?.id||''
              };
            }"""
        )

        page.evaluate(
            """()=>{
              const mission=document.getElementById('missionCount');
              const objects=document.getElementById('dataSyncObjectCount');
              for(let i=0;i<40;i++){
                if(mission)mission.textContent=(i%2?99:1)+' missions';
                if(objects)objects.textContent=(i%2?47:2)+' objects';
                TakMapCardControlsV477.refresh();
              }
              const sidebar=document.getElementById('sidebar');
              const sat=document.getElementById('satelliteTrackingPanelV409')||document.getElementById('satelliteTrackingPanelV408');
              if(sidebar&&sat)sidebar.appendChild(sat);
              TakMapCardControlsV477.refresh();
            }"""
        )
        page.wait_for_timeout(250)

        final = page.evaluate(
            """()=>{
              const chip=document.getElementById('dataSyncHeaderCountV486');
              const gateway=document.getElementById('gatewayDataTotalV476');
              const sidebar=document.getElementById('sidebar');
              const sat=document.getElementById('satelliteTrackingPanelV409')||document.getElementById('satelliteTrackingPanelV408');
              const panels=Array.from(sidebar.children).filter(x=>x.classList?.contains('panel'));
              const title=p=>String(p?.querySelector(':scope > h2,.gateway-heading h2')?.textContent||'').trim();
              const order=panels.map(title);
              const offlineIndex=order.indexOf('Offline Maps'),satIndex=panels.indexOf(sat),toolsIndex=order.indexOf('Tools');
              const rect=chip?.getBoundingClientRect(),grect=gateway?.getBoundingClientRect();
              return {
                text:chip?.textContent||'',
                chipRect:rect?{left:rect.left,right:rect.right,width:rect.width}:null,
                gatewayRect:grect?{left:grect.left,right:grect.right,width:grect.width,scrollWidth:gateway.scrollWidth,text:gateway.textContent}:null,
                duplicateChipCount:document.querySelectorAll('#dataSyncHeaderCountV486').length,
                authoritativeOwner:chip?.dataset.authoritativeOwner||'',
                authoritativeText:chip?.dataset.authoritativeText||'',
                legacyMissionHidden:document.getElementById('missionCount')?.hidden===true,
                legacyObjectHidden:document.getElementById('dataSyncObjectCount')?.hidden===true,
                order,offlineIndex,satIndex,toolsIndex,
                diagnostics:TakMapCardControlsV477.diagnostics()
              };
            }"""
        )
        browser.close()

    unexpected = [e for e in errors if "localStorage" not in e or "Access is denied" not in e]
    assert not unexpected, unexpected
    assert initial["text"] == "1 MIS, 2 ITEMS", initial
    assert final["text"] == "1 MIS, 2 ITEMS", final
    assert final["authoritativeOwner"] == "i491", final
    assert final["authoritativeText"] == "1 MIS, 2 ITEMS", final
    assert final["duplicateChipCount"] == 1, final
    assert final["legacyMissionHidden"] and final["legacyObjectHidden"], final
    assert abs(final["chipRect"]["right"] - initial["chipRect"]["right"]) <= 0.5, (initial, final)
    assert abs(final["chipRect"]["width"] - initial["chipRect"]["width"]) <= 0.5, (initial, final)
    assert final["diagnostics"]["dataSyncChipWrites"] == initial["diagnostics"]["dataSyncChipWrites"], (initial, final)
    assert final["diagnostics"]["dataSyncChipSkips"] > initial["diagnostics"]["dataSyncChipSkips"], (initial, final)
    assert final["gatewayRect"]["width"] < 90, final
    assert final["gatewayRect"]["width"] <= final["gatewayRect"]["scrollWidth"] + 2.5, final
    assert final["offlineIndex"] >= 0 and final["satIndex"] == final["offlineIndex"] + 1, final
    assert final["toolsIndex"] > final["satIndex"], final
    assert final["diagnostics"]["satelliteOrdered"], final
    assert final["diagnostics"]["satelliteOrderFixes"] == initial["diagnostics"]["satelliteOrderFixes"] + 1, (initial, final)
    print("i491 Data Sync chip stability, content width, and Satellite order test passed")
    print(json.dumps({"initial": initial, "final": final}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
