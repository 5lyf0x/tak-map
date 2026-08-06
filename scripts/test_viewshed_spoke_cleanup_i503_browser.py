#!/usr/bin/env python3
from __future__ import annotations
import json, runpy, shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def main()->int:
    chromium=next((n for n in ('chromium','chromium-browser','google-chrome','google-chrome-stable') if shutil.which(n)),None)
    if not chromium:
        print('SKIP: Chromium unavailable'); return 0
    helper=runpy.run_path(str(ROOT/'scripts'/'test_full_page_responsiveness_v486.py'))
    html=helper['self_contained_html']()
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,executable_path=shutil.which(chromium),args=['--no-sandbox','--disable-gpu','--disable-dev-shm-usage'])
        page=browser.new_page(viewport={'width':1200,'height':800})
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content(html,wait_until='domcontentloaded',timeout=20000)
        page.wait_for_function("window.TakMapViewshedMaskV503 && typeof TakMapViewshedMaskV503.cleanup==='function'",timeout=15000)
        result=page.evaluate("""()=>{
          const api=TakMapViewshedMaskV503;
          const w=51,h=51,c=25,at=(a,x,y)=>a[y*w+x];
          const blocked=()=>new Uint8ClampedArray(w*h).fill(2);
          function centerDisk(a,r=5){for(let y=0;y<h;y++)for(let x=0;x<w;x++)if(Math.hypot(x-c,y-c)<=r)a[y*w+x]=1}

          const spoke=blocked();centerDisk(spoke);for(let x=c+6;x<=c+20;x++)spoke[c*w+x]=1;
          const spokeOut=api.cleanup(spoke,w,h);

          const twoCellSpoke=blocked();centerDisk(twoCellSpoke);for(let x=c+6;x<=c+20;x++){twoCellSpoke[c*w+x]=1;twoCellSpoke[(c+1)*w+x]=1}
          const twoCellOut=api.cleanup(twoCellSpoke,w,h);

          const corridor=blocked();centerDisk(corridor);for(let x=c+6;x<=c+20;x++){corridor[(c-1)*w+x]=1;corridor[c*w+x]=1;corridor[(c+1)*w+x]=1}
          const corridorOut=api.cleanup(corridor,w,h);

          const lobe=blocked();centerDisk(lobe);for(let x=c+6;x<=c+20;x++)for(let y=c-2;y<=c+2;y++)lobe[y*w+x]=1;
          const lobeOut=api.cleanup(lobe,w,h);

          const shortOpening=blocked();centerDisk(shortOpening);for(let x=c+6;x<=c+9;x++)shortOpening[c*w+x]=1;
          const shortOut=api.cleanup(shortOpening,w,h);

          const diagonal=blocked();centerDisk(diagonal);for(let s=6;s<=17;s++)diagonal[(c+s)*w+(c+s)]=1;
          const diagonalOut=api.cleanup(diagonal,w,h);

          return {
            version:api.version,
            spoke:{values:[6,10,15,20].map(s=>at(spokeOut.classData,c+s,c)),changed:spokeOut.changed,removed:spokeOut.componentsRemoved,candidates:spokeOut.candidates},
            twoCellSpoke:{row0:[6,10,15,20].map(s=>at(twoCellOut.classData,c+s,c)),row1:[6,10,15,20].map(s=>at(twoCellOut.classData,c+s,c+1)),changed:twoCellOut.changed,removed:twoCellOut.componentsRemoved},
            corridor:{rowMinus:[6,10,15,20].map(s=>at(corridorOut.classData,c+s,c-1)),row0:[6,10,15,20].map(s=>at(corridorOut.classData,c+s,c)),row1:[6,10,15,20].map(s=>at(corridorOut.classData,c+s,c+1)),changed:corridorOut.changed},
            lobe:{center:[6,10,15,20].map(s=>at(lobeOut.classData,c+s,c)),edge:[6,10,15,20].map(s=>at(lobeOut.classData,c+s,c+2)),changed:lobeOut.changed},
            shortOpening:{values:[6,7,8,9].map(s=>at(shortOut.classData,c+s,c)),changed:shortOut.changed},
            diagonal:{values:[6,9,12,15,17].map(s=>at(diagonalOut.classData,c+s,c+s)),changed:diagonalOut.changed,removed:diagonalOut.componentsRemoved},
            near:{center:at(spokeOut.classData,c,c),nearEdge:at(spokeOut.classData,c+5,c),nearRadius:spokeOut.nearRadius,minRadialSpan:spokeOut.minRadialSpan}
          }
        }""")
        browser.close()
    assert result['version']=='i503',result
    assert result['spoke']['values']==[2,2,2,2] and result['spoke']['changed']>=15 and result['spoke']['removed']>=1,result
    assert result['twoCellSpoke']['row0']==[2,2,2,2] and result['twoCellSpoke']['row1']==[2,2,2,2] and result['twoCellSpoke']['changed']>=30 and result['twoCellSpoke']['removed']>=1,result
    assert result['corridor']['rowMinus']==[1,1,1,1] and result['corridor']['row0']==[1,1,1,1] and result['corridor']['row1']==[1,1,1,1] and result['corridor']['changed']==0,result
    assert result['lobe']['center']==[1,1,1,1] and result['lobe']['edge']==[1,1,1,1] and result['lobe']['changed']==0,result
    assert result['shortOpening']['values']==[1,1,1,1] and result['shortOpening']['changed']==0,result
    assert result['diagonal']['values']==[2,2,2,2,2] and result['diagonal']['changed']>=12 and result['diagonal']['removed']>=1,result
    assert result['near']['center']==1 and result['near']['nearEdge']==1,result
    fatal=[e for e in errors if any(t in e.lower() for t in ('maximum call stack','too much recursion','out of memory'))]
    assert not fatal,fatal
    print('TAK Map i503 observer-centered Viewshed spoke cleanup test passed')
    print(json.dumps(result,sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())
