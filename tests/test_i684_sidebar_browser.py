"""i684 sidebar style, toggle, ordering. Uses real i684 CSS and order script with stable DOM fixtures."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
CSS=(ROOT/'assets/tak-map-sidebar-uniform-i684.css').read_text()
ORDER=(ROOT/'assets/tak-map-sidebar-order-i684.js').read_text()
HTML='''<!doctype html><html><head><meta charset="utf-8"><style>
:root{--panel:#101923}*{box-sizing:border-box}body{margin:0;background:#080f15;color:#eee;font-family:Manrope,system-ui,sans-serif}
#sidebar{width:375px;padding:10px;display:flex;flex-direction:column;gap:8px}
.panel{background:#101923;border:1px solid #33414b;border-radius:13px;min-height:50px}
.panel>h2{margin:0;padding:14px 10px;display:flex;align-items:center;justify-content:space-between;font-size:13px}
#takVeilCardI665{padding:0;overflow:hidden;background:#0b171f}#takVeilCardI665 .tv-head{display:flex;align-items:center;gap:8px;min-height:50px;padding:10px 11px;background:#0d1c25}
#takVeilCardI665 .tv-head strong{font-size:12px}#takVeilCardI665 .tv-chip{margin-left:auto}#takVeilCardI665 .tv-switch{width:38px;height:20px;background:#233a43;border-radius:30px}
#takVeilCardI665 .tv-chevron{background:none;border:0;color:orange;padding:5px;font-size:16px}
#tokenMeshCardI660{background:#0a151b}#tokenMeshCardI660 .ms-header{margin:0;display:flex;align-items:center;gap:7px;padding:10px;background:#0d1c25;min-height:50px}#tokenMeshCardI660 .ms-header-right{margin-left:auto;display:flex;align-items:center;gap:7px}#tokenMeshCardI660 .ms-switch{width:38px;height:20px;background:#233a43;border-radius:30px}#tokenMeshCardI660 .ms-collapse{width:24px;height:26px;border:0}
</style></head><body><aside id="sidebar">
<div class="panel" id="local"><h2>LOCAL DATA <span class="chip">29 ITEMS</span></h2></div>
<div class="panel" id="offline"><h2>OFFLINE MAPS</h2></div>
<div class="panel" id="satelliteTrackingPanelV409"><h2>SATELLITE TRACKING <span class="chip">0 VISIBLE</span></h2></div>
<div class="panel" id="takVeilCardI665"><div class="tv-head"><strong>XTAK VEIL</strong><span class="tv-chip">DISABLED</span><label class="tv-switch" id="veilSwitch"></label><button class="tv-chevron">▾</button></div></div>
<div class="panel" id="tokenMeshCardI660"><h2 class="ms-header"><span class="ms-title">MESH SYNC</span><span class="ms-header-right"><span class="ms-chip">NOT ENROLLED</span><button class="ms-switch" id="meshSwitch" role="switch" aria-checked="true"></button><button class="ms-collapse">▾</button></span></h2></div>
</aside></body></html>'''
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 try:
  for width in (1280,390):
   page=browser.new_page(viewport={'width':width,'height':800})
   page.set_content(HTML)
   page.add_style_tag(content=CSS)
   page.add_script_tag(content=ORDER)
   page.wait_for_timeout(80)
   data=page.evaluate('''() => {
      let v=document.getElementById('veilSwitch').getBoundingClientRect(),m=document.getElementById('meshSwitch').getBoundingClientRect();
      let g=sel=>getComputedStyle(document.querySelector(sel));
      return {difference:Math.abs(v.right-m.right),order:[...document.querySelectorAll('#sidebar>.panel')].map(x=>x.id),
        backgrounds:['#local','#takVeilCardI665','#tokenMeshCardI660'].map(x=>g(x).backgroundColor),
        chips:['#local .chip','#takVeilCardI665 .tv-chip','#tokenMeshCardI660 .ms-chip'].map(x=>({size:g(x).fontSize,height:g(x).height,padding:g(x).padding})),
        titles:['#local h2','#takVeilCardI665 strong','#tokenMeshCardI660 .ms-title'].map(x=>({size:g(x).fontSize,weight:g(x).fontWeight,family:g(x).fontFamily}))};
   }''')
   assert data['order'].index('satelliteTrackingPanelV409')+1==data['order'].index('offline'),data
   assert len(set(data['backgrounds']))==1,data
   assert len(set((c['size'],c['height'],c['padding']) for c in data['chips']))==1,data
   assert len(set((t['size'],t['weight'],t['family']) for t in data['titles']))==1,data
   assert data['difference']<=2, data
   print('PASS sidebar uniformity width',width,'VEIL↔Mesh toggle right edge drift',data['difference'])
   page.close()
 finally:browser.close()
