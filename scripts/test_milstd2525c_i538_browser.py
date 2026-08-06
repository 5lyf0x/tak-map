#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = (ROOT / 'assets' / 'tak-map-milstd2525c-i538.js').read_text()
CATALOG = json.loads((ROOT / 'assets' / 'mil2525' / 'icons.json').read_text())
SVG_ROOT = ROOT / 'assets' / 'mil2525' / 'svg'

MISSION_UID = 'ANDROID-ATAK-AIR-DEFENSE-123'
MISSION = {
    'ok': True,
    'objects': [{
        'uid': MISSION_UID,
        'lat': 34.25,
        'lon': -118.25,
        'cot_type': 'a-f-G-U-C-D',
        'callsign': 'AD-1',
    }],
}
LIVE = {
    'ok': True,
    'markers': [
        {'uid': MISSION_UID, 'lat': 34.25, 'lon': -118.25, 'cot_type': 'a-f-G-U'},
        {'uid': 'ANDROID-OTHER', 'lat': 34.25, 'lon': -118.25, 'cot_type': 'a-f-G-U-C-D'},
    ],
}
EUDS = {
    'ok': True,
    'euds': [
        {'uid': MISSION_UID, 'lat': 34.25, 'lon': -118.25, 'cot_type': 'a-f-G-U'},
        {'uid': 'ANDROID-OTHER', 'lat': 34.25, 'lon': -118.25, 'cot_type': 'a-f-G-U-C-D'},
    ],
}


def page_script() -> str:
    return f'''window.__refreshCotCalls=0;
window.__refreshEudCalls=0;
window.refreshCot=function(){{window.__refreshCotCalls++}};
window.fetchEudsForDropdown=function(){{window.__refreshEudCalls++}};
const CATALOG={json.dumps(CATALOG)};
const MISSION={json.dumps(MISSION)};
const LIVE={json.dumps(LIVE)};
const EUDS={json.dumps(EUDS)};
window.fetch=async function(input){{
  const url=String((input&&input.url)||input||'');
  if(url.includes('/mil2525/icons.json')) return new Response(JSON.stringify(CATALOG),{{status:200,headers:{{'content-type':'application/json'}}}});
  if(url.includes('/api/tak-map/data-sync')) return new Response(JSON.stringify(MISSION),{{status:200,headers:{{'content-type':'application/json'}}}});
  if(url.includes('/api/tak-map/cot')) return new Response(JSON.stringify(LIVE),{{status:200,headers:{{'content-type':'application/json'}}}});
  if(url.includes('/api/tak-map/euds')) return new Response(JSON.stringify(EUDS),{{status:200,headers:{{'content-type':'application/json'}}}});
  return new Response(JSON.stringify({{ok:true}}),{{status:200,headers:{{'content-type':'application/json'}}}});
}};'''


def run_case(page, live_first: bool) -> None:
    page.set_content('<!doctype html><html><head></head><body></body></html>', wait_until='domcontentloaded')
    page.add_script_tag(content=page_script())
    page.add_script_tag(content=RUNTIME)
    page.wait_for_function("window.TakMapMilStd2525CI538 && window.TakMapMilStd2525CI538.audit().catalogCount===1448")

    if live_first:
        initial = page.evaluate("fetch('/api/tak-map/cot').then(r=>r.json())")
        assert len(initial['markers']) == 2, initial

    data_sync = page.evaluate("fetch('/api/tak-map/data-sync?force=1').then(r=>r.json())")
    assert data_sync['objects'][0]['uid'] == MISSION_UID
    page.wait_for_timeout(100)

    cot = page.evaluate("fetch('/api/tak-map/cot').then(async r=>({json:await r.json(),header:r.headers.get('x-tak-map-mission-uid-ownership')}))")
    assert cot['header'] == 'i538', cot
    assert [row['uid'] for row in cot['json']['markers']] == ['ANDROID-OTHER'], cot

    euds = page.evaluate("fetch('/api/tak-map/euds?online=1').then(async r=>({json:await r.json(),header:r.headers.get('x-tak-map-mission-uid-ownership')}))")
    assert euds['header'] == 'i538', euds
    assert [row['uid'] for row in euds['json']['euds']] == ['ANDROID-OTHER'], euds

    audit = page.evaluate("window.TakMapMilStd2525CI538.audit()")
    assert audit['exactMissionPointUidCount'] == 1, audit
    assert audit['fetchFilterPatched'] is True, audit
    assert page.evaluate("window.__refreshCotCalls") >= 1
    assert page.evaluate("window.__refreshEudCalls") >= 1

    cases = page.evaluate("""(() => {
      const r=window.TakMapMilStd2525CI538;
      return [
        r.resolveSymbol({properties:{mil2525_name:'FRIENDLY-GROUND-UNIT-AIR-DEFENSE.SVG'}}),
        r.resolveSymbol({detail:{usericon:{'@iconsetpath':'COT_MAPPING_2525C/a-h-G-U-C-D'}}}),
        r.resolveSymbol({eventType:'SNGPUCD--------'})
      ];
    })()""")
    assert [row['file'] for row in cases] == [
        'friendly-ground-unit-air-defense.svg',
        'hostile-ground-unit-air-defense.svg',
        'neutral-ground-unit-air-defense.svg',
    ], cases


def run_exhaustive_image_decode(page) -> None:
    page.set_content('<!doctype html><html><head></head><body><div id="icons"></div></body></html>', wait_until='domcontentloaded')
    page.add_script_tag(content=page_script())
    page.add_script_tag(content=RUNTIME)
    page.wait_for_function("window.TakMapMilStd2525CI538 && window.TakMapMilStd2525CI538.audit().catalogCount===1448")
    svg_map = {path.stem: path.read_text(encoding='utf-8') for path in SVG_ROOT.glob('*.svg')}
    result = page.evaluate("""async ({catalog, svgMap}) => {
      const host = document.getElementById('icons');
      host.style.cssText = 'position:fixed;left:-10000px;top:-10000px;width:1px;height:1px;overflow:hidden';
      const failures = [];
      let loaded = 0;
      for (let offset = 0; offset < catalog.length; offset += 80) {
        const batch = catalog.slice(offset, offset + 80);
        await Promise.all(batch.map(row => new Promise(resolve => {
          const source = svgMap[row.name];
          if (!source) {
            failures.push({name: row.name, reason: 'missing-source'});
            resolve();
            return;
          }
          const blobUrl = URL.createObjectURL(new Blob([source], {type: 'image/svg+xml'}));
          const img = new Image();
          img.className = 'tak-mil2525-img';
          img.width = 32;
          img.height = 20;
          img.onload = () => {
            if (img.naturalWidth > 0 && img.naturalHeight > 0) loaded++;
            else failures.push({name: row.name, reason: 'zero-dimensions'});
            URL.revokeObjectURL(blobUrl);
            resolve();
          };
          img.onerror = () => {
            failures.push({name: row.name, reason: 'decode-error'});
            URL.revokeObjectURL(blobUrl);
            resolve();
          };
          img.src = blobUrl;
          host.appendChild(img);
        })));
      }
      return {
        catalog: catalog.length,
        loaded,
        failures,
        audit: window.TakMapMilStd2525CI538.audit()
      };
    }""", {'catalog': CATALOG, 'svgMap': svg_map})
    assert result['catalog'] == 1448, result
    assert result['loaded'] == 1448, result
    assert result['failures'] == [], result['failures'][:20]
    assert result['audit']['brokenVisibleImages'] == 0, result['audit']


def main() -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        try:
            page = browser.new_page(viewport={'width': 1280, 'height': 800})
            run_case(page, live_first=False)
            page = browser.new_page(viewport={'width': 1280, 'height': 800})
            run_case(page, live_first=True)
            page = browser.new_page(viewport={'width': 1280, 'height': 800})
            page.set_content('<!doctype html><html><body><div id="milGrid"></div><div id="map"></div></body></html>', wait_until='domcontentloaded')
            page.add_script_tag(content=page_script())
            page.add_script_tag(content=RUNTIME)
            page.wait_for_function("window.TakMapMilStd2525CI538 && window.TakMapMilStd2525CI538.audit().catalogCount===1448")
            result = page.evaluate("""async () => {
              const grid=document.getElementById('milGrid');
              for(let i=0;i<1448;i++){const img=document.createElement('img');img.src='data:image/svg+xml,<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"1\" height=\"1\"></svg>';grid.appendChild(img)}
              const map=document.getElementById('map');
              let beats=0;const timer=setInterval(()=>beats++,1);const start=performance.now();
              for(let i=0;i<600;i++){await new Promise(resolve=>setTimeout(resolve,0));map.appendChild(document.createElement('div'))}
              clearInterval(timer);return {elapsed:performance.now()-start,beats};
            }""")
            assert result['beats'] > 100, result
            assert result['elapsed'] < 5000, result
        finally:
            browser.close()
    print('i538 Chromium source normalization, exact mission UID, and startup mutation responsiveness tests passed')


if __name__ == '__main__':
    main()
