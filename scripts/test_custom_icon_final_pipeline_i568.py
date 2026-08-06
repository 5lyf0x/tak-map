#!/usr/bin/env python3
from pathlib import Path
import importlib.util, json, sys
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('tak_i568_custom_final',ROOT/'tak_dashboard.py')
m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m; spec.loader.exec_module(m)

PATH='db450cbe-2fec-47fb-bd2b-ba2db89b035e/Incident Management/water point.png'
UID='ATAK-WATER-POINT-I568'
RAW={
    'uid':UID,'mission_name':'CUSTOM-ICON-TEST','lat':34.1,'lon':-117.2,'type':'a-n-G',
    'details':{'type':'a-n-G','callsign':'Water Point','iconsetPath':PATH,
               'location':{'lat':34.1,'lon':-117.2}},
}
# Exact OpenTAKServer-style MissionUID projection: identity and point data may
# exist only under data/details/location, and iconsetPath must not trigger the
# legacy broad 'path' route detector.
EXACT_RAW={'data':UID,'mission_name':'CUSTOM-ICON-TEST','timestamp':'2026-07-27T12:00:00Z',
           'details':{'type':'a-n-G','callsign':'Water Point','iconsetPath':PATH,
                      'location':{'lat':34.1,'lon':-117.2}}}
assert m._row_route_like(EXACT_RAW,'mission_uids') is False
exact_marker=m._normalize_tak_marker(EXACT_RAW,'mission_uids','datasync')
assert exact_marker and exact_marker['uid']==UID and exact_marker['callsign']=='Water Point',exact_marker
assert exact_marker.get('iconsetPath')==PATH and exact_marker.get('kind')=='datasync',exact_marker
exact_objects=m._extract_data_sync_objects({'mission_uids':[EXACT_RAW]})
assert len(exact_objects)==1 and exact_objects[0].get('geometry')=='point',exact_objects
assert exact_objects[0].get('iconsetPath')==PATH,exact_objects

# Exercise the real raw PostgreSQL MissionUID -> normalized visible object boundary.
marker=m._normalize_tak_marker(RAW,'mission_uids','datasync')
assert marker and marker.get('iconsetPath')==PATH, marker
for key in ('sidc','SIDC','mil2525_file','mil2525_name','mil2525_label'):
    assert not marker.get(key),(key,marker.get(key),marker)
# Exercise the real final augmentation ordering, after all legacy MIL normalizers.
out=m._i512_augment_data_sync({'ok':True,'objects':[marker],'mission_uids':[RAW]}, {}, {'username':'tester','auth_mode':'local'})
visible=out['objects'][0]
assert visible.get('data_sync_current_iconset_path_i567')==PATH,visible
assert visible.get('iconsetPath')==PATH,visible
for source in (visible,visible.get('properties') or {}):
    for key in ('sidc','SIDC','mil2525_file','mil2525_name','mil2525_label'):
        assert not source.get(key),(key,source.get(key),source)
assert visible['data_sync_symbol_decision_i567']['authority']=='usericon-iconsetpath'
# A complete current XML event without usericon explicitly blocks stale nested details.
no_icon=dict(RAW)
no_icon['cot_xml']=f'<event uid="{UID}" type="a-n-G"><point lat="34.1" lon="-117.2"/><detail><contact callsign="Water Point"/></detail></event>'
assert not m._i566_authoritative_custom_path(no_icon), no_icon
# A complete current XML event with usericon is authoritative.
with_icon=dict(RAW)
with_icon['cot_xml']=f'<event uid="{UID}" type="a-n-G"><point lat="34.1" lon="-117.2"/><detail><usericon iconsetpath="{PATH}"/></detail></event>'
assert m._i566_authoritative_custom_path(with_icon)==PATH
# Standard 2525 mappings remain standard, and deletes never become custom icons.
assert not m._i566_authoritative_custom_path({'details':{'iconsetPath':'COT_MAPPING_2525C/a-f/a-f-G-U-C-A'}})
deleted={'uid':'DEL','type':'t-x-d-d','lat':34.1,'lon':-117.2,'details':{'iconsetPath':PATH}}
assert m._i567_apply_custom_path(deleted, PATH).get('data_sync_current_iconset_path_i567') is None
# Exact packaged asset exists and canonical lookup resolves it.
item=m._i555_registry_load()['by_path'].get(PATH)
assert item and (ROOT/'assets/icon-registry'/item['internal_path']).is_file(),item

# Browser-side final renderer: both flattened and nested paths must bypass MIL fallback,
# request the packaged custom asset, and successfully decode the image.
try:
    from playwright.sync_api import sync_playwright
except Exception as exc:
    raise SystemExit(f'Playwright required: {exc}')
js=(ROOT/'assets/tak-map-icon-registry-i568.js').read_text()
png=(ROOT/'assets/icon-registry'/item['internal_path']).read_bytes()
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-gpu'])
    page=browser.new_page(viewport={'width':800,'height':600})
    requested=[]
    def route_handler(route,request):
        path=urlparse(request.url).path
        if path=='/api/tak-map/icon-registry/icon':
            requested.append(request.url)
            return route.fulfill(status=200,content_type='image/png',body=png)
        return route.fulfill(status=204,body='')
    page.route('**/*',route_handler)
    page.set_content('<!doctype html><html data-tak-map-runtime="ready"><head><base href="https://example.test/"></head><body><div id="milPicker"></div><div id="out"></div></body></html>')
    page.evaluate("""() => {
      window.L={divIcon:o=>o};
      window.v233PointState={};
      window.renderMilPicker=()=>{};
      window.dataSyncIcon=o=>({html:'BASE-MIL-FALLBACK'});
      window.mil2525IconHtml=o=>'BASE-MIL-FALLBACK';
      window.fetch=async url=>new Response(JSON.stringify({ok:true,sets:[],icons:[],count:0,custom_icon_count:0,custom_set_count:0}),{status:200,headers:{'Content-Type':'application/json'}});
    }""")
    page.add_script_tag(content=js)
    page.wait_for_function("window.TakMapIconRegistryI568 && window.TakMapIconRegistryI568.diagnostics().customRendererAuthoritative",timeout=10000)
    result=page.evaluate("""path => {
      const flat=window.dataSyncIcon({uid:'F',callsign:'Flat',lat:1,lon:2,type:'a-n-G',iconsetPath:path});
      const nested=window.dataSyncIcon({uid:'N',callsign:'Nested',lat:1,lon:2,type:'a-n-G',details:{iconsetPath:path}});
      document.getElementById('out').innerHTML=flat.html+nested.html;
      return {flat:flat.html,nested:nested.html};
    }""",PATH)
    assert 'BASE-MIL-FALLBACK' not in result['flat'] and 'BASE-MIL-FALLBACK' not in result['nested'],result
    assert '/api/tak-map/icon-registry/icon?path=' in result['flat'],result
    assert 'water%20point.png' in result['flat'] and 'water%20point.png' in result['nested'],result
    page.wait_for_function("[...document.querySelectorAll('#out img')].length===2 && [...document.querySelectorAll('#out img')].every(i=>i.complete && i.naturalWidth>0)",timeout=10000)
    assert len(requested)>=1,requested
    browser.close()

# Runtime route and release HTML must point at an actually served current file.
assert '/assets/runtime/tak-map-icon-registry-i568.js?v=1.3.0-i568' in m.TAK_MAP_HTML
assert "'/assets/runtime/tak-map-icon-registry-i568.js'" in (ROOT/'tak_dashboard.py').read_text()
print('i568 final MissionUID projection and browser custom-icon rendering checks passed')
