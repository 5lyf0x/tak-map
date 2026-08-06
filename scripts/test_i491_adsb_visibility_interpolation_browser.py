#!/usr/bin/env python3
from __future__ import annotations
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ADSB=ROOT/'assets'/'tak-map-adsb-v491.js'
INTERP=ROOT/'assets'/'tak-map-live-interpolation-v491.js'
HTML='''<!doctype html><html><head><meta charset="utf-8"><base href="http://localhost/"></head><body>
<div class="panel" data-collapse-key="adsbSettings"><div class="panel-body">
<button id="adsbToggleBtn">Disable ADS-B</button><input id="adsbHeaderEnableV476" type="checkbox" checked>
<input id="adsbUpdateInterval" value="1"><input id="adsbRadiusMiles" value="50">
<select id="adsbCenterSource"><option value="follow_map_center" selected>Follow</option></select><input id="adsbCenterLatLon" value="34,-118">
<input id="adsbFilterCivil" type="checkbox" checked><input id="adsbFilterMilitary" type="checkbox" checked><input id="adsbFilterGovt" type="checkbox" checked><input id="adsbFilterUnknown" type="checkbox" checked>
<div id="adsbStatus"></div><div id="adsbSettingsStatus"></div></div></div>
<div id="bannerAdsb"></div><div id="adsbHeaderCountV486"></div><div id="statusDropdown"></div>
<script>
(()=>{
 const store={}; Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>Object.prototype.hasOwnProperty.call(store,k)?store[k]:null,setItem:(k,v)=>store[k]=String(v),removeItem:k=>delete store[k]}});
 localStorage.setItem('takmap.adsb.altitude.mode','all'); localStorage.setItem('takmap.adsb.altitude.thresholdMeters','3048');
 class FakeWorker{constructor(){this.messages=[];this.terminated=false;window.__workers.push(this)}postMessage(m){this.messages.push(m)}terminate(){this.terminated=true}emit(d){if(this.onmessage)this.onmessage({data:d})}}
 window.__workers=[]; window.Worker=FakeWorker; window.URL.createObjectURL=()=>"blob:fake"; window.URL.revokeObjectURL=()=>{}; window.Blob=function(){};
 class Marker{constructor(row){this.row=row;this.ll={lat:Number(row.lat),lng:Number(row.lon)};this.heading=Number(row.track_deg||row.track||0);this._takAdsbId=row.id;this._takAdsbAircraft=row}getLatLng(){return {lat:this.ll.lat,lng:this.ll.lng}}setLatLng(v){this.ll={lat:Number(v[0]??v.lat),lng:Number(v[1]??v.lng)};return this}getElement(){return {querySelector:()=>null}}}
 const layer={removed:[],removeLayer(m){this.removed.push(m._takAdsbId)}};
 const markers=new Map(),data=new Map(); window.TakMapControllers={adsb:{version:'v491',markers,data,layer,tracking:{id:null,layer:null,label:null}}};
 window.drawAircraft=function(rows){const seen=new Set(); for(const r of rows){seen.add(r.id); data.set(r.id,r); let m=markers.get(r.id); if(!m){m=new Marker(r);markers.set(r.id,m)}else{m.row=r;m._takAdsbAircraft=r;m.setLatLng([r.lat,r.lon])}} for(const [id,m] of [...markers])if(!seen.has(id)){layer.removeLayer(m);markers.delete(id)} return rows};
 window.map=window.takLeafletMap={getCenter:()=>({lat:34,lng:-118}),on:()=>{},removeLayer:()=>{}};
 window.lastAdsbSettings={update_interval_seconds:1,stale_seconds:90,center_source:'follow_map_center',radius_miles:50};
 window.__emit=function(worker,seq,rows,snapshotReady=true){const now=Date.now();worker.emit({type:'poll-start',seq,scheduledAt:now,startedAt:now,actualIntervalMs:1000,dispatchLagMs:0,url:'http://localhost/api/tak-map/adsb'});worker.emit({type:'result',seq,startedAt:now,completedAt:now+5,workerMs:5,httpStatus:200,httpOk:true,ok:true,rows,sources:[],snapshotReady,url:'http://localhost/api/tak-map/adsb'})};
})();
</script>
<script src="/assets/runtime/tak-map-live-interpolation-v491.js"></script><script src="/assets/runtime/tak-map-adsb-v491.js"></script>
</body></html>'''

def main()->int:
    chromium=next((n for n in ('chromium','chromium-browser','google-chrome','google-chrome-stable') if shutil.which(n)),None)
    if not chromium:
        print('SKIP: Chromium unavailable'); return 0
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=shutil.which(chromium),args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
        page=browser.new_page(); errors=[]; page.on('pageerror',lambda e:errors.append(str(e)))
        def route(r):
            u=r.request.url
            if u.endswith('/assets/runtime/tak-map-adsb-v491.js'): r.fulfill(status=200,content_type='application/javascript',body=ADSB.read_text())
            elif u.endswith('/assets/runtime/tak-map-live-interpolation-v491.js'): r.fulfill(status=200,content_type='application/javascript',body=INTERP.read_text())
            else: r.fulfill(status=404,body='not found')
        page.route('**/*',route); page.set_content(HTML,wait_until='domcontentloaded')
        page.wait_for_function("window.TakMapAdsbWorkerV476 && window.__workers.length===1",timeout=10000)
        rows1=[{'id':'low','lat':34.0,'lon':-118.0,'alt_ft':5000,'track_deg':90},{'id':'high','lat':35.0,'lon':-117.0,'alt_ft':25000,'track_deg':45}]
        page.evaluate("rows=>__emit(__workers[0],1,rows,true)",rows1); page.wait_for_function("TakMapControllers.adsb.markers.size===2")
        # Altitude filter removes visuals but retains current tracking/interpolation state.
        page.evaluate("()=>{localStorage.setItem('takmap.adsb.altitude.mode','above');localStorage.setItem('takmap.adsb.altitude.thresholdMeters','3048');dispatchEvent(new CustomEvent('takmap:adsb-altitude-filter-change'))}")
        page.wait_for_function("TakMapControllers.adsb.markers.size===1 && !TakMapControllers.adsb.markers.has('low')")
        alt_hidden=page.evaluate("()=>({diag:TakMapAdsbWorkerV476.diagnostics(),raw:TakMapAdsbWorkerV476.rawSnapshot(),virt:TakMapAdsbWorkerV476.virtualSnapshot()})")
        rows2=[{'id':'low','lat':34.2,'lon':-117.8,'alt_ft':6000,'track_deg':100},{'id':'high','lat':35.2,'lon':-116.8,'alt_ft':26000,'track_deg':55}]
        page.evaluate("rows=>__emit(__workers[0],2,rows,true)",rows2); page.wait_for_timeout(350)
        moving1=page.evaluate("()=>TakMapAdsbWorkerV476.virtualSnapshot().find(x=>x.id==='low')")
        page.wait_for_timeout(350)
        moving2=page.evaluate("()=>TakMapAdsbWorkerV476.virtualSnapshot().find(x=>x.id==='low')")
        assert moving2['lat']>moving1['lat'],(moving1,moving2)
        assert page.evaluate("()=>!TakMapControllers.adsb.markers.has('low')")
        # Clearing altitude filter restores at current interpolated pose, then continues to newest target.
        page.evaluate("()=>{localStorage.setItem('takmap.adsb.altitude.thresholdMeters','');dispatchEvent(new CustomEvent('takmap:adsb-altitude-filter-change'))}")
        page.wait_for_function("TakMapControllers.adsb.markers.has('low')")
        restored=page.evaluate("()=>TakMapControllers.adsb.markers.get('low').getLatLng()")
        assert 34.0 < restored['lat'] <= 34.2,restored
        page.wait_for_timeout(500)
        restored_later=page.evaluate("()=>TakMapControllers.adsb.markers.get('low').getLatLng()")
        assert restored_later['lat']>=restored['lat'],(restored,restored_later)
        # Distance exclusion is the only filter that freezes virtual interpolation.
        rows3=[{'id':'low','lat':34.5,'lon':-117.5,'alt_ft':6000,'track_deg':110},{'id':'high','lat':35.4,'lon':-116.6,'alt_ft':26000,'track_deg':60}]
        page.evaluate("rows=>__emit(__workers[0],3,rows,true)",rows3); page.wait_for_timeout(180)
        page.evaluate("rows=>__emit(__workers[0],4,rows,true)",[rows3[1]])
        frozen1=page.evaluate("()=>TakMapAdsbWorkerV476.virtualSnapshot().find(x=>x.id==='low')")
        page.wait_for_timeout(500)
        frozen2=page.evaluate("()=>TakMapAdsbWorkerV476.virtualSnapshot().find(x=>x.id==='low')")
        assert abs(frozen2['lat']-frozen1['lat'])<1e-9,(frozen1,frozen2)
        diag_distance=page.evaluate("()=>TakMapAdsbWorkerV476.diagnostics()")
        assert diag_distance['distanceFilteredRows']==1 and diag_distance['distanceFilterStops']>=1,diag_distance
        # Reentry resumes from newest ADS-B state without replaying stale motion.
        rows4=[{'id':'low','lat':36.0,'lon':-116.0,'alt_ft':6000,'track_deg':120},{'id':'high','lat':35.5,'lon':-116.5,'alt_ft':26000,'track_deg':65}]
        page.evaluate("rows=>__emit(__workers[0],5,rows,true)",rows4); page.wait_for_function("TakMapControllers.adsb.markers.has('low')")
        reentered=page.evaluate("()=>TakMapControllers.adsb.markers.get('low').getLatLng()")
        assert abs(reentered['lat']-36.0)<1e-6,reentered
        # Master disable terminates ingestion/state/rendering; stale worker messages are ignored.
        page.evaluate("()=>TakMapAdsbWorkerV476.disable()")
        page.wait_for_function("TakMapAdsbWorkerV476.diagnostics().enabled===false && TakMapControllers.adsb.markers.size===0")
        disabled=page.evaluate("()=>({diag:TakMapAdsbWorkerV476.diagnostics(),workers:__workers.length,terminated:__workers[0].terminated,raw:TakMapAdsbWorkerV476.rawSnapshot()})")
        page.evaluate("rows=>__emit(__workers[0],6,rows,true)",rows4)
        page.wait_for_timeout(100)
        ignored=page.evaluate("()=>({size:TakMapControllers.adsb.markers.size,state:TakMapAdsbWorkerV476.diagnostics().currentStateSize,ignored:TakMapAdsbWorkerV476.diagnostics().ignoredDisabledWorkerMessages})")
        assert ignored['size']==0 and ignored['state']==0 and ignored['ignored']>=1,ignored
        page.evaluate("()=>TakMapAdsbWorkerV476.enable()")
        page.wait_for_function("__workers.length===2 && TakMapAdsbWorkerV476.diagnostics().enabled===true")
        fresh=[{'id':'low','lat':37.0,'lon':-115.0,'alt_ft':6000,'track_deg':130}]
        page.evaluate("rows=>__emit(__workers[1],7,rows,true)",fresh); page.wait_for_function("TakMapControllers.adsb.markers.has('low')")
        fresh_pose=page.evaluate("()=>TakMapControllers.adsb.markers.get('low').getLatLng()")
        final_diag=page.evaluate("()=>TakMapAdsbWorkerV476.diagnostics()")
        browser.close()
    assert not errors,errors
    assert alt_hidden['diag']['currentStateSize']==2 and alt_hidden['diag']['altitudeFilteredRows']==1,alt_hidden
    assert disabled['terminated'] and disabled['raw']==[] and disabled['diag']['pollingEnabled'] is False,disabled
    assert abs(fresh_pose['lat']-37.0)<1e-6,fresh_pose
    assert final_diag['masterStops']>=1,final_diag
    print('ADS-B visibility/interpolation/master-toggle browser test passed')
    print(json.dumps({'altHidden':alt_hidden['diag'],'moving1':moving1,'moving2':moving2,'restored':restored,'distance':diag_distance,'disabled':disabled,'final':final_diag},sort_keys=True))
    return 0
if __name__=='__main__': raise SystemExit(main())
