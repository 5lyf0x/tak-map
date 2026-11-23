from pathlib import Path
from playwright.sync_api import sync_playwright
import json,re
ROOT=Path(__file__).resolve().parents[1]
stack=(ROOT/'assets/tak-map-basemap-stack-i673.js').read_text()
core=(ROOT/'assets/tak-map-core-i553.js').read_text()
part=core.split('function renderBasemaps(){',1)[1].split('function reliefSource(){',1)[0]
core_render='function renderBasemaps(){'+part
builtin=[{'id':'esri_imagery','label':'ESRI World Imagery','group':'Imagery','url':'/tiles/imagery/{z}/{x}/{y}.png'},
 {'id':'esri_topo','label':'ESRI World Topographic','group':'Topo / Terrain','url':'/tiles/topo/{z}/{x}/{y}.png'}]
imports=[{'id':x,'label':name,'group':'Custom XML','importedBasemap':True,'serverPersisted':True,
         'url':'/api/tak-map/custom-basemap-tile/'+x+'/{z}/{x}/{y}.png','minZoom':0,'maxZoom':20}
 for x,name in [('google_road','Google Road'),('google_terrain','Google Terrain'),('blm_land','BLM Land Ownership'),('google_roads2','+ Google Roads')]]
page_html='''<!doctype html><html><head></head><body>
<select id="basemapSelect"></select>
<script>
const config={basemaps: %s,default_basemap:'esri_imagery'};
let activeBasemap='esri_imagery'; let baseLayer=null;
const tileStats={created:0,removed:0,added:0};
window.map={_layers:new Set(),_pane:null,getPane(){return this._pane},createPane(){this._pane={style:{}};return this._pane},hasLayer(lyr){return this._layers.has(lyr)},removeLayer(lyr){this._layers.delete(lyr);tileStats.removed++}};
window.L={tileLayer(url,options){tileStats.created++;return {url,options,container:{style:{}},_takMode:null,setOpacity(n){this.opacity=n;return this},setZIndex(n){this.z=n;return this},getContainer(){return this.container},addTo(map){map._layers.add(this);tileStats.added++;return this}}}};
function visibleText(){return true} function esc(s){return String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;')}
function basemapDisplayLabel(b){return b.label+' (max '+(b.maxZoom??19)+'x)'} function renderCustomBasemapStatus(){}
%s
window.setCatalog=rows=>{config.basemaps=rows;renderBasemaps()};
</script><script>%s</script></body></html>'''%(json.dumps(builtin),core_render,stack)
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 p=browser.new_page()
 errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
 p.set_content(page_html,wait_until='domcontentloaded')
 p.evaluate('window.TakMapBaseStackI673.boot()')
 before=p.evaluate('({order:[...TakMapBaseStackI673.state.order],enabled:[...TakMapBaseStackI673.state.enabled],created:tileStats.created})')
 assert before['order']==['esri_imagery','esri_topo'],before
 assert before['enabled']==['esri_imagery'],before
 p.evaluate('(rows)=>setCatalog(rows)',builtin+imports)
 after=p.evaluate('({order:[...TakMapBaseStackI673.state.order],enabled:[...TakMapBaseStackI673.state.enabled],created:tileStats.created})')
 assert after['order']==[x['id'] for x in builtin+imports],after
 assert after['enabled']==['esri_imagery'],after
 assert after['created']==before['created'], 'Import changed the active basemap images'
 assert p.locator('.tak-base-item-i673').count()==6
 assert p.locator('[data-base-i673="google_road"]').count()==1
 assert p.locator('select#basemapSelect option').count()==6
 p.locator('[data-base-check-i673="google_road"]').check()
 p.locator('[data-base-opacity-i673="google_road"]').fill('37')
 assert p.evaluate('TakMapBaseStackI673.state.opacity.google_road')==37
 # Even if fresh catalog arrives again, keep active overlay opacity and position.
 p.evaluate('(rows)=>setCatalog(rows)',builtin+imports)
 assert p.evaluate('TakMapBaseStackI673.state.opacity.google_road')==37
 assert p.evaluate('TakMapBaseStackI673.state.enabled.has("google_road")')
 # Remove another custom map: no other layer should reset.
 p.evaluate('(rows)=>setCatalog(rows)',builtin+[x for x in imports if x['id']!='blm_land'])
 assert p.locator('[data-base-i673="blm_land"]').count()==0
 assert p.locator('.tak-base-item-i673').count()==5
 assert p.evaluate('TakMapBaseStackI673.state.opacity.google_road')==37
 # Remove the selected imported layer, retaining the built-in imagery base.
 p.evaluate('(rows)=>setCatalog(rows)',builtin+[x for x in imports if x['id'] not in ('blm_land','google_road')])
 assert p.evaluate('TakMapBaseStackI673.state.enabled.has("google_road")'), "Keep enabled state when catalog temporarily omits ID"
 assert p.evaluate('TakMapBaseStackI673.state.enabled.has("esri_imagery")')
 assert p.evaluate('!TakMapBaseStackI673.state.layers.has("google_road")')
 # Reload a stable set without importing duplicates; restored source keeps its settings.
 p.evaluate('(rows)=>setCatalog(rows)',builtin+imports)
 assert p.locator('.tak-base-item-i673').count()==6
 # Removing all entries should leave normal built-in basemaps untouched.
 p.evaluate('(rows)=>setCatalog(rows)',builtin)
 assert p.locator('.tak-base-item-i673').count()==2
 assert p.evaluate('TakMapBaseStackI673.state.enabled.has("esri_imagery")')
 assert errors==[],errors
 print(json.dumps({'status':'PASS','initial':before,'after_import':after,'scenarios':['four XML imports','no automatic activation/refetch','toggle and opacity persist','catalog refresh','single deletion','remove selected layer','reimport with no duplicates','bulk removal preservation'],'errors':errors},indent=2))
 browser.close()
