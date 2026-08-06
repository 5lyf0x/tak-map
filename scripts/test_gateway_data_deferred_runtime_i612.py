#!/usr/bin/env python3
"""Static contract for the authoritative i612 Gateway Data deferred runtime."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
ASSET = (ROOT / "assets" / "tak-map-gateway-data-v491.js").read_text()
MANIFEST_PATH = ROOT / "assets" / "tak-map-deferred-i553.json"


def main() -> int:
    assert (ROOT / "VERSION").read_text().strip() == "1.3.0-i612"
    manifest = json.loads(MANIFEST_PATH.read_text())
    assert manifest["version"] == "1.3.0-i612"
    assert manifest["count"] == len(manifest["scripts"])

    rows = [row for row in manifest["scripts"] if row.get("id") == "takMapGatewayDataLoaderV476"]
    assert len(rows) == 1, len(rows)
    embedded = rows[0].get("code", "")
    assert embedded == ASSET, "Deferred Gateway Data runtime must exactly match the packaged asset"
    assert "const V='i612',POLL_MS=300000;" in embedded
    assert "const V='i523'" not in embedded
    assert "dynamicSourceDiscovery:true" in embedded
    assert "if(gt==='MultiPolygon')" in embedded
    assert "if(gt==='MultiLineString')" in embedded

    startup = (ROOT / "assets" / "tak-map-startup-i553.js").read_text()
    assert "/assets/runtime/tak-map-deferred-i553.json?v=1.3.0-i612" in startup
    assert "/assets/runtime/tak-map-deferred-i553.json?v=1.3.0-i611" not in startup

    package = (ROOT / "assets" / "tak-map-package-i580.js").read_text()
    assert "const VERSION='i612';" in package
    assert "const PACKAGE='1.3.0-i612';" in package

    print("TAK Map i612 authoritative deferred Gateway Data runtime contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
