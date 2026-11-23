"""i680: restore complete Local Data visibility on enriched-response recursion failure.

Tests operate on temporary files only. Do not migrate or modify real imports.
"""
import io
import json
import sys
import tempfile
import unittest
import warnings
from pathlib import Path
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
with warnings.catch_warnings():
    warnings.simplefilter('ignore', SyntaxWarning)
    import tak_dashboard as tak

class Response:
    def __init__(self, path='/api/tak-map/imported', command='GET'):
        self.path=path
        self.command=command
        self.wfile=io.BytesIO()
        self.status=None
        self.headers={}

    def _tak_map_refresh_headers(self, headers=None, code=200):
        return dict(headers or {})

    def send_response(self, code):
        self.status=code

    def send_header(self, key, val):
        self.headers[key]=val

    def end_headers(self):
        pass

    def payload(self):
        return json.loads(self.wfile.getvalue())


def catalog(n=5001):
    imports=[]
    for i in range(30):
        route=i<6
        coords=[[34.0+j/1000000, -112.0-j/1000000] for j in range(n)] if route else []
        feature={'kind':'route' if route else 'point','name':f'Feature {i}',
                 'object_id':f'local-{i:04d}-abcdef12345','coords':coords,
                 'lat':34.0,'lon':-112.0}
        imports.append({'id':f'import-{i:04d}','name':f'File {i}',
                        'features':[feature], 'counts':{'route':int(route),'point':int(not route)}})
    return {'imports':imports}

class UnserializableEnrichment:
    def __str__(self):
        raise RecursionError('maximum recursion depth exceeded')

class I680LocalDataRecovery(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix='tak-map-i680-')
        self.addCleanup(tmp.cleanup)
        self.path=Path(tmp.name)/'imports.json'
        self.path.write_text(json.dumps(catalog()))
        self.saved=self.path.read_bytes()
        patcher=patch.object(tak,'TAK_MAP_IMPORT_FILE',self.path)
        patcher.start(); self.addCleanup(patcher.stop)

    def test_read_only_recovery_full_30_and_5001_vertices(self):
        recovered=tak._i680_read_only_import_response()
        self.assertEqual(len(recovered['imports']),30)
        self.assertEqual(sum(f['kind']=='route' for imp in recovered['imports'] for f in imp['features']),6)
        self.assertEqual(sum(f['kind']=='point' for imp in recovered['imports'] for f in imp['features']),24)
        self.assertEqual(len(recovered['imports'][0]['features'][0]['coords']),5001)
        self.assertEqual(recovered['imports'][0]['features'][0]['coords'][-1], catalog(5001)['imports'][0]['features'][0]['coords'][-1])
        self.assertEqual(len(recovered['imports'][0]['features'][0]['route_revision_i659']),64)
        self.assertEqual(self.saved,self.path.read_bytes())

    def test_enriched_response_recursion_becomes_successful_read_only_response(self):
        # A failed enriched response must never mask the 30 good canonical records.
        response=Response()
        tak.Handler._send_json(response, {'ok':True,'imports':[], 'enrichment':UnserializableEnrichment()})
        self.assertEqual(response.status,200,response.wfile.getvalue()[:400])
        data=response.payload()
        self.assertTrue(data['ok'])
        self.assertEqual(len(data['imports']),30)
        self.assertEqual(response.headers.get('X-TAK-Map-Local-Data-Fallback'),'canonical-read-only')
        self.assertEqual(len(data['imports'][0]['features'][0]['coords']),5001)
        self.assertEqual(self.saved,self.path.read_bytes())

    def test_normal_response_keeps_complete_geometry_without_fallback(self):
        response=Response()
        tak.Handler._send_json(response, {'ok':True,'imports':catalog()['imports']})
        self.assertEqual(response.status,200)
        self.assertNotIn('X-TAK-Map-Local-Data-Fallback',response.headers)
        self.assertEqual(len(response.payload()['imports'][0]['features'][0]['coords']),5001)

    def test_invalid_canonical_data_is_not_silently_empty(self):
        self.path.write_text('{not valid')
        response=Response()
        tak.Handler._send_json(response, {'ok':True,'imports':[], 'enrichment':UnserializableEnrichment()})
        self.assertEqual(response.status,500)
        self.assertFalse(response.payload()['ok'])
        self.assertEqual(self.path.read_text(),'{not valid')

    def test_fallback_does_not_activate_on_non_import_endpoints(self):
        response=Response('/api/tak-map/other')
        tak.Handler._send_json(response, {'ok':True,'enrichment':UnserializableEnrichment()})
        self.assertEqual(response.status,500)
        self.assertNotIn('X-TAK-Map-Local-Data-Fallback',response.headers)

if __name__=='__main__': unittest.main()
