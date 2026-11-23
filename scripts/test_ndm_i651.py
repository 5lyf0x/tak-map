#!/usr/bin/env python3
"""i651 B0-B3 negative tests: no live network or service mutation."""
import hashlib,io,json,os,sys,tarfile,tempfile,unittest,zipfile,zlib,struct,sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ndm_packages_i651 import Catalog,NDMError,inspect_zip,sha256_file
from ndm_valhalla_i651 import _decode_polyline6,route,prepare_graph
from ndm_ctl_i651 import select as select_graph
from unittest.mock import patch


def make_routing(path,bad=False):
    manifest={'format':'takrig.valhalla.region.v1','name':'Utah','region_id':'ut','bounds':[-114,37,-109,42],
              'valhalla_version':'3.6.3','routing_coverage':{'index':'routing_coverage/index.json','nonempty_tile_count':1}}
    cfg={'mjolnir':{'tile_dir':'/data/old','tile_extract':'/data/old.tar','admin':'/data/valhalla/admin.sqlite'},
         'httpd':{'service':{'listen':'tcp://*:8002'}}}
    tar_io=io.BytesIO()
    with tarfile.open(fileobj=tar_io,mode='w') as tar:
        payload=b'valhalla-routing-fixture'
        ti=tarfile.TarInfo('2/000/751/952.gph');ti.size=len(payload)
        tar.addfile(ti,io.BytesIO(payload))
        if bad:
            t=tarfile.TarInfo('2/000/a.gph');t.type=tarfile.SYMTYPE;t.linkname='/etc/shadow';tar.addfile(t)
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,allowZip64=True) as z:
        z.writestr('manifest.json',json.dumps(manifest))
        z.writestr('valhalla.json',json.dumps(cfg))
        z.writestr('valhalla_tiles.tar',tar_io.getvalue())
        z.writestr('routing_coverage/index.json',json.dumps({'tiles':{}}))
        z.writestr('routing_coverage/11/375/760.geojson.gz',b'x')


def make_terrain(path):
    with tempfile.TemporaryDirectory() as d:
        db=Path(d)/'terrain.sqlite'
        con=sqlite3.connect(db)
        con.executescript('CREATE TABLE metadata (name TEXT PRIMARY KEY, value TEXT NOT NULL);\n'
                          'CREATE TABLE tiles (tile_id TEXT PRIMARY KEY,west REAL,south REAL,east REAL,north REAL,rows INTEGER,cols INTEGER,min_elev_m INTEGER,max_elev_m INTEGER,encoding TEXT,data BLOB);\n'
                          'CREATE TABLE tile_overviews (tile_id TEXT,resolution_m INTEGER,sample_spacing_arcseconds REAL,west REAL,south REAL,east REAL,north REAL,rows INTEGER,cols INTEGER,min_elev_m INTEGER,max_elev_m INTEGER,encoding TEXT,data BLOB,PRIMARY KEY(tile_id,resolution_m));')
        con.execute("INSERT INTO metadata VALUES ('schema','takrig.terrain.sqlite.v1')")
        blob=zlib.compress(struct.pack('<4h',100,101,102,103))
        con.execute("INSERT INTO tiles VALUES('a',-114,37,-113,38,2,2,100,103,'int16le+zlib',?)",(blob,))
        con.commit();con.close()
        meta={'format':'takrig.terrain.region.v1','database_schema':'takrig.terrain.sqlite.v1',
              'state_code':'UT','bounds':[-114,37,-113,38],'tile_count':1,'nominal_resolution_m':30}
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
            z.writestr('manifest.json',json.dumps(meta))
            z.write(db,'terrain.sqlite')


class NDMTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.dir=Path(self.tmp.name)
        self.nav=self.dir/'ut-nav.zip';self.dem=self.dir/'ut-dem.zip'
        make_routing(self.nav);make_terrain(self.dem)
        self.catalog=Catalog(self.dir/'catalog',external_roots=[self.dir])

    def test_routing_fixture(self):
        info=inspect_zip(self.nav)
        self.assertEqual(info['graph_tiles'],1)
    def test_terrain_fixture(self):
        self.assertEqual(inspect_zip(self.dem)['tiles'],1)
    def test_bad_archive(self):
        bad=self.dir/'bad.zip';make_routing(bad,True)
        with self.assertRaises(NDMError):inspect_zip(bad)
    def test_traversal(self):
        with zipfile.ZipFile(self.dir/'bad2.zip','w') as z:
            z.writestr('../etc/passwd',b'x')
        with self.assertRaises(NDMError):inspect_zip(self.dir/'bad2.zip')
    def test_no_system_paths_in_catalog(self):
        token=self.catalog.discover()[0]['discovery_id']
        entry,duplicate=self.catalog.register_existing(token)
        self.assertFalse(duplicate)
        self.assertNotIn('zip_path',str(entry))
        self.assertTrue(self.catalog.listing()[0]['available'])
        self.assertEqual(len(self.catalog.listing()),1)
    def test_external_removal_marked_unavailable(self):
        found=self.catalog.discover()[0]
        self.catalog.register_existing(found['discovery_id'])
        (self.dir/found['name']).unlink()
        self.assertFalse(self.catalog.listing()[0]['available'])
    def test_reject_forged_discovery(self):
        with self.assertRaises(NDMError):self.catalog.register_existing('f'*64)
    def test_duplicate_registration(self):
        token=self.catalog.discover()[0]['discovery_id']
        self.catalog.register_existing(token)
        _,dup=self.catalog.register_existing(token)
        self.assertTrue(dup)
    def test_import_stream_and_preservation(self):
        with open(self.nav,'rb') as fp:
            entry,dupe=self.catalog.import_stream(fp,self.nav.stat().st_size)
        self.assertFalse(dupe)
        self.assertTrue((self.catalog.root/'imports'/entry['dataset_id']/'valhalla_tiles.tar').exists())
        self.catalog.unregister(entry['dataset_id'])
        self.assertTrue((self.catalog.root/'imports'/entry['dataset_id']/'source.zip').exists())
    def test_import_stream_truncated(self):
        with self.assertRaises(NDMError):self.catalog.import_stream(io.BytesIO(b'xyz'),1000)
        self.assertEqual(len(self.catalog.listing()),0)
        self.assertFalse(list((self.catalog.root/'staging').glob('*.zip')))
    def test_unlisted_file_rejected(self):
        with self.assertRaises(NDMError):self.catalog.register_existing(str(self.nav))
    def test_activate_by_prepare_does_not_enable(self):
        with open(self.nav,'rb') as f:entry,_=self.catalog.import_stream(f,self.nav.stat().st_size)
        result=prepare_graph(self.catalog,entry['dataset_id'])
        self.assertFalse(result['router_enabled'])
        cfg=json.loads((self.catalog.root/'prepared'/(entry['dataset_id']+'.json')).read_text())
        self.assertEqual(cfg['httpd']['service']['listen'],'tcp://127.0.0.1:18882')
        self.assertNotIn('admin',cfg['mjolnir'])
        self.assertNotIn('elevation',cfg.get('additional_data',{}))
        self.assertEqual(cfg['loki']['service']['proxy'],'ipc:///tmp/takmap-valhalla-loki-i651') if 'loki' in cfg and 'proxy' in cfg['loki'].get('service',{}) else None
        self.assertTrue(Path(cfg['mjolnir']['tile_extract']).is_file())
    def test_operator_selection_confirmation_and_no_start(self):
        with open(self.nav,'rb') as f:entry,_=self.catalog.import_stream(f,self.nav.stat().st_size)
        with self.assertRaises(NDMError):select_graph(self.catalog,entry['dataset_id'],'')
        with patch('ndm_ctl_i651._version_ok',return_value=True):
            result=select_graph(self.catalog,entry['dataset_id'],'I-UNDERSTAND-LIVE-TEST')
        self.assertFalse(result['router_enabled'])
        self.assertTrue((self.catalog.root/'active'/'valhalla.json').is_file())
        self.assertTrue(self.catalog.detail(entry['dataset_id'])['active'])
        with self.assertRaises(NDMError):self.catalog.unregister(entry['dataset_id'])

    def test_route_validation(self):
        with self.assertRaises(NDMError):route([{'lat':0,'lon':0}],'roads')
        with self.assertRaises(NDMError):route([{'lat':0,'lon':0},{'lat':0,'lon':200}],'roads')
    def test_polyline_decoder(self):
        self.assertEqual(_decode_polyline6('??'),[[0.0,0.0]])
        with self.assertRaises(NDMError):_decode_polyline6('!')
    def test_upstream_error_not_fake_straight_line(self):
        with patch('ndm_valhalla_i651.urllib.request.urlopen',side_effect=OSError('refused')):
            with self.assertRaisesRegex(NDMError,'unavailable'):
                route([{'lat':40,'lon':-111},{'lat':40.01,'lon':-111.01}],'roads')


if __name__=='__main__':unittest.main(verbosity=2)
