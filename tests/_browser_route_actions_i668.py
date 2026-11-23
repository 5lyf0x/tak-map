"""i668 Edit | Delete DOM event preservation and layout in Chromium."""
from pathlib import Path
from playwright.sync_api import sync_playwright
s=(Path(__file__).resolve().parents[1]/'assets/tak-map-context-sidebar-i572.js').read_text()
start=s.index('  // i667: Local saved routes')
end=s.index('  function appendInfoDeleteAction()',start)
methods=s[start:end]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
 page=browser.new_page(viewport={'width':540,'height':650})
 page.set_content('''<html><body style="background:#0d151c"><div id="panel" style="width:320px"><div id="body"><div class="tak-context-delete-row-i572"><button type="button" data-tak-i572-delete-current="1">Delete Route</button></div></div></div></body></html>''')
 page.evaluate('''() => {
  window.savedRoute={object_id:'routeA',import_id:'fileA',route_revision_i659:'rev1',kind:'route',name:'Test Route'};
  window.lastImports=[{id:'fileA',features:[window.savedRoute]}];
  window.starts=0;window.deletes=0;
  window.takRouteEditorI654={startEditingSavedRoute:(feature,file)=>{window.starts++;return true}};
  window.state={body:document.getElementById('body'),panel:document.getElementById('panel'),selected:{object:window.savedRoute,source:'local'}};
  window.kindOf=o=>o.kind==='route'?'Route':'Other';
  document.addEventListener('click',e=>{if(e.target.matches('[data-tak-i572-delete-current]'))window.deletes++});
 }''')
 page.add_script_tag(content=methods)
 page.evaluate('''() => {appendRouteEditActionI667();combineLocalRouteActionsI668();const edit=document.querySelector('[data-tak-i667-edit-route]');edit.addEventListener('click',()=>beginSavedRouteEditI667());}''')
 assert page.locator('.tak-context-route-actions-i668 button').count()==2
 layout=page.evaluate('''() => {const row=document.querySelector('.tak-context-route-actions-i668');const r=[...row.children].map(x=>x.getBoundingClientRect());return {cols:getComputedStyle(row).gridTemplateColumns,gap:getComputedStyle(row).gap,widths:r.map(x=>x.width),heights:r.map(x=>x.height),labels:[...row.children].map(x=>x.textContent)}}''')
 assert layout['labels']==['Edit','Delete'],layout
 assert abs(layout['widths'][0]-layout['widths'][1])<1,layout
 assert layout['gap']=='8px',layout
 assert layout['heights']==[39,39],layout
 page.locator('[data-tak-i667-edit-route]').click()
 page.locator('[data-tak-i572-delete-current]').click()
 result=page.evaluate('''() =>({starts:window.starts,deletes:window.deletes})''')
 assert result=={'starts':1,'deletes':1},result
 print('PASS i668 equal-width Edit | Delete, preserved edit/delete event handlers',layout)
 browser.close()
