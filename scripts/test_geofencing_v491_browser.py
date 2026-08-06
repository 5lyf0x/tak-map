#!/usr/bin/env python3
from __future__ import annotations
import json, os, re, runpy, shutil, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STUB=(ROOT/'scripts'/'leaflet_stub_test.js').read_text()

def html_page():
    with tempfile.TemporaryDirectory(prefix='tak-gf-page-') as td:
        old=os.environ.get('TAK_DASHBOARD_DATA_DIR'); os.environ['TAK_DASHBOARD_DATA_DIR']=td
        try: ns=runpy.run_path(str(ROOT/'tak_dashboard.py'),run_name='tak_map_i491_geofence_browser')
        finally:
            if old is None: os.environ.pop('TAK_DASHBOARD_DATA_DIR',None)
            else: os.environ['TAK_DASHBOARD_DATA_DIR']=old
    html=ns['TAK_MAP_HTML']
    html=re.sub(r'<script src="https://unpkg\.com/leaflet@1\.9\.4/dist/leaflet\.js"></script>', '<script>'+STUB+'</script>', html, count=1)
    html=re.sub(r'<link[^>]+unpkg\.com/leaflet@1\.9\.4/dist/leaflet\.css[^>]*>','',html,count=1)
    pat=re.compile(r'<script id="([^"]+)" src="/assets/runtime/([^"?]+)[^"]*"></script>')
    def inline(m):
        fp=ROOT/'assets'/m.group(2); assert fp.exists(),fp
        return f'<script id="{m.group(1)}">\n{fp.read_text()}\n</script>'
    return pat.sub(inline,html)

def main():
    chromium=next((x for x in ('chromium','chromium-browser','google-chrome','google-chrome-stable') if shutil.which(x)),None)
    if not chromium:
        print('SKIP: Chromium unavailable'); return 0
    from playwright.sync_api import sync_playwright
    html=html_page()
    with sync_playwright() as pw:
        b=pw.chromium.launch(headless=True,executable_path=shutil.which(chromium),args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
        p=b.new_page(viewport={'width':1440,'height':1000}); p.set_default_timeout(6000)
        errors=[]; p.on('pageerror',lambda e:errors.append(str(e)))
        p.set_content(html,wait_until='domcontentloaded',timeout=30000)
        p.wait_for_function("window.TakMapGeofencingV491 && window.TakMapObjectLifecycleV486 && document.getElementById('geofencePanelV491')",timeout=20000)
        p.wait_for_timeout(2500)
        setup=p.evaluate("""()=>{
          window.__gfStore=[]; window.__native={confirm:0,prompt:0,alert:0};
          window.confirm=()=>{window.__native.confirm++;return true};
          window.prompt=()=>{window.__native.prompt++;return ''};
          window.alert=()=>{window.__native.alert++};
          const oldFetch=window.fetch.bind(window);
          window.fetch=async(url,init={})=>{
            const u=String(url||'');
            if(u.includes('/api/tak-map/geofences')){
              if(String(init.method||'GET').toUpperCase()==='POST'){
                const body=JSON.parse(init.body||'{}');
                if(body.action==='upsert'){
                  const i=window.__gfStore.findIndex(x=>x.id===body.fence.id);
                  if(i>=0)window.__gfStore[i]=body.fence;else window.__gfStore.push(body.fence);
                  return new Response(JSON.stringify({ok:true,fence:body.fence,fences:window.__gfStore}),{status:200,headers:{'Content-Type':'application/json'}});
                }
                if(body.action==='remove'){
                  window.__gfStore=window.__gfStore.filter(x=>x.id!==body.id);
                  return new Response(JSON.stringify({ok:true,removed:true,id:body.id,fences:window.__gfStore}),{status:200,headers:{'Content-Type':'application/json'}});
                }
              }
              return new Response(JSON.stringify({ok:true,fences:window.__gfStore,rules:{confirmation_seconds:2,rearm_seconds:10}}),{status:200,headers:{'Content-Type':'application/json'}});
            }
            return oldFetch(url,init);
          };
          window.__testAircraftRaw=[]; window.__testAircraftVirtual=[];
          window.TakMapAdsbWorkerV477={rawSnapshot:()=>window.__testAircraftRaw,snapshot:()=>window.__testAircraftRaw,virtualSnapshot:()=>window.__testAircraftVirtual,diagnostics:()=>({enabled:true})};
          window.lastTakMarkers=[];
          const obj={object_id:'local-area-test',canonical_id:'local:local-area-test',name:'Airport Perimeter',kind:'shape',geometry:'polygon',coords:[[34.0,-118.0],[34.0,-117.98],[34.02,-117.98],[34.02,-118.0],[34.0,-118.0]]};
          const layer=L.polygon(obj.coords).addTo(map).bindPopup('<div><b>Airport Perimeter</b><button>Delete</button></div>');
          TakMapObjectLifecycleV486.register(obj,'local',layer,window.importedLayer||null);
          const root=document.createElement('div');root.className='leaflet-popup';root.innerHTML='<div class="leaflet-popup-content"><b>Airport Perimeter</b><button>Delete</button></div>';document.body.appendChild(root);
          const popup={_source:layer,getElement:()=>root};TakMapGeofencingV491.attachPopup(popup);
          window.__gfLayer=layer;window.__gfPopup=popup;
          return {registered:!!TakMapObjectLifecycleV486.entryForId('local:local-area-test')};
        }""")
        assert setup['registered'],setup
        p.wait_for_timeout(300)
        print('popup debug',p.evaluate("()=>({diag:TakMapGeofencingV491.diagnostics(),entry:TakMapObjectLifecycleV486.entryForLayer(window.__gfLayer),root:window.__gfPopup.getElement().outerHTML})")); assert p.locator('.tak-geofence-popup-btn-v491').count()==1
        p.evaluate("document.querySelector('.tak-geofence-popup-btn-v491').click()")
        p.wait_for_selector('#takGeofenceEditorV491',timeout=5000)
        p.locator('#takGfNameV491').fill('Airport Perimeter')
        # Area: ADS-B only, Enter+Exit, dwell configured, altitude band.
        p.locator('[data-gf-source="eud"]').uncheck()
        p.locator('[data-gf-source="adsb"]').check()
        p.locator('[data-gf-trigger="enter"]').check()
        p.locator('[data-gf-trigger="exit"]').check()
        p.locator('[data-gf-trigger="dwell"]').check()
        p.locator('#takGfDwellV491').fill('5')
        p.locator('#takGfAltModeV491').select_option('band')
        p.locator('#takGfAltMinV491').fill('2000')
        p.locator('#takGfAltMaxV491').fill('12000')
        p.locator('[data-gf-save]').click()
        p.wait_for_function("TakMapGeofencingV491.fences().length===1")

        ui=p.evaluate("""()=>{
          const f=TakMapGeofencingV491.fences()[0];
          const row=document.querySelector('.tak-gf-row-v491');
          const adsb=document.querySelector('.adsb-type-card-v491.is-checked-v491');
          const cs=adsb?getComputedStyle(adsb):null;
          return {f,rowText:row&&row.innerText,buttons:Array.from(row?.querySelectorAll('button')||[]).map(x=>x.textContent.trim()),native:window.__native,
            sidebarDesign:TakMapGeofencingV491.diagnostics().sidebarDesign,eventDesign:TakMapGeofencingV491.diagnostics().eventDesign,
            selectedBorder:cs&&cs.borderTopColor,selectedBackground:cs&&cs.backgroundColor,
            protected:TakMapGeofencingV491.protectedIds()};
        }""")
        assert ui['f']['triggers']['enter'] and ui['f']['triggers']['exit'] and ui['f']['triggers']['dwell'],ui
        assert ui['f']['altitude']=={'mode':'band','min_ft':2000,'max_ft':12000},ui
        assert ui['buttons']==['Center','Edit','Pause'],ui
        assert all(x not in ui['rowText'] for x in ('Last event','Delete','Duplicate','Hide')),ui
        assert ui['sidebarDesign']=='Option A Operational Rows' and ui['eventDesign']=='Option C Dense Trigger Chips',ui
        assert ui['native']=={'confirm':0,'prompt':0,'alert':0},ui
        assert ui['protected']==['local:local-area-test'],ui
        assert '218' in ui['selectedBorder'] or '217' in ui['selectedBorder'] or '225' in ui['selectedBorder'],ui

        # Visual marker/icon overlap and interpolation must not count. Start with the
        # authoritative reported coordinate outside while the rendered marker and
        # virtual/interpolated snapshot are well inside the polygon.
        p.evaluate("""()=>{
          window.__testAircraftRaw=[{id:'A1',callsign:'N725TA',lat:33.99,lon:-118.01,altitude_ft:8400,updated:new Date().toISOString()}];
          window.__testAircraftVirtual=[{id:'A1',callsign:'N725TA',lat:34.01,lon:-117.99,altitude_ft:8400,updated:new Date().toISOString()}];
          const m=L.marker([34.01,-117.99]).addTo(map);m._takAdsbId='A1';
          const mel=document.createElement('div');mel.style.width='500px';mel.style.height='500px';mel.style.transform='rotate(45deg)';mel.textContent='oversized aircraft icon';document.body.appendChild(mel);
          m.getElement=()=>mel;window.__adsbMarker=m;window.TakMapControllers=window.TakMapControllers||{};window.TakMapControllers.adsb={markers:new Map([['a1',m]])};
          TakMapGeofencingV491.tick();
        }""")
        p.wait_for_timeout(2250)
        visual_only=p.evaluate("""()=>{window.__testAircraftRaw[0].updated=new Date().toISOString();window.__testAircraftVirtual[0].updated=new Date().toISOString();TakMapGeofencingV491.tick();return {events:TakMapGeofencingV491.events(),diag:TakMapGeofencingV491.diagnostics(),marker:window.__adsbMarker.getLatLng()}}""")
        assert visual_only['events']==[],visual_only
        assert visual_only['diag']['coordinateTruth']=='reported-lat-lon',visual_only
        assert visual_only['diag']['adsbCoordinateSnapshot']=='rawSnapshot',visual_only
        assert visual_only['diag']['visualMarkerGeometryIgnored'] is True and visual_only['diag']['iconBoundsIgnored'] is True,visual_only
        assert visual_only['diag']['interpolationAffectsGeofence'] is False and visual_only['diag']['visualCoordinateEvaluations']==0,visual_only

        # Now move the authoritative reported coordinate inside. The reported
        # outside-to-inside segment, not the already-overlapping icon, triggers.
        p.evaluate("""()=>{window.__testAircraftRaw=[{id:'A1',callsign:'N725TA',lat:34.01,lon:-117.99,altitude_ft:8400,updated:new Date().toISOString()}];TakMapGeofencingV491.tick()}""")
        p.wait_for_timeout(2150)
        p.evaluate("""()=>{window.__testAircraftRaw[0].updated=new Date().toISOString();TakMapGeofencingV491.tick()}""")
        p.wait_for_timeout(150)
        event=p.evaluate("""()=>({events:TakMapGeofencingV491.events(),html:document.getElementById('takGfEventRowsV491').innerHTML,pulsing:window.__adsbMarker.getElement()?.classList.contains('tak-geofence-pulse-v491'),diag:TakMapGeofencingV491.diagnostics()})""")
        assert len(event['events'])==1 and event['events'][0]['type']=='enter',event
        assert '<strong>N725TA</strong>' in event['html'] and 'Airport Perimeter' in event['html'],event
        assert event['pulsing'],event
        assert event['diag']['boundaryConfirmationSeconds']==2 and event['diag']['rearmSeconds']==10 and event['diag']['oneEventPerCrossing'],event

        # Repeated ticks cannot create another crossing event during the same state/rearm.
        p.evaluate("""()=>{window.__testAircraftRaw[0].updated=new Date().toISOString();TakMapGeofencingV491.tick();TakMapGeofencingV491.tick()}""")
        assert p.evaluate("TakMapGeofencingV491.events().length")==1

        # Stale data cannot generate a new exit.
        p.evaluate("""()=>{window.__testAircraftRaw=[{id:'A1',callsign:'N725TA',lat:33.99,lon:-118.01,altitude_ft:8400,updated:new Date(Date.now()-600000).toISOString()}];TakMapGeofencingV491.tick()}""")
        p.wait_for_timeout(2200)
        p.evaluate("TakMapGeofencingV491.tick()")
        assert p.evaluate("TakMapGeofencingV491.events().length")==1

        # Dense trigger-chip design, lower-right placement, minus/plus collapse and drag persistence.
        box=p.locator('#takGeofenceEventsV491').bounding_box(); scale=p.locator('.leaflet-control-scale, .scale-control').first
        collapse=p.locator('#takGfEventMinV491')
        assert collapse.count()==1
        collapse.click(); p.wait_for_timeout(80)
        collapsed=p.evaluate("""()=>({collapsed:document.getElementById('takGeofenceEventsV491').classList.contains('collapsed'),restore:document.getElementById('takGfEventMinV491').classList.contains('restore'),body:getComputedStyle(document.getElementById('takGfEventsBodyV491')).display})""")
        assert collapsed=={'collapsed':True,'restore':True,'body':'none'},collapsed
        collapse.click(); p.wait_for_timeout(80)
        head=p.locator('.tak-gf-events-head-v491').bounding_box(); assert head
        p.mouse.move(head['x']+30,head['y']+20);p.mouse.down();p.mouse.move(head['x']-40,head['y']-20,steps=4);p.mouse.up();p.wait_for_timeout(80)
        dragged=p.evaluate("""()=>({left:document.getElementById('takGeofenceEventsV491').style.left,top:document.getElementById('takGeofenceEventsV491').style.top})""")
        assert dragged['left'] and dragged['top'],dragged
        assert "sessionStorage.setItem('takmap.geofence.events.pos'" in (ROOT/'assets'/'tak-map-geofencing-v491.js').read_text()

        # Directly configure a route-cross rule through the same themed editor.
        p.evaluate("""()=>TakMapGeofencingV491.openEditor({id:'local:local-route-test',kind:'route',source:'local',name:'North Access Route',geometry:{type:'route',coordinates:[[-118.10,34.10],[-117.90,34.10]]}})""")
        p.locator('#takGfNameV491').fill('North Access Route')
        p.locator('[data-gf-source="adsb"]').uncheck();p.locator('[data-gf-source="eud"]').check()
        p.locator('[data-gf-save]').click();p.wait_for_function("TakMapGeofencingV491.fences().length===2")
        route=p.evaluate("""()=>TakMapGeofencingV491.fences().find(x=>x.kind==='route')""")
        assert route['triggers']=={'enter':False,'exit':False,'dwell':False,'cross':True},route

        # Verify source classes and no browser-native controls were invoked.
        final=p.evaluate("""()=>({diag:TakMapGeofencingV491.diagnostics(),native:window.__native,cardText:document.getElementById('geofencePanelV491').innerText,eventBottom:getComputedStyle(document.getElementById('takGeofenceEventsV491')).bottom,pageReady:document.readyState})""")
        assert final['native']=={'confirm':0,'prompt':0,'alert':0},final
        assert final['diag']['nativeBrowserControls'] is False
        assert final['pageReady']=='complete'
        assert 'Last event' not in final['cardText']
        fatal=[e for e in errors if any(x in e.lower() for x in ('maximum call stack','out of memory','too much recursion','syntaxerror'))]
        assert not fatal,(fatal,errors)
        b.close()
    print('TAK Map i502 geofencing reported-coordinate UI/event-engine browser test passed')
    print(json.dumps({'ui':ui,'visual_only':visual_only,'event':event,'dragged':dragged,'final':final},sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())
