#!/usr/bin/env python3
from __future__ import annotations
import json, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
JS=(ROOT/'assets'/'tak-map-i635.js').read_text()
STATES={'geofencing':False,'adsb':False,'data_sync':False,'gateway_data':False,'satellite':False,'local_data':True,'id:MixedCaseToggle':False}
BODY='''<div class="panel"><h2>Geofencing <span class="tak-card-header-actions-v491"><input id="takGfMasterV491" type="checkbox" checked></span></h2></div>
<div class="panel"><h2>ADS-B <span class="tak-card-header-actions-v491"><input id="adsbHeaderEnableV476" type="checkbox" checked></span></h2></div>
<div class="panel"><h2>Data Sync <span class="tak-card-header-actions-v491"><input id="dataSyncHeaderEnableV476" type="checkbox" checked></span></h2><div class="panel-body"><div id="dataSyncRows"></div></div></div>
<div class="panel"><h2>Satellite <span class="tak-card-header-actions-v491"><input id="satEnableV409" type="checkbox" checked></span></h2></div>
<div class="panel"><h2>Gateway Data <span class="gateway-master-actions"><input id="gatewayDataMasterV476" type="checkbox" checked></span></h2></div>
<div class="panel"><h2>Local Data <span class="tak-card-header-actions-v491"><input id="localDataHeaderEnableV486" type="checkbox"></span></h2></div>
<div class="panel"><h2>Future Card <span class="tak-card-header-actions-v491"><input id="MixedCaseToggle" type="checkbox" checked></span></h2></div>'''
def main():
 chromium=next((n for n in ('chromium','chromium-browser','google-chrome','google-chrome-stable') if shutil.which(n)),None)
 if not chromium: print('SKIP: Chromium unavailable'); return 0
 from playwright.sync_api import sync_playwright
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,executable_path=shutil.which(chromium),args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
  page=browser.new_page(); errors=[]; page.on('pageerror',lambda e: errors.append(str(e)))
  page.set_content('<!doctype html><html><head></head><body>'+BODY+'</body></html>',wait_until='domcontentloaded')
  page.evaluate("""states=>{const mk=()=>{const m=new Map();return {getItem:k=>m.has(String(k))?m.get(String(k)):null,setItem:(k,v)=>m.set(String(k),String(v)),removeItem:k=>m.delete(String(k)),clear:()=>m.clear()}};Object.defineProperty(window,'localStorage',{configurable:true,value:mk()});Object.defineProperty(window,'sessionStorage',{configurable:true,value:mk()});window.__posts=[];class X{open(method,url,async){this.method=method;this.url=url;this.status=0}send(){this.status=200;this.responseText=JSON.stringify({ok:true,states:states,per_user:true})}}Object.defineProperty(window,'XMLHttpRequest',{configurable:true,value:X});window.fetch=(url,opt={})=>{if(opt.method==='POST')try{window.__posts.push(JSON.parse(opt.body||'{}'))}catch(e){};return Promise.resolve({ok:true,json:()=>Promise.resolve({ok:true,states})})}}""",STATES)
  page.add_script_tag(content=JS); page.wait_for_timeout(200)
  after=page.evaluate("({geofence:sessionStorage.getItem('takmap.geofence.master'),adsb:localStorage.getItem('takmap.adsb.localDisabled'),dataSync:localStorage.getItem('takmap.dataSync.disabled'),gateway:localStorage.getItem('takmap.gatewayData.master'),satellite:JSON.parse(localStorage.getItem('takMapSatellitePrefsV409')||'{}').enabled})")
  assert after=={'geofence':'0','adsb':'1','dataSync':'1','gateway':'0','satellite':False},after
  expected={'takGfMasterV491':False,'adsbHeaderEnableV476':False,'dataSyncHeaderEnableV476':False,'satEnableV409':False,'gatewayDataMasterV476':False,'localDataHeaderEnableV486':True,'MixedCaseToggle':False}
  actual=page.evaluate("Object.fromEntries(%s.map(id=>[id,document.getElementById(id).checked]))"%json.dumps(list(expected)))
  assert actual==expected,(actual,expected)
  page.locator('#MixedCaseToggle').check(); page.wait_for_timeout(100)
  posts=page.evaluate('window.__posts')
  assert any(p.get('key')=='id:MixedCaseToggle' and p.get('enabled') is True for p in posts),posts
  assert not errors,errors; browser.close()
 print('TAK Map i635 card-state seed/hydration + generic mixed-case persistence browser contract passed')
 return 0
if __name__=='__main__': raise SystemExit(main())
