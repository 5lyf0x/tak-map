#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
resolver_js = (ROOT / 'assets/tak-map-milstd2525c-i551.js').read_text()
catalog = json.loads((ROOT / 'assets/mil2525/icons.json').read_text())

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'])
    page = browser.new_page(viewport={'width': 800, 'height': 600})
    page.set_content('<!doctype html><html><head></head><body><div id="target"></div></body></html>')
    page.add_script_tag(content=resolver_js)
    page.evaluate('(catalog) => window.TakMapMilStd2525CI551._resetCatalogForTest(catalog)', catalog)
    result = page.evaluate('''() => {
      const object = {
        uid: 'a1121512-4c56-4038-bca1-b82c602d3f96',
        name: 'DS-P13', callsign: 'DS-P13',
        type: 'a-f-G-U-C-A-A', cot_type: 'a-f-G-U-C-A-A',
        mission_cot_raw_type_i551: 'a-f-G-U-C-A-A',
        mission_cot_raw_iconset_path_i551: 'COT_MAPPING_2525C/a-f/a-f-G-U-C-D',
        data_sync_symbol_decision_i551: {
          version: 'i551', authority: 'event-type',
          reason: 'specific-type-changed-iconset-unchanged', conflict: true,
          selected_cot_type: 'a-f-G-U-C-A-A',
          selected_sidc: 'SFGPUCAA-------',
          selected_file: 'friendly-ground-unit-tank-destroyer.svg'
        }
      };
      const html = window.mil2525IconHtml(object);
      document.getElementById('target').innerHTML = html;
      const img = document.querySelector('#target img');
      return {
        html,
        src: img ? img.getAttribute('src') : '',
        sidc: img ? img.getAttribute('data-sidc') : '',
        cotType: img ? img.getAttribute('data-cot-type') : '',
        alt: img ? img.getAttribute('alt') : ''
      };
    }''')
    browser.close()

assert result['src'] == '/mil2525/svg/friendly-ground-unit-tank-destroyer.svg?v=i551', result
assert result['sidc'] == 'SFGPUCAA-------', result
assert result['cotType'] == 'a-f-G-U-C-A-A', result
assert result['alt'] == 'DS-P13', result
assert 'air-defense' not in result['html'], result
print('i551 browser DOM follows the reviewed DS-P13 symbol decision and not stale Air Defense')
