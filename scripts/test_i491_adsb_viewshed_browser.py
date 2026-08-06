#!/usr/bin/env python3
from __future__ import annotations
import json, runpy, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main()->int:
    chromium=next((n for n in ('chromium','chromium-browser','google-chrome','google-chrome-stable') if shutil.which(n)),None)
    if not chromium:
        print('SKIP: Chromium unavailable'); return 0
    helper=runpy.run_path(str(ROOT/'scripts'/'test_full_page_responsiveness_v486.py'))
    html=helper['self_contained_html']()
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=shutil.which(chromium),args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
        page=browser.new_page(viewport={'width':1440,'height':1000})
        errors=[]; page.on('pageerror',lambda e: errors.append(str(e)))
        page.set_content(html,wait_until='domcontentloaded',timeout=20000)
        page.wait_for_function("window.TakMapCardControlsV477 && window.TakMapViewshedWindowV488 && document.readyState==='complete'",timeout=15000)
        page.wait_for_timeout(7000)
        initial=page.evaluate("""()=>{
          const r=id=>document.getElementById(id)?.closest('label')?.getBoundingClientRect();
          const fr=r('adsbAltitudeFilterV477'), ar=r('adsbAltitudeThresholdV477'), sr=r('adsbCenterSource'), cr=r('adsbCenterLatLon');
          const cards=[...document.querySelectorAll('.adsb-type-grid-v491>.adsb-type-card-v491')];
          const govt=cards.find(c=>c.dataset.type==='govt');
          return {
            types:cards.map(c=>c.dataset.type), codes:cards.map(c=>c.querySelector('.adsb-type-badge-v491')?.textContent?.trim()),
            filterAltitudeSameRow:!!fr&&!!ar&&Math.abs(fr.top-ar.top)<2,
            centerSameRow:!!sr&&!!cr&&Math.abs(sr.top-cr.top)<2,
            filterWidths:[fr?.width,ar?.width],centerWidths:[sr?.width,cr?.width],
            govtColor:govt?getComputedStyle(govt).getPropertyValue('--type-color').trim():'',
            design:TakMapCardControlsV477.diagnostics().adsbFilterDesign
          }
        }""")
        page.evaluate("window.toggleViewshedModule(true)")
        page.wait_for_timeout(250)
        active=page.evaluate("()=>({cls:document.getElementById('toolViewshed').classList.contains('active'),pressed:document.getElementById('toolViewshed').getAttribute('aria-pressed'),diag:TakMapViewshedWindowV488.diagnostics()})")
        page.evaluate("window.setActiveMapTool('measure')")
        page.wait_for_timeout(1200)
        switched=page.evaluate("()=>({cls:document.getElementById('toolViewshed').classList.contains('active'),pressed:document.getElementById('toolViewshed').getAttribute('aria-pressed'),diag:TakMapViewshedWindowV488.diagnostics()})")
        page.evaluate("window.toggleViewshedModule(true)")
        page.keyboard.press('Escape'); page.wait_for_timeout(250)
        escaped=page.evaluate("()=>({cls:document.getElementById('toolViewshed').classList.contains('active'),pressed:document.getElementById('toolViewshed').getAttribute('aria-pressed'),diag:TakMapViewshedWindowV488.diagnostics()})")
        browser.close()
    assert initial['types']==['civil','govt','military','unknown'], initial
    assert initial['codes']==['CIV','GOV','MIL','UNK'], initial
    assert initial['filterAltitudeSameRow'] and initial['centerSameRow'], initial
    assert all(w and w>100 for w in initial['filterWidths']+initial['centerWidths']), initial
    assert initial['govtColor'].lower()=='#b56cff', initial
    assert initial['design']=='4A', initial
    assert active['cls'] and active['pressed']=='true' and active['diag']['toolActive'], active
    assert not switched['cls'] and switched['pressed']=='false' and not switched['diag']['toolActive'], switched
    assert not escaped['cls'] and escaped['pressed']=='false' and not escaped['diag']['toolActive'], escaped
    fatal=[e for e in errors if any(t in e.lower() for t in ('maximum call stack','too much recursion','out of memory'))]
    assert not fatal, fatal
    print('ADS-B 4A/layout and Viewshed active-state browser test passed')
    print(json.dumps({'initial':initial,'active':active,'switched':switched,'escaped':escaped},sort_keys=True))
    return 0
if __name__=='__main__': raise SystemExit(main())
