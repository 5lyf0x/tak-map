#!/usr/bin/env python3
"""Browser DOM gate for Replay Search in the final i622 served Replay script."""
from __future__ import annotations
from pathlib import Path
import re
import runpy
import shutil

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    chromium = next((shutil.which(n) for n in ('chromium','chromium-browser','google-chrome','google-chrome-stable') if shutil.which(n)), None)
    if not chromium:
        print('SKIP: Chromium unavailable')
        return 0

    ns = runpy.run_path(str(ROOT / 'tak_dashboard.py'), run_name='tak_map_i622_browser_contract')
    final_html = str(ns['TAK_MAP_HTML'])
    m = re.search(r'(<script id="v415ReplayModeIntegrationPatch">[\s\S]*?</script>)', final_html)
    assert m, 'Final served HTML does not contain Replay integration script'
    replay_script = m.group(1)
    assert 'replaySearchInputI621' in replay_script

    fixture = f'''<!doctype html><html><head><meta charset="utf-8"><style>
    html,body{{margin:0;background:#071018;color:#eee;font-family:Arial,sans-serif}}#sidebar{{width:396px;padding:8px}}.replay-v415-hidden{{display:none!important}}.replay-confirm-v415{{display:none}}
    </style></head><body><div id="sidebar"><div class="version-panel"><div class="version-product">TAK Map</div><span class="release-main">1.4.0</span><span class="iteration-chip">i622</span></div></div><div id="mapStatusBanner"></div>
    <script>
    window.fetch=async function(input){{
      const u=String(input&&input.url||input||'');
      let body={{ok:true}};
      if(u.includes('/api/tak-map/replay/config')) body={{ok:true,configured:true}};
      else if(u.includes('/api/tak-map/config')) body={{ok:true,default_basemap:'test',basemaps:[{{id:'test',type:'xyz',url:'about:blank',options:{{}}}}]}};
      else if(u.includes('/api/tak-map/replay/periods')) body={{ok:true,periods:[{{id:'period-1',start_utc:'2026-08-10T12:00:00Z',end_utc:'2026-08-10T12:01:00Z',duration_seconds:60}}]}};
      else if(u.includes('/api/tak-map/replay/events')) body={{ok:true,events:[]}};
      else if(u.includes('/api/tak-map/replay/search')) body={{ok:true,results:[]}};
      return new Response(JSON.stringify(body),{{status:200,headers:{{'Content-Type':'application/json'}}}});
    }};
    function chain(){{return {{on(){{return this}},addTo(){{return this}},setView(){{return this}},invalidateSize(){{}},remove(){{}},removeLayer(){{}},addLayer(){{}},hasLayer(){{return false}},panTo(){{}},getCenter(){{return {{lat:34,lng:-118}}}},getZoom(){{return 9}},clearLayers(){{}}}}}}
    window.L={{map:()=>chain(),control:{{scale:()=>chain()}},layerGroup:()=>chain(),tileLayer:function(){{return chain()}},divIcon:()=>({{}}),marker:()=>chain(),DomEvent:{{stopPropagation(){{}},preventDefault(){{}}}}}};
    window.L.tileLayer.wms=()=>chain();
    </script>{replay_script}</body></html>'''

    from playwright.sync_api import sync_playwright
    errors: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=chromium, args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
        page = browser.new_page(viewport={'width':1280,'height':760})
        page.on('pageerror', lambda exc: errors.append(str(exc)))
        page.set_content(fixture, wait_until='domcontentloaded', timeout=20_000)
        page.wait_for_selector('#replaySearchInputI621', state='attached', timeout=7_000)
        initial = page.evaluate('''() => {
          const p=document.getElementById('replayPeriodV415');
          const box=document.getElementById('replaySearchI621');
          const input=document.getElementById('replaySearchInputI621');
          return {afterPeriod:p.closest('.replay-select-field-v433').nextElementSibling===box,disabled:input.disabled,placeholder:input.placeholder};
        }''')
        assert initial['afterPeriod'] and initial['disabled'], initial
        assert 'Flight' in initial['placeholder'] and 'ICAO' in initial['placeholder'], initial

        page.evaluate("() => {const t=document.getElementById('replayModeToggleV415');t.dispatchEvent(new Event('change',{bubbles:true}))}")
        page.wait_for_function("document.getElementById('replayConfirmV415').style.display === 'grid'", timeout=5_000)
        page.evaluate("document.getElementById('replayConfirmOkV415').click()")
        page.wait_for_function("document.querySelectorAll('#replayPeriodV415 option').length >= 2", timeout=7_000)
        page.evaluate("() => {const s=document.getElementById('replayPeriodV415');s.value='period-1';s.dispatchEvent(new Event('change',{bubbles:true}))}")
        page.wait_for_function("document.getElementById('replaySearchInputI621').disabled === false", timeout=7_000)
        state = page.evaluate('''() => ({
          visible: !!(document.getElementById('replaySearchI621').offsetWidth || document.getElementById('replaySearchI621').offsetHeight),
          disabled: document.getElementById('replaySearchInputI621').disabled,
          status: document.getElementById('replaySearchStatusI621').textContent,
          iteration: document.documentElement.dataset.takMapIteration
        })''')
        assert state['visible'] and not state['disabled'], state
        assert 'Ready to search the entire selected recording.' in state['status'], state
        assert state['iteration'] == 'i622', state
        browser.close()
    assert not errors, errors
    print('TAK Map i622 Replay Search final DOM/browser visibility contract passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
