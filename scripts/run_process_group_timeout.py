#!/usr/bin/env python3
"""Run a validation command with a hard timeout and kill its full process group."""
from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import tempfile


def _dump(log) -> None:
    try:
        log.flush()
        log.seek(0)
        shutil.copyfileobj(log, sys.stdout.buffer)
        sys.stdout.buffer.flush()
    except Exception as exc:
        print(f"WARNING: unable to display validation output: {exc}", file=sys.stderr)


def main() -> int:
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} SECONDS COMMAND [ARG ...]", file=sys.stderr)
        return 2
    try:
        timeout = float(sys.argv[1])
    except ValueError:
        print("SECONDS must be numeric", file=sys.stderr)
        return 2
    command = sys.argv[2:]
    with tempfile.TemporaryFile() as log:
        proc = subprocess.Popen(
            command,
            start_new_session=True,
            stdout=log,
            stderr=subprocess.STDOUT,
        )
        timed_out = False
        try:
            return_code = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                proc.wait()
            return_code = 124
        finally:
            # A validation command can exit while leaving browser/server helpers
            # behind. Terminate anything still in its isolated process group so
            # those helpers cannot hold the package validator's output pipe open.
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            _dump(log)
        if timed_out:
            print(f"ERROR: validation command exceeded {timeout:g} seconds: {' '.join(command)}", file=sys.stderr)
        return return_code


if __name__ == "__main__":
    raise SystemExit(main())
