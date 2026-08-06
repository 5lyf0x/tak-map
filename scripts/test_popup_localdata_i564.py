#!/usr/bin/env python3
from __future__ import annotations

import os

import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / 'tak_dashboard.py'
ASSET = ROOT / 'assets/tak-map-popup-localdata-i564.js'

spec = importlib.util.spec_from_file_location('tak_dashboard_i564_localdata_test', DASH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader is not None
spec.loader.exec_module(mod)

html = mod.TAK_MAP_HTML
assert mod.TAK_MAP_ITERATION == 'i564'
assert '/assets/runtime/tak-map-icon-registry-i564.js?v=1.3.0-i564' in html
assert '/assets/runtime/tak-map-popup-localdata-i564.js?v=1.3.0-i564' in html
assert html.index('tak-map-icon-registry-i564.js') < html.index('tak-map-popup-localdata-i564.js') < html.index('tak-map-context-sidebar-i564.js')
assert 'tak-map-popup-localdata-i564.js' not in mod.TAK_MAP_LOGIN_HTML
cfg = mod.tak_map_config()
assert cfg['version'] == '1.3.0-i564'
assert cfg['popup_behavior']['leaflet_object_popups'] is False
assert cfg['local_data']['silent_row_limit_removed'] is True

source = ASSET.read_text(encoding='utf-8')
for token in [
    'leafletPopupSizingDisabled',
    'items.slice()',
    '/api/tak-map/imported',
    'canonicalRefresh',
    'local-highlight-i564',
    'All ${ordered.length}',
]:
    assert token in source, token
assert 'slice(0,120)' not in source

try:
    from playwright.sync_api import sync_playwright
except Exception as exc:
    raise SystemExit(f'Playwright is required for i557 browser validation: {exc}')

asset = source
points = []
for index in range(125):
    points.append({
        'kind': 'point',
        'geometry': 'point',
        'name': f'POINT-{index:03d}',
        'lat': 34.0 + index / 10000,
        'lon': -118.0 - index / 10000,
        'updated': f'2026-07-27T03:{index % 60:02d}:00Z',
    })
imports_payload = {
    'ok': True,
    'imports': [{
        'id': 'bulk-local',
        'name': 'Bulk Local Points',
        'uploaded': '2026-07-27T03:59:00Z',
        'counts': {'point': len(points)},
        'features': points,
    }],
}

bootstrap = f"""
window.state={{localCollapsed:{{points:false,routes:false,shapes:false}},local:{{points:{{}},routes:{{}},shapes:{{}},hidden:{{}}}}}};
window.esc=v=>String(v??'').replace(/[&<>\"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',\"'\":'&#39;'}}[c]));
window.formatCoords=(lat,lon)=>Number(lat).toFixed(6)+', '+Number(lon).toFixed(6);
window.renderLocalActions=()=>'';
window.toggleLocalSection=()=>{{}};
window.unselectLocalSection=()=>{{}};
window.toggleLocalItem=()=>{{}};
window.centerLocalItem=()=>{{}};
let lastImports=[];
window.importedFeatures=function(){{const out=[];for(const imp of lastImports){{(imp.features||[]).forEach((f,i)=>out.push(Object.assign({{}},f,{{import_id:imp.id,import_name:imp.name,uploaded:imp.uploaded,_local_id:(imp.id||imp.name)+':'+i}})))}}return out}};
window.localDataSets=function(){{const sets={{points:[],routes:[],shapes:[]}};for(const f of importedFeatures()){{sets.points.push({{id:f._local_id,name:f.name,source:f.import_name,shown:true,feature:f}})}}return sets}};
window.renderLocalDataRows=function(){{const sets=localDataSets();document.getElementById('localDataRows').innerHTML=renderLocalSection('points','Points',sets.points)}};
window.renderImportRows=function(){{window.__renderImportRows=(window.__renderImportRows||0)+1}};
window.drawImportedObjects=function(){{window.__drawImportedObjects=(window.__drawImportedObjects||0)+1}};
window.renderLocalSection=function(kind,title,items){{return '<div>legacy '+items.slice(0,120).length+'</div>'}};
const mapHandlers={{}};
window.map={{__handlers:mapHandlers,on:function(names,fn){{String(names).split(/\\s+/).forEach(n=>mapHandlers[n]=fn)}},getContainer:()=>document.getElementById('map'),_popup:null}};
window.__canonicalPayload={json.dumps(imports_payload)};
window.__canonicalGets=0;
window.__mutations=0;
window.fetch=async function(input,init){{const url=String(input&&input.url||input||'');const method=String(init&&init.method||'GET').toUpperCase();if(url.includes('/api/tak-map/imported')){{window.__canonicalGets++;return new Response(JSON.stringify(window.__canonicalPayload),{{status:200,headers:{{'content-type':'application/json'}}}})}}if(method!=='GET'&&url.includes('/api/tak-map/local-point-i556')){{window.__mutations++;return new Response(JSON.stringify({{ok:true,point:{{local_id:'bulk-local:124'}}}}),{{status:200,headers:{{'content-type':'application/json'}}}})}}return new Response(JSON.stringify({{ok:true}}),{{status:200,headers:{{'content-type':'application/json'}}}})}};
"""

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
    page = browser.new_page(viewport={'width': 1280, 'height': 800})
    errors: list[str] = []
    page.on('pageerror', lambda exc: errors.append(str(exc)))
    page.set_content('<!doctype html><html><head></head><body><div id="map" style="position:absolute;left:300px;top:40px;width:900px;height:700px"></div><div id="localDataRows"></div></body></html>')
    page.add_script_tag(content=bootstrap)
    page.add_script_tag(content=asset)
    page.wait_for_function('window.TakMapPopupLocalDataI564 && window.TakMapPopupLocalDataI564.audit().installed')

    page.evaluate('() => window.TakMapPopupLocalDataI564.canonicalRefresh({force:true})')
    page.wait_for_function("document.querySelectorAll('.local-data-row').length===125")
    result = page.evaluate("""() => ({
      rows: document.querySelectorAll('.local-data-row').length,
      note: document.querySelector('.local-list-complete-note-i564')?.textContent || '',
      canonicalGets: window.__canonicalGets,
      drawCalls: window.__drawImportedObjects || 0,
      renderCalls: window.__renderImportRows || 0,
      audit: window.TakMapPopupLocalDataI564.audit()
    })""")
    assert result['rows'] == 125, result
    assert 'All 125 points shown' in result['note'], result
    assert result['canonicalGets'] >= 1, result
    assert result['drawCalls'] >= 1 and result['renderCalls'] >= 1, result
    assert result['audit']['errors'] == [], result

    assert result['audit']['leafletPopupSizingDisabled'] is True, result

    page.evaluate("fetch('/api/tak-map/local-point-i556',{method:'POST',headers:{'content-type':'application/json'},body:'{}'})")
    page.wait_for_function("window.__canonicalGets>=2 && document.querySelector('.local-highlight-i564')")
    mutation_result = page.evaluate("""() => ({
      canonicalGets:window.__canonicalGets,
      mutations:window.__mutations,
      highlighted:document.querySelector('.local-highlight-i564')?.dataset.localId || '',
      first:document.querySelector('.local-data-row')?.dataset.localId || ''
    })""")
    assert mutation_result['mutations'] == 1, mutation_result
    assert mutation_result['highlighted'] == 'bulk-local:124', mutation_result
    assert mutation_result['first'] == 'bulk-local:124', mutation_result
    assert not errors, errors
    browser.close()

print('i564 canonical complete Local Data listing and post-mutation synchronization validation passed')
sys.stdout.flush()
os._exit(0)
