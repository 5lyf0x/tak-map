"""i667 isolated contextual sidebar edit-route DOM+identity acceptance."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
s=(ROOT/'assets/tak-map-context-sidebar-i572.js').read_text()
start=s.index('  // i667: Local saved routes')
end=s.index('  function appendInfoDeleteAction()',start)
methods=s[start:end]
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
 page=browser.new_page(viewport={'width':1000,'height':750})
 page.set_content('<body style="background:#0b1117"><section id="panel"><div id="body"><div class="tak-context-delete-row-i572">Delete Route</div></div></section></body>')
 page.evaluate('''() => {
  window.savedRoute={object_id:'routeA',import_id:'fileA',route_revision_i659:'rev1',kind:'route',name:'Test Route'};
  window.lastImports=[{id:'fileA',features:[window.savedRoute]}];
  window.starts=0;
  window.takRouteEditorI654={startEditingSavedRoute:(feature,file)=>{if(feature!==window.savedRoute||file.id!=='fileA')throw Error('wrong route');window.starts++;return true}};
  window.state={body:document.getElementById('body'),panel:document.getElementById('panel'),selected:{object:window.savedRoute,source:'local'}};
  window.kindOf=o=>o.kind==='route'?'Route':'Other';
 }''')
 page.add_script_tag(content=methods)
 res=page.evaluate('''() => {
  appendRouteEditActionI667();
  const btn=document.querySelector('[data-tak-i667-edit-route]');
  const beforeDelete=btn.parentElement.nextElementSibling.classList.contains('tak-context-delete-row-i572');
  const enabled=!btn.disabled;
  beginSavedRouteEditI667();
  const starts=window.starts;
  const collapsed=window.state.panel.classList.contains('collapsed');
  window.state.selected.source='datasync';window.state.body.innerHTML='';
  appendRouteEditActionI667();
  return {button:!!btn,enabled,beforeDelete,starts,collapsed,remoteHasButton:!!window.state.body.querySelector('[data-tak-i667-edit-route]')};
 }''')
 assert res=={'button':True,'enabled':True,'beforeDelete':True,'starts':1,'collapsed':True,'remoteHasButton':False},res
 print('i667 sidebar Edit Route DOM integration PASS',res)
 browser.close()
