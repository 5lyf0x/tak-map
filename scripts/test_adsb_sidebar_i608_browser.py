#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'assets' / 'tak-map-deferred-i553.json'


async def main() -> None:
    manifest=json.loads(MANIFEST.read_text(encoding='utf-8'))
    rows=[row for row in manifest.get('scripts',[]) if row.get('id')=='TakMapAdsbSidebarI608']
    assert len(rows)==1, rows
    code=rows[0]['code']
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            executable_path='/usr/bin/chromium',
            args=['--no-sandbox'],
        )
        page = await browser.new_page(viewport={"width": 1400, "height": 900})
        errors: list[str] = []
        page.on('pageerror', lambda exc: errors.append(str(exc)))
        await page.set_content('''<!doctype html><html><head></head><body style="margin:0">
          <div id="map" style="position:absolute;left:80px;top:70px;width:1240px;height:780px;background:#18232b"></div>
          <div id="floatingToolbarDock" style="position:fixed;right:10px;top:110px;width:54px;height:520px;z-index:2147481000;background:#333"></div>
          <aside id="takMapContextSidebarI572" style="position:fixed;right:76px;top:90px;z-index:9999"></aside>
          <button id="marker-one" style="position:absolute;left:300px;top:300px"><img data-adsb-img="1" src="/assets/adsb/adsb_gov_fixed.png">one</button>
          <button id="marker-two" style="position:absolute;left:500px;top:320px"><img data-adsb-img="1" src="/assets/adsb/adsb_gov_fixed.png">two</button>
          <button id="generic-object" style="position:absolute;left:700px;top:350px">generic</button>
        </body></html>''')
        await page.evaluate('''() => {
          const layers=[];
          const mapNode=document.getElementById('map');
          const map={
            layers,zoom:10,lastPan:null,lastView:null,
            panTo(ll){this.lastPan=ll},
            setView(ll,z){this.lastView=ll;this.zoom=z},
            getZoom(){return this.zoom},
            removeLayer(layer){const i=layers.indexOf(layer);if(i>=0)layers.splice(i,1)},
            hasLayer(layer){return layers.includes(layer)},
            getContainer(){return mapNode},on(){},getBounds(){return {}}
          };
          window.takLeafletMap=window.map=map;
          window.L={
            polyline(latlngs,options){return {latlngs:latlngs.slice(),options,
              addTo(m){if(!m.layers.includes(this))m.layers.push(this);return this},
              setLatLngs(next){this.latlngs=next.slice();return this}}}
          };
          function mk(row,el){
            const events={}; let pos={lat:row.lat,lng:row.lon};
            return {
              _takAdsbAircraft:row,
              getLatLng(){return {...pos}},
              setLatLng(ll){pos={lat:Number(ll[0]),lng:Number(ll[1])}; row.__markerLat=pos.lat;row.__markerLon=pos.lng;return this},
              getElement(){return el},closePopup(){},unbindPopup(){},setIcon(){row.__setIconCount=(row.__setIconCount||0)+1},
              on(type,fn){(events[type]||(events[type]=[])).push(fn)},off(){},
              fire(type,event){for(const fn of events[type]||[])fn(event||{})}
            };
          }
          const one={id:'rotor1',hex:'ROT001',callsign:'RESCUE7',registration:'N700RX',model:'Sikorsky UH-60',category:'A7',lat:34.0,lon:-117.0,alt_baro:1800,gs:110,track:75,baro_rate:100,squawk:'1200',seen:Date.now()/1000,class_key:'govt'};
          const two={id:'fixed2',hex:'FIX002',callsign:'UAL123',registration:'N123TA',model:'Boeing 737-800',category:'A3',lat:35.0,lon:-118.0,alt_baro:34000,gs:443,track:86,baro_rate:640,squawk:'1200',seen:Date.now()/1000,class_key:'civil'};
          const m1=mk(one,document.getElementById('marker-one'));
          const m2=mk(two,document.getElementById('marker-two'));
          const stable=new Map([
            ['rotor1',{id:'rotor1',shape:'fixed',classKey:'govt',lastSeen:Date.now(),iconPath:'/assets/adsb/adsb_gov_fixed.png'}],
            ['fixed2',{id:'fixed2',shape:'fixed',classKey:'civil',lastSeen:Date.now(),iconPath:'/assets/adsb/adsb_civ_fixed.png'}]
          ]);
          window.TakMapControllers={adsb:{markers:new Map([['rotor1',m1],['fixed2',m2]]),data:new Map([['rotor1',one],['fixed2',two]]),lastList:[one,two],stable}};
          window.v320AircraftLayersById={rotor1:m1,fixed2:m2};
          window.lastAircraft=[one,two];
          window.__rows={one,two};window.__markers={m1,m2};
          window.drawAircraft=function(input){if(Array.isArray(input)){window.lastAircraft=input;window.TakMapControllers.adsb.lastList=input;for(const row of input)window.TakMapControllers.adsb.data.set(row.id,row)}};
          window.focusAdsbAircraft=function(){};
          window.__saved=[];
          window.fetch=async function(url,opts){
            if(String(url).includes('/api/tak-map/import')){
              const f=opts.body.get('files');window.__saved.push(JSON.parse(await f.text()));
              return new Response(JSON.stringify({ok:true}),{status:200,headers:{'Content-Type':'application/json'}});
            }
            return new Response(JSON.stringify({ok:true}),{status:200,headers:{'Content-Type':'application/json'}});
          };
          window.refreshLocalData=async()=>({ok:true});window.refreshImports=async()=>({ok:true});
        }''')
        await page.add_script_tag(content=code)
        await page.wait_for_function('window.TakMapAdsbSidebarI608 && window.TakMapAdsbSidebarI608.initialized')
        await page.wait_for_timeout(1200)

        # A7 must override an existing fixed stable classification and map icon.
        await page.click('#marker-one')
        await page.wait_for_selector('#takMapAdsbLeftSidebarI608:not(.hidden)')
        await page.wait_for_timeout(300)
        chip_text = await page.locator('#takMapAdsbLeftSidebarI608 .tak-adsb-i608-chips').inner_text()
        assert 'ROTOR' in chip_text, chip_text
        src = await page.get_attribute('#marker-one img', 'src')
        assert src and src.endswith('/assets/adsb/adsb_gov_helo.png'), src
        stable_shape = await page.evaluate("TakMapControllers.adsb.stable.get('rotor1').shape")
        assert stable_shape == 'helo', stable_shape

        # Left panel must be above the toolbar and actually docked on the left.
        positions = await page.evaluate('''() => {
          const p=document.getElementById('takMapAdsbLeftSidebarI608').getBoundingClientRect();
          const m=document.getElementById('map').getBoundingClientRect();
          return {left:p.left,mapLeft:m.left,z:Number(getComputedStyle(document.getElementById('takMapAdsbLeftSidebarI608')).zIndex),toolbarZ:Number(getComputedStyle(document.getElementById('floatingToolbarDock')).zIndex)};
        }''')
        assert abs(positions['left'] - (positions['mapLeft'] + 12)) < 2, positions
        assert positions['z'] > positions['toolbarZ'], positions

        # Pin left aircraft, then select another aircraft into the independent right panel.
        await page.click('#takMapAdsbLeftSidebarI608 [data-adsb-i608-action="pin"]')
        d = await page.evaluate('TakMapAdsbSidebarI608.diagnostics()')
        assert d['pinned'] and d['leftId'] == 'rotor1', d
        await page.click('#marker-two')
        await page.wait_for_selector('#takMapAdsbRightSidebarI608:not(.hidden)')
        d = await page.evaluate('TakMapAdsbSidebarI608.diagnostics()')
        assert d['leftId'] == 'rotor1' and d['rightId'] == 'fixed2' and d['pinned'], d
        right_text = await page.locator('#takMapAdsbRightSidebarI608').inner_text()
        assert 'UAL123' in right_text and 'FIXED-WING' in right_text, right_text

        # A generic map click must not close the pinned left aircraft.
        await page.click('#generic-object')
        await page.wait_for_timeout(100)
        d = await page.evaluate('TakMapAdsbSidebarI608.diagnostics()')
        assert d['pinned'] and d['leftId'] == 'rotor1' and d['leftPanelVisible'] and not d['rightPanelVisible'] and d['rightId'] == '', d

        # Track the pinned aircraft and prove the background worker advances hidden-tab pose/trail state.
        await page.click('#takMapAdsbLeftSidebarI608 [data-adsb-i608-action="track"]')
        await page.evaluate('''() => {
          Object.defineProperty(document,'hidden',{configurable:true,get(){return true}});
          Object.defineProperty(document,'visibilityState',{configurable:true,get(){return 'hidden'}});
          document.dispatchEvent(new Event('visibilitychange'));
          const r=window.__rows.one;r.lat=34.04;r.lon=-117.04;r.track=100;r.seen=Date.now()/1000;
          window.drawAircraft([r,window.__rows.two]);
        }''')
        await page.wait_for_timeout(2200)
        hidden_state = await page.evaluate('''() => ({
          d:TakMapAdsbSidebarI608.diagnostics(),
          lat:window.__rows.one.__markerLat,
          lon:window.__rows.one.__markerLon
        })''')
        assert hidden_state['d']['backgroundTicks'] >= 2, hidden_state
        assert hidden_state['d']['backgroundSamples'] >= 1, hidden_state
        assert hidden_state['d']['leftTrailPoints'] >= 2, hidden_state
        assert hidden_state['lat'] is not None and hidden_state['lat'] > 34.0, hidden_state

        # Save full trail, continue tracking, and save again with full cumulative history.
        await page.evaluate('''() => {
          Object.defineProperty(document,'hidden',{configurable:true,get(){return false}});
          Object.defineProperty(document,'visibilityState',{configurable:true,get(){return 'visible'}});
          document.dispatchEvent(new Event('visibilitychange'));
        }''')
        await page.click('#takMapAdsbLeftSidebarI608 [data-adsb-i608-action="save"]')
        await page.wait_for_selector('#takAdsbSaveDialogI608')
        await page.click('#takAdsbSaveDialogI608 [data-save-act="save"]')
        await page.wait_for_function('window.__saved.length === 1')
        await page.wait_for_timeout(900)
        first = await page.evaluate('TakMapAdsbSidebarI608.diagnostics()')
        first_count = await page.evaluate('window.__saved[0].features[0].geometry.coordinates.length')
        assert first_count == first['leftLastSavedPointCount'] <= first['leftTrailPoints'], (first_count, first)
        assert 'rotor1' in first['trackingIds'], first

        await page.evaluate('''() => {
          const r=window.__rows.one;r.lat=34.08;r.lon=-117.08;r.track=115;r.seen=Date.now()/1000;
          window.drawAircraft([r,window.__rows.two]);
        }''')
        await page.wait_for_timeout(1200)
        await page.click('#takMapAdsbLeftSidebarI608 [data-adsb-i608-action="save"]')
        await page.wait_for_selector('#takAdsbSaveDialogI608')
        await page.click('#takAdsbSaveDialogI608 [data-save-act="save"]')
        await page.wait_for_function('window.__saved.length === 2')
        await page.wait_for_timeout(800)
        second = await page.evaluate('TakMapAdsbSidebarI608.diagnostics()')
        second_count = await page.evaluate('window.__saved[1].features[0].geometry.coordinates.length')
        assert second_count == second['leftLastSavedPointCount'] <= second['leftTrailPoints'], (second_count, second)
        assert second_count > first_count, (first_count, second_count)
        assert 'rotor1' in second['trackingIds'], second

        assert not errors, errors
        await browser.close()

    print('i608 ADS-B sidebar/browser test passed')


if __name__ == '__main__':
    asyncio.run(main())
