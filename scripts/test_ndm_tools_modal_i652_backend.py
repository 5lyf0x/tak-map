#!/usr/bin/env python3
"""i652 Tools-card NDM UI: verify real page injection and runtime asset route."""
import contextlib
import io
import os
import runpy
import tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='takmap-i652-ndm-ui-') as temp:
    os.environ['TAK_DASHBOARD_DATA_DIR']=temp
    with contextlib.redirect_stdout(io.StringIO()):
        ns=runpy.run_path(str(ROOT/'tak_dashboard.py'),run_name='takmap_i652_ui_test')
    page=ns['TAK_MAP_HTML']
    assert page.count('id="takMapNDMDataBtnI652"')==1
    assert page.count('takMapNDMDataLoaderI652')==1
    tools=page.index('<div class="panel"><h2>Tools</h2>')
    add=page.index('id="localElevAddBtn"',tools)
    ndm=page.index('id="takMapNDMDataBtnI652"',tools)
    export=page.index('onclick="exportAllData()"',tools)
    assert tools < add < ndm < export, 'NDM button must appear beside Add Elevation Data in Tools card'
    assert '/assets/runtime/tak-map-ndm-data-i652.js' in page
    assert 'openTakMapNDMData()' in page
    assert ns['INDEX_HTML']==page
    assert ns['TAK_MAP_ITERATION']=='i659','Release must use i654 identity'
    h=object.__new__(ns['Handler'])
    h.path='/assets/runtime/tak-map-ndm-data-i652.js?v=1.4.0-i659'
    h.command='GET'
    h.wfile=io.BytesIO()
    statuses=[];headers={}
    h.send_response=lambda code:statuses.append(code)
    h.send_header=lambda name,value:headers.__setitem__(name.lower(),value)
    h.end_headers=lambda:None
    h.do_GET()
    assert statuses==[200]
    assert headers['content-type'].startswith('application/javascript')
    assert headers['cache-control'].startswith('no-store')
    assert b'window, document' in h.wfile.getvalue()
    assert b'openTakMapNDMData' in h.wfile.getvalue()
    h.command='HEAD';h.wfile=io.BytesIO();h.do_GET()
    assert h.wfile.getvalue()==b''
    installer=(ROOT/'install.sh').read_text()
    assert 'install -m 0644 assets/tak-map-ndm-data-i652.js' in installer
    assert 'tak-map-ndm-data-i652.js?install-check=i659' in installer
print('PASS: effective Tools-card placement, i651 preserved identity, JS asset GET/HEAD, installer deployment and runtime checks')
