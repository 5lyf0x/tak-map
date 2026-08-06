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
        page.wait_for_function("window.TakMapViewshedMaskV502 && typeof TakMapViewshedMaskV502.cleanup==='function'",timeout=15000)
        result=page.evaluate("""()=>{
          const api=TakMapViewshedMaskV502;
          const make=(w,h,fill=1)=>new Uint8ClampedArray(w*h).fill(fill);
          const at=(a,w,x,y)=>a[y*w+x];
          const isolated=make(9,9);isolated[4*9+4]=2;const iso=api.cleanup(isolated,9,9);
          const ray=make(11,11);for(let y=3;y<=7;y++)ray[y*11+5]=2;const rayOut=api.cleanup(ray,11,11);
          const hole=make(11,11);for(let y=4;y<=5;y++)for(let x=4;x<=5;x++)hole[y*11+x]=2;const holeOut=api.cleanup(hole,11,11);
          const ridge=make(13,13);for(let y=3;y<=9;y++)for(let x=5;x<=9;x++)ridge[y*13+x]=2;const ridgeOut=api.cleanup(ridge,13,13);
          const outside=make(13,13);for(let x=0;x<=8;x++)outside[6*13+x]=2;const outsideOut=api.cleanup(outside,13,13);
          return {
            version:api.version,
            isolated:{value:at(iso.classData,9,4,4),changed:iso.changed},
            ray:{values:[3,4,5,6,7].map(y=>at(rayOut.classData,11,5,y)),changed:rayOut.changed},
            hole:{values:[at(holeOut.classData,11,4,4),at(holeOut.classData,11,5,4),at(holeOut.classData,11,4,5),at(holeOut.classData,11,5,5)],changed:holeOut.changed},
            ridge:{center:at(ridgeOut.classData,13,7,6),edge:at(ridgeOut.classData,13,5,3),changed:ridgeOut.changed},
            outside:{values:[0,2,4,6,8].map(x=>at(outsideOut.classData,13,x,6)),changed:outsideOut.changed}
          }
        }""")
        browser.close()
    assert result['version']=='i502', result
    assert result['isolated']['value']==1 and result['isolated']['changed']>=1, result
    assert result['ray']['values']==[1,1,1,1,1] and result['ray']['changed']>=5, result
    assert result['hole']['values']==[1,1,1,1] and result['hole']['changed']>=4, result
    assert result['ridge']['center']==2 and result['ridge']['edge']==2 and result['ridge']['changed']==0, result
    assert result['outside']['values']==[2,2,2,2,2] and result['outside']['changed']==0, result
    fatal=[e for e in errors if any(t in e.lower() for t in ('maximum call stack','too much recursion','out of memory'))]
    assert not fatal, fatal
    print('TAK Map i502 conservative Viewshed visibility-mask cleanup test passed')
    print(json.dumps(result,sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())
