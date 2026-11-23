#!/usr/bin/env python3
"""Static + tiny isolated runtime regression for i697 (no installed service required)."""
from pathlib import Path
import re
from types import SimpleNamespace
root = Path(__file__).resolve().parents[1]
source = (root/'tak_dashboard.py').read_text()
js = (root/'assets/tak-map-radar-history-i696.js').read_text()
css = (root/'assets/tak-map-radar-history-i696.css').read_text()
assert (root/'VERSION').read_text().strip() == '1.4.0-i697'
assert "TAK_MAP_ITERATION = 'i697'" in source
assert "'version': '1.4.0-i697'" in source
assert '?v=1.4.0-i697' not in (root/'assets/tak-map-radar-history-i696.js').read_text()  # asset not hardcoded to release
assert "1.4.0-i697" in source
m=re.search(r"^TAK_MAP_OFFLINE_DOWNLOAD_MAX_TILES=(int\(os\.environ\.get\(.+?\)\))$",source,re.M)
assert m, 'offline cap expression not found'
assert eval(m.group(1),{'os':SimpleNamespace(environ={})}) == 250000
assert eval(m.group(1),{'os':SimpleNamespace(environ={'TAK_DASH_OFFLINE_DOWNLOAD_MAX_TILES':'50000'})}) == 50000
assert eval(m.group(1),{'os':SimpleNamespace(environ={'TAK_DASH_OFFLINE_DOWNLOAD_MAX_TILES':'300000'})}) == 300000
assert source.count('if total > TAK_MAP_OFFLINE_DOWNLOAD_MAX_TILES')>=1
assert 'total<=TAK_MAP_OFFLINE_DOWNLOAD_MAX_TILES' in source
assert "history-tile-i696" in source and "history-i696" in source
assert "--tak-soft-pill-pct" in js and "--tak-soft-pill-pct" in css
assert 'timeline.style.setProperty' in js
assert 'tak-soft-pill-i678' in js
assert 'aria-valuetext' in js
print('PASS: i697 version, 250000 default / config overrides, estimate/resume, historical API, Soft Pill')
