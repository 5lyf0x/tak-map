#!/usr/bin/env python3
"""Exercise the exact live-page paths behind the i483 regression report."""
from __future__ import annotations

import json
import re
import runpy
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUB = (ROOT / "scripts" / "leaflet_stub_test.js").read_text()


def self_contained_html() -> str:
    ns = runpy.run_path(str(ROOT / "tak_dashboard.py"), run_name="tak_map_i491_reported_regressions")
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

    native_dialogs: list[dict[str, str]] = []
    page_errors: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            executable_path=shutil.which(chromium),
            args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
        )
        page = browser.new_page()
        page.on("pageerror", lambda error: page_errors.append(str(error)))

        def dismiss_native(dialog) -> None:
            native_dialogs.append({"type": dialog.type, "message": dialog.message})
            dialog.dismiss()

        page.on("dialog", dismiss_native)
        page.set_content(self_contained_html(), wait_until="domcontentloaded", timeout=20_000)
        page.wait_for_function(
            "window.TakMapObjectLifecycleV486 && window.TakMapToolUxV486 && window.TakMapCardControlsV477 && document.readyState === 'complete'",
            timeout=15_000,
        )
        page.wait_for_timeout(5_500)

        header = page.evaluate(
            """()=>{
              const panel=document.getElementById('localDataPanelV486')||[...document.querySelectorAll('.panel')].find(p=>/Local Data/.test(p.querySelector(':scope>h2')?.textContent||''));
              const header=panel?.querySelector(':scope>h2');
              const input=document.getElementById('localDataHeaderEnableV486');
              const button=input?.closest('.tak-header-switch-v491')?.querySelector('.tak-header-switch-button-v491');
              return {panel:!!panel,input:!!input,button:!!button,inHeader:!!button&&button.closest('h2')===header,checked:!!input?.checked,diagnostics:TakMapCardControlsV477.diagnostics()};
            }"""
        )

        page.evaluate(
            """()=>{
              window.__nativeConfirmCalls=0;
              window.confirm=()=>{window.__nativeConfirmCalls++;return false};
              const local={
                object_id:'local-delete-test',local_id:'local-delete-test',_local_id:'local-delete-test',source_id:'local-delete-test',
                canonical_id:'local:local-delete-test',source_kind:'local',kind:'point',name:'Local Delete Test',lat:34.12345,lon:-118.54321,
                import_name:'Field Notes',source:'Local Data'
              };
              lastImports=[{id:'imp-delete-test',name:'Field Notes',features:[local]}];
              drawImportedObjects();
              state.local.points={'local:local-delete-test':true};
              window.__localDeletePromise=localDataAction('points','delete');
            }"""
        )
        page.wait_for_selector("#takMapDeleteDialogV486", timeout=5_000)
        local_dialog = page.evaluate(
            """()=>({
              text:document.getElementById('takMapDeleteDialogV486')?.innerText||'',
              nativeConfirmCalls:window.__nativeConfirmCalls,
              lifecycleOpen:TakMapDialogV486.diagnostics().open
            })"""
        )
        page.click("#takMapDeleteDialogV486 [data-dialog-cancel]")
        page.evaluate("()=>window.__localDeletePromise")

        page.evaluate(
            """()=>{
              const ds={
                object_id:'datasync-delete-test',canonical_id:'datasync:datasync-delete-test',source_id:'UID-DELETE-TEST',source_kind:'datasync',
                delete_supported:true,mission_name:'Mission Alpha',mission_delete_target:'uid',mission_delete_value:'UID-DELETE-TEST',
                uid:'UID-DELETE-TEST',kind:'point',name:'Data Sync Delete Test',lat:35.11111,lon:-117.22222,source:'Data Sync'
              };
              lastDataSync={missions:[{name:'Mission Alpha'}],objects:[ds],packages:[]};
              drawDataSyncObjects(lastDataSync.objects);
              window.__dataSyncDeletePromise=deleteDataSyncItem(0,null);
            }"""
        )
        page.wait_for_selector("#takMapDeleteDialogV486", timeout=5_000)
        data_sync_dialog = page.evaluate(
            """()=>({
              text:document.getElementById('takMapDeleteDialogV486')?.innerText||'',
              nativeConfirmCalls:window.__nativeConfirmCalls,
              lifecycleOpen:TakMapDialogV486.diagnostics().open
            })"""
        )
        page.click("#takMapDeleteDialogV486 [data-dialog-cancel]")
        page.evaluate("()=>window.__dataSyncDeletePromise")

        result = page.evaluate(
            """()=>({
              nativeConfirmCalls:window.__nativeConfirmCalls,
              lifecycle:TakMapObjectLifecycleV486.diagnostics(),
              dialog:TakMapDialogV486.diagnostics(),
              localToggle:TakMapCardControlsV477.diagnostics()
            })"""
        )
        browser.close()

    assert header["panel"] and header["input"] and header["button"] and header["inHeader"] and header["checked"], header
    assert local_dialog["lifecycleOpen"] and local_dialog["nativeConfirmCalls"] == 0, local_dialog
    assert "Local Delete Test" in local_dialog["text"] and "Point" in local_dialog["text"] and "Local Data" in local_dialog["text"], local_dialog
    assert "34.12345" in local_dialog["text"] and "-118.54321" in local_dialog["text"], local_dialog
    assert data_sync_dialog["lifecycleOpen"] and data_sync_dialog["nativeConfirmCalls"] == 0, data_sync_dialog
    assert "Data Sync Delete Test" in data_sync_dialog["text"] and "Mission Alpha" in data_sync_dialog["text"], data_sync_dialog
    assert "35.11111" in data_sync_dialog["text"] and "-117.22222" in data_sync_dialog["text"], data_sync_dialog
    assert result["nativeConfirmCalls"] == 0 and not native_dialogs, (result, native_dialogs)
    assert result["lifecycle"]["themedDeleteDialog"] and result["lifecycle"]["nativeDeleteConfirm"] is False, result
    assert result["localToggle"]["localDataHeaderToggle"] and result["localToggle"]["localDataEnabled"], result

    fatal = [e for e in page_errors if any(token in e.lower() for token in ("maximum call stack", "out of memory", "too much recursion"))]
    assert not fatal, fatal
    print("i491 live-page reported-regression browser test passed")
    print(json.dumps({"header": header, "localDialog": local_dialog, "dataSyncDialog": data_sync_dialog, "result": result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
