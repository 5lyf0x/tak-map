#!/usr/bin/env python3
"""Chromium UI fixtures against real i001 sorting/rename function and footer scripts."""
from pathlib import Path
import re,sys,os
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(root))
os.environ.setdefault('TAK_DASHBOARD_DATA_DIR','/tmp/tak-map-i001-browser-test')
import tak_dashboard as m
h=m.TAK_MAP_HTML
css=(root/'assets/tak-map-offline-maps-i698.css').read_text()
core=(root/'assets/tak-map-core-i553.js').read_text()
rename=(root/'assets/tak-map-offline-maps-i698.js').read_text()
a=core.index('function sortOfflineMapPacksByNameI001(')
b=core.index('function titleCaseStatus(',a)
sort_js=core[a:b]
a=rename.index('function addRenameControl(')
b=rename.index('function decorateCards(',a)
rename_js=rename[a:b]

# Actual final generated HTML scripts, not new test-only reimplementations.
guard=re.search(r'<script id="takMapIdentityGuardI630">(.*?)</script>',h,re.S)
authority=re.search(r'<script id="takMapReleaseAuthorityI665">(.*?)</script>',h,re.S)
assert guard and authority

html='''<!doctype html><html><head><style>
.version-panel{padding:10px}.offline-list{max-height:300px;overflow-y:auto}
.offline-card{min-height:48px;padding:5px;border:1px solid #222;box-sizing:border-box}
</style><script>'''+guard.group(1)+'''</script></head><body>
<div class="version-panel"><div class="version-product">TAK Map</div><span class="release-main">1.4.0</span><span class="iteration-chip">i699</span></div>
<div id="offlineMapRows" class="offline-list tak-offline-i699"></div>
<script>'''+authority.group(1)+'''</script></body></html>'''
with sync_playwright() as p:
    print('starting chromium',flush=True)
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-gpu'])
    page=browser.new_page(viewport={'width':1200,'height':850})
    errors=[]
    page.on('pageerror',lambda e: errors.append(str(e)))
    print('content length',len(html),flush=True)
    page.set_default_timeout(6000)
    page.set_content(html,wait_until='domcontentloaded',timeout=7000)
    print('page loaded',flush=True)
    page.wait_for_timeout(50)
    assert page.locator('.release-main').inner_text()=='1.5.0'
    assert page.locator('.iteration-chip').inner_text()=='i004'
    page.evaluate("document.querySelector('.release-main').textContent='1.4.0';document.querySelector('.iteration-chip').textContent='i699';")
    page.wait_for_timeout(50)
    assert page.locator('.release-main').inner_text()=='1.5.0'
    assert page.locator('.iteration-chip').inner_text()=='i004'

    print('footer checked',flush=True)
    page.add_style_tag(content=css)
    page.evaluate('''() => {
      window.d=document;window.w=window;window.$=id=>document.getElementById(id);
      window.offlineMaps=[
      {id:'c',name:'map 10',created_by:'download',download_status:'complete'},
      {id:'a',name:'MAP 2',created_by:'download',download_status:'complete'},
      {id:'b',name:'imported',filename:'imported.mbtiles'},
      {id:'p',name:'partial',created_by:'download',download_status:'partial',partial:true,resume_available:true},
      {id:'q',name:'queued',created_by:'download',download_status:'queued'},
      ];
      window.lastSaved=null;
      window.fetch=async (url,opts)=>{
       const body=JSON.parse(opts.body);if(body.name==='Server Error')return {ok:false,status:400,json:async()=>({ok:false,error:'Server rejected'})};
       const m=window.offlineMaps.find(x=>x.id===body.id);m.name=body.name;
       window.lastSaved={id:m.id,name:m.name};return {ok:true,status:200,json:async()=>({ok:true,map:m,maps:window.offlineMaps})};
      };
      window.refreshOfflineMaps=async()=>{window.renderFixture();};
      window.renderFixture=()=>{const e=document.getElementById('offlineMapRows');
       e.innerHTML=window.takMapSortOfflineMapPacksI001(window.offlineMaps).map(m=>`<div class="offline-card" data-id="${m.id}"><div class="offline-card-title"><b>${m.name}</b></div><small>MBTILES</small><div class="row"><button>Apply</button><button>Send</button><button>Delete</button></div></div>`).join('');
       window.takMapSortOfflineMapPacksI001(window.offlineMaps).forEach((m,i)=>window.addRenameControl(e.children[i],m));
      };
    }''')
    page.add_script_tag(content=sort_js+'\n'+rename_js+'\nwindow.addRenameControl=addRenameControl;')
    page.evaluate('renderFixture()')
    print('fixture rendered',flush=True)
    order=page.locator('#offlineMapRows .offline-card').evaluate_all('(nodes)=>nodes.map(n=>n.getAttribute("data-id"))')
    assert order==['b','a','c','p','q'],order
    assert page.locator('#offlineMapRows .offline-rename-action').count()==3
    assert page.locator('[data-id="p"] .offline-rename-action').count()==0
    assert page.locator('[data-id="q"] .offline-rename-action').count()==0
    assert page.locator('[data-id="a"] .offline-rename-action').count()==1
    height=page.locator('#offlineMapRows').evaluate('e=>getComputedStyle(e).maxHeight')
    assert height=='600px',height
    print('opening editor',flush=True)
    page.locator('[data-id="a"] .offline-rename-action').click()
    assert page.locator('[data-id="a"] .offline-rename-editor').count()==1
    page.locator('[data-id="a"] .offline-rename-editor input').fill('no/path')
    page.locator('[data-id="a"] .offline-rename-buttons button').first.click()
    assert '1–120' in page.locator('[data-id="a"] .offline-rename-error').inner_text()
    page.locator('[data-id="a"] .offline-rename-editor input').fill('Changed 1')
    page.locator('[data-id="a"] .offline-rename-editor input').press('Escape')
    assert page.locator('[data-id="a"] .offline-rename-editor').count()==0
    page.locator('[data-id="a"] .offline-rename-action').click()
    page.locator('[data-id="a"] .offline-rename-editor input').fill('Server Error')
    page.locator('[data-id="a"] .offline-rename-editor input').press('Enter')
    page.wait_for_timeout(70)
    assert 'Server rejected' in page.locator('[data-id="a"] .offline-rename-error').inner_text()
    page.locator('[data-id="a"] .offline-rename-editor input').fill('Survey 1')
    page.locator('[data-id="a"] .offline-rename-editor input').press('Enter')
    print('submitted rename',flush=True)
    page.wait_for_function('window.lastSaved && window.lastSaved.name==="Survey 1"',timeout=6000)
    page.wait_for_timeout(60)
    assert page.locator('[data-id="a"] .offline-card-title b').inner_text()=='Survey 1'
    assert page.locator('.release-main').inner_text()=='1.5.0'
    assert page.locator('.iteration-chip').inner_text()=='i004'
    assert not errors,errors
    print('PASS: Chromium final footer guard, natural sorting, eligible buttons, 600px CSS, Save/Escape/Enter, client/server error rendering')
    browser.close()
