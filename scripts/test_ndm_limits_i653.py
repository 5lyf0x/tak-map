#!/usr/bin/env python3
"""i653 source-only tests: 4 GiB browser uploads, quota-free existing files.

All fixtures are synthetic; large-file test uses a sparse ZIP and patches only
hashing to avoid reading the sparse 5 GiB test preamble.
"""
import io
import json
import os
import shutil
import sys
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import ndm_packages_i651 as ndm

GB=1024**3


def write_nav_zip(path,fp=None,extras=0):
    manifest={
        'format':'takrig.valhalla.region.v1','name':'California','region_id':'ca',
        'bounds':[-125,32,-114,42], 'valhalla_version':'3.6.3',
        'routing_coverage':{'index':'routing_coverage/index.json','nonempty_tile_count':1}
    }
    t=io.BytesIO()
    with tarfile.open(fileobj=t,mode='w') as tar:
        data=b'fake-graph-contents'
        info=tarfile.TarInfo('2/000/751/952.gph');info.size=len(data)
        tar.addfile(info,io.BytesIO(data))
    target=fp if fp is not None else path
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,allowZip64=True) as z:
        z.writestr('manifest.json',json.dumps(manifest))
        z.writestr('valhalla.json',json.dumps({'mjolnir':{}}))
        z.writestr('valhalla_tiles.tar',t.getvalue())
        z.writestr('routing_coverage/index.json','{}')
        z.writestr('routing_coverage/11/375/760.geojson.gz','dummy')
        for i in range(extras):z.writestr(f'extra/{i}.txt','x')


class LimitsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='tak-map-i653-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.nav=self.root/'nav.zip'
        write_nav_zip(self.nav)

    def test_default_browser_upload_cap_is_4096_mib(self):
        self.assertEqual(ndm.MAX_ZIP_BYTES,4*GB)
        self.assertGreater(ndm.MAX_FILES,5000)
        self.assertGreater(ndm.MAX_UNCOMPRESSED,4*GB)

    def test_browser_upload_above_four_gib_rejected_before_read(self):
        catalog=ndm.Catalog(self.root/'catalog',external_roots=[self.root])
        for length in (4*GB+1,5*GB):
            with self.assertRaises(ndm.NDMError) as err:
                catalog.import_stream(io.BytesIO(),length)
            self.assertEqual(err.exception.code,'TOO_LARGE')
        self.assertFalse((self.root/'catalog'/'staging').exists())

    def test_browser_upload_at_cap_is_not_rejected_by_size_policy(self):
        catalog=ndm.Catalog(self.root/'catalog',external_roots=[self.root])
        # Simulates a full-size valid upload without writing 4 GiB: no space
        # preflight must report NO_SPACE, not TOO_LARGE.
        with patch('ndm_packages_i651.shutil.disk_usage',return_value=shutil._ntuple_diskusage(1,1,0)):
            with self.assertRaises(ndm.NDMError) as err:
                catalog.import_stream(io.BytesIO(),4*GB)
        self.assertEqual(err.exception.code,'NO_SPACE')

    def test_existing_zip_larger_than_four_gib_registers_without_copy(self):
        sparse=self.root/'takrig-routing-ca-valhalla-3.6.3.zip'
        with sparse.open('wb') as fp:
            fp.seek(5*GB)
            write_nav_zip(None,fp=fp)
        self.assertGreater(sparse.stat().st_size,5*GB)
        info=ndm.inspect_zip(sparse)
        self.assertEqual(info['type'],'routing')
        catalog=ndm.Catalog(self.root/'catalog',external_roots=[self.root])
        discovered={x['name']:x['discovery_id'] for x in catalog.discover()}
        self.assertIn(sparse.name,discovered)
        with patch('ndm_packages_i651.sha256_file',return_value='a'*64):
            entry,dup=catalog.register_existing(discovered[sparse.name])
        self.assertFalse(dup)
        self.assertEqual(entry['owner'],'ndm-external')
        self.assertEqual(entry['zip_size_bytes'],sparse.stat().st_size)
        self.assertFalse((catalog.root/'imports').exists(),'existing registration must not copy the ZIP')
        self.assertTrue(sparse.is_file())

    def test_more_than_old_5000_archive_entries_is_valid(self):
        large_count=self.root/'many-files.zip'
        write_nav_zip(large_count,extras=5050)
        info=ndm.inspect_zip(large_count)
        self.assertGreater(info['files'],5000)

    def test_missing_zip_has_not_found_message_not_quota(self):
        with self.assertRaises(ndm.NDMError) as err:ndm.inspect_zip(self.root/'absent.zip')
        self.assertEqual(err.exception.code,'NOT_FOUND')
        self.assertNotIn('quota',str(err.exception).lower())

    def test_upload_import_small_fixture_still_works(self):
        catalog=ndm.Catalog(self.root/'catalog',external_roots=[self.root])
        with self.nav.open('rb') as stream:
            entry,duplicate=catalog.import_stream(stream,self.nav.stat().st_size)
        self.assertFalse(duplicate)
        self.assertTrue((catalog.root/'imports'/entry['dataset_id']/'source.zip').is_file())
        self.assertEqual(entry['type'],'routing')

    def test_ndm_nginx_upload_is_4gib_but_other_locations_are_400m(self):
        for p in ('nginx/tak-map-https-9444.conf','nginx/tak-map-https-9444.conf.example'):
            text=(ROOT/p).read_text()
            self.assertIn('client_max_body_size 400M;',text)
            section=text.split('location = /api/tak-map/ndm/import {',1)[1].split('}',1)[0]
            self.assertIn('client_max_body_size 4096M;',section)
            self.assertIn('proxy_request_buffering off;',section)
            self.assertIn('proxy_set_header Host $http_host;',section)

    def test_modal_reads_server_cap_and_no_fixed_timeout(self):
        text=(ROOT/'assets/tak-map-ndm-data-i652.js').read_text()
        self.assertIn('max_upload_bytes',text)
        self.assertIn('maxUploadBytes',text)
        self.assertIn('xhr.timeout=0;',text)
        self.assertNotIn('1536*1024*1024',text)
        server=(ROOT/'tak_dashboard.py').read_text()
        self.assertIn("'existing_file_size_limit':None",server)
        self.assertIn("'max_upload_bytes':_I651_MAX_UPLOAD_BYTES",server)


if __name__=='__main__':unittest.main(verbosity=2)
