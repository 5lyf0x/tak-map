"""Offline release-gate tests for i682 Local Data integrity (no live TAK server)."""
import copy
import hashlib
import importlib.util
import io
import subprocess
import sys
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / 'tak_dashboard.py'
SPEC = importlib.util.spec_from_file_location('tak_dashboard_i682_staging', MODULE)
tak = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tak)


def body_file(filename, data, boundary='----takI682Boundary'):
    head = ('--' + boundary + '\r\n'
            + 'Content-Disposition: form-data; name="files"; filename="' + filename + '"\r\n'
            + 'Content-Type: application/geo+json\r\n\r\n').encode()
    raw = head + json.dumps(data, separators=(',', ':')).encode() + ('\r\n--' + boundary + '--\r\n').encode()
    return {'Content-Type': 'multipart/form-data; boundary=' + boundary,
            'Content-Length': str(len(raw))}, raw


class Handler:
    def __init__(self, filename, data):
        self.headers, raw = body_file(filename, data)
        self.rfile = io.BytesIO(raw)
        self.reply = None

    def _send_json(self, data, code=200, headers=None):
        # Ensure server response can be fully encoded (no circular/presentation data).
        assert isinstance(json.dumps(data), str)
        self.reply = (code, data)
        return self.reply


def upload(filename, data):
    h = Handler(filename, data)
    return tak.handle_tak_map_import_upload(h)


def point(n):
    return {'type':'Feature','geometry':{'type':'Point','coordinates':[-118.5 + n / 100000, 34.1]},
            'properties':{'name':f'Point {n}', 'source':'Integrity Test'}}


def geom_route(n=1305):
    return {'type':'Feature','geometry':{'type':'LineString',
            'coordinates':[[-118.0 + x/100000,34.5 + x/200000] for x in range(n)]},
            'properties':{'kind':'route','name':'LA to Peach Springs - Synthetic Full Route'}}


def shape():
    return {'type':'Feature','geometry':{'type':'Polygon','coordinates':[[
            [-113.0, 34.0],[-112.9,34.0],[-112.9,34.1],[-113.0,34.1],[-113.0,34.0]]]},
            'properties':{'kind':'shape','name':'Synthetic Polygon'}}


class LocalDataIntegrity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='tak-i682-local-')
        self.oldpath = tak.TAK_MAP_IMPORT_FILE
        tak.TAK_MAP_IMPORT_FILE = Path(self.tmp.name)/'imports.json'

    def tearDown(self):
        tak.TAK_MAP_IMPORT_FILE = self.oldpath
        self.tmp.cleanup()

    def snapshot(self):
        return tak.load_json_file(tak.TAK_MAP_IMPORT_FILE, None)['imports']

    def test_last_session_reload_preserves_full_geometry_and_ids(self):
        features=[geom_route(), point(1), shape()]
        code, resp=upload('session.geojson',{'type':'FeatureCollection','features':features})
        self.assertEqual((code,resp['ok']), (200,True))
        self.assertIsInstance(resp['imports'], list)
        self.assertEqual(len(resp['imports'][0]['features']), 3)
        a=self.snapshot()
        self.assertEqual(len(a),1)
        self.assertEqual(len(a[0]['features']),3)
        self.assertEqual(len(a[0]['features'][0]['coords']),1305)
        self.assertEqual(len(a[0]['features'][2]['coords'][0]),5)
        ids=[f['object_id'] for f in a[0]['features']]
        self.assertEqual(len(set(ids)),3)
        before=tak._i682_canonical_digest(a)
        # Simulated cold session: the same canonical file must be the source of truth.
        result=tak.tak_map_imported()
        b=result['imports']
        self.assertEqual([f['object_id'] for f in b[0]['features']],ids)
        self.assertEqual([len(f['coords']) for f in b[0]['features']],[1305,1,1])
        self.assertEqual(before,tak._i682_canonical_digest(self.snapshot()))

    def test_more_than_30_imports_not_evicted(self):
        for i in range(35):
            code,out=upload(f'upload-{i}.geojson',{'type':'FeatureCollection','features':[point(i)]})
            self.assertEqual(code,200, f'upload {i}: {out}')
        saved=self.snapshot()
        self.assertEqual(len(saved),35)
        self.assertEqual([x['name'] for x in saved],[f'upload-{i}.geojson' for i in range(35)])
        self.assertEqual(len({x['id'] for x in saved}),35)

    def test_more_than_1500_features_not_silently_truncated(self):
        all_features=[point(i) for i in range(1503)]
        code,out=upload('1503.geojson',{'type':'FeatureCollection','features':all_features})
        self.assertEqual(code,200,str(out)[:200])
        self.assertEqual(len(self.snapshot()[0]['features']),1503)
        self.assertEqual(len(tak.tak_map_imported()['imports'][0]['features']),1503)

    def test_delete_exact_id_preserves_unrelated_geometry(self):
        features=[geom_route(1407), point(5), shape()]
        self.assertEqual(upload('objects.geojson',{'type':'FeatureCollection','features':features})[0],200)
        before=self.snapshot()
        ids=[f['object_id'] for f in before[0]['features']]
        previous_route=copy.deepcopy(before[0]['features'][0])
        result=tak.tak_map_object_delete(['local:'+ids[1]])
        self.assertEqual(result['deleted_ids'],['local:'+ids[1]])
        self.assertNotIn('imports',result)
        after=self.snapshot()
        self.assertEqual([f['object_id'] for f in after[0]['features']],[ids[0],ids[2]])
        self.assertEqual(previous_route,after[0]['features'][0])
        self.assertEqual(len(after[0]['features'][0]['coords']),1407)

    def test_broken_file_does_not_become_empty_or_get_overwritten(self):
        path=tak.TAK_MAP_IMPORT_FILE
        path.write_text('{invalid json')
        old=path.read_bytes()
        with self.assertRaises(RuntimeError):
            tak.load_json_file(path,{'imports':[]})
        code,resp=upload('new.geojson',{'type':'FeatureCollection','features':[point(2)]})
        self.assertEqual(code,500)
        self.assertFalse(resp['ok'])
        self.assertEqual(path.read_bytes(),old)

    def test_restart_in_separate_python_process_keeps_same_objects(self):
        features=[geom_route(1999), point(51), shape()]
        self.assertEqual(upload('cold-start.geojson',{'type':'FeatureCollection','features':features})[0],200)
        expected=self.snapshot()
        expected_identity=[(row['object_id'],row['kind'],row['coords'])
                           for imp in expected for row in imp['features']]
        runner = """
import importlib.util,json,sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('cold_start_tak',sys.argv[1])
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
m.TAK_MAP_IMPORT_FILE=Path(sys.argv[2])
print(json.dumps([{'id':f['object_id'],'kind':f['kind'],'coords':f['coords']}
    for imp in m.tak_map_imported()['imports'] if imp.get('id') != 'webform-live'
    for f in imp['features']]))
"""
        result=subprocess.run([sys.executable,'-c',runner,str(MODULE),str(tak.TAK_MAP_IMPORT_FILE)],
                              capture_output=True,text=True,timeout=45,check=True)
        actual=json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual([(x['id'],x['kind'],x['coords']) for x in actual],expected_identity)
        self.assertEqual(expected,self.snapshot())

    def test_install_upgrade_does_not_purge_local_data(self):
        installer=(ROOT/'install.sh').read_text()
        self.assertIn('DATA_DIR="/var/lib/tak-map"',installer)
        self.assertIn('chown -R "$USER_NAME:$USER_NAME" "$DATA_DIR"',installer)
        self.assertNotIn('rm -rf "$DATA_DIR/tak_map_imports"',installer)
        self.assertNotIn('rm -f "$DATA_DIR/tak_map_imports/imports.json"',installer)
        self.assertNotIn('rm -rf /var/lib/tak-map',installer)

    def test_invalid_saved_catalog_returns_api_503_not_empty_success(self):
        tak.TAK_MAP_IMPORT_FILE.write_text('{broken existing data')
        class MockGet:
            path='/api/tak-map/imported'
            def _tak_map_auth_ok(self): return True
            def _send_json(self,data,status=200,headers=None): return status,data
        status,payload=tak.Handler.do_GET(MockGet())
        self.assertEqual(status,503)
        self.assertIs(payload['ok'],False)
        self.assertNotIn('imports',payload)
        self.assertEqual(tak.TAK_MAP_IMPORT_FILE.read_text(),'{broken existing data')

    def test_missing_file_after_initialization_is_not_empty_catalog(self):
        self.assertEqual(upload('point.geojson',{'type':'FeatureCollection','features':[point(1)]})[0],200)
        self.assertTrue(tak._i682_marker_path().is_file())
        tak.TAK_MAP_IMPORT_FILE.unlink()
        with self.assertRaises(FileNotFoundError):
            tak.load_json_file(tak.TAK_MAP_IMPORT_FILE,{'imports':[]})


if __name__=='__main__':
    unittest.main(verbosity=2)
