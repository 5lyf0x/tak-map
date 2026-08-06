#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import runpy
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]

CATALOG_ROWS = [
    ("tg-imagery-radar", "TG-ESRI-Img+NOAA", "NOAA Radar", "noaa", "imagery"),
    ("tg-street-radar", "TG-ESRI-Strt+NOAA", "NOAA Radar", "noaa", "street"),
    ("tg-imagery-rainviewer", "TG-ESRI-Img+RainViewer", "RainViewer", "rainviewer", "imagery"),
    ("tg-street-rainviewer", "TG-ESRI-Strt+RainViewer", "RainViewer", "rainviewer", "street"),
    ("tg-imagery-imerg", "TG-ESRI-Img+IMERG", "NASA IMERG", "imerg", "imagery"),
    ("tg-street-imerg", "TG-ESRI-Strt+IMERG", "NASA IMERG", "imerg", "street"),
    ("tg-imagery-goes18", "TG-ESRI-Img+GOES18-Pacific", "GOES-18 Pacific", "goes18", "imagery"),
    ("tg-street-goes18", "TG-ESRI-Strt+GOES18-Pacific", "GOES-18 Pacific", "goes18", "street"),
    ("tg-imagery-goes19", "TG-ESRI-Img+GOES19-Atlantic", "GOES-19 Atlantic", "goes19", "imagery"),
    ("tg-street-goes19", "TG-ESRI-Strt+GOES19-Atlantic", "GOES-19 Atlantic", "goes19", "street"),
]

XML_TEMPLATE = '''<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
  <name>{name}</name><minZoom>2</minZoom><maxZoom>22</maxZoom>
  <tileType>PNG</tileType><tileUpdate>None</tileUpdate><ignoreErrors>true</ignoreErrors>
  <url><![CDATA[{url}]]></url><backgroundColor>#000000</backgroundColor>
</customMapSource>
'''


class GatewayFixture(BaseHTTPRequestHandler):
    counts = {"catalog": 0, "xml": 0, "tile": 0}

    def log_message(self, *_args):
        return

    def reply(self, status: int, raw: bytes, ctype: str):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        host = f"http://127.0.0.1:{self.server.server_address[1]}"
        if self.path in ("/basemaps/catalog", "/basemaps/catalog.json"):
            type(self).counts["catalog"] += 1
            rows = []
            for bid, name, _label, source, kind in CATALOG_ROWS:
                base_url = (
                    "https://services.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}"
                    if kind == "street" else
                    "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                )
                rows.append({
                    "id": bid,
                    "name": name,
                    "group": "TAK Gateway Composite",
                    "xml_url": f"{host}/basemaps/xml/{bid}.xml",
                    "client_composition": {
                        "enabled": True,
                        "base_url": base_url,
                        "overlay_url": f"{host}/tiles/overlay-{source}/{{z}}/{{x}}/{{y}}.png",
                        "overlay_opacity": 0.68 if source.startswith("goes") else 0.90,
                        "overlay_source": source,
                        "base_kind": kind,
                        "tile_size": 256,
                        "max_native_zoom": 22,
                        "freshness_seconds": 600,
                    },
                })
            payload = {"ok": True, "iteration": "i159", "basemaps": rows}
            return self.reply(200, json.dumps(payload).encode(), "application/json")
        if self.path.startswith("/basemaps/xml/") and self.path.endswith(".xml"):
            bid = unquote(self.path.rsplit("/", 1)[-1][:-4])
            match = next((row for row in CATALOG_ROWS if row[0] == bid), None)
            if match:
                type(self).counts["xml"] += 1
                return self.reply(200, XML_TEMPLATE.format(
                    name=match[1], url=f"{host}/tiles/{bid}/{{$z}}/{{$x}}/{{$y}}.png"
                ).encode(), "application/xml")
        if self.path.startswith("/tiles/"):
            type(self).counts["tile"] += 1
            return self.reply(200, b"\x89PNG\r\n\x1a\nI508-DIRECT-TILE", "image/png")
        self.send_response(404); self.end_headers()


def main() -> int:
    GatewayFixture.counts = {"catalog": 0, "xml": 0, "tile": 0}
    server = ThreadingHTTPServer(("127.0.0.1", 0), GatewayFixture)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    gateway = f"http://127.0.0.1:{server.server_address[1]}"

    with tempfile.TemporaryDirectory(prefix="tak-map-i508-") as td:
        os.environ["TAK_DASHBOARD_DATA_DIR"] = td
        os.environ["TAK_MAP_GATEWAY_BASEMAP_URL"] = gateway
        os.environ["TAK_MAP_GATEWAY_BASEMAP_TIMEOUT"] = "5"
        os.environ["TAK_MAP_GATEWAY_DIRECT_BASEMAPS"] = "true"
        os.environ["TAK_MAP_GATEWAY_CA_CERT"] = str(Path(td) / "missing-ca.crt")
        module = runpy.run_path(str(ROOT / "tak_dashboard.py"), run_name="tak_dashboard_i508_test")
        try:
            result = module["_i506_import_gateway_basemaps"]()
            assert result["ok"] is True, result
            assert result["version"] == "i517", result
            assert len(result["imported"]) == len(CATALOG_ROWS), result
            assert GatewayFixture.counts == {"catalog": 1, "xml": 10, "tile": 0}, GatewayFixture.counts

            stored = json.loads(Path(module["TAK_MAP_CUSTOM_BASEMAPS_FILE"]).read_text())
            assert stored["version"] == "i517", stored
            assert all((row.get("client_composition") or {}).get("enabled") for row in stored["basemaps"]), stored

            cfg = module["tak_map_config"]()
            assert cfg["tak_map_iteration"] == "i537", cfg.get("tak_map_iteration")
            gateway_rows = [b for b in cfg["basemaps"] if b.get("managementType") == "gateway"]
            assert len(gateway_rows) == 10, gateway_rows
            for row in gateway_rows:
                assert row.get("clientComposition") is True, row
                assert row.get("baseUrl", "").startswith("https://services.arcgisonline.com/"), row
                assert row.get("overlayUrl", "").startswith(gateway + "/tiles/overlay-"), row
                assert row.get("serverCompositeUrl") == row.get("url"), row
                assert row.get("takMapPythonProxy") is False, row
                assert row.get("overlayFreshnessSeconds") == 600, row
                assert "/api/tak-map/custom-basemap-tile/" not in row.get("url", ""), row

            # Existing i507 rows without catalog metadata are upgraded in place by
            # source/name inference and do not need to be deleted and re-imported.
            inferred = module["_i508_gateway_composition"]({
                "source_kind": "tak-gateway",
                "label": "TG-ESRI-Strt+GOES19-Atlantic",
                "gateway_catalog_id": "tg-street-goes19",
            })
            assert inferred["overlay_source"] == "goes19", inferred
            assert "World_Street_Map" in inferred["base_url"], inferred
            assert inferred["overlay_url"].startswith(gateway + "/tiles/overlay-goes19/"), inferred

            manual = module["_i505_parse_basemap_xml"](
                XML_TEMPLATE.format(name="Manual Test", url="https://example.invalid/{z}/{x}/{y}.png").encode(),
                "manual.xml", "manual",
            )
            module["_i505_upsert_custom_basemaps"]([manual])
            cfg2 = module["tak_map_config"]()
            manual_public = next(b for b in cfg2["basemaps"] if b.get("managementType") == "custom")
            assert manual_public["url"].startswith("/api/tak-map/custom-basemap-tile/"), manual_public

            meta = cfg2["composite_basemaps"]
            assert meta["version"] == "i517", meta
            assert meta["delivery_path"] == "browser-direct-base-provider-plus-gateway-overlay", meta
            assert meta["client_side_composition"] is True, meta
            assert meta["server_side_composition_for_tak_map"] is False, meta
            assert meta["server_composite_compatibility_for_atak"] is True, meta
            assert meta["dynamic_overlay_freshness_seconds"] == 600, meta
            assert meta["base_cache_seconds"] == 30 * 24 * 60 * 60, meta

            html = module["TAK_MAP_HTML"]
            for token in (
                "takMapSplitCompositeBasemapsV508",
                "TakMapCompositePerformanceV508",
                "takMapCreateOnlineLayerV476=create",
                "L.layerGroup([base,overlay])",
                "direct-base-plus-gateway-overlay",
                "takMapBasemapManagementV506",
                "Manage Basemaps",
                "1.3.0-i537",
                ">i537<",
            ):
                assert token in html, token

            print("TAK Map i508 split-layer composite basemap performance test passed")
            print(json.dumps({
                "catalog": GatewayFixture.counts,
                "gateway_imports": len(gateway_rows),
                "delivery": meta["delivery_path"],
                "manual_proxy_preserved": True,
            }, sort_keys=True))
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=3)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
