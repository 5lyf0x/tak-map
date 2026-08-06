#!/usr/bin/env python3
from __future__ import annotations
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / 'tak_dashboard.py'


def runtime_script() -> str:
    src = SERVER.read_text()
    helper = re.search(
        r'(function takMapSelectionExplicitLocalIdV478\(o\)\{[\s\S]*?)(?=function addObjectLayer\(group,o,sourceKey\))',
        src,
    )
    runtime = re.search(r'<script id="v362SelectionToolPointerFixPatch">\n([\s\S]*?)\n</script>', src)
    if not helper or not runtime:
        raise AssertionError('selection helper/runtime script not found')
    js = helper.group(1) + '\n' + runtime.group(1)
    for token in (
        'targetedDeleteOnly:true',
        'broadRefreshAfterDelete:false',
        'sourceOwnedIdentityRecovery:true',
        'resolveLayerDeleteMetaV478',
        'takMapStampSelectionIdentityV478',
        'previewFreehandForTest',
        'tak-selection-freehand-preview-v491',
    ):
        assert token in js, token
    return js


def main() -> int:
    chromium = next((n for n in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable') if shutil.which(n)), None)
    if not chromium:
        print('SKIP: Chromium unavailable')
        return 0

    html = '''<!doctype html><html><head><meta charset="utf-8"></head><body>
    <div id="mapStatus"></div><div id="map"></div><div id="floatingMapToolbar"></div>
    <div id="selectionToolMenu"></div>
    <div id="selectionReviewPanel"><button id="selectionReviewClose"></button><div id="selectionReviewSummary"></div><div id="selectionReviewList"></div><div id="selectionDeleteNote" class="sel-note"></div><button id="selectionFitBtn"></button><button id="selectionExportBtn"></button><button id="selectionDeleteBtn"></button><button id="selectionClearBtn"></button></div>
    </body></html>'''

    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, executable_path=shutil.which(chromium), args=['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage'])
        page = browser.new_page()
        errors: list[str] = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.set_content(html, wait_until='domcontentloaded')
        page.evaluate('''() => {
          window.__fetches=[];window.__refreshCounts={cot:0,imports:0,local:0,ds:0};
          window.confirm=()=>true;
          window.fetch=async (url,opts={})=>{window.__fetches.push({url:String(url),body:String(opts.body||''),method:String(opts.method||'GET')});return {ok:true,status:200,json:async()=>({ok:true,imports:[]})}};
          window.refreshCot=()=>{window.__refreshCounts.cot++};window.refreshImports=()=>{window.__refreshCounts.imports++};window.refreshLocalData=()=>{window.__refreshCounts.local++};window.refreshDataSync=()=>{window.__refreshCounts.ds++};
          window.renderDataSyncRows=()=>{};
          window.popupEditKey=o=>String(o.source||o.source_table||'Data Sync')+':'+String(o.uid||o.id||'');
          const mapContainer=document.getElementById('map');mapContainer.getBoundingClientRect=()=>({left:0,top:0,width:800,height:600});
          window.map={hasLayer:()=>false,removeLayer(){},eachLayer(){},getContainer:()=>mapContainer,invalidateSize(){},distance:()=>10,containerPointToLatLng:p=>({lat:p[1],lng:p[0]}),latLngToLayerPoint:ll=>({x:ll.lng,y:ll.lat})};
          class Circle{} class Polygon{} class TileLayer{}
          function layerGroup(){return {items:[],_takSelectionLayer:false,addTo(){return this},addLayer(x){if(!this.items.includes(x))this.items.push(x);return this},removeLayer(x){const i=this.items.indexOf(x);if(i>=0)this.items.splice(i,1);window.__removed=(window.__removed||[]).concat([x])},eachLayer(fn){this.items.slice().forEach(fn)}}}
          function shape(options){return {options,addTo(g){g.addLayer(this);return this},remove(){}}}
          window.L={Circle,Polygon,TileLayer,layerGroup,polygon:(pts,opts)=>shape(opts),circleMarker:(p,opts)=>shape(opts),circle:(p,opts)=>shape(opts),rectangle:(b,opts)=>shape(opts),latLngBounds:()=>null,DomEvent:{stop(){}}};
          window.setActiveMapTool=()=>{};
        }''')
        page.add_script_tag(content=runtime_script())
        page.wait_for_function('window.TakMapSelectionV478 && window.__takSelectionStateV477', timeout=5000)
        result = page.evaluate('''async () => {
          const api=window.TakMapSelectionV478,st=window.__takSelectionStateV477;
          const ownerLocal={removed:[],removeLayer(layer){this.removed.push(layer)}};
          const ownerDs={removed:[],removeLayer(layer){this.removed.push(layer)}};
          const layerLike=(leafletId)=>({_leaflet_id:leafletId,addTo(){return this},remove(){this.removed=true}});

          // Simulate the reported defect: selectable representations have no pre-stamped delete metadata.
          // Their exact source objects still own those layers under arbitrary renderer property names.
          const localLayer=layerLike(5781),dsLayer=layerLike(5782);
          localLayer._takSelectionOwnerGroup=ownerLocal;dsLayer._takSelectionOwnerGroup=ownerDs;
          const localObject={name:'Square 11:04:20 AM Shape',mysteryPolygonRepresentation:localLayer};
          const dsObject={name:'Mission Polygon',uid:'DS-UID-77',source:'Data Sync',alternateRendererLayer:dsLayer};
          window.lastImports=[{id:'import-abc',name:'shape.geojson',features:[localObject]}];
          window.lastDataSync={objects:[dsObject]};

          const unrelatedA={uid:'POINT-A',lat:34.1234567,lon:-118.2345678};
          const unrelatedB={uid:'POINT-B',lat:35.3456789,lon:-117.4567891};
          const before={a:[unrelatedA.lat,unrelatedA.lon],b:[unrelatedB.lat,unrelatedB.lon],aRef:unrelatedA,bRef:unrelatedB};
          st.selected=[
            {id:'layer:5781',canonicalId:'layer:5781',name:localObject.name,kind:'shape',layer:localLayer,layers:[localLayer],points:[{lat:34,lng:-118}]},
            {id:'layer:5782',canonicalId:'layer:5782',name:dsObject.name,kind:'shape',layer:dsLayer,layers:[dsLayer],points:[{lat:35,lng:-117}]}
          ];
          st.selectedIds=new Set(st.selected.map(x=>x.id));
          api.refreshReview();
          const reviewBefore={
            disabled:document.getElementById('selectionDeleteBtn').disabled,
            note:document.getElementById('selectionDeleteNote').textContent,
            summary:document.getElementById('selectionReviewSummary').textContent,
            localMeta:api.selectedDeleteMeta(st.selected[0]),
            dsMeta:api.selectedDeleteMeta(st.selected[1])
          };

          const out=await api.deleteSelected();
          const requests=window.__fetches.map(req=>{let body={};try{body=JSON.parse(req.body||'{}')}catch(e){}return {...req,body}});
          const coordsStable=unrelatedA===before.aRef&&unrelatedB===before.bRef&&unrelatedA.lat===before.a[0]&&unrelatedA.lon===before.a[1]&&unrelatedB.lat===before.b[0]&&unrelatedB.lon===before.b[1];
          const noBroad=Object.values(window.__refreshCounts).every(v=>v===0);

          // Unsupported live/transient layer: UI must disable Delete and explain why.
          const unsupportedLayer=layerLike(9001);
          unsupportedLayer.name='Not an identity';unsupportedLayer.lat=34.2;unsupportedLayer.lon=-117.2;
          st.selected=[{id:'layer:9001',canonicalId:'layer:9001',name:'Transient object',kind:'shape',layer:unsupportedLayer,layers:[unsupportedLayer],points:[{lat:34.2,lng:-117.2}]}];
          st.selectedIds=new Set(['layer:9001']);
          api.refreshReview();
          const unsupportedMeta=api.selectedDeleteMeta(st.selected[0]);
          const fetchBeforeUnsupported=window.__fetches.length;
          const unsupportedOut=await api.deleteSelected();
          const unsupportedUi={
            disabled:document.getElementById('selectionDeleteBtn').disabled,
            aria:document.getElementById('selectionDeleteBtn').getAttribute('aria-disabled'),
            note:document.getElementById('selectionDeleteNote').textContent,
            warning:document.getElementById('selectionDeleteNote').classList.contains('warning'),
            fetchDelta:window.__fetches.length-fetchBeforeUnsupported
          };

          const explicitLayer=layerLike(9100);explicitLayer.feature={properties:{_local_id:'explicit-import:4'}};
          const explicitMeta=api.resolveLayerDeleteMeta(explicitLayer,[explicitLayer]);
          const unsafeLayer=layerLike(9200);unsafeLayer.feature={properties:{name:'Same name',lat:34,lon:-118}};
          const unsafeMeta=api.resolveLayerDeleteMeta(unsafeLayer,[unsafeLayer]);
          const preview=api.previewFreehandForTest([{lat:1,lng:1},{lat:1,lng:2},{lat:2,lng:2}]);
          return {
            aliasSame:window.TakMapSelectionV477===window.TakMapSelectionV478,
            reviewBefore,out,requests,ownerLocalRemoved:ownerLocal.removed.length,ownerDsRemoved:ownerDs.removed.length,
            coordsStable,noBroad,remainingAfterDelete:out&&out.deleted===2?0:null,
            unsupportedMeta,unsupportedOut,unsupportedUi,explicitMeta,unsafeMeta,preview,diagnostics:api.diagnostics()
          };
        }''')
        browser.close()

    if errors:
        raise AssertionError(errors)
    assert result['aliasSame'] is True, result
    review = result['reviewBefore']
    assert review['disabled'] is False and '2 deletable' in review['summary'], result
    assert review['localMeta']['canonicalId'] == 'local:import-abc:0', result
    assert review['localMeta']['identityOrigin'] == 'local-registry-reference', result
    assert review['dsMeta']['canonicalId'] == 'datasync:data sync:DS-UID-77', result
    assert review['dsMeta']['identityOrigin'] == 'datasync-registry-reference', result
    assert 'source-owned Local Data or Data Sync identities' in review['note'], result

    assert result['out']['deleted'] == 2 and result['out']['unsupported'] == 0, result
    assert len(result['requests']) == 2, result
    local_req = next(r for r in result['requests'] if r['url'] == '/api/tak-map/local-data-delete')
    ds_req = next(r for r in result['requests'] if r['url'] == '/api/tak-map/popup-edit')
    assert local_req['body']['ids'] == ['import-abc:0'], result
    assert ds_req['body'] == {'key': 'Data Sync:DS-UID-77', 'source': 'Data Sync', 'delete_item': True}, result
    assert result['ownerLocalRemoved'] == 1 and result['ownerDsRemoved'] == 1, result
    assert result['coordsStable'] and result['noBroad'], result

    assert result['unsupportedMeta']['supported'] is False, result
    assert result['unsupportedOut']['deleted'] == 0 and result['unsupportedUi']['fetchDelta'] == 0, result
    assert result['unsupportedUi']['disabled'] is True and result['unsupportedUi']['aria'] == 'true' and result['unsupportedUi']['warning'] is True, result
    assert 'stable Local Data or Data Sync identity' in result['unsupportedUi']['note'], result
    assert result['explicitMeta']['canonicalId'] == 'local:explicit-import:4', result
    assert result['unsafeMeta'] is None, result

    preview = result['preview']
    assert preview['color'] == '#ff6f2e' and preview['weight'] == 2 and preview['fillColor'] == '#ff6f2e' and abs(preview['fillOpacity'] - .12) < 1e-9, result
    diagnostics = result['diagnostics']
    assert diagnostics['targetedDeleteOnly'] is True and diagnostics['broadRefreshAfterDelete'] is False, result
    assert diagnostics['sourceOwnedIdentityRecovery'] is True and diagnostics['deleteButtonDisabled'] is True, result
    print('Selection Local/Data Sync identity recovery, targeted delete, unsupported UI, and freehand preview browser test passed')
    print(json.dumps({
        'requests': [(r['url'], r['body']) for r in result['requests']],
        'deleted': result['out']['deleted'],
        'unsupportedDisabled': result['unsupportedUi']['disabled'],
        'coordsStable': result['coordsStable'],
        'noBroad': result['noBroad'],
        'preview': preview,
    }, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
