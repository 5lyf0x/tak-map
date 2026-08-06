#!/usr/bin/env python3
from __future__ import annotations
import runpy
from playwright.sync_api import sync_playwright

ns = runpy.run_path('tak_dashboard.py', run_name='tak_map_password_change_i517_browser_source')
html = ns['_i512_password_page']()
stub = r'''<script>
window.__passwordRequests=[];
window.fetch=async function(url,opt){
  window.__passwordRequests.push({url:String(url),body:String(opt&&opt.body||'')});
  return {ok:false,status:400,json:async()=>({ok:false,error:'Test password rejection'})};
};
</script>'''
html = html.replace('</head>', stub + '</head>', 1)

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    page = browser.new_page(viewport={'width': 900, 'height': 700})
    errors=[]
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.set_content(html, wait_until='domcontentloaded')
    assert page.locator('#confirm').count() == 0
    assert page.locator('#currentPassword').count() == 1
    assert page.locator('#newPassword').get_attribute('minlength') == '8'
    assert page.locator('#confirmPassword').get_attribute('minlength') == '8'
    page.locator('#currentPassword').fill('password')
    page.locator('#newPassword').fill('Eight888')
    page.locator('#confirmPassword').fill('Eight888')
    page.locator('#changePasswordButton').click()
    page.wait_for_timeout(100)
    reqs = page.evaluate('window.__passwordRequests.slice()')
    assert len(reqs) == 1, reqs
    assert '"new_password":"Eight888"' in reqs[0]['body'], reqs
    assert '"confirm_password":"Eight888"' in reqs[0]['body'], reqs
    assert page.locator('#passwordChangeStatus').inner_text() == 'Test password rejection'
    page.locator('#newPassword').fill('Different8')
    page.locator('#confirmPassword').fill('Mismatch8')
    page.locator('#changePasswordButton').click()
    page.wait_for_timeout(50)
    assert len(page.evaluate('window.__passwordRequests.slice()')) == 1
    # Reopen with a successful response and verify visible acknowledgement before navigation.
    success_html = ns['_i512_password_page']().replace('</head>', r'''<script>
window.fetch=async function(){return {ok:true,status:200,json:async()=>({ok:true,message:'Password changed successfully. Opening TAK Map…'})};};
</script>''' + '</head>', 1)
    page.set_content(success_html, wait_until='domcontentloaded')
    page.locator('#currentPassword').fill('password')
    page.locator('#newPassword').fill('Eight888')
    page.locator('#confirmPassword').fill('Eight888')
    page.locator('#changePasswordButton').click()
    page.wait_for_timeout(100)
    assert 'Password changed successfully' in page.locator('#passwordChangeStatus').inner_text()
    assert page.locator('#passwordChangeStatus').get_attribute('class') == 'success'
    assert page.locator('#changePasswordButton').inner_text() == 'Password Changed'
    assert not errors, errors
    browser.close()
print('i517 local password-change browser collision, 8-character policy, and status tests passed')
