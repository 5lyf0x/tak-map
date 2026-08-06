#!/usr/bin/env python3
"""TAK Map i493 OTS PostgreSQL URL compatibility and auth redaction tests."""
from __future__ import annotations

import contextlib
import inspect
import io
import json
import os
import runpy
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import quote

os.environ.setdefault("TAK_MAP_TEST_SKIP_ADSB_WARMUP", "1")
# install.sh persists this detected OpenTAKServer interpreter in production.
os.environ["TAK_DASH_OTS_PYTHON"] = sys.executable
os.environ.pop("TAK_DASH_OTS_SQLALCHEMY_PYTHON", None)

from sqlalchemy.engine import make_url

NS = runpy.run_path("tak_dashboard.py", run_name="tak_map_i493_pg_uri_test")
PARSE = NS["_pg_parse_uri"]
PARSE_ERROR = NS["_OTS_PG_PARSE_ERROR"]
QUERY_ERROR = NS["_OTS_PG_QUERY_ERROR"]
G = PARSE.__globals__


def expected(uri: str) -> dict[str, str]:
    url = make_url(uri)
    return {
        "host": str(url.host or "127.0.0.1"),
        "port": str(url.port or 5432),
        "user": str(url.username or ""),
        "password": str(url.password or ""),
        "database": str(url.database or "ots"),
        "drivername": str(url.drivername or ""),
    }


def assert_matches(uri: str) -> dict[str, str]:
    got = PARSE(uri)
    exp = expected(uri)
    assert got == exp, (uri.split(":", 1)[0], got, exp)
    return got


# _candidate_ots_pg_uris must preserve each accepted SQLAlchemy PostgreSQL
# driver prefix verbatim rather than rewriting it before parsing.
prefixes = (
    "postgresql",
    "postgres",
    "postgresql+psycopg",
    "postgresql+psycopg2",
    "postgresql+pg8000",
    "postgresql+asyncpg",
)
old_load = G["_load_ots_config_values"]
old_env = {k: os.environ.get(k) for k in (
    "TAK_DASH_OTS_POSTGRES_URI", "TAK_DASH_OTS_DB_URI", "SQLALCHEMY_DATABASE_URI"
)}
try:
    G["_load_ots_config_values"] = lambda: ({}, [])
    for key in old_env:
        os.environ.pop(key, None)
    raw_candidates = [f"{prefix}://ots:secret@127.0.0.1/ots" for prefix in prefixes]
    os.environ["TAK_DASH_OTS_POSTGRES_URI"] = raw_candidates[0]
    os.environ["TAK_DASH_OTS_DB_URI"] = raw_candidates[1]
    os.environ["SQLALCHEMY_DATABASE_URI"] = raw_candidates[2]
    uris, errors = G["_candidate_ots_pg_uris"]()
    assert errors == [] and uris == raw_candidates[:3], (uris, errors)
    for uri in raw_candidates:
        # SQLAlchemy itself recognizes the URL structure without loading the dialect.
        assert make_url(uri).drivername == uri.split(":", 1)[0]
finally:
    G["_load_ots_config_values"] = old_load
    for key, value in old_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value

# Actual TAK Map parsing through the detected OTS interpreter: reserved
# characters, supported drivers, IPv4, IPv6, and omitted ports.
reserved = "#?/:=+&%@"
encoded = quote(reserved, safe="")
uri_encoded = f"postgresql+psycopg2://ots:{encoded}@192.0.2.10:6543/ots"
cfg_encoded = assert_matches(uri_encoded)
assert cfg_encoded["password"] == reserved
assert cfg_encoded["host"] == "192.0.2.10" and cfg_encoded["port"] == "6543"

uri_ipv6 = "postgresql+psycopg://ots:secret@[2001:db8::5]:6543/ots"
assert_matches(uri_ipv6)

uri_omitted = "postgres://ots:secret@db.example/ots"
assert_matches(uri_omitted)
assert PARSE(uri_omitted)["port"] == "5432"  # cached second access

# Existing raw strings accepted by the installed SQLAlchemy parser must be
# interpreted identically. Literal @ remains a delimiter and must be %40 when
# the intended password contains @.
raw_compatible = "postgresql://ots:pa#?/:=+&%ss@127.0.0.1:5432/ots"
assert_matches(raw_compatible)
raw_at_uri = "postgresql://ots:pa@ss@127.0.0.1:5432/ots"
raw_at = assert_matches(raw_at_uri)
assert raw_at["password"] != "pa@ss"
encoded_at_uri = "postgresql://ots:pa%40ss@127.0.0.1:5432/ots"
assert assert_matches(encoded_at_uri)["password"] == "pa@ss"

# Continue reading OTS config.yml directly. The explicit TAK Map URI remains
# optional and, when provided, precedes the config value without rewriting it.
with tempfile.TemporaryDirectory() as td:
    cfg_path = Path(td) / "config.yml"
    cfg_uri = f"postgresql+psycopg://ots:{encoded}@127.0.0.1/ots"
    cfg_path.write_text(f'SQLALCHEMY_DATABASE_URI: "{cfg_uri}"\n', encoding="utf-8")
    old_paths = G["_candidate_ots_config_paths"]
    old_env2 = {k: os.environ.get(k) for k in old_env}
    try:
        G["_candidate_ots_config_paths"] = lambda: [cfg_path]
        for key in old_env2:
            os.environ.pop(key, None)
        uris, errors = G["_candidate_ots_pg_uris"]()
        assert errors == [] and uris == [cfg_uri], (uris, errors)
        override = "postgresql://override:secret@127.0.0.1/ots"
        os.environ["TAK_DASH_OTS_POSTGRES_URI"] = override
        uris, _ = G["_candidate_ots_pg_uris"]()
        assert uris == [override, cfg_uri], uris
    finally:
        G["_candidate_ots_config_paths"] = old_paths
        for key, value in old_env2.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

# Malformed ports are rejected before psql authentication and emit only the
# fixed sanitized message. Failure caching also prevents repeated helper churn.
bad_uri = "postgresql://ots:part-of-password@db.example:not-a-port/ots"
secret_fragments = ("ots", "part-of-password", bad_uri, "not-a-port")
stdout = io.StringIO()
stderr = io.StringIO()
with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
    try:
        PARSE(bad_uri)
    except ValueError as exc:
        assert str(exc) == PARSE_ERROR
    else:
        raise AssertionError("malformed port unexpectedly parsed")
assert not any(fragment in stdout.getvalue() + stderr.getvalue() for fragment in secret_fragments)

old_which = G["shutil"].which
old_run = G["subprocess"].run
try:
    G["shutil"].which = lambda _name: "/usr/bin/psql"
    rows, error = G["_pg_query"](bad_uri, "select 1")  # cached parse failure
    assert rows is None and error == PARSE_ERROR, (rows, error)
    assert not any(fragment in error for fragment in secret_fragments)

    # Use a previously parsed/cached valid URI so this mock exercises psql
    # redaction only, not the SQLAlchemy helper process.
    calls = []

    def failed_psql(cmd, **kwargs):
        calls.append((list(cmd), dict(kwargs)))
        return SimpleNamespace(
            returncode=2,
            stdout="",
            stderr=f'connection failed for user "{cfg_encoded["user"]}"; password={cfg_encoded["password"]}; uri={uri_encoded}',
        )

    G["subprocess"].run = failed_psql
    rows, error = G["_pg_query"](uri_encoded, "select 1")
    assert rows is None and error == QUERY_ERROR, (rows, error)
    for fragment in (cfg_encoded["user"], cfg_encoded["password"], uri_encoded):
        assert fragment not in error
    assert calls and cfg_encoded["password"] not in " ".join(calls[0][0])
    assert calls[0][1]["env"]["PGPASSWORD"] == cfg_encoded["password"]
finally:
    G["shutil"].which = old_which
    G["subprocess"].run = old_run

# Login flow remains unchanged for both successful PostgreSQL-backed paths:
# OTS /api/login plus DB role verification, and direct DB hash fallback.
auth = NS["authenticate_opentak_admin"]
AG = auth.__globals__
originals = {name: AG[name] for name in (
    "_candidate_ots_pg_uris", "_ots_api_password_valid",
    "_pg_verify_opentak_admin_role", "_pg_authenticate_opentak_admin",
)}
try:
    AG["_candidate_ots_pg_uris"] = lambda: ([uri_encoded], [])
    AG["_ots_api_password_valid"] = lambda _u, _p: (True, "accepted")
    AG["_pg_verify_opentak_admin_role"] = lambda _uri, _u: (True, "admin")
    ok, message = auth("administrator", "correct horse battery staple")
    assert ok is True and "verified" in message.lower(), (ok, message)

    AG["_ots_api_password_valid"] = lambda _u, _p: (False, "offline")
    AG["_pg_authenticate_opentak_admin"] = lambda _uri, _u, _p: (
        True, "OpenTAKServer admin verified from PostgreSQL database."
    )
    ok, message = auth("administrator", "correct horse battery staple")
    assert ok is True and "verified" in message.lower(), (ok, message)
finally:
    AG.update(originals)

# Static security contract: make_url is imported inside the detected OTS
# interpreter helper; the URI travels through stdin and urlparse is absent.
source = inspect.getsource(PARSE)
assert "from sqlalchemy.engine import make_url" in source
assert "input=payload" in source
assert "[str(py),'-c',helper]" in source
assert "urlparse(" not in source
assert "print(json.dumps({'status':'parse_error'}" in source
assert "_OTS_PG_PARSE_FAILURE_CACHE" in source

print("TAK Map i493 OTS SQLAlchemy URI compatibility, login flow, and credential redaction tests passed", flush=True)
print(json.dumps({
    "drivers_checked": list(prefixes),
    "reserved_characters": list(reserved),
    "ipv4": True,
    "ipv6": True,
    "omitted_port": True,
    "config_default": True,
    "override_optional": True,
    "login_api_path": True,
    "login_db_fallback": True,
    "credential_redaction": True,
}, sort_keys=True), flush=True)
os._exit(0)
