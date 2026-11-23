"""Chromium regression: selecting modes below the scroll fold updates the visible label, layer and storage."""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'assets/tak-map-basemap-stack-i673.js').read_text()
html='''<!doctype html><html><head><meta charset="utf-8"></head>
<body style="background:#152733;color:white;font:12px Arial;margin:0">
<div id="map" style="position:absolute;width:520px;height:520px;left:0;top:0"></div>
<div style="position:absolute;left:530px;width:260px"><select id="basemapSelect"><option value="imagery">Imagery</option>
<option value="topo">Topo</option></select></div></body></html>'''
init=r'''
window.__fakeStorage=window.__fakeStorage||{};
Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>window.__fakeStorage[k]??null,setItem:(k,v)=>window.__fakeStorage[k]=String(v)}});
window.config={basemaps:[{id:'imagery',label:'ESRI World Imagery',url:'imagery'},
{id:'topo',label:'ESRI World Topographic',url:'topo'}],default_basemap:'imagery'};
window.activeBasemap='imagery';window.saveBasemap=async()=>({ok:true});
const panes={},members=new Set(),parent=document.getElementById('map');
window.map={getPane:n=>panes[n]||null,createPane:n=>{let p=document.createElement('div');panes[n]=p;parent.append(p);return p},
addLayer:l=>{members.add(l);l._el=document.createElement('div');l._el.style.opacity=l.options.opacity??1;l._el.style.mixBlendMode='normal';l._el.style.filter='';l._el.style.zIndex=l._zi||0;panes[l.options.pane||'tilePane'].append(l._el);return map},
hasLayer:l=>members.has(l),removeLayer:l=>{members.delete(l);l._el?.remove();return map}};
map.createPane('tilePane');
class Layer{
constructor(url,options){this._url=url;this.options={...options};this._zi=0}
addTo(map){map.addLayer(this);return this}
setOpacity(value){this.options.opacity=value;if(this._el)this._el.style.opacity=value;return this}
setZIndex(value){this._zi=value;if(this._el)this._el.style.zIndex=value;return this}
getContainer(){return this._el}
}
window.L={tileLayer:(url,options)=>new Layer(url,options),TileLayer:{extend:()=>class extends Layer {}}};
window.baseLayer=L.tileLayer('legacy',{pane:'tilePane'}).addTo(map);
'''

def setup(browser, saved=None):
    page=browser.new_page(viewport={'width':850,'height':620})
    page.set_content(html)
    page.evaluate('window.__fakeStorage = '+__import__('json').dumps(saved or {})+';')
    page.evaluate(init)
    page.evaluate(source)
    page.wait_for_function('window.TakMapBaseStackI673 && TakMapBaseStackI673.state.ready')
    return page

def check_mode(page,mode,label):
    opener=page.locator('[data-base-menu-i678="blend:imagery"]')
    # Test both the closed-menu case and the still-open custom-controls case.
    if page.locator('#takBasemapPopoverI678').count()==0:
        opener.click()
    selected=page.locator(f'#takBasemapPopoverI678 [data-mode-i678="{mode}"]')
    selected.scroll_into_view_if_needed()
    selected.click()
    assert page.evaluate('TakMapBaseStackI673.state.blend.imagery')==mode
    assert page.evaluate('TakMapBaseStackI673.state.layers.get("imagery")._takMode')==mode
    assert opener.locator('span').inner_text()==label
    assert opener.get_attribute('title')=='Blend: '+label
    assert page.evaluate('JSON.parse(localStorage.getItem("takmap.basemap.blend.i673.v1")).blend.imagery')==mode
    if page.locator('#takBasemapPopoverI678').count()==0:opener.click()
    assert page.locator(f'[data-mode-i678="{mode}"]').get_attribute('class')=='selected'
    # UI must remain usable when selecting a lower option.
    assert page.locator('#takBasemapPopoverI678').is_visible()
    page.keyboard.press('Escape')

if __name__=='__main__':
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        try:
            page=setup(browser)
            check_mode(page,'screen','Screen')
            check_mode(page,'hard-light','Hard Light')
            check_mode(page,'difference','Difference')
            check_mode(page,'map-details','Map Details')
            check_mode(page,'terrain-relief','Terrain Relief')
            check_mode(page,'contour-emphasis','Contour Emphasis')
            saved=page.evaluate('window.__fakeStorage')
            page.close()
            restored=setup(browser,saved)
            assert restored.locator('[data-base-menu-i678="blend:imagery"] span').inner_text()=='Contour Emphasis'
            assert restored.evaluate('TakMapBaseStackI673.state.blend.imagery')=='contour-emphasis'
            check_mode(restored,'normal','Normal')
            restored.close()
            print('PASS: 7 blend-mode selections incl. lower options, label, render mode, persisted storage and reopen')
        finally:browser.close()
