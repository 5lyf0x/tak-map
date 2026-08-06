#!/usr/bin/env python3
"""Compatibility entry point for the current protected-Mission backend security test."""
from pathlib import Path
import runpy
ROOT = Path(__file__).resolve().parents[1]
runpy.run_path(str(ROOT / 'scripts/test_data_sync_discoverable_locked_i594.py'), run_name='__main__')
