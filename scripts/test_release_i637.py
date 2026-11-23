#!/usr/bin/env python3
from pathlib import Path
import re, sys
ROOT=Path(__file__).resolve().parents[1]
py=(ROOT/'tak_dashboard.py').read_text(encoding='utf-8')
js=(ROOT/'takmap.js').read_text(encoding='utf-8')

def check(text,name):
    assert '.popup-edit{margin:8px 10px 10px;border:0;border-radius:0;background:transparent;overflow:visible;width:auto;max-width:100%;}' in text, name+' stable base popup CSS missing'
    assert '.popup-edit summary{cursor:pointer;display:inline-flex;width:auto;min-width:0;max-width:max-content;' in text, name+' stable Edit summary CSS missing'
    assert 'setInterval(function(){setVersion();pruneLocalSelection();fixEditControlWidths()},700)' not in text, name+' v324 periodic popup fixer still active'
    assert 'setTimeout(fixEditControlWidths,0)' not in text, name+' rerender popup fixer still active'
    assert 'patchSaveDialogDrag();fixPopupEdit(d)}catch(_){}},1000)' not in text, name+' v348 periodic popup fixer still active'
    assert 'if(n&&n.nodeType===1)fixPopupEdit(n)' not in text, name+' v348 MutationObserver popup fixer still active'
check(py,'tak_dashboard.py')
check(js,'takmap.js')
assert "_I637_PACKAGE_VERSION='1.4.0-i637'" in py
assert "'shape_edit_resize_rotation':'planned-next'" in py
assert (ROOT/'VERSION').read_text().strip()=='1.4.0-i637'
print('PASS i637 stable Shape popup Edit control regression')
