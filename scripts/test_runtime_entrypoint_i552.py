#!/usr/bin/env python3
from __future__ import annotations

import os
import pathlib
import socket
import subprocess
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

ROOT = pathlib.Path(__file__).resolve().parents[1]
DASH = ROOT / "tak_dashboard.py"

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]

with tempfile.TemporaryDirectory(prefix="tak-map-i552-entrypoint-") as data_dir:
    env = os.environ.copy()
    env.update({
        "TAK_DASHBOARD_BIND": "127.0.0.1",
        "TAK_DASHBOARD_PORT": str(port),
        "TAK_DASHBOARD_DATA_DIR": data_dir,
        "PYTHONUNBUFFERED": "1",
        "PYTHONWARNINGS": "ignore::SyntaxWarning",
    })
    proc = subprocess.Popen(
        [sys.executable, str(DASH)],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        deadline = time.monotonic() + 20
        last_error = "server did not answer"
        startup_url = f"http://127.0.0.1:{port}/assets/runtime/tak-map-startup-i552.js"
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                output = proc.stdout.read() if proc.stdout else ""
                raise AssertionError(f"TAK Map exited before serving i552 assets: {output}")
            try:
                with urlopen(startup_url, timeout=1.5) as response:
                    body = response.read().decode("utf-8", "replace")
                    assert response.status == 200
                    assert "TakMapStartupDiagnosticsI552" in body
                    break
            except (HTTPError, URLError, TimeoutError, AssertionError) as exc:
                last_error = str(exc)
                time.sleep(0.15)
        else:
            output = proc.stdout.read() if proc.stdout else ""
            raise AssertionError(f"TAK Map never served the i552 startup asset: {last_error}\n{output}")

        assets = {
            "tak-map-startup-i552.js": "TakMapStartupDiagnosticsI552",
            "tak-map-core-i552.js": "__takMapCoreInitI552",
            "tak-map-data-sync-i552.js": "__takMapDataSyncControlReadyI552",
            "tak-map-deferred-i552.json": '"version":"1.3.0-i552"',
            "tak-map-milstd2525c-i552.js": "TakMapMilStd2525CI552",
        }
        for filename, marker in assets.items():
            url = f"http://127.0.0.1:{port}/assets/runtime/{filename}"
            with urlopen(url, timeout=4) as response:
                body = response.read().decode("utf-8", "replace")
                assert response.status == 200, (filename, response.status)
                assert marker in body, (filename, marker)
                content_type = response.headers.get("Content-Type", "")
                assert "javascript" in content_type or "json" in content_type, (filename, content_type)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)

print("i552 executable entrypoint serves all current runtime assets")
