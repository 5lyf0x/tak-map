#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import sys
import time
from urllib.parse import parse_qs, urlparse

ROOT = pathlib.Path(__file__).resolve().parents[1]
os.environ['TAK_MAP_MIL_ROOT'] = str(ROOT / 'assets/mil2525')
os.environ['TAK_MAP_TEST_SKIP_ADSB_WARMUP'] = '1'

spec = importlib.util.spec_from_file_location('tak_dashboard_i601_browser', ROOT / 'tak_dashboard.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
assert spec.loader
spec.loader.exec_module(mod)
assert mod.TAK_MAP_ITERATION == 'i601'
HTML = mod.TAK_MAP_HTML
CONFIG = mod.tak_map_config()
LEAFLET = (ROOT / 'scripts/leaflet_stub_test.js').read_text()

ALPHA = 'PROTECTED-ALPHA'
BRAVO = 'PROTECTED-BRAVO'
OPEN = 'OPEN-CHARLIE'


def access(mission: str, protected: bool, unlocked: bool, state: str) -> dict:
    unlocked = bool(unlocked or not protected)
    return {
        'ok': True,
        'version': 'i601',
        'mission': mission,
        'name': mission,
        'protected': protected,
        'password_protected': protected,
        'passwordProtected': protected,
        'unlocked': unlocked,
        'locked': bool(protected and not unlocked),
        'credential_configured': bool(protected and unlocked),
        'password_stored_server_side': bool(protected and unlocked),
        'metadata_only': bool(protected and not unlocked),
        'locked_descriptor_i594': bool(protected and not unlocked),
        'content_state_i599': state,
        'content_authoritative_i599': state == 'ready',
        'content_error_i599': '',
    }


def mission_row(mission: str, protected: bool, locked: bool = False) -> dict:
    return {
        'name': mission,
        'mission': mission,
        'passwordProtected': protected,
        'password_protected': protected,
        'protected': protected,
        'locked': bool(locked),
        'unlocked': bool(not locked),
        'metadata_only': bool(locked),
        'locked_descriptor_i594': bool(locked),
    }


def background(generation: int, completed: int, running: bool, transitional: bool) -> dict:
    return {
        'version': 'i601',
        'state': 'loading' if running else 'ready',
        'snapshot_available': True,
        'worker_running': running,
        'refreshing': running,
        'generation': generation,
        'completed_generation': completed,
        'snapshot_generation': completed,
        'transitional_response': transitional,
        'single_polling_owner': True,
        'security_filter_read_only': True,
        'last_known_good_preserved': True,
    }


def payload(access_rows: list[dict], missions: list[dict], objects: list[dict], generation: int,
            completed: int, running: bool = False, transitional: bool = False) -> dict:
    any_locked = any(row.get('locked') for row in access_rows)
    any_unlocked = any(row.get('unlocked') for row in access_rows)
    data = {
        'ok': True,
        'version': 'i601',
        'partial': bool(any_locked),
        'locked': bool(any_locked and not any_unlocked),
        'partially_locked_i599': bool(any_locked and any_unlocked),
        'requires_mission_password': bool(any_locked),
        'mission_password_required': bool(any_locked),
        'missions': missions,
        'objects': objects,
        'packages': [],
        'mission_content': [],
        'mission_uids': [dict(row) for row in objects],
        'warnings': [],
        'mission_access_i599': access_rows,
        'data_sync_background_i599': background(generation, completed, running, transitional),
    }
    # Compatibility arrays must be identical projections of the canonical state.
    for key in ('mission_access_i596', 'mission_access_i595', 'mission_access_i594', 'mission_access_i591', 'mission_access_i576'):
        data[key] = json.loads(json.dumps(access_rows))
    return data


locked_access = [
    access(ALPHA, True, False, 'locked'),
    access(BRAVO, True, False, 'locked'),
    access(OPEN, False, True, 'ready'),
]
loading_access = [
    access(ALPHA, True, True, 'loading'),
    access(BRAVO, True, False, 'locked'),
    access(OPEN, False, True, 'ready'),
]
ready_access = [
    access(ALPHA, True, True, 'ready'),
    access(BRAVO, True, False, 'locked'),
    access(OPEN, False, True, 'ready'),
]
relocked_access = [
    access(ALPHA, True, False, 'locked'),
    access(BRAVO, True, False, 'locked'),
    access(OPEN, False, True, 'ready'),
]
empty_ready_access = [
    access(ALPHA, True, False, 'locked'),
    access(BRAVO, True, True, 'ready'),
    access(OPEN, False, True, 'ready'),
]
error_access = [
    access(ALPHA, True, True, 'error'),
    access(BRAVO, True, False, 'locked'),
    access(OPEN, False, True, 'ready'),
]
error_access[0]['content_error_i599'] = 'temporary Mission /cot outage'

OPEN_OBJECT = {'mission_name': OPEN, 'mission': OPEN, 'uid': 'OPEN-POINT-1', 'callsign': 'OPEN-POINT', 'lat': 34.0, 'lon': -117.0}
ALPHA_OBJECT = {'mission_name': ALPHA, 'mission': ALPHA, 'uid': 'ALPHA-POINT-1', 'callsign': 'ALPHA-SECRET-POINT', 'lat': 34.1, 'lon': -117.1}

INITIAL = payload(
    locked_access,
    [mission_row(ALPHA, True, True), mission_row(BRAVO, True, True), mission_row(OPEN, False)],
    [OPEN_OBJECT], 1, 1,
)
# Deliberately empty collections emulate the request that lands while the worker
# is still acquiring the authorized Mission. The browser must preserve completed
# objects and update access/loading state without promoting this as last-known-good.
TRANSITIONAL = payload(
    loading_access,
    [], [], 2, 1, running=True, transitional=True,
)
READY = payload(
    ready_access,
    [mission_row(ALPHA, True), mission_row(BRAVO, True, True), mission_row(OPEN, False)],
    [OPEN_OBJECT, ALPHA_OBJECT], 2, 2,
)
RELOCKED = payload(
    relocked_access,
    [mission_row(ALPHA, True, True), mission_row(BRAVO, True, True), mission_row(OPEN, False)],
    [OPEN_OBJECT], 3, 3,
)
EMPTY_READY = payload(
    empty_ready_access,
    [mission_row(ALPHA, True, True), mission_row(BRAVO, True), mission_row(OPEN, False)],
    [OPEN_OBJECT], 4, 4,
)
ERROR_READY = payload(
    error_access,
    [mission_row(ALPHA, True), mission_row(BRAVO, True, True), mission_row(OPEN, False)],
    [OPEN_OBJECT, ALPHA_OBJECT], 5, 5,
)
ERROR_READY['partial'] = True
ERROR_READY['warnings'] = ['Mission content refresh failed for PROTECTED-ALPHA. Last-known-good data was preserved.']

RESPONSES = {
    '/api/tak-map/status-banner': {'ok': True},
    '/api/tak-map/cot': {'ok': True, 'markers': []},
    '/api/tak-map/euds': {'ok': True, 'euds': []},
    '/api/tak-map/local-data': {'ok': True, 'routes': [], 'points': [], 'shapes': []},
    '/api/tak-map/imported': {'ok': True, 'imports': []},
    '/api/tak-map/offline-maps': {'ok': True, 'maps': [], 'jobs': []},
    '/api/tak-map/geofences': {'ok': True, 'geofences': []},
    '/api/tak-map/custom-basemaps': {'ok': True, 'basemaps': []},
    '/api/tak-map/account/tak-identity': {'ok': True, 'callsign': 'ALICE', 'username': 'alice'},
    '/api/tak-map/account/sentinel-hub': {'ok': True, 'configured': False},
    '/api/tak-map/ots/session': {'ok': True, 'authenticated': True, 'username': 'alice', 'callsign': 'ALICE'},
    '/api/tak-map/icon-registry/summary': {'ok': True, 'iconsets': []},
    '/api/tak-map/icon-registry/sets': {'ok': True, 'iconsets': []},
    '/api/tak-map/tile-cache-status': {'ok': True, 'bytes': 0},
    '/api/tak-map/adsb-settings': {'ok': True, 'settings': {'enabled': False}},
    '/api/tak-map/adsb': {'ok': True, 'aircraft': []},
}


def ctype(path: pathlib.Path) -> str:
    return {
        '.js': 'application/javascript', '.json': 'application/json', '.css': 'text/css',
        '.svg': 'image/svg+xml', '.png': 'image/png', '.woff2': 'font/woff2',
    }.get(path.suffix.lower(), 'application/octet-stream')


from playwright.sync_api import sync_playwright

errors: list[str] = []
consoles: list[str] = []
requests: list[dict] = []
state = {
    'mode': 'locked',
    'data_sync_requests': 0,
    'unlock_posts': 0,
    'post_unlock_reads': 0,
    'unlock_time': 0.0,
}

with sync_playwright() as pw:
    browser = pw.chromium.launch(
        headless=True,
        executable_path='/usr/bin/chromium',
        args=['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage', '--no-first-run', '--disable-background-networking'],
    )
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.on('console', lambda message: consoles.append(message.text) if message.type == 'error' else None)

    def route_handler(route, request):
        parsed = urlparse(request.url)
        path = parsed.path
        now = time.monotonic()
        if path in ('/', '/tak-map'):
            return route.fulfill(status=200, content_type='text/html', body=HTML)
        if path == '/api/tak-map/config':
            return route.fulfill(status=200, content_type='application/json', body=json.dumps(CONFIG))
        if path == '/api/tak-map/data-sync':
            state['data_sync_requests'] += 1
            reason = parse_qs(parsed.query).get('reason', [''])[0]
            requests.append({'path': path, 'reason': reason, 'at': now, 'method': request.method})
            if state['mode'] == 'locked':
                answer = INITIAL
            elif state['mode'] == 'unlocking':
                state['post_unlock_reads'] += 1
                if now - state['unlock_time'] < 4.0:
                    answer = TRANSITIONAL
                else:
                    state['mode'] = 'ready'
                    answer = READY
            elif state['mode'] == 'ready':
                answer = READY
            elif state['mode'] == 'relocked':
                answer = RELOCKED
            elif state['mode'] == 'empty_ready':
                answer = EMPTY_READY
            else:
                answer = ERROR_READY
            return route.fulfill(status=200, content_type='application/json', body=json.dumps(answer))
        if path == '/api/tak-map/data-sync-mission-access-i573':
            if request.method == 'POST':
                state['unlock_posts'] += 1
                body = request.post_data_json or {}
                mission = str(body.get('mission') or '')
                if body.get('action') == 'unlock' and mission == ALPHA and body.get('password') == 'correct-password':
                    state['mode'] = 'unlocking'
                    state['post_unlock_reads'] = 0
                    state['unlock_time'] = now
                    answer = access(ALPHA, True, True, 'loading')
                    answer['message'] = 'Mission unlocked for this TAK Map user.'
                    return route.fulfill(status=200, content_type='application/json', body=json.dumps(answer))
                return route.fulfill(status=403, content_type='application/json', body=json.dumps({'ok': False, 'error': 'Invalid Mission password.'}))
            mission = parse_qs(parsed.query).get('mission', [''])[0]
            if state['mode'] == 'locked': rows = locked_access
            elif state['mode'] == 'relocked': rows = relocked_access
            elif state['mode'] == 'unlocking': rows = loading_access
            elif state['mode'] == 'empty_ready': rows = empty_ready_access
            elif state['mode'] == 'error_ready': rows = error_access
            else: rows = ready_access
            row = next((item for item in rows if item['mission'] == mission), access(mission, True, False, 'locked'))
            return route.fulfill(status=200, content_type='application/json', body=json.dumps(row))
        if 'leaflet' in request.url and path.endswith('.js'):
            return route.fulfill(status=200, content_type='application/javascript', body=LEAFLET)
        if path.endswith('leaflet.css'):
            return route.fulfill(status=200, content_type='text/css', body=(ROOT / 'assets/vendor/leaflet-1.9.4/leaflet.css').read_bytes())
        if path == '/mil2525/icons.json':
            return route.fulfill(status=200, content_type='application/json', body=(ROOT / 'assets/mil2525/icons.json').read_bytes())
        if path.startswith('/mil2525/svg/'):
            return route.fulfill(status=200, content_type='image/svg+xml', body=b'<svg xmlns="http://www.w3.org/2000/svg"/>')
        if path.startswith('/api/tak-map/'):
            return route.fulfill(status=200, content_type='application/json', body=json.dumps(RESPONSES.get(path, {'ok': True})))
        if path.startswith('/assets/runtime/'):
            file_path = ROOT / 'assets' / path[len('/assets/runtime/'):]
            if file_path.is_file():
                return route.fulfill(status=200, content_type=ctype(file_path), body=file_path.read_bytes())
        if path.startswith('/assets/'):
            file_path = ROOT / 'assets' / path[len('/assets/'):]
            if file_path.is_file():
                return route.fulfill(status=200, content_type=ctype(file_path), body=file_path.read_bytes())
        return route.fulfill(status=204, body='')

    page.route('**/*', route_handler)
    storage_stub = """(() => { const m=new Map(); const store={getItem:k=>m.has(String(k))?m.get(String(k)):null,setItem:(k,v)=>m.set(String(k),String(v)),removeItem:k=>m.delete(String(k)),clear:()=>m.clear(),key:i=>Array.from(m.keys())[i]||null,get length(){return m.size}}; try{Object.defineProperty(window,'localStorage',{value:store,configurable:true})}catch(_){} try{Object.defineProperty(window,'sessionStorage',{value:store,configurable:true})}catch(_){} })();"""
    page.add_init_script(storage_stub)
    page.evaluate(storage_stub)
    page.set_content(HTML.replace('<head>', '<head><base href="https://example.test/">', 1), wait_until='domcontentloaded', timeout=20000)
    page.wait_for_function("document.documentElement.dataset.takMapShell==='ready'", timeout=15000)
    page.wait_for_function("document.documentElement.dataset.takMapRuntime==='ready'", timeout=45000)
    page.wait_for_function(f"document.querySelector('#dataSyncRows [data-mission-edit-i576][data-mission=\"{ALPHA}\"]')", timeout=15000)
    page.wait_for_timeout(700)

    initial = page.evaluate("""() => ({
      iteration:(document.querySelector('.iteration-chip')||{}).textContent||'',
      text:(document.getElementById('dataSyncRows')||{}).innerText||'',
      states:Array.from(document.querySelectorAll('#dataSyncRows .tak-mission-card-i576')).map(card=>({name:(card.querySelector('b')||{}).textContent||'',state:(card.querySelector('.tak-mission-state-i576')||{}).textContent||''})),
      objects:(window.__takMapLastDataSyncJsonI553&&window.__takMapLastDataSyncJsonI553.objects||[]).map(x=>x.callsign||x.uid),
      manual:!!document.querySelector('#dataSyncRows [data-mission-manual-i591]'),
      owner:window.__takMapMissionRowFinalRendererI576||null
    })""")
    assert initial['iteration'] == 'i601', initial
    assert not initial['manual'], initial
    by_name = {row['name']: row['state'].strip() for row in initial['states']}
    assert by_name[ALPHA] == 'Locked' and by_name[BRAVO] == 'Locked', initial
    assert OPEN_OBJECT['callsign'] in initial['text'] and ALPHA_OBJECT['callsign'] not in initial['text'], initial

    page.click(f'#dataSyncRows [data-mission-edit-i576][data-mission="{ALPHA}"]')
    page.wait_for_function("!document.getElementById('takMapMissionAccessDialogI576').hidden", timeout=5000)
    page.fill('#takMapMissionPasswordI576', 'correct-password')
    page.click('#takMapMissionAccessDialogI576 button[type="submit"]')
    page.wait_for_function("Array.from(document.querySelectorAll('#dataSyncRows .tak-mission-card-i576')).some(card => (card.querySelector('b')||{}).textContent==='PROTECTED-ALPHA' && (card.querySelector('.tak-mission-state-i576')||{}).textContent.trim()==='Unlocked')", timeout=7000)
    page.wait_for_function("document.body.innerText.includes('Refreshing Mission contents')", timeout=7000)

    # There must be one forced read after unlock, not four delayed follow-ups.
    page.wait_for_timeout(2800)
    rapid = [item for item in requests if state['unlock_time'] and item['at'] >= state['unlock_time'] and item['at'] - state['unlock_time'] < 3.0]
    assert len(rapid) <= 2, rapid
    assert not any('followup' in item['reason'].lower() for item in requests), requests

    transition = page.evaluate("""() => ({
      text:(document.getElementById('dataSyncRows')||{}).innerText||'',
      objects:(window.__takMapLastDataSyncJsonI553&&window.__takMapLastDataSyncJsonI553.objects||[]).map(x=>x.callsign||x.uid),
      state:(Array.from(document.querySelectorAll('#dataSyncRows .tak-mission-card-i576')).find(card=>(card.querySelector('b')||{}).textContent==='PROTECTED-ALPHA')?.querySelector('.tak-mission-state-i576')||{}).textContent||'',
      diagnostics:window.TakMapDataSyncControlI553&&window.TakMapDataSyncControlI553.diagnostics?window.TakMapDataSyncControlI553.diagnostics():null,
      refreshSource:String(window.refreshDataSync||'').slice(0,300),
      fetchSource:String(window.fetch||'').slice(0,300)
    })""")
    assert transition['state'].strip() == 'Unlocked', transition
    assert OPEN_OBJECT['callsign'] in transition['objects'], transition
    assert ALPHA in transition['text'] and 'Refreshing Mission contents' in transition['text'], transition

    # The single automatic polling owner retrieves the completed generation.
    page.wait_for_function("document.body.innerText.includes('ALPHA-SECRET-POINT')", timeout=9000)
    page.wait_for_timeout(500)
    ready = page.evaluate("""() => ({
      text:(document.getElementById('dataSyncRows')||{}).innerText||'',
      states:Array.from(document.querySelectorAll('#dataSyncRows .tak-mission-card-i576')).map(card=>({name:(card.querySelector('b')||{}).textContent||'',state:(card.querySelector('.tak-mission-state-i576')||{}).textContent||''})),
      objects:(window.__takMapLastDataSyncJsonI553&&window.__takMapLastDataSyncJsonI553.objects||[]).map(x=>x.callsign||x.uid),
      diagnostics:window.TakMapDataSyncControlI553&&window.TakMapDataSyncControlI553.diagnostics?window.TakMapDataSyncControlI553.diagnostics():null
    })""")
    by_name = {row['name']: row['state'].strip() for row in ready['states']}
    assert by_name[ALPHA] == 'Unlocked' and by_name[BRAVO] == 'Locked', ready
    assert set(ready['objects']) >= {OPEN_OBJECT['callsign'], ALPHA_OBJECT['callsign']}, ready
    assert 'Refreshing Mission contents' not in ready['text'], ready
    assert ready['diagnostics']['pollTimerInstalled'] is True, ready
    assert ready['diagnostics']['requests'] >= 3 and ready['diagnostics']['networkRequests'] >= 2, ready
    assert page.evaluate("() => !!(window.refreshDataSync && window.refreshDataSync.__takMapI599Owner)") is True

    # A completed backend relock/token-expiry snapshot must override the prior
    # unlocked client state and remove only that Mission's objects.
    state['mode'] = 'relocked'
    page.evaluate("() => window.refreshDataSync(true,'i601-test-token-expiry')")
    page.wait_for_function("Array.from(document.querySelectorAll('#dataSyncRows .tak-mission-card-i576')).some(card => (card.querySelector('b')||{}).textContent==='PROTECTED-ALPHA' && (card.querySelector('.tak-mission-state-i576')||{}).textContent.trim()==='Locked')", timeout=7000)
    page.wait_for_timeout(400)
    relocked = page.evaluate("""() => ({
      text:(document.getElementById('dataSyncRows')||{}).innerText||'',
      objects:(window.__takMapLastDataSyncJsonI553&&window.__takMapLastDataSyncJsonI553.objects||[]).map(x=>x.callsign||x.uid),
      states:Array.from(document.querySelectorAll('#dataSyncRows .tak-mission-state-i576')).map(x=>x.textContent.trim())
    })""")
    assert ALPHA_OBJECT['callsign'] not in relocked['objects'] and OPEN_OBJECT['callsign'] in relocked['objects'], relocked
    assert all(value in ('Locked', 'Unlocked') for value in relocked['states']), relocked

    # A completed, authorized empty Mission is ready rather than perpetually
    # loading, and it authoritatively contributes no objects.
    state['mode'] = 'empty_ready'
    page.evaluate("() => window.refreshDataSync(true,'i601-test-authorized-empty')")
    page.wait_for_function("Array.from(document.querySelectorAll('#dataSyncRows .tak-mission-card-i576')).some(card => (card.querySelector('b')||{}).textContent==='PROTECTED-BRAVO' && (card.querySelector('.tak-mission-state-i576')||{}).textContent.trim()==='Unlocked')", timeout=7000)
    page.wait_for_timeout(300)
    empty_ready = page.evaluate("""() => ({
      text:(document.getElementById('dataSyncRows')||{}).innerText||'',
      objects:(window.__takMapLastDataSyncJsonI553&&window.__takMapLastDataSyncJsonI553.objects||[]).map(x=>x.callsign||x.uid)
    })""")
    assert 'Refreshing Mission contents' not in empty_ready['text'], empty_ready
    assert empty_ready['objects'] == [OPEN_OBJECT['callsign']], empty_ready

    # A completed error state preserves that Mission's last-known-good object and
    # stops the loading message instead of appearing to refresh forever.
    state['mode'] = 'error_ready'
    page.evaluate("() => window.refreshDataSync(true,'i601-test-mission-error-lkg')")
    page.wait_for_function("Array.from(document.querySelectorAll('#dataSyncRows .tak-mission-card-i576')).some(card => (card.querySelector('b')||{}).textContent==='PROTECTED-ALPHA' && (card.querySelector('.tak-mission-state-i576')||{}).textContent.trim()==='Unlocked')", timeout=7000)
    page.wait_for_timeout(300)
    error_ready = page.evaluate("""() => ({
      text:(document.getElementById('dataSyncRows')||{}).innerText||'',
      objects:(window.__takMapLastDataSyncJsonI553&&window.__takMapLastDataSyncJsonI553.objects||[]).map(x=>x.callsign||x.uid),
      states:Array.from(document.querySelectorAll('#dataSyncRows .tak-mission-state-i576')).map(x=>x.textContent.trim())
    })""")
    assert 'Refreshing Mission contents' not in error_ready['text'], error_ready
    assert set(error_ready['objects']) >= {OPEN_OBJECT['callsign'], ALPHA_OBJECT['callsign']}, error_ready
    assert all(value in ('Locked', 'Unlocked') for value in error_ready['states']), error_ready

    assert state['unlock_posts'] == 1, state
    assert not errors and not consoles, {'errors': errors, 'console': consoles, 'requests': requests[-80:]}
    browser.close()

print(json.dumps({
    'ok': True,
    'version': 'i601',
    'locked_names_visible': True,
    'single_unlock_refresh': True,
    'transitional_snapshot_preserved': True,
    'mixed_lock_states_preserved': True,
    'completed_objects_rendered': True,
    'backend_relock_authoritative': True,
    'authorized_empty_stops_loading': True,
    'mission_error_stops_loading_and_preserves_lkg': True,
    'data_sync_requests': state['data_sync_requests'],
}, indent=2))
