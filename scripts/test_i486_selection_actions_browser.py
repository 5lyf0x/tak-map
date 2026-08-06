#!/usr/bin/env python3
from __future__ import annotations
import json, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ASSET=ROOT/'assets'/'tak-map-object-lifecycle-v491.js'

def main()->int:
    chromium=next((n for n in ('chromium','chromium-browser','google-chrome','google-chrome-stable') if shutil.which(n)),None)
    if not chromium:
        print('SKIP: Chromium unavailable');return 0
    html='''<!doctype html><html><head><meta charset="utf-8"></head><body>
    <div id="localDataRows"><div class="local-add-grid"></div><div class="local-actions"><button id="localCardDelete" onclick="localDataAction('points','delete')">Delete</button></div></div>
    <div id="dataSyncRows"><div class="sync-card-actions"><button id="dataSyncCardDelete" onclick="deleteDataSyncItem(0,event)">Delete</button></div></div>
    <button id="toolSelectArea" class="active" aria-pressed="true"></button>
    <div id="selectionReviewPanel" class="active"><button id="selectionFitBtn">Fit</button><button id="selectionExportBtn">Export</button><button id="selectionDeleteBtn">Delete</button><button id="selectionClearBtn">Clear</button><div id="selectionDeleteNote"></div></div>
    </body></html>'''
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=shutil.which(chromium),args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
        page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content(html,wait_until='domcontentloaded')
        page.evaluate('''() => {
          window.__nativeConfirmCalls=0;window.confirm=()=>{window.__nativeConfirmCalls++;return true};window.__calls={fit:0,export:0,clear:0};
          window.state={local:{hidden:{},points:{},routes:{},shapes:{}}};window.lastImports=[];
          window.lastDataSync={objects:[{kind:'point',name:'Mission Marker',object_id:'datasync-mission-marker',canonical_id:'datasync:datasync-mission-marker',source_kind:'datasync',source:'Data Sync',mission_name:'Alpha Mission',delete_supported:true,mission_delete_target:'uid',mission_delete_value:'ATAK-123',lat:34.222222,lon:-118.333333}]};
          window.importedFeatures=()=>[];window.localDataSets=()=>({points:[],routes:[],shapes:[]});window.renderLocalDataRows=()=>{};window.renderDataSyncRows=()=>{};
          window.renderLocalActions=()=>'';window.renderLocalSection=()=>'';window.localDataAction=()=>{};window.drawImportedObjects=()=>{};window.drawDataSyncObjects=()=>{};window.addObjectLayer=()=>{};
          window.popupEditKey=()=>'';window.popupEditForm=()=>'';window.deletePopupEdit=()=>{};window.deleteDataSyncItem=()=>{};window.terrain3DDataHash=()=>'';window.refreshTerrain3DObjects=()=>{};
          window.fetch=async(url,opts)=>{const ids=JSON.parse(opts.body).object_ids;return {ok:true,status:200,json:async()=>({ok:true,deleted_ids:ids,failed_ids:[],not_found_ids:[],unsupported_ids:[],imports:[]})}};
          window.refreshImports=async()=>{};window.refreshDataSync=async()=>{};window.refreshLocalData=async()=>{};window.selectedLocal=()=>window.__selectedLocalIds||[];window.formatCoords=(lat,lon)=>Number(lat).toFixed(5)+', '+Number(lon).toFixed(5);
          const st=window.__takSelectionStateV477={selected:[],selectedIds:new Set(),mode:'rectangle',drawing:true,bounds:{},circle:{},freehandPts:[1]};
          window.TakMapSelectionV478={refreshReview(){window.__reviewCount=(window.__reviewCount||0)+1},diagnostics(){return {base:true}}};window.TakMapSelectionV477=window.TakMapSelectionV478;
          function baseClear(){window.__calls.clear++;st.selected=[];st.selectedIds=new Set();document.getElementById('selectionReviewPanel').classList.remove('active');const tool=document.getElementById('toolSelectArea');tool.classList.remove('active');tool.setAttribute('aria-pressed','false')}
          document.getElementById('selectionClearBtn').onclick=baseClear;
          document.getElementById('selectionFitBtn').onclick=()=>{window.__calls.fit++};
          document.getElementById('selectionExportBtn').onclick=()=>{window.__calls.export++};
        }''')
        page.add_script_tag(content=ASSET.read_text())
        page.wait_for_function('document.getElementById("selectionDeleteBtn").dataset.objectLifecycleV486 === "1"',timeout=5000)
        result=page.evaluate('''async()=>{
          const tick=()=>new Promise(r=>setTimeout(r,20));
          const waitDialog=async sel=>{for(let i=0;i<50&&!document.querySelector(sel);i++)await new Promise(r=>setTimeout(r,10))};
          const st=window.__takSelectionStateV477,panel=document.getElementById('selectionReviewPanel'),tool=document.getElementById('toolSelectArea');
          function fill(id){const layer={addTo(){return this}};const obj={kind:'point',name:id,object_id:id,local_id:id,_local_id:id,source_id:id,source_kind:'local',canonical_id:'local:'+id};TakMapObjectLifecycleV486.register(obj,'local',layer,null);st.selected=[{id:'layer-'+id,canonicalId:'layer-'+id,name:id,kind:'point',layer,layers:[layer]}];st.selectedIds=new Set(['layer-'+id]);st.mode='rectangle';st.drawing=true;st.bounds={};st.circle={};st.freehandPts=[1];panel.classList.add('active');tool.classList.add('active');tool.setAttribute('aria-pressed','true')}
          function cleared(){return st.selected.length===0&&st.selectedIds.size===0&&!panel.classList.contains('active')&&!tool.classList.contains('active')&&tool.getAttribute('aria-pressed')==='false'}
          fill('local-fit');document.getElementById('selectionFitBtn').click();await tick();const fitCleared=cleared();
          fill('local-export');document.getElementById('selectionExportBtn').click();await tick();const exportCleared=cleared();
          fill('local-clear');document.getElementById('selectionClearBtn').click();await tick();const clearCleared=cleared();

          const localObj={kind:'point',name:'Local Test Point',object_id:'local-card',local_id:'local-card',_local_id:'local-card',source_id:'local-card',source_kind:'local',canonical_id:'local:local-card',lat:34.123456,lon:-118.654321};TakMapObjectLifecycleV486.register(localObj,'local',{addTo(){return this}},null);window.__selectedLocalIds=['local:local-card'];
          document.getElementById('localCardDelete').click();await waitDialog('[data-dialog-cancel]');const localDialogText=document.getElementById('takMapDeleteDialogV486')?.textContent.replace(/\\s+/g,' ').trim()||'';document.querySelector('[data-dialog-cancel]').click();await tick();

          const dsObj=window.lastDataSync.objects[0];TakMapObjectLifecycleV486.register(dsObj,'datasync',{addTo(){return this}},null);
          document.getElementById('dataSyncCardDelete').click();await waitDialog('[data-dialog-cancel]');const dataSyncDialogText=document.getElementById('takMapDeleteDialogV486')?.textContent.replace(/\\s+/g,' ').trim()||'';document.querySelector('[data-dialog-cancel]').click();await tick();

          fill('local-test');const selectedEntry=TakMapObjectLifecycleV486.entryForId('local:local-test');selectedEntry.object.name='Selection Point';selectedEntry.object.lat=34.111111;selectedEntry.object.lon=-118.222222;
          const promise=TakMapSelectionV478.deleteSelected();await waitDialog('[data-dialog-confirm]');const dialog=document.getElementById('takMapDeleteDialogV486');const dialogText=dialog?.textContent.replace(/\\s+/g,' ').trim()||'';const dialogRole=dialog?.querySelector('[role=dialog]')?.getAttribute('role')||'';document.querySelector('[data-dialog-confirm]').click();const deletion=await promise;await tick();const deleteCleared=cleared();
          return {fitCleared,exportCleared,clearCleared,deleteCleared,deletion,dialogText,dialogRole,localDialogText,dataSyncDialogText,calls:window.__calls,nativeConfirmCalls:window.__nativeConfirmCalls,dialogDiagnostics:TakMapDialogV486.diagnostics(),selectionDiagnostics:TakMapSelectionV486.diagnostics(),lifecycleDiagnostics:TakMapObjectLifecycleV486.diagnostics()}
        }''')
        browser.close()
    if errors: raise AssertionError(errors)
    assert all(result[k] for k in ('fitCleared','exportCleared','clearCleared','deleteCleared')),result
    assert result['calls']['fit']==1 and result['calls']['export']==1 and result['calls']['clear']>=4,result
    assert result['deletion']['deleted']==1,result
    assert result['dialogRole']=='dialog' and 'Selection Point' in result['dialogText'] and 'Point' in result['dialogText'] and 'Local Data' in result['dialogText'] and '34.11111' in result['dialogText'],result
    assert 'Local Test Point' in result['localDialogText'] and '34.12346' in result['localDialogText'] and 'Local Data' in result['localDialogText'],result
    assert 'Mission Marker' in result['dataSyncDialogText'] and 'Alpha Mission' in result['dataSyncDialogText'] and '34.22222' in result['dataSyncDialogText'],result
    assert 'local:' not in result['dialogText'] and 'datasync:' not in result['dataSyncDialogText'] and result['nativeConfirmCalls']==0,result
    assert result['dialogDiagnostics']['themed'] and result['dialogDiagnostics']['enrichedDetails'] and not result['dialogDiagnostics']['nativeConfirm'],result
    assert result['selectionDiagnostics']['selectionClearsAfterAction'] is True,result
    assert result['lifecycleDiagnostics']['deleteActionCapture'] and result['lifecycleDiagnostics']['enrichedDeleteDetails'],result
    print('i491 enriched themed delete dialogs and Selection action reset browser test passed')
    print(json.dumps(result,sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())
