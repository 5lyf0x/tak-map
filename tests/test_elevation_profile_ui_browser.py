"""Regression: closing, route-mode exit, saved profiles, steep grades and chart ticks.

Run: python tests/test_elevation_profile_ui_browser.py
Requires Chromium and Playwright. No TAK server or real terrain data is touched.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / 'assets' / 'tak-map-route-elevation-i681.js'
HTML = '''<!doctype html><html><head><meta charset="utf-8"><style>
body{margin:0;background:#172b35;color:white;font:13px system-ui}
#map{position:fixed;inset:0;background:#243742}
#toolRoute{position:absolute;right:40px;top:30px}
#routeMiniToolbar{position:absolute;right:40px;top:90px}
</style></head><body><div id="map"></div><button id="toolRoute">Route Creation</button>
<div id="routeMiniToolbar">Route toolbar</div></body></html>'''


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        try:
            page = browser.new_page(viewport={'width': 1280, 'height': 850})
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.set_content(HTML)
            # The actual application declares activeMapTool with let in a classic script.
            page.add_script_tag(content="let activeMapTool='move';")
            page.evaluate("""() => {
                window.map={getContainer:()=>document.getElementById('map'),
                    distance:(a,b)=>Math.hypot((a[0]-b[0])*111000,(a[1]-b[1])*111000),
                    hasLayer:()=>false};
                window.L={circleMarker:()=>({addTo:()=>({})})};
                window.localDataFeatureById=()=>({name:'Saved trail',
                    coords:[[33.03,-116.10],[33.04,-116.09]]});
            }""")
            page.add_script_tag(path=str(JS))
            assert page.locator('#takRouteElevationI681').is_hidden()
            # A stale active CSS class cannot override authoritative tool state.
            page.evaluate("""() => {document.getElementById('toolRoute').classList.add('active');
                document.getElementById('routeMiniToolbar').classList.add('active')}""")
            page.wait_for_timeout(200)
            assert page.locator('#takRouteElevationI681').is_hidden()
            page.evaluate("activeMapTool='route'")
            page.wait_for_timeout(900)
            assert page.locator('#takRouteElevationI681').is_visible()
            page.locator('#takElevCloseI681').click()
            assert page.locator('#takRouteElevationI681').is_hidden()
            page.evaluate("window.dispatchEvent(new Event('tak-map-route-geometry-i681'))")
            page.wait_for_timeout(850)
            assert page.locator('#takRouteElevationI681').is_hidden(), 'X must remain dismissed'
            print('PASS: close X hides full panel and dismissal remains for route session')
            page.evaluate("activeMapTool='move'")
            page.wait_for_timeout(900)
            assert page.locator('#takRouteElevationI681').is_hidden()
            page.evaluate("activeMapTool='route'")
            page.wait_for_timeout(900)
            assert page.locator('#takRouteElevationI681').is_visible(), 'reopen on fresh route session'
            page.evaluate("activeMapTool='move'")
            page.wait_for_timeout(900)
            assert page.locator('#takRouteElevationI681').is_hidden(), 'auto-hide when leaving tool'
            print('PASS: exit auto-hides, new route session reopens, even with stale button class')
            page.evaluate("window.TakMapElevationI681.showSavedRouteById('saved1')")
            assert page.locator('#takRouteElevationI681').is_visible()
            page.locator('#takElevCloseI681').click()
            assert page.locator('#takRouteElevationI681').is_hidden()
            print('PASS: explicit saved route profile X also closes')
            page.evaluate("window.TakMapElevationI681.showSavedRouteById('saved1')")
            page.evaluate("""() => {let api=TakMapElevationI681,s=api.state;
                s.samples=Array.from({length:11},(_,i)=>({d:i*30,lat:33.03+i*.0001,lng:-116.10}));
                s.elev=Array.from({length:11},(_,i)=>120+i*30);s.gradeWindowM=90;api.redraw()}""")
            assert page.locator('#takElevSlopeI681').inner_text()=='45.0°'
            assert page.locator('#takElevSteepI681').inner_text()!='—'
            assert page.locator('#takElevSteepNoticeI681').evaluate('(el)=>el.classList.contains("danger")')
            assert page.locator('#takElevMinI681').inner_text().endswith('ft')
            assert page.locator('#takElevMaxI681').inner_text().endswith('ft')
            assert page.locator('.tak-elev-legend-i682 span').count()==4
            assert page.locator('#takElevCanvasI681').evaluate('(c)=>c.width>0&&c.height>0')
            print('PASS: actual 45° slope flagged red, grade summary and canvas axes present')
            # Large-route slope calculation is linear and cached between redraws.
            elapsed=page.evaluate("""() => {let api=TakMapElevationI681,s=api.state;
                s.samples=Array.from({length:40000},(_,i)=>({d:i*30,lat:33.0,lng:-116.0}));
                s.elev=Array.from({length:40000},(_,i)=>1000+i*.25);
                const start=performance.now();api.gradeProfile();api.gradeProfile();
                return performance.now()-start;}""")
            assert elapsed<2000, f'long-route grade calculation too slow: {elapsed:.1f} ms'
            assert not errors, errors
            print(f'PASS: 40,000-sample grade computation and cached repeat ({elapsed:.1f} ms), zero exceptions')
        finally:
            browser.close()


if __name__ == '__main__':
    main()
