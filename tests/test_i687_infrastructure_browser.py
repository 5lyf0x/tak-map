"""i687 Infrastructure browser regression: zoom, per-mode category hide, click-only objects."""
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_i685_infrastructure_browser import ROOT, CORE, OLD_CSS, HTML, FAKE_MAP, CATS, FEATURE
from test_i686_infrastructure_browser import LAYERS
JS=(ROOT/'assets/tak-map-infrastructure-i687.js').read_text()
CSS=(ROOT/'assets/tak-map-infrastructure-i687.css').read_text()

def test():
 with sync_playwright() as p:
  b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  try:
   for width in (1280,390):
    page=b.new_page(viewport={'width':width,'height':850})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('dialog',lambda d:d.accept(prompt_text='Water & Wastewater' if d.type=='prompt' else None))
    page.set_content(HTML)
    for style in (CORE,OLD_CSS,CSS):page.add_style_tag(content=style)
    page.evaluate(FAKE_MAP)
    cats=[{**x,'hidden_online':0,'hidden_offline':0} for x in CATS]
    layers=[{**x,'min_zoom':None} for x in LAYERS]
    # The existing County source behaves as the built-in manhole layer, with z14 default.
    layers[0].update({'id':'lacounty-sewer-manholes','kind':'point','name':'Sewer Manholes — Los Angeles County','min_zoom':14})
    state={'ok':True,'categories':cats,'layers':layers,'jobs':[]}
    page.evaluate('''({state,feature})=>{
      const storage={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>storage[k]??null,setItem:(k,v)=>storage[k]=String(v)}});
      window.__zoom=13;window.map.getZoom=()=>window.__zoom;
      window.__requests=[];window.__manages=[];window.__featuresDrawn=[];window.__fixture=state;
      window.fetch=async(url,opts)=>{
        const query=String(url);window.__requests.push(query);
        const body=opts?.body?JSON.parse(opts.body):{};
        if(query.includes('/manage')){
          window.__manages.push(body);
          const cat=state.categories.find(x=>x.id===body.id);
          if(body.op==='category-hide'&&cat)cat['hidden_'+body.mode]=Number(!!body.hidden);
          for(const l of state.layers){if(l.id!==body.id)continue;
            if(body.op==='layer-enable')l.enabled=Number(!!body.enabled);
            if(body.op==='layer-minzoom')l.min_zoom=body.min_zoom;
          }
          return {ok:true,json:async()=>state};
        }
        if(query.includes('/count'))return {ok:true,json:async()=>({ok:true,count:window.__dense?6500:1})};
        if(query.includes('/features')){
          const params=new URL(query,'https://test.invalid').searchParams;
          const f=structuredClone(feature);f.id=params.get('layer')+'-p1';
          f.properties.MH_DESCRIPTION='Maintenance Hole';f.properties.MH_TYPE='Standard';
          return {ok:true,json:async()=>({ok:true,features:[f],loaded_count:1,limited:false,has_more:false,feature_cap_reached:false,geometry_simplified:false,mode:params.get('mode')})};
        }
        return {ok:true,json:async()=>state};
      };
      window.L.geoJSON=(data,options)=>{
        const shapes=[];
        for(const f of data.features){const shape={options:{color:'#aaa',weight:2},bindTooltip(v){this.tooltip=v;return this},on(k,fn){this[k]=fn},setStyle(v){Object.assign(this.options,v)}};
          options.onEachFeature(f,shape);shapes.push(shape)}
        window.__featuresDrawn.push(...shapes);
        return {addTo(g){g.shapes=(g.shapes||[]).concat(shapes);return this}};
      };
      window.L.layerGroup=()=>({addTo(){return this},eachLayer(fn){(this.shapes||[]).forEach(fn)}});
    }''',{'state':state,'feature':FEATURE})
    page.add_script_tag(content=JS)
    page.wait_for_function('window.TakMapInfrastructureI687?.state.initialized',timeout=9000)
    page.wait_for_function("window.__requests.some(x=>x.includes('/features')&&x.includes('layer=online-elec'))",timeout=9000)
    page.wait_for_timeout(400)
    assert not errors,errors
    # Manholes not fetched below min zoom despite being enabled.
    req=page.evaluate("window.__requests.filter(x=>x.includes('/features')&&x.includes('lacounty-sewer-manholes'))")
    assert not req,req
    page.locator('#takInfraCategoriesI685 .infra-category').filter(has_text='Water & Wastewater').locator('.infra-cat-head').click() if not page.locator('#takInfraCategoriesI685 .infra-category').filter(has_text='Water & Wastewater').locator('.infra-layer').count() else None
    assert page.get_by_text('Hidden below z14').count()>=1
    page.evaluate("window.__zoom=14;window.map.handlers['moveend zoomend']()")
    page.wait_for_function("window.__requests.some(x=>x.includes('/features')&&x.includes('lacounty-sewer-manholes'))",timeout=8000)
    page.wait_for_timeout(100)
    assert not page.evaluate('window.__featuresDrawn.some(s=>!!s.tooltip)'), 'Hover tooltip accidentally bound'
    page.evaluate('window.__featuresDrawn.at(-1).click({originalEvent:{}})')
    detail=page.evaluate('window.__detail')
    assert detail and 'Original GIS Attributes' in detail['html'] and 'Maintenance Hole' in detail['html']
    before=page.evaluate("window.__requests.filter(x=>x.includes('/features')).length")
    page.locator('#takInfraCategoriesI685 .infra-category').filter(has_text='Water & Wastewater').get_by_role('button',name='Remove from Online').click()
    page.wait_for_function("window.__manages.some(x=>x.op==='category-hide'&&x.mode==='online'&&x.hidden)")
    page.wait_for_timeout(500)
    assert page.locator('#takInfraCategoriesI685 .infra-category').filter(has_text='Water & Wastewater').count()==0
    records=page.evaluate('[...window.TakMapInfrastructureI687.state.records.keys()]')
    assert 'import-local' in records and 'lacounty-sewer-manholes' not in records,records
    page.locator('#takInfraCardI685 [data-mode="offline"]').click()
    assert page.locator('#takInfraCategoriesI685 .infra-category').filter(has_text='Water & Wastewater').count()==1
    assert page.locator('#takInfraCategoriesI685 .infra-category').filter(has_text='Water & Wastewater').locator('.infra-layer').count()==1
    page.locator('#takInfraCardI685 [data-mode="online"]').click()
    page.locator('#takInfraCardI685 [data-action="restore"]').click()
    page.wait_for_function("window.__manages.some(x=>x.op==='category-hide'&&x.mode==='online'&&x.hidden===false)")
    assert page.locator('#takInfraCategoriesI685 .infra-category').filter(has_text='Water & Wastewater').count()==1
    # Below threshold again: cancel query, remove manhole point while offline remains.
    page.evaluate("window.__zoom=13;window.map.handlers['moveend zoomend']()")
    page.wait_for_timeout(600)
    records=page.evaluate('[...window.TakMapInfrastructureI687.state.records.keys()]')
    assert 'lacounty-sewer-manholes' not in records and 'import-local' in records,records
    # Known >5k point count uses 16 geographic cells instead of provider-first 5k.
    page.evaluate("window.__zoom=14;window.__dense=true;window.map.handlers['moveend zoomend']()")
    page.wait_for_function("window.TakMapInfrastructureI687.state.records.get('lacounty-sewer-manholes')?.featureCap===true",timeout=10000)
    assert page.evaluate("new Set(window.__requests.filter(x=>x.includes('/features')&&x.includes('lacounty-sewer-manholes')).map(x=>new URL(x,'https://test.invalid').searchParams.get('bbox'))).size")>=16
    assert page.get_by_text('LIMIT REACHED',exact=False).count()>=1
    assert not errors,errors
    print(f'PASS i687 browser {width}: zoom threshold, independent mode removal/restore, click-only details, both source types')
    page.close()
  finally:b.close()

if __name__=='__main__':test()
