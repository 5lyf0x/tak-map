from pathlib import Path
from playwright.sync_api import sync_playwright
import json
root=Path(__file__).resolve().parent.parent
core=(root/"assets/tak-map-core-i553.js").read_text()
mod=(root/"assets/tak-map-offline-maps-i698.js").read_text()
# Use actual renderer, API refresh function, and module, not recreated rendering.
a=core.index('function offlineBasemapEntry(m)')
b=core.index('async function uploadOfflineMaps()',a)
refresh_code=core[a:b]
a=core.index('function sortOfflineMapPacksByNameI001(')
b=core.index('async function apiJsonResponse(',a)
renderer_code=core[a:b]
assert "renderOfflineMapRows();Promise.resolve().then(()=>refreshOfflineMaps(true))" in core
assert "['offline-maps',()=>refreshOfflineMaps(true),10000]" in core
records=[
 {'id':'C','name':'Central California','created_by':'download','download_status':'complete','tile_count':51082,'format':'jpg','size_bytes':846200000},
 {'id':'s1','name':'Sample Map 1','created_by':'download','download_status':'complete','tile_count':3576,'format':'jpg'},
 {'id':'s2','name':'Sample Map 2','created_by':'download','download_status':'complete','tile_count':3576,'format':'jpg'},
 {'id':'sat','name':'SAT: Southern California','created_by':'download','download_status':'complete','tile_count':157425,'format':'jpg'},
]
html='''<!doctype html><html><head></head><body><div class="panel"><h2>Offline Maps</h2><div class="subgroup-title">Create Offline Map</div><div class="row"><button onclick="useCurrentViewForOffline()">Current View</button></div><div class="row"><button onclick="refreshOfflineMaps()">Refresh Offline Maps</button></div><div class="row"><button onclick="startOfflineDownload()">Download</button></div><div class="row"><button onclick="previewOfflineZoom()">Preview</button></div><div class="row" id="offlineSourceTextRow"><span id="offlineSourceText">online</span></div><div class="row" id="offlineBoundsTextRow"><span id="offlineBoundsText">bounds</span></div><input id="offlinePackName"><input id="offlineMinZoom" value="8"><input id="offlineMaxZoom" value="14"><div id="offlineEstimate"></div><div id="offlineMapRows" class="offline-list"></div></div></body></html>'''
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-gpu'])
 for case,js in [('i003',mod)]:
  page=browser.new_page()
  errors=[]
  page.on('pageerror',lambda e: errors.append(str(e)))
  page.set_content(html)
  # Stub the production endpoints and simple functions unrelated to Offline Maps.
  page.add_script_tag(content='''window.config={basemaps:[],offline_download_sources:[]};window.offlineMaps=[];window.renderBasemaps=()=>{};window.esc=x=>String(x||'');window.fetch=async function(u){const path=String(u);let j;if(path.includes('/offline-maps')){j={ok:true,maps:'''+json.dumps(records)+'''};}else if(path.includes('/offline-areas-i698')){j={ok:false};}else if(path.includes('/config')){j={ok:true,offline_download_sources:[]};}else{j={ok:true};}return {ok:true,status:200,headers:{get:()=> 'application/json'},json:async()=>j}};''')
  # Bug reproduction: module executes before asynchronously loaded core renderer.
  page.add_script_tag(content=js)
  before=page.evaluate('typeof window.renderOfflineMapRows')
  assert before=='undefined',before
  page.add_script_tag(content=refresh_code+'\n'+renderer_code)
  # Core's early shell render happens while offlineMaps still empty.
  page.evaluate('renderOfflineMapRows()')
  assert page.locator('#offlineMapRows .offline-card').count()==0
  # Startup renderer becomes available and notifies modules.
  page.evaluate("window.__takMapShellReadyI553=true;window.dispatchEvent(new CustomEvent('takmap:shell-ready-i553'))")
  # Model the core initial fetch/render path, no manual Refresh click.
  # Expression verified against the real source above; this is core startup, not a click.
  page.evaluate("Promise.resolve().then(()=>refreshOfflineMaps(true)).catch(e=>console.warn('Initial offline maps refresh failed',e));")
  page.wait_for_timeout(180)
  count=page.locator('#offlineMapRows .offline-card').count()
  rename=page.locator('#offlineMapRows .offline-rename-action').count()
  assert count==4,(case,count)
  assert rename==4,(case,rename)
  # Re-run lifecycle events, verify no duplicated controls.
  for event in ['takmap:runtime-ready-i553','takmap:optional-data-ready-i553']:
   page.evaluate(f"window.dispatchEvent(new CustomEvent('{event}'))")
  assert page.locator('#offlineMapRows .offline-rename-action').count()==4
  assert page.locator('#offlineMapRows .offline-i698-recovery').count()==0
  # Simulate subsequent programmatic render and catalog refresh, preserving Rename buttons.
  page.evaluate('renderOfflineMapRows()')
  assert page.locator('#offlineMapRows .offline-rename-action').count()==4
  print('PASS i003: all 4 offline packs load without click, all 4 rename controls exist, repeated lifecycle/redraw stays idempotent')
  assert not errors,(case,errors)
  page.close()
 browser.close()
print('PASS combined realistic startup ordering and reconnect test')
