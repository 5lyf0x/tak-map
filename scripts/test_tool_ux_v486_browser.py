#!/usr/bin/env python3
from __future__ import annotations
import json, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ASSET=ROOT/'assets'/'tak-map-tool-ux-v491.js'

def main()->int:
    chromium=next((n for n in ('chromium','chromium-browser','google-chrome','google-chrome-stable') if shutil.which(n)),None)
    if not chromium:
        print('SKIP: Chromium unavailable');return 0
    html='''<!doctype html><html><head><meta charset="utf-8"></head><body>
    <aside class="sidebar">
      <input id="layerSearch"><div id="mapStatus">Ready</div>
      <div class="panel collapsible" id="basemapPanel"><h2>Basemap <span class="panel-toggle">▾</span></h2><div class="panel-body"><select id="basemapSelect"><option>Topo</option></select></div></div>
    </aside>
    <div id="map" class="leaflet-container"></div>
    <div id="routeMiniToolbar"><button title="Undo Last Point">Undo</button><button title="Clear Route">Clear</button><button title="Cancel" onclick="setActiveMapTool('move')">Cancel</button></div>
    <div id="routeEditPanel" class="active"></div>
    <input id="routeColorInput" type="color" value="#ff6f2e"><input id="measureLineColorInput" type="color" value="#b9c4c9"><select id="routeStyleInput"><option value="solid" selected>Solid</option><option value="dashed">Dashed</option></select>
    <script>
    var activeMapTool='move';
    window.v233RouteState={points:[],layer:null,hitLayer:null,color:'#ff6f2e',style:'solid'};
    var measurePoints=[],measureLocked=false,measureUnitsMode='all',measureLineColor='#b9c4c9',measureTextColor='#c6d0d5';
    window.measureLayer={removed:[],removeLayer(layer){this.removed.push(layer);if(layer)layer.removed=true},clearLayers(){}};
    const handlers={};
    window.map=window.takLeafletMap={
      on(name,fn){(handlers[name]=handlers[name]||[]).push(fn);return this},
      emit(name,payload){(handlers[name]||[]).forEach(fn=>fn(payload||{}))},
      getContainer(){return document.getElementById('map')},
      _panes:{},getPane(name){return this._panes[name]||null},createPane(name){const pane=document.createElement('div');pane.className='leaflet-pane';document.getElementById('map').appendChild(pane);this._panes[name]=pane;return pane},
      removeLayer(layer){if(layer)layer.removed=true},
      distance(a,b){const dx=Number(a.lat)-Number(b.lat),dy=Number(a.lng)-Number(b.lng);return Math.sqrt(dx*dx+dy*dy)*100000}
    };
    window.L={
      polyline(points,opts){return {kind:'polyline',points,opts,removed:false,addTo(target){this.target=target;return this},setLatLngs(v){this.points=v;return this},setStyle(v){this.opts=Object.assign({},this.opts,v);return this},remove(){this.removed=true}}},
      marker(point,opts){return {kind:'marker',point,opts,removed:false,addTo(target){this.target=target;return this},remove(){this.removed=true}}},
      divIcon(opts){return opts},
      latLng(lat,lng){return {lat,lng}}
    };
    window.setActiveMapTool=function(tool){activeMapTool=tool||'move';window.activeMapTool=activeMapTool;return activeMapTool};
    window.toggleMapTool=function(tool){return setActiveMapTool(activeMapTool===tool?'move':tool)};
    window.v233RouteMapClick=function(ll){v233RouteState.points.push(ll)};
    window.v233UndoRoute=function(){v233RouteState.points.pop()};
    window.v233ClearRoute=function(){v233RouteState.points=[]};
    window.v233FinishRoute=function(){v233RouteState.points=[];setActiveMapTool('move')};
    window.v233StartDraw=function(){setActiveMapTool('draw')};
    window.measureAddPoint=function(ll){measurePoints.push(ll)};
    window.measureUndo=function(){measurePoints.pop()};
    window.measureClear=function(){measurePoints=[];measureLocked=false};
    window.measureLock=function(){measureLocked=true};
    window.measureResume=function(){measureLocked=false};
    window.measureUnitsToggle=function(){};
    window.setMeasureLineColor=function(v){measureLineColor=v};
    window.setMeasureTextColor=function(v){measureTextColor=v};
    window.fmtDistance=function(m){return Math.round(m)+' m'};
    </script>
    </body></html>'''
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=shutil.which(chromium),args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
        page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content(html,wait_until='domcontentloaded')
        page.add_script_tag(content=ASSET.read_text())
        page.wait_for_function('window.TakMapToolUxV486 && window.TakMapToolUxV486.diagnostics().routeCancelInstalled',timeout=5000)
        result=page.evaluate('''async()=>{
          const tick=()=>new Promise(r=>setTimeout(r,30));
          const mapEl=document.getElementById('map'),status=document.getElementById('mapStatus');
          setActiveMapTool('pointdropper');await tick();const pointCross=mapEl.classList.contains('tak-create-crosshair-v491');
          setActiveMapTool('draw');await tick();const drawCross=mapEl.classList.contains('tak-create-crosshair-v491');
          setActiveMapTool('measure');await tick();const measureCross=mapEl.classList.contains('tak-create-crosshair-v491');
          measureAddPoint({lat:34,lng:-118});map.emit('mousemove',{latlng:{lat:34.001,lng:-118.002}});await tick();
          const md=TakMapToolUxV486.diagnostics();const measurePreview=md.measurePreviewActive&&md.measurePreviewHaloActive&&md.measurePreviewLabelActive;
          measureLayer.clearLayers();const afterLegacyClear=TakMapToolUxV486.diagnostics();const previewLineDashed=afterLegacyClear.measurePreviewDashArray==='10 8'&&afterLegacyClear.measurePreviewDirectMap&&!afterLegacyClear.measurePreviewInMeasureLayer&&afterLegacyClear.measurePreviewActive;
          setActiveMapTool('draw');await tick();const switchClearedMeasure=measurePoints.length===0&&!TakMapToolUxV486.diagnostics().measurePreviewActive;
          setActiveMapTool('measure');measureAddPoint({lat:35,lng:-117});map.emit('mousemove',{latlng:{lat:35.002,lng:-117.002}});await tick();
          document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true,cancelable:true}));await tick();
          const escapeClearedMeasure=measurePoints.length===0&&!TakMapToolUxV486.diagnostics().measurePreviewActive&&activeMapTool==='measure';
          const color=document.getElementById('measureLineColorInput');color.click();await tick();const pickerOpened=!!document.getElementById('takMapColorPickerV486');const swatch=document.querySelector('#takMapColorPickerV486 [data-color="#2386ff"]');swatch.click();await tick();const colorClosed=pickerOpened&&!document.getElementById('takMapColorPickerV486')&&color.value.toLowerCase()==='#2386ff';
          setActiveMapTool('route');v233RouteMapClick({lat:34,lng:-118});map.emit('mousemove',{latlng:{lat:34.1,lng:-118.1}});await tick();
          const routeCross=mapEl.classList.contains('tak-create-crosshair-v491');const previewBefore=TakMapToolUxV486.diagnostics().routePreviewActive;
          v233RouteMapClick({lat:34.2,lng:-118.2});map.emit('mousemove',{latlng:{lat:34.3,lng:-118.3}});await tick();const previewAfter=TakMapToolUxV486.diagnostics().routePreviewActive;
          const cancel=document.querySelector('.tak-route-cancel-v491');const clear=document.querySelector('.tak-route-clear-v491');cancel.click();await tick();
          const cancelCleared=v233RouteState.points.length===0&&activeMapTool==='move'&&!mapEl.classList.contains('tak-create-crosshair-v491')&&!TakMapToolUxV486.diagnostics().routePreviewActive&&!document.getElementById('routeEditPanel').classList.contains('active');
          return {pointCross,drawCross,measureCross,measurePreview,previewLineDashed,switchClearedMeasure,escapeClearedMeasure,colorClosed,routeCross,previewBefore,previewAfter,cancelCleared,cancelTitle:cancel.title,cancelAria:cancel.getAttribute('aria-label'),clearTitle:clear&&clear.title,statusHidden:status.hidden&&getComputedStyle(status).display==='none',noLegacyPrecacheApi:!Object.hasOwn(TakMapToolUxV486,'repairBasemapPrecache'),diagnostics:TakMapToolUxV486.diagnostics()}
        }''')
        browser.close()
    if errors: raise AssertionError(errors)
    assert result['pointCross'] and result['drawCross'] and result['measureCross'] and result['routeCross'],result
    assert result['measurePreview'] and result['previewLineDashed'],result
    assert result['switchClearedMeasure'] and result['escapeClearedMeasure'],result
    assert result['colorClosed'],result
    assert result['previewBefore'] and result['previewAfter'],result
    assert result['cancelCleared'],result
    assert 'discard' in result['cancelTitle'].lower() and 'exit' in result['cancelAria'].lower(),result
    assert 'start over' in (result['clearTitle'] or '').lower(),result
    assert result['statusHidden'],result
    assert result['noLegacyPrecacheApi'],result
    print('Tool UX and Measure preview i491 browser test passed')
    print(json.dumps(result,sort_keys=True))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
