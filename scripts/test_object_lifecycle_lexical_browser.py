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
    from playwright.sync_api import sync_playwright
    html='''<!doctype html><html><body><div id="localDataRows"></div><div id="dataSyncRows"></div><button id="selectionDeleteBtn">Delete</button><div id="selectionDeleteNote"></div></body></html>'''
    lexical=r'''
      let lastImports=[];
      let lastDataSync={missions:[],objects:[],packages:[]};
      let map={hasLayer(){return false},removeLayer(){}};
      function group(){return {items:[],addLayer(x){this.items.push(x);return this},removeLayer(x){this.items=this.items.filter(v=>v!==x)},clearLayers(){this.items=[]},eachLayer(fn){this.items.slice().forEach(fn)}}}
      let importedLayer=group();
      let dataSyncLayer=group();
      const state={dataSync:true,imported:true,local:{routes:{},points:{},shapes:{},hidden:{}},localCollapsed:{routes:false,points:false,shapes:false},dataSyncCollapsed:{missions:false,pointers:false,routes:false,shapes:false,files:false,other:true}};
      function importedFeatures(){return [{name:'legacy'}]}
      function addObjectLayer(owner,o){const layer={on(){return this},addTo(){return this},remove(){this.removed=true}};owner.addLayer(layer);o.__layer=layer;return layer}
      function drawImportedObjects(){for(const o of importedFeatures())addObjectLayer(importedLayer,o,'imported')}
      function drawDataSyncObjects(items){for(const o of items||[])addObjectLayer(dataSyncLayer,o,'datasync')}
      function renderLocalActions(){return '<button>Hide</button>'}
      function renderLocalSection(){return ''}
      function localDataSets(){return {routes:[],points:[],shapes:[]}}
      function localDataAction(){}
      function renderDataSyncRows(){}
      function deleteDataSyncItem(){}
      function popupEditKey(){return 'legacy'}
      function popupEditForm(){return ''}
      function deletePopupEdit(){}
      function refreshTerrain3DObjects(){}
      function terrain3DDataHash(){return 'old'}
      window.esc=x=>String(x);window.formatCoords=(a,b)=>a+','+b;window.assetDescriptor=()=>'';window.popupNotes=()=>'';
      window.localDataKindForFeature=o=>o.kind==='route'?'routes':o.kind==='shape'?'shapes':'points';
      window.selectedLocal=()=>[];window.localSelectedLabel=()=>'';window.renderLocalDataRows=()=>{};
      window.refreshImports=async()=>{};window.refreshDataSync=async()=>{};window.refreshLocalData=async()=>{};
      window.renderDataSyncSection=()=>'';window.missionNameFromAny=()=>'';window.missionDisplayMeta=()=>'';window.dataSyncCategory=()=>'';
      window.__takSelectionStateV477={selected:[],selectedIds:new Set()};window.TakMapSelectionV478={refreshReview(){}};
      window.fetch=async()=>({ok:true,status:200,json:async()=>({deleted_ids:[],failed_ids:[],not_found_ids:[],unsupported_ids:[]})});
      window.confirm=()=>true;window.alert=()=>{};
    '''
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=shutil.which(chromium),args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
        page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content(html,wait_until='domcontentloaded')
        page.add_script_tag(content=lexical)
        page.add_script_tag(content=ASSET.read_text())
        page.wait_for_function('window.TakMapObjectLifecycleV486',timeout=5000)
        result=page.evaluate('''() => {
          const local={kind:'point',name:'Lexical Local',object_id:'local-lex',local_id:'local-lex',_local_id:'local-lex',source_id:'local-lex',source_kind:'local',canonical_id:'local:local-lex'};
          const webform={kind:'point',name:'Lexical Webform',source:'webform'};
          lastImports=[{id:'imp',name:'imp',features:[local]},{id:'webform-live',source:'webform',features:[webform]}];
          const features=importedFeatures();
          drawImportedObjects();
          return {
            names:features.map(x=>x.name),
            localIds:localDataSets().points.map(x=>x.id),
            actions:renderLocalActions('points',[]),
            localEntry:!!TakMapObjectLifecycleV486.entryForId('local:local-lex'),
            webformEntry:TakMapObjectLifecycleV486.canonicalId(webform,'local'),
            hidden:state.local.hidden
          }
        }''')
        browser.close()
    if errors:raise AssertionError(errors)
    assert result['names']==['Lexical Local','Lexical Webform'],result
    assert result['localIds']==['local:local-lex'],result
    assert 'Hide' not in result['actions'] and 'Show' not in result['actions'],result
    assert result['localEntry'] is True,result
    assert result['webformEntry']=='',result
    assert result['hidden']=={},result
    print('Object lifecycle lexical-global integration and Webform separation browser test passed')
    print(json.dumps(result,sort_keys=True))
    return 0

if __name__=='__main__':raise SystemExit(main())
