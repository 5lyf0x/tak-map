#!/usr/bin/env python3
from __future__ import annotations
import json
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'tak_dashboard.py').read_text(errors='replace')
m = re.search(r"_I587_CONFIGURE_OTS_UI\s*=\s*r'''(<style id=\"takMapConfigureOtsI587Style\".*?</script>)'''", SOURCE, re.S)
assert m, 'i587 Configure OTS UI block not found'
UI = m.group(1)

STATUS = {
    'ok': True, 'version': 'i587',
    'config': {'configured': False, 'enabled': True, 'login_enabled': True, 'data_sync_enabled': True,
               'automatic_trust_installation': True, 'enrollment_manifest': {'status': 'not-enrolled'}},
    'manifest': {'status': 'not-enrolled', 'file_count': 0, 'managed_tree_count': 0, 'remote_certificate_count': 0}
}


def html():
    return f'''<!doctype html><html><head></head><body>
    <button id="takClientSetupBtn">Configure OTS</button><div id="otsModalV509">legacy</div><div id="otsModalI586">old i586</div>
    <script>
    window.__mode='status'; window.__requests=[];
    window.confirm=()=>true; window.alert=()=>{{}}; window.prompt=()=>null;
    const STATUS={json.dumps(STATUS)};
    window.fetch=async function(url,opts){{
      if(url==='/api/tak-map/ots/enrollment-status')return {{ok:true,status:200,json:async()=>STATUS}};
      if(url==='/api/tak-map/local-users')return {{ok:true,status:200,json:async()=>({{ok:true,ots_connected:false,users:[]}})}};
      if(url==='/api/tak-map/ots/enroll-auto'){{
        const sent=JSON.parse(opts.body); window.__requests.push(sent);
        if(window.__mode==='marti')return {{ok:false,status:400,json:async()=>({{ok:false,needs_input:true,required_fields:['marti_url'],error:'Marti failed'}})}};
        if(window.__mode==='otp')return {{ok:false,status:400,json:async()=>({{ok:false,needs_input:true,required_fields:['otp'],error:'2FA required'}})}};
        return {{ok:true,status:200,json:async()=>({{ok:true,message:'Connected',config:{{configured:true,enabled:true,login_enabled:true,data_sync_enabled:true,automatic_trust_installation:true,base_url:'https://ots.example'}},manifest:{{status:'enrolled'}}}})}};
      }}
      if(url==='/api/tak-map/ots/disconnect')return {{ok:true,status:200,json:async()=>({{ok:true,message:'Disconnected',helper_text:'Disabled OTS login but keeps connection details.'}})}};
      if(url==='/api/tak-map/local-users/manage')return {{ok:true,status:200,json:async()=>({{ok:true}})}};
      return {{ok:true,status:200,json:async()=>({{ok:true}})}};
    }};
    </script>{UI}</body></html>'''


def unlock_and_fill(page, selector: str, value: str):
    page.locator(selector).click()
    assert page.locator(selector).get_attribute('readonly') is None, selector
    page.locator(selector).fill(value)


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        page = browser.new_page()
        errors=[]
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.set_content(html(), wait_until='domcontentloaded')
        page.wait_for_timeout(500)
        assert page.locator('#otsModalV509').count() == 0
        assert page.locator('#otsModalI586').count() == 0
        page.evaluate('TakMapConfigureOtsI587.open()')
        page.wait_for_timeout(250)
        assert 'active' in (page.locator('#otsModalI587').get_attribute('class') or '')
        assert page.locator('#ots587Advanced').is_hidden()
        assert page.locator('#ots587OtpWrap').is_hidden()
        for selector in ('#ots587Enable','#ots587Login','#ots587DataSync','#ots587Trust'):
            assert page.locator(selector).is_checked(), selector
        body=page.locator('#otsModalI587').inner_text()
        assert 'Disabled OTS login but keeps connection details.' in body
        assert 'Disconnects and completely removes OTS enrollment.' in body

        # Every non-checkbox field receives layered browser/password-manager suppression.
        fields=page.locator('#otsModalI587 input:not([type="checkbox"])')
        assert fields.count()==15
        names=[]
        for i in range(fields.count()):
            field=fields.nth(i)
            assert field.get_attribute('autocomplete')=='off'
            assert field.get_attribute('aria-autocomplete')=='none'
            assert field.get_attribute('autocorrect')=='off'
            assert field.get_attribute('autocapitalize')=='none'
            assert field.get_attribute('spellcheck')=='false'
            assert field.get_attribute('data-lpignore')=='true'
            assert field.get_attribute('data-1p-ignore')=='true'
            assert field.get_attribute('data-bwignore')=='true'
            assert field.get_attribute('data-protonpass-ignore')=='true'
            assert field.get_attribute('data-form-type')=='other'
            assert field.get_attribute('readonly') is not None
            name=field.get_attribute('name') or ''
            assert name.startswith('takmap_i587_field_'), name
            assert not any(term in name.lower() for term in ('user','login','email','password','otp','token','secret'))
            names.append(name)
        assert len(set(names))==len(names)
        for selector in ('#ots587Pass','#ots587TrustPass','#ots587LocalPassword'):
            assert page.locator(selector).get_attribute('type')=='text'

        # Autofill-like input while locked is rejected.
        page.evaluate("""() => {
          const n=document.getElementById('ots587User');
          n.value='browser-filled-user';
          n.dispatchEvent(new Event('input',{bubbles:true}));
          const p=document.getElementById('ots587Pass');
          p.value='browser-filled-password';
          p.dispatchEvent(new Event('input',{bubbles:true}));
        }""")
        assert page.locator('#ots587User').input_value()==''
        assert page.locator('#ots587Pass').input_value()==''

        # Deliberate interaction unlocks a field; repeated hardening does not interrupt typing.
        unlock_and_fill(page,'#ots587Address','https://ots.example')
        unlock_and_fill(page,'#ots587User','admin')
        unlock_and_fill(page,'#ots587Pass','secret-one')
        assert page.locator('#ots587Pass').get_attribute('type')=='password'
        page.evaluate('TakMapConfigureOtsI587.prepareNoAutofill()')
        assert page.locator('#ots587User').input_value()=='admin'
        assert page.locator('#ots587User').get_attribute('readonly') is None
        assert page.locator('#ots587Pass').input_value()=='secret-one'
        assert page.locator('#ots587Pass').get_attribute('readonly') is None

        # Standard flow shows only the failed Marti override, and request secrets are cleared afterward.
        page.evaluate("window.__mode='marti'")
        page.click('#ots587EnrollBtn'); page.wait_for_timeout(250)
        assert page.locator('#ots587Advanced').is_visible()
        required=page.locator('#otsModalI587 [data-override].required')
        assert required.count()==1
        assert required.first.get_attribute('data-override')=='marti_url'
        assert page.locator('#ots587OtpWrap').is_hidden()
        sent=page.evaluate('window.__requests[0]')
        assert sent['server_address']=='https://ots.example'
        assert sent['username']=='admin' and sent['password']=='secret-one'
        assert sent['enabled'] and sent['login_enabled'] and sent['data_sync_enabled']
        assert sent['automatic_user_certificate_enrollment'] and sent['automatic_trust_installation']
        for selector in ('#ots587Pass','#ots587Otp','#ots587TrustPass'):
            assert page.locator(selector).input_value()==''
            assert page.locator(selector).get_attribute('readonly') is not None
        assert page.locator('#ots587Pass').get_attribute('type')=='text'

        # 2FA appears only after the server asks for it; password must be deliberately re-entered.
        unlock_and_fill(page,'#ots587Pass','secret-two')
        page.evaluate("window.__mode='otp'")
        page.click('#ots587EnrollBtn'); page.wait_for_timeout(250)
        assert page.locator('#ots587OtpWrap').is_visible()
        second=page.evaluate('window.__requests[1]')
        assert second['password']=='secret-two' and second['otp']==''
        assert page.locator('#ots587Pass').input_value()==''

        # A completed enrollment clears password, OTP, and truststore password.
        unlock_and_fill(page,'#ots587Pass','secret-three')
        unlock_and_fill(page,'#ots587Otp','123456')
        page.evaluate("document.querySelector('[data-override=truststore_password]').classList.add('required'); document.getElementById('ots587Advanced').classList.add('active')")
        unlock_and_fill(page,'#ots587TrustPass','trust-secret')
        page.evaluate("window.__mode='success'")
        page.click('#ots587EnrollBtn'); page.wait_for_timeout(250)
        third=page.evaluate('window.__requests[2]')
        assert third['password']=='secret-three' and third['otp']=='123456' and third['truststore_password']=='trust-secret'
        for selector in ('#ots587Pass','#ots587Otp','#ots587TrustPass'):
            assert page.locator(selector).input_value()==''
            assert page.locator(selector).get_attribute('readonly') is not None

        # Closing clears credential/local-account values but preserves the TAK Map-owned server address.
        unlock_and_fill(page,'#ots587User','admin-close')
        page.locator('#otsModalI587 details summary').click()
        unlock_and_fill(page,'#ots587LocalUser','local-user')
        unlock_and_fill(page,'#ots587LocalCallsign','LOCAL')
        unlock_and_fill(page,'#ots587LocalPassword','temporary-password')
        page.evaluate('TakMapConfigureOtsI587.close()')
        assert page.locator('#ots587Address').input_value()=='https://ots.example'
        for selector in ('#ots587User','#ots587Pass','#ots587Otp','#ots587TrustPass','#ots587LocalUser','#ots587LocalCallsign','#ots587LocalPassword'):
            assert page.locator(selector).input_value()==''
            assert page.locator(selector).get_attribute('readonly') is not None

        assert errors == [], errors
        assert page.evaluate('TakMapConfigureOtsI587.version')=='i587'
        browser.close()
    print('i587 Configure OTS progressive discovery, full defaults, layered autofill suppression, deliberate unlock, and credential clearing browser tests passed')


if __name__=='__main__':
    main()
