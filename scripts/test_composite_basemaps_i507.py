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
    ("tg-imagery-radar", "TG-ESRI-Img+NOAA", "NOAA Radar"),
    ("tg-street-radar", "TG-ESRI-Strt+NOAA", "NOAA Radar"),
    ("tg-imagery-rainviewer", "TG-ESRI-Img+RainViewer", "RainViewer"),
    ("tg-street-rainviewer", "TG-ESRI-Strt+RainViewer", "RainViewer"),
    ("tg-imagery-imerg", "TG-ESRI-Img+IMERG", "NASA IMERG"),
    ("tg-street-imerg", "TG-ESRI-Strt+IMERG", "NASA IMERG"),
    ("tg-imagery-goes18", "TG-ESRI-Img+GOES18-Pacific", "GOES-18 Pacific"),
    ("tg-street-goes18", "TG-ESRI-Strt+GOES18-Pacific", "GOES-18 Pacific"),
    ("tg-imagery-goes19", "TG-ESRI-Img+GOES19-Atlantic", "GOES-19 Atlantic"),
    ("tg-street-goes19", "TG-ESRI-Strt+GOES19-Atlantic", "GOES-19 Atlantic"),
]

XML_TEMPLATE = '''<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
  <name>{name}</name>
  <minZoom>2</minZoom>
  <maxZoom>22</maxZoom>
  <tileType>PNG</tileType>
  <tileUpdate>None</tileUpdate>
  <ignoreErrors>true</ignoreErrors>
  <url><![CDATA[{url}]]></url>
  <backgroundColor>#000000</backgroundColor>
</customMapSource>
'''


class GatewayFixture(BaseHTTPRequestHandler):
    counts = {"catalog": 0, "xml": 0, "tile": 0}

    def log_message(self, *_args):
        return

    def _bytes(self, status: int, raw: bytes, ctype: str):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        host = f"http://127.0.0.1:{self.server.server_address[1]}"
        if self.path in ("/basemaps/catalog", "/basemaps/catalog.json"):
            type(self).counts["catalog"] += 1
            rows = [
                {
                    "id": bid,
                    "name": name,
                    "group": "TAK Gateway Composite",
                    "xml_url": f"{host}/basemaps/xml/{bid}.xml",
                }
                for bid, name, _source in CATALOG_ROWS
            ]
            return self._bytes(200, json.dumps({"ok": True, "basemaps": rows}).encode(), "application/json")
        if self.path.startswith("/basemaps/xml/") and self.path.endswith(".xml"):
            bid = unquote(self.path.rsplit("/", 1)[-1][:-4])
            match = next((row for row in CATALOG_ROWS if row[0] == bid), None)
            if match:
                type(self).counts["xml"] += 1
                return self._bytes(
                    200,
                    XML_TEMPLATE.format(
                        name=match[1],
                        url=f"{host}/tiles/{bid}/{{$z}}/{{$x}}/{{$y}}.png",
                    ).encode(),
                    "application/xml",
                )
        if self.path.startswith("/tiles/"):
            type(self).counts["tile"] += 1
            return self._bytes(200, b"\x89PNG\r\n\x1a\nI507-DIRECT-TILE", "image/png")
        self.send_response(404)
        self.end_headers()


def main() -> int:
    GatewayFixture.counts = {"catalog": 0, "xml": 0, "tile": 0}
    server = ThreadingHTTPServer(("127.0.0.1", 0), GatewayFixture)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"

    with tempfile.TemporaryDirectory(prefix="tak-map-i507-") as td:
        os.environ["TAK_DASHBOARD_DATA_DIR"] = td
        os.environ["TAK_MAP_GATEWAY_BASEMAP_URL"] = base
        os.environ["TAK_MAP_GATEWAY_BASEMAP_TIMEOUT"] = "5"
        os.environ["TAK_MAP_GATEWAY_DIRECT_BASEMAPS"] = "true"
        os.environ["TAK_MAP_GATEWAY_CA_CERT"] = str(Path(td) / "missing-ca.crt")
        module = runpy.run_path(str(ROOT / "tak_dashboard.py"), run_name="tak_dashboard_i507_test")
        try:
            result = module["_i506_import_gateway_basemaps"]()
            assert result["ok"] is True, result
            assert result["version"] == "i507", result
            assert len(result["imported"]) == len(CATALOG_ROWS), result
            assert result["catalog_source"].endswith("/basemaps/catalog.json"), result
            assert result["catalog_entries"] == len(CATALOG_ROWS), result
            assert GatewayFixture.counts["catalog"] == 1, GatewayFixture.counts
            assert GatewayFixture.counts["xml"] == len(CATALOG_ROWS), GatewayFixture.counts
            # Import reads definitions only. It must never relay an interactive tile.
            assert GatewayFixture.counts["tile"] == 0, GatewayFixture.counts

            stored_file = Path(module["TAK_MAP_CUSTOM_BASEMAPS_FILE"])
            stored = json.loads(stored_file.read_text())
            assert stored["version"] == "i507", stored
            assert len(stored["basemaps"]) == len(CATALOG_ROWS), stored

            cfg = module["tak_map_config"]()
            assert cfg["tak_map_iteration"] == "i507", cfg.get("tak_map_iteration")
            custom = [b for b in cfg["basemaps"] if b.get("importedBasemap")]
            gateway = [b for b in custom if b.get("managementType") == "gateway"]
            assert len(gateway) == len(CATALOG_ROWS), gateway
            assert {b["managementSource"] for b in gateway} == {
                "NOAA Radar", "RainViewer", "NASA IMERG", "GOES-18 Pacific", "GOES-19 Atlantic"
            }, gateway
            assert all(b["url"].startswith(base + "/tiles/") for b in gateway), gateway
            assert all(b.get("directGateway") is True for b in gateway), gateway
            assert all(b.get("directBrowserRequest") is True for b in gateway), gateway
            assert all(b.get("clientCertificateRequired") is False for b in gateway), gateway
            assert all(b.get("serverCertificateTrustRequired") is True for b in gateway), gateway
            assert all("/api/tak-map/custom-basemap-tile/" not in b["url"] for b in gateway), gateway
            assert all("upstream_url" not in b for b in gateway), gateway

            # Existing i505/i506 rows that contain the legacy port-8090 origin are
            # rewritten to the currently enrolled secure Gateway base.
            legacy = module["_i507_direct_gateway_url"](
                "http://old-gateway.example:8090/tiles/esri-imagery-radar/{z}/{x}/{y}.png?legacy=1"
            )
            assert legacy == base + "/tiles/esri-imagery-radar/{z}/{x}/{y}.png?legacy=1", legacy

            # Manually imported XML remains on the compatibility proxy because it
            # may point at arbitrary external hosts and is not a Gateway resource.
            manual = module["_i505_parse_basemap_xml"](
                XML_TEMPLATE.format(name="Manual Test", url="https://example.invalid/{z}/{x}/{y}.png").encode(),
                "manual.xml",
                "manual",
            )
            module["_i505_upsert_custom_basemaps"]([manual])
            cfg2 = module["tak_map_config"]()
            manual_public = next(b for b in cfg2["basemaps"] if b.get("managementType") == "custom")
            assert manual_public["url"].startswith("/api/tak-map/custom-basemap-tile/"), manual_public

            meta = cfg2["composite_basemaps"]
            assert meta["version"] == "i507", meta
            assert meta["delivery_path"] == "browser-direct-to-tak-gateway", meta
            assert meta["direct_browser_requests"] is True, meta
            assert meta["tak_map_python_tile_proxy_for_gateway"] is False, meta
            assert meta["tak_map_nginx_tile_relay_for_gateway"] is False, meta
            assert meta["browser_client_certificate_required"] is False, meta
            assert meta["gateway_server_certificate_trust_required"] is True, meta
            assert meta["manual_custom_xml_proxy_preserved"] is True, meta
            assert meta["proxy_mode"] == "direct-browser-to-tak-gateway-https", meta

            enrollment = cfg2["tak_map_enrollment"]
            assert enrollment["role"] == "tak-map-service", enrollment
            assert enrollment["direct_basemaps"] is True, enrollment

            html = module["TAK_MAP_HTML"]
            for token in (
                "takMapDirectGatewayBasemapsV507",
                "TakMapDirectGatewayBasemapsV507",
                "takMapBasemapManagementV506",
                "Manage Basemaps",
                "1.3.0-i507",
                ">i507<",
            ):
                assert token in html, token

            print("TAK Map i507 direct Gateway basemap server test passed")
            print(json.dumps({
                "catalog": GatewayFixture.counts,
                "gateway_imports": len(gateway),
                "delivery": meta["delivery_path"],
                "manual_proxy": manual_public["url"].split("/")[3],
            }, sort_keys=True))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
