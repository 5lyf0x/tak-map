#!/usr/bin/env python3
"""Browser contract for TAK Map i638 stable shape context/sidebar behavior."""
from __future__ import annotations
from pathlib import Path
import shutil, urllib.parse

ROOT=Path(__file__).resolve().parents[1]
CONTEXT=(ROOT/'assets'/'tak-map-context-sidebar-i572.js').read_text()
PACKAGE=(ROOT/'assets'/'tak-map-package-i580.js').read_text()
ORIGIN='http://127.0.0.1'
FIXTURE=f"""<!doctype html><html><head><meta charset='utf-8'><base href='{ORIGIN}/'><style>
html,body{{margin:0;width:100%;height:100%;overflow:hidden;background:#071117;color:#e9f0f5;font-family:Arial,sans-serif}}#map{{position:relative;width:100%;height:100%}}
</style></head><body><aside class='version-panel'><div class='version-product'>TAK Map</div><span class='release-main'>1.4.0</span><span class='iteration-chip'>i637</span></aside><div id='map'></div>
<script>
window.ResizeObserver=class{{constructor(cb){{this.cb=cb}}observe(){{}}disconnect(){{}}}};
window.L={{DomEvent:{{disableClickPropagation(){{}},disableScrollPropagation(){{}},stop(){{}}}}}};
window.layerPopupForObject=(o)=>`<div class="tak-v322-popup" data-kind="Shape" data-source="Local Data"><div class="tak-v322-bar"></div><div class="tak-v322-inner"><div class="tak-v322-title">${{o.name}}</div><div class="tak-v322-sub">Shape · Local Data</div><div class="tak-v322-table"><div class="tak-v322-row"><b>Category</b><span>shape</span></div><div class="tak-v322-row"><b>Lat/Lon</b><span>${{o.lat}}, ${{o.lon}}</span></div><div class="tak-v322-row"><b>Points</b><span>${{o.coords.length}}</span></div><div class="tak-v322-row"><b>Added</b><span>9/2/2026, 07:06</span></div></div><details class="popup-edit tak-v322-edit"><summary>Edit</summary><div class="tak-v322-edit-fields"><label>Name<input name="name" value="${{o.name}}"></label></div><div class="tak-v322-actions"><button data-v322-popup-action="save" data-popup-source="Local Data">Save</button></div></details></div></div>`;
window.dataSyncCategory=(o)=>/u-d-r/.test(o.type||'')?'Shapes / Areas':'Point Markers';
window.lastDataSync={{objects:[]}};
</script>
<script src='/assets/runtime/tak-map-context-sidebar-i572.js?v=1.4.0-i638'></script>
<script src='/assets/runtime/tak-map-package-i580.js?v=1.4.0-i638'></script>
</body></html>"""

OBJ={
    'uid':'rect-i638','name':'Rectangle 3','type':'u-d-r','cot_type':'u-d-r','kind':'shape','geometry':'shape',
    'is_mission_object':True,'mission_memberships':['1-40TH RECON'],'mission_name':'1-40TH RECON',
    'lat':34.2060116,'lon':-118.72761,'shape_kind_i636':'rectangle','shape_closed_i636':True,
    'delete_supported':True,
    'coords':[[34.21028794604995,-118.75832320362926],[34.18305784557117,-118.71324111471124],[34.201731109450755,-118.69689581442177],[34.22896713330185,-118.74198259098516]],
}

def main()->int:
    chromium=next((n for n in ('chromium','chromium-browser','google-chrome','google-chrome-stable') if shutil.which(n)),None)
    if not chromium: raise SystemExit('Chromium is required')
    from playwright.sync_api import sync_playwright
    errors=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=shutil.which(chromium),args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
        context=browser.new_context(locale='en-US',viewport={'width':1280,'height':760})
        page=context.new_page(); page.on('pageerror',lambda exc:errors.append(str(exc)))
        def route(route):
            path=urllib.parse.urlsplit(route.request.url).path
            if path.endswith('tak-map-context-sidebar-i572.js'): route.fulfill(status=200,content_type='application/javascript',body=CONTEXT)
            elif path.endswith('tak-map-package-i580.js'): route.fulfill(status=200,content_type='application/javascript',body=PACKAGE)
            else: route.fulfill(status=404,body='not found')
        page.route('**/*',route)
        page.set_content(FIXTURE,wait_until='domcontentloaded',timeout=20000)
        page.wait_for_function('window.TakMapContextSidebarI572 && window.TakMapContextPanelSizingI620')
        page.evaluate('(o)=>{window.lastDataSync={objects:[o]};TakMapContextSidebarI572.showObject(o,"datasync",null,false)}',OBJ)
        page.wait_for_timeout(250)
        result=page.evaluate("""() => {
          const p=document.getElementById('takMapContextSidebarI572'), b=document.getElementById('takMapContextSidebarBodyI572');
          const popup=b.querySelector('.tak-v322-popup'), sub=b.querySelector('.tak-v322-sub'), edit=b.querySelector('.tak-shape-edit-toggle-i638'), details=b.querySelector('details.popup-edit'), summary=details.querySelector('summary'), del=b.querySelector('.tak-context-delete-button-i572');
          const rows=Object.fromEntries([...b.querySelectorAll('.tak-v322-row')].map(r=>[(r.querySelector('b')?.textContent||'').trim(),(r.querySelector('span')?.textContent||'').trim()]));
          const r=x=>{const q=x.getBoundingClientRect();return {w:q.width,c:q.left+q.width/2}};
          return {panel:r(p),body:r(b),popup:r(popup),edit:r(edit),del:r(del),source:sub.textContent,summaryDisplay:getComputedStyle(summary).display,gutter:getComputedStyle(b).scrollbarGutter,scrollbarWidth:getComputedStyle(b).scrollbarWidth,rows,editText:edit.textContent,detailsOpen:details.open};
        }""")
        assert 316 <= result['panel']['w'] <= 321, result
        assert abs(result['body']['w']-result['popup']['w']) <= 1.5, result
        assert abs(result['edit']['c']-result['del']['c']) <= 1.0, result
        assert 'Data Sync · 1-40TH RECON' in result['source'], result
        assert result['summaryDisplay']=='none' and result['editText']=='Edit', result
        assert result['gutter']=='auto' and result['scrollbarWidth']=='none', result
        for key in ('Width','Height','Area','Perimeter','Rotation'): assert key in result['rows'], result
        assert 'sq ft' in result['rows']['Area'], result
        # Edit button toggles the existing form without using native summary painting.
        page.click('.tak-shape-edit-toggle-i638'); page.wait_for_timeout(50)
        toggled=page.evaluate("() => ({open:document.querySelector('details.popup-edit').open,text:document.querySelector('.tak-shape-edit-toggle-i638').textContent})")
        assert toggled=={'open':True,'text':'Close Edit'}, toggled
        page.click('.tak-shape-edit-toggle-i638');
        # Unchanged Data Sync scan must preserve the exact Edit DOM node.
        stable=page.evaluate("""(o) => { const n=document.querySelector('.tak-shape-edit-toggle-i638'); window.__i638EditNode=n; window.lastDataSync={objects:[JSON.parse(JSON.stringify(o))]}; TakMapContextSidebarI572.refresh(); return window.__i638EditNode===document.querySelector('.tak-shape-edit-toggle-i638'); }""",OBJ)
        assert stable is True
        page.wait_for_timeout(2700)
        stable2=page.evaluate("window.__i638EditNode===document.querySelector('.tak-shape-edit-toggle-i638')")
        assert stable2 is True
        diag=page.evaluate('TakMapContextSidebarI572.diagnostics()')
        assert diag['version']=='i638' and diag['stableShapeInfoI638'] and diag['localizedGeometryI638'] and not diag['errors'], diag
        sizing=page.evaluate('TakMapContextPanelSizingI620.diagnostics()')
        assert sizing['version']=='i638' and sizing['compactContextWidth']==320 and sizing['contextScrollbarHidden'], sizing
        assert not errors, errors
        context.close()

        # Metric regional locale uses metric display units from the same neutral geometry.
        metric_context=browser.new_context(locale='de-DE',viewport={'width':1280,'height':760})
        metric=metric_context.new_page()
        metric_errors=[]; metric.on('pageerror',lambda exc:metric_errors.append(str(exc)))
        metric.route('**/*',route)
        metric.set_content(FIXTURE,wait_until='domcontentloaded',timeout=20000)
        metric.wait_for_function('window.TakMapContextSidebarI572 && window.TakMapContextPanelSizingI620')
        metric.evaluate('(o)=>{window.lastDataSync={objects:[o]};TakMapContextSidebarI572.showObject(o,"datasync",null,false)}',OBJ)
        metric.wait_for_timeout(200)
        metric_area=metric.evaluate("() => [...document.querySelectorAll('.tak-v322-row')].find(r=>(r.querySelector('b')?.textContent||'').trim()==='Area')?.querySelector('span')?.textContent||''")
        assert 'm²' in metric_area and 'sq ft' not in metric_area, metric_area
        assert not metric_errors, metric_errors
        metric_context.close(); browser.close()
    print('TAK Map i638 stable shape context browser test passed')
    return 0
if __name__=='__main__': raise SystemExit(main())
