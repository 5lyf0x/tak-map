#!/usr/bin/env python3
from __future__ import annotations
import re
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/'tak_dashboard.py').read_text(errors='replace')

def extract(name, marker):
    m=re.search(rf"{name}\s*=\s*r'''(<script id=\"{marker}\">.*?</script>)'''",SOURCE,re.S)
    assert m, marker
    return m.group(1)

OLD=extract('_I509_OTS_UI','takMapConfigureOtsV509')
NEW=extract('_I511_IDENTITY_UI','takMapOtsIdentityV511')

CONFIG={
    'display_name':'Test OTS','base_url':'https://ots.example','api_url':'https://ots.example',
    'marti_url':'https://ots.example:8443','enrollment_url':'https://ots.example:8446',
    'cot_host':'ots.example','cot_port':8089,'ca_cert_path':'/var/lib/tak-map/ots_trust/ca.crt',
    'verify_tls':True,'enabled':True,'login_enabled':True,'configured_at':'2026-07-21T13:00:00Z',
    'last_discovery':{'summary':{'web_reachable':True,'strict_web_tls':True,'hostname_match':True,'cot_tls_reachable':True,'enrollment_available':True}}
}
STATUS={'ok':True,'version':'i511','state':'complete','title':'OTS Connection: Complete','message':'OpenTAKServer has been successfully configured. TAK Map is ready for end-user sign-in.','checks':{'web_reachable':True,'tls_trusted':True,'hostname_verified':True,'administrator_authenticated':True,'configuration_saved':True,'login_enabled':True}}
SESSION={'ok':True,'version':'i511','username':'alice','callsign':'SLYFOX','display_identity':'SLYFOX','identity_source':'OpenTAKServer','connection_state':'Authenticated','is_admin':True,'team':'Cyan','team_role':'Team Lead'}

def html(session):
    import json
    return f'''<!doctype html><html><head></head><body>
    <div class="top-actions"><button onclick="window.open('/ca-cert.crt')">Cert Setup</button><button id="takClientSetupBtn">TAK Client</button><button onclick="logoutTakMap()">Map Logout</button></div>
    <div id="takClientReminder" class="active"></div><div id="takClientModal"></div>
    <script>
    window.__logoutCalled=false; window.logoutTakMap=function(){{window.__logoutCalled=true}};
    window.openTakClientSetup=function(){{window.__legacyOpened=true}};
    const CONFIG={json.dumps(CONFIG)}; const STATUS={json.dumps(STATUS)}; const SESSION={json.dumps(session)};
    window.fetch=async function(url,opts){{
      if(url==='/api/tak-map/ots/session')return {{ok:true,status:200,json:async()=>SESSION}};
      if(url==='/api/tak-map/ots/config')return {{ok:true,status:200,json:async()=>({{ok:true,config:CONFIG}})}};
      if(url==='/api/tak-map/ots/status')return {{ok:true,status:200,json:async()=>STATUS}};
      if(url==='/api/tak-map/ots/discover')return {{ok:true,status:200,json:async()=>({{ok:true,version:'i511',summary:{{web_reachable:true,strict_web_tls:true,hostname_match:true,cot_tls_reachable:true,enrollment_available:true}},certificate:{{}},cot_tls:{{}},capabilities:{{}},detected_ots_version:'test'}})}};
      return {{ok:true,status:200,json:async()=>({{ok:true,config:CONFIG,message:'Saved'}})}};
    }};
    </script>{OLD}{NEW}</body></html>'''

def main():
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        page=browser.new_page()
        page.set_content(html(SESSION),wait_until='domcontentloaded'); page.wait_for_timeout(1200)
        assert page.locator('#takMapAccountBtnV511').inner_text()=='SLYFOX ▾'
        assert page.locator('#takClientSetupBtn').is_hidden()
        assert page.get_by_text('Cert Setup',exact=True).is_hidden()
        assert page.get_by_text('Map Logout',exact=True).is_hidden()
        page.locator('#takMapAccountBtnV511').click()
        assert 'open' in (page.locator('#takMapAccountMenuV511').get_attribute('class') or '')
        menu=page.locator('#takMapAccountMenuV511').inner_text()
        assert 'alice' in menu and 'OpenTAKServer' in menu and 'Authenticated' in menu
        assert page.locator('#takAccountConfigureV511').count()==1
        page.locator('#takAccountConfigureV511').click(); page.wait_for_timeout(1000)
        assert 'active' in (page.locator('#otsModalV509').get_attribute('class') or '')
        assert page.locator('#otsAuthV509').inner_text()=='Validate Administrator'
        assert page.locator('#otsLegacyClientV509').count()==0
        assert page.locator('.ots-advanced-v509').count()==0
        assert page.locator('#otsServiceIdentityNoteV511').count()==1
        primary=page.locator('#otsPrimaryStatusV511').inner_text()
        assert 'OTS Connection: Complete' in primary, primary
        for text in ('OpenTAKServer reachable','TLS trusted','Hostname verified','Administrator authentication successful','Configuration saved','End-user login enabled'):
            assert text in primary, (text,primary)
        assert page.locator('#otsTechnicalV511').count()==1
        page.locator('#otsTechnicalV511').evaluate('(e)=>e.open=true')
        assert page.locator('#otsOutputV509').count()==1
        page.locator('#otsCloseV509').click(); page.wait_for_timeout(80)
        page.locator('#takMapAccountBtnV511').click(); page.locator('#takAccountLogoutV511').click()
        assert page.evaluate('window.__logoutCalled===true')

        nonadmin=browser.new_page()
        normal=dict(SESSION); normal.update({'callsign':'','display_identity':'bob','username':'bob','is_admin':False,'team':'','team_role':''})
        nonadmin.set_content(html(normal),wait_until='domcontentloaded'); nonadmin.wait_for_timeout(1000)
        assert nonadmin.locator('#takMapAccountBtnV511').inner_text()=='bob ▾'
        nonadmin.locator('#takMapAccountBtnV511').click()
        assert nonadmin.locator('#takAccountConfigureV511').count()==0
        assert nonadmin.locator('#takAccountLogoutV511').count()==1
        browser.close()
    print('i511 OTS identity browser tests passed')
if __name__=='__main__': main()
