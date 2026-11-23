"""i689 Chromium: delayed map readiness, direct selection, custom zoom picker and fallback."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from test_i685_infrastructure_browser import ROOT,CORE,OLD_CSS,HTML,CATS
from test_i688_infrastructure_browser import HARNESS
JS=(ROOT/'assets/tak-map-infrastructure-i689.js').read_text()
CSS=(ROOT/'assets/tak-map-infrastructure-i689.css').read_text()

def test():
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  try:
   for width in (1280,390):
    page=browser.new_page(viewport={'width':width,'height':850});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content(HTML)
    for style in (CORE,OLD_CSS,CSS):page.add_style_tag(content=style)
    page.evaluate('(cats)=>window.__cats=cats',[{**x,'hidden_online':0,'hidden_offline':0} for x in CATS])
    page.evaluate(HARNESS)
    # The mock gets the functions required of a real map. Start with DOM#map in window.map.
    page.evaluate('''()=>{
      window.__realMap=window.map;
      window.__realMap.addLayer=function(){};
      window.__realMap.fireWith=function(name,original){for(const fn of this.handlers[name]||[])fn({originalEvent:original})};
      window.map=document.getElementById('map') || document.createElement('div');
      window.takLeafletMap=window.map;
      window.L.divIcon=o=>o;
      // The legacy mock geoJSON never invokes pointToLayer, unlike real Leaflet.
      const oldGeo=window.L.geoJSON;
      window.L.geoJSON=(data,options={})=>oldGeo(data,{...options,onEachFeature:(f,s)=>{
        if(f.geometry?.type==='Point'&&options.pointToLayer){const m=options.pointToLayer(f,[f.geometry.coordinates[1],f.geometry.coordinates[0]]);s.options.icon=m.options.icon;}
        options.onEachFeature?.(f,s);
      }});
      window.__fixture.layers.find(x=>x.id==='stored-tower').point_symbol_mode='registry';
      window.__fixture.layers.find(x=>x.id==='stored-tower').point_symbol_ref={kind:'custom',iconsetpath:'test.png'};
      window.TakMapIconRegistryI572={imageFor(){return '/api/tak-map/icon-registry/icon?path=test.png'}};
    }''')
    page.add_script_tag(content=JS)
    page.wait_for_timeout(1100)
    assert page.evaluate('window.TakMapInfrastructureI689?.state.map') is None
    assert not errors,errors
    # Publishing the valid Leaflet map after DOM is already initialized must recover.
    page.evaluate('window.map=window.__realMap;window.takLeafletMap=window.__realMap;')
    page.wait_for_function('window.TakMapInfrastructureI689?.state?.ready',timeout=8000)
    page.wait_for_function('window.TakMapInfrastructureI689?.state?.records.get("stored-pipes")?.status==="ready"',timeout=8000)
    assert not errors,errors
    assert page.evaluate('window.TakMapInfrastructureI689.state.map===window.__realMap')
    assert page.evaluate('window.__realMap.handlers.click.length')==1
    # Click must be owned by the feature, not immediately cleared by map event bubbling.
    page.evaluate('''()=>{const shape=window.__shapes.find(s=>s.click&&s.options.color==='#66bdd0');
      const click={};shape.click({originalEvent:click});window.__realMap.fireWith('click',click);
      window.__lastClick=click;}''')
    assert page.evaluate('window.__lastClick._infraHandled===true')
    assert page.evaluate('window.TakMapInfrastructureI689.state.selected?.feature?.id')=='pipe-48'
    assert page.evaluate('window.__detail?.title')=='MAIN_48'
    # blank click deselects; subsequent click still works
    page.evaluate("window.__realMap.fireWith('click',{})")
    assert page.evaluate('window.TakMapInfrastructureI689.state.selected') is None
    page.evaluate("window.__shapes.find(s=>s.click&&s.options.color==='#66bdd0').click({originalEvent:{}})")
    assert page.evaluate('window.TakMapInfrastructureI689.state.selected?.feature.id')=='pipe-48'
    assert page.evaluate('window.TakMapInfrastructureI689.state.selection.stroke.options.color')=='#e43b42'
    # Custom registry symbol includes an image-failure fallback while retaining marker selection.
    assert page.evaluate("window.__shapes.some(s=>s.options?.icon?.html?.includes('infra-symbol-fallback-i689'))")
    # The custom listbox is dark and fully controlled (no native <select>).
    btn=page.locator('#takInfraCardI685 .infra-minzoom').first
    assert btn.evaluate('(e)=>e.tagName')=='BUTTON'
    btn.click();lst=page.locator('.infra-zoom-menu-i689');assert lst.count()==1
    assert lst.get_attribute('role')=='listbox'
    assert lst.locator('[role="option"]').count()==24
    assert btn.get_attribute('aria-expanded')=='true'
    assert 'rgb(' in lst.evaluate('(e)=>getComputedStyle(e).backgroundColor')
    page.keyboard.press('Escape');assert lst.count()==0
    assert not page.evaluate('window.__manages.some(x=>x.op==="layer-minzoom")')
    btn.click();lst.get_by_text('z16+',exact=True).click()
    page.wait_for_function('window.__manages.some(x=>x.op==="layer-minzoom"&&x.min_zoom===16)',timeout=4000)
    # Recreating Leaflet must invalidate the old group's completed viewport cache.
    page.evaluate('''()=>{const previous=window.__realMap;
      const replacement={...previous,handlers:{},getZoom:previous.getZoom,getCenter:previous.getCenter,getBounds:previous.getBounds,addLayer(){},removeLayer(g){window.__removed++},on:previous.on,off:previous.off};
      window.map=replacement;window.takLeafletMap=replacement;window.__replacement=replacement;
    }''')
    page.wait_for_function('window.TakMapInfrastructureI689.state.map===window.__replacement',timeout=5000)
    page.wait_for_function('window.TakMapInfrastructureI689.state.records.get("stored-pipes")?.status==="ready"',timeout=5000)
    assert page.evaluate('window.__replacement.handlers.click.length')==1
    assert not errors,errors
    print('PASS i689 browser',width,'map recovery/replacement, owned clicks, icon fallback, dark zoom listbox')
    page.close()
  finally:browser.close()
if __name__=='__main__':test()
