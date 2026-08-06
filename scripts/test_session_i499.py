#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import runpy
import shutil
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module():
    old_data = os.environ.get('TAK_DASHBOARD_DATA_DIR')
    old_ttl = os.environ.pop('TAK_DASH_TAK_MAP_SESSION_TTL_SECONDS', None)
    with tempfile.TemporaryDirectory(prefix='tak-map-i499-session-') as td:
        os.environ['TAK_DASHBOARD_DATA_DIR'] = td
        try:
            return runpy.run_path(str(ROOT / 'tak_dashboard.py'), run_name='tak_map_i499_session_test')
        finally:
            if old_data is None:
                os.environ.pop('TAK_DASHBOARD_DATA_DIR', None)
            else:
                os.environ['TAK_DASHBOARD_DATA_DIR'] = old_data
            if old_ttl is not None:
                os.environ['TAK_DASH_TAK_MAP_SESSION_TTL_SECONDS'] = old_ttl


def server_checks(ns):
    assert ns['TAK_MAP_SESSION_TTL_SECONDS'] == 43200
    token = ns['create_tak_map_session']('operator', 'memory-only-password')
    with ns['TAK_MAP_SESSIONS_LOCK']:
        ns['TAK_MAP_SESSIONS'][token]['expires'] = time.time() + 1
        old_expiry = ns['TAK_MAP_SESSIONS'][token]['expires']
    session = ns['get_tak_map_session'](token)
    assert session and session['username'] == 'operator'
    assert session['expires'] > old_expiry + 40000, session

    handler = object.__new__(ns['Handler'])
    handler.path = '/api/tak-map/config'
    handler.headers = {'Cookie': f"{ns['TAK_MAP_COOKIE_NAME']}={token}"}
    headers = handler._tak_map_refresh_headers({}, 200)
    cookie = headers.get('Set-Cookie', '')
    assert f"{ns['TAK_MAP_COOKIE_NAME']}={token}" in cookie, headers
    assert 'Max-Age=43200' in cookie, headers
    assert headers.get('X-TAK-Map-Session-Renewed') == '1', headers

    ns['destroy_tak_map_session'](token)
    expired_headers = handler._tak_map_refresh_headers({}, 200)
    assert 'Set-Cookie' not in expired_headers, expired_headers

    cfg = ns['tak_map_config']()
    session_cfg = cfg['tak_map_session']
    assert cfg['tak_map_iteration'] == 'i541'
    assert session_cfg['sliding_expiration'] is True
    assert session_cfg['cookie_renewed_on_authenticated_response'] is True
    assert session_cfg['ttl_seconds'] == 43200
    assert "get('reason')==='session-expired'" in ns['TAK_MAP_LOGIN_HTML']
    return ns['TAK_MAP_HTML']


def browser_checks(html: str):
    chromium = next((name for name in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable') if shutil.which(name)), None)
    if not chromium:
        print('SKIP: Chromium unavailable for session client test')
        return
    match = re.search(r'<script id="takMapSessionV499">(.*?)</script>', html, re.S)
    if match:
        script = match.group(1)
    else:
        import json
        manifest = json.loads((ROOT / 'assets' / 'tak-map-deferred-i541.json').read_text())
        script = next(row['code'] for row in manifest['scripts'] if row.get('id') == 'takMapSessionV499')
    page_html = f'''<!doctype html><html><head></head><body>
<script>
window.__authEvents=0;window.__timerDelays=[];
window.addEventListener('takmap:auth-required',()=>window.__authEvents++);
window.setTimeout=(fn,ms)=>{{window.__timerDelays.push(ms);return 1}};
window.fetch=async()=>new Response(JSON.stringify({{ok:false,auth_required:true,error:'TAK Map login required.'}}),{{status:401,headers:{{'Content-Type':'application/json'}}}});
</script><script>{script}</script></body></html>'''
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=shutil.which(chromium), args=['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'])
        page = browser.new_page()
        errors = []
        page.on('pageerror', lambda exc: errors.append(str(exc)))
        page.set_content(page_html, wait_until='domcontentloaded')
        result = page.evaluate('''async()=>{const r=await fetch('http://tak-map.test/api/tak-map/adsb');return {status:r.status,eventCount:window.__authEvents,overlay:!!document.getElementById('takMapSessionExpiredV499'),diag:TakMapSessionV499.diagnostics(),timers:window.__timerDelays.slice()}}''')
        browser.close()
    assert not errors, errors
    assert result['status'] == 401
    assert result['eventCount'] == 1, result
    assert result['overlay'] is True, result
    assert result['diag']['expired'] is True, result
    assert 850 in result['timers'], result


def main() -> int:
    ns = load_module()
    html = server_checks(ns)
    browser_checks(html)
    print('TAK Map i508 package / i499 sliding-session and auth-loss client test passed')
    return 0


if __name__ == '__main__':
    code = main()
    try:
        import sys
        sys.stdout.flush(); sys.stderr.flush()
    finally:
        os._exit(code)
