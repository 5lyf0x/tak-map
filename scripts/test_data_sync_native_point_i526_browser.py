#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'tak_dashboard.py').read_text(errors='replace')


def extract(name: str, marker: str) -> str:
    match = re.search(rf"{re.escape(name)}\s*=\s*r'''(<script id=\"{re.escape(marker)}\">.*?</script>)'''", SOURCE, re.S)
    assert match, marker
    return match.group(1)


IDENTITY = extract('_I511_IDENTITY_UI', 'takMapOtsIdentityV511')
I526 = extract('_I526_HEADER_RUNTIME', 'takMapNativeDataSyncI526')
SESSION = {
    'ok': True,
    'username': 'slyfox',
    'callsign': 'SLYFOX',
    'display_identity': 'SLYFOX',
    'identity_source': 'OpenTAKServer',
    'connection_state': 'Authenticated',
    'is_admin': True,
}

PAGE = f'''<!doctype html><html><head></head><body>
<div class="top-actions"><a id="legacyDashboard" href="/">Dashboard</a></div>
<script>
const SESSION={json.dumps(SESSION)};
window.fetch=async function(url){{
  if(String(url).includes('/api/tak-map/ots/session')) return {{ok:true,status:200,json:async()=>SESSION}};
  return {{ok:true,status:200,json:async()=>({{ok:true}})}};
}};
window.logoutTakMap=function(){{window.__logoutCalled=true}};
</script>
{IDENTITY}
{I526}
<script>
setTimeout(function(){{
  const a=document.createElement('a');a.id='delayedDashboard';a.href='/';a.textContent='Dashboard';
  document.querySelector('.top-actions').appendChild(a);
}},300);
</script>
</body></html>'''


def main() -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        page = browser.new_page(viewport={'width': 1280, 'height': 800})
        page.set_content(PAGE, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_timeout(1200)
        assert page.locator('#legacyDashboard').count() == 0
        assert page.locator('#delayedDashboard').count() == 0
        assert page.locator('.top-actions').get_by_text('Dashboard', exact=True).count() == 0
        button = page.locator('#takMapAccountBtnV511')
        assert button.count() == 1
        assert button.get_attribute('data-i526-bound') == '1'
        button.click()
        menu = page.locator('#takMapAccountMenuV511')
        assert 'open' in (menu.get_attribute('class') or '')
        # A second click closes once; the old listener must not immediately undo it.
        button.click()
        assert 'open' not in (menu.get_attribute('class') or '')
        browser.close()
    print('i526 Dashboard removal and account-menu browser tests passed')


if __name__ == '__main__':
    main()
