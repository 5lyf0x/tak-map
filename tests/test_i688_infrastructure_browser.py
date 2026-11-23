"""i688 Chromium: offline card, stable state, line hit/selection, search, filters, icons."""
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_i685_infrastructure_browser import ROOT, CORE, OLD_CSS, HTML, CATS
JS=(ROOT/'assets/tak-map-infrastructure-i688.js').read_text()
CSS=(ROOT/'assets/tak-map-infrastructure-i688.css').read_text()

HARNESS=r'''()=>{
 const sidebar=document.querySelector('#sidebar');const search=document.createElement('div');
 search.innerHTML='<input id="layerSearch" placeholder="Search"><div id="searchResults"></div>';sidebar.prepend(search);
 window.renderSearchResults=function(){const box=document.querySelector('#searchResults');box.textContent='No matching map objects.';box.style.display='block'};
 const storage={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>storage[k]??null,setItem:(k,v)=>storage[k]=String(v)}});
 window.__zoom=15;window.__bounds=[-119,34,-118,35];window.__requests=[];window.__manages=[];window.__groups=[];window.__shapes=[];window.__removed=0;window.__detail=null;window.__popupClose=0;
 window.map={handlers:{},getZoom(){return window.__zoom},getCenter(){return{lat:34.5,lng:-118.5}},getBounds(){const b=window.__bounds;return{getWest:()=>b[0],getSouth:()=>b[1],getEast:()=>b[2],getNorth:()=>b[3]}},on(n,fn){for(const key of n.split(' '))(this.handlers[key]??=[]).push(fn)},off(){},removeLayer(g){window.__removed++},fire(n){for(const cb of this.handlers[n]||[])cb({originalEvent:{},latlng:{lat:34.5,lng:-118.5}})},setView(){window.__zoom=15;this.fire('moveend')},fitBounds(){this.fire('moveend')}};
 window.takLeafletMap=window.map;
 window.TakMapContextSidebarI572={showReadOnly(o){window.__detail=o},hide(){window.__popupClose++},diagnostics(){return{open:true}}};
 function P(){};function G(){};function M(){};
 function shape(options){return {options:{...options},setStyle(o){Object.assign(this.options,o)},on(k,fn){this[k]=fn},getLatLngs(){return [[34,-118],[34.1,-118.1]]},bringToFront(){},bringToBack(){},addTo(gr){gr.items.push(this);return this}}}
 window.L={Polyline:P,Polygon:G,layerGroup(){return{items:[],addTo(){window.__groups.push(this);return this},removeLayer(s){this.items=this.items.filter(x=>x!==s)},eachLayer(fn){this.items.forEach(fn)}}},polyline(coords,o){const s=shape(o);Object.setPrototypeOf(s,P.prototype);s.getLatLngs=()=>coords;return s},geoJSON(data,o={}){
   const items=[];for(const f of data?.features||(data?.type==='Feature'?[data]:[])){
     let s=shape(o.style?.(f)||{});if(f.geometry?.type?.includes('Line'))Object.setPrototypeOf(s,P.prototype);
     if(f.geometry?.type?.includes('Polygon'))Object.setPrototypeOf(s,G.prototype);
     o.onEachFeature?.(f,s);items.push(s);window.__shapes.push(s)
   }return{getBounds(){return{isValid:()=>true,getNorthEast:()=>({distanceTo:()=>0}),getSouthWest:()=>({})}},addTo(group){if(group?.items)group.items.push(...items);return this}}},
 circleMarker(ll,o){return shape(o)},marker(ll,o){return shape(o)},icon(o){return o},rectangle(){return shape({})},DomEvent:{stopPropagation(){}},
 };
 window.__feature={type:'Feature',id:'pipe-48',geometry:{type:'LineString',coordinates:[[-118.5,34.3],[-118.2,34.5]]},properties:{NAME:'MAIN_48',PIPE_DIAMETER:48,ZERO:0,ACTIVE:false,NULLVAL:null,NESTED:{a:2}}};
 window.__other={type:'Feature',id:'tower-9',geometry:{type:'Point',coordinates:[-118.3,34.4]},properties:{NAME:'Tower 9',HEIGHT:100}};
 const categories=window.__cats;const layers=[
  {id:'stored-pipes',category_id:'water',name:'Imported Sewer Network',mode:'offline',kind:'sewer',enabled:1,hidden:0,color:'#66bdd0',min_zoom:null,feature_count:850,filter_spec:{enabled:false,mode:'all',rules:[]}},
  {id:'stored-tower',category_id:'communications',name:'My Towers',mode:'offline',kind:'point',enabled:1,hidden:0,color:'#b1a2f1',min_zoom:14,feature_count:123,filter_spec:{enabled:false,mode:'all',rules:[]}},
  {id:'online-source',category_id:'water',name:'County service',mode:'online',kind:'point',enabled:1,hidden:0,feature_count:0}];
 window.__fixture={ok:true,categories,layers,jobs:[]};
 window.fetch=async(url,opts)=>{const q=String(url);window.__requests.push(q);
  if(q.includes('/features')){const params=new URL(q,'https://test.invalid').searchParams;const f=params.get('layer')==='stored-pipes'?window.__feature:window.__other;
   return {ok:true,json:async()=>({ok:true,features:[structuredClone(f)],feature_cap_reached:false,geometry_simplified:false})}}
  if(q.includes('/manage')){const body=JSON.parse(opts.body);window.__manages.push(body);const l=layers.find(x=>x.id===body.id);
   if(l){if(body.op==='layer-filter')l.filter_spec=body.filter_spec;if(body.op==='layer-enable')l.enabled=Number(!!body.enabled);if(body.op==='layer-symbol'){l.point_symbol_mode=body.point_symbol_mode;l.point_symbol_ref=body.point_symbol_ref};if(body.op==='layer-color')l.color=body.color}
   return {ok:true,json:async()=>window.__fixture}}
  if(q.includes('/fields'))return{ok:true,json:async()=>({ok:true,fields:['PIPE_DIAMETER','NAME','HEIGHT']})};
  if(q.includes('/feature'))return{ok:true,json:async()=>({ok:true,feature:structuredClone(window.__feature),min_zoom:14})};
  if(q.includes('/search'))return{ok:true,json:async()=>({ok:true,results:[{id:'pipe-48',layer_id:'stored-pipes',label:'MAIN_48',category:'Water & Wastewater',layer_name:'Imported Sewer Network'}]})};
  return{ok:true,json:async()=>window.__fixture};
 };
}'''

def test():
 with sync_playwright() as pw:
  browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  try:
   for width in (1280,390):
    page=browser.new_page(viewport={'width':width,'height':850})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('dialog',lambda d:d.accept(prompt_text='dot' if d.type=='prompt' else None))
    page.set_content(HTML)
    for style in (CORE,OLD_CSS,CSS):page.add_style_tag(content=style)
    page.evaluate('(cats)=>window.__cats=cats',[{**x,'hidden_online':0,'hidden_offline':0} for x in CATS])
    page.evaluate(HARNESS)
    page.add_script_tag(content=JS)
    page.wait_for_function('window.TakMapInfrastructureI688?.state.ready',timeout=9000)
    page.wait_for_function('window.TakMapInfrastructureI688?.state.records.get("stored-pipes")?.status==="ready"',timeout=9000)
    assert not errors,errors
    assert page.locator('#takInfraCardI685 .infra-mode').count()==0
    assert page.locator('#takInfraCardI685 [data-mode]').count()==0
    assert page.locator('#takInfraCardI685 .infra-status').inner_text()=='OFFLINE'
    req=page.evaluate('window.__requests.filter(q=>q.includes("/features"))')
    assert len(req)==2 and all('mode=offline' in r for r in req),req
    assert all('bbox=-119.25' in r and '-117.750000' in r for r in req),req
    assert page.locator('#takInfraCardI685 .infra-category').count()==14
    # Hover stays silent, line geometry uses invisible hit stroke, two independent controls present.
    assert page.evaluate('window.__shapes.some(s=>!!s.tooltip)') is False
    assert page.evaluate('window.__groups.some(g=>g.items.some(s=>s.options.weight===13))'), 'no 5px hit stroke'
    page.evaluate('window.__shapes.find(s=>s.click && s.options.color==="#66bdd0").click({originalEvent:{}})')
    detail=page.evaluate('window.__detail')
    assert detail and 'GIS ATTRIBUTES' in detail['html'] and 'NULLVAL' in detail['html'] and 'false' in detail['html'] and 'NESTED' in detail['html'],detail
    assert '<details>' not in detail['html']
    assert page.evaluate('window.__shapes.find(s=>s.options.color==="#66bdd0").options.color')=='#66bdd0'
    assert page.evaluate('window.TakMapInfrastructureI688.state.selection.stroke.options.color')=='#e43b42'
    page.evaluate('window.map.fire("click")')
    assert page.evaluate('window.TakMapInfrastructureI688.state.selected') is None
    # View-model controls remain mounted through poll at least 6 seconds.
    page.evaluate('window.__zoomElement=document.querySelector("#takInfraCardI685 .infra-minzoom")')
    page.wait_for_timeout(5600)
    assert page.evaluate('window.__zoomElement===document.querySelector("#takInfraCardI685 .infra-minzoom")')
    # Both category rows can be expanded independently.
    page.locator('.infra-cat-head').filter(has_text='Communications').click()
    assert page.locator('.infra-category').filter(has_text='Water & Wastewater').locator('.infra-layer').count()==1
    assert page.locator('.infra-category').filter(has_text='Communications').locator('.infra-layer').count()==1
    # Filters & registry controls modify only their own layer.
    page.locator('.infra-category').filter(has_text='Water & Wastewater').get_by_role('button',name='Filter').click()
    assert page.locator('.infra-filter-modal').count()==1
    page.locator('[data-field]').fill('PIPE_DIAMETER')
    page.locator('[data-op]').select_option('>=')
    page.locator('[data-value]').fill('36')
    page.locator('[data-filter-enabled]').check()
    page.locator('[data-filter-save]').click()
    page.wait_for_function('window.__manages.some(x=>x.op==="layer-filter")')
    page.wait_for_function('document.querySelector(".infra-filter-modal")==null')
    page.locator('.infra-category').filter(has_text='Communications').get_by_role('button',name='Symbol').click()
    page.wait_for_function('window.__manages.some(x=>x.op==="layer-symbol")')
    # Search external to viewport merges results in existing sidebar without online requests.
    page.locator('#layerSearch').fill('MAIN')
    page.wait_for_function('document.querySelectorAll(".infra-search-hit-i688").length>0',timeout=5000)
    page.locator('.infra-search-hit-i688').first.click()
    page.wait_for_function('window.__detail?.title==="MAIN_48"',timeout=5000)
    # Rapid A->B->A with deliberately stale B responses: old geometry remains
    # visible while loading and delayed requests cannot overwrite the new viewport.
    page.evaluate("""()=>{
      window.__originalFetch=window.fetch;window.__slow=[];
      window.fetch=async (url,opt)=>{const q=String(url);
        if(q.includes('/features')&&q.includes('-111.250000'))return new Promise(resolve=>window.__slow.push(()=>resolve(window.__originalFetch(url,opt))));
        return window.__originalFetch(url,opt);
      };
      window.__bounds=[-111,30,-110,31];window.map.fire('moveend');
    }""")
    page.wait_for_function('window.__slow.length>=2',timeout=5000)
    assert page.evaluate('window.TakMapInfrastructureI688.state.records.get("stored-pipes").features.length')==1
    page.evaluate('window.__bounds=[-119,34,-118,35];window.map.fire("moveend")')
    page.wait_for_function('window.TakMapInfrastructureI688.state.records.get("stored-pipes").status==="ready"',timeout=5000)
    page.evaluate('window.__slow.forEach(resolve=>resolve());window.__slow=[]')
    page.wait_for_timeout(140)
    assert page.evaluate('window.TakMapInfrastructureI688.state.records.get("stored-pipes").cache[0][0]')==-119.25
    assert page.evaluate('window.TakMapInfrastructureI688.state.records.get("stored-pipes").features.length')==1
    # Startup/viewport cache: no online provider queries despite saved online source enabled.
    assert not any('mode=online' in s for s in page.evaluate('window.__requests'))
    assert not errors,errors
    print('PASS i688 browser',width,'offline sources, selection/details, stable dropdowns, filter, symbol, search')
    page.close()
  finally:browser.close()
if __name__=='__main__':test()
