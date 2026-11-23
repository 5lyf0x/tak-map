from pathlib import Path
import os, runpy, tempfile, xml.etree.ElementTree as ET, json, re

ROOT=Path(__file__).resolve().parents[1]
assert (ROOT/'VERSION').exists()
os.environ['TAK_DASHBOARD_DATA_DIR']=tempfile.mkdtemp(prefix='takmap-i636-')
ns=runpy.run_path(str(ROOT/'tak_dashboard.py'),run_name='takmap_i636_test')

assert ns['TAK_MAP_ITERATION']=='i659'
cfg=ns['tak_map_config']()
assert cfg['version']=='1.4.0-i659'
assert cfg['tak_map_iteration']=='i659'
assert cfg['tak_shape_compat_i636']['canonical_tak_wire_format'] is True
assert cfg['server_authoritative_data_sync_i636']['null_mission_history_counts_as_active'] is False
assert 'takMapI636Loader' in ns['TAK_MAP_HTML']
assert '/assets/runtime/tak-map-i636.js?v=1.4.0-i659' in ns['TAK_MAP_HTML']

RECT='''<?xml version="1.0" encoding="utf-8"?>
<event access="Undefined" how="h-e" stale="2026-09-03T14:06:34.877Z" start="2026-09-02T14:06:32.217Z" time="2026-09-02T14:06:34.877Z" type="u-d-r" uid="d9d9f0c2-696b-472d-95ed-29a705537a69" version="2.0"><point ce="9999999.0" hae="473.563" lat="34.2060116" le="9999999.0" lon="-118.72761"/><detail><link point="34.21028794604995,-118.75832320362926"/><link point="34.18305784557117,-118.71324111471124"/><link point="34.201731109450755,-118.69689581442177"/><link point="34.22896713330185,-118.74198259098516"/><__shapeExtras cpvis="true" editable="true"/><remarks/><archive/><strokeColor value="-256"/><strokeWeight value="3.0"/><strokeStyle value="solid"/><fillColor value="16776960"/><creator callsign="slyfox" time="2026-06-25T01:47:49.237Z" type="a-f-G-U-C-R-V-G" uid="ANDROID-20ce457f78ce778e"/><labels_on value="false"/><tog enabled="0"/><precisionlocation altsrc="SRTM1"/><contact callsign="Rectangle 3"/><marti><dest mission="1-40TH RECON"/></marti></detail></event>'''
event={'uid':'d9d9f0c2-696b-472d-95ed-29a705537a69','type':'u-d-r','cot_type':'u-d-r','mission_cot_xml':RECT,'lat':34.2060116,'lon':-118.72761}
shape=ns['_i636_parse_tak_shape_event'](event,'1-40TH RECON')
assert shape['uid']==event['uid']
assert shape['mission_name']=='1-40TH RECON'
assert shape['shape_kind_i636']=='rectangle'
assert shape['shape_closed_i636'] is True
assert len(shape['coords'])==4
assert shape['name']=='Rectangle 3'
assert shape['color'].lower()=='#ffff00'
assert shape['weight']==3.0
assert shape['raw_cot_preserved_i636'] is True
assert shape['preserved_detail_i636']['creator']['attributes']['callsign']=='slyfox'

# The authoritative Mission projection must replace any legacy marker/route
# interpretation of the same u-d-r UID.
rows=ns['_i512_mission_api_objects'](RECT,'1-40TH RECON')
matches=[r for r in rows if isinstance(r,dict) and r.get('uid')==event['uid']]
assert len(matches)==1, matches
assert matches[0]['geometry']=='shape' and len(matches[0]['coords'])==4

# Legacy TAK Maps rectangle with a duplicated closing point is accepted on read
# and normalized in-memory only. Raw XML remains unchanged.
legacy=RECT.replace('</detail>','<link point="34.21028794604995,-118.75832320362926"/></detail>')
legacy_event=dict(event,mission_cot_xml=legacy)
legacy_shape=ns['_i636_parse_tak_shape_event'](legacy_event,'1-40TH RECON')
assert len(legacy_shape['coords'])==4
assert legacy_shape['legacy_closed_link_i636'] is True
assert legacy_shape['raw_cot_i636']==legacy

# TAK Maps v345 legacy __shape/polyline/vertex payload remains readable.
V345='''<event uid="legacy-v345" type="u-d-f" version="2.0"><point lat="34.0" lon="-118.0"/><detail><contact callsign="Old Circle"/><strokeColor value="-37074"/><fillColor value="1090518784"/><__shape type="circle" closed="true"><polyline closed="true"><vertex lat="34.0" lon="-118.01"/><vertex lat="34.01" lon="-118.0"/><vertex lat="34.0" lon="-117.99"/><vertex lat="33.99" lon="-118.0"/><vertex lat="34.0" lon="-118.01"/></polyline></__shape><takmap_shape type="circle" format="geojson"/></detail></event>'''
old_circle=ns['_i636_parse_tak_shape_event']({'uid':'legacy-v345','type':'u-d-f','cot_type':'u-d-f','mission_cot_xml':V345},'Legacy Mission')
assert old_circle['shape_kind_i636']=='circle'
assert old_circle['shape_closed_i636'] is True
assert len(old_circle['coords'])==4
assert old_circle['raw_cot_i636']==V345

# Non-shape route CoT must not be intercepted by the shape codec.
assert ns['_i636_parse_tak_shape_event']({'uid':'r1','type':'b-m-r','cot_type':'b-m-r','mission_cot_xml':'<event uid="r1" type="b-m-r"/>'},'M') is None

# Canonical rectangle serialization: exactly four unique link points, no closing duplicate.
rect_feature={'uid':'rect-new','name':'Rect New','shape_type':'rectangle','geometry':'shape','coords':[
    [34.0,-118.0],[34.0,-117.9],[34.1,-117.9],[34.1,-118.0],[34.0,-118.0]
], 'properties':{'shape_type':'rectangle','name':'Rect New'}}
built=ns['_v346_shape_cot_event_for_feature'](rect_feature,0,'pkg','creator','takmap')
assert built['ok'] and built['cot_type']=='u-d-r'
root=ET.fromstring(built['events'][0]['xml'].split('\n',1)[1])
links=[n for n in root.find('detail') if n.tag.endswith('link') and n.attrib.get('point')]
assert len(links)==4
assert links[0].attrib['point']!=links[-1].attrib['point']

# Polygon uses u-d-p and implicit closure, not the old u-d-f + duplicated final link.
poly=dict(rect_feature,uid='poly-new',name='Poly',shape_type='polygon',properties={'shape_type':'polygon','name':'Poly'})
pb=ns['_v346_shape_cot_event_for_feature'](poly,0,'pkg','creator','takmap')
assert pb['ok'] and pb['cot_type']=='u-d-p'
pr=ET.fromstring(pb['events'][0]['xml'].split('\n',1)[1])
pl=[n.attrib['point'] for n in pr.find('detail') if n.tag.endswith('link') and n.attrib.get('point')]
assert len(pl)==4 and pl[0]!=pl[-1]

# Freeform remains open and uses u-d-f.
free={'uid':'free','name':'Free','shape_type':'freehand','geometry':'shape','coords':[[34,-118],[34.01,-117.99],[34.02,-118.01]],'properties':{'shape_type':'freehand'}}
fb=ns['_v346_shape_cot_event_for_feature'](free,0,'pkg','creator','takmap')
assert fb['ok'] and fb['cot_type']=='u-d-f'

# Circle/ellipse publish native ellipse geometry instead of 72/96 point u-d-f polygons.
circle={'uid':'circle','name':'Circle','shape_type':'circle','geometry':'shape','coords':[
    [34.0,-118.01],[34.01,-118.0],[34.0,-117.99],[33.99,-118.0],[34.0,-118.01]
], 'properties':{'shape_type':'circle'}}
cb=ns['_v346_shape_cot_event_for_feature'](circle,0,'pkg','creator','takmap')
assert cb['ok'] and cb['cot_type']=='u-d-c-c'
cr=ET.fromstring(cb['events'][0]['xml'].split('\n',1)[1])
ell=next(n for n in cr.iter() if n.tag.endswith('ellipse'))
assert float(ell.attrib['major'])>0 and abs(float(ell.attrib['major'])-float(ell.attrib['minor']))<1e-6
assert not [n for n in cr.find('detail') if n.tag.endswith('link') and n.attrib.get('point')]

ellipse=dict(circle,uid='ellipse',name='Ellipse',shape_type='ellipse',coords=[
    [34.0,-118.02],[34.01,-118.0],[34.0,-117.98],[33.99,-118.0],[34.0,-118.02]
],properties={'shape_type':'ellipse'})
eb=ns['_v346_shape_cot_event_for_feature'](ellipse,0,'pkg','creator','takmap')
assert eb['ok'] and eb['cot_type']=='u-d-c-e'
er=ET.fromstring(eb['events'][0]['xml'].split('\n',1)[1])
ee=next(n for n in er.iter() if n.tag.endswith('ellipse'))
assert float(ee.attrib['major'])>float(ee.attrib['minor'])

# Read canonical native circle back into display geometry while retaining raw CoT.
cev={'uid':'circle','type':'u-d-c-c','cot_type':'u-d-c-c','mission_cot_xml':cb['events'][0]['xml']}
cs=ns['_i636_parse_tak_shape_event'](cev,'M')
assert cs['shape_kind_i636']=='circle' and len(cs['coords'])>=24 and cs['raw_cot_i636']==cb['events'][0]['xml']

# Exact Mission delete verification: NULL MissionUID history no longer counts active.
rg=ns['_i636_raw_active'].__globals__
old=rg['_i636_snapshot_before']
try:
    rg['_i636_snapshot_before']=lambda:{'objects':[],'mission_uids':[{'uid':'ABC','mission_name':None}]}
    assert ns['_i636_raw_active']('ABC','Alpha') is False
    rg['_i636_snapshot_before']=lambda:{'objects':[],'mission_uids':[{'uid':'ABC','mission_name':'Bravo'}]}
    assert ns['_i636_raw_active']('ABC','Alpha') is False
    assert ns['_i636_raw_active']('ABC','Bravo') is True
finally:
    rg['_i636_snapshot_before']=old

# Server-backed Data Sync objects without Mission membership are hidden, not
# legitimized as server-side Local Data. Client/local import storage is separate.
sess={'username':'test-i636'}
payload={'objects':[{'uid':'M1','name':'Mission object','lat':1,'lon':2,'mission_name':'Alpha'},
                    {'uid':'O1','name':'Orphan','lat':3,'lon':4}],
         'mission_uids':[{'uid':'M1','mission_name':'Alpha'}],
         'mission_content_mission':[],'mission_content':[],'packages':[],'missions':[{'name':'Alpha'}]}
out=ns['_i635_normalize_server_authoritative'](payload,sess)
ids={r.get('uid') for r in out['objects']}
assert 'M1' in ids and 'O1' not in ids
assert out['data_sync_association_i636']['server_orphans_hidden']>=1

front=(ROOT/'assets'/'tak-map-i636.js').read_text()
for token in ["const V='i636'",'tak_shape_i636','shape_closed_i636','L.polygon','L.polyline','fill_opacity']:
    assert token in front, token

print('PASS i636 canonical TAK shape compatibility, backward-compatible read, exact delete verification, Mission-only server invariant')
