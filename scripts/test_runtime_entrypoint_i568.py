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

with tempfile.TemporaryDirectory(prefix="tak-map-i568-entrypoint-") as data_dir:
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
        startup_url = f"http://127.0.0.1:{port}/assets/runtime/tak-map-startup-i553.js"
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                output = proc.stdout.read() if proc.stdout else ""
                raise AssertionError(f"TAK Map exited before serving i568 assets: {output}")
            try:
                with urlopen(startup_url, timeout=1.5) as response:
                    body = response.read().decode("utf-8", "replace")
                    assert response.status == 200
                    assert "TakMapStartupDiagnosticsI553" in body
                    break
            except (HTTPError, URLError, TimeoutError, AssertionError) as exc:
                last_error = str(exc)
                time.sleep(0.15)
        else:
            output = proc.stdout.read() if proc.stdout else ""
            raise AssertionError(f"TAK Map never served the i568 startup asset: {last_error}\n{output}")

        assets = {
            "tak-map-startup-i553.js": "TakMapStartupDiagnosticsI553",
            "tak-map-core-i553.js": "__takMapCoreInitI553",
            "tak-map-data-sync-i553.js": "__takMapDataSyncControlReadyI553",
            "tak-map-deferred-i553.json": '"version":"1.3.0-i568"',
            "tak-map-milstd2525c-i553.js": "TakMapMilStd2525CI553",
            "tak-map-icon-registry-i568.js": "TakMapIconRegistryI568",
            "tak-map-popup-localdata-i568.js": "TakMapPopupLocalDataI568",
            "tak-map-context-sidebar-i568.js": "TakMapContextSidebarI568",
        }
        for filename, marker in assets.items():
            url = f"http://127.0.0.1:{port}/assets/runtime/{filename}"
            with urlopen(url, timeout=4) as response:
                body = response.read().decode("utf-8", "replace")
                assert response.status == 200, (filename, response.status)
                assert marker in body, (filename, marker)
                content_type = response.headers.get("Content-Type", "")
                assert "javascript" in content_type or "json" in content_type, (filename, content_type)

        with urlopen(f"http://127.0.0.1:{port}/mil2525/atak-compatibility-aliases-i553.json", timeout=4) as response:
            body = response.read().decode('utf-8','replace')
            assert response.status == 200
            assert 'by_cot_type' in body and 'atak-compatibility-aliases-i553' in body
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)

print("i568 executable entrypoint serves the preserved i553 runtime and active i568 registry, Local Data, and contextual-sidebar plug-ins")
sys.stdout.flush()
os._exit(0)
