#!/usr/bin/env python3
"""i651 pinned-wheel installer tests using controlled native-executable fixtures."""
import hashlib,importlib.util,io,json,os,sys,tempfile,unittest,zipfile,stat
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('valhalla_install_i651',ROOT/'scripts/install-valhalla-i651.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.name='pyvalhalla-3.6.3-cp312-abi3-manylinux_2_28_x86_64.whl'
        b=io.BytesIO()
        with zipfile.ZipFile(b,'w') as z:
            z.writestr('valhalla/bin/valhalla_service',b'#!/bin/sh\necho Valhalla 3.6.3\n')
            z.writestr('valhalla.libs/libtest.so',b'fake-library')
        self.wheel=b.getvalue()
        self.sha=hashlib.sha256(self.wheel).hexdigest()
        self.meta={'urls':[{'filename':self.name,'url':'https://files.pythonhosted.org/packages/demo/'+self.name,'digests':{'sha256':self.sha}}]}
    def test_version_and_architecture(self):
        with patch.object(m.platform,'machine',return_value='x86_64'),patch.object(m.platform,'libc_ver',return_value=('glibc','2.36')):
            self.assertEqual(m.architecture(),'x86_64')
        with patch.object(m.platform,'machine',return_value='armv7l'):
            with self.assertRaises(RuntimeError):m.architecture()
    def test_legacy_glibc_rejected(self):
        with patch.object(m.platform,'machine',return_value='x86_64'),patch.object(m.platform,'libc_ver',return_value=('glibc','2.27')):
            with self.assertRaises(RuntimeError):m.architecture()
    def test_source_pinning(self):
        with patch.dict(m.SHA,{'x86_64':self.sha}):
            self.assertEqual(m.source_info('x86_64',self.meta)[1],self.name)
        with self.assertRaises(RuntimeError):m.source_info('x86_64',self.meta)
    def test_unsafe_url_rejected(self):
        self.meta['urls'][0]['url']='http://example.com/'+self.name
        with patch.dict(m.SHA,{'x86_64':self.sha}):
            with self.assertRaises(RuntimeError):m.source_info('x86_64',self.meta)
    def test_successful_native_install(self):
        def open_stub(url,timeout=None):
            if url==m.PYPI:return io.BytesIO(json.dumps(self.meta).encode())
            return io.BytesIO(self.wheel)
        with patch.dict(m.SHA,{'x86_64':self.sha}),patch.object(m.platform,'machine',return_value='x86_64'),patch.object(m.platform,'libc_ver',return_value=('glibc','2.36')),patch.object(m.urllib.request,'urlopen',side_effect=open_stub):
            dest=self.root/'vendor'/'valhalla-3.6.3'
            m.install(dest)
            self.assertTrue((dest/'valhalla/bin/valhalla_service').is_file())
            self.assertTrue((dest/'valhalla.libs/libtest.so').exists())
            m.install(dest)
    def test_tampered_payload_rejected_safely(self):
        def open_stub(url,timeout=None):
            if url==m.PYPI:return io.BytesIO(json.dumps(self.meta).encode())
            return io.BytesIO(self.wheel+b'tampered')
        with patch.dict(m.SHA,{'x86_64':self.sha}),patch.object(m.platform,'machine',return_value='x86_64'),patch.object(m.platform,'libc_ver',return_value=('glibc','2.36')),patch.object(m.urllib.request,'urlopen',side_effect=open_stub):
            dest=self.root/'vendor'/'valhalla-3.6.3'
            with self.assertRaises(RuntimeError):m.install(dest)
            self.assertFalse(dest.exists())

if __name__=='__main__':unittest.main(verbosity=2)
