#!/usr/bin/env python3
from __future__ import annotations
import importlib.util
import json
import os
import pathlib
import sys
from urllib.parse import urlparse, parse_qs

ROOT = pathlib.Path(__file__).resolve().parents[1]
os.environ['TAK_MAP_MIL_ROOT'] = str(ROOT / 'assets/mil2525')
os.environ['TAK_MAP_TEST_SKIP_ADSB_WARMUP'] = '1'

spec = importlib.util.spec_from_file_location('tak_dashboard_i596_browser', ROOT / 'tak_dashboard.py')
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
HTML = mod.TAK_MAP_HTML
CONFIG = mod.tak_map_config()
LEAFLET = (ROOT / 'scripts/leaflet_stub_test.js').read_text()

LOCKED_A = 'PROTECTED-ALPHA'
LOCKED_B = 'PROTECTED-BRAVO'
OPEN = 'OPEN-CHARLIE'


def access(mission, protected, unlocked):
    return {
        'ok': True, 'version': 'i598', 'mission': mission,
        'protected': protected, 'password_protected': protected,
        'unlocked': unlocked if protected else True,
        'locked': bool(protected and not unlocked),
        'credential_configured': bool(protected and unlocked),
        'password_stored_server_side': bool(protected and unlocked),
    }


def descriptor(mission):
    return {
        'name': mission, 'mission': mission,
        'passwordProtected': True, 'password_protected': True,
        'protected': True, 'locked': True, 'unlocked': False,
        'metadata_only': True, 'locked_descriptor_i594': True,
    }

locked_access = [access(LOCKED_A, True, False), access(LOCKED_B, True, False), access(OPEN, False, True)]
initial_payload = {
    'ok': True, 'version': 'i598', 'partial': True,
    'locked': True, 'requires_mission_password': True, 'mission_password_required': True,
    'missions': [descriptor(LOCKED_A), descriptor(LOCKED_B), {'name': OPEN, 'passwordProtected': False}],
    'objects': [{'mission_name': OPEN, 'uid': 'OPEN-POINT-1', 'callsign': 'OPEN-POINT', 'lat': 34.0, 'lon': -117.0}],
    'packages': [], 'mission_content': [], 'mission_uids': [],
    'warnings': ['One or more protected Missions are locked. Mission names remain visible, but protected contents are withheld.'],
    'mission_access_i595': [],
    'mission_access_i594': locked_access,
    'mission_access_i591': locked_access,
    'mission_access_i576': locked_access,
}

unlocked_access = [access(LOCKED_A, True, True), access(LOCKED_B, True, False), access(OPEN, False, True)]
unlocked_payload = {
    'ok': True, 'version': 'i598', 'partial': True,
    'locked': True, 'requires_mission_password': True, 'mission_password_required': True,
    'missions': [
        {'name': LOCKED_A, 'passwordProtected': True, 'description': 'Authorized Mission'},
        descriptor(LOCKED_B),
        {'name': OPEN, 'passwordProtected': False},
    ],
    'objects': [
        {'mission_name': OPEN, 'uid': 'OPEN-POINT-1', 'callsign': 'OPEN-POINT', 'lat': 34.0, 'lon': -117.0},
        {'mission_name': LOCKED_A, 'uid': 'ALPHA-POINT-1', 'callsign': 'ALPHA-SECRET-POINT', 'lat': 34.1, 'lon': -117.1},
    ],
    'packages': [], 'mission_content': [], 'mission_uids': [],
    'warnings': ['One or more protected Missions are locked. Mission names remain visible, but protected contents are withheld.'],
    'mission_access_i596': unlocked_access,
    'mission_access_i595': [],
    'mission_access_i594': unlocked_access,
    'mission_access_i591': unlocked_access,
    'mission_access_i576': unlocked_access,
}

transitional_payload = {
    'ok': True, 'version': 'i598', 'partial': True,
    'locked': True, 'requires_mission_password': True, 'mission_password_required': True,
    'missions': [], 'objects': [], 'packages': [], 'mission_content': [], 'mission_uids': [],
    'mission_access_i595': [],
    'mission_access_i594': unlocked_access,
    'mission_access_i591': unlocked_access,
    'mission_access_i576': unlocked_access,
    'data_sync_transition_i596': {'version':'i598','refreshing_contents':True},
}


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

errors, consoles, requests = [], [], []
state = {'unlocked_alpha': False, 'data_sync_requests': 0, 'unlock_posts': 0, 'post_unlock_reads': 0}

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage', '--no-first-run', '--disable-background-networking'])
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('console', lambda m: consoles.append(m.text) if m.type == 'error' else None)

    def route_handler(route, request):
        path = urlparse(request.url).path
        requests.append(path)
        if path in ('/', '/tak-map'):
            return route.fulfill(status=200, content_type='text/html', body=HTML)
        if path == '/api/tak-map/config':
            return route.fulfill(status=200, content_type='application/json', body=json.dumps(CONFIG))
        if path == '/api/tak-map/data-sync':
            state['data_sync_requests'] += 1
            if state['unlocked_alpha']:
                state['post_unlock_reads'] += 1
                payload = transitional_payload if state['post_unlock_reads'] <= 2 else unlocked_payload
            else:
                payload = initial_payload
            return route.fulfill(status=200, content_type='application/json', body=json.dumps(payload))
        if path == '/api/tak-map/data-sync-mission-access-i573':
            if request.method == 'POST':
                state['unlock_posts'] += 1
                body = request.post_data_json or {}
                mission = str(body.get('mission') or '')
                if body.get('action') == 'unlock' and mission == LOCKED_A and body.get('password') == 'correct-password':
                    state['unlocked_alpha'] = True
                    return route.fulfill(status=200, content_type='application/json', body=json.dumps(access(LOCKED_A, True, True)))
                return route.fulfill(status=403, content_type='application/json', body=json.dumps({'ok': False, 'error': 'Invalid Mission password.'}))
            mission = parse_qs(urlparse(request.url).query).get('mission', [''])[0]
            rows = unlocked_access if state['unlocked_alpha'] else locked_access
            row = next((x for x in rows if x['mission'] == mission), access(mission, True, False))
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
            fp = ROOT / 'assets' / path[len('/assets/runtime/'):]
            if fp.is_file():
                return route.fulfill(status=200, content_type=ctype(fp), body=fp.read_bytes())
        if path.startswith('/assets/'):
            fp = ROOT / 'assets' / path[len('/assets/'):]
            if fp.is_file():
                return route.fulfill(status=200, content_type=ctype(fp), body=fp.read_bytes())
        return route.fulfill(status=204, body='')

    page.route('**/*', route_handler)
    storage_stub = """(() => { const m=new Map(); const store={getItem:k=>m.has(String(k))?m.get(String(k)):null,setItem:(k,v)=>m.set(String(k),String(v)),removeItem:k=>m.delete(String(k)),clear:()=>m.clear(),key:i=>Array.from(m.keys())[i]||null,get length(){return m.size}}; try{Object.defineProperty(window,'localStorage',{value:store,configurable:true})}catch(_){} try{Object.defineProperty(window,'sessionStorage',{value:store,configurable:true})}catch(_){} })();"""
    page.add_init_script(storage_stub)
    page.evaluate(storage_stub)
    page.set_content(HTML.replace('<head>', '<head><base href="https://example.test/">', 1), wait_until='domcontentloaded', timeout=20000)
    page.wait_for_function("document.documentElement.dataset.takMapShell==='ready'", timeout=15000)
    page.wait_for_function("document.documentElement.dataset.takMapRuntime==='ready'", timeout=45000)
    page.wait_for_function(f"document.querySelector('#dataSyncRows [data-mission-edit-i576][data-mission=\"{LOCKED_A}\"]')", timeout=12000)
    page.wait_for_timeout(800)

    initial = page.evaluate("""() => ({
      iteration:(document.querySelector('.iteration-chip')||{}).textContent||'',
      text:(document.getElementById('dataSyncRows')||{}).innerText||'',
      manual:!!document.querySelector('#dataSyncRows [data-mission-manual-i591]'),
      alpha:!!document.querySelector("#dataSyncRows [data-mission-edit-i576][data-mission='PROTECTED-ALPHA']"),
      bravo:!!document.querySelector("#dataSyncRows [data-mission-edit-i576][data-mission='PROTECTED-BRAVO']"),
      states:Array.from(document.querySelectorAll('#dataSyncRows .tak-mission-card-i576')).map(card=>({name:(card.querySelector('b')||{}).textContent||'',state:(card.querySelector('.tak-mission-state-i576')||{}).textContent||''})),
      owner:window.__takMapMissionRowFinalRendererI576||null
    })""")
    assert initial['iteration'] == 'i598', initial
    assert initial['alpha'] and initial['bravo'] and not initial['manual'], initial
    assert LOCKED_A in initial['text'] and LOCKED_B in initial['text'] and OPEN in initial['text'], initial
    assert 'ALPHA-SECRET-POINT' not in initial['text'] and 'BRAVO-HIDDEN-POINT' not in initial['text'], initial
    by_name = {row['name']: row['state'] for row in initial['states']}
    assert by_name[LOCKED_A] == 'Locked' and by_name[LOCKED_B] == 'Locked', initial
    assert initial['owner']['package'] == 'i598' and initial['owner']['manualMissionEntry'] is False, initial

    # Cross the regular five-second polling interval. Mission rows and Edit
    # controls must remain stable and must not be replaced by manual name entry.
    page.wait_for_timeout(6200)
    after_poll = page.evaluate("""() => ({text:(document.getElementById('dataSyncRows')||{}).innerText||'',manual:!!document.querySelector('#dataSyncRows [data-mission-manual-i591]'),edits:Array.from(document.querySelectorAll('#dataSyncRows [data-mission-edit-i576]')).map(x=>x.getAttribute('data-mission'))})""")
    assert not after_poll['manual'] and LOCKED_A in after_poll['edits'] and LOCKED_B in after_poll['edits'], after_poll

    page.click(f'#dataSyncRows [data-mission-edit-i576][data-mission="{LOCKED_A}"]')
    page.wait_for_function("!document.getElementById('takMapMissionAccessDialogI576').hidden", timeout=5000)
    dialog = page.evaluate("""() => ({
      mission:(document.getElementById('takMapMissionNameI591')||{}).value||'',
      missionFieldHidden:(document.querySelector('#takMapMissionAccessDialogI576 .mission-access-name-i591')||{}).hidden,
      copy:(document.querySelector('#takMapMissionAccessDialogI576 .mission-access-copy-i576')||{}).textContent||''
    })""")
    assert dialog['mission'] == LOCKED_A and dialog['missionFieldHidden'] is True, dialog
    assert LOCKED_A in dialog['copy'], dialog
    page.fill('#takMapMissionPasswordI576', 'correct-password')
    page.click('#takMapMissionAccessDialogI576 button[type="submit"]')
    page.wait_for_function("Array.from(document.querySelectorAll('#dataSyncRows .tak-mission-state-i576')).some(x=>x.textContent.trim()==='Unlocked')", timeout=7000)
    assert page.locator('#dataSyncRows .tak-mission-state-i576').filter(has_text='refreshing contents').count() == 0
    transition = page.evaluate("() => ({text:(document.getElementById('dataSyncRows')||{}).innerText||'',edits:Array.from(document.querySelectorAll('#dataSyncRows [data-mission-edit-i576]')).map(x=>x.getAttribute('data-mission'))})")
    assert LOCKED_A in transition['text'] and LOCKED_A in transition['edits'], transition
    assert 'No Missions discovered' not in transition['text'], transition
    page.wait_for_function("document.body.innerText.includes('ALPHA-SECRET-POINT')", timeout=12000)
    page.wait_for_timeout(700)

    unlocked = page.evaluate("""() => ({
      text:(document.getElementById('dataSyncRows')||{}).innerText||'',
      states:Array.from(document.querySelectorAll('#dataSyncRows .tak-mission-card-i576')).map(card=>({name:(card.querySelector('b')||{}).textContent||'',state:(card.querySelector('.tak-mission-state-i576')||{}).textContent||''})),
      manual:!!document.querySelector('#dataSyncRows [data-mission-manual-i591]')
    })""")
    by_name = {row['name']: row['state'] for row in unlocked['states']}
    assert by_name[LOCKED_A] == 'Unlocked' and by_name[LOCKED_B] == 'Locked', unlocked
    assert 'ALPHA-SECRET-POINT' in unlocked['text'] and 'BRAVO-HIDDEN-POINT' not in unlocked['text'], unlocked
    assert not unlocked['manual'], unlocked

    assert state['unlock_posts'] == 1 and state['data_sync_requests'] >= 2, state
    assert not errors and not consoles, {'errors': errors, 'console': consoles, 'requests': requests[-80:]}
    browser.close()

print(json.dumps({
    'ok': True, 'version': 'i598',
    'locked_mission_names_visible_before_password': True,
    'manual_mission_name_entry_removed': True,
    'polling_stable': True,
    'mixed_locked_unlocked_after_password': True,
    'data_sync_requests': state['data_sync_requests'],
}, indent=2))
