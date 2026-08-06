#!/usr/bin/env python3
"""Validate i491 header alignment and source-level themed delete ownership."""
from __future__ import annotations

import json
import re
import runpy
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUB = (ROOT / "scripts" / "leaflet_stub_test.js").read_text()


def self_contained_html() -> str:
    ns = runpy.run_path(str(ROOT / "tak_dashboard.py"), run_name="tak_map_i491_header_delete")
    html = ns["TAK_MAP_HTML"]
    html = re.sub(
        r'<script src="https://unpkg\.com/leaflet@1\.9\.4/dist/leaflet\.js"></script>',
        "<script>" + STUB + "</script>",
        html,
        count=1,
    )
    html = re.sub(r'<link[^>]+unpkg\.com/leaflet@1\.9\.4/dist/leaflet\.css[^>]*>', "", html, count=1)
    # Capture the original main-page functions before the lifecycle runtime replaces
    # the global bindings. Calling these later proves the source functions themselves
    # delegate to the TAK Map dialog rather than invoking window.confirm.
    marker = '<script id="takMapObjectLifecycleLoaderV486"'
    capture = (
        '<script id="takMapSourceDeleteCaptureV486">'
        'window.__takSourceLocalDeleteV486=window.localDataAction;'
        'window.__takSourceDataSyncDeleteV486=window.deleteDataSyncItem;'
        '</script>\n'
    )
    assert marker in html
    html = html.replace(marker, capture + marker, 1)
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
    native_dialogs: list[dict[str, str]] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            executable_path=shutil.which(chromium),
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
        )
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.on("pageerror", lambda error: errors.append(str(error)))

        def dismiss_native(dialog) -> None:
            native_dialogs.append({"type": dialog.type, "message": dialog.message})
            dialog.dismiss()

        page.on("dialog", dismiss_native)
        page.set_content(self_contained_html(), wait_until="domcontentloaded", timeout=25_000)
        page.wait_for_function(
            "window.TakMapObjectLifecycleV486 && window.TakMapCardControlsV477 && window.TakMapGatewayDataV476 && document.readyState === 'complete'",
            timeout=20_000,
        )
        page.wait_for_timeout(6_000)

        alignment = page.evaluate(
            """()=>{
              const rows=[
                ['adsb',document.getElementById('adsbHeaderCountV486'),document.getElementById('adsbHeaderEnableV476')?.closest('.tak-header-switch-v491'),document.querySelector('.panel[data-collapse-key="adsbSettings"] .tak-card-chevron-v491')],
                ['gateway',document.getElementById('gatewayDataTotalV476'),document.getElementById('gatewayDataMasterWrapV476'),document.getElementById('gatewayDataChevronV476')],
                ['datasync',document.getElementById('dataSyncHeaderCountV486'),document.getElementById('dataSyncHeaderEnableV476')?.closest('.tak-header-switch-v491'),document.querySelector('#dataSyncPanelV476 .tak-card-chevron-v491')],
                ['local',document.getElementById('localDataCount'),document.getElementById('localDataHeaderEnableV486')?.closest('.tak-header-switch-v491'),document.querySelector('#localDataPanelV486 .panel-toggle')]
              ];
              return rows.map(([name,chip,toggle,chevron])=>{
                const c=chip?.getBoundingClientRect(),t=toggle?.getBoundingClientRect(),a=chevron?.getBoundingClientRect();
                return {name,present:!!(chip&&toggle&&chevron),chipRight:c?.right||0,toggleLeft:t?.left||0,toggleRight:t?.right||0,chevronRight:a?.right||0,actionsClass:chip?.parentElement?.className||''};
              });
            }"""
        )

        page.evaluate(
            """()=>{
              window.__nativeDeleteConfirmCallsV486=0;
              window.confirm=()=>{window.__nativeDeleteConfirmCallsV486++;return false};
              const local={object_id:'local-source-test',local_id:'local-source-test',_local_id:'local-source-test',source_id:'local-source-test',canonical_id:'local:local-source-test',source_kind:'local',kind:'point',name:'Source Local Point',lat:34.13579,lon:-118.24680,import_name:'Field Notes',source:'Local Data'};
              lastImports=[{id:'imp-source-test',name:'Field Notes',features:[local]}];
              drawImportedObjects();
              state.local.points={'local:local-source-test':true};
              window.__sourceLocalPromiseV486=window.__takSourceLocalDeleteV486('points','delete');
            }"""
        )
        page.wait_for_selector("#takMapDeleteDialogV486", timeout=5_000)
        local_text = page.locator("#takMapDeleteDialogV486").inner_text()
        page.click("#takMapDeleteDialogV486 [data-dialog-cancel]")
        page.evaluate("()=>window.__sourceLocalPromiseV486")

        page.evaluate(
            """()=>{
              const ds={object_id:'datasync-source-test',canonical_id:'datasync:datasync-source-test',source_id:'UID-SOURCE-TEST',source_kind:'datasync',delete_supported:true,mission_name:'Mission Bravo',mission_delete_target:'uid',mission_delete_value:'UID-SOURCE-TEST',uid:'UID-SOURCE-TEST',kind:'point',name:'Source Mission Point',lat:35.97531,lon:-117.86420,source:'Data Sync'};
              lastDataSync={missions:[{name:'Mission Bravo'}],objects:[ds],packages:[]};
              drawDataSyncObjects(lastDataSync.objects);
              window.__sourceDsPromiseV486=window.__takSourceDataSyncDeleteV486(0,null);
            }"""
        )
        page.wait_for_selector("#takMapDeleteDialogV486", timeout=5_000)
        ds_text = page.locator("#takMapDeleteDialogV486").inner_text()
        page.click("#takMapDeleteDialogV486 [data-dialog-cancel]")
        page.evaluate("()=>window.__sourceDsPromiseV486")

        result = page.evaluate(
            """()=>({
              nativeConfirmCalls:window.__nativeDeleteConfirmCallsV486,
              lifecycle:TakMapObjectLifecycleV486.diagnostics(),
              dialog:TakMapDialogV486.diagnostics(),
              card:TakMapCardControlsV477.diagnostics()
            })"""
        )
        browser.close()

    unexpected_errors = [e for e in errors if "localStorage" not in e or "Access is denied" not in e]
    assert not unexpected_errors, unexpected_errors
    assert not native_dialogs, native_dialogs
    assert all(row["present"] for row in alignment), alignment
    for key in ("chipRight", "toggleRight", "chevronRight"):
        values = [row[key] for row in alignment]
        assert max(values) - min(values) <= 1.5, (key, alignment)
    assert all(("tak-card-header-actions-v491" in row["actionsClass"] or row["name"] == "gateway") for row in alignment), alignment
    assert "Source Local Point" in local_text and "Local Data" in local_text and "34.13579" in local_text, local_text
    assert "Source Mission Point" in ds_text and "Mission Bravo" in ds_text and "35.97531" in ds_text, ds_text
    assert result["nativeConfirmCalls"] == 0, result
    assert result["dialog"]["themed"] and not result["dialog"]["nativeConfirm"], result
    print("i491 header alignment and source-level themed delete test passed")
    print(json.dumps({"alignment": alignment, "local": local_text, "datasync": ds_text, "result": result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
