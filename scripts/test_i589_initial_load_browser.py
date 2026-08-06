#!/usr/bin/env python3
from __future__ import annotations

import importlib.util, os
import json
import pathlib
import sys
import time
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parents[1]
os.environ['TAK_MAP_MIL_ROOT']=str(ROOT/'assets/mil2525')
os.environ['TAK_MAP_TEST_SKIP_ADSB_WARMUP']='1'
DASH = ROOT / 'tak_dashboard.py'

spec = importlib.util.spec_from_file_location('tak_dashboard_i589_initial_load', DASH)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader is not None
spec.loader.exec_module(mod)

html = mod.TAK_MAP_HTML
config = mod.tak_map_config()
leaflet_stub = (ROOT / 'scripts/leaflet_stub_test.js').read_text(encoding='utf-8')
page_errors: list[str] = []
console_errors: list[str] = []
requests: list[str] = []
data_sync_calls = 0

MISSION = 'PROTECTED-I585'

first_sync = {
    'ok': True,
    'version': 'i589',
    'missions': [{
        'name': MISSION,
        'passwordProtected': True,
        'owner': {'callsign': 'OWNER'},
    }],
    'mission_access_i576': [{
        'ok': True,
        'known': True,
        'mission': MISSION,
        'protected': True,
        'password_protected': True,
        'unlocked': True,
        'locked': False,
        'credential_configured': True,
    }],
    'objects': [{
        'uid': 'I585-POINT-1',
        'mission_name': MISSION,
        'mission': MISSION,
        'callsign': 'I585-POINT',
        'name': 'I585-POINT',
        'lat': 34.4,
        'lon': -117.4,
        'cot_type': 'a-f-G',
        'source': 'OpenTAKServer Data Sync mission_uids',
        'delete_supported': True,
        'object_id': 'I585-POINT-1',
    }, {
        'uid': 'I585-SENSOR-1',
        'mission_name': MISSION,
        'mission': MISSION,
        'callsign': 'I585-SENSOR',
        'name': 'I585-SENSOR',
        'lat': 34.41,
        'lon': -117.41,
        'type': 'a-f-G-E-S',
        'cot_type': 'a-f-G-E-S',
        'sidc': 'SFGPES---------',
        'mission_cot_raw_sidc_i553': 'SFGPES---------',
        'mission_cot_raw_type_i553': 'a-f-G-E-S',
        'data_sync_symbol_decision_i553': {
            'version': 'i553', 'authority': 'explicit-sidc',
            'selected_sidc': 'SFGPES---------',
        },
        'source': 'OpenTAKServer Data Sync mission_uids',
        'delete_supported': True,
        'object_id': 'I585-SENSOR-1',
    }, {
        'uid': 'I585-TANK-1',
        'mission_name': MISSION,
        'mission': MISSION,
        'callsign': 'I585-TANK',
        'name': 'I585-TANK',
        'lat': 34.42,
        'lon': -117.42,
        'type': 'a-f-G-E-V-A-T',
        'cot_type': 'a-f-G-E-V-A-T',
        'sidc': 'SFGPEVAT-------',
        'mission_cot_raw_sidc_i553': 'SFGPEVAT-------',
        'data_sync_symbol_decision_i553': {
            'version': 'i553', 'authority': 'explicit-sidc',
            'selected_sidc': 'SFGPEVAT-------',
        },
        'source': 'OpenTAKServer Data Sync mission_uids',
        'delete_supported': True,
        'object_id': 'I585-TANK-1',
    }, {
        'uid': 'I585-RADAR-1',
        'mission_name': MISSION,
        'mission': MISSION,
        'callsign': 'I585-RADAR',
        'name': 'I585-RADAR',
        'lat': 34.43,
        'lon': -117.43,
        'type': 'a-f-G-E-S-R',
        'cot_type': 'a-f-G-E-S-R',
        'mission_cot_raw_type_i553': 'a-f-G-E-S-R',
        'data_sync_symbol_decision_i553': {
            'version': 'i553', 'authority': 'event-type',
            'selected_cot_type': 'a-f-G-E-S-R',
        },
        'source': 'OpenTAKServer Data Sync mission_uids',
        'delete_supported': True,
        'object_id': 'I585-RADAR-1',
    }],
    'packages': [],
}

# Deliberately incomplete/downgraded access metadata. The browser must preserve
# the directly confirmed protected/unlocked state and the same control nodes.
partial_sync = {
    'ok': True,
    'version': 'i589',
    'missions': [{'name': MISSION}],
    'mission_access_i576': [{
        'ok': True,
        'known': False,
        'mission': MISSION,
        'protected': False,
        'password_protected': False,
        'unlocked': False,
        'locked': False,
    }],
    'objects': first_sync['objects'],
    'packages': [],
}

responses = {
    '/api/tak-map/status-banner': {'ok': True, 'tak_server': 'Online', 'internet': 'Connected', 'euds_connected': 0, 'adsb_aircraft': 0, 'downloads': {'active': 0}},
    '/api/tak-map/cot': {'ok': True, 'markers': []},
    '/api/tak-map/local-data': {'ok': True, 'routes': [], 'points': [], 'shapes': []},
    '/api/tak-map/imported': {'ok': True, 'imports': []},
    '/api/tak-map/offline-maps': {'ok': True, 'maps': [], 'jobs': []},
    '/api/tak-map/adsb-settings': {'ok': True, 'settings': {'enabled': False, 'update_interval_seconds': 30}},
    '/api/tak-map/adsb': {'ok': True, 'aircraft': []},
    '/api/tak-map/euds': {'ok': True, 'euds': []},
    '/api/tak-map/geofences': {'ok': True, 'geofences': []},
    '/api/tak-map/custom-basemaps': {'ok': True, 'basemaps': []},
    '/api/tak-map/account/tak-identity': {'ok': True, 'callsign': 'TEST', 'username': 'test'},
    '/api/tak-map/account/sentinel-hub': {'ok': True, 'configured': False},
    '/api/tak-map/ots/session': {'ok': True, 'username': 'test', 'callsign': 'TEST', 'authenticated': True},
    '/api/tak-map/icon-registry/summary': {'ok': True, 'version': 'i589', 'iconsets': [], 'custom_set_count': 0, 'custom_icon_count': 0},
    '/api/tak-map/icon-registry/sets': {'ok': True, 'version': 'i589', 'iconsets': []},
    '/api/tak-map/tile-cache-status': {'ok': True, 'bytes': 0, 'hits': 0, 'misses': 0},
}

try:
    from playwright.sync_api import sync_playwright
except Exception as exc:  # pragma: no cover
    raise SystemExit(f'Playwright is required for initial-load validation: {exc}')


def content_type(path: pathlib.Path) -> str:
    return {
        '.js': 'application/javascript',
        '.json': 'application/json',
        '.css': 'text/css',
        '.svg': 'image/svg+xml',
        '.png': 'image/png',
        '.webp': 'image/webp',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.woff2': 'font/woff2',
    }.get(path.suffix.lower(), 'application/octet-stream')


with sync_playwright() as pw:
    browser = pw.chromium.launch(
        headless=True,
        executable_path='/usr/bin/chromium',
        args=['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'],
    )
    page = browser.new_page(viewport={'width': 1440, 'height': 900}, timezone_id='UTC')
    page.on('pageerror', lambda exc: page_errors.append(str(exc)))
    page.on('console', lambda msg: console_errors.append(msg.text) if msg.type == 'error' else None)

    def route_handler(route, request):
        nonlocal_data = None
        del nonlocal_data
        global data_sync_calls
        parsed = urlparse(request.url)
        path = parsed.path
        requests.append(path)

        if path in {'/', '/tak-map'}:
            return route.fulfill(status=200, content_type='text/html', body=html)

        if path == '/api/tak-map/config':
            return route.fulfill(status=200, content_type='application/json', body=json.dumps(config))

        if path == '/api/tak-map/data-sync':
            data_sync_calls += 1
            payload = first_sync if data_sync_calls == 1 else partial_sync
            return route.fulfill(status=200, content_type='application/json', body=json.dumps(payload))

        if path == '/api/tak-map/data-sync-mission-access-i573':
            return route.fulfill(status=200, content_type='application/json', body=json.dumps({
                'ok': True,
                'version': 'i589',
                'known': True,
                'mission': MISSION,
                'protected': True,
                'password_protected': True,
                'unlocked': True,
                'locked': False,
                'credential_configured': True,
            }))

        if 'leaflet' in request.url and path.endswith('.js'):
            return route.fulfill(status=200, content_type='application/javascript', body=leaflet_stub)
        if path.endswith('leaflet.css'):
            return route.fulfill(status=200, content_type='text/css', body=(ROOT / 'assets/vendor/leaflet-1.9.4/leaflet.css').read_bytes())

        if path == '/mil2525/icons.json':
            return route.fulfill(status=200, content_type='application/json', body=(ROOT / 'assets/mil2525/icons.json').read_bytes())
        if path.startswith('/mil2525/svg/'):
            return route.fulfill(status=200, content_type='image/svg+xml', body=b'<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"/>')

        if path.startswith('/api/tak-map/'):
            return route.fulfill(status=200, content_type='application/json', body=json.dumps(responses.get(path, {'ok': True})))

        if path.startswith('/assets/runtime/'):
            file_path = ROOT / 'assets' / path[len('/assets/runtime/'):]
            if file_path.is_file():
                return route.fulfill(status=200, content_type=content_type(file_path), body=file_path.read_bytes())

        if path.startswith('/assets/'):
            file_path = ROOT / 'assets' / path[len('/assets/'):]
            if file_path.is_file():
                return route.fulfill(status=200, content_type=content_type(file_path), body=file_path.read_bytes())

        # External providers/fonts are irrelevant to the startup contract.
        return route.fulfill(status=204, body='')

    page.route('**/*', route_handler)
    storage_stub = """(() => { const m=new Map(); const store={getItem:k=>m.has(String(k))?m.get(String(k)):null,setItem:(k,v)=>m.set(String(k),String(v)),removeItem:k=>m.delete(String(k)),clear:()=>m.clear(),key:i=>Array.from(m.keys())[i]||null,get length(){return m.size}}; try{Object.defineProperty(window,'localStorage',{value:store,configurable:true})}catch(_){} try{Object.defineProperty(window,'sessionStorage',{value:store,configurable:true})}catch(_){} })();"""
    page.add_init_script(storage_stub)
    page.evaluate(storage_stub)

    started = time.perf_counter()
    page.set_content(html.replace('<head>', '<head><base href="https://example.test/">', 1), wait_until='domcontentloaded', timeout=20_000)
    try:
        page.wait_for_function("document.documentElement.dataset.takMapShell === 'ready'", timeout=10_000)
    except Exception:
        print(json.dumps({'page_errors':page_errors,'console_errors':console_errors,'requests_tail':requests[-80:],'state':page.evaluate("() => ({shell:document.documentElement.dataset.takMapShell||'',runtime:document.documentElement.dataset.takMapRuntime||'',body:(document.body&&document.body.innerText||'').slice(0,1200),diag:window.TakMapStartupDiagnosticsI553&&TakMapStartupDiagnosticsI553.snapshot?TakMapStartupDiagnosticsI553.snapshot():null})")},indent=2),flush=True)
        raise
    page.wait_for_function("document.documentElement.dataset.takMapRuntime === 'ready'", timeout=35_000)
    page.wait_for_function("window.__takMapDataSyncStartupResultI553 && window.__takMapDataSyncStartupResultI553.rendered === true", timeout=10_000)
    page.wait_for_function("document.querySelector('#geofencePanelV491 .tak-gf-card-head-v491')", timeout=10_000)
    page.wait_for_function("document.querySelector('#dataSyncRows [data-mission-key] .tak-mission-state-i576')", timeout=10_000)
    page.wait_for_timeout(600)
    load_seconds = time.perf_counter() - started

    initial = page.evaluate("""() => {
      const row=document.querySelector('#dataSyncRows [data-mission-key]');
      const status=row&&row.querySelector('.tak-mission-state-i576');
      const edit=row&&row.querySelector('[data-mission-edit-i576]');
      window.__i589InitialStatusNode=status;
      window.__i589InitialEditNode=edit;
      const diag=window.TakMapStartupDiagnosticsI553&&TakMapStartupDiagnosticsI553.snapshot?TakMapStartupDiagnosticsI553.snapshot():{};
      const ctx=window.TakMapContextSidebarI572&&TakMapContextSidebarI572.diagnostics?TakMapContextSidebarI572.diagnostics():null;
      return {
        shell:document.documentElement.dataset.takMapShell,
        runtime:document.documentElement.dataset.takMapRuntime,
        diag,ctx,
        missionState:status&&status.textContent,
        editPresent:!!edit,
        geofencePresent:!!document.getElementById('geofencePanelV491'),
        geofenceObserverAdded:String((window.TakMapGeofencingV491&&TakMapGeofencingV491.diagnostics&&TakMapGeofencingV491.diagnostics())||{}).includes('MutationObserver'),
        packageIteration:(document.querySelector('.iteration-chip')||{}).textContent||'',
      };
    }""")

    assert initial['shell'] == 'ready' and initial['runtime'] == 'ready', initial
    assert initial['diag']['deferredLoaded'] == initial['diag']['deferredTotal'], initial['diag']
    assert initial['diag']['deferredFailed'] == [], initial['diag']
    assert initial['missionState'] == 'Unlocked', initial
    assert initial['editPresent'] is True, initial
    assert initial['geofencePresent'] is True, initial
    assert initial['ctx'] and initial['ctx']['installed'] is True, initial
    assert initial['ctx']['leafletPopupLifecycleUsed'] is False, initial
    assert initial['packageIteration'] == 'i591', initial

    # The active browser resolver must render exact canonical objects without
    # suppressing unrelated Data Sync points.
    icon_results = page.evaluate("""() => {
      const api=window.TakMapMilStd2525CI553;
      const payload=window.__takMapLastDataSyncJsonI553||{};
      const rows=Array.isArray(payload.objects)?payload.objects:[];
      const result={count:rows.length, audit:api&&api.audit?api.audit():null, objects:{}};
      for(const row of rows){
        const key=row.callsign||row.name||row.uid;
        if(!key||!api)continue;
        const resolved=api.resolveSymbol(row);
        result.objects[key]={resolved,html:api.iconHtml(row)};
      }
      return result;
    }""")
    assert icon_results['count'] == 4, icon_results
    sensor = icon_results['objects']['I585-SENSOR']
    tank = icon_results['objects']['I585-TANK']
    radar = icon_results['objects']['I585-RADAR']
    assert sensor['resolved']['file'] == 'friendly-ground-equipment-sensor.svg', sensor
    assert sensor['resolved']['canonicalPrecedenceI579'] is True, sensor
    assert 'friendly-ground-equipment-sensor.svg' in sensor['html'], sensor
    assert tank['resolved']['file'] == 'friendly-ground-equipment-tank.svg', tank
    assert 'friendly-ground-equipment-tank.svg' in tank['html'], tank
    assert radar['resolved']['file'] == 'friendly-ground-equipment-radar.svg', radar
    assert radar['resolved']['canonicalPrecedenceI579'] is True, radar
    assert 'friendly-ground-equipment-radar.svg' in radar['html'], radar
    assert icon_results['audit']['exactCanonicalPrecedenceI579'] is True, icon_results['audit']

    # Refresh with incomplete access metadata. Controls must remain the same DOM
    # nodes and remain Unlocked without any delayed restoration.
    page.evaluate("() => refreshDataSync(true,'i589-browser-stability-test')")
    page.wait_for_timeout(350)
    stable = page.evaluate("""() => {
      const row=document.querySelector('#dataSyncRows [data-mission-key]');
      const status=row&&row.querySelector('.tak-mission-state-i576');
      const edit=row&&row.querySelector('[data-mission-edit-i576]');
      return {
        state:status&&status.textContent,
        statusPresent:!!status,
        editPresent:!!edit,
        sameStatusNode:status===window.__i589InitialStatusNode,
        sameEditNode:edit===window.__i589InitialEditNode,
        finalOwner:window.__takMapMissionRowStableI577||null,
      };
    }""")
    assert stable['state'] == 'Unlocked', stable
    assert stable['statusPresent'] and stable['editPresent'], stable
    assert stable['sameStatusNode'] and stable['sameEditNode'], stable
    assert stable['finalOwner'] and stable['finalOwner']['owner'] == 'takMapObjectLifecycleLoaderV486', stable

    # Geofences header must toggle, the switch must not toggle, keyboard must
    # toggle, and the chevron/background styling must match the approved design.
    geofence_before = page.evaluate("""() => {
      const panel=document.getElementById('geofencePanelV491');
      const head=panel.querySelector('.tak-gf-card-head-v491');
      const arrow=document.getElementById('takGfCollapseV491');
      return {collapsed:panel.classList.contains('collapsed'),bg:getComputedStyle(head).backgroundColor,arrow:getComputedStyle(arrow).color,aria:head.getAttribute('aria-expanded')};
    }""")
    page.click('#geofencePanelV491 .tak-gf-card-head-v491 h2')
    geofence_clicked = page.evaluate("""() => ({collapsed:document.getElementById('geofencePanelV491').classList.contains('collapsed'),aria:document.querySelector('#geofencePanelV491 .tak-gf-card-head-v491').getAttribute('aria-expanded'),hidden:document.getElementById('takGfBodyV491').getAttribute('aria-hidden')})""")
    assert geofence_clicked['collapsed'] != geofence_before['collapsed'], (geofence_before, geofence_clicked)
    assert geofence_clicked['aria'] == ('false' if geofence_clicked['collapsed'] else 'true')
    assert geofence_clicked['hidden'] == ('true' if geofence_clicked['collapsed'] else 'false')

    collapsed_before_switch = geofence_clicked['collapsed']
    page.click('#geofencePanelV491 .tak-gf-switch-v491')
    collapsed_after_switch = page.evaluate("document.getElementById('geofencePanelV491').classList.contains('collapsed')")
    assert collapsed_after_switch == collapsed_before_switch

    page.focus('#geofencePanelV491 .tak-gf-card-head-v491')
    page.keyboard.press('Enter')
    collapsed_after_key = page.evaluate("document.getElementById('geofencePanelV491').classList.contains('collapsed')")
    assert collapsed_after_key != collapsed_after_switch

    page.hover('#geofencePanelV491 .tak-gf-card-head-v491')
    geofence_after = page.evaluate("""() => {const head=document.querySelector('#geofencePanelV491 .tak-gf-card-head-v491');const arrow=document.getElementById('takGfCollapseV491');return {bg:getComputedStyle(head).backgroundColor,arrow:getComputedStyle(arrow).color};}""")
    assert geofence_after['bg'] == geofence_before['bg'], (geofence_before, geofence_after)
    assert geofence_after['arrow'] == 'rgb(184, 195, 203)', geofence_after

    # The three generic layout rows identified by the user must not inherit the
    # silver interactive-row hover background. Actual buttons remain interactive.
    hover_targets = page.evaluate("""() => {
      const buttons=[...document.querySelectorAll('#sidebar button')];
      const byText=t=>buttons.find(b=>(b.textContent||'').trim()===t);
      const refreshSync=byText('Refresh Data Sync')?.closest('.row');
      const showSync=[...document.querySelectorAll('#sidebar label')].find(l=>(l.textContent||'').includes('Show Data Sync objects'))?.closest('.row');
      const localPanel=[...document.querySelectorAll('#sidebar .panel')].find(x=>x.querySelector('h2')&&(x.querySelector('h2').textContent||'').trim().startsWith('Local Data'));
      const refreshLocal=localPanel?.querySelector('.panel-body > .row');
      const pack=(el,name)=>el?{name,className:el.className,bg:getComputedStyle(el).backgroundColor,border:getComputedStyle(el).borderColor}:null;
      return [pack(refreshSync,'refresh-data-sync'),pack(showSync,'show-data-sync-objects'),pack(refreshLocal,'refresh-local-data')];
    }""")
    assert all(hover_targets), hover_targets
    for target in hover_targets:
        selector = {
            'refresh-data-sync': "#sidebar button:text-is('Refresh Data Sync')",
            'show-data-sync-objects': "#sidebar label:has-text('Show Data Sync objects')",
            'refresh-local-data': "#sidebar .panel:has(h2:has-text('Local Data')) .panel-body > .row",
        }[target['name']]
        page.hover(selector)
        after = page.evaluate("""name => {
          const buttons=[...document.querySelectorAll('#sidebar button')];
          const byText=t=>buttons.find(b=>(b.textContent||'').trim()===t);
          let el=null;
          if(name==='refresh-data-sync')el=byText('Refresh Data Sync')?.closest('.row');
          if(name==='show-data-sync-objects')el=[...document.querySelectorAll('#sidebar label')].find(l=>(l.textContent||'').includes('Show Data Sync objects'))?.closest('.row');
          if(name==='refresh-local-data'){const p=[...document.querySelectorAll('#sidebar .panel')].find(x=>x.querySelector('h2')&&(x.querySelector('h2').textContent||'').trim().startsWith('Local Data'));el=p?.querySelector('.panel-body > .row');}
          return el?{bg:getComputedStyle(el).backgroundColor,border:getComputedStyle(el).borderColor}:null;
        }""", target['name'])
        assert after == {'bg': target['bg'], 'border': target['border']}, (target, after)

    # Confirm that the correction did not remove hover feedback from the actual
    # Refresh Data Sync button itself.
    button_before = page.evaluate("""() => {const b=[...document.querySelectorAll('#sidebar button')].find(x=>(x.textContent||'').trim()==='Refresh Data Sync');return {bg:getComputedStyle(b).backgroundColor,border:getComputedStyle(b).borderColor};}""")
    page.hover("#sidebar button:text-is('Refresh Data Sync')")
    button_after = page.evaluate("""() => {const b=[...document.querySelectorAll('#sidebar button')].find(x=>(x.textContent||'').trim()==='Refresh Data Sync');return {bg:getComputedStyle(b).backgroundColor,border:getComputedStyle(b).borderColor};}""")
    assert button_after != button_before, (button_before, button_after)

    # Responsiveness check catches runaway observers/render loops that would
    # freeze the page before the user can test the requested change.
    frame_ms = page.evaluate("() => new Promise(resolve => { const s=performance.now(); requestAnimationFrame(() => resolve(performance.now()-s)); })")
    page.wait_for_timeout(600)
    final_diag = page.evaluate("() => TakMapStartupDiagnosticsI553.snapshot()")
    control_diag = page.evaluate("() => (window.TakMapDataSyncControlI585&&TakMapDataSyncControlI585.diagnostics?TakMapDataSyncControlI585.diagnostics():null)")
    mutation = final_diag.get('mutation', {})
    assert control_diag and control_diag.get('pollTimerInstalled') is True, control_diag
    assert control_diag.get('automaticPollMs') == 5000, control_diag
    assert control_diag.get('pollTicks', 0) >= 1, control_diag
    assert frame_ms < 250, frame_ms
    assert mutation.get('deliveredCallbacks', 0) < 1000, mutation
    assert mutation.get('records', 0) < 50000, mutation
    assert load_seconds < 30, load_seconds
    assert not page_errors, page_errors
    assert not console_errors, console_errors

    browser.close()

print(json.dumps({
    'ok': True,
    'version': 'i589',
    'initial_load_seconds': round(load_seconds, 3),
    'data_sync_requests': data_sync_calls,
    'browser_poll_timer_installed': control_diag.get('pollTimerInstalled'),
    'browser_poll_ticks': control_diag.get('pollTicks'),
    'mission_nodes_stable': True,
    'geofence_header_toggle': True,
    'geofence_switch_excluded': True,
    'contextual_right_sidebar_preserved': True,
    'generic_sidebar_rows_hover_stable': True,
    'generic_sensor_canonical': True,
    'specific_radar_canonical': True,
    'unrelated_tank_preserved': True,
    'animation_frame_ms': round(frame_ms, 3),
    'mutation_callbacks': mutation.get('deliveredCallbacks', 0),
    'mutation_records': mutation.get('records', 0),
    'page_errors': len(page_errors),
    'console_errors': len(console_errors),
}, indent=2))
