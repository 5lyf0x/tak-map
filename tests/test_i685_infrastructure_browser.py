"""i685 browser test: real sidebar assets and Infrastructure card interaction in Chromium."""
import json,re
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
CORE=(ROOT/'assets/tak-map-sidebar-uniform-i684.css').read_text()
CSS=(ROOT/'assets/tak-map-infrastructure-i685.css').read_text()
JS=(ROOT/'assets/tak-map-infrastructure-i685.js').read_text()
OLD=(ROOT/'assets/tak-map-routing-dropdown-i675.js').read_text()
OLD_CSS=OLD.split("style.id='takMapSidebarAndSoftPillI675';style.textContent=`",1)[1].split('`;\nD.head.append(style)',1)[0]
CATS=[{'id':i,'label':label,'builtin':1,'hidden':0,'position':n} for n,(i,label) in enumerate([
 ('electrical','Electrical Power'),('communications','Communications'),('oil-gas','Oil & Natural Gas'),('water','Water & Wastewater'),
 ('rail','Rail Infrastructure'),('bridges','Bridges'),('aviation','Aviation'),('maritime','Maritime & Ports'),
 ('industrial','Industrial Facilities'),('emergency','Emergency Services'),('environmental','Environmental Facilities'),
 ('dams','Dams & Flood Control'),('space','Space & Satellite'),('logistics','Logistics & Distribution')])]
LAYERS=[{'id':'lacounty-sewer-mains','category_id':'water','name':'Sewer Gravity Mains — Los Angeles County','mode':'online','url':'https://dpw.gis.lacounty.gov/dpw/rest/services/Sewer_Network/FeatureServer/5','enabled':1,'kind':'sewer','hidden':0,'feature_count':0},
 {'id':'import-local','category_id':'water','name':'Offline Sewer Test','mode':'offline','url':'','enabled':1,'kind':'sewer','hidden':0,'feature_count':1}]
FEATURE={'type':'Feature','id':'main-1','geometry':{'type':'LineString','coordinates':[[-118.6,34.1],[-118.5,34.2]]},'properties':{'PIPE_DIAMETER':48,'PIPE_MATERIAL':'RCP','NAME':'Major sewer main'}}
HTML='''<!doctype html><html><head><meta charset="utf-8"><style>
:root{--panel:#101923}body{background:#0b141d;color:#eee;font-family:Manrope,system-ui,sans-serif}#sidebar{width:370px;display:flex;flex-direction:column;gap:7px}
.panel{background:#101923;border:1px solid #33414b;border-radius:13px;min-height:50px}.panel>h2{font-size:13px;line-height:1.3;display:flex;align-items:center;margin:0;padding:10px}
#tokenMeshCardI660 .ms-header{display:flex;align-items:center;padding:10px;background:#0d1c25}#takVeilCardI665 .tv-head{display:flex;padding:10px}
#takVeilCardI665 .tv-chip,#tokenMeshCardI660 .ms-chip{margin-left:auto}
</style></head><body><aside id="sidebar">
<div class="panel collapsible collapsed" id="mapmode"><h2>MAP MODE</h2></div>
<div class="panel collapsible collapsed" id="basemap"><h2>BASEMAP</h2></div>
<div class="panel" id="takVeilCardI665"><div class="tv-head"><strong>XTAK VEIL</strong><span class="tv-chip">DISABLED</span></div></div>
<div class="panel" id="tokenMeshCardI660"><h2 class="ms-header"><span class="ms-title">MESH SYNC</span><span class="ms-chip">NOT ENROLLED</span></h2></div>
<div class="panel collapsible collapsed" id="offline"><h2>OFFLINE MAPS</h2></div>
<div class="panel collapsible collapsed" id="tools"><h2>TOOLS</h2></div>
</aside><div id="map"></div></body></html>'''
FAKE_MAP="""
window.map={handlers:{},getBounds(){return{getWest:()=>-119,getSouth:()=>34,getEast:()=>-118,getNorth:()=>35}},on(name,fn){this.handlers[name]=fn},off(){},removeLayer(){},getZoom:()=>12};
window.takLeafletMap=window.map;
window.TakMapContextSidebarI572={showReadOnly(o){window.__detail=o}};
window.L={layerGroup(){return{addTo(){return this}}},geoJSON(data,o){window.__features=data.features;window.__shapes=[];
  for(const f of data.features){const shape={options:{color:'#666',weight:2},bindTooltip(t){this.tooltip=t;return this},on(e,fn){this[e]=fn},setStyle(next){Object.assign(this.options,next)}};o.onEachFeature(f,shape);window.__shapes.push(shape)}
  return{addTo(){return this}}},circleMarker(ll,opts){return{}},rectangle(){return{addTo(){return this}}},DomEvent:{stopPropagation(){}}};
"""

def test():
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  try:
   for width in (1280,390):
    page=browser.new_page(viewport={'width':width,'height':800})
    page.set_content(HTML)
    page.add_style_tag(content=CORE)
    page.add_style_tag(content=OLD_CSS) # loaded AFTER i684, as in the actual site
    page.add_style_tag(content=CSS)
    page.evaluate(FAKE_MAP)
    state={'ok':True,'categories':CATS,'layers':[dict(x) for x in LAYERS],'jobs':[]}
    page.evaluate("""({state,feature}) => {
      const store={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>store[k]??null,setItem:(k,v)=>store[k]=String(v)}});
      window.__fixture=state;
      window.fetch=async(url,opts)=>{
        const path=String(url),payload=opts?.body?JSON.parse(opts.body):{};
        if(path.includes('/manage')){
          for(const row of state.layers){if(row.id===payload.id&&payload.op==='layer-enable')row.enabled=Number(!!payload.enabled)}
          return {ok:true,json:async()=>state};
        }
        if(path.includes('/features'))return {ok:true,json:async()=>({ok:true,features:[feature],partial:false})};
        return {ok:true,json:async()=>state};
      };
    }""",{'state':state,'feature':FEATURE})
    page.on("pageerror",lambda e:print("PAGE ERROR",e))
    page.add_script_tag(content=JS)
    page.wait_for_function("document.getElementById('takInfraCardI685') && document.querySelectorAll('#takInfraCategoriesI685 .infra-category').length===14",timeout=8000)
    card=page.locator('#takInfraCardI685')
    assert card.count()==1
    assert page.locator('#sidebar').evaluate('(el)=>el.children[2].id')=='takInfraCardI685' # after BASEMAP
    fonts=page.evaluate("""() => ['#mapmode h2','#basemap h2','#offline h2','#tools h2','#tokenMeshCardI660 .ms-title','#takVeilCardI665 strong','#takInfraCardI685 .infra-title'].map(x=>{let s=getComputedStyle(document.querySelector(x));return [s.fontFamily,s.fontSize,s.fontWeight,s.letterSpacing,s.lineHeight]})""")
    assert len({tuple(x) for x in fonts})==1,fonts
    page.evaluate("document.getElementById('basemap').classList.remove('collapsed')")
    fonts2=page.evaluate("""() => ['#mapmode h2','#basemap h2','#offline h2','#tokenMeshCardI660 .ms-title'].map(x=>[getComputedStyle(document.querySelector(x)).fontSize,getComputedStyle(document.querySelector(x)).fontWeight])""")
    assert len({tuple(x) for x in fonts2})==1,fonts2
    page.locator('#takInfraCardI685 .infra-category').filter(has=page.locator('.infra-cat-head',has_text='Water & Wastewater')).first.locator('input[type=checkbox]').first.wait_for(timeout=5000)
    page.wait_for_function('window.__shapes && window.__shapes.length>0')
    tip=page.evaluate('window.__shapes[0].tooltip')
    assert '48 in diameter' in tip,tip
    page.evaluate('window.__shapes[0].click({originalEvent:{}})')
    detail=page.evaluate('window.__detail')
    assert 'Major sewer main' in detail['title'],detail
    assert 'Original GIS Attributes' in detail['html'] and '48 in' in detail['html'],detail
    page.locator('#takInfraCardI685 [data-mode="offline"]').click()
    page.wait_for_function("document.querySelector('#takInfraCardI685 [data-mode=offline]').getAttribute('aria-pressed')==='true'")
    assert page.locator('#takInfraCategoriesI685').get_by_text('Offline Sewer Test').count()==1
    assert page.locator('#takInfraCategoriesI685').get_by_text('Sewer Gravity Mains — Los Angeles County').count()==0
    print('PASS i685 browser '+str(width)+': headings identical, category parity, tooltip, single-click details, offline switching')
    page.close()
  finally:browser.close()

if __name__=='__main__':test()
