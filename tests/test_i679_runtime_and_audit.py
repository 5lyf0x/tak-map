import ast
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/'tak_dashboard.py'
sys.path.insert(0,str(ROOT/'scripts'))
import tak_map_import_geometry_audit_i679 as audit

class ReleaseSafetyTest(unittest.TestCase):
    def test_single_service_start_after_release_extensions(self):
        tree=ast.parse(SCRIPT.read_text())
        mains=[(index,node) for index,node in enumerate(tree.body) if isinstance(node,ast.If)
               and isinstance(node.test,ast.Compare)
               and isinstance(node.test.left,ast.Name)
               and node.test.left.id=='__name__']
        self.assertEqual(len(mains),1)
        self.assertEqual(mains[0][0],len(tree.body)-1,
                         'Blocking server main must be after all handler and version registration')
        self.assertIn("TAK_MAP_ITERATION='i681'",SCRIPT.read_text()[-3000:])

    def test_damaged_old_route_identified_without_modification(self):
        with tempfile.TemporaryDirectory(prefix='i679-audit-') as temp:
            path=Path(temp)/'imports.json'
            payload={'imports':[{'id':'legacy','name':'broken.geojson','features':[{'kind':'route','name':'old',
                'coords':[[34,-112]]*1000+['...truncated...']}]},
                {'id':'good','name':'good.geojson','features':[{'kind':'route','name':'full',
                'coords':[[34,-112],[35,-111]]}]}]}
            path.write_text(json.dumps(payload))
            before=hashlib.sha256(path.read_bytes()).hexdigest()
            result=audit.audit(path)
            self.assertEqual(result['suspect_routes'],1)
            self.assertEqual(result['problems'][0]['import_id'],'legacy')
            self.assertFalse(result['modified'])
            self.assertEqual(before,hashlib.sha256(path.read_bytes()).hexdigest())

if __name__=='__main__':unittest.main()
