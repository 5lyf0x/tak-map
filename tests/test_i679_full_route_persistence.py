"""i679: real Local Data import/API/disk and existing-route edit regression tests.

Isolated temp catalog; never reads or mutates actual server state.
"""
import io
import json
import math
import sys
import tempfile
import unittest
import warnings
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
with warnings.catch_warnings():
    warnings.simplefilter('ignore', SyntaxWarning)
    import tak_dashboard as tak


class FakeHttp:
    def __init__(self, path, body=b'', ctype=''):
        self.path=path
        self.rfile=io.BytesIO(body)
        self.wfile=io.BytesIO()
        self.headers={'Content-Type':ctype,'Content-Length':str(len(body))}
        self.status=None
        self.response_headers={}

    def _send_json(self, data, code=200, headers=None):
        return tak.Handler._send_json(self,data,code,headers)

    def _tak_map_refresh_headers(self,headers=None,code=200):
        return dict(headers or {})

    def send_response(self,code):
        self.status=code

    def send_header(self,key,val):
        self.response_headers[key]=val

    def end_headers(self):
        pass

    def json(self):
        return json.loads(self.wfile.getvalue())


def make_route(n,name='Full trail'):
    # Realistic 10-waypoint metadata and distinct coordinates; no floats outside
    # the valid geographic range, including the 50,000-vertex stress case.
    points=[[round(-114.0+i*0.00003,7),round(34.5+0.009*math.sin(i/65),7)]
            for i in range(n)]
    props={'name':name,'kind':'route','route_control_point_count':10,
           'route_resolved_vertex_count':n,'takmap_route_editor':'resolved-line-v2'}
    for i in range(10):
        p=points[min(n-1,round(i*(n-1)/9))]
        props['route_cp_'+str(i)]=f'{p[1]:.7f},{p[0]:.7f},roads'
    return {'type':'Feature','geometry':{'type':'LineString','coordinates':points},
            'properties':props}


def multipart(name,payload):
    boundary='tak-i679-boundary'
    body=(f'--{boundary}\r\nContent-Disposition: form-data; name="files"; filename="{name}"\r\n'
          'Content-Type: application/geo+json\r\n\r\n').encode()+payload+f'\r\n--{boundary}--\r\n'.encode()
    return body,'multipart/form-data; boundary='+boundary


class FullRouteSaveTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='tak-route-i679-')
        self.addCleanup(self.temp.cleanup)
        self.dir=Path(self.temp.name)
        self.catalog=self.dir/'tak_map_imports'/'imports.json'
        patches=[
            patch.object(tak,'DATA_DIR',self.dir),
            patch.object(tak,'TAK_MAP_IMPORT_FILE',self.catalog),
            patch.object(tak,'TAK_MAP_IMPORT_DIR',self.catalog.parent),
            patch.object(tak,'_webform_features_from_ots',return_value=[]),
            patch.object(tak,'_load_popup_edits',return_value={}),
        ]
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)

    def post_route(self,n,name='Full Trail.geojson'):
        route=make_route(n)
        data=json.dumps({'type':'FeatureCollection','features':[route]},separators=(',',':')).encode()
        body,ctype=multipart(name,data)
        fake=FakeHttp('/api/tak-map/import',body,ctype)
        tak.handle_tak_map_import_upload(fake)
        self.assertEqual(fake.status,200,fake.wfile.getvalue()[:300])
        result=fake.json()
        self.assertTrue(result['ok'])
        rid=result['added'][0]['id']
        self.assertEqual(result['added'][0]['features'][0]['coords'][-1],
                         [route['geometry']['coordinates'][-1][1],route['geometry']['coordinates'][-1][0]])
        self.assertEqual(len(result['added'][0]['features'][0]['coords']),n)
        return rid,route

    def test_import_disk_get_long_routes(self):
        for vertices in (1001,5000,20000,50001):
            with self.subTest(vertices=vertices):
                self.catalog.unlink(missing_ok=True)
                # Each subcase intentionally simulates a brand-new catalog.
                # i682 tracks previously initialized catalogs, so reset the
                # test-only marker as well to avoid simulating data loss.
                tak._i682_marker_path().unlink(missing_ok=True)
                route_id,route=self.post_route(vertices)
                content=self.catalog.read_text()
                self.assertNotIn('...truncated...',content)
                disk=json.loads(content)
                self.assertEqual(disk['imports'][0]['id'],route_id)
                saved=disk['imports'][0]['features'][0]['coords']
                self.assertEqual(len(saved),vertices)
                self.assertEqual(saved[0][::-1],route['geometry']['coordinates'][0])
                self.assertEqual(saved[-1][::-1],route['geometry']['coordinates'][-1])
                response=FakeHttp('/api/tak-map/imported')
                response._send_json(tak.tak_map_imported())
                self.assertEqual(response.status,200)
                api=response.json()
                self.assertEqual(api['imports'][0]['id'],route_id)
                self.assertEqual(len(api['imports'][0]['features'][0]['coords']),vertices)
                self.assertNotIn('...truncated...',response.wfile.getvalue().decode())

    def test_long_route_edit_and_reopen(self):
        rid,_=self.post_route(21010)
        existing=tak.tak_map_imported()['imports'][0]['features'][0]
        oid=existing['object_id']
        rev=existing['route_revision_i659']
        updated=make_route(32005,name='Edited Full Trail')
        result,status=tak._i659_update_route({'import_id':rid,'object_id':oid,
            'expected_revision':rev,'feature':updated})
        self.assertEqual(status,200,str(result)[:350])
        disk=json.loads(self.catalog.read_text())
        self.assertEqual(len(disk['imports'][0]['features'][0]['coords']),32005)
        reread=tak.tak_map_imported()['imports'][0]['features'][0]
        self.assertEqual(len(reread['coords']),32005)
        self.assertEqual(reread['coords'][-1][::-1],updated['geometry']['coordinates'][-1])
        self.assertNotEqual(reread['route_revision_i659'],rev)

    def test_legacy_corruption_is_not_silently_deleted(self):
        old={'id':'legacy-bad','name':'old.geojson','features':[{
            'kind':'route','name':'Older damaged route','coords':[[34,-112]]*1000+['...truncated...']}]}
        tak.atomic_write_json(self.catalog,{'imports':[old]})
        rid,_=self.post_route(1100,'new.geojson')
        contents=json.loads(self.catalog.read_text())['imports']
        self.assertEqual(len(contents),2)
        self.assertEqual(contents[0]['features'][0]['coords'][-1],'...truncated...')
        self.assertEqual(contents[1]['id'],rid)
        self.assertEqual(len(contents[1]['features'][0]['coords']),1100)

    def test_circular_data_refuses_write_without_corrupting_existing_file(self):
        tak.atomic_write_json(self.catalog,{'imports':[{'id':'safe'}]})
        before=self.catalog.read_bytes()
        loop=[]
        loop.append(loop)
        with self.assertRaises(ValueError):
            tak.atomic_write_json(self.catalog,{'imports':loop})
        self.assertEqual(before,self.catalog.read_bytes())

    def test_no_more_truncation_on_api(self):
        payload={'ok':True,'coordinates':[[34.1,-111.3]]*20000}
        fake=FakeHttp('/api/tak-map/imported')
        fake._send_json(payload)
        self.assertEqual(fake.status,200)
        self.assertEqual(len(fake.json()['coordinates']),20000)
        self.assertEqual(fake.response_headers['Content-Length'],str(len(fake.wfile.getvalue())))


if __name__=='__main__':
    unittest.main()
