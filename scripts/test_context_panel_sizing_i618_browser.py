#!/usr/bin/env python3
"""Browser contract for the shared i618 content-aware context-panel sizing policy."""
from __future__ import annotations

from pathlib import Path
import shutil
import urllib.parse

ROOT = Path(__file__).resolve().parents[1]
CONTEXT = (ROOT / 'assets' / 'tak-map-context-sidebar-i572.js').read_text()
PACKAGE = (ROOT / 'assets' / 'tak-map-package-i580.js').read_text()
ORIGIN = 'http://127.0.0.1'

FIXTURE = f"""<!doctype html><html><head><meta charset='utf-8'><base href='{ORIGIN}/'><style>
html,body{{margin:0;width:100%;height:100%;overflow:hidden;background:#071117;color:#e9f0f5;font-family:Arial,sans-serif}}#map{{position:relative;width:100%;height:100%}}#floatingToolbarDock{{position:absolute;right:8px;top:60px;width:46px;height:420px;z-index:2147481000;background:#263842}}#topModal{{position:fixed;inset:30px;display:none;z-index:2147483000;background:#111}}.feature-popup .kvp{{display:grid;grid-template-columns:112px minmax(0,1fr)}}
</style></head><body><div id='map'><div id='floatingToolbarDock'></div></div><div id='topModal'></div>
<script>
window.ResizeObserver=class{{constructor(cb){{this.cb=cb}}observe(){{}}disconnect(){{}}}};
window.L={{DomEvent:{{disableClickPropagation(){{}},disableScrollPropagation(){{}}}}}};
window.layerPopupForObject=(o)=>`<div class="feature-popup"><h3>${{o.name||'Object'}}</h3><div class="kvp"><b>Source</b><span>${{o.source||'TAK Map'}}</span><b>Details</b><span>${{o.details||'Compact value'}}</span></div></div>`;
</script>
<script src='/assets/runtime/tak-map-context-sidebar-i572.js?v=1.4.0-i618'></script>
<script src='/assets/runtime/tak-map-package-i580.js?v=1.4.0-i618'></script>
</body></html>"""


def main() -> int:
    chromium = next((n for n in ('chromium','chromium-browser','google-chrome','google-chrome-stable') if shutil.which(n)), None)
    if not chromium:
        raise SystemExit('Chromium is required')
    from playwright.sync_api import sync_playwright
    errors: list[str] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=shutil.which(chromium), args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
        page = browser.new_page(viewport={'width': 1280, 'height': 760})
        page.on('pageerror', lambda exc: errors.append(str(exc)))
        def route(route):
            path = urllib.parse.urlsplit(route.request.url).path
            if path == '/': route.fulfill(status=200, content_type='text/html', body=FIXTURE)
            elif path.endswith('tak-map-context-sidebar-i572.js'): route.fulfill(status=200, content_type='application/javascript', body=CONTEXT)
            elif path.endswith('tak-map-package-i580.js'): route.fulfill(status=200, content_type='application/javascript', body=PACKAGE)
            else: route.fulfill(status=404, body='not found')
        page.route('**/*', route)
        page.set_content(FIXTURE, wait_until='domcontentloaded', timeout=20_000)
        page.wait_for_function('window.TakMapContextSidebarI572 && window.TakMapContextPanelSizingI618')

        # Compact Local Data panel.
        page.evaluate("TakMapContextSidebarI572.showObject({name:'Local Point',source:'Local Data',lat:34,lon:-118,details:'Short note'},'local',null,false)")
        page.wait_for_timeout(120)
        local = page.evaluate("""() => {const p=document.getElementById('takMapContextSidebarI572'),b=document.getElementById('takMapContextSidebarBodyI572'),t=document.getElementById('floatingToolbarDock');const r=p.getBoundingClientRect();return {width:r.width,parent:p.parentElement===document.body,z:Number(getComputedStyle(p).zIndex),toolbarZ:Number(getComputedStyle(t).zIndex),gutter:getComputedStyle(b).scrollbarGutter,overflowX:getComputedStyle(b).overflowX}}""")
        assert 300 <= local['width'] < 430, local
        assert local['parent'] and local['z'] > local['toolbarZ'], local
        assert 'stable' in local['gutter'] and local['overflowX'] == 'hidden', local

        # Data Sync content expands but remains bounded.
        page.evaluate("TakMapContextSidebarI572.showObject({name:'Mission Route Alpha',source:'Data Sync',lat:34,lon:-118,details:'A substantially longer mission-provided description that should expand the context panel without creating horizontal scrolling or consuming the entire map.'},'datasync',null,false)")
        page.wait_for_timeout(120)
        ds = page.evaluate("""() => {const p=document.getElementById('takMapContextSidebarI572'),b=document.getElementById('takMapContextSidebarBodyI572');return {width:p.getBoundingClientRect().width,scrollWidth:b.scrollWidth,clientWidth:b.clientWidth}}""")
        assert ds['width'] > local['width'], (local, ds)
        assert ds['width'] <= 568 and ds['scrollWidth'] <= ds['clientWidth'] + 1, ds

        # Compact NIFC remains narrow.
        nifc_html = "<div class='feature-popup gateway-context-i617'><div class='kvp'><b>Source</b><span>NIFC Fire Perimeters</span><b>Incident</b><span>Summit</span><b>Type</b><span>Wildfire</span><b>Acres</b><span>2,690</span><b>Containment</b><span>100%</span></div></div>"
        page.evaluate("([html])=>TakMapContextSidebarI572.showReadOnly({key:'nifc',kicker:'Gateway Data · NIFC Fire Perimeters',title:'NIFC Wildfire: Summit',html})", [nifc_html])
        page.wait_for_timeout(120)
        nifc = page.evaluate("document.getElementById('takMapContextSidebarI572').getBoundingClientRect().width")
        assert 300 <= nifc < 430, nifc

        # Long NWS values expand and become vertically scrollable without horizontal overflow.
        areas = ''.join(f'<li>Long affected area number {i} with regional wording</li>' for i in range(1,35))
        nws_html = f"<div class='feature-popup gateway-context-i617'><div class='kvp'><b>Source</b><span>NWS Weather Alerts</span><b>Affected areas</b><span><ul class='gateway-area-list-i617'>{areas}</ul></span><b>Description</b><span>Source-provided alert description with enough content to require a wider but still bounded panel.</span></div></div>"
        page.evaluate("([html])=>TakMapContextSidebarI572.showReadOnly({key:'nws',kicker:'Gateway Data · NWS Weather Alerts',title:'NWS Extreme Heat Warning',html})", [nws_html])
        page.wait_for_timeout(180)
        nws = page.evaluate("""() => {const p=document.getElementById('takMapContextSidebarI572'),b=document.getElementById('takMapContextSidebarBodyI572');return {width:p.getBoundingClientRect().width,scrollHeight:b.scrollHeight,clientHeight:b.clientHeight,scrollWidth:b.scrollWidth,clientWidth:b.clientWidth}}""")
        assert nws['width'] > nifc + 40 and nws['width'] <= 568, (nifc, nws)
        assert nws['scrollHeight'] > nws['clientHeight'], nws
        assert nws['scrollWidth'] <= nws['clientWidth'] + 1, nws

        # Synthetic ADS-B pair uses the same shared policy and never overlaps.
        page.evaluate("""() => {
          for (const side of ['left','right']) {const p=document.createElement('aside');p.id=side==='left'?'takMapAdsbLeftSidebarI610':'takMapAdsbRightSidebarI610';p.className=`tak-adsb-panel-i610 tak-adsb-panel-${side}-i610`;p.style.position='fixed';p.style[side]='12px';p.style.bottom='12px';p.innerHTML=`<div class='tak-adsb-panel-body-i610'><div class='tak-adsb-i610-name'>${side==='left'?'AIR1':'A very long aircraft identity value'}</div><div class='tak-adsb-i610-row'><div class='tak-adsb-i610-key'>Registration</div><div class='tak-adsb-i610-value'>${side==='left'?'N1TA':'N123456789 LONG OPERATOR NAME'}</div></div></div>`;document.body.appendChild(p)}
          TakMapContextSidebarI572.hide('adsb-test');TakMapContextPanelSizingI618.fitAll();
        }""")
        page.wait_for_timeout(120)
        pair = page.evaluate("""() => {const l=document.getElementById('takMapAdsbLeftSidebarI610').getBoundingClientRect(),r=document.getElementById('takMapAdsbRightSidebarI610').getBoundingClientRect();return {lw:l.width,rw:r.width,lr:l.right,rl:r.left,viewport:innerWidth,gutter:getComputedStyle(document.querySelector('.tak-adsb-panel-body-i610')).scrollbarGutter}}""")
        assert 300 <= pair['lw'] < pair['rw'] <= 462, pair
        assert pair['lr'] + 20 <= pair['rl'], pair
        assert 'stable' in pair['gutter'], pair

        # Narrow viewport remains bounded and horizontally safe.
        page.set_viewport_size({'width': 520, 'height': 700})
        page.evaluate("""() => {document.getElementById('takMapAdsbLeftSidebarI610').remove();document.getElementById('takMapAdsbRightSidebarI610').remove();TakMapContextSidebarI572.showObject({name:'Narrow screen object',source:'Local Data',lat:34,lon:-118,details:'A long narrow-screen value that must wrap cleanly without horizontal scrolling.'},'local',null,false);TakMapContextPanelSizingI618.fitAll()}""")
        page.wait_for_timeout(120)
        narrow = page.evaluate("""() => {const p=document.getElementById('takMapContextSidebarI572'),b=document.getElementById('takMapContextSidebarBodyI572');return {width:p.getBoundingClientRect().width,scrollWidth:b.scrollWidth,clientWidth:b.clientWidth,right:p.getBoundingClientRect().right}}""")
        assert narrow['width'] <= 496 and narrow['right'] <= 520, narrow
        assert narrow['scrollWidth'] <= narrow['clientWidth'] + 1, narrow

        diag = page.evaluate('TakMapContextPanelSizingI618.diagnostics()')
        assert diag['version'] == 'i618' and diag['fits'] >= 5 and not diag['lastError'], diag
        assert not errors, errors
        browser.close()
    print('TAK Map i618 shared content-aware context-panel sizing browser test passed')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
