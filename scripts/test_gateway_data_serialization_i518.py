#!/usr/bin/env python3
"""Verify Gateway Data GeoJSON bypasses the generic 1,000-item diagnostics cap."""
from __future__ import annotations

import io
import json
import os
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fake_handler(path: str):
    class Fake:
        def __init__(self) -> None:
            self.path = path
            self.wfile = io.BytesIO()
            self.status = None
            self.headers: dict[str, str] = {}

        def _tak_map_refresh_headers(self, headers, _code):
            return dict(headers or {})

        def send_response(self, code):
            self.status = code

        def send_header(self, key, value):
            self.headers[str(key)] = str(value)

        def end_headers(self):
            return None

    return Fake()


def ring(count: int) -> list[list[float]]:
    assert count >= 4
    rows = [[-118.0 + i * 0.00001, 34.0 + (i % 17) * 0.00001] for i in range(count - 1)]
    rows.append(rows[0][:])
    return rows


def main() -> int:
    os.environ["TAK_MAP_TEST_SKIP_ADSB_WARMUP"] = "1"
    ns = runpy.run_path(str(ROOT / "tak_dashboard.py"), run_name="tak_map_i518_serialization_test")
    send_json = ns["Handler"]._send_json

    large_ring = ring(4737)
    payload = {
        "ok": True,
        "full": True,
        "revision": 1,
        "objects": [
            {
                "type": "Feature",
                "id": "TAKGATE-NWS-I518-LARGE",
                "geometry": {"type": "Polygon", "coordinates": [large_ring]},
                "properties": {"source": "nws_alerts", "title": "Large valid NWS polygon"},
            }
        ],
    }

    gateway = fake_handler("/api/tak-map/gateway-data/snapshot?since_revision=0")
    send_json(gateway, payload, 200)
    decoded = json.loads(gateway.wfile.getvalue().decode("utf-8"))
    output_ring = decoded["objects"][0]["geometry"]["coordinates"][0]
    assert gateway.status == 200
    assert len(output_ring) == 4737
    assert output_ring[-1] == output_ring[0]
    assert "...truncated..." not in gateway.wfile.getvalue().decode("utf-8")

    ordinary = fake_handler("/api/diagnostics/example")
    send_json(ordinary, {"rows": list(range(1001))}, 200)
    ordinary_json = json.loads(ordinary.wfile.getvalue().decode("utf-8"))
    assert len(ordinary_json["rows"]) == 1001
    assert ordinary_json["rows"][-1] == "...truncated..."

    print("Gateway Data i518 lossless large-geometry serialization test passed")
    os._exit(0)


if __name__ == "__main__":
    raise SystemExit(main())
