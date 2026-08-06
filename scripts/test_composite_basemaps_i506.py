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
    ("tg-imagery-goes18", "TG-ESRI-Img+GOES-18", "GOES-18 Pacific"),
    ("tg-street-goes18", "TG-ESRI-Strt+GOES-18", "GOES-18 Pacific"),
    ("tg-imagery-goes19", "TG-ESRI-Img+GOES-19", "GOES-19 Atlantic"),
    ("tg-street-goes19", "TG-ESRI-Strt+GOES-19", "GOES-19 Atlantic"),
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

    def _bytes(self, status: int, raw: bytes, ctype: str, headers=None):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        host = f"http://127.0.0.1:{self.server.server_address[1]}"
        if self.path == "/basemaps/catalog.json":
            type(self).counts["catalog"] += 1
            rows = [
                {"id": bid, "name": name, "group": "TAK Gateway Composite", "xml_url": f"/basemaps/xml/{bid}.xml"}
                for bid, name, _source in CATALOG_ROWS
            ]
            raw = json.dumps({"version": "fixture", "basemaps": rows}).encode()
            return self._bytes(200, raw, "application/json")
        if self.path.startswith("/basemaps/xml/") and self.path.endswith(".xml"):
            bid = unquote(self.path.rsplit("/", 1)[-1][:-4])
            match = next((row for row in CATALOG_ROWS if row[0] == bid), None)
            if match:
                type(self).counts["xml"] += 1
                raw = XML_TEMPLATE.format(
                    name=match[1],
                    url=f"{host}/tiles/{bid}/{{$z}}/{{$x}}/{{$y}}.png",
                ).encode()
                return self._bytes(200, raw, "application/xml")
        if self.path == "/tiles/tg-imagery-rainviewer/4/2/6.png":
            type(self).counts["tile"] += 1
            raw = b"\x89PNG\r\n\x1a\nI506-COMPOSITE-TILE"
            return self._bytes(200, raw, "image/png", {
                "Cache-Control": "public, max-age=60",
                "ETag": '"i506-tile"',
                "Expires": "Mon, 20 Jul 2026 20:40:00 GMT",
            })
        self.send_response(404)
        self.end_headers()


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="tak-map-i506-") as td:
        os.environ["TAK_DASHBOARD_DATA_DIR"] = td
        os.environ["TAK_MAP_GATEWAY_BASEMAP_TIMEOUT"] = "5"
        module = runpy.run_path(str(ROOT / "tak_dashboard.py"), run_name="tak_dashboard_i506_test")

        server = ThreadingHTTPServer(("127.0.0.1", 0), GatewayFixture)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_address[1]}"
        os.environ["TAK_MAP_GATEWAY_BASEMAP_URL"] = base
        try:
            result = module["_i506_import_gateway_basemaps"]()
            assert result["ok"] is True, result
            assert len(result["imported"]) == len(CATALOG_ROWS), result
            assert result["catalog_source"].endswith("/basemaps/catalog.json"), result
            assert result["catalog_entries"] == len(CATALOG_ROWS), result
            assert GatewayFixture.counts["catalog"] == 1, GatewayFixture.counts
            assert GatewayFixture.counts["xml"] == len(CATALOG_ROWS), GatewayFixture.counts

            stored_file = Path(module["TAK_MAP_CUSTOM_BASEMAPS_FILE"])
            stored = json.loads(stored_file.read_text())
            assert stored["version"] == "i506", stored
            assert len(stored["basemaps"]) == len(CATALOG_ROWS), stored
            assert all(x.get("gateway_catalog_source", "").endswith("catalog.json") for x in stored["basemaps"]), stored

            cfg = module["tak_map_config"]()
            assert cfg["tak_map_iteration"] == "i506", cfg.get("tak_map_iteration")
            custom = [b for b in cfg["basemaps"] if b.get("importedBasemap")]
            assert len(custom) == len(CATALOG_ROWS), custom
            assert {b["managementSource"] for b in custom} == {
                "NOAA Radar", "RainViewer", "NASA IMERG", "GOES-18 Pacific", "GOES-19 Atlantic"
            }, custom
            assert all(b["managementType"] == "gateway" for b in custom), custom
            assert all(b["precacheAllowed"] is False for b in custom), custom
            assert all(b["url"].startswith("/api/tak-map/custom-basemap-tile/") for b in custom), custom
            assert all("upstream_url" not in b for b in custom), custom

            rain = next(x for x in stored["basemaps"] if "rainviewer" in x["upstream_url"] and "imagery" in x["upstream_url"])
            upstream = module["_i505_expand_tile_url"](rain["upstream_url"], 4, 2, 6)
            before = GatewayFixture.counts["tile"]
            status, body, headers = module["_i505_upstream_tile"](upstream, {})
            assert status == 200 and body.endswith(b"I506-COMPOSITE-TILE"), (status, body)
            assert headers["Cache-Control"] == "public, max-age=60", headers
            assert headers["ETag"] == '"i506-tile"', headers
            assert GatewayFixture.counts["tile"] == before + 1, GatewayFixture.counts
            module["_i505_upstream_tile"](upstream, {})
            assert GatewayFixture.counts["tile"] == before + 2, GatewayFixture.counts

            # A manual XML remains after bulk-removing Gateway imports.
            manual = module["_i505_parse_basemap_xml"](
                XML_TEMPLATE.format(name="Manual Test", url="https://example.invalid/{z}/{x}/{y}.png").encode(),
                "manual.xml", "manual"
            )
            module["_i505_upsert_custom_basemaps"]([manual])
            deleted = module["_i506_bulk_delete"]("gateway")
            assert deleted["ok"] and deleted["removed_count"] == len(CATALOG_ROWS), deleted
            remaining = module["_i505_load_custom_basemaps"]()
            assert len(remaining) == 1 and remaining[0]["source_kind"] == "manual", remaining
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=3)

        # Existing Gateways without a catalog are covered by known-ID aliases.
        fallback_ids = {
            "tg-imagery-radar": "TG-ESRI-Img+NOAA",
            "tg-street-radar": "TG-ESRI-Strt+NOAA",
            "tg-rainviewer-esri-img": "TG-ESRI-Img+RainViewer",
            "tg-rainviewer-esri-street": "TG-ESRI-Strt+RainViewer",
            "tg-imerg-esri-img": "TG-ESRI-Img+IMERG",
            "tg-imerg-esri-street": "TG-ESRI-Strt+IMERG",
            "tg-goes18-esri-img": "TG-ESRI-Img+GOES-18",
            "tg-goes18-esri-street": "TG-ESRI-Strt+GOES-18",
            "tg-goes19-esri-img": "TG-ESRI-Img+GOES-19",
            "tg-goes19-esri-street": "TG-ESRI-Strt+GOES-19",
        }
        globals506 = module["_i506_import_gateway_basemaps"].__globals__
        globals506["_i506_fetch_gateway_json"] = lambda _url: (_ for _ in ()).throw(RuntimeError("no catalog"))
        def fallback_xml(url):
            bid = unquote(url.rsplit("/", 1)[-1].removesuffix(".xml"))
            if bid not in fallback_ids:
                raise RuntimeError("not found")
            return XML_TEMPLATE.format(name=fallback_ids[bid], url=f"{base}/tiles/{bid}/{{$z}}/{{$x}}/{{$y}}.png").encode()
        globals506["_i505_fetch_gateway_xml"] = fallback_xml
        module["_i506_save_custom_basemaps"]([])
        fallback = module["_i506_import_gateway_basemaps"]()
        assert fallback["ok"] and len(fallback["imported"]) == 10, fallback
        assert fallback["catalog_source"] == "", fallback
        assert set(fallback["composite_families"]) == {
            "noaa-imagery", "noaa-street", "rainviewer-imagery", "rainviewer-street",
            "imerg-imagery", "imerg-street", "goes18-imagery", "goes18-street",
            "goes19-imagery", "goes19-street",
        }, fallback

        html = module["TAK_MAP_HTML"]
        for token in (
            "takMapBasemapManagementV506", "basemapManagerBackdropV506", "basemapSummaryV506",
            "Manage Basemaps", "reliefOverlayButtonV506", "Refresh Gateway Catalog",
            "Remove All Gateway Imports", "1.3.0-i506", ">i506<",
        ):
            assert token in html, token
        assert "#customBasemapRowsV505{display:none!important}" in html
        meta = module["tak_map_config"]()["composite_basemaps"]
        assert meta["gateway_import_mode"] == "catalog-first-with-known-id-fallback", meta
        assert meta["single_upstream_tile_request"] is True, meta
        assert meta["additional_gateway_composition"] is False, meta
        assert meta["client_side_composition"] is False, meta
        assert meta["tak_map_tile_cache"] is False, meta

        print("TAK Map i506 composite catalog/import/management server test passed")
        print(json.dumps({
            "catalog": GatewayFixture.counts,
            "imported": len(CATALOG_ROWS),
            "sources": sorted({b["managementSource"] for b in custom}),
            "proxy": meta["proxy_mode"],
        }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
