#!/usr/bin/env python3
"""Static contract for the authoritative Gateway Data deferred runtime in i616."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
ASSET = (ROOT / "assets" / "tak-map-gateway-data-v491.js").read_text()
MANIFEST_PATH = ROOT / "assets" / "tak-map-deferred-i553.json"


def main() -> int:
    assert (ROOT / "VERSION").read_text().strip() == "1.3.0-i616"
    manifest = json.loads(MANIFEST_PATH.read_text())
    assert manifest["version"] == "1.3.0-i616"
    assert manifest["count"] == len(manifest["scripts"])
    rows = [row for row in manifest["scripts"] if row.get("id") == "takMapGatewayDataLoaderV476"]
    assert len(rows) == 1, len(rows)
    embedded = rows[0].get("code", "")
    assert embedded == ASSET, "Deferred Gateway Data runtime must exactly match the packaged asset"
    for marker in (
        "const V='i616',POLL_MS=300000;",
        "contextPanelUsed:true",
        "floatingLeafletPopups:false",
        "dynamicContextCurated:true",
        "gateway-data-selected-i614",
        "gatewayDataReadOnly:true",
        "contextEditControls:false",
        "contextDeleteControls:false",
        "contextAnimatedAccents:false",
        "function showGatewayReadOnly",
        "showReadOnly",
        "function dynamicImportantRows",
        "function openGatewayPopup",
        "function bindGatewayContext",
        "if(gt==='MultiPolygon')",
        "if(gt==='MultiLineString')",
        "dynamicSourceDiscovery:true",
    ):
        assert marker in embedded, marker
    assert ".bindPopup(" not in embedded
    assert "const V='i523'" not in embedded
    assert "const V='i612'" not in embedded
    startup = (ROOT / "assets" / "tak-map-startup-i553.js").read_text()
    assert "/assets/runtime/tak-map-deferred-i553.json?v=1.3.0-i616" in startup
    assert "/assets/runtime/tak-map-deferred-i553.json?v=1.3.0-i613" not in startup
    package = (ROOT / "assets" / "tak-map-package-i580.js").read_text()
    assert "const VERSION='i616';" in package
    assert "const PACKAGE='1.3.0-i616';" in package
    assert "window.TakMapPackageI616=window.TakMapPackageI615=" in package
    print("TAK Map i616 release/deferred Gateway Data runtime contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
