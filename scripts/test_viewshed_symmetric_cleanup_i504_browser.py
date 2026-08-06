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
        page=browser.new_page(viewport={'width':1200,'height':900})
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content(html,wait_until='domcontentloaded',timeout=30000)
        page.wait_for_function("window.TakMapViewshedMaskV504 && typeof TakMapViewshedMaskV504.cleanup==='function'",timeout=15000)
        result=page.evaluate("""()=>{
          const api=TakMapViewshedMaskV504,w=81,h=81,c=40,at=(a,x,y)=>a[y*w+x];
          const fill=v=>new Uint8ClampedArray(w*h).fill(v);
          const disk=(a,v,r=7)=>{for(let y=0;y<h;y++)for(let x=0;x<w;x++)if(Math.hypot(x-c,y-c)<=r)a[y*w+x]=v};
          const redRay=fill(1);disk(redRay,1);for(let x=c+8;x<=c+31;x++)for(let y=c-1;y<=c+1;y++)redRay[y*w+x]=2;
          const redOut=api.cleanup(redRay,w,h);
          const greenRay=fill(2);disk(greenRay,1);for(let x=c+8;x<=c+31;x++)for(let y=c-1;y<=c+1;y++)greenRay[y*w+x]=1;
          const greenOut=api.cleanup(greenRay,w,h);
          const redWide=fill(1);disk(redWide,1);for(let x=c+8;x<=c+31;x++)for(let y=c-2;y<=c+2;y++)redWide[y*w+x]=2;
          const redWideOut=api.cleanup(redWide,w,h);
          const greenWide=fill(2);disk(greenWide,1);for(let x=c+8;x<=c+31;x++)for(let y=c-2;y<=c+2;y++)greenWide[y*w+x]=1;
          const greenWideOut=api.cleanup(greenWide,w,h);
          const redDiag=fill(1);disk(redDiag,1);for(let s=8;s<=27;s++){for(const o of [-1,0,1])redDiag[(c+s+o)*w+(c+s)]=2}
          const redDiagOut=api.cleanup(redDiag,w,h);
          const wedge=fill(1);disk(wedge,1);for(let y=0;y<h;y++)for(let x=0;x<w;x++){const dx=x-c,dy=y-c,r=Math.hypot(dx,dy),a=Math.atan2(dy,dx);if(r>8&&r<34&&Math.abs(a)<.22)wedge[y*w+x]=2}
          const wedgeOut=api.cleanup(wedge,w,h);
          return {
            version:api.version,
            redRay:{vals:[8,15,23,31].map(s=>at(redOut.classData,c+s,c)),changed:redOut.changed,toVisible:redOut.toVisible,toBlocked:redOut.toBlocked},
            greenRay:{vals:[8,15,23,31].map(s=>at(greenOut.classData,c+s,c)),changed:greenOut.changed,toVisible:greenOut.toVisible,toBlocked:greenOut.toBlocked},
            redWide:{center:[8,15,23,31].map(s=>at(redWideOut.classData,c+s,c)),edge:[8,15,23,31].map(s=>at(redWideOut.classData,c+s,c+2)),changed:redWideOut.changed},
            greenWide:{center:[8,15,23,31].map(s=>at(greenWideOut.classData,c+s,c)),edge:[8,15,23,31].map(s=>at(greenWideOut.classData,c+s,c+2)),changed:greenWideOut.changed},
            diagonal:{vals:[8,13,19,27].map(s=>at(redDiagOut.classData,c+s,c+s)),changed:redDiagOut.changed,toVisible:redDiagOut.toVisible},
            wedge:{center:[10,18,26,32].map(s=>at(wedgeOut.classData,c+s,c)),changed:wedgeOut.changed},
            near:{center:at(redOut.classData,c,c),near:at(redOut.classData,c+7,c),nearRadius:redOut.nearRadius,maxRayWidth:redOut.maxRayWidth}
          }
        }""")
        browser.close()
    assert result['version']=='i504',result
    assert result['redRay']['vals']==[1,1,1,1] and result['redRay']['toVisible']>=60 and result['redRay']['toBlocked']==0,result
    assert result['greenRay']['vals']==[2,2,2,2] and result['greenRay']['toBlocked']>=60 and result['greenRay']['toVisible']==0,result
    assert result['redWide']['center']==[2,2,2,2] and result['redWide']['edge']==[2,2,2,2] and result['redWide']['changed']==0,result
    assert result['greenWide']['center']==[1,1,1,1] and result['greenWide']['edge']==[1,1,1,1] and result['greenWide']['changed']==0,result
    assert result['diagonal']['vals']==[1,1,1,1] and result['diagonal']['toVisible']>0,result
    assert result['wedge']['center']==[2,2,2,2],result
    assert result['near']['center']==1 and result['near']['near']==1,result
    fatal=[e for e in errors if any(t in e.lower() for t in ('maximum call stack','too much recursion','out of memory'))]
    assert not fatal,fatal
    print('TAK Map i504 symmetric Viewshed red/green ray cleanup test passed')
    print(json.dumps(result,sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())
