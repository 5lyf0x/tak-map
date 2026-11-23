#!/usr/bin/env python3
"""Focused browser contract for restored Cert Setup entry and safe CA operations."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
JS=ROOT/'assets/tak-map-cert-setup-i650.js'
DASHBOARD=(ROOT/'tak_dashboard.py').read_text()
INSTALLER=(ROOT/'install.sh').read_text()
assert 'takMapCertSetupLoaderI650' in DASHBOARD
assert '/api/tak-map/cert-setup/status' in DASHBOARD
assert 'CA_CERT_FILE.is_file()' in DASHBOARD
assert 'Administrator access required.' in DASHBOARD
assert 'Same-origin request required.' in DASHBOARD
assert 'tak-map-cert-setup-i650.js' in INSTALLER
assert 'tak-map-cert-setup-i650.js?install-check=i659' in INSTALLER
HTML='<html><head></head><body><div class="top-actions"><div id="takAccountV511" class="tak-account-v511"><button id="takMapAccountBtnV511">ACCOUNT</button></div></div></body></html>'
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
 page=browser.new_page()
 page.set_content(HTML)
 page.evaluate("""()=>{window.__requests=[];window.fetch=async (url,init={})=>{window.__requests.push([url,init.method||'GET']); if(url.includes('/status'))return {ok:true,status:200,json:async()=>({ok:true,ca_exists:true,server_cert_exists:true,ca_download_url:'/ca-cert.crt',ca_fingerprint_sha256:'AA:BB:CC',ips:['10.10.10.101'],is_admin:true})};return {ok:true,status:200,json:async()=>({ok:true})};};}""")
 page.add_script_tag(path=str(JS))
 page.wait_for_selector('#takMapCertSetupBtnI650')
 assert page.locator('.top-actions').locator('button').all_inner_texts()==['Cert Setup','ACCOUNT']
 assert page.evaluate('window.__requests.length')==0,'UI must not make certificate requests without user action'
 page.locator('#takMapCertSetupBtnI650').click()
 page.wait_for_selector('#takMapCertModalI650.open')
 page.wait_for_function("document.querySelector('#certInfoI650').textContent.includes('AA:BB:CC')")
 assert page.locator('#certDownloadI650').get_attribute('href')=='/ca-cert.crt'
 assert page.locator('#certDownloadI650').get_attribute('aria-disabled') is None
 assert page.locator('#certAdvancedI650').is_visible()
 page.locator('#certAdvancedI650 summary').click()
 assert page.locator('#certGenerateI650').is_disabled()
 page.locator('#certPhraseI650').fill('REGENERATE')
 assert page.locator('#certGenerateI650').is_enabled()
 assert page.evaluate('window.__requests.filter(x=>x[1]==="POST").length')==0
 page.keyboard.press('Escape')
 assert page.locator('#takMapCertModalI650').is_hidden()
 page.locator('#takMapCertSetupBtnI650').click()
 page.wait_for_function("document.querySelector('#certInfoI650').textContent.includes('AA:BB:CC')")
 assert page.locator('#certPhraseI650').input_value()==''
 # Signed-in nonadministrator sees download/status but no generation controls.
 page.evaluate("""()=>{window.fetch=async()=>({ok:true,status:200,json:async()=>({ok:true,ca_exists:true,server_cert_exists:true,ca_download_url:'/ca-cert.crt',is_admin:false})});}""")
 page.locator('#certRefreshI650').click()
 page.wait_for_function('document.querySelector("#certAdvancedI650").hidden===true')
 assert page.locator('#certDownloadI650').get_attribute('aria-disabled') is None
 print('PASS: visible Cert Setup, status, fingerprint, download, admin-only advanced controls, explicit confirmation, Escape closure, no auto-regeneration')
 browser.close()
