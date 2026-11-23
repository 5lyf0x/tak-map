#!/usr/bin/env python3
"""i693 browser integration fixture: missing tiles, recovery, frame swapping, 3D, alerts."""
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 page=browser.new_page()
 errors=[]
 page.on('pageerror',lambda e:errors.append(str(e)))
 page.set_content('<!doctype html><html><body><div id="basemapSelect"></div></body></html>')
 page.evaluate('''() => {
 window._events=[];window._layers=new Set();window._frame='p1790000200000';window._alerts=0;
 window.map={_panes:{},getPane(k){return this._panes[k]},createPane(k){return this._panes[k]=document.createElement('div')},
  hasLayer(l){return window._layers.has(l)},removeLayer(l){window._layers.delete(l);window._events.push(['remove',l._takToken||'alert'])}};
 window.L={tileLayer(url,options){
   const layer={url,options,events:{},setZIndex(n){this._z=n},getTileUrl(c){return this.url.replace('{z}',c.z).replace('{x}',c.x).replace('{y}',c.y)},
    on(k,fn){this.events[k]=fn;return this},
    addTo(m){window._layers.add(this);window._events.push(['add',this._takToken]);
      for(let i=0;i<3;i++){
        const c={z:9,x:85+i,y:206};const tile={};let src='';
        Object.defineProperty(tile,'src',{get(){return src},set(v){src=v;setTimeout(()=>layer.events.tileload?.({coords:c,tile}),15)}});
        setTimeout(()=>{layer.events.tileloadstart?.({coords:c,tile});
          if(i===2&&this._takToken==='p1790000200000')layer.events.tileerror?.({coords:c,tile});
          else layer.events.tileload?.({coords:c,tile});
        },15+i*8);
      }
      // i696 handoff waits for the Leaflet viewport-batch 'load' event;
      // the previous fixture omitted that event, which falsely held a frame.
      setTimeout(()=>layer.events.load?.(),this._takToken==='p1790000200000'?1480:140);
      return this;
    },
    setOpacity(v){this.options.opacity=v}};
   return layer;
  },
  geoJSON(data,options){return {options,data,addTo(m){window._layers.add(this);return this}}},DomEvent:{stopPropagation(){}}};
 window.fetch=async(url)=>{window._events.push(['fetch',url]);
   if(url.includes('status-i693'))return {ok:true,json:async()=>({ok:true,provider_id:'nws-time',service_state:'ready',frame_token:window._frame,frame_source:'catalog_observation',valid_time_utc:'2026-11-12T23:59:00Z',native_max_zoom:10})};
   if(url.includes('alerts-i691')){window._alerts++;return {ok:true,json:async()=>({type:'FeatureCollection',features:[{type:'Feature',geometry:null,properties:{event:'No geometry'}}]})}};
   return {ok:false,status:404};
 };
 window.Cesium={WebMercatorTilingScheme:class{},UrlTemplateImageryProvider:class{constructor(v){this.config=v;window._events.push(['3d',v.url])}},
 GeoJsonDataSource:{load:async()=>({})},Color:{ORANGE:{withAlpha(){return {}}}}};
 window.terrain3DActive=false;
 window.terrain3DViewer={imageryLayers:{_layers:new Set(),addImageryProvider(p){const l={provider:p,alpha:1};this._layers.add(l);return l},
  remove(l){this._layers.delete(l)},contains(l){return this._layers.has(l)}},dataSources:{add:async(s)=>s,remove(){}}};
 }''')
 page.add_script_tag(path=str(root/'assets/tak-map-weather-i693.js'))
 assert page.locator('#takNativeWeatherI691').count()==1
 page.locator('#takWeatherRadarI691').check()
 page.wait_for_timeout(160)
 assert page.evaluate('window.TakMapNativeWeatherI693.state.radarToken')=='p1790000200000'
 assert 'Radar recovering' in page.locator('#takWeatherRadarStatusI691').inner_text(),page.locator('#takWeatherRadarStatusI691').inner_text()
 page.wait_for_timeout(1600)
 assert 'Radar ready · 3/3' in page.locator('#takWeatherRadarStatusI691').inner_text(),page.locator('#takWeatherRadarStatusI691').inner_text()
 page.locator('#takWeatherOpacitySoftPillI694').fill('94')
 assert page.locator('#takWeatherOpacityOutI694').inner_text()=='94%'
 page.locator('#takWeatherAlertsI691').check();page.wait_for_timeout(120)
 assert 'without geometry' in page.locator('#takWeatherAlertStatusI691').inner_text()
 page.evaluate("window._frame='p1790000500000'")
 page.evaluate('window.TakMapNativeWeatherI693.refreshRadar()')
 page.wait_for_timeout(180)
 assert page.evaluate('window.TakMapNativeWeatherI693.state.radarPendingLayer !== null')
 assert page.evaluate('window.TakMapNativeWeatherI693.state.radarLayer._takToken')=='p1790000200000'
 page.wait_for_timeout(2200)
 assert page.evaluate('window.TakMapNativeWeatherI693.state.radarPendingLayer===null')
 assert page.evaluate('window.TakMapNativeWeatherI693.state.radarLayer._takToken')=='p1790000500000'
 page.evaluate('window.terrain3DActive=true')
 page.wait_for_timeout(2250)
 assert page.evaluate('window.TakMapNativeWeatherI693.state.cesRadar !== null')
 assert any(row[0]=='3d' for row in page.evaluate('window._events'))
 page.locator('#takWeatherRadarI691').uncheck()
 assert page.evaluate('window.TakMapNativeWeatherI693.state.cesRadar===null')
 assert page.locator('#takWeatherAlertsI691').is_checked()
 assert page.evaluate('window.TakMapNativeWeatherI693.state.opacity')==94
 assert all('mapservices.weather.noaa.gov' not in str(row) for row in page.evaluate('window._events'))
 assert not errors,errors
 browser.close()
print('PASS i693 Chromium: per-tile retry, viewport status, preserved frame, 2D/3D, alerts and opacity')
