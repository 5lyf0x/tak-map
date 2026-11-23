"""i677 Chromium: controlled Leaflet-style tile panes, visual opacity and order."""
from pathlib import Path
from io import BytesIO
from PIL import Image
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
js=(root/'assets/tak-map-basemap-stack-i673.js').read_text()
html='''<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:0;background:#101924;color:white;font:12px sans-serif}
#map{position:absolute;left:0;top:0;width:420px;height:310px;background:#000;overflow:hidden}
.pane{position:absolute;inset:0;pointer-events:none}
#sidebar{position:absolute;left:430px;top:8px;width:300px}
</style></head><body><div id="map"></div><div id="sidebar"><select id="basemapSelect"><option value="imagery">Imagery</option><option value="topo">Topographic</option></select></div></body></html>'''
init=r'''
window.__fakeStorage={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>window.__fakeStorage[k]??null,setItem:(k,v)=>window.__fakeStorage[k]=String(v),removeItem:k=>delete window.__fakeStorage[k]}});
window.config={basemaps:[{id:'imagery',label:'ESRI World Imagery',url:'imagery'}, {id:'topo',label:'ESRI World Topographic',url:'topo'}],default_basemap:'imagery'};
window.activeBasemap='imagery';window.saveBasemap=async()=>({ok:true});
const panes={},members=new Set(),container=document.getElementById('map');
window.map={getPane:(n)=>panes[n]||null,createPane:(n)=>{const q=document.createElement('div');q.className='pane';q.id=n;panes[n]=q;container.append(q);return q},
 addLayer:(l)=>{members.add(l);l._el=document.createElement('div');l._el.style.cssText='position:absolute;inset:0;background:'+(l._url==='imagery'?'#ff0000':l._url==='topo'?'#0000ff':'#00ff00');l._el.style.opacity=l.options.opacity??1;l._el.style.zIndex=l._zi||0;map.getPane(l.options.pane||'tilePane').append(l._el);return map},
 hasLayer:(l)=>members.has(l),removeLayer:(l)=>{members.delete(l);l._el?.remove();return map}};
map.createPane('tilePane').style.zIndex='200';
window.L={tileLayer:(url,options)=>{const l={_url:url,options:{...(options||{})},_zi:0,addTo:(m)=>{m.addLayer(l);return l},setOpacity:(v)=>{l.options.opacity=v;if(l._el)l._el.style.opacity=v;return l},setZIndex:(v)=>{l._zi=v;if(l._el)l._el.style.zIndex=v;return l}};return l}};
window.baseLayer=L.tileLayer('legacy',{pane:'tilePane'}).addTo(map);
'''
def sample(page):
 img=Image.open(BytesIO(page.locator('#map').screenshot())).convert('RGB')
 return img.getpixel((150,135))
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':750,'height':325})
 page.set_content(html);page.evaluate(init);page.evaluate(js);page.wait_for_timeout(350)
 assert page.evaluate('TakMapBaseStackI673.state.ready')
 assert page.evaluate("map.getPane('takBasemapI673').style.zIndex")=='220'
 assert page.evaluate('map.hasLayer(window.baseLayer)') # now managed bottom (topo when enabled)
 assert page.evaluate("Array.from(document.querySelectorAll('#tilePane>div')).length")==0,'legacy basemap still covering stack'
 # Enable both, imagery top 100%, topo below 100% -> red.
 page.evaluate("TakMapBaseStackI673.changeEnabled('topo',true)")
 a=sample(page);assert a[0]>235 and a[1]<25 and a[2]<25,('imagery not on top',a)
 # Imagery 0%, topo 100% -> blue.
 page.evaluate("TakMapBaseStackI673.setOpacity('imagery',0)")
 b=sample(page);assert b[2]>235 and b[0]<25,('topo not visible under transparency',b)
 # 50% red over 100% blue -> purple, distinct from either opaque source.
 page.evaluate("TakMapBaseStackI673.setOpacity('imagery',50)")
 c=sample(page);assert c[0]>95 and c[2]>95 and c[1]<20,('blending failed',c)
 # Changing both to 50% must visibly change output again.
 page.evaluate("TakMapBaseStackI673.setOpacity('topo',50)")
 d=sample(page);assert d!=c and d[2]<c[2],('underlay opacity unchanged',c,d)
 # Restore opacity and reorder, topo becomes visual top.
 page.evaluate("TakMapBaseStackI673.setOpacity('topo',100);TakMapBaseStackI673.move(1,0)")
 e=sample(page);assert e[2]>235 and e[0]<25,('reorder failed',e)
 # Checkbox changes actual rendered layer state, not just DOM controls.
 page.evaluate("TakMapBaseStackI673.changeEnabled('topo',false)")
 f=sample(page);assert f[0]>95 and f[2]<25,('toggle did not hide layer',f)
 assert page.evaluate("JSON.parse(localStorage.getItem('takmap.basemap.blend.i673.v1')).opacity.imagery")==50
 browser.close()
 print('PASS i677 basemap pane / opacity / reorder / toggle / persisted preferences; pixels:',a,b,c,d,e,f)
