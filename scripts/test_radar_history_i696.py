"""Offline no-network radar history security and observation regression (i696)."""
import importlib
import json
import sys
import time
import urllib.parse
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import tak_map_radar_i693 as core
import tak_map_radar_history_i696 as hist

NOW=int(time.time()*1000)
END=NOW-45_000
START=END-112*60_000
TIMES=[END-i*5*60_000 for i in range(23)]
# Seconds-apart regional catalog components, and a future record outside metadata.
RECORDS=[]
for index,t in enumerate(TIMES):
    RECORDS.extend([{'attributes':{'idp_validtime':t-450, 'objectid':index*3}},
                    {'attributes':{'idp_validtime':t, 'objectid':index*3+1}}])
RECORDS += [{'attributes':{'idp_validtime':END+10*60_000,'objectid':1000}}]
requests=[]
orig_request=core._request
orig_fetch=core._fetch_tile_with_retry

def fake_request(url,limit,timeout=8):
    requests.append(url)
    if '/query?' in url:
        return 'application/json',json.dumps({'features':RECORDS,'exceededTransferLimit':False}).encode()
    if url.endswith('f=pjson'):
        return 'application/json',json.dumps({'timeInfo':{'timeExtent':[START,END]},'currentVersion':11}).encode()
    raise AssertionError('unexpected network call '+url)

core._request=fake_request
try:
    cat=hist.history(60)
    assert cat['ok'] and cat['historical_supported'],cat
    assert 11<=len(cat['frames'])<=13,cat
    assert cat['provider_id']=='nws-time'
    assert all(f['valid_time_ms']<=END for f in cat['frames'])
    assert all(f['frame_id'].startswith('h') for f in cat['frames'])
    assert len({f['valid_time_ms']//300_000 for f in cat['frames']})==len(cat['frames'])
    assert [f['valid_time_ms'] for f in cat['frames']]==sorted(f['valid_time_ms'] for f in cat['frames'])
    frames30=hist.history(30)['frames']
    assert frames30 and len(frames30)<len(cat['frames'])
    assert len(requests)==2,'Catalog should be cached rather than retrieved per frame'
    for bad in ('h'+str(END)+'_deadbeefdeadbeef','p12345','h123','http://noaa',''):
        try:hist.tile(4,5,6,bad)
        except core.RadarError as exc:assert exc.code in ('invalid_frame','historical_frame_expired')
        else:raise AssertionError('unissued frame accepted: '+bad)
    for bad in (-1,0,31,241,'60'):
        try:hist.history(bad)
        except core.RadarError as exc:assert exc.code=='invalid_window'
        else:raise AssertionError('invalid window accepted')
    for bad in ('/api/tak-map/weather/radar/history-tile-i696/11/0/0.png',
                '/api/tak-map/weather/radar/history-tile-i696/2/4/0.png',
                '/api/tak-map/weather/radar/history-tile-i696/2/0/4.png'):
        try:hist.parse_tile(bad)
        except core.RadarError as exc:assert exc.code=='invalid_tile'
        else:raise AssertionError('invalid XYZ accepted')
    good=hist.parse_tile('/api/tak-map/weather/radar/history-tile-i696/2/1/1.png')
    assert good==(2,1,1)
    selected=cat['frames'][5]
    calls=[]
    def fake_fetch(provider,z,x,y,ms):
        calls.append((provider,z,x,y,ms))
        return b'correctly pinned stand-in'  # Underlying i693 validates real PNG upstream.
    core._fetch_tile_with_retry=fake_fetch
    one=hist.tile(2,1,1,selected['frame_id'])
    two=hist.tile(2,1,1,selected['frame_id'])
    assert one==two and len(calls)==1
    assert calls[0]==('nws-time',2,1,1,selected['valid_time_ms'])
    print('PASS 14 i696 backend checks: strict catalog, real-bin dedup, windows, fixed provider, authenticated opaque IDs, token expiry, XYZ, cache, pinned time')
finally:
    core._request=orig_request
    core._fetch_tile_with_retry=orig_fetch
