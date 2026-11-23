"""Isolated graph-selection and rollback regression tests for TAK Map i675."""
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tak_map_graph_switch_i675 import GraphSwitcher
from ndm_packages_i651 import Catalog, NDMError

A = 'a' * 64
B = 'b' * 64

class SwitchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='takmap-i675-switch-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.catalog = Catalog(root=self.root, external_roots=[])
        for ident in (A, B):
            (self.root / (ident+'.zip')).write_bytes(b'fake local registered archive')
        self.catalog._save({'schema':1,'datasets':{
            ident:{'dataset_id':ident,'type':'routing','valhalla_version':'3.6.3',
                   'zip_path':str(self.root/(ident+'.zip')),
                   'owner':'import','region':label,'region_id':label.lower().replace(' ','-'),
                   'active':ident == A}
            for ident,label in ((A,'Arizona'),(B,'US West'))}})
        active = self.root/'active'
        active.mkdir()
        (active/'valhalla.json').write_text('{"mjolnir":{"tile_extract":"/previous.tar"}}')
        (active/'dataset-id').write_text(A+'\n')
        self.restarts = []

    def _prepare(self,catalog,ident):
        graph = self.root/'graphs'/ident/'valhalla_tiles.tar'
        graph.parent.mkdir(parents=True,exist_ok=True)
        graph.write_bytes(b'fixture graph')
        prepared = self.root/'prepared'
        prepared.mkdir(exist_ok=True)
        (prepared/(ident+'.json')).write_text(json.dumps({'mjolnir':{'tile_extract':str(graph)}}))

    def _restart(self):
        self.restarts.append((self.root/'active'/'dataset-id').read_text().strip() if (self.root/'active'/'dataset-id').is_file() else '')

    def _wait(self, switcher):
        for _ in range(300):
            if switcher.job['status'] not in ('preparing','restarting'):
                return
            time.sleep(.01)
        self.fail('Switch worker never completed')

    @patch('tak_map_graph_switch_i675._wheel_binary', lambda: Path('/fake/valhalla'))
    @patch('tak_map_graph_switch_i675._version_ok', lambda _:True)
    def test_selection_updates_real_active_config_and_catalog(self):
        sw = GraphSwitcher(self.catalog, prepare=self._prepare, restart=self._restart, ready=lambda:True)
        self.assertFalse(any(row['dataset_id'] == B and row['active'] for row in sw.options()['datasets']))
        self.assertTrue(sw.start(B)['accepted'])
        self._wait(sw)
        self.assertEqual(sw.job['status'],'ready')
        self.assertEqual(self.restarts,[B])
        self.assertEqual((self.root/'active'/'dataset-id').read_text().strip(),B)
        self.assertEqual(sw.options()['active_dataset_id'],B)
        self.assertEqual([row['dataset_id'] for row in sw.options()['datasets'] if row['active']],[B])
        already = sw.start(B)
        self.assertTrue(already['already_active'])
        self.assertEqual(self.restarts,[B])

    @patch('tak_map_graph_switch_i675._wheel_binary', lambda: Path('/fake/valhalla'))
    @patch('tak_map_graph_switch_i675._version_ok', lambda _:True)
    def test_unready_new_graph_rolls_back_old_config_and_catalog(self):
        before = (self.root/'active'/'valhalla.json').read_bytes()
        sw = GraphSwitcher(self.catalog, prepare=self._prepare, restart=self._restart, ready=lambda:False)
        sw.start(B)
        self._wait(sw)
        self.assertEqual(sw.job['status'],'error')
        self.assertEqual(self.restarts,[B,A])
        self.assertEqual((self.root/'active'/'dataset-id').read_text().strip(),A)
        self.assertEqual((self.root/'active'/'valhalla.json').read_bytes(),before)
        self.assertEqual(sw.options()['active_dataset_id'],A)

    @patch('tak_map_graph_switch_i675._wheel_binary', lambda: Path('/fake/valhalla'))
    @patch('tak_map_graph_switch_i675._version_ok', lambda _:True)
    def test_bad_ids_and_nonlocal_packages_rejected(self):
        sw = GraphSwitcher(self.catalog, prepare=self._prepare, restart=self._restart, ready=lambda:True)
        for ident in ('../../etc/passwd', 'https://example.invalid/a.zip','c'*64):
            with self.assertRaises(NDMError): sw.start(ident)
        self.assertEqual(self.restarts,[])

    @patch('tak_map_graph_switch_i675._wheel_binary', lambda: Path('/fake/valhalla'))
    @patch('tak_map_graph_switch_i675._version_ok', lambda _:True)
    def test_switch_busy_while_preparing(self):
        import threading
        gate=threading.Event()
        def slow(catalog,ident):
            gate.wait(1)
            self._prepare(catalog,ident)
        sw = GraphSwitcher(self.catalog, prepare=slow, restart=self._restart, ready=lambda:True)
        sw.start(B)
        with self.assertRaises(NDMError) as err: sw.start(A)
        self.assertEqual(err.exception.code,'SWITCH_BUSY')
        gate.set()
        self._wait(sw)
        self.assertEqual(sw.job['status'],'ready')

if __name__ == '__main__': unittest.main(verbosity=2)
