#!/usr/bin/env python3
from pathlib import Path
import hashlib, json
ROOT=Path(__file__).resolve().parents[1]
standalone=(ROOT/'assets/tak-map-milstd2525c-i553.js').read_text()
manifest=json.loads((ROOT/'assets/tak-map-deferred-i553.json').read_text())
rows=[row for row in manifest.get('scripts',[]) if row.get('id')=='takMapMilStd2525CLoaderI553']
assert len(rows)==1, [row.get('id') for row in manifest.get('scripts',[]) if 'MilStd2525C' in str(row.get('id',''))]
embedded=str(rows[0].get('code') or '')
assert embedded==standalone
assert hashlib.sha256(embedded.encode()).hexdigest()==hashlib.sha256(standalone.encode()).hexdigest()
assert 'REVIEWED_ALIASES_I553' in embedded
assert 'a-f-g-u-c-e-n' in embedded
assert 'a-f-g-e-w-h' in embedded
assert manifest.get('version')=='1.3.0-i553'
assert manifest.get('count')==len(manifest.get('scripts',[]))
assert manifest['scripts'][-1]['id']=='takMapMilStd2525CLoaderI553'
print('i553 standalone/deferred resolver byte parity and reviewed alias presence passed')
