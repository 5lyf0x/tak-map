#!/usr/bin/env python3
"""Verify the exact missing-module installer defect cannot recur in i004.

This runs the real module-install command in a sandbox APP_DIR, not the full
root installer (which would change the live host or use apt/network).
"""
from pathlib import Path
import hashlib, importlib.util, os, re, stat, subprocess, tempfile
root=Path(__file__).resolve().parent.parent
source=(root/'tak_map_offline_perf_i003.py').read_bytes()
installer=(root/'install.sh').read_text()
backend=(root/'tak_dashboard.py').read_text()
assert 'import tak_map_offline_perf_i003 as _offline_perf_i003' in backend
line='install -m 0644 tak_map_offline_perf_i003.py "$APP_DIR/tak_map_offline_perf_i003.py"'
assert installer.count(line)==1
assert installer.find(line)<installer.find('cp tak_dashboard.py "$APP_DIR/tak_dashboard.py"')
assert installer.find(line)<installer.find('systemctl restart tak-map') or installer.find('systemctl restart tak-map')<0
with tempfile.TemporaryDirectory(prefix='tak-map-i004-installer-') as tmp:
    env=dict(os.environ, APP_DIR=tmp)
    result=subprocess.run(['bash','-euo','pipefail','-c',line],cwd=root,env=env,capture_output=True,text=True)
    assert result.returncode==0,(result.stdout,result.stderr)
    target=Path(tmp)/'tak_map_offline_perf_i003.py'
    assert target.is_file() and target.read_bytes()==source
    assert (target.stat().st_mode & 0o777)==0o644
    spec=importlib.util.spec_from_file_location('tak_map_offline_perf_i003',str(target))
    assert spec and spec.loader
    # Test module loading in a clean import context with the correct installed path.
    check=subprocess.run(['python3','-c', 'import sys;sys.path.insert(0,sys.argv[1]);import tak_map_offline_perf_i003 as m;assert hasattr(m,"OfflineTileStore")',str(Path(tmp))],capture_output=True,text=True)
    assert check.returncode==0,check.stderr
print('PASS i004: missing helper installed before backend with 0644, identical bytes, importable module')
