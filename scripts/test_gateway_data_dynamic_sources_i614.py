#!/usr/bin/env python3
"""Static release contract preserving dynamic Gateway Data behavior in i614."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / "assets" / "tak-map-gateway-data-v491.js").read_text()


def main() -> int:
    assert (ROOT / "VERSION").read_text().strip() == "1.3.0-i614"
    manifest = json.loads((ROOT / "assets" / "tak-map-deferred-i553.json").read_text())
    assert manifest["version"] == "1.3.0-i614"
    startup = (ROOT / "assets" / "tak-map-startup-i553.js").read_text()
    package = (ROOT / "assets" / "tak-map-package-i580.js").read_text()
    assert "/assets/runtime/tak-map-deferred-i553.json?v=1.3.0-i614" in startup
    assert "const VERSION='i614';" in package
    assert "const PACKAGE='1.3.0-i614';" in package
    for marker in (
        "const V='i614'",
        "function dynamicSource",
        "function sourceCatalog",
        "source_extension:",
        "getBool('ingest.'+id,false)",
        "clearSourceObjects(id,'ingest-disabled')",
        "discardSourceGroup(id)",
        "S.worker.postMessage({cmd:'refresh'})",
        "function reconcileSources",
        "function shouldIngestFeature",
        "dynamicSourceDiscovery:true",
        "dynamicObjectsSkipped",
        "dynamicObjectsCleared",
        "MultiLineString",
        "MultiPolygon",
        "sourceLabel(p.source)",
        "function dynamicImportantRows",
        "contextPanelUsed:true",
        "floatingLeafletPopups:false",
    ):
        assert marker in JS, marker
    assert JS.count("panel gateway-data-v491") == 1
    print("TAK Map i614 dynamic Source Extension/context contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
