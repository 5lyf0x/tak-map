"""TAK Map i693 same-origin NOAA/NWS radar tile proxy.

No arbitrary external URLs or BBOX arguments are accepted from the browser.
This module has no side effects on application data and uses only stdlib.
"""
from __future__ import annotations

from collections import OrderedDict
from datetime import datetime, timezone
import io
from collections import deque
import json
import math
import re
import struct
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import zlib

VERSION = '1.4.0-i693'
NWS_HOST = 'mapservices.weather.noaa.gov'
PRIMARY = 'https://mapservices.weather.noaa.gov/eventdriven/rest/services/radar/radar_base_reflectivity_time/ImageServer'
FALLBACK = 'https://mapservices.weather.noaa.gov/eventdriven/rest/services/radar/radar_base_reflectivity/MapServer'
PROVIDERS = {
    'nws-time': (PRIMARY, 'NWS MRMS · timed imagery'),
    'nws-latest': (FALLBACK, 'NWS MRMS · latest imagery'),
}
MAX_NATIVE_ZOOM = 10
STATUS_TTL = 105
TILE_RETRIES = 2
TILE_RETRY_DELAYS = (0.25, 0.85)
# Memory bound: at most 160 tiles, 24 MiB in aggregate, 4 simultaneous upstream connections.
MAX_TILES = 160
MAX_CACHE_BYTES = 24 * 1024 * 1024
MAX_PNG_BYTES = 1_600_000
VALID_RESPONSE_TYPE = ('image/png', 'image/x-png', 'application/octet-stream')
WEB_MERCATOR_HALF_WORLD = 20037508.342789244

class RadarError(Exception):
    def __init__(self, code, message='Radar provider unavailable'):
        self.code = code
        super().__init__(message)

class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        raise RadarError('upstream_redirect')

_OPEN = urllib.request.build_opener(_NoRedirect())
_LOCK = threading.RLock()
_STATUS_LOCK = threading.Lock()
_WORKERS = threading.BoundedSemaphore(4)
# Per-tile in-flight event: a second browser request waits for the first fetch.
_FLIGHTS = {}
_CACHE = OrderedDict()
_CACHE_BYTES = 0
_STATE = dict(provider=None, token=None, valid_ms=None, valid_time=None,
              last_ok=None, last_check=0.0, last_error=None, failures=0,
              frame_source=None, tile_errors=0, tile_successes=0,
              last_tile_error=None, last_tile_error_at=0.0,
              primary_retry_at=0.0, generation=0)
_LOGGED = {}
# Diagnostics only; individual tile errors must not de-activate healthy providers.
_RECENT_TILE_ERRORS = deque(maxlen=80)


def _log_once(code):
    now = time.monotonic()
    with _LOCK:
        if now - _LOGGED.get(code, -1e9) < 90:
            return
        _LOGGED[code] = now
    print('TAK Map radar i693:', code, flush=True)


def _request(url, limit, timeout=8):
    # The URL is built solely from hardcoded NOAA host and fixed service paths.
    parsed = urllib.parse.urlsplit(url)
    if (parsed.scheme != 'https' or parsed.hostname != NWS_HOST or
            parsed.username or parsed.password or parsed.port not in (None, 443) or
            not parsed.path.startswith('/eventdriven/rest/services/radar/')):
        raise RadarError('unapproved_upstream')
    req = urllib.request.Request(url, headers={
        'User-Agent': 'TAKMap/1.4.0-i693 (NOAA radar proxy; contact local system administrator)',
        'Accept': 'image/png,application/json', 'Accept-Encoding': 'identity',
    })
    try:
        with _OPEN.open(req, timeout=timeout) as resp:
            if resp.status != 200:
                raise RadarError('upstream_http_' + str(resp.status))
            mime = (resp.headers.get('Content-Type') or '').lower().split(';', 1)[0].strip()
            payload = resp.read(limit + 1)
            if len(payload) > limit:
                raise RadarError('upstream_too_large')
            return mime, payload
    except RadarError:
        raise
    except urllib.error.HTTPError as e:
        raise RadarError('upstream_http_' + str(e.code)) from e
    except (OSError, TimeoutError, urllib.error.URLError) as e:
        raise RadarError('upstream_connection') from e


def _check_png(mime, data):
    if mime not in VALID_RESPONSE_TYPE or not data.startswith(b'\x89PNG\r\n\x1a\n'):
        raise RadarError('upstream_not_png')
    offset = 8
    seen_ihdr = seen_idat = seen_iend = False
    idat = bytearray()
    expected = None
    for _ in range(10000):
        if offset + 12 > len(data):
            break
        length = struct.unpack_from('>I', data, offset)[0]
        if length > MAX_PNG_BYTES or offset + length + 12 > len(data):
            raise RadarError('upstream_invalid_png')
        name = data[offset + 4:offset + 8]
        chunk = data[offset + 8:offset + 8 + length]
        crc = struct.unpack_from('>I', data, offset + 8 + length)[0]
        if zlib.crc32(name + chunk) & 0xffffffff != crc:
            raise RadarError('upstream_invalid_png')
        offset += 12 + length
        if name == b'IHDR':
            if seen_ihdr or length != 13:
                raise RadarError('upstream_invalid_png')
            width, height, depth, color, compr, filtering, interlace = struct.unpack('>IIBBBBB', chunk)
            if (width != 256 or height != 256 or depth not in (1, 2, 4, 8, 16)
                    or color not in (0, 2, 3, 4, 6) or compr != 0 or filtering != 0
                    or interlace not in (0, 1)):
                raise RadarError('upstream_invalid_png')
            seen_ihdr = True
            if not interlace:
                channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color]
                expected = 256 * (1 + math.ceil(256 * depth * channels / 8))
        elif name == b'IDAT':
            if not seen_ihdr:
                raise RadarError('upstream_invalid_png')
            seen_idat = True
            idat.extend(chunk)
            if len(idat) > MAX_PNG_BYTES:
                raise RadarError('upstream_invalid_png')
        elif name == b'IEND':
            seen_iend = True
            if length or offset != len(data):
                raise RadarError('upstream_invalid_png')
            break
    if not (seen_ihdr and seen_idat and seen_iend):
        raise RadarError('upstream_invalid_png')
    try:
        decompressor = zlib.decompressobj()
        decoded = decompressor.decompress(bytes(idat), 2_000_000)
        decoded += decompressor.flush(2_000_000 - len(decoded))
        if not decompressor.eof or decompressor.unused_data or (expected is not None and len(decoded) != expected):
            raise RadarError('upstream_invalid_png')
    except (zlib.error, ValueError) as e:
        raise RadarError('upstream_invalid_png') from e
    return data


def xyz_bounds(z, x, y):
    if not all(type(v) is int for v in (z, x, y)) or not 0 <= z <= MAX_NATIVE_ZOOM:
        raise RadarError('invalid_tile')
    n = 1 << z
    if x < 0 or x >= n or y < 0 or y >= n:
        raise RadarError('invalid_tile')
    cell = 2.0 * WEB_MERCATOR_HALF_WORLD / n
    min_x = -WEB_MERCATOR_HALF_WORLD + x * cell
    max_y = WEB_MERCATOR_HALF_WORLD - y * cell
    return (min_x, max_y - cell, min_x + cell, max_y)


def _catalog_valid_time(extent):
    """Prefer real image-catalog observation times to the time-range boundary.

    ArcGIS image service query may be restricted or unavailable. Do not silently
    invent data when it fails; report provisional range-derived frame in status.
    """
    params = urllib.parse.urlencode({
        'f': 'pjson', 'where': '1=1',
        'outFields': 'objectid,idp_validtime,idp_validendtime,name',
        'returnGeometry': 'false', 'orderByFields': 'idp_validtime DESC',
        'resultRecordCount': '25'
    })
    mime, raw = _request(PRIMARY + '/query?' + params, 600_000, timeout=8)
    if mime not in ('application/json','text/json','text/plain'):
        raise RadarError('upstream_catalog_format')
    try:
        payload = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as e:
        raise RadarError('upstream_catalog_format') from e
    if not isinstance(payload,dict) or payload.get('error') or not isinstance(payload.get('features'),list):
        raise RadarError('upstream_catalog_unavailable')
    times=[]
    for feature in payload['features'][:1000]:
        attr=feature.get('attributes',{}) if isinstance(feature,dict) else {}
        t=attr.get('idp_validtime')
        if type(t) in (int,float) and 1_000_000_000_000 <= t <= 4_102_444_800_000:
            t=int(t)
            if (not extent or extent[0]-600_000 <= t <= extent[1]+600_000):
                times.append(t)
    if not times:
        raise RadarError('upstream_catalog_empty')
    return max(times)


def _metadata(provider):
    url, _ = PROVIDERS[provider]
    mime, data = _request(url + '?f=pjson', 800_000, timeout=6)
    if mime not in ('application/json', 'text/json', 'text/plain'):
        raise RadarError('upstream_metadata_format')
    try:
        d = json.loads(data)
    except (ValueError, UnicodeDecodeError) as e:
        raise RadarError('upstream_metadata_format') from e
    if not isinstance(d, dict) or d.get('error') or d.get('currentVersion') is None:
        raise RadarError('upstream_metadata_format')
    if provider == 'nws-latest':
        return None, 'latest_only'
    tinfo=d.get('timeInfo') or {}
    times=tinfo.get('timeExtent') or d.get('timeExtent') or []
    extent=None
    if isinstance(times,list) and len(times)>=2 and all(type(t) in (int,float) for t in times[:2]):
        a,b=int(times[0]),int(times[1])
        if 1_000_000_000_000 <= a <= b <= 4_102_444_800_000:
            extent=a,b
    if not extent:
        raise RadarError('upstream_time_extent_unavailable')
    try:
        return _catalog_valid_time(extent), 'catalog_observation'
    except RadarError as e:
        _log_once('catalog:' + e.code)
        # Retain i692-compatible service availability as a documented fallback.
        # Range end is provisional, never labeled as a verified observation.
        return extent[1], 'time_range_provisional'


def _token(provider, valid_ms, now):
    # A latest-image service does not publish observation time. Bucket is a
    # refresh token, NOT a claimed observation timestamp.
    return ('p' + str(valid_ms)) if provider == 'nws-time' and valid_ms else ('f' if provider == 'nws-latest' else 'u') + str(int(now // 300))


def _activate(provider, valid_ms, now, recovered=False, frame_source=None):
    with _LOCK:
        previous = _STATE['provider']
        token = _token(provider, valid_ms, time.time())
        if previous != provider or _STATE['token'] != token:
            _STATE['generation'] += 1
            _STATE['last_ok'] = None
            _STATE['failures'] = 0
        _STATE.update(provider=provider, token=token, valid_ms=valid_ms,
                      valid_time=datetime.fromtimestamp(valid_ms / 1000, timezone.utc).isoformat().replace('+00:00', 'Z') if valid_ms else None,
                      last_check=now, last_error=None, failures=0, frame_source=frame_source)
        if recovered:
            _STATE['primary_retry_at'] = 0.0


def _refresh_provider(force=False):
    with _STATUS_LOCK:
        return _refresh_provider_locked(force)

def _refresh_provider_locked(force=False):
    now = time.monotonic()
    with _LOCK:
        if not force and now - _STATE['last_check'] < STATUS_TTL:
            return
        primary_first = now >= _STATE['primary_retry_at']
        current = _STATE['provider']
    checks = ['nws-time', 'nws-latest'] if primary_first else ['nws-latest']
    errors = []
    for provider in checks:
        try:
            valid_ms, frame_source = _metadata(provider)
            _activate(provider, valid_ms, now, recovered=(provider == 'nws-time'), frame_source=frame_source)
            return
        except RadarError as e:
            errors.append(provider + ':' + e.code)
            _log_once(provider + ':' + e.code)
            if provider == 'nws-time':
                with _LOCK:
                    _STATE['primary_retry_at'] = now + 180
    with _LOCK:
        _STATE['last_check'] = now
        _STATE['last_error'] = 'all_providers_unavailable'
        # Preserve last selected provider/frame during transient metadata errors;
        # its already rendered tiles may still be useful. No rapid global reset.
        if _STATE['provider'] is None or _STATE['last_ok'] is None or time.time() - _STATE['last_ok'] > 600:
            _STATE['provider'] = None
            _STATE['token'] = None
        _STATE['failures'] += 1
    _log_once('all_providers_unavailable')


def status():
    _refresh_provider()
    with _LOCK:
        s=dict(_STATE)
        recent=[x for x in _RECENT_TILE_ERRORS if time.monotonic()-x[0] < 180]
    provider=s['provider']
    age=(int(time.time()-s['last_ok']) if s['last_ok'] else None)
    service_state=('unavailable' if not provider else
                   'stale' if age is not None and age>600 else
                   'partial' if recent else
                   'degraded' if provider=='nws-latest' or s['last_error'] else
                   'ready' if age is not None else 'checking')
    return dict(ok=bool(provider), provider_id=provider,
                provider_label=PROVIDERS[provider][1] if provider else None,
                service_state=service_state, frame_token=s['token'],
                frame_source=s['frame_source'],
                observation_verified=(s['frame_source']=='catalog_observation'),
                valid_time_utc=s['valid_time'],
                last_successful_fetch_utc=(datetime.fromtimestamp(s['last_ok'], timezone.utc).isoformat().replace('+00:00','Z') if s['last_ok'] is not None else None),
                checked_at_utc=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                error_code=s['last_error'], last_success_age_seconds=age,
                total_tile_successes=s['tile_successes'],
                total_tile_errors=s['tile_errors'], recent_tile_errors=len(recent),
                last_tile_error_code=s['last_tile_error'],
                native_max_zoom=MAX_NATIVE_ZOOM)


def _tile_url(provider, z, x, y, valid_ms):
    bbox = ','.join(format(v, '.5f') for v in xyz_bounds(z, x, y))
    if provider == 'nws-time':
        params = dict(f='image', bbox=bbox, bboxSR='3857', imageSR='3857',
                      size='256,256', format='png32', interpolation='RSP_NearestNeighbor',
                      adjustAspectRatio='false')
        if valid_ms:
            params['time'] = str(valid_ms)
        endpoint = PRIMARY + '/exportImage'
    else:
        params = dict(f='image', bbox=bbox, bboxSR='3857', imageSR='3857',
                      size='256,256', format='png32', transparent='true', layers='show:3', dpi='96')
        endpoint = FALLBACK + '/export'
    return endpoint + '?' + urllib.parse.urlencode(params)


def _cache_get(key):
    with _LOCK:
        item = _CACHE.get(key)
        if not item:
            return None
        expires, payload = item
        if expires <= time.monotonic():
            _CACHE.pop(key)
            global _CACHE_BYTES
            _CACHE_BYTES -= len(payload)
            return None
        _CACHE.move_to_end(key)
        return payload


def _cache_put(key, png):
    global _CACHE_BYTES
    now = time.monotonic()
    with _LOCK:
        prior = _CACHE.pop(key, None)
        if prior:
            _CACHE_BYTES -= len(prior[1])
        _CACHE[key] = (now + 230, png)
        _CACHE_BYTES += len(png)
        while len(_CACHE) > MAX_TILES or _CACHE_BYTES > MAX_CACHE_BYTES:
            _, (_, removed) = _CACHE.popitem(last=False)
            _CACHE_BYTES -= len(removed)


def _fetch_tile_with_retry(provider,z,x,y,valid_ms):
    # Retry only this XYZ tile. No global provider changes or cache flushing.
    for attempt in range(TILE_RETRIES+1):
        try:
            if not _WORKERS.acquire(timeout=35):
                raise RadarError('upstream_busy')
            try:
                mime,payload=_request(_tile_url(provider,z,x,y,valid_ms), MAX_PNG_BYTES, timeout=8)
                return _check_png(mime,payload)
            finally:
                _WORKERS.release()
        except RadarError as e:
            if (attempt >= TILE_RETRIES or e.code.startswith('invalid_') or
                e.code in ('upstream_redirect','unapproved_upstream','upstream_too_large')):
                raise
            time.sleep(TILE_RETRY_DELAYS[attempt])


def tile(z, x, y, requested_frame):
    xyz_bounds(z,x,y)
    if not re.fullmatch(r'[puf][0-9]{1,16}', requested_frame or ''):
        raise RadarError('invalid_frame')
    _refresh_provider()
    with _LOCK:
        provider=_STATE['provider'];token=_STATE['token']
        valid_ms=_STATE['valid_ms'];generation=_STATE['generation']
    if not provider: raise RadarError('radar_unavailable')
    if requested_frame!=token: raise RadarError('frame_changed')
    key=(provider,token,z,x,y)
    hit=_cache_get(key)
    if hit is not None:return hit
    with _LOCK:
        if key in _FLIGHTS:waiter,owner=_FLIGHTS[key],False
        else:
            waiter,owner=threading.Event(),True
            _FLIGHTS[key]=waiter
    if not owner:
        if waiter.wait(48):
            hit=_cache_get(key)
            if hit is not None:return hit
        raise RadarError('upstream_fetch_failed')
    try:
        png=_fetch_tile_with_retry(provider,z,x,y,valid_ms)
        with _LOCK:
            # A newer coherent frame has arrived. This tile is useful for the
            # former frame but must not rewrite current-frame status.
            if _STATE['generation']==generation:
                _STATE['last_ok']=time.time()
                _STATE['tile_successes']+=1
        _cache_put(key,png)
        return png
    except RadarError as e:
        _log_once('tile:'+provider+':'+e.code)
        with _LOCK:
            if _STATE['generation']==generation:
                _STATE['tile_errors']+=1
                _STATE['last_tile_error']=e.code
                _STATE['last_tile_error_at']=time.monotonic()
                _RECENT_TILE_ERRORS.append((time.monotonic(),e.code,key))
        raise
    finally:
        with _LOCK:
            _FLIGHTS.pop(key,None)
            waiter.set()


def parse_tile(path):
    match = re.fullmatch(r'/api/tak-map/weather/radar/tile-i693/(\d{1,2})/(\d{1,7})/(\d{1,7})\.png', path)
    if not match:
        raise RadarError('invalid_tile')
    z, x, y = map(int, match.groups())
    xyz_bounds(z, x, y)
    return z, x, y
