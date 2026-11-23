"""i690 Chromium interaction/DOM and layout checks for the integrated status strip."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
CSS=(ROOT/'assets/tak-map-status-strip-i690.css').read_text()
JS=(ROOT/'assets/tak-map-status-strip-i690.js').read_text()
HTML='''<!DOCTYPE html><html><head><style>
html,body{margin:0;background:#05090c;color:#e7f0f5}#topbar{position:fixed;top:0;left:0;right:0;height:58px;background:#03060a}
#sidebar{position:fixed;left:0;top:86px;width:396px;height:calc(100vh - 86px);background:#111e25;transition:transform .2s}
#sidebar.collapsed{transform:translateX(-396px)}#map{position:fixed;left:396px;right:0;top:86px;bottom:0;background:#284750}
#sidebar.collapsed~#map{left:0}
</style></head><body><div id="topbar">TAK MAP</div>
<div id="mapStatusBanner" class="map-status-banner"><span id="bannerEudsItem"><span id="bannerEudsDot"></span><b id="bannerEuds">98 Connected</b></span><span id="bannerNonTakItem">Old Sensors</span><span id="bannerTakItem"><b id="bannerTak">Offline</b></span><span id="bannerInternetItem"><span id="bannerInternetDot" class="good"></span><b id="bannerInternet">Connected</b></span><span id="bannerAdsbItem">ADS-B old</span><span id="bannerDownloadsItem"><span id="bannerDownloadsDot"></span><b id="bannerDownloads">1 Active</b></span></div>
<div id="statusDropdown"></div><aside id="sidebar"></aside><div id="map"></div></body></html>'''
def test():
  with sync_playwright() as p:
    b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    try:
      for width in (1440,760,390):
        page=b.new_page(viewport={'width':width,'height':780});errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content(HTML)
        page.evaluate("""()=>{window.fetch=async url=>{const j=String(url).includes('euds')?{ok:true,euds:[{uid:'abc',callsign:'Alpha'},{uid:'abc',callsign:'Alpha duplicate'},{uid:'xyz',callsign:'Zulu'}]}:{ok:true,lan:{state:'Available'},tak:{configured:false,enabled:false,state:'Unknown'}};return {ok:true,headers:new Headers({'content-type':'application/json'}),json:async()=>j}}}""")
        page.add_style_tag(content=CSS)
        page.add_script_tag(content=JS)
        page.wait_for_function('window.TakMapStatusStripI690?.state.euds?.length===2',timeout=7000)
        assert page.locator('#statusItemsI690 > *').count()==6
        assert page.locator('#statusItemsI690').locator('.i690-label').all_text_contents()==['EUDs:','VEIL:','Downloads:','LAN:','Internet:','TAK Server:']
        assert page.locator('#valueI690euds').inner_text()=='2'
        assert page.locator('#statusI690Tak').is_hidden()
        pos=page.locator('#mapStatusBanner').bounding_box()
        assert round(pos['y'])==58 and round(pos['height'])==28,(width,pos)
        expected=396 if width>900 else 0
        assert round(pos['x'])==expected,(width,pos)
        panel=page.locator('#statusDropdownI690')
        page.locator('#statusI690Veil').click()
        page.evaluate('''()=>document.dispatchEvent(new CustomEvent('takmap:veil-status-i690',{detail:{ok:true,config:{enabled:true},nodes:[{nodeId:'node1',name:'VEIL Node 1',state:'receiving',apiSubscribed:true,apiState:'connected',apiLastSync:Date.now()/1000,objects:5},{nodeId:'node2',name:'VEIL Node 2',state:'waiting',apiSubscribed:true,apiState:'reconnecting',objects:0}]}}))''')
        assert page.locator('#valueI690veil').inner_text()=='1'
        assert panel.is_visible()
        assert page.locator('#i690PanelRows .i690-row').count()==2
        assert page.locator('#i690PanelSummary').inner_text()=='1 receiving · 2 subscribed'
        row_before=page.locator('#i690PanelRows .i690-row').first.evaluate('(e)=>{window.__nodeRef=e;return e.dataset.key}')
        page.locator('#i690PanelRows .i690-row').first.focus()
        page.evaluate('''()=>document.dispatchEvent(new CustomEvent('takmap:veil-status-i690',{detail:{ok:true,config:{enabled:true},nodes:[{nodeId:'node1',name:'VEIL Node 1',state:'receiving',apiSubscribed:true,apiState:'connected',apiLastSync:Date.now()/1000,objects:7},{nodeId:'node2',name:'VEIL Node 2',state:'waiting',apiSubscribed:true,apiState:'reconnecting',objects:0}]}}))''')
        assert page.evaluate('document.querySelector("#i690PanelRows .i690-row")===window.__nodeRef')
        assert page.evaluate('document.activeElement===window.__nodeRef')
        assert panel.is_visible()
        page.keyboard.press('Escape');assert not panel.is_visible()
        page.locator('#statusI690Euds').click()
        assert panel.is_visible() and panel.locator('.i690-row').count()==2
        assert panel.locator('.i690-name').all_text_contents()==['Alpha duplicate','Zulu']
        # Legacy marker-derived changes must never overwrite the authoritative EUD count.
        page.evaluate("document.getElementById('bannerEuds').textContent='61 Connected'")
        assert page.locator('#valueI690euds').inner_text()=='2'
        page.evaluate("document.getElementById('sidebar').classList.add('collapsed')")
        assert round(page.locator('#mapStatusBanner').bounding_box()['x'])==0
        assert not errors,errors
        print('PASS i690 Chromium',width,'order, geometry, EUD authority, VEIL keyed rows, focus, Escape, collapsed sidebar')
        page.close()
    finally:b.close()
if __name__=='__main__':test()
