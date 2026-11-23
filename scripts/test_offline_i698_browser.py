#!/usr/bin/env python3
import json,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
geo=json.loads((ROOT/'assets/tak-map-offline-us-regions-i698.json').read_text())
JS=(ROOT/'assets/tak-map-offline-maps-i698.js').read_text()
CSS=(ROOT/'assets/tak-map-offline-maps-i698.css').read_text()
page_html='''<!doctype html><html><head><title>OFFLINE fixture</title></head><body>
<div class="panel"><h2>Offline Maps</h2><div class="subgroup-title">Create Offline Map Pack</div>
<input id="offlinePackName" value="AZ pack"><div class="row"><span id="offlineSourceText">Source basemap</span></div>
<div class="row"><span>Area</span><button onclick="useCurrentViewForOffline()">Current View</button><button onclick="startOfflineAreaDraw()">Draw Area</button><button onclick="clearOfflineArea()">Clear</button></div>
<div id="offlineDrawHelp" style="display:none"></div><div id="offlineBoundsText"></div><div id="offlineEstimate"></div>
<input id="offlineMinZoom" type="number" value="8"><input id="offlineMaxZoom" type="number" value="12">
<div class="row"><button onclick="previewOfflineZoom()">Preview Max Zoom</button><button onclick="startOfflineDownload()">Create Offline Map</button></div>
<div id="offlineJobStatus"></div><div id="offlineMapRows"></div></div>
<script>
var map={getBounds:()=>({getWest:()=>-110,getEast:()=>-108,getNorth:()=>35,getSouth:()=>33}),fitBounds:()=>{},setView:()=>{},removeLayer:()=>{}};
var config={offline_download_sources:[{id:'fixture',label:'Fixture Map'},{id:'google',label:'Google Terrain'}]};var activeBasemap='fixture';var offlineDownloadBounds=null;var offlineAreaRect=null;var offlineMaps=[];
var L={geoJSON:(x)=>({getBounds:()=>({isValid:()=>true}),addTo:()=>{},}),};
function useCurrentViewForOffline(){offlineDownloadBounds={west:-110,east:-108,south:33,north:35}}
function startOfflineAreaDraw(){}function clearOfflineArea(){}function updateOfflineBoundsText(){}function stopOfflineAreaDraw(){}
function scheduleOfflineEstimate(){}function estimateOfflineDownload(){}function startOfflineDownload(){}
function renderOfflineMapRows(){document.getElementById('offlineMapRows').innerHTML=offlineMaps.map(m=>`<div class="offline-card"><div class="offline-card-title"><span>${m.name}</span><span class="chip good offline-status-chip">Complete</span></div><small>${m.source_label||''}</small></div>`).join('')}
function refreshOfflineMaps(){renderOfflineMapRows()};function pollOfflineJob(){window.mockPolled=true}
</script></body></html>'''
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 pg=browser.new_page(viewport={'width':1100,'height':850})
 failures=[];pg.on('pageerror',lambda e:failures.append(str(e)))
 pg.set_content(page_html)
 pg.evaluate("""(geo)=>{window.__fixtureGeo=geo;
 window.fetch=async(url,init)=>{
  const q=String(url);
  let body={ok:true};
  if(q.includes('offline-areas-i698'))body={ok:true,geojson:geo};
  else if(q.includes('offline-estimate'))body={ok:true,tile_count:720000,max_tiles:250000,internal_jobs:3,estimated_bytes:18000000000};
  else if(q.includes('offline-download'))body={ok:true,job:{id:'abc'}};
  else if(q.includes('offline-retry-i698'))body={ok:true,job:{id:'retryabc'}};
  return {ok:true,status:200,json:async()=>body};
 };}
 """,geo)
 pg.add_style_tag(content=CSS)
 pg.add_script_tag(content=JS)
 pg.wait_for_function('window.TakMapOfflineMapsI698 && TakMapOfflineMapsI698.diagnostic().options===54',timeout=20000)
 val=pg.evaluate('TakMapOfflineMapsI698.diagnostic()')
 assert val['attached'] and val['options']==54,val
 assert pg.locator('#offlineAreaSelectI698 option').count()==54
 assert pg.locator('button[onclick*="startOfflineDownload"]').count()==0
 assert pg.get_by_text('Download',exact=True).count()>=1
 print('PASS UI mounted, 54 choices, Download label')
 pg.select_option('#offlineAreaSelectI698','CA-S')
 pg.wait_for_timeout(300)
 assert pg.evaluate('TakMapOfflineMapsI698.diagnostic().selectedArea')=='CA-S'
 assert pg.evaluate('offlineDownloadBounds.west < -119 && offlineDownloadBounds.east > -115')
 print('PASS California selection and region bounds')
 pg.select_option('#offlineAreaSelectI698','AK')
 assert pg.evaluate('TakMapOfflineMapsI698.diagnostic().selectedArea')=='AK'
 pg.select_option('#offlineAreaSelectI698','view')
 assert pg.evaluate('TakMapOfflineMapsI698.diagnostic().outlinePresent')==False
 print('PASS Alaska state selected and Current View clears outline')
 pg.fill('#offlineAreaSearchI698','hawaii');assert pg.locator('#offlineAreaSelectI698 option').count()==2
 pg.fill('#offlineAreaSearchI698','')
 pg.locator('#offlineMinZoom').fill('5');pg.locator('#offlineMinZoom').dispatch_event('input')
 pg.wait_for_timeout(900)
 assert '3 × up to 250,000' in pg.locator('#offlineEstimate').inner_text(),pg.locator('#offlineEstimate').inner_text()
 print('PASS search and estimated internal batching')
 pg.evaluate("offlineMaps=[{id:'map1',name:'Arizona pack',failed_tile_count:18,source_label:'Google Terrain',partial:false,resume_available:false,internal_jobs:3}];renderOfflineMapRows();")
 assert pg.get_by_role('button',name='Retry/Finish').count()==1
 assert 'Incomplete' in pg.locator('.offline-card-title').inner_text()
 pg.get_by_role('button',name='Retry/Finish').click()
 assert pg.get_by_role('button',name='Retry Failed Tiles').is_visible()
 pg.get_by_role('button',name='Retry Failed Tiles').click();pg.wait_for_timeout(350)
 assert pg.evaluate('window.mockPolled')==True
 print('PASS failed tile recovery UI and targeted retry request')
 assert not failures,failures
 print('PASS no page errors')
 browser.close()
