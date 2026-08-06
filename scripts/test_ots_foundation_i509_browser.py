#!/usr/bin/env python3
from __future__ import annotations
import re
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/'tak_dashboard.py').read_text(errors='replace')

def extract(name, marker):
    m=re.search(rf"{name}\s*=r'''(<script id=\"{marker}\">.*?</script>)'''",SOURCE,re.S)
    assert m, marker
    return m.group(1)
MAP_PATCH=extract('_I509_OTS_UI','takMapConfigureOtsV509')
LOGIN_PATCH=extract('_I509_LOGIN_UI','takMapOtsLoginV509')

def main():
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        page=browser.new_page()
        map_html=f'''<!doctype html><html><head></head><body>
        <div class="top-actions"><button id="takClientSetupBtn">TAK Client</button></div>
        <div id="takClientReminder" class="active"></div><div id="takClientModal"></div>
        <script>
        window.openTakClientSetup=function(){{window.__legacyOpened=true}};
        window.fetch=async function(url,opts){{
          if(url==='/api/tak-map/ots/session')return {{ok:true,json:async()=>({{ok:true,is_admin:true}})}};
          if(url==='/api/tak-map/ots/config')return {{ok:true,json:async()=>({{ok:true,config:{{display_name:'Test OTS',base_url:'https://ots.example',api_url:'https://ots.example',marti_url:'https://ots.example:8443',enrollment_url:'https://ots.example:8446',cot_host:'ots.example',cot_port:8089,verify_tls:true,enabled:false,login_enabled:false,last_discovery:{{}}}}}})}};
          if(url==='/api/tak-map/ots/discover')return {{ok:true,json:async()=>({{ok:true,summary:{{web_reachable:true,strict_web_tls:true,hostname_match:true,cot_tls_reachable:true,enrollment_available:true}},certificate:{{}},cot_tls:{{}},capabilities:{{oauth_token:'available-auth-or-method-required',groups:'available-auth-or-method-required',missions:'available-auth-or-method-required',marti_contacts:'available-auth-or-method-required'}},detected_ots_version:'1.7.test'}})}};
          return {{ok:true,json:async()=>({{ok:true}})}};
        }};
        </script>{MAP_PATCH}</body></html>'''
        page.set_content(map_html,wait_until='domcontentloaded')
        page.wait_for_timeout(900)
        assert page.locator('#takClientSetupBtn').inner_text()=='Configure OTS'
        page.locator('#takClientSetupBtn').click()
        page.wait_for_timeout(150)
        assert 'active' in (page.locator('#otsModalV509').get_attribute('class') or '')
        assert page.locator('#otsDisplayV509').input_value()=='Test OTS'
        assert page.locator('#otsTrustPassV509').count()==1
        page.locator('#otsDiscoverV509').click(); page.wait_for_timeout(100)
        assert 'Reachable' in page.locator('#otsStatusV509').inner_text()
        page.locator('.ots-advanced-v509').evaluate('(e)=>e.open=true'); page.locator('#otsLegacyClientV509').click(); page.wait_for_timeout(50)
        assert page.evaluate('window.__legacyOpened===true')

        login=browser.new_page()
        login_html=f'''<!doctype html><html><head></head><body><form id="takMapLoginForm"><p class="sub">OpenTAKServer admin login required</p><label>Username<input id="username"></label><label>Password<input id="password" type="password"></label><button id="takMapLoginButton" type="submit">Enter TAK Map</button><div id="takMapError"></div></form><script>window.fetch=async function(url,opts){{if(url==='/api/tak-map/ots/public-status')return {{ok:true,json:async()=>({{ok:true,enabled:true,login_enabled:true,display_name:'Test OTS'}})}};return {{ok:false,json:async()=>({{ok:false,error:'stop'}})}}}};</script>{LOGIN_PATCH}</body></html>'''
        login.set_content(login_html,wait_until='domcontentloaded'); login.wait_for_timeout(150)
        assert login.locator('.sub').inner_text()=='Sign in with your OpenTAKServer account'
        assert login.locator('#otsRecoveryV509').inner_text()=='Local Recovery Login'
        assert 'Test OTS' in login.locator('#otsLoginStateV509').inner_text()
        assert login.locator('#otsOtpLabelV509').is_visible()
        login.locator('#otsRecoveryV509').click()
        assert 'Local recovery' in login.locator('.sub').inner_text()
        assert not login.locator('#otsOtpLabelV509').is_visible()
        browser.close()
    print('i509 Configure OTS Chromium tests passed')
if __name__=='__main__': main()
