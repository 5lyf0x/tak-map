#!/usr/bin/env python3
"""Read-only audit of legacy TAK Map imports for truncated route geometry.

Does not modify, delete, repair or export any saved data. Run separately after
installation if earlier versions reported incomplete route-save verification.
"""
import argparse
import json
from pathlib import Path

TRUNCATION_TOKEN = '...truncated...'


def route_problems(imp):
    for index, feature in enumerate(imp.get('features') or []):
        if not isinstance(feature, dict):
            continue
        if str(feature.get('kind') or '').lower() != 'route':
            continue
        coords=feature.get('coords')
        reasons=[]
        if not isinstance(coords, list):
            reasons.append('coordinates missing or not a list')
        else:
            if any(point == TRUNCATION_TOKEN for point in coords):
                reasons.append('legacy 1000-element truncation marker')
            if len(coords) < 2:
                reasons.append('fewer than 2 vertices')
            if any(not isinstance(point, (list, tuple)) or len(point)<2 or
                   not all(isinstance(value,(int,float)) for value in point[:2])
                   for point in coords):
                reasons.append('invalid coordinate entry')
        if reasons:
            yield {'import_id':str(imp.get('id') or ''),
                   'filename':str(imp.get('name') or ''),
                   'route_index':index,
                   'route_name':str(feature.get('name') or '')[:120],
                   'vertices_or_entries':len(coords) if isinstance(coords, list) else 0,
                   'problems':reasons}


def audit(path):
    data=json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(data,dict) or not isinstance(data.get('imports'),list):
        raise ValueError('Imports catalog is not a valid imports.json object.')
    problems=[]
    for imp in data['imports']:
        if isinstance(imp,dict):
            problems.extend(route_problems(imp))
    return {'file':str(path),'imports':len(data['imports']),
            'suspect_routes':len(problems),'problems':problems,
            'modified':False,
            'note':'Previously truncated geometry cannot be reconstructed from this catalog alone.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--file',default='/var/lib/tak-map/tak_map_imports/imports.json')
    args=parser.parse_args()
    try:
        print(json.dumps(audit(args.file),indent=2))
    except (ValueError,OSError,json.JSONDecodeError) as exc:
        parser.exit(2,'Unable to audit imports: '+str(exc)+'\n')

if __name__=='__main__':
    main()
