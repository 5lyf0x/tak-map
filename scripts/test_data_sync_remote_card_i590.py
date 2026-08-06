#!/usr/bin/env python3
"""Re-run the full browser startup fixture with the exact remote-OTS
PostgreSQL-missing response that made the i589 Data Sync card blank."""
from pathlib import Path
import subprocess, sys, tempfile
root=Path(__file__).resolve().parents[1]
base=(root/'scripts/test_i589_initial_load_browser.py').read_text()
needle="first_sync = {\n    'ok': True,"
replacement="first_sync = {\n    'ok': False,\n    'error': 'No OpenTAKServer PostgreSQL URI found.',"
if needle not in base: raise SystemExit('first Data Sync fixture marker missing')
base=base.replace(needle,replacement,1)
needle2="partial_sync = {\n    'ok': True,"
replacement2="partial_sync = {\n    'ok': False,\n    'error': 'No OpenTAKServer PostgreSQL URI found.',"
if needle2 not in base: raise SystemExit('follow-up Data Sync fixture marker missing')
base=base.replace(needle2,replacement2,1)
with tempfile.NamedTemporaryFile('w',suffix='.py',prefix='test_data_sync_remote_card_i590_',dir=root/'scripts',delete=False) as fh:
    fh.write(base); temp=Path(fh.name)
try:
    cp=subprocess.run([sys.executable,str(temp)],cwd=root,text=True,capture_output=True,timeout=180)
finally:
    temp.unlink(missing_ok=True)
if cp.returncode:
    sys.stderr.write(cp.stdout);sys.stderr.write(cp.stderr);raise SystemExit(cp.returncode)
print(cp.stdout.strip())
print('i590 remote OTS usable snapshot rendered in the Data Sync card despite optional missing PostgreSQL source')
