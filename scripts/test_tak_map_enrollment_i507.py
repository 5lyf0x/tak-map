#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import io
import json
import os
import runpy
import ssl
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd):
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode:
        raise RuntimeError(proc.stderr or proc.stdout)


def make_pki(base: Path):
    ca_key, ca_crt = base / "ca.key", base / "ca.crt"
    server_key, server_csr, server_crt, server_ext = base / "server.key", base / "server.csr", base / "server.crt", base / "server.ext"
    client_key, client_csr, client_crt, client_ext = base / "client.key", base / "client.csr", base / "client.crt", base / "client.ext"
    run(["openssl", "genrsa", "-out", str(ca_key), "2048"])
    run(["openssl", "req", "-x509", "-new", "-key", str(ca_key), "-sha256", "-days", "2", "-subj", "/CN=Test CA", "-addext", "basicConstraints=critical,CA:TRUE", "-addext", "keyUsage=critical,keyCertSign,cRLSign", "-out", str(ca_crt)])
    run(["openssl", "genrsa", "-out", str(server_key), "2048"])
    run(["openssl", "req", "-new", "-key", str(server_key), "-out", str(server_csr), "-subj", "/CN=127.0.0.1"])
    server_ext.write_text("subjectAltName=IP:127.0.0.1\nextendedKeyUsage=serverAuth\nkeyUsage=digitalSignature,keyEncipherment\n")
    run(["openssl", "x509", "-req", "-in", str(server_csr), "-CA", str(ca_crt), "-CAkey", str(ca_key), "-CAcreateserial", "-out", str(server_crt), "-days", "2", "-sha256", "-extfile", str(server_ext)])
    run(["openssl", "genrsa", "-out", str(client_key), "2048"])
    run(["openssl", "req", "-new", "-key", str(client_key), "-out", str(client_csr), "-subj", "/CN=tak-map-test"])
    client_ext.write_text("extendedKeyUsage=clientAuth\nkeyUsage=digitalSignature,keyEncipherment\n")
    run(["openssl", "x509", "-req", "-in", str(client_csr), "-CA", str(ca_crt), "-CAkey", str(ca_key), "-CAcreateserial", "-out", str(client_crt), "-days", "2", "-sha256", "-extfile", str(client_ext)])
    return ca_crt, server_crt, server_key, client_crt, client_key


class Fixture(BaseHTTPRequestHandler):
    protected_peer_certs = 0
    public_peer_certs = 0

    def log_message(self, *_args):
        return

    def peer_present(self):
        try:
            return bool(self.connection.getpeercert())
        except Exception:
            return False

    def reply(self, payload, ctype="application/json"):
        raw = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path.startswith("/api/replay/v1/") or self.path.startswith("/api/external-sources/v1/"):
            if not self.peer_present():
                self.send_response(403); self.end_headers(); return
            type(self).protected_peer_certs += 1
            if self.path.endswith("/health"):
                self.reply({"ok": True, "service": "test"})
            elif self.path.endswith("/capabilities"):
                self.reply({"ok": True, "replay": True})
            else:
                self.send_response(404); self.end_headers()
            return
        if self.path == "/basemaps/catalog":
            if self.peer_present():
                type(self).public_peer_certs += 1
            base = f"https://127.0.0.1:{self.server.server_address[1]}"
            self.reply({"ok": True, "basemaps": [{"id": "tg-imagery-radar", "xml_url": base + "/basemaps/xml/tg-imagery-radar.xml"}]})
            return
        if self.path == "/basemaps/xml/tg-imagery-radar.xml":
            if self.peer_present():
                type(self).public_peer_certs += 1
            self.reply(b'<?xml version="1.0"?><customMapSource><name>Test</name><url>https://127.0.0.1/tiles/x/{$z}/{$x}/{$y}.png</url></customMapSource>', "application/xml")
            return
        self.send_response(404); self.end_headers()


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="tak-map-enroll-i507-") as td:
        base = Path(td)
        pki = base / "pki"; pki.mkdir()
        ca_crt, server_crt, server_key, client_crt, client_key = make_pki(pki)
        server = ThreadingHTTPServer(("127.0.0.1", 0), Fixture)
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(str(server_crt), str(server_key))
        ctx.load_verify_locations(cafile=str(ca_crt))
        ctx.verify_mode = ssl.CERT_OPTIONAL
        server.socket = ctx.wrap_socket(server.socket, server_side=True)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        gateway = f"https://127.0.0.1:{server.server_address[1]}"

        source = base / "source"; source.mkdir()
        (source / "client.crt").write_bytes(client_crt.read_bytes())
        (source / "client.key").write_bytes(client_key.read_bytes())
        (source / "ca.crt").write_bytes(ca_crt.read_bytes())
        (source / "connection.json").write_text(json.dumps({
            "schema_version": 1,
            "name": "tak-map-test",
            "instance_id": "tak-map-test",
            "role": "tak-map-service",
            "scope": "tak-map-service",
            "gateway_url": gateway,
            "protected_endpoints": {
                "replay_api_base": gateway + "/api/replay/v1",
                "gateway_data_api_base": gateway + "/api/external-sources/v1",
            },
            "public_endpoints": {
                "basemap_catalog_url": gateway + "/basemaps/catalog",
                "basemap_xml_base_url": gateway + "/basemaps/xml",
                "basemap_tile_base_url": gateway + "/tiles",
            },
            "capabilities": {"future_tak_map_services": True, "direct_browser_basemaps": True},
        }))

        mod = runpy.run_path(str(ROOT / "scripts" / "tak-map-enroll"), run_name="tak_map_enroll_i507_test")
        runtime = mod["main"].__globals__
        runtime["ENV"] = base / "tak-map.env"
        runtime["DEST"] = base / "etc-tak-map"
        runtime["MANIFEST"] = runtime["DEST"] / "enrollment.json"
        runtime["SERVICE"] = "tak-map-test"
        old_argv = sys.argv
        sys.argv = ["tak-map-enroll", "--source-dir", str(source), "--no-restart"]
        out = io.StringIO()
        try:
            with contextlib.redirect_stdout(out):
                mod["main"]()
        finally:
            sys.argv = old_argv
            server.shutdown(); server.server_close(); thread.join(timeout=3)

        result = json.loads(out.getvalue())
        assert result["ok"] is True, result
        assert result["role"] == "tak-map-service", result
        assert result["direct_browser_basemaps"] is True, result
        assert result["basemap_catalog_count"] == 1, result
        assert result["basemap_xml_validation"]["custom_map_source"] is True, result
        assert Fixture.protected_peer_certs >= 3, Fixture.protected_peer_certs
        # Public catalog/XML verification deliberately uses no client cert.
        assert Fixture.public_peer_certs == 0, Fixture.public_peer_certs

        env = runtime["ENV"].read_text()
        for token in (
            f"TAK_MAP_GATEWAY_URL={gateway}",
            "TAK_MAP_SERVICE_CLIENT_CERT=",
            "TAK_MAP_ENROLLMENT_MANIFEST=",
            f"TAK_MAP_GATEWAY_BASEMAP_URL={gateway}",
            "TAK_MAP_GATEWAY_BASEMAP_PORT=9443",
            "TAK_MAP_GATEWAY_BASEMAP_SCHEME=https",
            "TAK_MAP_GATEWAY_DIRECT_BASEMAPS=true",
        ):
            assert token in env, token
        manifest = json.loads(runtime["MANIFEST"].read_text())
        assert manifest["role"] == "tak-map-service", manifest
        for name in ("service-client.crt", "service-client.key", "gateway-ca.crt", "replay-client.crt", "replay-client.key", "replay-ca.crt"):
            assert (runtime["DEST"] / name).is_file(), name

        print("TAK Map i507 enrollment receiver protected/public TLS test passed")
        print(json.dumps({"protected_requests": Fixture.protected_peer_certs, "public_client_cert_requests": Fixture.public_peer_certs}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
