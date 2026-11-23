#!/usr/bin/env python3
"""Headless Chromium fixture: i692 UI, same-origin URLs, 2D/3D, toggles, alerts."""
from pathlib import Path
from playwright.sync_api import sync_playwright

root = Path(__file__).resolve().parents[1]
js = root/'assets/tak-map-weather-i692.js'
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
    page = browser.new_page()
    page.set_content('<!doctype html><html><body><div id="basemapSelect"></div></body></html>')
    page.evaluate('''() => {
      window._seen=[];
      window._layers=new Set();
      window.map={
        _panes:{},
        getPane(id){return this._panes[id]||null},
        createPane(id){const pane=document.createElement('div');this._panes[id]=pane;return pane},
        hasLayer(l){return window._layers.has(l)},
        removeLayer(l){window._layers.delete(l)}
      };
      window.L={
        tileLayer(url,opt){
          const l={url,options:opt,events:{},on(ev,cb){this.events[ev]=cb;return this},
          addTo(m){window._layers.add(this);window._seen.push(['tile',url,opt.maxNativeZoom]);if(this.events.tileload)setTimeout(()=>this.events.tileload(),0);return this},
          setOpacity(v){this.options.opacity=v}}
          return l;
        },
        geoJSON(data,opt){return {data,options:opt,addTo(m){window._layers.add(this);return this}}},
        DomEvent:{stopPropagation(){}}
      };
      window.fetch = async (url)=>{
         window._seen.push(['fetch',url]);
         if(url.includes('/status-i692')) return {ok:true,json:async()=>({ok:true,provider_id:'nws-time',service_state:'checking',frame_token:'p1790000300000',valid_time_utc:'2026-11-12T23:59:00Z',native_max_zoom:10})};
         if(url.includes('/alerts-i691')) return {ok:true,json:async()=>({type:'FeatureCollection',features:[{type:'Feature',geometry:null,properties:{event:'No geometry'}}]})};
         return {ok:false,status:404};
      };
      window.Cesium={
        WebMercatorTilingScheme:class {},
        UrlTemplateImageryProvider:class {constructor(config){this.config=config;window._seen.push(['3d',config.url,config.maximumLevel])}},
        GeoJsonDataSource:{load:async()=>({})},
        Color:{ORANGE:{withAlpha(){return {}}}}
      };
      window.terrain3DActive=false;
      window.terrain3DViewer={
        imageryLayers:{_layers:new Set(),addImageryProvider(p){const l={provider:p,alpha:1};this._layers.add(l);return l},remove(l){this._layers.delete(l)},contains(l){return this._layers.has(l)}},
        dataSources:{add:async(s)=>s,remove(){}},
      };
    }''')
    page.add_script_tag(path=str(js))
    page.wait_for_timeout(200)
    assert page.locator('#takNativeWeatherI691').count() == 1
    assert not page.locator('#takWeatherRadarI691').is_checked()
    page.locator('#takWeatherRadarI691').check()
    page.wait_for_timeout(200)
    seen = page.evaluate('window._seen')
    assert any(x[0]=='fetch' and x[1]=='/api/tak-map/weather/radar/status-i692' for x in seen), seen
    assert any(x[0]=='tile' and x[1].startswith('/api/tak-map/weather/radar/tile-i692/') and 'frame=p1790000300000' in x[1] for x in seen), seen
    assert all('nowcoast.noaa.gov' not in str(x) and 'mapservices.weather.noaa.gov' not in str(x) for x in seen)
    assert 'Radar ready' in page.locator('#takWeatherRadarStatusI691').inner_text()
    page.locator('#takWeatherOpacityI691').fill('94')
    assert page.locator('#takWeatherOpacityOutI691').inner_text() == '94%'
    page.locator('#takWeatherAlertsI691').check()
    page.wait_for_timeout(100)
    assert 'without geometry' in page.locator('#takWeatherAlertStatusI691').inner_text()
    page.evaluate('window.terrain3DActive=true;')
    page.wait_for_timeout(2300)
    seen = page.evaluate('window._seen')
    assert any(x[0]=='3d' and x[1].startswith('/api/tak-map/weather/radar/tile-i692/') for x in seen), seen
    page.locator('#takWeatherRadarI691').uncheck()
    assert page.locator('#takWeatherAlertsI691').is_checked()
    assert page.evaluate('window.TakMapNativeWeatherI692.state.cesRadar===null')
    assert page.evaluate('window.TakMapNativeWeatherI692.state.opacity') == 94
    browser.close()
print('PASS: Chromium weather UI, independent alerts, same-origin 2D/3D, opacity, toggle')
