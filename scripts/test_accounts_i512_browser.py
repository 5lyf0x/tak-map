#!/usr/bin/env python3
from __future__ import annotations
import json, re
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/'tak_dashboard.py').read_text(errors='replace')
def extract(name,marker):
    m=re.search(rf"{name}\s*=\s*r'''(<script id=\"{marker}\">.*?</script>)'''",SOURCE,re.S); assert m,marker; return m.group(1)
OTS_UI=extract('_I509_OTS_UI','takMapConfigureOtsV509')
IDENTITY=extract('_I511_IDENTITY_UI','takMapOtsIdentityV511')
ACCOUNTS=extract('_I512_UI','takMapAccountsV512')
SESSION={'ok':True,'version':'i512','username':'alice','callsign':'VIPER 6','selected_callsign':'VIPER 6','suggested_callsign':'SLYFOX','display_identity':'VIPER 6','identity_source':'OpenTAKServer','connection_state':'Authenticated','is_admin':True,'tak_uid':'TAKMAP-USER-11111111-1111-1111-1111-111111111111','must_change_password':False}
USERS={'ok':True,'ots_connected':True,'users':[{'username':'administrator','is_admin':True,'active':True,'must_change_password':False,'callsign':'','tak_uid':'TAKMAP-LOCAL-A'},{'username':'operator1','is_admin':False,'active':True,'must_change_password':True,'callsign':'RAVEN 12','tak_uid':'TAKMAP-LOCAL-B'}]}
CONFIG={'ok':True,'config':{'display_name':'Test OTS','base_url':'https://ots.example','api_url':'https://ots.example','marti_url':'https://ots.example:8443','enrollment_url':'https://ots.example:8446','cot_host':'ots.example','cot_port':8089,'ca_cert_path':'/var/lib/tak-map/ots_trust/ca.crt','verify_tls':True,'enabled':True,'login_enabled':True,'configured_at':'2026-07-21T00:00:00Z'}}
STATUS={'ok':True,'version':'i512','state':'complete','title':'OTS Connection: Complete','message':'ready','checks':{'web_reachable':True,'tls_trusted':True,'hostname_verified':True,'administrator_authenticated':True,'configuration_saved':True,'login_enabled':True}}
def app_html():
    return f'''<!doctype html><html><body><div class="top-actions"><button id="configureOtsBtnV509">Configure OTS</button></div><script>window.__logoutCalled=false;window.logoutTakMap=()=>window.__logoutCalled=true;const S={json.dumps(SESSION)},U={json.dumps(USERS)},C={json.dumps(CONFIG)},T={json.dumps(STATUS)};window.fetch=async(url,opt)=>{{if(url==='/api/tak-map/ots/session')return{{ok:true,status:200,json:async()=>S}};if(url==='/api/tak-map/local-users')return{{ok:true,status:200,json:async()=>U}};if(url==='/api/tak-map/ots/config')return{{ok:true,status:200,json:async()=>C}};if(url==='/api/tak-map/ots/status')return{{ok:true,status:200,json:async()=>T}};if(url==='/api/tak-map/ots/public-status')return{{ok:true,status:200,json:async()=>({{ots_connected:true,enabled:true,login_enabled:true}})}};if(url==='/api/tak-map/account/callsign')return{{ok:true,status:200,json:async()=>({{ok:true,session:S}})}};return{{ok:true,status:200,json:async()=>({{ok:true}})}}}};</script>{OTS_UI}{IDENTITY}{ACCOUNTS}</body></html>'''
def login_html():
    return f'''<!doctype html><html><body><form id="takMapLoginForm"><p class="sub"></p><input id="username"><input id="password" type="password"><button id="takMapLoginButton">Enter TAK Map</button><div id="takMapError"></div></form><script>window.fetch=async(url,opt)=>{{if(url==='/api/tak-map/ots/public-status')return{{ok:true,status:200,json:async()=>({{ots_connected:true,enabled:true,login_enabled:true}})}};return{{ok:true,status:200,json:async()=>({{ok:true}})}}}};</script>{ACCOUNTS}</body></html>'''
def main():
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        p=browser.new_page(); p.set_content(login_html(),wait_until='domcontentloaded'); p.wait_for_timeout(900)
        assert p.get_by_role('button',name='OpenTAKServer Login').count()==1
        assert p.get_by_role('button',name='Local Login').count()==1
        assert p.locator('#otsRecoveryV509').count()==0
        p2=browser.new_page(); p2.set_content(app_html(),wait_until='domcontentloaded'); p2.wait_for_timeout(1800)
        assert p2.locator('#takMapAccountBtnV511').inner_text()=='VIPER 6 ▾'
        p2.locator('#takMapAccountBtnV511').click(); p2.wait_for_timeout(100)
        menu=p2.locator('#takMapAccountMenuV511').inner_text()
        assert 'TAK UID' in menu and 'Change Callsign' in menu and 'Configure OTS' in menu
        p2.locator('#configureV512').click(); p2.wait_for_timeout(900)
        assert p2.locator('#localAccountsV512').count()==1
        text=p2.locator('#localAccountsV512').inner_text()
        assert 'Local Accounts' in text and 'Disconnect OTS' in text and 'operator1' in text
        browser.close()
    print('i512 login, account-menu, and local-account browser tests passed')
if __name__=='__main__': main()
