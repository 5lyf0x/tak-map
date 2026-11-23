from pathlib import Path
import json
from playwright.sync_api import sync_playwright
fragment=(Path(__file__).resolve().parents[1]/'assets/tak-map-token-mesh-i664.html').read_text(encoding='utf8')
page_html='<!doctype html><html><head><meta charset="UTF-8"><title>i664 browser check</title><style>body{background:#08111a;color:#edf4f8;font:14px Arial,sans-serif;margin:0;padding:15px}.panel{border:1px solid #354957;border-radius:15px}</style></head><body><aside id="sidebar" style="width:362px">'+fragment+'</aside></body></html>'
model={'ok':True,'enrolled':False,'meshEnabled':True,'name':'','authenticatedPeers':0,'journalOperations':0,'missionBindings':[],'transportReady':False,'lastSuccessfulSync':None}
called=[];errors=[]
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
 context=b.new_context(viewport={'width':480,'height':900},device_scale_factor=1)
 page=context.new_page()
 page.on('pageerror',lambda e:errors.append(str(e)))
 def route(req):
  url=req.request.url
  if url.startswith('https://fonts.googleapis.com') or url.startswith('https://fonts.gstatic.com'):req.fulfill(status=200,content_type='text/css',body='')
  elif '/api/tak-map/mesh/status' in url:req.fulfill(status=200,content_type='application/json',body=json.dumps(model))
  elif '/api/tak-map/mesh/' in url:
   method=url.rsplit('/',1)[-1];data=req.request.post_data_json if req.request.post_data else None;called.append((method,data))
   if method=='control':model['meshEnabled']=data['enabled']
   req.fulfill(status=200,content_type='application/json',body=json.dumps({'ok':True,'meshEnabled':model['meshEnabled']}))
  else:req.fulfill(status=200,content_type='text/html',body=page_html)
 page.evaluate("""window.__model = %s; window.__called = []; window.fetch = async function(path,opts){
    if(String(path).includes('/mesh/status'))return {ok:true,json:async()=>window.__model};
    const method=String(path).split('/').pop(), data=opts&&opts.body?JSON.parse(opts.body):null;
    window.__called.push([method,data]);
    if(method==='control') window.__model.meshEnabled=data.enabled;
    return {ok:true,json:async()=>({ok:true,meshEnabled:window.__model.meshEnabled})};
 };""" % json.dumps(model))
 page.set_content(page_html,wait_until='domcontentloaded')
 page.wait_for_timeout(500)
 assert page.locator('#tokenMeshCardI660').count()==1
 header=page.locator('#meshHeaderI663');chip=page.locator('#tokenMeshStateI660');sw=page.locator('#meshSwitchI662');arr=page.locator('#meshCollapseI663')
 assert header.locator('.ms-title').inner_text()=='MESH SYNC'
 assert header.locator('#tokenMeshStateI660').count()==1
 assert header.locator('#meshSwitchI662').count()==1
 assert header.locator('#meshCollapseI663').count()==1
 coords=[header.locator('.ms-title').bounding_box(),chip.bounding_box(),sw.bounding_box(),arr.bounding_box()]
 assert all(q for q in coords),coords
 assert coords[0]['x']<coords[1]['x']<coords[2]['x']<coords[3]['x'],coords
 assert len({round(q['y']/5) for q in coords})<=2,coords
 assert coords[3]['x']+coords[3]['width']<=header.bounding_box()['x']+header.bounding_box()['width']+1
 assert page.locator('.ms-chip').inner_text()=='NOT ENROLLED'
 assert chip.evaluate('(e)=>getComputedStyle(e,"::before").content')=='none'
 assert sw.evaluate('(e)=>getComputedStyle(e).width')=='38px'
 assert sw.evaluate('(e)=>getComputedStyle(e).height')=='20px'
 assert page.locator('#meshMissionCreateI662').is_disabled()
 assert page.locator('#meshBodyI663').is_visible()
 page.screenshot(path='/mnt/data/_i664_browser_open.png',full_page=True)
 page.evaluate('window.__called=[]')
 arr.click();page.wait_for_timeout(80)
 assert not page.locator('#meshBodyI663').is_visible()
 assert arr.get_attribute('aria-expanded')=='false'
 assert sw.is_visible() and chip.is_visible()
 assert not page.evaluate('window.__called'),page.evaluate('window.__called')
 # Switch while collapsed, must keep collapse state and call backend exactly once.
 sw.click();page.wait_for_timeout(200)
 assert page.evaluate('window.__called')==[['control',{'enabled':False}]],page.evaluate('window.__called')
 assert not page.locator('#meshBodyI663').is_visible()
 arr.click();page.wait_for_timeout(80)
 assert page.locator('#meshBodyI663').is_visible()
 assert arr.get_attribute('aria-expanded')=='true'
 sw.click();page.wait_for_timeout(200)
 assert page.evaluate('window.__called')[-1]==['control',{'enabled':True}]
 page.evaluate("Object.assign(window.__model, {enrolled:true,name:'FIELD MESH',authenticatedPeers:2,missionBindings:[{mission:'1111-2222',name:'Mission Alpha',enabled:true}]})")
 page.evaluate('window.tokenMeshRefreshI662()');page.wait_for_timeout(160)
 assert chip.inner_text()=='CONNECTED'
 assert page.locator('#meshMissionCreateI662').is_enabled()
 coords=[header.locator('.ms-title').bounding_box(),chip.bounding_box(),sw.bounding_box(),arr.bounding_box()]
 assert coords[0]['x']<coords[1]['x']<coords[2]['x']<coords[3]['x'],coords
 page.screenshot(path='/mnt/data/_i664_browser_connected.png',full_page=True)
 assert sw.locator('.ms-knob').evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgb(57, 217, 138)'
 assert not errors,errors
 print('PASS: header order, no wrap, status states, independent toggle/collapse, restore expand, mission control; no JS errors')
 b.close()
