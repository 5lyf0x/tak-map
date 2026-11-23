#!/usr/bin/env python3
"""i653 Chromium test: 4 GiB NDM uploads vs unlimited existing registration."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
    page=browser.new_page()
    page.set_content('<!doctype html><html><body><div class="panel"><h2>Tools</h2><button id="takMapNDMDataBtnI652" onclick="openTakMapNDMData()">NDM Data</button></div></body></html>')
    page.evaluate('''() => {
      window.__requests=[]; window.__uploads=[];
      window.fetch=async (url,opts={})=>{
        window.__requests.push({url:String(url),method:opts.method||'GET'});
        const data=String(url).endsWith('/catalog')
          ? {ok:true,datasets:[],max_upload_bytes:4*1024*1024*1024,existing_file_size_limit:null}
          : {ok:true,available:[{name:'takrig-routing-ca-valhalla-3.6.3.zip',size_bytes:5*1024*1024*1024,discovery_id:'large-california'}]};
        return {ok:true,status:200,json:async()=>data};
      };
      window.XMLHttpRequest=class {
        constructor(){this.upload={};this.headers={};this.response=null;this.status=0;this.timeout=-1;}
        open(method,url){this.method=method;this.url=url;}
        setRequestHeader(name,value){this.headers[name.toLowerCase()]=value;}
        send(file){
          window.__uploads.push({size:file.size,name:file.name,timeout:this.timeout,method:this.method,url:this.url});
          this.status=200;
          this.response={ok:true,dataset:{type:'terrain',region:'Utah'},duplicate:false};
          if(this.onload)this.onload();
        }
      };
    }''')
    page.add_script_tag(path=str(ROOT/'assets/tak-map-ndm-data-i652.js'))
    page.locator('#takMapNDMDataBtnI652').click()
    page.wait_for_function("document.getElementById('takMapNDMExistingRowsI652').textContent.includes('takrig-routing-ca')")
    assert page.locator('#takMapNDMExistingRowsI652').inner_text().count('5.00 GiB')==1
    # Existing 5 GiB ZIP is discoverable and not disabled because of the upload limit.
    assert page.locator('[data-ndm-operation="register"]').is_enabled()
    page.locator('#takMapNDMSelectUploadI652').click()
    def fake_file(size):
        page.evaluate('''(size) => {
          const f=new File([new Uint8Array([80,75,3,4])],'california.zip',{type:'application/zip'});
          Object.defineProperty(f,'size',{value:size});
          Object.defineProperty(document.getElementById('takMapNDMFileI652'),'files',{configurable:true,get:()=>[f]});
        }''',size)
    fake_file(3*1024*1024*1024)
    page.locator('#takMapNDMUploadI652').click()
    page.wait_for_function('window.__uploads.length===1')
    assert page.evaluate('window.__uploads[0].size')==3*1024*1024*1024
    assert page.evaluate('window.__uploads[0].timeout')==0
    page.wait_for_function("document.getElementById('takMapNDMStatusI652').textContent.includes('Imported')")
    fake_file(4*1024*1024*1024+1)
    page.locator('#takMapNDMUploadI652').click()
    assert page.evaluate('window.__uploads.length')==1,'over-cap file must be rejected locally'
    assert '4.00 GiB' in page.locator('#takMapNDMStatusI652').inner_text()
    browser.close()
print('PASS: existing 5 GiB NDM ZIP remains registerable, 3 GiB browser ZIP allowed, over-4 GiB rejected, no fixed upload timeout')
