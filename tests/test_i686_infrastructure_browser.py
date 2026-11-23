"""Chromium i686 Infrastructure active mixed-mode card tests using real i686 assets."""
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_i685_infrastructure_browser import ROOT, CORE, OLD_CSS, HTML, FAKE_MAP, CATS, FEATURE
JS=(ROOT/'assets/tak-map-infrastructure-i686.js').read_text()
CSS=(ROOT/'assets/tak-map-infrastructure-i686.css').read_text()
LAYERS=[
 {'id':'lacounty-sewer-mains','category_id':'water','name':'Sewer Gravity Mains — Los Angeles County','mode':'online','url':'https://dpw.gis.lacounty.gov/dpw/rest/services/Sewer_Network/FeatureServer/5','enabled':1,'kind':'sewer','hidden':0,'color':'#66bdd0','feature_count':0},
 {'id':'online-elec','category_id':'electrical','name':'Transmission Lines','mode':'online','enabled':1,'kind':'line','hidden':0,'color':'#eec477','feature_count':0},
 {'id':'import-local','category_id':'water','name':'Offline Sewer Test','mode':'offline','url':'','enabled':1,'kind':'sewer','hidden':0,'color':'#cc2222','feature_count':842},
 {'id':'offline-bridge','category_id':'bridges','name':'Offline Bridges','mode':'offline','url':'','enabled':1,'kind':'line','hidden':0,'color':'#93cb8b','feature_count':100}]

def test():
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  try:
   for width in (1280,390):
    page=browser.new_page(viewport={'width':width,'height':800})
    page.set_content(HTML)
    page.add_style_tag(content=CORE);page.add_style_tag(content=OLD_CSS);page.add_style_tag(content=CSS)
    page.evaluate(FAKE_MAP)
    page.evaluate('''()=>{
      window.__entities=[];
      const canvas=document.createElement('canvas');
      window.Cesium={Color:{fromCssColorString(s){return{hex:s,withAlpha(a){return{hex:s,alpha:a}}}},BLACK:{hex:'#000000'},WHITE:{hex:'#ffffff'}},
        HeightReference:{CLAMP_TO_GROUND:1},Cartesian3:{fromDegrees(x,y){return[x,y]},fromDegreesArray(a){return a}},Cartesian2:function(x,y){this.x=x;this.y=y}};
      window.terrain3DViewer={canvas,scene:{pick(){return null}},entities:{add(o){window.__entities.push(o);return o},remove(o){window.__entities=window.__entities.filter(x=>x!==o)}}};
    }''')
    state={'ok':True,'categories':CATS,'layers':[dict(x) for x in LAYERS],'jobs':[]}
    page.evaluate('''({state,feature})=>{
       const storage={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>storage[k]??null,setItem:(k,v)=>storage[k]=String(v)}});
       window.__requests=[];window.__manages=[];window.__groups=[];window.__fixture=state;
       window.fetch=async(url,options)=>{
         const query=String(url);window.__requests.push(query);
         const body=options?.body?JSON.parse(options.body):{};
         if(query.includes('/manage')){
           window.__manages.push(body);
           for(const l of state.layers){if(l.id===body.id&&body.op==='layer-enable')l.enabled=Number(!!body.enabled);
             if(l.id===body.id&&body.op==='layer-color')l.color=body.color;}
           return {ok:true,json:async()=>state};
         }
         if(query.includes('/features')){
           const mode=new URL(query,'https://test.invalid').searchParams;
           const id=mode.get('layer');const f=structuredClone(feature);
           f.id=id+'-f1';f.properties.NAME=id;
           if(id==='offline-bridge')f.geometry={type:'LineString',coordinates:[[-118.5,34.55],[-118.45,34.65]]};
           return {ok:true,json:async()=>({ok:true,features:[f],loaded_count:1,limited:false,mode:mode.get('mode')})};
         }
         return {ok:true,json:async()=>state};
       };
       window.map.removeLayer=function(group){window.__removed=(window.__removed||0)+1;};
       window.L.layerGroup=()=>({addTo(){window.__groups.push(this);return this},eachLayer(cb){(this.all||[]).forEach(cb)}});
       window.L.geoJSON=(data,o)=>{const local=[];
         for(const f of data.features){const shape={options:{color:'#666',weight:2},bindTooltip(t){this.tooltip=t;return this},on(e,fn){this[e]=fn},setStyle(x){Object.assign(this.options,x)}};
           o.onEachFeature(f,shape);local.push(shape)}
         window.__shapes=(window.__shapes||[]).concat(local);
         return{addTo(group){group.all=(group.all||[]).concat(local);return this}}};
     }''',{'state':state,'feature':FEATURE})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.add_script_tag(content=JS)
    page.wait_for_function("window.TakMapInfrastructureI686 && window.TakMapInfrastructureI686.state.initialized")
    page.wait_for_function("window.__requests.filter(x=>x.includes('/features')).length>=4",timeout=9000)
    page.wait_for_timeout(120)
    assert not errors,errors
    parts=page.evaluate('window.TakMapInfrastructureI686.boxParts([179,10,-179,12],1.5)')
    assert len(parts)==2 and parts[0][2]==180 and parts[1][0]==-180,parts
    polar=page.evaluate('window.TakMapInfrastructureI686.boxParts([0,89,1,90],1.5)')
    assert all(-90<=b[1]<b[3]<=90 for b in polar),polar
    page.evaluate('window.__shapes[0].click({originalEvent:{}})')
    detail=page.evaluate('window.__detail')
    assert detail and 'INFRASTRUCTURE' in detail['kicker'] and 'Original GIS Attributes' in detail['html'],detail
    assert page.locator('#takInfraCardI685').count()==1
    assert page.locator('#sidebar').evaluate('(el)=>el.children[2].id')=='takInfraCardI685'
    # Main management tab starts Online, but the map fetched all four layers.
    def counts():return page.evaluate("window.__requests.filter(x=>x.includes('/features')).length")
    assert counts()==4,counts()
    # Check all 4 geographic queries padded +50%, 25% on each side.
    got=page.evaluate('''()=>window.__requests.filter(x=>x.includes('/features')).map(q=>new URL(q,'https://test.invalid').searchParams.get('bbox'))''')
    for b in got:
     w,s,e,n=map(float,b.split(','))
     assert abs(w+119.25)<.001 and abs(e+117.75)<.001,(b,got)
     assert abs(s-33.75)<.001 and abs(n-35.25)<.001,(b,got)
    # Expand three independent categories and ensure closing one leaves others.
    categories=page.locator('#takInfraCategoriesI685 .infra-cat-head')
    categories.filter(has_text='Electrical Power').click()
    categories.filter(has_text='Bridges').click()
    assert page.locator('#takInfraCategoriesI685 .infra-category').filter(has_text='Electrical Power').locator('.infra-layer').count()==1
    assert page.locator('#takInfraCategoriesI685 .infra-category').filter(has_text='Water & Wastewater').locator('.infra-layer').count()==1
    assert page.locator('#takInfraCategoriesI685 .infra-category').filter(has_text='Bridges').locator('.infra-layer').count()==0 # offline hidden in Online management
    categories.filter(has_text='Water & Wastewater').click()
    assert page.locator('#takInfraCategoriesI685 .infra-category').filter(has_text='Electrical Power').locator('.infra-layer').count()==1
    n=counts();page.locator('#takInfraCardI685 [data-mode="offline"]').click();page.wait_for_timeout(150)
    assert counts()==n,'switching management modes should not fetch or clear visible features'
    assert page.evaluate('window.__detail.title')==detail['title'],'management switch dismissed selected object'
    assert page.locator('#takInfraCategoriesI685 .infra-category').filter(has_text='Bridges').locator('.infra-layer').count()==1
    assert page.locator('#takInfraCategoriesI685 .infra-category').filter(has_text='Water & Wastewater').locator('.infra-layer').count()==0
    assert page.locator('#takInfraCategoriesI685 .infra-category').filter(has_text='Electrical Power').locator('.infra-cat-head').count()==1
    categories.filter(has_text='Water & Wastewater').click()
    assert page.get_by_text('1 / 842',exact=False).count()>=1
    # Changing color persists via backend and does not requery.
    picker=page.locator('#takInfraCategoriesI685 .infra-category').filter(has_text='Bridges').locator('input[type=color]')
    picker.fill('#12a1b2');page.wait_for_timeout(150)
    assert counts()==n
    assert page.evaluate('window.__manages.some(x=>x.op===\'layer-color\' && x.color===\'#12a1b2\')')
    assert page.evaluate('window.__entities.some(x=>x.properties?.infraSource==="offline-bridge"&&x.polyline?.material?.hex==="#12a1b2")')

    # Origin master switches suppress only that origin's render set.
    page.locator('#takInfraOnlineVisibleI686').uncheck();page.wait_for_timeout(600)
    record=page.evaluate("[...window.TakMapInfrastructureI686.state.records.keys()]")
    assert set(record)=={'import-local','offline-bridge'},record
    assert page.locator('#takInfraCardI685').count()==1
    if width==1280:page.screenshot(path='/mnt/data/_tak_i686_card_browser.png',full_page=True)
    print('PASS i686 browser',width,'mixed layers, padded bounds, multi-open, counters, colors, origin switches')
    page.close()
  finally:browser.close()

if __name__=='__main__':test()
