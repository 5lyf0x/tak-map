#!/usr/bin/env python3
from __future__ import annotations
import ast, json, os, shutil, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TREE=ast.parse((ROOT/'tak_dashboard.py').read_text())
SCRIPT=''
for node in TREE.body:
    if isinstance(node, ast.Try):
        for child in node.body:
            if isinstance(child, ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_I500_ROUTE_UI' for t in child.targets):
                SCRIPT=ast.literal_eval(child.value)
                break
assert SCRIPT and 'takMapRouteUiV500' in SCRIPT
SCRIPT=SCRIPT.replace('<script id="takMapRouteUiV500">','',1).rsplit('</script>',1)[0]

HTML='''<!doctype html><html><head><meta charset="utf-8"></head><body>
<input id="routeNameInput" value=""><input id="routeColorInput" type="color" value="#ff6f2e">
<select id="routeMethodInput"><option selected>Driving</option></select>
<select id="routeDirectionInput"><option selected>Infil</option></select>
<select id="routeTypeInput"><option selected>Primary</option></select>
<select id="routeOrderInput"><option selected>Ascending Check Points</option></select>
<input id="routePrefixInput" value="CP"><select id="routeStyleInput"><option value="solid" selected>Solid</option></select>
<textarea id="routeNotesInput"></textarea><div id="routeEditPanel" class="active"></div>
</body></html>'''

STUB=r'''(()=>{
window.prompt=()=>{window.__promptCalled=true;throw new Error('native prompt called')};
window.alert=msg=>window.__alert=String(msg);
window.v233RouteState={points:[{lat:34,lng:-118},{lat:34.01,lng:-117.99},{lat:34.02,lng:-117.98}],color:'#ff6f2e',style:'solid'};
window.map={distance(a,b){const dx=(Number(b.lat)-Number(a.lat))*111000,dy=(Number(b.lng??b.lon)-Number(a.lng??a.lon))*92000;return Math.sqrt(dx*dx+dy*dy)}};
window.v234RedrawRoute=()=>window.__redraw=(window.__redraw||0)+1;
window.v233UploadGeoJson=async(name,feature)=>{window.__upload={name,feature};return {ok:true}};
window.v233ClearRoute=()=>{window.v233RouteState.points=[];window.__cleared=true};
window.v233ClosePanel=id=>{document.getElementById(id)?.classList.remove('active');window.__closed=id};
window.setActiveMapTool=tool=>window.__tool=tool;
window.v233FinishRoute=()=>window.__oldFinish=true;
})();'''

def main():
    chromium=next((x for x in ('chromium','chromium-browser','google-chrome','google-chrome-stable') if shutil.which(x)),None)
    if not chromium:
        print('SKIP: Chromium unavailable');return 0
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b=pw.chromium.launch(headless=True,executable_path=shutil.which(chromium),args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
        p=b.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
        p.set_content(HTML,wait_until='domcontentloaded');p.add_script_tag(content=STUB);p.add_script_tag(content=SCRIPT)
        p.wait_for_function("window.TakMapRouteUiV500 && window.v233FinishRoute.__takRouteSaveV500===true")
        p.evaluate("()=>window.v233FinishRoute()")
        p.wait_for_selector('#takRouteSaveV500')
        opened=p.evaluate("""()=>({prompt:!!window.__promptCalled,title:document.getElementById('takRouteSaveTitleV500').textContent.trim(),categories:Array.from(document.getElementById('takRouteCategoryV500').options).map(o=>o.textContent),category:document.getElementById('takRouteCategoryV500').value,length:document.getElementById('takRouteLengthV500').textContent.trim(),points:v233RouteState.points.length})""")
        expected=['General','Primary','Alternate','Ingress','Egress','Evacuation','Patrol','Search','Medical','Logistics','Restricted / Avoid','Training','Other']
        assert opened['prompt'] is False and opened['title']=='Save Route' and opened['categories']==expected and opened['category']=='General',opened
        assert 'mi' in opened['length'] and 'km' in opened['length'] and opened['points']==3,opened
        # Color selection updates the unfinished route and closes the native picker by blurring.
        p.locator('#takRouteColorV500').evaluate("e=>{e.focus();e.value='#3366cc';e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}))}")
        color=p.evaluate("()=>({value:document.getElementById('takRouteColorV500').value,hex:document.getElementById('takRouteColorHexV500').textContent,state:v233RouteState.color,legacy:document.getElementById('routeColorInput').value,focused:document.activeElement===document.getElementById('takRouteColorV500'),redraw:window.__redraw||0})")
        assert color=={'value':'#3366cc','hex':'#3366CC','state':'#3366cc','legacy':'#3366cc','focused':False,'redraw':2},color
        p.locator('#takRouteNameV500').fill('Evacuation North')
        p.locator('#takRouteCategoryV500').select_option('Evacuation')
        p.locator('#takRouteNotesV500').fill('Use during flood response.')
        p.locator('[data-route-close]').last.click()
        canceled=p.evaluate("()=>({dialog:!!document.getElementById('takRouteSaveV500'),points:v233RouteState.points.length,name:v233RouteState.name,category:v233RouteState.category,notes:v233RouteState.notes})")
        assert canceled=={'dialog':False,'points':3,'name':'Evacuation North','category':'Evacuation','notes':'Use during flood response.'},canceled
        p.evaluate("()=>window.v233FinishRoute()")
        p.wait_for_selector('#takRouteSaveV500')
        assert p.locator('#takRouteNameV500').input_value()=='Evacuation North'
        assert p.locator('#takRouteCategoryV500').input_value()=='Evacuation'
        p.locator('#takRouteSaveButtonV500').click();p.wait_for_function("window.__upload && window.__cleared===true")
        saved=p.evaluate("""()=>{const x=window.__upload.feature,p=x.properties;return {name:window.__upload.name,geometry:x.geometry.type,coords:x.geometry.coordinates,category:p.category,routeCategory:p.route_category,color:p.color,notes:p.notes,hasMiles:Number.isFinite(p.length_miles)&&p.length_miles>0,hasKm:Number.isFinite(p.length_km)&&p.length_km>0,start:[p.start_lat,p.start_lon],end:[p.end_lat,p.end_lon],created:!!p.created_at,points:v233RouteState.points.length,panel:document.getElementById('routeEditPanel').classList.contains('active'),tool:window.__tool,dialog:!!document.getElementById('takRouteSaveV500')}}""")
        assert saved['name']=='Evacuation North' and saved['geometry']=='LineString' and saved['category']=='Evacuation' and saved['routeCategory']=='Evacuation' and saved['color']=='#3366cc' and saved['notes']=='Use during flood response.',saved
        assert saved['hasMiles'] and saved['hasKm'] and saved['start']==[34,-118] and saved['end']==[34.02,-117.98] and saved['created'],saved
        assert saved['points']==0 and saved['panel'] is False and saved['tool']=='move' and saved['dialog'] is False,saved
        diag=p.evaluate("()=>TakMapRouteUiV500.diagnostics()")
        b.close()
    if errors:raise AssertionError(errors)
    assert diag['version']=='i500' and diag['opened']==2 and diag['saved']==1 and diag['canceled']==1,diag
    print('TAK Map i500 themed route save dialog browser test passed')
    print(json.dumps(diag,sort_keys=True))
    return 0

if __name__=='__main__':
    code=main()
    try:sys.stdout.flush();sys.stderr.flush()
    except Exception:pass
    os._exit(int(code or 0))
