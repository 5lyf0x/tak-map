#!/usr/bin/env python3
from __future__ import annotations
import re
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/'tak_dashboard.py').read_text(errors='replace')
m=re.search(r"_I509_OTS_UI\s*=r'''(<script id=\"takMapConfigureOtsV509\">.*?</script>)'''",SOURCE,re.S)
assert m, 'Configure OTS UI patch not found'
PATCH=m.group(1)

def main():
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        page=browser.new_page()
        page.on('dialog',lambda dialog: dialog.accept())
        html=f'''<!doctype html><html><head></head><body>
        <button id="takClientSetupBtn">TAK Client</button><div id="takClientReminder"></div>
        <script>
        window.openTakClientSetup=function(){{}};
        const partial={{ok:false,version:'i510',primary_problem:'Web/API TLS validation failed: unable to get local issuer certificate',summary:{{web_reachable:false,strict_web_tls:false,hostname_match:true,cot_tls_reachable:true,enrollment_available:true}},certificate:{{ok:true,strict_tls_error:'unable to get local issuer certificate'}},cot_tls:{{ok:true}},capabilities:{{truststore:'available',oauth_token:'available-auth-or-method-required',groups:'available-auth-or-method-required',missions:'available-auth-or-method-required',marti_contacts:'available-auth-or-method-required'}},detected_ots_version:'1.7.test'}};
        const complete={{ok:true,version:'i510',primary_problem:'',summary:{{web_reachable:true,strict_web_tls:true,hostname_match:true,cot_tls_reachable:true,enrollment_available:true}},certificate:{{ok:true,strict_tls_ok:true}},cot_tls:{{ok:true,strict_tls_ok:true}},capabilities:{{truststore:'available',oauth_token:'available-auth-or-method-required',groups:'available-auth-or-method-required',missions:'available-auth-or-method-required',marti_contacts:'available-auth-or-method-required'}},detected_ots_version:'1.7.test'}};
        window.fetch=async function(url,opts){{
          if(url==='/api/tak-map/ots/session')return {{ok:true,status:200,json:async()=>({{ok:true,is_admin:true}})}};
          if(url==='/api/tak-map/ots/config')return {{ok:true,status:200,json:async()=>({{ok:true,config:{{display_name:'Test OTS',base_url:'https://opentakserver',api_url:'https://opentakserver',marti_url:'https://opentakserver:8443',enrollment_url:'https://opentakserver:8446',cot_host:'opentakserver',cot_port:8089,verify_tls:true,enabled:false,login_enabled:false,last_discovery:{{}}}}}})}};
          if(url==='/api/tak-map/ots/discover')return {{ok:true,status:200,json:async()=>partial}};
          if(url==='/api/tak-map/ots/install-truststore')return {{ok:true,status:200,json:async()=>({{ok:true,message:'OpenTAKServer public CA chain installed and strict discovery reran automatically.',path:'/var/lib/tak-map/ots_trust/opentakserver-ca-chain.crt',certificates:1,extraction:{{mode:'pkcs12-legacy',used_legacy:true}},certificate_identities:[{{subject:{{commonName:'OpenTAKServer-CA'}},is_ca:true}}],discovery:complete,config:{{display_name:'Test OTS',base_url:'https://opentakserver',api_url:'https://opentakserver',marti_url:'https://opentakserver:8443',enrollment_url:'https://opentakserver:8446',cot_host:'opentakserver',cot_port:8089,ca_cert_path:'/var/lib/tak-map/ots_trust/opentakserver-ca-chain.crt',verify_tls:true,enabled:false,login_enabled:false}}}})}};
          return {{ok:true,status:200,json:async()=>({{ok:true}})}};
        }};
        </script>{PATCH}</body></html>'''
        page.set_content(html,wait_until='domcontentloaded'); page.wait_for_timeout(700)
        page.locator('#takClientSetupBtn').click(); page.wait_for_timeout(100)
        page.locator('#otsDiscoverV509').click(); page.wait_for_timeout(120)
        text=page.locator('#otsOutputV509').inner_text()
        status=page.locator('#otsStatusV509').inner_text()
        assert 'Discovery incomplete:' in text, text
        assert 'unable to get local issuer certificate' in text, text
        assert 'HTTP 200' not in text, text
        assert 'Primary issue' in status and 'TLS validation failed' in status, status
        page.locator('#otsTrustPassV509').fill('atakatak')
        page.locator('#otsTrustV509').click(); page.wait_for_timeout(150)
        text=page.locator('#otsOutputV509').inner_text()
        status=page.locator('#otsStatusV509').inner_text()
        assert 'pkcs12-legacy' in text, text
        assert 'Strict discovery: complete' in text, text
        assert 'Certificates installed: 1' in text, text
        assert 'TLS validation' in status and 'Valid' in status, status
        assert 'Primary issue' not in status, status
        assert page.locator('#otsTrustPassV509').input_value()==''
        browser.close()
    print('i510 Configure OTS browser correction tests passed')
if __name__=='__main__': main()
