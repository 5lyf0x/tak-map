#!/usr/bin/env python3
from __future__ import annotations
import json,re,runpy,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main()->int:
 c=next((n for n in ('chromium','chromium-browser','google-chrome','google-chrome-stable') if shutil.which(n)),None)
 if not c: print('SKIP: Chromium unavailable');return 0
 helper=runpy.run_path(str(ROOT/'scripts'/'test_full_page_responsiveness_v486.py'));html=helper['self_contained_html']()
 asset=(ROOT/'assets'/'tak-map-adsb-v491.js').read_text()
 html=re.sub(r'<script id="takMapAdsbWorkerI463"[^>]*src="/assets/runtime/tak-map-adsb-v491\.js[^"]*"[^>]*></script>',lambda _:'<script id="takMapAdsbWorkerI463">\n'+asset+'\n</script>',html,count=1)
 from playwright.sync_api import sync_playwright
 with sync_playwright() as pw:
  b=pw.chromium.launch(headless=True,executable_path=shutil.which(c),args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage']);p=b.new_page(viewport={'width':1440,'height':1000});errs=[];p.on('pageerror',lambda e:errs.append(str(e)));p.set_content(html,wait_until='domcontentloaded',timeout=20000);p.wait_for_function("window.TakMapControllers && window.TakMapControllers.adsb && typeof window.drawAircraft==='function' && window.TakMapAdsbWorkerV477",timeout=18000);p.wait_for_timeout(3500)
  rows=[{'id':'civil-low','lat':34.0,'lon':-118.0,'alt_ft':5000,'category_class':'civil','description':'CIVIL','callsign':'LOW'},{'id':'gov-high','lat':34.2,'lon':-117.8,'alt_ft':25000,'category_class':'govt','description':'GOVERNMENT','is_govt':True,'callsign':'HIGH'}]
  first=p.evaluate("""async rows=>{
    const api=window.TakMapAdsbWorkerV477||window.TakMapAdsbWorkerV476;api&&api.stop&&api.stop();
    const m=L.map(document.getElementById('map'));window.map=m;window.takLeafletMap=m;
    const baseMarker=L.marker;
    L.marker=function(coords,opts){
      const mk=baseMarker(coords,opts),events={};let popup=null,opened=false;
      mk.on=function(name,fn,ctx){(events[name]||(events[name]=[])).push({fn,ctx:ctx||mk});mk._events=events;return mk};
      mk.off=function(name,fn,ctx){if(!name){Object.keys(events).forEach(k=>delete events[k]);return mk}const a=events[name]||[];events[name]=a.filter(x=>!((!fn||x.fn===fn)&&(!ctx||x.ctx===ctx)));return mk};
      mk.fire=function(name,data){for(const x of (events[name]||[]).slice())x.fn.call(x.ctx||mk,data||{});return mk};
      mk.bindPopup=function(content,options){
        popup={content,options:Object.assign({},options||{}),_source:mk,_open:false,_el:document.createElement('div'),getContent(){return this.content},setContent(v){this.content=v;return this},getElement(){return this._el},isOpen(){return this._open}};
        mk._openPopup=function(ev){if(opened)mk.closePopup();else mk.openPopup(ev&&ev.latlng)};
        mk.on('click',mk._openPopup,mk);
        TakMapPopupLifecycleV463.registerPopupLayer(mk);
        return mk
      };
      mk.getPopup=()=>popup;
      mk.setPopupContent=v=>{if(popup)popup.content=v;return mk};
      mk.openPopup=function(at){if(!popup)return mk;opened=true;popup._open=true;m._popup=popup;mk.fire('popupopen',{popup,latlng:at});m.fire('popupopen',{popup});return mk};
      mk.closePopup=function(){if(!popup||!opened)return mk;opened=false;popup._open=false;mk.fire('popupclose',{popup});m.fire('popupclose',{popup});if(m._popup===popup)m._popup=null;return mk};
      mk.isPopupOpen=()=>opened;
      return mk
    };
    window.__takMapAllowExternalAdsbDraw=true;window.__takMapAdsbOwnerRendering=TakMapControllers.adsb.version;
    const out=window.drawAircraft(rows);
    delete window.__takMapAdsbOwnerRendering;window.__takMapAllowExternalAdsbDraw=false;
    const mk=TakMapControllers.adsb.markers.get('civil-low')||[...TakMapControllers.adsb.markers.values()][0];
    if(!mk)return {missing:true,out:out.map(x=>x.id),markers:[...TakMapControllers.adsb.markers.keys()]};
    const oe={};mk.fire('click',{latlng:L.latLng(34,-118),originalEvent:oe});
    if(!oe._stopped)m.fire('click',{originalEvent:oe,sourceTarget:mk,propagatedFrom:mk});
    await new Promise(r=>setTimeout(r,40));
    const listeners=(mk._events&&mk._events.click)||[];
    return {out:out.map(x=>x.id),markers:[...TakMapControllers.adsb.markers.keys()],first_click:{open:mk.isPopupOpen(),pinned:mk._takPopupPinned===true,stopped:!!oe._stopped,defaultToggle:listeners.some(x=>x.fn===mk._openPopup),openAfter:mk.isPopupOpen()}}
  }""",rows)
  first_click=first.pop('first_click')
  p.evaluate("()=>{document.getElementById('adsbFilterCivil').checked=false}")
  hidden=p.evaluate("rows=>{window.__takMapAllowExternalAdsbDraw=true;window.__takMapAdsbOwnerRendering=TakMapControllers.adsb.version;const out=window.drawAircraft(rows);delete window.__takMapAdsbOwnerRendering;window.__takMapAllowExternalAdsbDraw=false;return {out:out.map(x=>x.id),markers:[...TakMapControllers.adsb.markers.keys()],data:[...TakMapControllers.adsb.data.keys()]}}",rows)
  # Simulate altitude owner passing only the eligible row; excluded marker must disappear now, not age out.
  altitude=p.evaluate("rows=>{document.getElementById('adsbFilterCivil').checked=true;window.__takMapAllowExternalAdsbDraw=true;window.__takMapAdsbOwnerRendering=TakMapControllers.adsb.version;const out=window.drawAircraft([rows[1]]);delete window.__takMapAdsbOwnerRendering;window.__takMapAllowExternalAdsbDraw=false;return {out:out.map(x=>x.id),markers:[...TakMapControllers.adsb.markers.keys()]}}",rows)
  restored=p.evaluate("rows=>{window.__takMapAllowExternalAdsbDraw=true;window.__takMapAdsbOwnerRendering=TakMapControllers.adsb.version;window.drawAircraft(rows);delete window.__takMapAdsbOwnerRendering;window.__takMapAllowExternalAdsbDraw=false;return [...TakMapControllers.adsb.markers.keys()]}",rows)
  auth_lost=p.evaluate("""()=>{const api=window.TakMapAdsbWorkerV477||window.TakMapAdsbWorkerV476;const before=TakMapControllers.adsb.markers.size;api.authLost();return {before,after:TakMapControllers.adsb.markers.size,aircraft:(window.lastAircraft||[]).length,diag:api.diagnostics()}}""")
  b.close()
 assert not [e for e in errs if 'maximum call stack' in e.lower()],errs
 assert sorted(first['markers'])==['civil-low','gov-high'],first
 assert first_click=={'open':True,'pinned':True,'stopped':True,'defaultToggle':False,'openAfter':True},first_click
 assert hidden['markers']==['gov-high'] and sorted(hidden['data'])==['civil-low','gov-high'],hidden
 assert altitude['markers']==['gov-high'],altitude
 assert sorted(restored)==['civil-low','gov-high'],restored
 assert auth_lost['before']==2 and auth_lost['after']==0 and auth_lost['aircraft']==0 and auth_lost['diag']['authRequired'] is True,auth_lost
 print('Generated-page ADS-B first-click, immediate visual removal, and auth-loss test passed');print(json.dumps({'first':first,'first_click':first_click,'hidden':hidden,'altitude':altitude,'restored':restored,'auth_lost':auth_lost},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
