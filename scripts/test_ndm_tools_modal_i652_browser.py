#!/usr/bin/env python3
"""Browser contract for Tools -> NDM Data modal and the i651 JSON/ZIP API."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
HTML='''<!doctype html><html><head><title>TAK Map test</title></head><body><aside id="sidebar">
<div class="panel"><h2>Tools</h2><div class="row"><button id="takMapNDMDataBtnI652" class="layer-button" onclick="openTakMapNDMData()">NDM Data</button></div><div class="row"><button id="localElevAddBtn" onclick="openLocalElevationDialog()">Add Elevation Data</button></div></div>
</aside></body></html>'''
FAKE_API=r"""() => {
  window.__ndmRequests=[];
  window.__ndmState={datasets:[],deny:false};
  const ok=(value,status=200)=>({ok:status>=200&&status<300,status,json:async()=>value});
  window.fetch=async (url,opts={})=>{
    const method=opts.method||'GET'; window.__ndmRequests.push({url:String(url),method,headers:opts.headers,body:opts.body});
    if(url.endsWith('/catalog'))return ok({ok:true,datasets:window.__ndmState.datasets});
    if(url.endsWith('/discover'))return window.__ndmState.deny?ok({ok:false,error:'Administrator required'},403):ok({ok:true,available:[
      {name:'takrig-routing-ut-valhalla-3.6.3.zip',size_bytes:384000000,discovery_id:'ut-id'},
      {name:'takrig-terrain-ut.zip',size_bytes:410000000,discovery_id:'terrain-id'}]});
    if(url.endsWith('/register-existing')){
      if(method!=='POST'||JSON.parse(opts.body||'{}').discovery_id!=='ut-id')throw Error('Bad register contract');
      const item={region:'Utah',type:'routing',owner:'ndm-external',available:true,dataset_id:'a'.repeat(64),zip_size_bytes:384000000};
      window.__ndmState.datasets.push(item);return ok({ok:true,dataset:item,duplicate:false});
    }
    return ok({ok:false,error:'Unknown request'},404);
  };
  window.XMLHttpRequest=class {
    constructor(){this.upload={};this.headers={};this.status=0;this.response=null;this.timeout=0;}
    open(method,url){this.method=method;this.url=url;}
    setRequestHeader(k,v){this.headers[k.toLowerCase()]=v;}
    send(file){
      window.__ndmRequests.push({url:this.url,method:this.method,headers:this.headers,fileName:file.name,size:file.size});
      if(this.method!=='POST'||!this.url.endsWith('/import')||this.headers['content-type']!=='application/zip')throw Error('Bad upload contract');
      this.status=200;
      const item={region:'Utah',type:'terrain',owner:'tak-map',available:true,dataset_id:'b'.repeat(64),zip_size_bytes:file.size};
      window.__ndmState.datasets.push(item);this.response={ok:true,dataset:item,duplicate:false};
      if(this.onload)this.onload();
    }
  };
}"""
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
    page=browser.new_page()
    page.set_content(HTML)
    page.evaluate(FAKE_API)
    page.add_script_tag(path=str(ROOT/'assets/tak-map-ndm-data-i652.js'))
    assert page.locator('#sidebar .panel h2').all_inner_texts()==['Tools']
    assert page.locator('#sidebar .panel').locator('button').all_inner_texts()==['NDM Data','Add Elevation Data']
    assert page.evaluate('window.__ndmRequests.length')==0,'No API request until modal is opened'
    page.locator('#takMapNDMDataBtnI652').click()
    page.wait_for_selector('#takMapNDMModalI652:not([hidden])')
    page.wait_for_function("document.getElementById('takMapNDMExistingRowsI652').textContent.includes('takrig-terrain-ut.zip')")
    assert page.get_by_text('takrig-routing-ut-valhalla-3.6.3.zip').is_visible()
    assert page.locator('#takMapNDMTabUploadI652').is_hidden()
    page.locator('[data-ndm-operation="register"]').first.click()
    page.wait_for_function("document.getElementById('takMapNDMRegisteredRowsI652').textContent.includes('Utah')")
    assert page.evaluate('window.__ndmRequests.some(x=>x.url.includes("register-existing")&&x.method==="POST")')
    page.locator('#takMapNDMSelectUploadI652').click()
    page.wait_for_selector('#takMapNDMTabUploadI652:not([hidden])')
    page.locator('#takMapNDMFileI652').set_input_files({'name':'takrig-terrain-ut.zip','mimeType':'application/zip','buffer':b'PK\x03\x04unit-test-data'})
    page.locator('#takMapNDMUploadI652').click()
    page.wait_for_function("document.getElementById('takMapNDMRegisteredRowsI652').textContent.includes('Elevation')")
    assert page.evaluate('window.__ndmRequests.filter(x=>x.url.includes("/import")&&x.method==="POST").length')==1
    assert not page.evaluate(r'window.__ndmRequests.some(x=>/\/(?:prepare|activate|resolve)/.test(x.url))')
    page.keyboard.press('Escape')
    assert page.locator('#takMapNDMModalI652').is_hidden()
    page.evaluate('window.__ndmState.deny=true')
    page.locator('#takMapNDMDataBtnI652').click()
    page.wait_for_function("document.getElementById('takMapNDMStatusI652').textContent.includes('administrator')")
    assert page.locator('#takMapNDMFileI652').is_disabled()
    assert page.get_by_text('Administrator access is required',exact=False).is_visible()
    page.locator('#takMapNDMCloseI652').click()
    browser.close()
print('PASS: Tools card placement, existing NDM registration, ZIP upload, accessible modal, admin denial, no Valhalla activation')
