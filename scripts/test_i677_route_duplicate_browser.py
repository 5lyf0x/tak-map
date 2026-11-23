"""i677 regression: filename collisions never cause false failed route saves."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import ast,re
root=Path(__file__).resolve().parents[1]
text=(root/'scripts/test_i676_browser.py').read_text()
namespace={'__file__':str(root/'scripts/test_i676_browser.py')}
exec(text.split('with sync_playwright() as p:')[0],namespace)
editor=namespace['editor']; html=namespace['html']; modal=namespace['modal']; init_js=namespace['init_js']; seed=namespace['seed']
fetch_js=r'''
window.__savedImports=[{id:'old-200',name:'Demo Trail.geojson',features:[{kind:'route',coords:[[33,-118],[34,-117]],object_id:'old-route'}]}];
window.__uploadSeq=0;window.__truncateNew=false;window.__omitAdded=false;
window.fetch=async function(url,opts={}){
 const name=String(url);
 if(name.includes('/api/tak-map/ndm/status'))return {ok:true,json:async()=>({routing_enabled:true})};
 if(name.includes('/api/tak-map/imported'))return {ok:true,json:async()=>({ok:true,imports:window.__savedImports.map((i,idx)=>({...i,features:i.features.map(f=>({...f,coords:window.__truncateNew&&idx===window.__savedImports.length-1?f.coords.slice(0,3):f.coords}))}))})};
 if(name.includes('/api/tak-map/import')&&opts.method==='POST'){
   const file=opts.body.get('files'),data=JSON.parse(await file.text()),f=data.features[0];
   const imported={id:'fresh-'+(++window.__uploadSeq),name:file.name,features:[{kind:'route',properties:f.properties,coords:f.geometry.coordinates.map(p=>[p[1],p[0]]),object_id:'new-'+window.__uploadSeq}]};
   window.__savedImports.push(imported);
   return {ok:true,json:async()=>({ok:true,added:window.__omitAdded?[]:[imported],imports:window.__savedImports})};
 }
 throw Error('unexpected '+name);
};
'''
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1742,'height':864})
 page.set_content(html);page.evaluate(init_js);page.evaluate("(()=>{"+fetch_js+";return true})()");page.evaluate(modal);page.evaluate(editor)
 page.wait_for_timeout(350)
 assert seed(page)['ready']
 saved=page.evaluate('window.takRouteEditorI654.saveResolvedRoute({name:"Demo Trail"})')
 assert saved, 'new route with duplicate filename was rejected'
 assert page.evaluate('window.__savedImports.length')==2
 assert page.evaluate('window.__savedImports[1].features[0].coords.length')>=22
 assert seed(page)['ready']
 saved=page.evaluate('window.takRouteEditorI654.saveResolvedRoute({name:"Demo Trail"})')
 assert saved, 'second duplicate route was rejected'
 assert page.evaluate('window.__savedImports.length')==3
 assert page.evaluate('window.__savedImports[2].id')=='fresh-2'
 page.evaluate('window.__truncateNew=true');assert seed(page)['ready']
 saved=page.evaluate('window.takRouteEditorI654.saveResolvedRoute({name:"Demo Trail"})')
 assert saved is False, 'truncated newest route was incorrectly verified via older same-named full route'
 assert page.evaluate('window.v233RouteState.points.length')==13
 assert page.evaluate('window.__savedImports.length')==4
 page.evaluate('window.__truncateNew=false;window.__omitAdded=true')
 saved=page.evaluate('window.takRouteEditorI654.saveResolvedRoute({name:"Demo Trail"})')
 assert saved is False, 'missing server-created ID should fail closed'
 assert page.evaluate('window.v233RouteState.points.length')==13
 browser.close()
 print('PASS i677 duplicate route: same filename saved twice by unique IDs, truncated latest rejected, missing ID fail-closed, editor retained')
