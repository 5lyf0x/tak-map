#!/usr/bin/env python3
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[1]
JS=(ROOT/'assets'/'tak-map-i636.js').read_text()

def main():
    chromium=next((n for n in ('chromium','chromium-browser','google-chrome','google-chrome-stable') if shutil.which(n)),None)
    if not chromium:
        print('SKIP: Chromium unavailable')
        return 0
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=shutil.which(chromium),args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
        page=browser.new_page(); errors=[]; page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content('<!doctype html><html><head></head><body><div id="dataSyncRows"></div></body></html>',wait_until='domcontentloaded')
        page.evaluate("""()=>{
          const store=()=>{const m=new Map();return {getItem:k=>m.get(k)||null,setItem:(k,v)=>m.set(k,String(v)),removeItem:k=>m.delete(k)}};
          Object.defineProperty(window,'localStorage',{configurable:true,value:store()});Object.defineProperty(window,'sessionStorage',{configurable:true,value:store()});
          class X{open(){}send(){this.status=200;this.responseText='{"states":{}}'}};window.XMLHttpRequest=X;window.fetch=()=>Promise.resolve({ok:true,json:()=>Promise.resolve({ok:true})});
          window.__layers=[];
          function mk(kind,pts,opt){const x={kind,pts,opt,popup:null,bindPopup(v){this.popup=v;return this},addTo(g){g.layers.push(this);window.__layers.push(this);return this}};return x}
          window.L={polygon:(p,o)=>mk('polygon',p,o),polyline:(p,o)=>mk('polyline',p,o)};
          window.dataSyncCategory=o=>'Other / Unknown';
          window.collectCoordPairs=v=>{const out=[];(function walk(x){if(Array.isArray(x)&&x.length>=2&&typeof x[0]==='number'&&typeof x[1]==='number'){out.push(x);return}if(Array.isArray(x))x.forEach(walk)})(v);return out};
          window.shapeCoords=o=>o.coords||[];window.objectCenter=o=>[o.lat||0,o.lon||0];window.layerPopupForObject=()=>'<b>shape</b>';
          window.stabilizeLayerPopup=()=>{};window.takMapStampSelectionIdentityV478=()=>{};window.addSearchItem=()=>{};window.shapeAreaPopupRows=()=>'<b>Area</b>';
          window.addObjectLayer=(group,o)=>({base:true,o});
        }""")
        page.add_script_tag(content=JS); page.wait_for_timeout(800)
        result=page.evaluate("""()=>{
          const g1={layers:[]},g2={layers:[]};
          const rect={uid:'R',cot_type:'u-d-r',tak_shape_i636:true,shape_closed_i636:true,coords:[[34,-118],[34,-117.9],[34.1,-117.9],[34.1,-118]],lat:34.05,lon:-117.95,color:'#ffff00',fill_color:'#112233',fill_opacity:.25,weight:3,line_style:'dashed'};
          const free={uid:'F',cot_type:'u-d-f',tak_shape_i636:true,shape_closed_i636:false,coords:[[34,-118],[34.1,-117.9],[34.2,-118]],lat:34.1,lon:-117.97,color:'#abcdef',weight:2};
          const a=window.addObjectLayer(g1,rect,'datasync');const b=window.addObjectLayer(g2,free,'datasync');
          return {cat:window.dataSyncCategory(rect),a:a&&a.kind,aOpt:a&&a.opt,b:b&&b.kind,bOpt:b&&b.opt,areaFree:window.shapeAreaPopupRows(free),compat:window.__takMapShapeCompatI636};
        }""")
        assert result['cat']=='Shapes / Areas',result
        assert result['a']=='polygon' and result['b']=='polyline',result
        assert result['aOpt']['color']=='#ffff00' and result['aOpt']['fillColor']=='#112233' and result['aOpt']['dashArray']=='8,7',result
        assert result['areaFree']=='',result
        assert result['compat']['version']=='i636' and result['compat']['legacyRead'] is True,result
        assert not errors,errors
        browser.close()
    print('PASS i636 browser shape renderer closed/open/style contract')
    return 0

if __name__=='__main__': raise SystemExit(main())
