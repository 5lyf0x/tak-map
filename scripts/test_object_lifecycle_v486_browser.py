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
    <button id="toolClearHidden">Clear Hidden</button>
    <div id="localDataRows"></div><div id="dataSyncRows"></div>
    <div id="selectionReviewPanel"><button id="selectionDeleteBtn">Delete</button><div id="selectionDeleteNote"></div></div>
    </body></html>'''
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=shutil.which(chromium),args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
        page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content(html,wait_until='domcontentloaded')
        page.evaluate('''() => {
          window.__nativeConfirmCalls=0;window.confirm=()=>{window.__nativeConfirmCalls++;return true};window.alerts=[];window.alert=x=>window.alerts.push(String(x));window.__requests=[];
          window.fetch=async (url,opts={})=>{let body={};try{body=JSON.parse(opts.body||'{}')}catch(e){}window.__requests.push({url:String(url),body});const ids=body.object_ids||[];const response=ids.includes('local:local-card-a')?{ok:false,partial:true,deleted_ids:['local:local-card-a'],failed_ids:['local:local-card-b'],not_found_ids:[],unsupported_ids:[],results:[{object_id:'local:local-card-b',status:'failed',error:'test card failure'}],imports:[]}:{ok:false,partial:true,deleted_ids:['local:local-aaa'],failed_ids:['datasync:datasync-bbb'],not_found_ids:[],unsupported_ids:[],results:[{object_id:'datasync:datasync-bbb',status:'failed',error:'test failure'}],imports:[]};return {ok:true,status:200,json:async()=>response}};
          window.state={dataSync:true,imported:true,local:{routes:{},points:{},shapes:{},hidden:{'local:local-aaa':true}},localCollapsed:{routes:false,points:false,shapes:false},dataSyncCollapsed:{missions:false,pointers:false,routes:false,shapes:false,files:false,other:true}};
          window.lastImports=[];window.lastDataSync={missions:[],packages:[],objects:[]};
          function group(){return {items:[],addLayer(x){if(!this.items.includes(x))this.items.push(x);return this},removeLayer(x){this.items=this.items.filter(v=>v!==x);x.removed=true},clearLayers(){this.items=[]},eachLayer(fn){this.items.slice().forEach(fn)}}}
          window.importedLayer=group();window.dataSyncLayer=group();window.map={hasLayer:()=>false,removeLayer(x){x.removed=true}};
          window.esc=x=>String(x);window.formatCoords=(a,b)=>a+','+b;window.assetDescriptor=()=> 'Asset';window.popupNotes=()=>'';
          window.localDataKindForFeature=o=>o.kind==='route'?'routes':o.kind==='shape'?'shapes':'points';
          window.selectedLocal=kind=>Object.keys(window.state.local[kind]||{}).filter(id=>window.state.local[kind][id]);
          window.localSelectedLabel=(kind,n)=>n+' '+kind;window.centerSelectedLocal=()=>{};window.downloadLocalData=()=>{};window.openLocalDataPublish=()=>{};
          window.renderLocalDataRows=()=>{window.__localActions=window.renderLocalActions?window.renderLocalActions('points',[]):''};
          window.refreshImports=async()=>({ok:true});window.refreshDataSync=async()=>({ok:true});window.refreshLocalData=async()=>({ok:true});
          window.renderDataSyncSection=(kind,title,items,render)=>'<section data-kind="'+kind+'">'+items.map(render).join('')+'</section>';
          window.missionNameFromAny=()=>'';window.missionDisplayMeta=()=>'';window.dataSyncCategory=o=>o.kind==='route'?'Routes':o.kind==='shape'?'Shapes / Areas':'Point Markers';
          window.openDataSyncItemEdit=()=>{};window.centerDataSyncIndex=()=>{};
          window.renderLocalActions=()=>'<button>Hide</button>';window.renderLocalSection=()=>'';window.localDataSets=()=>({routes:[],points:[],shapes:[]});window.localDataAction=()=>{};
          window.importedFeatures=()=>[];window.drawImportedObjects=()=>{};window.drawDataSyncObjects=()=>{};
          window.popupEditKey=()=> 'legacy';window.popupEditForm=()=>'';window.deletePopupEdit=()=>{};window.deleteDataSyncItem=()=>{};
          window.terrain3DDataHash=()=> 'hash';window.refreshTerrain3DObjects=()=>{};
          window.addObjectLayer=(owner,o,source)=>{const primary={name:'primary',on(){return this},addTo(){return this},remove(){this.removed=true}};const hit={name:'hit',on(){return this},addTo(){return this},remove(){this.removed=true}};owner.addLayer(primary);owner.addLayer(hit);o.__layer=primary;o.__hitLayer=hit;return primary};
          window.__takSelectionStateV477={selected:[],selectedIds:new Set()};
          window.TakMapSelectionV478={refreshReview(){window.__reviewed=(window.__reviewed||0)+1}};window.TakMapSelectionV477=window.TakMapSelectionV478;
        }''')
        page.add_script_tag(content=ASSET.read_text())
        page.wait_for_function('window.TakMapObjectLifecycleV486 && document.getElementById("selectionDeleteBtn").dataset.objectLifecycleV486 === "1"',timeout=5000)
        result=page.evaluate('''async () => {
          async function acceptDelete(start){
            const promise=start();
            for(let i=0;i<50&&!document.querySelector('#takMapDeleteDialogV486 [data-dialog-confirm]');i++)await new Promise(r=>setTimeout(r,10));
            const dialog=document.getElementById('takMapDeleteDialogV486');
            if(!dialog)throw new Error('Themed delete dialog did not open');
            const text=dialog.textContent.replace(/\\s+/g,' ').trim();
            const themed=!!dialog.querySelector('.tak-delete-dialog-v491[role="dialog"]');
            dialog.querySelector('[data-dialog-confirm]').click();
            return {value:await promise,text,themed};
          }
          const local={kind:'point',name:'Local',lat:34,lon:-118,object_id:'local-aaa',local_id:'local-aaa',_local_id:'local-aaa',source_id:'local-aaa',source_kind:'local',canonical_id:'local:local-aaa'};
          const ds={kind:'shape',name:'Mission Shape',uid:'UID-1',source_kind:'datasync',object_id:'datasync-bbb',canonical_id:'datasync:datasync-bbb',source_id:'UID-1',mission_name:'Alpha',mission_delete_target:'uid',mission_delete_value:'UID-1',delete_supported:true,coords:[[1,2],[1,3],[2,3]]};
          const unsupported={kind:'point',name:'Read Only',uid:'UID-2',source_kind:'datasync',object_id:'datasync-ccc',canonical_id:'datasync:datasync-ccc',source_id:'UID-2',delete_supported:false,delete_unavailable_reason:'No mission ownership'};
          addObjectLayer(importedLayer,local,'imported');addObjectLayer(dataSyncLayer,ds,'datasync');
          const webform={kind:'point',name:'Live Webform',lat:35,lon:-117,source:'webform'};
          lastImports=[{id:'imp',name:'test',features:[local]},{id:'webform-live',name:'Webform Reports',source:'webform',features:[webform]}];lastDataSync={missions:[],packages:[],objects:[ds,unsupported]};
          const importedNamesBeforeDelete=importedFeatures().map(x=>x.name);
          const localSetNamesBeforeDelete=Object.values(localDataSets()).flat().map(x=>x.name);
          const webformCanonicalBeforeDelete=TakMapObjectLifecycleV486.canonicalId(webform,'local');
          const localEntry=TakMapObjectLifecycleV486.entryForId('local:local-aaa');const dsEntry=TakMapObjectLifecycleV486.entryForId('datasync:datasync-bbb');
          state.local.points={'local:local-aaa':true};
          const actions=renderLocalActions('points',[{id:'local:local-aaa'}]);
          await localDataAction('points','hide');
          renderDataSyncRows();
          const dataSyncHtml=document.getElementById('dataSyncRows').innerHTML;
          const transient={kind:'point',lat:10,lon:20};
          const popupKeys={local:popupEditKey(local),ds:popupEditKey(ds),transient:popupEditKey(transient)};
          const st=window.__takSelectionStateV477;
          st.selected=[
            {id:'layer:1',canonicalId:'layer:1',name:'Local',kind:'point',layer:local.__layer,layers:[local.__layer]},
            {id:'layer:2',canonicalId:'layer:2',name:'DS',kind:'shape',layer:ds.__layer,layers:[ds.__layer]}
          ];st.selectedIds=new Set(st.selected.map(x=>x.id));
          const localMeta=TakMapSelectionV478.selectedDeleteMeta(st.selected[0]);const dsMeta=TakMapSelectionV478.selectedDeleteMeta(st.selected[1]);
          const deletionRun=await acceptDelete(()=>TakMapSelectionV478.deleteSelected());
          const deletion=deletionRun.value;
          const cardA={kind:'point',name:'Card A',object_id:'local-card-a',local_id:'local-card-a',_local_id:'local-card-a',source_id:'local-card-a',source_kind:'local',canonical_id:'local:local-card-a'};
          const cardB={kind:'point',name:'Card B',object_id:'local-card-b',local_id:'local-card-b',_local_id:'local-card-b',source_id:'local-card-b',source_kind:'local',canonical_id:'local:local-card-b'};
          addObjectLayer(importedLayer,cardA,'imported');addObjectLayer(importedLayer,cardB,'imported');
          state.local.points={'local:local-card-a':true,'local:local-card-b':true};
          const cardDeleteRun=await acceptDelete(()=>localDataAction('points','delete'));
          const cardDelete=cardDeleteRun.value;
          return {
            localLayers:localEntry?localEntry.layers.size:0,dsLayers:dsEntry?dsEntry.layers.size:0,
            localMeta,dsMeta,deletion,remainingSelected:st.selected.map(x=>TakMapSelectionV478.selectedDeleteMeta(x).canonicalId),
            localRemoved:!!local.__layer.removed,dsRemoved:!!ds.__layer.removed,
            requests:window.__requests,actions,dataSyncHtml,popupKeys,
            hiddenState:state.local.hidden,clearHiddenExists:!!document.getElementById('toolClearHidden'),alerts:window.alerts,
            diagnostics:TakMapObjectLifecycleV486.diagnostics(),selectionDiagnostics:TakMapSelectionV486.diagnostics(),selectionAlias:TakMapSelectionV486===TakMapSelectionV478,
            importedNames:importedNamesBeforeDelete,
            localSetNames:localSetNamesBeforeDelete,
            webformCanonical:webformCanonicalBeforeDelete,
            dialog:{selection:deletionRun,card:cardDeleteRun,diagnostics:TakMapDialogV486.diagnostics(),nativeConfirmCalls:window.__nativeConfirmCalls},
            cardDelete,cardSelections:Object.keys(state.local.points).filter(id=>state.local.points[id]),
            cardARemoved:!!cardA.__layer.removed,cardBRemoved:!!cardB.__layer.removed
          }
        }''')
        browser.close()
    if errors:raise AssertionError(errors)
    assert result['localLayers']==2 and result['dsLayers']==2,result
    assert result['localMeta']['canonicalId']=='local:local-aaa' and result['localMeta']['supported'],result
    assert result['dsMeta']['canonicalId']=='datasync:datasync-bbb' and result['dsMeta']['supported'],result
    assert result['requests'][0]['url']=='/api/tak-map/object-delete',result
    assert result['requests'][0]['body']['object_ids']==['local:local-aaa','datasync:datasync-bbb'],result
    assert result['requests'][-1]['body']['object_ids']==['local:local-card-a','local:local-card-b'],result
    assert result['localRemoved'] is True and result['dsRemoved'] is False,result
    assert result['remainingSelected']==[],result
    assert 'Hide' not in result['actions'] and 'Show' not in result['actions'],result
    assert 'Delete unavailable' in result['dataSyncHtml'],result
    assert result['popupKeys']=={'local':'local:local-aaa','ds':'datasync:datasync-bbb','transient':'legacy'},result
    assert result['hiddenState']=={} and result['clearHiddenExists'] is False,result
    assert result['dialog']['selection']['themed'] and result['dialog']['card']['themed'],result
    assert all(token in result['dialog']['selection']['text'] for token in ['Delete Selected Items','Local','Mission Shape','Local Data','Data Sync','34,-118','3 vertices']),result
    assert 'local:' not in result['dialog']['selection']['text'] and 'datasync:' not in result['dialog']['selection']['text'],result
    assert result['dialog']['nativeConfirmCalls']==0 and result['dialog']['diagnostics']['nativeConfirm'] is False,result
    assert result['diagnostics']['perObjectHide'] is False,result
    assert result['selectionDiagnostics']['version']=='i491' and result['selectionDiagnostics']['perObjectHide'] is False,result
    assert result['selectionAlias'] is True,result
    assert 'Live Webform' in result['importedNames'],result
    assert 'Live Webform' not in result['localSetNames'],result
    assert result['webformCanonical']=='',result
    assert result['cardDelete']['deleted_ids']==['local:local-card-a'],result
    assert result['cardSelections']==['local:local-card-b'],result
    assert result['cardARemoved'] is True and result['cardBRemoved'] is False,result
    print('Object lifecycle canonical registration, confirmed-only deletion, and per-object Hide removal browser test passed')
    print(json.dumps({'request':result['requests'][-1],'remainingSelected':result['remainingSelected'],'diagnostics':result['diagnostics']},sort_keys=True))
    return 0

if __name__=='__main__':raise SystemExit(main())
