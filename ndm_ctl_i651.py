#!/usr/bin/env python3
"""Local operator-only NDM graph selection for TAK Map i651 service smoke tests.
This command NEVER starts or enables systemd service.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from ndm_packages_i651 import Catalog,NDMError,_LOCK
from ndm_valhalla_i651 import prepare_graph,_version_ok,_wheel_binary


def select(catalog,dataset_id,confirmation):
    if confirmation!='I-UNDERSTAND-LIVE-TEST':
        raise NDMError('Explicit I-UNDERSTAND-LIVE-TEST confirmation required')
    if not _version_ok(_wheel_binary()):
        raise NDMError('Verified Valhalla 3.6.3 executable not installed')
    result=prepare_graph(catalog,dataset_id)
    prepared=catalog.root/'prepared'/(dataset_id+'.json')
    active=catalog.root/'active'
    active.mkdir(mode=0o750,parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.valhalla-',dir=active)
    try:
        with os.fdopen(fd,'wb') as fp:
            fp.write(prepared.read_bytes())
            fp.flush();os.fsync(fp.fileno())
        os.replace(tmp,active/'valhalla.json')
        (active/'dataset-id').write_text(dataset_id+'\n')
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    with _LOCK:
        data=catalog._load()
        for k,v in data['datasets'].items():v['active']=(k==dataset_id)
        catalog._save(data)
    return result


def main():
    ap=argparse.ArgumentParser(description='TAK Map i651 NDM operator smoke-test prep (never starts services)')
    group=ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--list',action='store_true')
    group.add_argument('--prepare',metavar='SHA256')
    group.add_argument('--select-for-live-test',metavar='SHA256')
    ap.add_argument('--confirm',default='')
    args=ap.parse_args()
    catalog=Catalog()
    try:
        if args.list:
            for row in catalog.listing():print(row['dataset_id'],row['type'],row['region'],row['owner'],row['available'])
        elif args.prepare:print(json.dumps(prepare_graph(catalog,args.prepare),indent=2))
        else:
            print(json.dumps(select(catalog,args.select_for_live_test,args.confirm),indent=2))
            print('Active config selected. Valhalla service remains STOPPED/DISABLED. For a controlled smoke test, an operator may now run: sudo systemctl start tak-map-valhalla.service')
    except (NDMError,OSError,ValueError) as e:
        print('NDM operation failed:',e,file=sys.stderr)
        sys.exit(1)

if __name__=='__main__':main()
