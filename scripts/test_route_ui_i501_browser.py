#!/usr/bin/env python3
from __future__ import annotations
import ast, json, os, shutil, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TREE=ast.parse((ROOT/'tak_dashboard.py').read_text())
SCRIPTS={}
for node in TREE.body:
    if isinstance(node, ast.Try):
        for child in node.body:
            if isinstance(child, ast.Assign):
                for t in child.targets:
                    if isinstance(t,ast.Name) and t.id in {'_I500_ROUTE_UI','_I501_ROUTE_SAVE_FIX'}:
                        SCRIPTS[t.id]=ast.literal_eval(child.value)
assert set(SCRIPTS)=={'_I500_ROUTE_UI','_I501_ROUTE_SAVE_FIX'},SCRIPTS.keys()
def body(name,script_id):
    return SCRIPTS[name].replace(f'<script id="{script_id}">','',1).rsplit('</script>',1)[0]
ROUTE_SCRIPT=body('_I500_ROUTE_UI','takMapRouteUiV500')
FIX_SCRIPT=body('_I501_ROUTE_SAVE_FIX','takMapRouteSaveFixV501')
TOOL_SCRIPT=(ROOT/'assets'/'tak-map-tool-ux-v491.js').read_text()

HTML='''<!doctype html><html><head><meta charset="utf-8"></head><body>
<div id="map"></div><input id="routeNameInput" value=""><input id="routeColorInput" type="color" value="#ff6f2e">
<select id="routeMethodInput"><option selected>Driving</option></select>
<select id="routeDirectionInput"><option selected>Infil</option></select>
<select id="routeTypeInput"><option selected>Primary</option></select>
<select id="routeOrderInput"><option selected>Ascending Check Points</option></select>
<input id="routePrefixInput" value="CP"><select id="routeStyleInput"><option value="solid" selected>Solid</option></select>
<textarea id="routeNotesInput"></textarea><div id="routeEditPanel" class="active"></div>
</body></html>'''

STUB=r'''(()=>{
window.prompt=()=>{window.__promptCalled=true;throw new Error('native prompt called')};
window.alert=msg=>window.__alert=String(msg);window.activeMapTool='route';
window.v233RouteState={points:[{lat:34,lng:-118},{lat:34.01,lng:-117.99},{lat:34.02,lng:-117.98}],color:'#ff6f2e',style:'solid'};
window.map={distance(a,b){const dx=(Number(b.lat)-Number(a.lat))*111000,dy=(Number(b.lng??b.lon)-Number(a.lng??a.lon))*92000;return Math.sqrt(dx*dx+dy*dy)}};
window.v234RedrawRoute=()=>window.__redraw=(window.__redraw||0)+1;
window.v233ClearRoute=()=>{window.v233RouteState.points=[];window.__cleared=true};
window.v233ClosePanel=id=>{document.getElementById(id)?.classList.remove('active');window.__closed=id};
window.setActiveMapTool=tool=>{window.activeMapTool=tool;window.__tool=tool};
window.v233FinishRoute=()=>window.__oldFinish=true;
window.refreshLocalData=async()=>{window.__refreshed=(window.__refreshed||0)+1;return {ok:true}};
window.drawImportedObjects=()=>window.__redrawn=(window.__redrawn||0)+1;
window.renderImportRows=()=>window.__rows=(window.__rows||0)+1;
window.fetch=async(url,init={})=>{if(String(url)==='/api/tak-map/import'){
  const f=init.body&&init.body.get&&init.body.get('files');window.__uploadFile={name:f&&f.name,type:f&&f.type,text:f?await f.text():''};
  return new Response(JSON.stringify({ok:true,imports:[{id:'saved-route'}]}),{status:200,headers:{'Content-Type':'application/json'}})}
  return new Response(JSON.stringify({ok:true}),{status:200,headers:{'Content-Type':'application/json'}})};
})();'''

def main():
    chromium=next((x for x in ('chromium','chromium-browser','google-chrome','google-chrome-stable') if shutil.which(x)),None)
    if not chromium:
        print('SKIP: Chromium unavailable');return 0
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b=pw.chromium.launch(headless=True,executable_path=shutil.which(chromium),args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
        p=b.new_page(viewport={'width':1200,'height':900});errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
        p.set_content(HTML,wait_until='domcontentloaded');p.add_script_tag(content=STUB);p.add_script_tag(content=TOOL_SCRIPT);p.add_script_tag(content=ROUTE_SCRIPT);p.add_script_tag(content=FIX_SCRIPT)
        p.wait_for_function("window.TakMapRouteUiV500 && window.TakMapRouteSaveFixV501 && window.TakMapToolUxV486 && window.v233FinishRoute.__takRouteSaveV500===true")
        assert p.evaluate("typeof window.v233UploadGeoJson")=='function'
        p.evaluate("()=>window.v233FinishRoute()")
        p.wait_for_selector('#takRouteSaveV500')
        # Real user click opens the shared Measure-tool picker above the route modal.
        p.locator('#takRouteColorV500').click()
        p.wait_for_selector('#takMapColorPickerV486')
        picker=p.evaluate("()=>({pickerZ:Number(getComputedStyle(document.getElementById('takMapColorPickerV486')).zIndex),overlayZ:Number(getComputedStyle(document.getElementById('takRouteSaveV500')).zIndex),swatches:document.querySelectorAll('#takMapColorPickerV486 [data-color]').length})")
        assert picker['pickerZ']>picker['overlayZ'] and picker['swatches']>=20,picker
        p.locator('#takMapColorPickerV486 [data-color="#2386ff"]').click()
        p.wait_for_function("!document.getElementById('takMapColorPickerV486')")
        color=p.evaluate("()=>({value:document.getElementById('takRouteColorV500').value,hex:document.getElementById('takRouteColorHexV500').textContent,state:v233RouteState.color,legacy:document.getElementById('routeColorInput').value,redraw:window.__redraw||0})")
        assert color['value']=='#2386ff' and color['hex']=='#2386FF' and color['state']=='#2386ff' and color['legacy']=='#2386ff' and color['redraw']>=2,color
        p.locator('#takRouteNameV500').fill('Evacuation North');p.locator('#takRouteCategoryV500').select_option('Evacuation');p.locator('#takRouteNotesV500').fill('Use during flood response.')
        p.locator('#takRouteSaveButtonV500').click();p.wait_for_function("window.__uploadFile && window.__cleared===true")
        saved=p.evaluate("""()=>{const fc=JSON.parse(window.__uploadFile.text),x=fc.features[0],q=x.properties;return {url:'/api/tak-map/import',filename:window.__uploadFile.name,mime:window.__uploadFile.type,featureCount:fc.features.length,name:q.name,color:q.color,category:q.category,notes:q.notes,geometry:x.geometry.type,coords:x.geometry.coordinates,refreshed:window.__refreshed||0,redrawn:window.__redrawn||0,rows:window.__rows||0,imports:(window.lastImports||[]).length,dialog:!!document.getElementById('takRouteSaveV500'),points:v233RouteState.points.length,tool:window.__tool,diag:TakMapRouteSaveFixV501.diagnostics()}}""")
        assert saved['filename']=='Evacuation North.geojson' and saved['mime']=='application/geo+json' and saved['featureCount']==1,saved
        assert saved['name']=='Evacuation North' and saved['color']=='#2386ff' and saved['category']=='Evacuation' and saved['notes']=='Use during flood response.' and saved['geometry']=='LineString',saved
        assert saved['refreshed']==1 and saved['redrawn']==1 and saved['rows']==1 and saved['imports']==1,saved
        assert saved['dialog'] is False and saved['points']==0 and saved['tool']=='move' and saved['diag']['uploads']==1,saved
        b.close()
    if errors:raise AssertionError(errors)
    print('TAK Map i501 route save adapter and shared color picker browser test passed')
    print(json.dumps({'picker':picker,'color':color,'saved':saved},sort_keys=True))
    return 0

if __name__=='__main__':
    code=main()
    try:sys.stdout.flush();sys.stderr.flush()
    except Exception:pass
    os._exit(int(code or 0))
