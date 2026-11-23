"""Chromium layout/interactions for route-only 155x25px Tactical HUD dropdown."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parents[1]
js=(root/'assets/tak-map-routing-dropdown-i675.js').read_text()
AZ='a'*64;WEST='b'*64
html='''<!doctype html><html><head><meta charset="utf-8"><style>
body{padding:0;margin:0;background:#0d1720}#map{position:absolute;top:55px;left:269px;right:0;bottom:0;background:#d2e6e8}
#zoom{position:absolute;right:7px;top:42px;width:154px;height:26px;background:#111c23;color:white;z-index:500}
#toolbar{position:absolute;right:4px;top:100px;width:36px;height:330px;background:#1c2a32;z-index:300}
</style></head><body><div id="map"></div><div id="zoom">Zoom/coordinates</div><div id="toolbar"></div></body></html>'''
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1742,'height':864})
    page.set_content(html)
    page.evaluate('window.activeMapTool="move"; window.takRouteEditorI654={}; window.v233RouteState={points:[]};')
    response = {'ok':True,'active_dataset_id':AZ,'datasets':[{'dataset_id':AZ,'label':'Arizona','active':True},{'dataset_id':WEST,'label':'US West','active':False}], 'switch':{'status':'idle','dataset_id':'','error':''},'router_state':'ready'}
    page.evaluate('window.fetch = async () => ({ok:true,json:async ()=>(' + json.dumps(response) + ')})')
    page.evaluate(js)
    page.wait_for_timeout(700)
    assert page.locator('#takRouteDataI675').is_hidden(), 'Selector visible while route tool disabled'
    page.evaluate('window.activeMapTool="route"')
    page.wait_for_timeout(700)
    hud=page.locator('#takRouteDataButtonI675')
    assert hud.is_visible(), 'Selector did not appear when route tool active'
    r=hud.bounding_box();assert r
    print('reference control bounds',r)
    assert abs(r['x']-1580)<=2 and abs(r['y']-73)<=2, 'Selector missed user marked rectangle'
    assert r['width']<=155 and r['height']<=25, 'Dropdown exceeds specified max bounds'
    assert r['x']+r['width']<=1735+1 and r['y']+r['height']<=98+1
    hud.click()
    page.wait_for_timeout(300)
    menu=page.locator('#takRouteDataMenuI675')
    assert menu.is_visible()
    rm=menu.bounding_box();assert rm
    print('expanded popup bounds',rm)
    assert rm['x']+rm['width'] < 1704, 'Popup intrudes into right-side vertical controls'
    assert page.get_by_text('US West',exact=True).count()>=1
    page.evaluate('window.activeMapTool="move"')
    page.wait_for_timeout(700)
    assert page.locator('#takRouteDataI675').is_hidden()
    # At narrower viewport, anchor stays within map and vertical controls.
    page.set_viewport_size({'width':1200,'height':760})
    page.evaluate('window.activeMapTool="route"')
    page.wait_for_timeout(700)
    r=hud.bounding_box()
    assert r and 0<=r['x'] and r['x']+r['width']<=1200
    assert r['height']<=25 and r['width']<=155
    print('narrow control bounds',r)
    browser.close()
print('PASS: i675 Tactical HUD viewport placement, 155x25 max, popup clearance, visibility, responsive layout')
