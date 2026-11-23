#!/usr/bin/env python3
"""i695 focused offline regressions: typography, inline counts, panel actions, slider migration."""
from pathlib import Path
import re
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
CSS=(ROOT/'assets/tak-map-infrastructure-i689.css').read_text()
JS=(ROOT/'assets/tak-map-infrastructure-i689.js').read_text()
WJS=(ROOT/'assets/tak-map-weather-i693.js').read_text()
WCSS=(ROOT/'assets/tak-map-weather-i693.css').read_text()
BASECSS=(ROOT/'assets/tak-map-sidebar-uniform-i684.css').read_text()
DASH=(ROOT/'tak_dashboard.py').read_text()
assert 'function ensureInfrastructureHeader(card)' in JS and 'ensureInfrastructureHeader($(ID))' in JS
assert 'const raw=Object.entries(p)' in JS
assert JS.index('<section class="infra-raw-attrs"',JS.index('function info(')) < JS.index('<div class="infra-detail-actions"',JS.index('function info('))
# i696 permanently removed the pre-cache machinery instead of hiding its UI.
assert 'basemapPrecacheRemoved:true' not in DASH
assert 'function ensureRadarOpacityControl(panel)' in WJS and 'slider.addEventListener(\'input\'' in WJS
assert 'tak-map-native-weather-i691' in WJS
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
 for width in (820,400,340):
  page=browser.new_page(viewport={'width':width,'height':750})
  page.set_content('''<html><body style="background:#101923;color:#dce8f0;font:12px Manrope,system-ui"><div id="sidebar" style="max-width:340px"><section class="panel" id="takInfraCardI685"><div class="infra-body"><section class="infra-category"><button class="infra-cat-head"><span class="name">Water &amp; Wastewater</span><span class="infra-cat-count">2</span><span>▾</span></button><div class="infra-layer"><input type="checkbox" checked><div class="infra-layer-name-area"><div class="infra-layer-name">Manholes to 36 Inches or Larger</div><div class="infra-layer-meta" data-infra-counter="a">1,309 / 1,309</div></div><div class="infra-tools">Filter</div></div><div class="infra-layer"><input type="checkbox"><div class="infra-layer-name-area"><div class="infra-layer-name">LA City Small Cell Antennas</div><div class="infra-layer-meta" data-infra-counter="b">Disabled</div></div></div></section></div></section></div></body></html>''')
  page.add_style_tag(content=CSS)
  row=page.evaluate('''() => {let a=document.querySelector('.infra-cat-head .name'),b=document.querySelector('.infra-layer-name'),c=document.querySelector('.infra-layer-meta'),r=document.querySelector('.infra-layer-name-area');let as=getComputedStyle(a),bs=getComputedStyle(b),cs=getComputedStyle(c),rs=getComputedStyle(r);let rectb=b.getBoundingClientRect(),rectc=c.getBoundingClientRect();return {headingSize:as.fontSize,headingWeight:as.fontWeight,headingLetter:as.letterSpacing,headingAfter:getComputedStyle(a,'::after').content,layerSize:bs.fontSize,layerWeight:bs.fontWeight,countSize:cs.fontSize,countWeight:cs.fontWeight,gridGap:rs.columnGap,sameRow:Math.abs(rectb.top-rectc.top)<9,overflows:r.scrollWidth>r.clientWidth+2}}''')
  assert row['headingSize']=='14px' and row['headingWeight']=='550' and row['headingLetter']=='0.14px',row
  assert row['headingAfter'] not in ('none','normal'),row
  assert row['layerSize']=='12.5px' and row['layerWeight']=='750',row
  assert row['countSize']=='10px' and row['countWeight']=='400',row
  assert row['gridGap']=='12px' and row['sameRow'] and not row['overflows'],row
  page.close()
 # The legacy weather panel must migrate instead of duplicating a slider.
 page=browser.new_page()
 page.set_content('''<html><body><select id="basemapSelect"></select><section id="takNativeWeatherI691"><button class="tak-weather-head-i691">WEATHER OVERLAYS<span>⌃</span></button><div class="tak-weather-body-i691"><label class="tak-weather-row-i691"><span>Radar Reflectivity</span><input id="takWeatherRadarI691" type="checkbox"></label><div id="takWeatherRadarSettingsI691" class="tak-weather-sub-i691"><label>Opacity <output id="takWeatherOpacityOutI691">55%</output></label><input id="takWeatherOpacityI691" type="range" value="55"><small id="takWeatherRadarStatusI691">Off</small></div><label class="tak-weather-row-i691"><span>Alerts</span><input id="takWeatherAlertsI691" type="checkbox"></label></div></section></body></html>''')
 page.evaluate("() => Object.defineProperty(window,'localStorage',{configurable:true,value:{_d:{},getItem(k){return this._d[k]||null},setItem(k,v){this._d[k]=String(v)}}})")
 page.add_style_tag(content=WCSS)
 page.add_script_tag(content=WJS)
 page.wait_for_selector('#takWeatherOpacitySoftPillI694',timeout=5000)
 assert page.locator('#takWeatherOpacityI691').count()==0
 assert page.locator('#takWeatherOpacitySoftPillI694').count()==1
 assert page.locator('#takWeatherOpacitySoftPillI694').get_attribute('class')=='tak-soft-pill-i678'
 page.evaluate('''() => {let s=TakMapNativeWeatherI693.state;s.radarLayer={setOpacity(v){this.alpha=v}};s.radarPendingLayer={setOpacity(v){this.alpha=v}};s.cesRadar={alpha:0};s.cesRadarRetiring={alpha:0};window._fetches=0;window.fetch=()=>{_fetches++}}''')
 page.locator('#takWeatherOpacitySoftPillI694').fill('71')
 data=page.evaluate('''() => {let s=TakMapNativeWeatherI693.state;return [s.opacity,s.radarLayer.alpha,s.radarPendingLayer.alpha,s.cesRadar.alpha,s.cesRadarRetiring.alpha,_fetches]}''')
 assert data==[71,.71,.71,.71,.71,0],data
 assert page.locator('#takWeatherOpacityOutI694').inner_text()=='71%'
 page.close();browser.close()
print('PASS i695 UI: 3 widths, Extended Divider + Clear Type + count row, detail action ordering, legacy radar slider upgrade, 2D/3D opacity no fetch')
