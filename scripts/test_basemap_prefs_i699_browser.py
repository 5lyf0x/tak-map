#!/usr/bin/env python3
from pathlib import Path
from playwright.sync_api import sync_playwright
src=(Path(__file__).resolve().parents[1]/'assets/tak-map-basemap-stack-i673.js').read_text()
html='''<!doctype html><html><body><select id="basemapSelect"><option value="a">A</option><option value="b">B</option></select><div id="other"></div><script>
window.config={basemaps:[{id:'a',label:'Road',url:'https://example/a/{z}/{x}/{y}'},{id:'b',label:'Terrain',url:'https://example/b/{z}/{x}/{y}'}],default_basemap:'a'};
window.activeBasemap='a';window.baseLayer=null;
window.map={panes:{},hasLayer(l){return !!l._visible},getPane(id){return this.panes[id]},createPane(id){return this.panes[id]=document.createElement('div')},removeLayer(l){l._visible=false}};
const layer=()=>({ _visible:false, addTo(m){this._visible=true;return this},setOpacity(n){this.alpha=n;},setZIndex(n){this.z=n;},getContainer(){return document.createElement('div')},on(){},redraw(){} });
window.L={tileLayer(){return layer()},TileLayer:{extend(){return class{}}}};
window.__server={revision:1,preferences:{order:['b','unavailable','a'],enabled:['b','a'],opacity:{b:77,a:100},blend:{b:'multiply'},tone:{b:{brightness:119,contrast:108,saturation:83}},detail:{},expanded:true}};
window.__posts=[];
window.fetch=async(url,options={})=>{
if(String(url).includes('basemap-stack-i699')){
 if(options.method==='POST'){const sent=JSON.parse(options.body);window.__posts.push(sent);
  if(sent.revision!==window.__server.revision)return {ok:false,status:409,json:async()=>({ok:false,conflict:true,revision:window.__server.revision})};
  window.__server.revision++;window.__server.preferences=sent.preferences;
  return {ok:true,status:200,json:async()=>({ok:true,revision:window.__server.revision})}; }
 return {ok:true,status:200,json:async()=>({ok:true,user_key:'a'.repeat(64),revision:window.__server.revision,preferences:window.__server.preferences})};
}
throw Error('unexpected fetch '+url)
}
</script></body></html>'''
with sync_playwright() as w:
 browser=w.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox']);p=browser.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
 p.set_content(html);p.add_script_tag(content=src)
 p.wait_for_function('TakMapBaseStackI673.state.order[0] === "b"',timeout=10000)
 a=p.evaluate('({order:TakMapBaseStackI673.state.order,enabled:[...TakMapBaseStackI673.state.enabled],blend:TakMapBaseStackI673.state.blend,tone:TakMapBaseStackI673.state.tone})')
 assert a['order']==['b','unavailable','a'],a
 assert a['blend']['b']=='multiply' and a['tone']['b']['brightness']==119,a
 assert p.locator('#takBasemapSyncStatusI699').count()>=0
 p.wait_for_timeout(750)
 assert p.evaluate('__posts.length')==0,'Remote hydration must not rewrite server preferences'
 print('PASS server-authoritative restoration, missing imported layer kept, no silent overwrite')
 p.evaluate('TakMapBaseStackI673.setOpacity("b",45)')
 p.wait_for_function('__server.revision===2',timeout=10000)
 assert p.evaluate('__server.preferences.opacity.b')==45
 print('PASS per-user opacity saved with revision check')
 p.evaluate('window.config.basemaps=[{id:"a",label:"Road",url:"https://example/a/{z}/{x}/{y}"}];TakMapBaseStackI673.syncCatalog();')
 assert p.evaluate('TakMapBaseStackI673.state.order.includes("b") && TakMapBaseStackI673.state.order.includes("unavailable")')
 print('PASS temporarily missing basemaps do not lose saved order')
 # restore tile source while server record stays authoritative
 p.evaluate('window.config.basemaps.push({id:"b",label:"Terrain",url:"https://example/b/{z}/{x}/{y}"});TakMapBaseStackI673.syncCatalog()')
 # another session edits on server, stale local write rejected
 p.evaluate('window.__server.revision=3;window.__server.preferences={...window.__server.preferences,opacity:{...window.__server.preferences.opacity,b:67}};TakMapBaseStackI673.setOpacity("b",20)')
 p.wait_for_function('TakMapBaseStackI673.state.opacity.b===67',timeout=15000)
 assert p.evaluate('__server.revision')==3
 print('PASS conflict reloads latest server preferences without replacing other user changes')
 assert not errors,errors
 print('PASS no browser errors')
 browser.close()
