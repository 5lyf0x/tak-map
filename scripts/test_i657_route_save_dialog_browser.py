#!/usr/bin/env python3
"""Regression: actual legacy Save Route modal must save the resolved road polyline."""
from __future__ import annotations
import ast,runpy,shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
tree=ast.parse((ROOT/'tak_dashboard.py').read_text())
script=''
script501=''
for node in tree.body:
    if isinstance(node,ast.Try):
        for stmt in node.body:
            if isinstance(stmt,ast.Assign):
                if any(isinstance(t,ast.Name) and t.id=='_I500_ROUTE_UI' for t in stmt.targets):script=ast.literal_eval(stmt.value)
                if any(isinstance(t,ast.Name) and t.id=='_I501_ROUTE_SAVE_FIX' for t in stmt.targets):script501=ast.literal_eval(stmt.value)
assert script.startswith('<script id="takMapRouteUiV500">')
script=script.split('>',1)[1].rsplit('</script>',1)[0]
assert script501.startswith('<script id="takMapRouteSaveFixV501">')
script501=script501.split('>',1)[1].rsplit('</script>',1)[0]
editor=(ROOT/'assets/tak-map-route-editor-i654.js').read_text()
harness=runpy.run_path(str(ROOT/'scripts/test_route_editor_i654_browser.py'))['harness']
chromium=shutil.which('chromium') or shutil.which('chromium-browser')
assert chromium
with sync_playwright() as playwright:
    browser=playwright.chromium.launch(headless=True,executable_path=chromium,args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
    page=browser.new_page(viewport={'width':1200,'height':850})
    errors=[]
    page.on('pageerror', lambda error:errors.append(str(error)))
    page.set_content(harness,wait_until='domcontentloaded')
    page.evaluate('''()=>{
      const fields=`<input id="routeNameInput" value=""><input id="routeMethodInput" value="Driving">
      <input id="routeDirectionInput" value="Infil"><input id="routeTypeInput" value="Primary">
      <input id="routeOrderInput" value="Ascending Check Points"><input id="routePrefixInput" value="CP">
      <textarea id="routeNotesInput"></textarea><div id="routeEditPanel"></div>`;
      document.body.insertAdjacentHTML('beforeend',fields);
    }''')
    page.add_script_tag(content=script)
    page.add_script_tag(content=script501)
    page.add_script_tag(content=editor)
    page.wait_for_function('window.takRouteEditorI654?.installed && window.TakMapRouteUiV500',timeout=4000)
    # Legacy dialog schedules replacement after 250, 800, 1800 and 4000ms.
    page.wait_for_timeout(4400)
    assert page.evaluate('window.v233FinishRoute.__takRouteSaveV500===true')
    # Build a route with two clicks but three snapped road vertices.
    page.evaluate('''async()=>{
       v233ClearRoute();await v233RouteMapClick(L.latLng(34,-118));
       await v233RouteMapClick(L.latLng(34.01,-118.01));
    }''')
    page.wait_for_function('takRouteEditorI654.getResolvedSaveState().ready')
    assert page.evaluate('takRouteEditorI654.getResolvedSaveState().vertexCount')==3
    page.evaluate('window.v233FinishRoute()')
    page.wait_for_selector('#takRouteSaveV500')
    assert 'mi' in page.locator('#takRouteLengthV500').inner_text()
    page.locator('#takRouteNameV500').fill('Peach Springs Test')
    page.locator('#takRouteCategoryV500').select_option('Patrol')
    page.locator('#takRouteNotesV500').fill('Test full snapped geometry')
    page.locator('#takRouteColorV500').fill('#11aa77')
    page.locator('#takRouteSaveButtonV500').click()
    page.wait_for_function('window.savedRoute?.length===3',timeout=6000)
    result=page.evaluate('''()=>({
      shape:window.savedRoute,
      controls:window.lastSavedFeature.properties.route_control_point_count,
      resolved:window.lastSavedFeature.properties.route_resolved_vertex_count,
      category:window.lastSavedFeature.properties.category,
      color:window.lastSavedFeature.properties.color,
      notes:window.lastSavedFeature.properties.notes,
      length:window.lastSavedFeature.properties.length_m,
      dialog:!!document.querySelector('#takRouteSaveV500'),
      editorCleared:window.v233RouteState.points.length===0,
      saveCount:window.TakMapRouteUiV500.diagnostics().saved
    })''')
    assert len(result['shape'])==3,result
    assert result['controls']==2 and result['resolved']==3,result
    assert result['category']=='Patrol' and result['color']=='#11aa77',result
    assert result['notes']=='Test full snapped geometry' and result['length']>0,result
    assert not result['dialog'] and result['editorCleared'] and result['saveCount']==1,result
    # Rejected road connection cannot be saved by the legacy modal.
    page.evaluate('''async()=>{
      window.failResolve=true;setActiveMapTool('route');
      await v233RouteMapClick(L.latLng(34,-118));
      await v233RouteMapClick(L.latLng(34.01,-118.01));
    }''')
    page.wait_for_function('takRouteEditorI654.legs[0]?.status==="error"')
    page.evaluate('window.v233FinishRoute()')
    page.wait_for_selector('#takRouteSaveV500')
    page.locator('#takRouteSaveButtonV500').click()
    assert 'not ready' in page.locator('#takRouteSaveStatusV500').inner_text().lower()
    assert page.evaluate('v233RouteState.points.length')==2
    assert page.evaluate('window.savedRoute.length')==3
    assert not errors,errors
    browser.close()
print('PASS: i657 actual Save Route modal preserves snapped road vertices, metadata, and disconnected-leg blocking after legacy handler takeover')
