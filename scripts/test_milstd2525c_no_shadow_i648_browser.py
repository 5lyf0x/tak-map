#!/usr/bin/env python3
"""Check all tactical icon shadow sources and selected AIS glow in Chromium."""
from pathlib import Path
import re
import shutil
import xml.etree.ElementTree as ET
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
GATEWAY = (ROOT/'assets/tak-map-gateway-data-v491.js').read_text()
MIL = (ROOT/'assets/tak-map-milstd2525c-i553.js').read_text()
SVG_DIR = ROOT/'assets/mil2525/svg'

svgs=list(SVG_DIR.glob('*.svg'))
assert len(svgs)==1448
for p in svgs:
    s=p.read_text()
    assert 'filter:url(#ef0)' not in s,p.name
    assert 'feGaussianBlur' not in s,p.name
    assert '<feOffset' not in s,p.name
    ET.fromstring(s)
assert sum('takmapThinBlack' in p.read_text() for p in svgs)==476

# Load the real CSS content and no-shadow injection helper from the modules.
css_start=GATEWAY.index('st.textContent=`') + len('st.textContent=`')
css_end=GATEWAY.index('`;',css_start)
gw_css=GATEWAY[css_start:css_end]
assert '.gateway-data-ais-milstd2525c-i648.gateway-data-selected-i614' in gw_css
snippet=MIL[MIL.index('  function ensureMilStd2525CNoShadowI648()'):MIL.index('  function boot()')]

chromium=next((shutil.which(n) for n in ('chromium','chromium-browser','google-chrome') if shutil.which(n)), None)
assert chromium, 'Chromium is needed for this test'
html='''<!doctype html><html><head><style>
.tak-icon-wrap { filter:drop-shadow(0 0 8px rgba(0,0,0,.75)); }
.tak-icon-selected { filter:drop-shadow(0 0 10px currentColor); }
</style></head><body>
<div id="normal" class="leaflet-marker-icon gateway-data-marker-v491 gateway-data-milstd2525c-i538">
<div class="tak-icon-wrap"><img class="tak-mil2525-img" alt="symbol"></div></div>
<div id="selected" class="leaflet-marker-icon gateway-data-marker-v491 gateway-data-milstd2525c-i538 gateway-data-ais-milstd2525c-i648 gateway-data-selected-i614">
<div class="tak-icon-wrap"><img class="tak-mil2525-img" alt="symbol"></div></div>
<div id="cot" class="leaflet-marker-icon"><div class="tak-icon-wrap tak-icon-selected"><svg class="tak-icon-svg"></svg></div></div>
</body></html>'''

with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path=chromium,args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
    try:
        page=browser.new_page()
        page.set_content(html)
        page.add_style_tag(content=gw_css)
        page.evaluate('(function(){const d=document;'+snippet+'ensureMilStd2525CNoShadowI648();})()')
        computed=page.evaluate('''() => Object.fromEntries(['normal','selected','cot'].map(id => {
          const el=document.getElementById(id);
          const inner=el.querySelector('.tak-icon-wrap');
          const img=el.querySelector('img, svg');
          const fmt=e=>({filter:getComputedStyle(e).filter,shadow:getComputedStyle(e).boxShadow});
          return [id,{outer:fmt(el),inner:fmt(inner),image:fmt(img)}];
        }))''')
        assert computed['normal']['outer']['filter']=='none',computed
        assert computed['normal']['inner']['filter']=='none',computed
        assert computed['normal']['image']['filter']=='none',computed
        assert computed['cot']['inner']['filter']=='none',computed
        assert computed['cot']['image']['filter']=='none',computed
        assert '255, 48, 48' in computed['selected']['outer']['filter'], computed
        assert computed['selected']['inner']['filter']=='none',computed
        assert computed['selected']['image']['filter']=='none',computed
        for d in computed.values():
            assert all(v['shadow']=='none' for v in d.values()),computed
        print('PASS: 1448 SVGs parsed with no baked-in blur; Chromium normal MIL markers no halo, selected AIS red outer glow only.')
    finally:
        browser.close()
