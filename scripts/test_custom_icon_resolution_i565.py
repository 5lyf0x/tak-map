#!/usr/bin/env python3
from pathlib import Path
import importlib.util, sys, urllib.parse
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('tak_i565_custom',ROOT/'tak_dashboard.py')
m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m; spec.loader.exec_module(m)
path='db450cbe-2fec-47fb-bd2b-ba2db89b035e/Incident Management/water point.png'
uid='ATAK-WATER-POINT-1'
xml=f'''<event version="2.0" uid="{uid}" type="a-n-G" time="2026-07-27T12:00:00Z" start="2026-07-27T12:00:00Z" stale="2026-07-27T12:10:00Z" how="h-g-i-g-o"><point lat="34.1" lon="-117.2" hae="0" ce="10" le="10"/><detail><contact callsign="Water Point"/><usericon iconsetpath="{path}"/></detail></event>'''
summary={'uid':uid,'type':'a-n-G','time':'2026-07-27T12:00:01Z','point':{'lat':34.1,'lon':-117.2}}
events=m._i545_extract_events({'rows':[xml,summary]})
row=events[uid.casefold()]
assert row['iconsetpath']==path,row
assert row['mission_cot_custom_icon_coalesced_i565'] is True
for key in ('sidc','SIDC','mil2525_file','mil2525_name'): assert not row.get(key), (key,row.get(key))
# A newer complete XML event intentionally without usericon must remove the old custom icon.
xml2=f'''<event version="2.0" uid="{uid}" type="a-n-G" time="2026-07-27T12:00:02Z" start="2026-07-27T12:00:02Z" stale="2026-07-27T12:10:02Z" how="h-g-i-g-o"><point lat="34.1" lon="-117.2" hae="0" ce="10" le="10"/><detail><contact callsign="Water Point"/></detail></event>'''
row2=m._i545_extract_events({'rows':[xml,xml2]})[uid.casefold()]
assert not m._i565_event_iconset(row2),row2
# Delete event must never inherit the old path.
delete=f'''<event version="2.0" uid="{uid}" type="t-x-d-d" time="2026-07-27T12:00:03Z" start="2026-07-27T12:00:03Z" stale="2026-07-27T12:00:04Z" how="m-g"><point lat="0" lon="0" hae="0" ce="9999999" le="9999999"/><detail/></event>'''
row3=m._i545_extract_events({'rows':[xml,delete]})[uid.casefold()]
assert m._i565_delete_event(row3) and not m._i565_event_iconset(row3),row3
# Registry lookups accept encoded, slash-variant, and case-variant paths and return canonical row.
by=m._i555_registry_load()['by_path']
variants=[path,urllib.parse.quote(path,safe='/'),path.replace('/','\\'),path.upper()]
for variant in variants:
    item=by.get(variant); assert item and item['iconsetpath']==path,(variant,item)
js=(ROOT/'assets'/'tak-map-icon-registry-i565.js').read_text()
for token in ('function normalizeIconsetPath','function customIconImageError','TakMapCustomIconI565.onImageError(this)','data_sync_current_iconset_path_i565'):
    assert token in js,token
assert "state.customByPath.get(iconsetPathKey(path))" in js
cfg=m.tak_map_config()['custom_icon_resolution_i565']
assert cfg['image_retry_count']==2 and cfg['case_insensitive_lookup'] and cfg['generic_mil_fallback_suppressed']
print('i565 custom-icon coalescing, canonical registry lookup, no-generic-fallback, and browser retry checks passed')
