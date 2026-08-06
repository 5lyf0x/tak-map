#!/usr/bin/env python3
from __future__ import annotations
import runpy
from playwright.sync_api import sync_playwright

ns = runpy.run_path('tak_dashboard.py', run_name='tak_map_login_i513_browser_source')
html = ns['TAK_MAP_LOGIN_HTML']
stub = r'''<script>
window.__loginRequests=[];
window.fetch=async function(url,opt){
  if(url==='/api/tak-map/ots/public-status') return {ok:true,status:200,json:async()=>({ok:true,ots_connected:true,enabled:true,login_enabled:true})};
  if(url==='/api/tak-map/login'){
    window.__loginRequests.push(String(opt&&opt.body||''));
    return {ok:false,status:401,json:async()=>({ok:false,error:'Test login rejection'})};
  }
  return {ok:false,status:404,json:async()=>({ok:false,error:'not found'})};
};
</script>'''
needle = '<script>\n(function(){\'use strict\';'
assert needle in html
html = html.replace(needle, stub + needle, 1)

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 1280, 'height': 800})
    errors=[]
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.set_content(html, wait_until='domcontentloaded')
    page.wait_for_timeout(300)
    assert page.locator('#takMapLoginForm').count() == 1
    assert page.locator('#otsMode').inner_text() == 'OpenTAKServer Login'
    assert page.locator('#localMode').inner_text() == 'Local Login'
    assert page.locator('#takMapLoginButton').inner_text() == 'Login'
    assert page.locator('#takMapLoginButton').bounding_box()['width'] < 180
    assert page.locator('#otsMode').bounding_box()['height'] < 45
    page.locator('#username').fill('alice')
    page.locator('#password').fill('secret')
    page.locator('#takMapLoginButton').click()
    page.wait_for_timeout(100)
    assert page.locator('#takMapError').inner_text() == 'Test login rejection'
    reqs = page.evaluate('window.__loginRequests.slice()')
    assert len(reqs) == 1 and 'mode=ots' in reqs[0] and 'username=alice' in reqs[0], reqs
    page.locator('#password').press('Enter')
    page.wait_for_timeout(100)
    reqs = page.evaluate('window.__loginRequests.slice()')
    assert len(reqs) == 2, reqs
    assert not errors, errors
    browser.close()
print('i513 compact login click and Enter-key browser tests passed')
