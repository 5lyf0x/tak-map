#!/usr/bin/env python3
"""Offline ADS-B provider priority/failover smoke tests; never makes network requests."""
from pathlib import Path
import threading
import time

src = (Path(__file__).resolve().parents[1] / 'tak_dashboard.py').read_text()
start = src.rfind('# --- TAK Map v1.4.0 i620 ADS-B provider priority / failover hotfix ---')
end = src.find('# --- end TAK Map v1.4.0 i620 ADS-B provider priority / failover hotfix ---', start)
assert start >= 0 and end > start
snippet = src[start:end + len('# --- end TAK Map v1.4.0 i620 ADS-B provider priority / failover hotfix ---')]
lock = threading.RLock()
state = {'last_error': '', 'fetch_count': 0}
snapshots = {}

def normalize(d, settings):
    assert isinstance(d['ac'], list)
    return [{'id': e['hex'], 'source':'Airplanes.live', 'lat': e.get('lat', 34), 'lon': e.get('lon', -118)} for e in d['ac']], len(d['ac']), 12345, 90, ','.join(e['hex'] for e in d['ac'])

def store(key, settings, rows, raw_count, source_now, stale, sig, note):
    snapshots[key] = {'source_note': note, 'aircraft': list(rows), 'key': key}
    state['last_error'] = ''

def base_adsb(query_settings=None):
    return {'ok': True, 'snapshot_key': 'A', 'sources': [{'source': 'airplanes.live', 'ok': True}]}

def base_config():
    return {'adsb': {'settings': {}}}

ns = {'_I464_ADSB_LOCK': lock, '_I464_ADSB_STATE':state, '_I464_ADSB_SNAPSHOTS': snapshots,
      '_i465_adsb_normalize':normalize, '_i464_adsb_store':store,
      'tak_map_adsb':base_adsb, 'tak_map_config':base_config,
      '_I465_ADSB_POOL':None}
exec(compile(snippet, 'adsb_failover_hotfix', 'exec'), ns)
settings={'center_lat':34.0, 'center_lon': -118.0, 'radius_miles':50}
assert ns['_ADSBFO_PRIORITY'] == ('airplanes.live', 'adsb.lol', 'adsb.fi')
assert '/v3/lat/34.000000/lon/-118.000000/dist/44' in ns['_adsbfo_url']('adsb.fi',settings)
assert '/v2/point/34.000000/-118.000000/44' in ns['_adsbfo_url']('adsb.lol', settings)
assert '/v2/point/34.000000/-118.000000/44' in ns['_adsbfo_url']('airplanes.live', settings)

calls=[]
def fake(name, url):
    calls.append(name)
    if name == 'airplanes.live':raise RuntimeError('HTTP 403')
    return {'ac':[{'hex':'abc123'}]}
ns['_adsbfo_json_get']=fake
ns['_i464_adsb_collect_once'](settings, 'A')
assert calls == ['airplanes.live','adsb.lol'], calls
assert ns['tak_map_adsb']()['active_source'] == 'adsb.lol'
assert snapshots['A']['aircraft'][0]['source'] == 'ADSB.lol'
assert ns['tak_map_adsb']()['sources'][0]['ok'] is True
assert ns['tak_map_adsb']()['source_priority'] == list(ns['_ADSBFO_PRIORITY'])
assert ns['_ADSBFO_STATUS']['airplanes.live']['retry_at'] > time.time()

calls=[]
def second(name,url):
    calls.append(name)
    if name == 'adsb.lol': raise RuntimeError('HTTP 429')
    return {'ac':[{'hex':'def123'}]}
ns['_adsbfo_json_get']=second
ns['_i464_adsb_collect_once'](settings,'A')
assert calls == ['adsb.lol','adsb.fi'],calls
assert ns['tak_map_adsb']()['active_source'] == 'adsb.fi'
assert snapshots['A']['aircraft'][0]['source'] == 'ADSB.fi'
assert ns['_ADSBFO_STATUS']['adsb.lol']['retry_at'] > time.time()

# Higher priority comes back; always prefer it when cooldown expires.
ns['_ADSBFO_STATUS']['airplanes.live']['retry_at'] = 0
calls=[]
ns['_adsbfo_json_get']=lambda name,url: (calls.append(name) or {'ac':[]})
ns['_i464_adsb_collect_once'](settings,'A')
assert calls == ['airplanes.live'],calls
assert ns['tak_map_adsb']()['active_source']=='airplanes.live'
assert snapshots['A']['aircraft']==[], 'a valid empty array must not trigger failover'

# All unavailable: no new snapshot replaces the last good.
original=snapshots['A']
for p in ns['_ADSBFO_PRIORITY']:ns['_ADSBFO_STATUS'][p]['retry_at'] = 0
ns['_adsbfo_json_get']=lambda name,url: (_ for _ in ()).throw(RuntimeError('HTTP 503'))
try:ns['_i464_adsb_collect_once'](settings,'A')
except RuntimeError as ex:
    assert 'All ADS-B providers unavailable' in str(ex)
else:raise AssertionError('Expected failover chain to raise')
assert snapshots['A'] is original

# A malformed HTTP 200 body is an error, not a legitimate empty map.
for bad in [b'not-json', b'{}', b'{"ac":"not an array"}']:
    class Resp:
        status=200
        data=bad
        def release_conn(self):pass
    class Pool:
        def request(self,*a,**kw):return Resp()
    ns['_I465_ADSB_POOL']=Pool()
    try:ns['_adsbfo_json_get']('adsb.lol','https://api.adsb.lol/v2/point/34/-118/40')
    except RuntimeError:pass
    else:raise AssertionError(f'Expected invalid-data detection: {bad!r}')
print('PASS: ADS-B prioritized fallback, cooldown, recovery, empty response, malformed response and snapshot retention')
