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
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content(html,wait_until='domcontentloaded',timeout=30000)
        page.wait_for_function("document.readyState==='complete' && window.TakMapViewshedUiV504 && document.getElementById('toolViewshed')",timeout=18000)
        page.wait_for_timeout(6500)
        page.click('#toolViewshed')
        page.wait_for_function("document.getElementById('viewshedModule')?.classList.contains('tak-viewshed-v504')",timeout=8000)
        page.wait_for_timeout(300)
        initial=page.evaluate("""()=>{
          const p=document.getElementById('viewshedModule'),b=p.querySelector('.viewshed-body'),calc=document.getElementById('viewshedCalc'),r=p.getBoundingClientRect(),cs=getComputedStyle(p),bs=getComputedStyle(b),cc=getComputedStyle(calc);
          return {height:r.height,scrollHeight:p.scrollHeight,overflow:cs.overflow,bodyOverflow:bs.overflowY,bodyMaxHeight:bs.maxHeight,display:cs.display,calculateBackground:cc.backgroundImage,calculateColor:cc.color,tabs:p.querySelectorAll('.viewshed-tab:not(.add)').length,closes:p.querySelectorAll('.viewshed-tab-close-v504').length,count:document.getElementById('viewshedCountV504')?.textContent||'',topGrip:!!p.querySelector('.viewshed-resize-v504.top'),bottomGrip:!!p.querySelector('.viewshed-resize-v504.bottom'),diag:TakMapViewshedUiV504.diagnostics()}
        }""")
        assert initial['display']=='flex',initial
        assert initial['overflow']=='visible' and initial['bodyOverflow']=='visible',initial
        assert initial['bodyMaxHeight']=='none',initial
        assert initial['height']>=initial['scrollHeight']-2,initial
        assert initial['calculateColor'] in ('rgb(24, 33, 40)','rgb(24, 33, 40)'),initial
        assert initial['tabs']==1 and initial['closes']==1 and initial['count']=='1 ACTIVE',initial
        assert initial['topGrip'] and initial['bottomGrip'],initial

        page.click('#viewshedTabs .viewshed-tab.add')
        page.wait_for_timeout(150)
        after_add=page.evaluate("""()=>({views:window.v249Viewshed.views.length,tabs:document.querySelectorAll('#viewshedTabs .viewshed-tab:not(.add)').length,closes:document.querySelectorAll('#viewshedTabs .viewshed-tab-close-v504').length,count:document.getElementById('viewshedCountV504').textContent})""")
        assert after_add=={'views':2,'tabs':2,'closes':2,'count':'2 ACTIVE'},after_add

        page.locator('#viewshedTabs .viewshed-tab-close-v504').nth(1).click()
        page.wait_for_timeout(150)
        after_delete=page.evaluate("""()=>({views:window.v249Viewshed.views.length,tabs:document.querySelectorAll('#viewshedTabs .viewshed-tab:not(.add)').length,count:document.getElementById('viewshedCountV504').textContent,calcDisabled:document.getElementById('viewshedCalc').disabled})""")
        assert after_delete=={'views':1,'tabs':1,'count':'1 ACTIVE','calcDisabled':False},after_delete

        page.locator('#viewshedTabs .viewshed-tab-close-v504').click()
        page.wait_for_timeout(150)
        empty=page.evaluate("""()=>({views:window.v249Viewshed.views.length,tabs:document.querySelectorAll('#viewshedTabs .viewshed-tab:not(.add)').length,count:document.getElementById('viewshedCountV504').textContent,calcDisabled:document.getElementById('viewshedCalc').disabled,status:document.getElementById('viewshedStatus').textContent})""")
        assert empty['views']==0 and empty['tabs']==0 and empty['count']=='0 ACTIVE' and empty['calcDisabled'] and 'No viewsheds' in empty['status'],empty
        page.click('#viewshedTabs .viewshed-tab.add')
        page.wait_for_timeout(150)
        restored=page.evaluate("""()=>({views:window.v249Viewshed.views.length,tabs:document.querySelectorAll('#viewshedTabs .viewshed-tab:not(.add)').length,calcDisabled:document.getElementById('viewshedCalc').disabled})""")
        assert restored=={'views':1,'tabs':1,'calcDisabled':False},restored

        page.click('#viewshedVisibleColor')
        page.wait_for_function("document.getElementById('viewshedColorPopoverV504')?.classList.contains('open')",timeout=4000)
        page.locator('#viewshedColorPopoverV504 .viewshed-color-swatch-v504').nth(6).click()
        page.wait_for_timeout(150)
        colors=page.evaluate("""()=>{const input=document.getElementById('viewshedVisibleColor'),range=document.getElementById('viewshedVisibleOpacity');return {value:input.value,swatch:getComputedStyle(input).backgroundColor,track:range.style.getPropertyValue('--viewshed-track'),state:window.v249Viewshed.views[window.v249Viewshed.active].visibleColor,popOpen:document.getElementById('viewshedColorPopoverV504').classList.contains('open')}}""")
        assert colors['value']=='#56b8ff' and colors['track']=='#56b8ff' and colors['state']=='#56b8ff' and not colors['popOpen'],colors

        page.click('#viewshedBlockedColor')
        page.wait_for_function("document.getElementById('viewshedColorPopoverV504')?.classList.contains('open')",timeout=4000)
        page.locator('#viewshedColorPopoverV504 .viewshed-color-swatch-v504').nth(5).click()
        page.wait_for_timeout(150)
        blocked_colors=page.evaluate("""()=>{const input=document.getElementById('viewshedBlockedColor'),range=document.getElementById('viewshedBlockedOpacity');return {value:input.value,swatch:getComputedStyle(input).backgroundColor,track:range.style.getPropertyValue('--viewshed-track'),state:window.v249Viewshed.views[window.v249Viewshed.active].blockedColor,popOpen:document.getElementById('viewshedColorPopoverV504').classList.contains('open')}}""")
        assert blocked_colors['value']=='#a86c54' and blocked_colors['track']=='#a86c54' and blocked_colors['state']=='#a86c54' and not blocked_colors['popOpen'],blocked_colors

        page.click('#viewshedHideBtn')
        page.wait_for_timeout(100)
        minimized=page.evaluate("""()=>({panel:document.getElementById('viewshedModule').classList.contains('active'),min:document.getElementById('viewshedMinimized').classList.contains('active')})""")
        assert minimized=={'panel':False,'min':True},minimized
        page.click('#viewshedMinimized')
        page.wait_for_timeout(250)
        restored_panel=page.evaluate("""()=>({panel:document.getElementById('viewshedModule').classList.contains('active'),min:document.getElementById('viewshedMinimized').classList.contains('active'),bodyOverflow:getComputedStyle(document.querySelector('#viewshedModule .viewshed-body')).overflowY})""")
        assert restored_panel['panel'] and not restored_panel['min'] and restored_panel['bodyOverflow']=='visible',restored_panel
        browser.close()
    fatal=[e for e in errors if any(t in e.lower() for t in ('maximum call stack','too much recursion','out of memory'))]
    assert not fatal,(errors,fatal)
    result={'initial':initial,'after_add':after_add,'after_delete':after_delete,'empty':empty,'restored':restored,'colors':colors,'blockedColors':blocked_colors,'minimized':minimized,'restored_panel':restored_panel,'pageErrors':errors}
    print('TAK Map i504 Geofence-style Viewshed floating-window browser test passed')
    print(json.dumps(result,sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())
