#!/usr/bin/env python3
from __future__ import annotations
import json, re, runpy
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
ns=runpy.run_path(str(ROOT/'tak_dashboard.py'),run_name='tak_map_i517_browser_source')
HTML=ns['TAK_MAP_HTML']
LOGIN=ns['TAK_MAP_LOGIN_HTML']
SCRIPT=re.search(r'(<style id="takMapSharedBasemapCatalogStyleV517">.*?<script id="takMapSharedBasemapCatalogV517">.*?</script>)',HTML,re.S)
assert SCRIPT, 'i517 shared catalog UI missing'
SCRIPT=SCRIPT.group(1)
GUARD=re.search(r'(<script id="takMapIterationGuardV519">.*?</script>)',HTML,re.S)
assert GUARD, 'i519 iteration guard missing'
SCRIPT+=GUARD.group(1)
ROWS=[{'id':'shared-one','label':'Shared One','group':'Custom','importedBasemap':True,'managementType':'custom','minZoom':0,'maxZoom':19,'url':'/tiles/{z}/{x}/{y}.png'}]

def app(admin: bool):
    return f'''<!doctype html><html><body><div class="iteration-marker">i516</div><button id="basemapManagerBulkV506">Remove</button><button class="tak-bm-remove-v506">×</button><script>window.config={{basemaps:[{{id:'builtin',label:'Built In'}}]}};window.renderCount=0;window.renderBasemaps=()=>window.renderCount++;window.TakMapBasemapManagementV506={{render:()=>window.managerRendered=true}};window.fetch=async u=>u==='/api/tak-map/custom-basemaps'?{{ok:true,json:async()=>({{ok:true,basemaps:{json.dumps(ROWS)}}})}}:{{ok:true,json:async()=>({{ok:true,is_admin:{str(admin).lower()}}})}};</script>{SCRIPT}</body></html>'''

def main():
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        p=browser.new_page(viewport={'width':1280,'height':800});p.set_content(app(False),wait_until='domcontentloaded');p.wait_for_timeout(700)
        assert p.evaluate('config.basemaps.length')==1
        assert p.evaluate('config.basemaps[0].id')=='shared-one'
        assert p.evaluate('window.renderCount')>=1 and p.evaluate('window.managerRendered') is True
        assert p.locator('.iteration-marker').inner_text()=='i526'
        assert p.evaluate("getComputedStyle(document.querySelector('.tak-bm-remove-v506')).display")=='none'
        p2=browser.new_page(viewport={'width':1280,'height':800});p2.set_content(app(True),wait_until='domcontentloaded');p2.wait_for_timeout(700)
        assert p2.evaluate("getComputedStyle(document.querySelector('.tak-bm-remove-v506')).display")!='none'
        lp=browser.new_page(viewport={'width':1280,'height':800});lp.set_content(LOGIN,wait_until='domcontentloaded');lp.wait_for_timeout(250)
        box=lp.locator('.card').bounding_box();assert box
        center=box['y']+box['height']/2
        assert abs(center-400)<3,(center,box)
        browser.close()
    print('i517 browser startup hydration, non-admin removal hiding, sidebar iteration, and vertical login centering tests passed')
if __name__=='__main__': main()
