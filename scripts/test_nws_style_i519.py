#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "assets" / "tak-map-gateway-data-v491.js").read_text()

assert "weight:src==='nws_alerts'?2" in SOURCE
assert "opacity:src==='nws_alerts'?.8:.95" in SOURCE
assert "fillOpacity:src==='nws_alerts'?.05" in SOURCE
assert "fillOpacity:src==='nws_alerts'?.10" not in SOURCE
print("TAK Map i519 NWS polygon style contract test passed")
