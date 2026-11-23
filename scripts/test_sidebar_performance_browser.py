#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import re
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "assets" / "tak-map-sidebar-performance-v491.js"
FINAL_HTML = str(runpy.run_path(str(ROOT / 'tak_dashboard.py'), run_name='tak_map_sidebar_i625_contract')['TAK_MAP_HTML'])
IDENTITY_GUARD = re.search(r'<script id="takMapIdentityGuardI630">.*?</script>', FINAL_HTML, re.S).group(0)
ORIGIN = "https://takmap.test"


def main() -> int:
    chromium = shutil.which("chromium") or shutil.which("chromium-browser")
    if not chromium:
        print("SKIP: Chromium unavailable")
        return 0

    from playwright.sync_api import sync_playwright

    fixture = r'''<!doctype html><html data-tak-map-iteration="i620" data-tak-map-package="1.4.0-i620"><head><meta charset="utf-8"><style>
      html,body{margin:0;height:100%}#sidebar{height:400px;overflow:auto;width:396px}
      .panel{height:180px;border:1px solid #333}.iteration-chip{display:inline-block}
    </style></head><body>
      <div id="sidebar">
        <div class="panel"><span class="iteration-chip" data-iteration="i620">i620</span></div>
        <div class="panel"></div><div class="panel"></div><div class="panel"></div><div class="panel"></div>
      </div>
      <pre id="result"></pre>
      <script>
        const chip=document.querySelector('.iteration-chip');
        function legacyWrite(){chip.textContent='i602';chip.setAttribute('data-iteration','i602');document.documentElement.dataset.takMapIteration='i602'}
        window.__takVersionObserverV442=new MutationObserver(()=>requestAnimationFrame(legacyWrite));
        window.__takVersionObserverV442.observe(document.body,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:['data-iteration']});
        legacyWrite();
        window.__legacyTimer=setInterval(legacyWrite,2);
      </script>
      <script src="https://takmap.test/assets/runtime/tak-map-sidebar-performance-v491.js?v=1.3.0-i491"></script>
      <script>
        (async()=>{
          await new Promise(r=>setTimeout(r,250));
          let total=0,chipMutations=0,attrMutations=0,childMutations=0;
          const sidebar=document.getElementById('sidebar');
          const observedChip=document.querySelector('.iteration-chip');
          const mo=new MutationObserver(records=>{
            for(const rec of records){
              total++;
              if(rec.target===observedChip||rec.target.parentElement===observedChip)chipMutations++;
              if(rec.type==='attributes')attrMutations++;
              if(rec.type==='childList')childMutations++;
            }
          });
          mo.observe(sidebar,{subtree:true,childList:true,characterData:true,attributes:true});
          const frames=[],iterationFrames=[];let last=performance.now(),running=true;
          function raf(now){if(!running)return;frames.push(now-last);iterationFrames.push(observedChip.textContent);last=now;requestAnimationFrame(raf)}requestAnimationFrame(raf);
          const start=performance.now();
          while(performance.now()-start<2200){
            sidebar.scrollTop=(sidebar.scrollTop+19)%Math.max(1,sidebar.scrollHeight-sidebar.clientHeight);
            await new Promise(r=>setTimeout(r,8));
          }
          running=false;mo.disconnect();
          const dynamic=document.createElement('span');dynamic.className='iteration-chip';dynamic.textContent='v409';dynamic.setAttribute('data-iteration','v409');document.querySelector('.panel').appendChild(dynamic);
          await new Promise(r=>setTimeout(r,80));
          clearInterval(window.__legacyTimer);
          const d=window.TakMapSidebarPerformanceV476.diagnostics();
          const sorted=frames.slice(2).sort((a,b)=>a-b);const p95=sorted.length?sorted[Math.min(sorted.length-1,Math.floor(sorted.length*.95))]:0;
          const authority=window.__takMapReleaseIdentity||null;const result={total,chipMutations,attrMutations,childMutations,p95FrameMs:Number(p95.toFixed(1)),diagnostics:d,dynamicText:dynamic.textContent,dynamicIteration:dynamic.getAttribute('data-iteration'),iterationFrames,authority:authority&&{release:authority.release,iteration:authority.iteration,packageVersion:authority.packageVersion},identityGuard:!!Node.prototype.__takMapIdentityAuthorityI620};
          const pass=d.textContentGuardInstalled&&d.setAttributeGuardInstalled&&d.legacyObserversDisconnected>=1&&d.stable&&authority&&authority.iteration==='i635'&&authority.packageVersion==='1.4.0-i635'&&Node.prototype.__takMapIdentityAuthorityI620&&iterationFrames.length>30&&iterationFrames.every(v=>v==='i635')&&chipMutations<=4&&total<=8&&dynamic.textContent==='i635'&&dynamic.getAttribute('data-iteration')==='i635'&&d.currentIteration==='i635';
          document.body.dataset.testResult=pass?'pass':'fail';
          document.getElementById('result').textContent=JSON.stringify(result);
        })().catch(e=>{document.body.dataset.testResult='error';document.getElementById('result').textContent=String(e&&e.stack||e)});
      </script>
    </body></html>'''

    fixture = fixture.replace('</head>', IDENTITY_GUARD + '</head>', 1)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=chromium, args=["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"])
        page = browser.new_page()
        page_errors: list[str] = []
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))

        def route_request(route):
            url = route.request.url
            if url == ORIGIN + "/":
                route.fulfill(status=200, content_type="text/html; charset=utf-8", body=fixture)
            elif url.startswith(ORIGIN + "/assets/runtime/tak-map-sidebar-performance-v491.js"):
                route.fulfill(status=200, content_type="application/javascript; charset=utf-8", body=ASSET.read_text())
            else:
                route.fulfill(status=404, content_type="text/plain", body="not found")

        page.route("**/*", route_request)
        page.set_content(fixture, wait_until="domcontentloaded")
        page.wait_for_function("document.body.dataset.testResult", timeout=10000)
        result = page.get_attribute("body", "data-test-result")
        detail = page.text_content("#result") or ""
        browser.close()

    if result != "pass":
        raise AssertionError(f"sidebar performance fixture result={result}: {detail}; page errors={page_errors}")
    if page_errors:
        raise AssertionError(f"sidebar performance fixture page errors: {page_errors}")
    parsed = json.loads(detail)
    print("Sidebar i625 authoritative iteration and anti-flicker browser test passed")
    print(json.dumps({k: parsed[k] for k in ["total", "chipMutations", "attrMutations", "childMutations", "p95FrameMs"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
