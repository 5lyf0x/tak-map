"""Read-only, fixed-provider NOAA MRMS historical radar observations for TAK Map i696.

Browser input is a catalog-issued opaque frame ID and validated XYZ only; the
browser cannot choose a time, raster, mosaic, URL, provider or geographic BBOX.
Existing i693 latest-radar endpoint is deliberately unaffected.
"""
from __future__ import annotations

from collections import OrderedDict
from datetime import datetime, timezone
import hashlib
import json
import math
import re
import secrets
import threading
import time
import urllib.parse

import tak_map_radar_i693 as radar

VERSION = '1.4.0-i696'
_HISTORY_LOCK = threading.RLock()
_REFRESH_LOCK = threading.Lock()
_SECRET = secrets.token_bytes(32)
_CATALOG = {'checked': 0.0, 'frames': [], 'extent': None, 'error': None}
_ALLOWED = {}  # exact opaque token -> strict-in-extent observation epoch-ms
_MAX_FRAMES = 48
_MAX_TILES = 96
_MAX_BYTES = 18 * 1024 * 1024
_TILE_TTL = 230
_TILE_CACHE = OrderedDict()
_TILE_BYTES = 0
_TILE_FLIGHTS = {}
_WINDOWS = (30, 60, 120, 240)
_JSON_MIMES = ('application/json', 'text/json', 'text/plain')
_TOKEN_RE = re.compile(r'h\d{13}_[0-9a-f]{16}\Z')


def _utc(ms):
    return datetime.fromtimestamp(ms / 1000, timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')


def _token(ms):
    digest = hashlib.sha256(_SECRET + str(ms).encode('ascii')).hexdigest()[:16]
    return 'h' + str(ms) + '_' + digest


def _json(url, limit=850_000):
    mime, raw = radar._request(url, limit, timeout=9)
    if mime not in _JSON_MIMES:
        raise radar.RadarError('history_json_type')
    try:
        result = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise radar.RadarError('history_json_invalid') from exc
    if not isinstance(result, dict) or result.get('error'):
        raise radar.RadarError('history_upstream_error')
    return result


def _fetch_catalog():
    metadata = _json(radar.PRIMARY + '?f=pjson')
    info = metadata.get('timeInfo') or {}
    extent = info.get('timeExtent') or metadata.get('timeExtent')
    if not (isinstance(extent, list) and len(extent) >= 2 and
            all(type(v) in (int, float) for v in extent[:2])):
        raise radar.RadarError('history_no_time_extent')
    lo, hi = int(extent[0]), int(extent[1])
    now_ms = int(time.time() * 1000)
    if not (1_000_000_000_000 < lo < hi < now_ms + 600_000):
        raise radar.RadarError('history_invalid_time_extent')
    query = urllib.parse.urlencode({
        'f': 'pjson', 'where': '1=1',
        'outFields': 'objectid,idp_validtime,idp_validendtime,idp_subset,name',
        'returnGeometry': 'false', 'orderByFields': 'idp_validtime DESC',
        'resultRecordCount': '1000', 'resultOffset': '0',
    })
    response = _json(radar.PRIMARY + '/query?' + query, limit=950_000)
    features = response.get('features')
    if not isinstance(features, list):
        raise radar.RadarError('history_no_catalog')
    # NOAA may publish several mosaicking component rasters a few seconds
    # apart. Group as a single observation by 5-min clock bin. One timestamp
    # per bin is used, with no synthesized bins to fill missing observations.
    bins = {}
    cutoff = max(lo, hi - 240 * 60_000)
    for feature in features[:1000]:
        attrs = feature.get('attributes') if isinstance(feature, dict) else None
        if not isinstance(attrs, dict):
            continue
        value = attrs.get('idp_validtime')
        if type(value) not in (int, float) or not math.isfinite(value):
            continue
        ms = int(value)
        if not (cutoff <= ms <= hi and ms <= now_ms + 60_000):
            continue
        bin_id = ms // 300_000
        # Prefer a representative within the bin with multiple matching rasters,
        # but never expose individual seconds-apart entries as separate steps.
        bins.setdefault(bin_id, []).append(ms)
    observations = []
    for values in bins.values():
        counts = {value: values.count(value) for value in set(values)}
        selected = max(counts, key=lambda v: (counts[v], v))
        observations.append(selected)
    observations = sorted(set(observations))[-_MAX_FRAMES:]
    frames = [{'frame_id': _token(ms), 'valid_time_ms': ms,
               'valid_time_utc': _utc(ms)} for ms in observations]
    return frames, (lo, hi)


def _catalog(force=False):
    now = time.monotonic()
    with _HISTORY_LOCK:
        if not force and now - _CATALOG['checked'] < 75:
            return list(_CATALOG['frames']), _CATALOG['extent'], _CATALOG['error']
    if not _REFRESH_LOCK.acquire(blocking=False):
        with _HISTORY_LOCK:
            return list(_CATALOG['frames']), _CATALOG['extent'], _CATALOG['error'] or 'refreshing'
    try:
        try:
            frames, extent = _fetch_catalog()
            error = None
        except radar.RadarError as exc:
            frames, extent, error = [], None, exc.code
        with _HISTORY_LOCK:
            # Do not grant tokens outside the most recently verified catalog.
            _ALLOWED.clear()
            _ALLOWED.update({f['frame_id']: f['valid_time_ms'] for f in frames})
            _CATALOG.update({'checked': time.monotonic(), 'frames': frames,
                             'extent': extent, 'error': error})
            return list(frames), extent, error
    finally:
        _REFRESH_LOCK.release()


def history(window=60):
    if type(window) is not int or window not in _WINDOWS:
        raise radar.RadarError('invalid_window')
    frames, extent, error = _catalog()
    if not frames:
        return {'ok': True, 'historical_supported': False,
                'provider_id': 'nws-time', 'frames': [],
                'error_code': error or 'history_no_frames',
                'checked_at_utc': _utc(int(time.time() * 1000)),
                'window_requested_minutes': window,
                'window_available_minutes': 0}
    newest = frames[-1]['valid_time_ms']
    start = newest - window * 60_000
    filtered = [dict(frame) for frame in frames if frame['valid_time_ms'] >= start]
    return {'ok': True, 'historical_supported': len(filtered) >= 3,
            'provider_id': 'nws-time', 'frames': filtered,
            'window_requested_minutes': window,
            'window_available_minutes': int((newest - frames[0]['valid_time_ms']) / 60_000),
            'available_from_utc': frames[0]['valid_time_utc'],
            'available_to_utc': frames[-1]['valid_time_utc'],
            'checked_at_utc': _utc(int(time.time() * 1000)),
            'error_code': error}


def parse_tile(path):
    pattern = r'/api/tak-map/weather/radar/history-tile-i696/(\d{1,2})/(\d{1,7})/(\d{1,7})\.png\Z'
    match = re.fullmatch(pattern, path)
    if not match:
        raise radar.RadarError('invalid_tile')
    z, x, y = map(int, match.groups())
    radar.xyz_bounds(z, x, y)
    return z, x, y


def _cache_get(key):
    global _TILE_BYTES
    with _HISTORY_LOCK:
        item = _TILE_CACHE.get(key)
        if item is None:
            return None
        exp, value = item
        if time.monotonic() > exp:
            _TILE_BYTES -= len(value)
            _TILE_CACHE.pop(key, None)
            return None
        _TILE_CACHE.move_to_end(key)
        return value


def _cache_put(key, value):
    global _TILE_BYTES
    with _HISTORY_LOCK:
        old = _TILE_CACHE.pop(key, None)
        if old:
            _TILE_BYTES -= len(old[1])
        _TILE_CACHE[key] = (time.monotonic() + _TILE_TTL, value)
        _TILE_BYTES += len(value)
        while len(_TILE_CACHE) > _MAX_TILES or _TILE_BYTES > _MAX_BYTES:
            _, (_, evicted) = _TILE_CACHE.popitem(last=False)
            _TILE_BYTES -= len(evicted)


def tile(z, x, y, frame_id):
    radar.xyz_bounds(z, x, y)
    if not isinstance(frame_id, str) or not _TOKEN_RE.fullmatch(frame_id):
        raise radar.RadarError('invalid_frame')
    with _HISTORY_LOCK:
        ms = _ALLOWED.get(frame_id)
        age = time.monotonic() - _CATALOG['checked']
    if ms is None or age > 300:
        raise radar.RadarError('historical_frame_expired')
    key = (frame_id, z, x, y)
    hit = _cache_get(key)
    if hit is not None:
        return hit
    with _HISTORY_LOCK:
        flight = _TILE_FLIGHTS.get(key)
        if flight is None:
            flight = threading.Event()
            _TILE_FLIGHTS[key] = flight
            owner = True
        else:
            owner = False
    if not owner:
        if flight.wait(45):
            hit = _cache_get(key)
            if hit is not None:
                return hit
        raise radar.RadarError('history_tile_unavailable')
    try:
        # i693's fixed NOAA host policy, retry backoff, concurrency, PNG validation.
        png = radar._fetch_tile_with_retry('nws-time', z, x, y, ms)
        _cache_put(key, png)
        return png
    finally:
        with _HISTORY_LOCK:
            _TILE_FLIGHTS.pop(key, None)
            flight.set()
