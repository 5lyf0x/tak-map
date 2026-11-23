#!/usr/bin/env python3
"""i655 browser check for the actual i654 early-DOM map-collision failure."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from test_route_editor_i654_browser import harness,js
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':900})
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.set_content(harness)
    page.evaluate("window.__realMap=window.map;window.map=document.getElementById('map');setTimeout(()=>{window.map=window.__realMap},420)")
    page.add_script_tag(content=js)
    assert not page.evaluate('takRouteEditorI654.installed'),'Should wait for Leaflet map readiness'
    page.wait_for_function('takRouteEditorI654.installed',timeout=5000)
    assert page.evaluate('takRouteEditorI654.mode')=='roads'
    assert page.locator('#takRouteSelectorI654').is_visible()
    assert page.locator('#takRouteNetworkStateI655').is_visible()
    left=page.locator('#takRouteSelectorI654').bounding_box()['x']
    assert left>700,left
    assert not errors,errors
    browser.close()
    print('PASS: delayed Leaflet initialization, Roads default, top-right selector and routing status')
