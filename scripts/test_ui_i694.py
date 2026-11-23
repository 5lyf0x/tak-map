#!/usr/bin/env python3
"""Isolated Chromium regression for i694 Blend, radar Soft Pill, and Infrastructure header/order."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]


def check(page, expression, message):
    assert page.evaluate(expression), message

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    for width in (1280, 390):
        page = browser.new_page(viewport={'width': width, 'height': 900})
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.set_content('''<!doctype html><html><body><div id="sidebar">
            <section class="panel" id="basemap-panel"><h2>BASEMAP LAYERS</h2><select id="basemapSelect"><option value="imagery">Imagery</option></select><div id="takBasemapBlendI673"></div></section>
            <section class="panel" id="takVeilCardI665"><h2>XTAK VEIL</h2></section>
            <section class="panel" id="trailing"><h2>Other</h2></section>
            </div></body></html>''')
        page.evaluate("() => Object.defineProperty(window, 'localStorage', {configurable:true, value:{_data:{},getItem(k){return this._data[k]??null},setItem(k,v){this._data[k]=String(v)},removeItem(k){delete this._data[k]}}})")
        page.evaluate('''() => {
          window._trace = []; window._mapLayers = new Set();
          window.config = {basemaps:[{id:'imagery',label:'Imagery',url:'about:blank'},{id:'topo',label:'Topo',url:'about:blank'}],default_basemap:'imagery'};
          window.activeBasemap='imagery'; window.baseLayer=null;
          window.map = {
            _panes: {}, getPane(n){return this._panes[n]||null}, createPane(n){let d=document.createElement('div');return this._panes[n]=d},
            hasLayer(l){return window._mapLayers.has(l)},addLayer(l){window._mapLayers.add(l);window._trace.push('add')},
            removeLayer(l){window._mapLayers.delete(l);window._trace.push('remove')},
            on(){},off(){},getZoom(){return 12},getCenter(){return {lat:34,lng:-119}},
            getBounds(){return {getSouth(){return 33.5},getNorth(){return 34.5},getWest(){return -119.5},getEast(){return -118.5}}}
          };
          const makeLayer = (url,opts)=>({url,options:opts,setOpacity(n){this.options.opacity=n},setZIndex(n){this._z=n},
            addTo(m){m.addLayer(this);return this},getContainer(){return {style:{}}},getTileUrl(){return url}});
          window.L = {tileLayer: makeLayer, TileLayer: {extend: ()=>class {constructor(url,opts){Object.assign(this,makeLayer(url,opts));}}},
            layerGroup(){return {addTo(m){m.addLayer(this);return this}}}};
          window.fetch = async (url)=>({ok:true,json:async()=>({ok:true,categories:[],layers:[],jobs:[]})});
          window.Cesium={SceneMode:{SCENE3D:3}};
          window.terrain3DViewer={entities:{remove(){window._trace.push('entity-remove')}},scene:{mode:2}};
          window.takLeafletMap=window.map;
        }''')
        page.add_script_tag(path=str(ROOT/'assets/tak-map-basemap-stack-i673.js'))
        page.wait_for_function('window.TakMapBaseStackI673?.state?.ready===true',timeout=5000)
        page.add_script_tag(path=str(ROOT/'assets/tak-map-infrastructure-i689.js'))
        page.add_style_tag(path=str(ROOT/'assets/tak-map-infrastructure-i689.css'))
        try:
            page.wait_for_function("document.getElementById('takInfraVisibilityI694')!==null", timeout=4000)
        except Exception:
            print('DEBUG browser errors:', errors)
            print('DEBUG state:', page.evaluate("() => ({infra: !!window.TakMapInfrastructureI689, len: document.body.innerHTML.length, mapValid:!!window.map, sidebar: !!document.querySelector('#sidebar'), loaded: !!document.querySelector('#takInfraCardI685')})"))
            raise
        check(page, "Array.from(document.querySelectorAll('#sidebar>.panel')).slice(0,3).map(x=>x.id).join('|')==='basemap-panel|takInfraCardI685|takVeilCardI665'",'INFRASTRUCTURE not placed between BASEMAP and VEIL')
        # Simulate a third-party reorder, then let the direct-child observer repair it.
        page.evaluate("() => document.getElementById('sidebar').appendChild(document.getElementById('takInfraCardI685'))")
        page.wait_for_function("Array.from(document.querySelectorAll('#sidebar>.panel')).slice(0,3).map(x=>x.id).join('|')==='basemap-panel|takInfraCardI685|takVeilCardI665'")
        # Both installed VEIL scripts have their own placement loops. Run those
        # routines repeatedly to verify they agree with the Infrastructure anchor.
        for veil_name in ('tak-map-veil-i665.js', 'tak-map-veil-i666.js'):
            veil_source=(ROOT/'assets'/veil_name).read_text()
            body=veil_source.split('function place(){',1)[1].split('function pbutton(',1)[0] if veil_name.endswith('i665.js') else veil_source.split('function place(){',1)[1].split('// Other sidebar components',1)[0]
            fn='function place(){'+body
            page.evaluate("() => {const D=document,$=id=>D.getElementById(id);"+fn+"for(let i=0;i<12;i++)place()}")
            check(page,"Array.from(document.querySelectorAll('#sidebar>.panel')).slice(0,3).map(x=>x.id).join('|')==='basemap-panel|takInfraCardI685|takVeilCardI665'",'VEIL script displaced Infrastructure: '+veil_name)
        # Visibility and collapse are independent. A synthetic loaded 2D/3D record gets cleared.
        page.evaluate('''() => {let s=window.TakMapInfrastructureI689.state;
           s.data={categories:[{id:'water',hidden_offline:false}],layers:[{id:'pipes',mode:'offline',category_id:'water',enabled:true,hidden:false,min_zoom:0,kind:'line',feature_count:1}],jobs:[]};s.ready=true;
           s.records.set('pipes',{group:{},entities:[{viewer:window.terrain3DViewer,entity:{}}],epoch:1,features:[],cache:null,status:'ready'});
        }''')
        page.locator('#takInfraVisibilityI694').uncheck()
        check(page,"window.TakMapInfrastructureI689.state.visible===false",'Master visibility did not disable')
        check(page,"window.TakMapInfrastructureI689.state.records.size===0",'Graphics not cleared')
        check(page,"window.TakMapInfrastructureI689.state.data.layers[0].enabled===true",'User layer choice lost')
        check(page,"document.querySelector('#takInfraCardI685 .infra-status').textContent==='HIDDEN'",'Header HIDDEN status missing')
        page.locator('#takInfraCardI685 .infra-chevron-button').click()
        check(page,"window.TakMapInfrastructureI689.state.collapsed===true && window.TakMapInfrastructureI689.state.visible===false",'Collapse toggled master unexpectedly')
        page.locator('#takInfraVisibilityI694').check()
        check(page,"window.TakMapInfrastructureI689.state.visible===true && window.TakMapInfrastructureI689.state.collapsed===true",'Master toggle changed collapse')
        # Blend remains open for all twelve modes, selected highlight follows mode.
        page.locator('#takInfraCardI685 .infra-chevron-button').click()
        page.locator('[data-base-menu-i678="blend:imagery"]').click()
        for mode in ('normal','multiply','screen','overlay','soft-light','hard-light','darken','lighten','difference','map-details','terrain-relief','contour-emphasis'):
            page.locator(f'#takBasemapPopoverI678 [data-mode-i678="{mode}"]').click()
            check(page,f"window.TakMapBaseStackI673.state.blend.imagery==='{mode}'",'Blend did not apply '+mode)
            check(page,"document.querySelector('#takBasemapPopoverI678')!==null",'Blend dropdown closed on '+mode)
            check(page,f"document.querySelector('#takBasemapPopoverI678 [data-mode-i678=\"{mode}\"]').classList.contains('selected')",'Selected highlight missing '+mode)
        # Outside click should close the dropdown.
        page.evaluate("document.querySelector('#trailing').dispatchEvent(new PointerEvent('pointerdown',{bubbles:true}))")
        check(page,"document.querySelector('#takBasemapPopoverI678')===null",'Outside click failed to close Blend')
        assert not errors, errors
        page.close()
    # Radar opacity independently: both active and pending Leaflet and Cesium frames.
    page=browser.new_page()
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content('<!doctype html><html><body><div id="basemapSelect"></div></body></html>')
    page.evaluate("() => Object.defineProperty(window, 'localStorage', {configurable:true, value:{_data:{},getItem(k){return this._data[k]??null},setItem(k,v){this._data[k]=String(v)},removeItem(k){delete this._data[k]}}})")
    page.evaluate('''() => {
      window._requests=[];
      window.map={_panes:{},getPane(n){return this._panes[n]||null},createPane(n){return this._panes[n]=document.createElement('div')},hasLayer(){return false},removeLayer(){}};
      window.L={tileLayer(url,opts){return {url,options:opts,on(){return this},setZIndex(){},addTo(){return this},setOpacity(v){this.alpha=v}}},geoJSON(){return {addTo(){return this}}}};
      window.fetch=async(url)=>{window._requests.push(url);return {ok:true,json:async()=>({ok:true,frame_token:'p1790000200000',provider_id:'nws-time',valid_time_utc:'2026-11-12T23:59:00Z',native_max_zoom:10})}};
    }''')
    page.add_style_tag(content='.tak-soft-pill-i678{width:100%;appearance:none}')
    page.add_script_tag(path=str(ROOT/'assets/tak-map-weather-i693.js'))
    page.locator('#takWeatherRadarI691').check()
    page.wait_for_timeout(150)
    page.evaluate('''() => {
      let s=window.TakMapNativeWeatherI693.state;
      s.radarLayer={setOpacity(x){this.alpha=x}};
      s.radarPendingLayer={setOpacity(x){this.alpha=x}};
      s.cesRadar={alpha:1};s.cesRadarRetiring={alpha:1};
      s.viewer={scene:{requestRender(){window._renderCalls=(window._renderCalls||0)+1}}};
      window._beforeRequests=window._requests.length;
    }''')
    page.locator('#takWeatherOpacitySoftPillI694').fill('74')
    check(page,"document.querySelector('#takWeatherOpacityOutI694').textContent==='74%'",'Radar percent not updated')
    check(page,"document.querySelector('#takWeatherOpacitySoftPillI694').style.getPropertyValue('--tak-soft-pill-pct')==='74%'",'Radar track not updated')
    check(page,"[window.TakMapNativeWeatherI693.state.radarLayer.alpha,window.TakMapNativeWeatherI693.state.radarPendingLayer.alpha,window.TakMapNativeWeatherI693.state.cesRadar.alpha,window.TakMapNativeWeatherI693.state.cesRadarRetiring.alpha].every(x=>Math.abs(x-.74)<.001)",'2D/3D frame alpha mismatch')
    check(page,"window._requests.length===window._beforeRequests",'Opacity adjustment triggered imagery fetch')
    check(page,"document.querySelector('#takWeatherOpacityI691')===null",'Old radar opacity control still present')
    assert not errors,errors
    browser.close()
print('PASS i694 Chromium: 12 Blend modes + outside dismiss; Infrastructure position/recovery/master visibility/collapse; radar Soft Pill/opacity without tile fetch (desktop+narrow)')
