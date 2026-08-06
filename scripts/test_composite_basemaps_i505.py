#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import runpy
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

XML_TEMPLATE = '''<?xml version="1.0" encoding="UTF-8"?>
<customMapSource>
  <name>{name}</name>
  <minZoom>3</minZoom>
  <maxZoom>23</maxZoom>
  <tileType>PNG</tileType>
  <tileUpdate>None</tileUpdate>
  <ignoreErrors>true</ignoreErrors>
  <url><![CDATA[{url}]]></url>
  <backgroundColor>#000000</backgroundColor>
</customMapSource>
'''

class GatewayFixture(BaseHTTPRequestHandler):
    counts = {"xml": 0, "tile": 0}

    def log_message(self, *_args):
        return

    def do_GET(self):
        host = f"http://127.0.0.1:{self.server.server_address[1]}"
        if self.path == "/basemaps/xml/tg-imagery-radar.xml":
            type(self).counts["xml"] += 1
            raw = XML_TEMPLATE.format(
                name="TG-ESRI-Img+Radar",
                url=host + "/tiles/esri-imagery-radar/{$z}/{$x}/{$y}.png",
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/xml")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers(); self.wfile.write(raw); return
        if self.path == "/basemaps/xml/tg-street-radar.xml":
            type(self).counts["xml"] += 1
            raw = XML_TEMPLATE.format(
                name="TG-ESRI-Strt+Radar",
                url=host + "/tiles/esri-street-radar/{$z}/{$x}/{$y}.png",
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/xml")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers(); self.wfile.write(raw); return
        if self.path in (
            "/tiles/esri-imagery-radar/4/2/6.png",
            "/tiles/esri-street-radar/4/2/6.png",
        ):
            type(self).counts["tile"] += 1
            raw = b"\x89PNG\r\n\x1a\nI505-COMPOSITE-TILE"
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Cache-Control", "public, max-age=60")
            self.send_header("ETag", '"i505-tile"')
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers(); self.wfile.write(raw); return
        self.send_response(404); self.end_headers()


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="tak-map-i505-") as td:
        os.environ["TAK_DASHBOARD_DATA_DIR"] = td
        os.environ["TAK_MAP_GATEWAY_BASEMAP_TIMEOUT"] = "5"
        module = runpy.run_path(str(ROOT / "tak_dashboard.py"), run_name="tak_dashboard_i505_test")

        sample = XML_TEMPLATE.format(
            name="NOAA Radar over Esri Imagery - TAK Gateway",
            url="http://192.0.2.101:8097/weather/noaa/composite/imagery/{$z}/{$x}/{$y}.png",
        ).encode()
        parsed = module["_i505_parse_basemap_xml"](sample, "imagery.xml", "manual")
        assert parsed["label"] == "NOAA Radar over Esri Imagery - TAK Gateway", parsed
        assert parsed["upstream_url"].endswith("/imagery/{z}/{x}/{y}.png"), parsed
        assert parsed["minZoom"] == 3 and parsed["maxZoom"] == 23, parsed
        assert parsed["tileType"] == "png" and parsed["ignoreErrors"] is True, parsed
        assert parsed["backgroundColor"] == "#000000", parsed
        assert parsed["group"] == "TAK Gateway Composite", parsed
        assert parsed["precache_allowed"] is False, parsed

        server = ThreadingHTTPServer(("127.0.0.1", 0), GatewayFixture)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_address[1]}"
        os.environ["TAK_MAP_GATEWAY_BASEMAP_URL"] = base
        try:
            result = module["_i505_import_gateway_basemaps"]()
            assert result["ok"] is True, result
            assert len(result["imported"]) == 2 and not result["errors"], result
            assert GatewayFixture.counts["xml"] == 2, GatewayFixture.counts

            stored_file = Path(module["TAK_MAP_CUSTOM_BASEMAPS_FILE"])
            assert stored_file.is_file(), stored_file
            stored = json.loads(stored_file.read_text())
            assert stored["version"] == "i506" and len(stored["basemaps"]) == 2, stored

            cfg = module["tak_map_config"]()
            custom = [b for b in cfg["basemaps"] if b.get("importedBasemap")]
            assert len(custom) == 2, custom
            assert all(b["group"] == "TAK Gateway Composite" for b in custom), custom
            assert all(b["url"].startswith("/api/tak-map/custom-basemap-tile/") for b in custom), custom
            assert all("upstream_url" not in b for b in custom), custom
            meta = cfg["composite_basemaps"]
            assert meta["single_upstream_tile_request"] is True, meta
            assert meta["client_side_composition"] is False, meta
            assert meta["additional_gateway_composition"] is False, meta
            assert meta["tak_map_tile_cache"] is False and meta["background_precache"] is False, meta

            imagery = next(x for x in stored["basemaps"] if "imagery" in x["upstream_url"])
            upstream = module["_i505_expand_tile_url"](imagery["upstream_url"], 4, 2, 6)
            before = GatewayFixture.counts["tile"]
            status, body, headers = module["_i505_upstream_tile"](upstream, {})
            assert status == 200 and body.endswith(b"I505-COMPOSITE-TILE"), (status, body)
            assert headers["Cache-Control"] == "public, max-age=60", headers
            assert headers["ETag"] == '"i505-tile"', headers
            assert GatewayFixture.counts["tile"] == before + 1, GatewayFixture.counts
            # A second proxy invocation means one additional upstream tile request;
            # TAK Map intentionally has no second application-level tile cache.
            module["_i505_upstream_tile"](upstream, {})
            assert GatewayFixture.counts["tile"] == before + 2, GatewayFixture.counts
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=3)

        html = module["TAK_MAP_HTML"]
        assert "takMapCompositeBasemapsV505" in html
        assert "Import Gateway" in html
        assert "customBasemapRowsV505" in html
        assert "TAK Gateway Composite" in html
        assert "1.3.0-i506" in html and ">i506<" in html

        print("TAK Map legacy i505 composite basemap compatibility test passed under i506")
        print(json.dumps({
            "parsed": {k: parsed[k] for k in ("label", "minZoom", "maxZoom", "tileType", "group")},
            "gatewayRequests": GatewayFixture.counts,
            "stored": len(stored["basemaps"]),
            "public": len(custom),
            "proxy": meta["proxy_mode"],
        }, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
