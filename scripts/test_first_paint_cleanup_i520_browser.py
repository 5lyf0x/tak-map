#!/usr/bin/env python3
from __future__ import annotations
import re
import runpy
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
ns = runpy.run_path(str(ROOT / 'tak_dashboard.py'), run_name='tak_map_i520_first_paint_browser')
HTML = ns['TAK_MAP_HTML']
ACCOUNT = ns['_I520_ACCOUNT_HTML']
ADSB = ns['_I520_ADSB_PANEL_HTML']


def inline_script(script_id: str) -> str:
    match = re.search(
        rf'<script\b[^>]*id=["\']{re.escape(script_id)}["\'][^>]*>([\s\S]*?)</script>',
        HTML,
        re.I,
    )
    assert match, script_id
    return match.group(1)


# Exercise the startup paths that previously hid/replaced/recreated the retired
# controls, without loading the full map and its unrelated long-lived workers.
STARTUP = '\n'.join([
    inline_script('v320AdsbControlsRuntime'),
    inline_script('takMapConfigureOtsV509'),
    inline_script('takMapOtsIdentityV511'),
    (ROOT / 'assets/tak-map-card-controls-v491.js').read_text(),
    (ROOT / 'assets/tak-map-adsb-v491.js').read_text(),
])

PAGE = f'''<!doctype html><html><head></head><body>
<div class="topbar">{ACCOUNT}</div>
<aside id="sidebar">{ADSB}</aside>
<div id="mapStatusBanner"><span id="bannerDownloadsItem"></span></div>
<div id="floatingMapToolbar"></div>
<script>
window.fetch=async function(url){{
  if(String(url).includes('/api/tak-map/ots/session')) return {{ok:true,json:async()=>({{ok:true,is_admin:true,display_identity:'SLYFOX',username:'jon',identity_source:'OpenTAKServer',connection_state:'Authenticated'}})}};
  if(String(url).includes('/api/tak-map/adsb-settings')) return {{ok:true,json:async()=>({{ok:true,settings:{{radius_miles:10,update_interval_seconds:5,center_source:'manual',center_lat:34.3,center_lon:-118.6}}}})}};
  return {{ok:true,json:async()=>({{ok:true}})}};
}};
window.config={{adsb:{{settings:{{}}}}}};
window.TakMapControllers={{adsb:{{lastList:[],markers:new Map(),data:new Map()}}}};
window.refreshAdsb=function(){{return Promise.resolve([])}};
window.drawAircraft=function(){{}};
</script>
<script>{STARTUP}</script>
</body></html>'''


def snapshot(page):
    return page.evaluate("""() => ({
      oldIds: ['adsbToggleBtn','takClientSetupBtn','mapCertSetupBtn','takClientModal','takClientReminder']
        .filter(id => document.getElementById(id)),
      oldActions: [...document.querySelectorAll('button,a')]
        .map(n => String(n.textContent || '').replace(/\\s+/g,' ').trim())
        .filter(t => ['TAK Client','Cert Setup','Map Logout','Enable ADS-B'].includes(t)),
      adsbPanels: document.querySelectorAll('[data-collapse-key="adsbSettings"]').length,
      currentAdsb: document.querySelectorAll('.tak-adsb-authoritative-i520').length,
      typeCards: document.querySelectorAll('.adsb-type-card-v491').length,
      account: document.querySelectorAll('#takAccountV511').length,
      accountButton: document.querySelectorAll('#takMapAccountBtnV511').length,
      headerSwitch: document.querySelectorAll('#adsbHeaderEnableV476').length
    })""")


def assert_current(state):
    assert state['oldIds'] == [], state
    assert state['oldActions'] == [], state
    assert state['adsbPanels'] == 1, state
    assert state['currentAdsb'] == 1, state
    assert state['typeCards'] == 4, state
    assert state['account'] == 1 and state['accountButton'] == 1, state
    assert state['headerSwitch'] == 1, state


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        page = browser.new_page(viewport={'width': 1440, 'height': 900})
        page.on('dialog', lambda dialog: dialog.dismiss())
        page.set_content(PAGE, wait_until='domcontentloaded', timeout=60000)
        assert_current(snapshot(page))
        page.wait_for_timeout(9500)
        assert_current(snapshot(page))
        browser.close()
    print('TAK Map i520 first-paint and delayed-startup browser cleanup test passed')


if __name__ == '__main__':
    main()
