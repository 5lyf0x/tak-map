#!/usr/bin/env python3
"""NDM terrain read-only schema, coverage and datum probe.

Uses only SQLite immutable read-only connections. Does not extract, write to,
repair, or register any dataset. Reports a single bounded example grid for
format verification; no bulk decompression or private path disclosure.
"""
import argparse
import array
import json
from pathlib import Path
import sqlite3
import sys
import zlib

ROOT = Path('/var/lib/tak-map/ndm/elevation-cache')


def inspect(path: Path):
    report = {'dataset': path.parent.name, 'status': 'error', 'datum': 'unverified'}
    try:
        uri = path.resolve().as_uri() + '?mode=ro&immutable=1'
        with sqlite3.connect(uri, uri=True, timeout=3) as conn:
            names = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not {'metadata', 'tiles'} <= names:
                raise ValueError('missing tiles or metadata table')
            meta = list(conn.execute('SELECT name,value FROM metadata LIMIT 150'))
            metadata = {str(k): str(v)[:200] for k, v in meta}
            if metadata.get('schema') != 'takrig.terrain.sqlite.v1':
                raise ValueError('unexpected terrain schema')
            cols = {row[1] for row in conn.execute('PRAGMA table_info(tiles)')}
            must = {'tile_id','west','south','east','north','rows','cols','encoding','data'}
            if not must <= cols:
                raise ValueError('terrain grid fields missing: ' + ','.join(sorted(must-cols)))
            count, min_w, min_s, max_e, max_n = conn.execute(
                'SELECT COUNT(*),MIN(west),MIN(south),MAX(east),MAX(north) FROM tiles'
            ).fetchone()
            if count > 50000:
                raise ValueError('tile catalog too large for current TAK Map sampler')
            datums = {k: v for k, v in metadata.items() if any(t in k.lower() for t in ('datum','geoid','vertical','reference'))}
            row = conn.execute('SELECT rows,cols,encoding,data FROM tiles LIMIT 1').fetchone()
            sample = None
            if row:
                rows, cols, encoding, compressed = row
                rows, cols = int(rows), int(cols)
                if encoding != 'int16le+zlib' or rows < 2 or cols < 2 or rows*cols > 5000000:
                    raise ValueError('unsupported NDM tile dimensions/encoding')
                d = zlib.decompressobj()
                payload = d.decompress(compressed, rows*cols*2+1)
                if not d.eof or d.unconsumed_tail or d.unused_data or len(payload) != rows*cols*2:
                    raise ValueError('invalid compressed height grid')
                heights = array.array('h')
                heights.frombytes(payload)
                if sys.byteorder != 'little':
                    heights.byteswap()
                valid = [h for h in heights if h > -32767]
                sample = {'rows':rows, 'cols':cols, 'encoding': encoding,
                          'valid_samples':len(valid), 'missing_samples':len(heights)-len(valid),
                          'minimum_m':min(valid) if valid else None,
                          'maximum_m':max(valid) if valid else None}
            report.update(status='readable', schema=metadata['schema'],
                tile_count=count, bounds=[min_w,min_s,max_e,max_n],
                metadata_keys=sorted(metadata.keys()), vertical_reference_fields=datums,
                first_grid=sample)
            if not datums:
                report['datum']='unverified: no explicit vertical reference metadata'
            else:
                report['datum']='metadata present — requires geodetic verification'
    except Exception as exc:
        report['error'] = f'{type(exc).__name__}: {str(exc)[:180]}'
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cache', type=Path, default=ROOT, help='Prepared NDM terrain cache directory (read-only)')
    ap.add_argument('--db', type=Path, action='append', help='Explicit terrain.sqlite file (may repeat)')
    args = ap.parse_args()
    paths = args.db or sorted(args.cache.glob('*/terrain.sqlite'))[:20]
    if not paths:
        print(json.dumps({'status':'no_prepared_ndm_db','cache':str(args.cache),'note':'No registered prepared NDM terrain.sqlite is present; do not infer schema/datum.'},indent=2))
        return 2
    results=[inspect(p) for p in paths]
    print(json.dumps({'status':'inspected','datasets':results,'writes_performed':False},indent=2))
    return 0 if all(r['status']=='readable' for r in results) else 1

if __name__ == '__main__':
    raise SystemExit(main())
