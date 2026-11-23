#!/usr/bin/env python3
"""Install pinned official native Valhalla 3.6.3 executable from PyPI wheels.
No installation into system Python; preserves entire vendored .libs/RPATH tree.
Executed *before* upgrading TAK Map by install.sh. Fail closed if download,
checksum, architecture or runnable version is not verified.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import zipfile

VERSION='3.6.3'
SHA={
 'x86_64':'e123720983ce570f340c3ef78289098bf647deba68d56143571384a5aa874868',
 'aarch64':'b3e60b2b474c9e27e3303b964d54603a249ca952ae5100e3a8d361107d1c329d',
}
PYPI='https://pypi.org/pypi/pyvalhalla/3.6.3/json'


def architecture():
    if sys.platform!='linux':raise RuntimeError('Only Linux is supported')
    cpu=platform.machine().lower()
    if cpu not in SHA:raise RuntimeError(f'Unsupported processor {cpu}; x86_64 or aarch64 required')
    libc,ver=platform.libc_ver()
    if libc!='glibc' or tuple(map(int,(ver.split('.')[:2])))<(2,28):
        raise RuntimeError('Official wheel requires glibc 2.28 or later')
    return cpu


def _version_ok(path):
    try:
        p=subprocess.run([str(path),'--version'],capture_output=True,text=True,timeout=12)
        return p.returncode==0 and VERSION in (p.stdout+p.stderr)
    except (OSError,subprocess.TimeoutExpired):return False


def source_info(cpu,metadata):
    expected=f'pyvalhalla-{VERSION}-cp312-abi3-manylinux_2_28_{cpu}.whl'
    for entry in metadata.get('urls',[]):
        if entry.get('filename')==expected:
            url=entry.get('url','')
            parsed=urllib.parse.urlsplit(url)
            if parsed.scheme!='https' or parsed.hostname!='files.pythonhosted.org' or not parsed.path.endswith('/'+expected):
                raise RuntimeError('Unexpected PyPI wheel download URL')
            if entry.get('digests',{}).get('sha256')!=SHA[cpu]:
                raise RuntimeError('Published PyPI SHA-256 differs from pinned upstream release')
            return url,expected
    raise RuntimeError('Matching official Valhalla wheel not found')


def validate_name(name):
    parts=PurePosixPath(name).parts
    if name.startswith('/') or '\\' in name or '..' in parts or '\x00' in name or not name:
        raise RuntimeError('Wheel contains unsafe path')
    return name


def _unpack_wheel(wheel,dest):
    count=0;total=0;seen=set()
    with zipfile.ZipFile(wheel) as z:
        for entry in z.infolist():
            name=validate_name(entry.filename)
            if name in seen:raise RuntimeError('Wheel contains duplicate path')
            seen.add(name);count+=1;total+=entry.file_size
            if count>10000 or total>400*1024*1024:raise RuntimeError('Wheel extraction quota exceeded')
            typ=(entry.external_attr>>16)&0o170000
            if typ and typ not in (stat.S_IFREG,stat.S_IFDIR):raise RuntimeError('Wheel contains symlinks')
            target=dest/name
            if entry.is_dir():target.mkdir(parents=True,exist_ok=True);continue
            target.parent.mkdir(parents=True,exist_ok=True)
            with z.open(entry) as fi,open(target,'wb') as fo:shutil.copyfileobj(fi,fo,1024*1024)
            if name.startswith('valhalla/bin/'):
                target.chmod(0o755)
            else:target.chmod(0o644)
        if z.testzip() is not None:raise RuntimeError('Wheel CRC check failed')
    executable=dest/'valhalla/bin/valhalla_service'
    if not executable.is_file():raise RuntimeError('Official wheel did not include native valhalla_service')
    if not _version_ok(executable):raise RuntimeError('Native Valhalla executable version test failed')
    return executable


def install(dest):
    cpu=architecture(); dest=Path(dest)
    binary=dest/'valhalla/bin/valhalla_service'
    if binary.exists() and _version_ok(binary):
        print('Verified Valhalla 3.6.3 already installed:',binary);return
    if dest.exists():
        raise RuntimeError(f'Unverified existing Valhalla directory must be investigated, not overwritten: {dest}')
    with urllib.request.urlopen(PYPI,timeout=25) as r:
        metadata=json.load(r)
    url,name=source_info(cpu,metadata)
    dest.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.valhalla-i651-',dir=dest.parent) as temporary:
        temp=Path(temporary)
        wheel=temp/name
        h=hashlib.sha256()
        with urllib.request.urlopen(url,timeout=120) as response,open(wheel,'wb') as output:
            bytes_read=0
            while True:
                chunk=response.read(1024*1024)
                if not chunk:break
                bytes_read+=len(chunk)
                if bytes_read>100*1024*1024:raise RuntimeError('Wheel download exceeded limit')
                h.update(chunk);output.write(chunk)
        if h.hexdigest()!=SHA[cpu]:raise RuntimeError('Downloaded wheel failed pinned SHA-256')
        extracted=temp/'installed'
        extracted.mkdir()
        _unpack_wheel(wheel,extracted)
        # Atomic promotion only after executable check. No system Valhalla replacement.
        extracted.rename(dest)
        print('Installed verified Valhalla 3.6.3 native executable:',dest/'valhalla/bin/valhalla_service')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--dest',default='/opt/tak-map/vendor/valhalla-3.6.3')
    args=parser.parse_args()
    try:install(args.dest)
    except Exception as e:
        print('Valhalla provisioning failed:',e,file=sys.stderr)
        sys.exit(1)
