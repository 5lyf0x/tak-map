#!/usr/bin/env python3
"""Deterministic offline i003 tile HTTP/auth/pool/row-scheme/resume regression.

All MBTiles fixtures are synthetic. No production throughput claims are made.
"""
import hashlib
import io
import json
import os
import sqlite3
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

root=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(root))
with tempfile.TemporaryDirectory(prefix='tak-map-i003-') as tmp:
    os.environ['TAK_DASHBOARD_DATA_DIR']=tmp
    import tak_dashboard as app
    base=Path(tmp)/'offline'
    base.mkdir()
    app.TAK_MAP_OFFLINE_DIR=base
    app.TAK_MAP_OFFLINE_FILE=base/'offline_maps.json'
    png=b'\x89PNG\r\n\x1a\n'
    tms=base/'north-tms.mbtiles'
    xyz=base/'north-xyz.mbtiles'
    partial=base/'partial.mbtiles'

    for fp,scheme in [(tms,'tms'),(xyz,'xyz'),(partial,'tms')]:
        with sqlite3.connect(fp) as c:
            c.execute('CREATE TABLE metadata (name TEXT,value TEXT)')
            c.executemany('INSERT INTO metadata VALUES (?,?)', [('name',fp.stem),('format','png'),('scheme',scheme)])
            c.execute('CREATE TABLE tiles(zoom_level INTEGER,tile_column INTEGER,tile_row INTEGER,tile_data BLOB)')
            c.execute('CREATE UNIQUE INDEX tile_index ON tiles(zoom_level,tile_column,tile_row)')
            if fp!=partial:
                # Both rows exist, so guessing TMS first misrenders the XYZ fixture.
                north=0 if scheme=='xyz' else 1
                south=1 if scheme=='xyz' else 0
                c.executemany('INSERT INTO tiles VALUES (?,?,?,?)',[(1,0,north,png+b'North'),(1,0,south,png+b'South')])
    orig={fp.name:hashlib.sha256(fp.read_bytes()).hexdigest() for fp in (tms,xyz,partial)}
    assert app._mbtiles_metadata(xyz)['tile_row_scheme']=='xyz'
    records=[
        dict(id='tms',name='Standard TMS',path=str(tms),format='png',min_zoom=1,max_zoom=1,
             tile_row_scheme='tms',created_by='download',download_status='complete',bounds='-180,0,0,85'),
        dict(id='xyz',name='Imported XYZ',path=str(xyz),format='png',min_zoom=1,max_zoom=1,
             tile_row_scheme='xyz',bounds='-180,0,0,85'),
        dict(id='partial',name='Incomplete',path=str(partial),format='png',min_zoom=1,max_zoom=1,
             tile_row_scheme='tms',created_by='download',download_status='partial',partial=True)
    ]
    app._save_offline_maps(records)
    assert app._mbtiles_tile_bytes('tms',1,0,0)[0]==png+b'North'
    assert app._mbtiles_tile_bytes('xyz',1,0,0)[0]==png+b'North'
    assert app._mbtiles_tile_bytes('xyz',1,0,1)[0]==png+b'South'
    assert app._mbtiles_tile_bytes('tms',1,0,1)[0]==png+b'South'
    assert app._mbtiles_tile_bytes('tms',2,0,0)[0] is None
    assert app._mbtiles_tile_bytes('missing',1,0,0)[0] is None
    assert app._mbtiles_tile_bytes('tms',23,0,0)[0] is None

    class FakeGet:
        command='GET'
        def __init__(self,path,auth=True):
            self.path=path;self.auth=auth;self.status=None;self.headers_out={};self.wfile=io.BytesIO()
        def _tak_map_auth_ok(self):return self.auth
        def _require_tak_map_login(self):return 'login-required'
        def send_response(self,status):self.status=status
        def send_header(self,k,v):self.headers_out[k]=v
        def end_headers(self):pass
    def req(mid,z=1,x=0,y=0,auth=True):
        r=FakeGet(f'/api/tak-map/offline-tile/{mid}/{z}/{x}/{y}.png',auth)
        val=app.Handler.do_GET(r)
        return r,val
    r,_=req('xyz'); assert r.status==200 and r.wfile.getvalue()==png+b'North'
    assert r.headers_out['Cache-Control'].startswith('private') and r.headers_out['Vary']=='Cookie'
    r,_=req('xyz',1,1,0);assert r.status==404 and r.headers_out['Cache-Control']=='private, no-store'
    r,_=req('tms',2,0,0);assert r.status==404 and r.headers_out['X-TAK-Offline-Tile-Status']=='zoom'
    r,_=req('xyz',auth=False);assert r.status is None and _=='login-required'
    r,_=req('partial');assert r.status==404 and r.headers_out['Cache-Control']=='private, no-store'
    # A resumed partial map immediately becomes visible and is never 404-cached.
    with sqlite3.connect(partial) as c:c.execute('INSERT INTO tiles VALUES (1,0,1,?)',(png+b'Added',))
    r,_=req('partial');assert r.status==200 and r.wfile.getvalue()==png+b'Added'
    assert r.headers_out['Cache-Control']=='private, no-store'

    # Imported XYZ vs TMS operator override only updates catalog metadata.
    class FakePost:
        path='/api/tak-map/offline-row-scheme-i003'
        def __init__(self,mid,scheme,auth=True):
            self.auth=auth
            body=json.dumps({'id':mid,'tile_row_scheme':scheme}).encode()
            self.headers={'Content-Length':str(len(body))};self.rfile=io.BytesIO(body)
        def _tak_map_auth_ok(self):return self.auth
        def _require_tak_map_login(self):return 'login-required'
        def _send_json(self,obj,status=200,headers=None):return obj,status,headers
    assert app.Handler.do_POST(FakePost('xyz','tms',auth=False))=='login-required'
    assert app.Handler.do_POST(FakePost('tms','xyz'))[1]==409
    assert app.Handler.do_POST(FakePost('xyz','bad'))[1]==400
    assert app.Handler.do_POST(FakePost('xyz','tms'))[1]==200
    assert app._mbtiles_tile_bytes('xyz',1,0,0)[0]==png+b'South'
    assert app.Handler.do_POST(FakePost('xyz','xyz'))[1]==200
    assert app._mbtiles_tile_bytes('xyz',1,0,0)[0]==png+b'North'
    rec=next(x for x in app._load_offline_maps() if x['id']=='xyz')
    assert rec['tile_row_scheme']=='xyz' and rec['name']=='Imported XYZ'

    # Concurrent HTTP requests hit a small hot connection pool, not one open
    # and full JSON parse per tile. 100+ actual handlers, not mock result bytes.
    app._I003_TILE_STORE.invalidate()
    def fetch(i):
        mid='xyz' if i%2 else 'tms'
        r,_=req(mid,1,0,i%2)
        return r.status,r.wfile.getvalue()
    with ThreadPoolExecutor(max_workers=10) as executor:
        results=list(executor.map(fetch,range(160)))
    assert all(code==200 for code,_ in results),[x for x in results if x[0]!=200][:4]
    counts=app._I003_TILE_STORE.diagnostic_summary()
    assert counts['requests']>=170
    assert counts['sqlite_opens']<30,counts
    assert counts['catalog_parses']<12,counts
    assert counts['connections_open']<=12,counts
    assert counts['pool_reuses']>100,counts
    # Deletion invalidates catalog and all prior connections; no stale tile.
    app._save_offline_maps([x for x in app._load_offline_maps() if x['id']!='xyz'])
    r,_=req('xyz');assert r.status==404
    assert app._I003_TILE_STORE.diagnostic_summary()['connections_open']==0
    for fp in (tms,xyz):assert hashlib.sha256(fp.read_bytes()).hexdigest()==orig[fp.name]

    # Layer catalog includes only available native zoom and a stable generation.
    entries=app._offline_basemap_entries()
    e=next(e for e in entries if e['id']=='offline_tms')
    assert e['maxNativeZoom']==1 and e['minNativeZoom']==1 and e['maxZoom']==22
    assert '?generation=' in e['url'] and e['bounds']=='-180,0,0,85'
    assert app.tak_map_config()['version']=='1.5.0-i004'
    assert 'i004</span>' in app.TAK_MAP_HTML
    assert "const RELEASE='1.5.0',ITERATION='i004',PACKAGE='1.5.0-i004'" in app.TAK_MAP_HTML
    assert "const iteration='i004',version='1.5.0'" in app.TAK_MAP_HTML
    print('PASS i003: 160 parallel HTTP requests, auth, row-scheme override, resume, tile hashes, metadata, footer')
    print('POOL DIAGNOSTICS (synthetic fixtures):',counts)
