#!/usr/bin/env python3
"""Offline Map Packs i001 isolated on-disk regression: no host/service operations."""
import io, json, os, sqlite3, tempfile, hashlib, zipfile, sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))

with tempfile.TemporaryDirectory(prefix='takmap-i001-') as d:
    os.environ['TAK_DASHBOARD_DATA_DIR']=d
    import tak_dashboard as m
    base=Path(d)/'tak_map_offline';base.mkdir()
    m.TAK_MAP_OFFLINE_DIR=base
    m.TAK_MAP_OFFLINE_FILE=base/'offline_maps.json'
    m.TAK_MAP_OFFLINE_PACKAGE_DIR=base/'packages'
    mb=base/'original.mbtiles'
    with sqlite3.connect(mb) as c:
        c.execute('create table metadata(name text,value text)')
        c.execute('insert into metadata values(?,?)',('name','Original embedded name'))
        c.execute('insert into metadata values(?,?)',('format','png'))
        c.execute('create table tiles(zoom_level integer,tile_column integer,tile_row integer,tile_data blob)')
        c.execute('insert into tiles values (2,1,1,?)',(b'not-a-real-image-but-valid-tile-data',))
    start_sha=hashlib.sha256(mb.read_bytes()).hexdigest()
    maps=[]
    for i in range(86):
        maps.append(dict(id=f'map-{i:03d}',name=f'Map {i}',filename='original.mbtiles',path=str(mb),
                         tile_count=1,format='png',download_status='complete',created_by='download',
                         partial=False,resume_available=False,download_concurrency=4,
                         retry_manifest=['saved'],send_history=[{'send_id':f'history-{i}'}],
                         mission_publish_history=[{'mission':'existing'}],
                         eud_package_url='/api/old',eud_package_name='Original.sqlite',eud_package_path='old.zip',
                         eud_package_sha256='oldhash'))
    maps.append(dict(id='imported',name='Imported 10',filename='original.mbtiles',path=str(mb),tile_count=1,format='png',send_history=[{'keep':True}]))
    maps.append(dict(id='partial',name='Partial 5',filename='original.mbtiles',path=str(mb),created_by='download',download_status='partial',partial=True,resume_available=True,retry_manifest=['remaining']))
    maps.append(dict(id='queued',name='Queued 3',filename='original.mbtiles',path=str(mb),created_by='download',download_status='queued',partial=False,resume_available=False))
    m._save_offline_maps(maps)
    before=m._load_offline_maps()
    assert len(before)==89
    a,status=m.tak_map_offline_rename_i001('map-082','Survey 2')
    assert status==200 and a['ok']
    after=m._load_offline_maps()
    assert len(after)==89 and [v['id'] for v in after]==[v['id'] for v in before]
    old=next(x for x in before if x['id']=='map-082');new=next(x for x in after if x['id']=='map-082')
    changed={k for k in set(old)|set(new) if old.get(k)!=new.get(k)}
    assert changed=={'name','name_updated','eud_package_url','eud_package_name','eud_package_path','eud_package_sha256'},changed
    assert new['send_history']==old['send_history'] and new['retry_manifest']==old['retry_manifest']
    assert hashlib.sha256(mb.read_bytes()).hexdigest()==start_sha
    with sqlite3.connect(mb) as c:
        assert c.execute("select value from metadata where name='name'").fetchone()[0]=='Original embedded name'
    assert m._offline_basemap_entries()[82]['label']=='Offline · Survey 2'

    # Invalid or incomplete states do not modify the catalog.
    for mid,name,expected in [('not-found','Any',404),('partial','No',409),('queued','No',409),
                              ('map-001',' Bad\nname ',400),('map-001','bad/path',400),
                              ('map-001','bad\\path',400),('map-001','',400),
                              ('map-001','x'*121,400),('map-001','xx\u0085xx',400)]:
        result,code=m.tak_map_offline_rename_i001(mid,name)
        assert code==expected and not result['ok'],(mid,code,result)
    assert m.tak_map_offline_rename_i001('imported','Imported 2')[1]==200

    # Rebuilt outgoing package uses renamed display name without changing MBTiles.
    package=m.tak_map_offline_eud_package('map-082')
    assert package['ok'] and package['content_name']=='Survey 2.sqlite',package
    assert package['package_name']=='Survey 2.sqlite.zip'
    with zipfile.ZipFile(package['path']) as z:
        assert z.namelist()==['Survey 2.sqlite']
        assert hashlib.sha256(z.read('Survey 2.sqlite')).hexdigest()==start_sha
    assert hashlib.sha256(mb.read_bytes()).hexdigest()==start_sha

    # Concurrent catalog upserts cannot silently drop older or newly-added records.
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(lambda n: m._upsert_offline_map_record({'id':f'late-{n}','name':f'Late {n}','filename':'original.mbtiles','path':str(mb)}),range(12)))
    assert len(m._load_offline_maps())==101

    # Authenticated API contract at the actual Handler.do_POST dispatch.
    class FakeRequest:
        path='/api/tak-map/offline-rename-i001'
        def __init__(self,authorized):
            self.auth=authorized
            raw=json.dumps({'id':'imported','name':'Imported 3'}).encode()
            self.headers={'Content-Length':str(len(raw))}
            self.rfile=io.BytesIO(raw)
        def _tak_map_auth_ok(self):return self.auth
        def _require_tak_map_login(self):return ('login-required',401)
        def _send_json(self,data,status=200,headers=None):return data,status,headers
    assert m.Handler.do_POST(FakeRequest(False))==('login-required',401)
    j,code,headers=m.Handler.do_POST(FakeRequest(True))
    assert code==200 and j['ok'] and headers.get('Cache-Control')=='no-store'
    assert next(x for x in m._load_offline_maps() if x['id']=='imported')['name']=='Imported 3'

    config=m.tak_map_config()
    assert config['version']=='1.5.0-i004' and config['tak_map_iteration']=='i004'
    h=m.TAK_MAP_HTML
    assert '<span class="release-main">1.5.0</span>' in h
    assert '<span class="iteration-chip">i004</span>' in h
    assert "const RELEASE='1.5.0',ITERATION='i004',PACKAGE='1.5.0-i004'" in h
    assert "const iteration='i004',version='1.5.0'" in h
    assert "const iteration='i699',version='1.4.0'" not in h
    assert '1.4.0-i699' not in __import__('re').sub(r'v=1\.5\.0-i003', '', h)
    print('PASS: 101 records; imported/completed eligibility, validation, auth, renamed EUD, original MBTiles SHA, footer identity, concurrent saves')
