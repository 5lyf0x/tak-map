#!/usr/bin/env python3
from __future__ import annotations
import json, re
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'tak_dashboard.py').read_text(errors='replace')
m=re.search(r"_I589_CONFIGURE_OTS_UI\s*=\s*r'''(<style id=\"takMapConfigureOtsI589Style\".*?</script>\s*)'''",source,re.S)
assert m,'i589 Configure OTS UI block not found'
UI=m.group(1)
STATUS={'ok':True,'version':'i589','config':{'configured':False,'enabled':False,'login_enabled':False,'data_sync_enabled':False,'automatic_user_certificate_enrollment':False,'automatic_trust_installation':False,'enrollment_manifest':{'status':'not-enrolled'}},'manifest':{'status':'not-enrolled','file_count':0,'managed_tree_count':0,'remote_certificate_count':0}}

def page_html():
    return f'''<!doctype html><html><head></head><body>
<button id="takClientSetupBtn">Configure OTS</button><div id="otsModalV509">legacy</div><div id="otsModalI586">old</div><div id="otsModalI587">old</div>
<script>
window.__mode='marti';window.__requests=[];window.__localRequests=[];
window.confirm=()=>true;window.alert=()=>{{}};window.prompt=()=>null;
const STATUS={json.dumps(STATUS)};
window.fetch=async function(url,opts){{
 if(url==='/api/tak-map/ots/enrollment-status')return {{ok:true,status:200,json:async()=>STATUS}};
 if(url==='/api/tak-map/local-users')return {{ok:true,status:200,json:async()=>({{ok:true,ots_connected:false,users:[]}})}};
 if(url==='/api/tak-map/ots/enroll-auto'){{const sent=JSON.parse(opts.body);window.__requests.push(sent);if(window.__mode==='marti')return {{ok:false,status:422,json:async()=>({{ok:false,needs_input:true,required_fields:['marti_url'],error:'Marti failed'}})}};if(window.__mode==='otp')return {{ok:false,status:422,json:async()=>({{ok:false,needs_input:true,required_fields:['otp'],error:'2FA required'}})}};return {{ok:true,status:200,json:async()=>({{ok:true,message:'Connected',config:{{configured:true,enabled:true,login_enabled:true,data_sync_enabled:true,automatic_trust_installation:true,base_url:'https://ots.example'}},manifest:{{status:'enrolled'}}}})}};}}
 if(url==='/api/tak-map/local-users/q589'){{const sent=JSON.parse(opts.body);window.__localRequests.push(sent);return {{ok:true,status:200,json:async()=>({{ok:true}})}};}}
 if(url==='/api/tak-map/ots/disconnect')return {{ok:true,status:200,json:async()=>({{ok:true,message:'Disconnected'}})}};
 return {{ok:true,status:200,json:async()=>({{ok:true}})}};
}};
</script>{UI}</body></html>'''

def field(page,x): return page.locator(f'#otsModalI589 [data-x="{x}"]')
def unlock_fill(page,x,value):
    n=field(page,x);n.click();assert n.get_attribute('readonly') is None,(x,n.get_attribute('readonly'));n.fill(value)

def main():
  with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage','--no-first-run','--disable-background-networking'])
    page=browser.new_page(viewport={'width':1200,'height':900})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content(page_html(),wait_until='domcontentloaded');page.wait_for_timeout(350)
    for old in ('#otsModalV509','#otsModalI586','#otsModalI587'):assert page.locator(old).count()==0,old
    page.evaluate('TakMapConfigureOtsI589.open()');page.wait_for_timeout(300)
    assert page.locator('#otsModalI589').get_attribute('aria-hidden')=='false'
    body=page.locator('#otsModalI589').inner_text()
    assert 'Connect this TAK Map server' not in body
    assert page.locator('#otsModalI589 [data-l="a04"]').text_content()=='2FA Code (optional)'
    assert 'Disabled OTS login but keeps connection details.' in body
    assert 'Disconnects and completely removes OTS enrollment.' in body
    assert 'OTS Default: https://opentakserver' in body
    assert page.locator('#otsModalI589 [data-w="a04"]').is_hidden()
    assert page.locator('#o589Advanced').is_hidden()
    for x in ('b01','b02','b03','b04'):assert field(page,x).is_checked(),x

    visible_fields=page.locator('#otsModalI589 input[data-nf]')
    assert visible_fields.count()==15,visible_fields.count()
    first_names=[];first_ids=[]
    forbidden=('address','server','host','user','login','admin','password','pass','otp','code','trust','certificate','account','callsign','email','token','secret')
    for i in range(visible_fields.count()):
      n=visible_fields.nth(i);name=n.get_attribute('name') or '';ident=n.get_attribute('id') or ''
      assert name.startswith('q_') and ident.startswith('n_'),(name,ident)
      assert not any(t in name.lower() or t in ident.lower() for t in forbidden),(name,ident)
      first_names.append(name);first_ids.append(ident)
      for k,v in [('autocomplete','off'),('aria-autocomplete','none'),('autocorrect','off'),('autocapitalize','none'),('spellcheck','false'),('data-lpignore','true'),('data-1p-ignore','true'),('data-bwignore','true'),('data-protonpass-ignore','true'),('data-form-type','other')]:assert n.get_attribute(k)==v,(i,k,n.get_attribute(k))
      assert n.get_attribute('readonly') is not None,i
      assert n.get_attribute('aria-labelledby'),i
    assert len(set(first_names))==15 and len(set(first_ids))==15
    for x in ('a03','a04','a11','a15'):
      assert field(page,x).get_attribute('type')=='text'
      assert field(page,x).get_attribute('data-secret') is not None

    # Locked autofill-like events cannot populate visible fields.
    page.evaluate("""() => {for(const x of ['a02','a03']){const n=document.querySelector('[data-x="'+x+'"]');n.value='autofilled';n.dispatchEvent(new Event('input',{bubbles:true}));}}""")
    assert field(page,'a02').input_value()=='' and field(page,'a03').input_value()==''

    # Field titles and check rows use sentence case/compact styling.
    labels=page.locator('#otsModalI589 .field-title')
    texts=[labels.nth(i).inner_text().strip() for i in range(labels.count())]
    assert all(not (any(c.isalpha() for c in t) and t==t.upper()) for t in texts),texts
    title_size=float(page.locator('#otsModalI589 .field-title').first.evaluate("e=>parseFloat(getComputedStyle(e).fontSize)"))
    check_size=float(page.locator('#otsModalI589 .check').first.evaluate("e=>parseFloat(getComputedStyle(e).fontSize)"))
    assert check_size<title_size,(check_size,title_size)
    assert page.locator('#otsModalI589 .check').first.evaluate("e=>getComputedStyle(e).textTransform")=='none'

    unlock_fill(page,'a01','https://ots.example');unlock_fill(page,'a02','admin');unlock_fill(page,'a03','secret-one')
    page.click('#o589Enroll');page.wait_for_timeout(250)
    sent=page.evaluate('window.__requests[0]')
    assert list(sent.keys())==['q'],sent
    assert sent['q'][0:4]==['https://ots.example','admin','secret-one',''],sent
    assert sent['q'][4:9]==[True,True,True,True,True],sent
    assert page.locator('#o589Advanced').is_visible()
    assert page.locator('#otsModalI589 [data-o].required').count()==1
    assert page.locator('#otsModalI589 [data-o].required').get_attribute('data-o')=='marti_url'
    for x in ('a03','a04','a11'):
      assert field(page,x).input_value()=='' and field(page,x).get_attribute('readonly') is not None,x

    # OTP appears only after the server requests it and retains the approved optional label.
    unlock_fill(page,'a03','secret-two');page.evaluate("window.__mode='otp'");page.click('#o589Enroll');page.wait_for_timeout(250)
    assert page.locator('#otsModalI589 [data-w="a04"]').is_visible()
    assert page.locator('#otsModalI589 [data-l="a04"]').inner_text()=='2FA Code (optional)'
    assert list(page.evaluate('window.__requests[1]').keys())==['q']

    # Local-account request is opaque too.
    page.locator('#otsModalI589 details summary').click();unlock_fill(page,'a13','local-user');unlock_fill(page,'a14','LOCAL');unlock_fill(page,'a15','temporary-password')
    page.click('#o589CreateLocal');page.wait_for_timeout(200)
    local=page.evaluate('window.__localRequests[0]');assert list(local.keys())==['q'] and local['q']==['create','local-user','LOCAL','temporary-password'],local

    # Closing clears credentials, preserves TAK Map-owned address, and opening randomizes IDs/names again.
    page.evaluate('TakMapConfigureOtsI589.close()')
    assert field(page,'a01').input_value()=='https://ots.example'
    for x in ('a02','a03','a04','a11','a13','a14','a15'):assert field(page,x).input_value()=='',x
    page.evaluate('TakMapConfigureOtsI589.open()');page.wait_for_timeout(120)
    second_names=[visible_fields.nth(i).get_attribute('name') for i in range(visible_fields.count())]
    second_ids=[visible_fields.nth(i).get_attribute('id') for i in range(visible_fields.count())]
    assert second_names!=first_names and second_ids!=first_ids
    assert errors==[],errors
    assert page.evaluate('TakMapConfigureOtsI589.version')=='i589'
    browser.close()
  print('i589 Configure OTS opaque field identity, opaque request transport, modal styling, progressive 2FA, secret clearing, and autofill suppression browser tests passed')

if __name__=='__main__':main()
