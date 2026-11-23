"""TAK Map i687 infrastructure overlays.

An isolated, persistent GIS catalog. Online ArcGIS REST layer queries and
staged, restartable regional downloads; local GIS imports, spatial indexing,
export, category management. No Local Data tables are read or altered.
"""
from __future__ import annotations
import base64
from contextlib import contextmanager
import csv
import io
import ipaddress
import json
import math
import re
import os
import shutil
import socket
import sqlite3
import tempfile
import threading
import time
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError

BUILTINS = (
    ('electrical', 'Electrical Power'), ('communications','Communications'),
    ('oil-gas','Oil & Natural Gas'), ('water','Water & Wastewater'),
    ('rail','Rail Infrastructure'), ('bridges','Bridges'), ('aviation','Aviation'),
    ('maritime','Maritime & Ports'), ('industrial','Industrial Facilities'),
    ('emergency','Emergency Services'), ('environmental','Environmental Facilities'),
    ('dams','Dams & Flood Control'), ('space','Space & Satellite'),
    ('logistics','Logistics & Distribution'),
)
SOURCES = (
    # Built-in authoritative sources. Some categories intentionally start empty:
    # a category is not advertised as a streamed provider unless an endpoint is configured.
    ('lacounty-sewer-mains','water','Sewer Gravity Mains — Los Angeles County','https://dpw.gis.lacounty.gov/dpw/rest/services/Sewer_Network/FeatureServer/5','sewer'),
    ('lacounty-sewer-manholes','water','Sewer Manholes — Los Angeles County','https://dpw.gis.lacounty.gov/dpw/rest/services/Sewer_Network/FeatureServer/0','point'),
    ('lacounty-sewer-force','water','Sewer Force Mains — Los Angeles County','https://dpw.gis.lacounty.gov/dpw/rest/services/Sewer_Network/FeatureServer/14','sewer'),
    ('lacity-sewer-structures','water','Sewer Structures — City of Los Angeles','https://maps.lacity.org/arcgis/rest/services/Core/Master_sewer_external/MapServer/0','point'),
    ('us-transmission','electrical','U.S. Transmission Lines','https://services2.arcgis.com/FiaPA4ga0iQKduv3/arcgis/rest/services/US_Electric_Power_Transmission_Lines/FeatureServer/0','line'),
)
MAX_HTTP_BODY = 25 * 1024 * 1024  # single service response safety bound, NOT a download speed cap
MAX_UPLOAD_BYTES = 1024 * 1024 * 1024
PAGE_SIZE = 1000
MAX_VIEWPORT_FEATURES = 5000  # per-layer automatic display query; never applies to stored/download/export
MAX_PROVIDER_PAGES = 12
MAX_DISPLAY_VERTICES = 100000
MAX_FEATURE_VERTICES = 500
DB_LOCK = threading.RLock()
ACTIVE = {}


def now():
    return datetime.now(timezone.utc).isoformat()


def _root():
    return Path(os.environ.get('TAK_MAP_INFRA_DIR','/var/lib/tak-map/infrastructure'))


def _connect():
    root = _root()
    root.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(root/'infrastructure.sqlite3'),timeout=30)
    con.row_factory=sqlite3.Row
    con.execute('PRAGMA journal_mode=WAL')
    con.execute('PRAGMA busy_timeout=30000')
    con.execute('PRAGMA recursive_triggers=ON')
    con.executescript('''
    CREATE TABLE IF NOT EXISTS categories(id TEXT PRIMARY KEY,label TEXT NOT NULL,builtin INTEGER NOT NULL DEFAULT 0,hidden INTEGER NOT NULL DEFAULT 0,position INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE IF NOT EXISTS layers(id TEXT PRIMARY KEY,category_id TEXT NOT NULL,name TEXT NOT NULL,mode TEXT NOT NULL CHECK(mode IN ('online','offline')),url TEXT NOT NULL DEFAULT '',kind TEXT NOT NULL DEFAULT 'other',parent_id TEXT NOT NULL DEFAULT '',created TEXT NOT NULL DEFAULT '',updated TEXT NOT NULL DEFAULT '',metadata TEXT NOT NULL DEFAULT '{}',enabled INTEGER NOT NULL DEFAULT 0,hidden INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE IF NOT EXISTS features(fid INTEGER PRIMARY KEY AUTOINCREMENT,layer_id TEXT NOT NULL,feature_key TEXT NOT NULL,geometry TEXT NOT NULL,properties TEXT NOT NULL, minx REAL NOT NULL,maxx REAL NOT NULL,miny REAL NOT NULL,maxy REAL NOT NULL);
    CREATE UNIQUE INDEX IF NOT EXISTS infra_feature_unique ON features(layer_id,feature_key);
    CREATE INDEX IF NOT EXISTS infra_feature_layer ON features(layer_id);
    CREATE VIRTUAL TABLE IF NOT EXISTS infrastructure_spatial USING rtree(fid,minx,maxx,miny,maxy);
    CREATE TRIGGER IF NOT EXISTS infra_feature_ins AFTER INSERT ON features BEGIN INSERT INTO infrastructure_spatial(fid,minx,maxx,miny,maxy) VALUES(new.fid,new.minx,new.maxx,new.miny,new.maxy); END;
    CREATE TRIGGER IF NOT EXISTS infra_feature_del AFTER DELETE ON features BEGIN DELETE FROM infrastructure_spatial WHERE fid=old.fid; END;
    CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY,source_id TEXT NOT NULL,layer_id TEXT NOT NULL,bbox TEXT NOT NULL,status TEXT NOT NULL,offset INTEGER NOT NULL DEFAULT 0,received INTEGER NOT NULL DEFAULT 0,error TEXT NOT NULL DEFAULT '',created TEXT NOT NULL,updated TEXT NOT NULL);
    ''')
    # Additive upgrade from i685: never recreate or drop the persistent database.
    if 'color' not in {row[1] for row in con.execute('PRAGMA table_info(layers)')}: con.execute("ALTER TABLE layers ADD COLUMN color TEXT NOT NULL DEFAULT ''")
    # i687: migrate legacy category hide exactly once, preserving existing state.
    category_columns={row[1] for row in con.execute('PRAGMA table_info(categories)')}
    if 'hidden_online' not in category_columns:
        con.execute('ALTER TABLE categories ADD COLUMN hidden_online INTEGER NOT NULL DEFAULT 0')
        con.execute('UPDATE categories SET hidden_online=hidden')
    if 'hidden_offline' not in category_columns:
        con.execute('ALTER TABLE categories ADD COLUMN hidden_offline INTEGER NOT NULL DEFAULT 0')
        con.execute('UPDATE categories SET hidden_offline=hidden')
    # Per-layer zoom; only existing built-in County manholes get the new default.
    layer_columns={row[1] for row in con.execute('PRAGMA table_info(layers)')}
    if 'min_zoom' not in layer_columns:
        con.execute('ALTER TABLE layers ADD COLUMN min_zoom INTEGER DEFAULT NULL')
        con.execute('UPDATE layers SET min_zoom=14 WHERE id=?',('lacounty-sewer-manholes',))

    for i,(key,label) in enumerate(BUILTINS):
        con.execute('INSERT OR IGNORE INTO categories(id,label,builtin,position) VALUES(?,?,1,?)',(key,label,i))
    for key,cat,name,url,kind in SOURCES:
        default_zoom = 14 if key in ('lacounty-sewer-manholes','lacity-sewer-structures') else None
        con.execute('INSERT OR IGNORE INTO layers(id,category_id,name,mode,url,kind,created,updated,enabled,min_zoom) VALUES(?,?,?,?,?,?,?,?,0,?)',
                    (key,cat,name,'online',url,kind,now(),now(),default_zoom))
    con.commit()
    return con


@contextmanager
def _db():
    con=_connect()
    try:
        yield con
        con.commit()
    except BaseException:
        con.rollback()
        raise
    finally:
        con.close()


def _row(row): return dict(row)


def catalog():
    with DB_LOCK:
        with _db() as c:
            cats=[_row(x) for x in c.execute('SELECT * FROM categories ORDER BY position,label')]
            layers=[_row(x) for x in c.execute("SELECT layers.*, (SELECT COUNT(*) FROM features WHERE layer_id=layers.id) AS feature_count FROM layers ORDER BY name")]
            # Recover persisted jobs after a service restart; staging remains intact.
            for pending in c.execute("SELECT id FROM jobs WHERE status='running'").fetchall():
                if pending['id'] not in ACTIVE:
                    c.execute("UPDATE jobs SET status='interrupted',error='Server restarted; resume download',updated=? WHERE id=?",(now(),pending['id']))
            jobs=[_row(x) for x in c.execute('SELECT * FROM jobs ORDER BY created DESC LIMIT 50')]
    for x in layers:
        x['metadata']=json.loads(x['metadata'] or '{}')
    return {'ok':True,'categories':cats,'layers':layers,'jobs':jobs,'version':'i687',
            'download_bandwidth_limit':None,'server_store':str(_root())}


def _category(c, category):
    if c.execute('SELECT 1 FROM categories WHERE id=?',(category,)).fetchone() is None:
        raise ValueError('Choose an existing infrastructure category')


def mutate(payload):
    op=str(payload.get('op') or '').lower()
    with DB_LOCK:
        with _db() as c:
            if op=='category-create':
                name=str(payload.get('name') or '').strip()[:100]
                if not name:raise ValueError('Category name required')
                key='custom-'+uuid.uuid4().hex[:16]
                position=c.execute('SELECT COALESCE(MAX(position),0)+1 FROM categories').fetchone()[0]
                c.execute('INSERT INTO categories(id,label,position) VALUES(?,?,?)',(key,name,position))
            elif op=='category-rename':
                key=str(payload.get('id') or '')
                name=str(payload.get('name') or '').strip()[:100]
                if not name:raise ValueError('Category name required')
                c.execute('UPDATE categories SET label=? WHERE id=?',(name,key))
                if not c.total_changes:raise ValueError('Category not found')
            elif op=='category-hide':
                mode=payload.get('mode')
                if mode not in ('online','offline'):raise ValueError('Online or Offline mode is required for category visibility')
                key=str(payload.get('id') or '')
                if not c.execute('SELECT 1 FROM categories WHERE id=?',(key,)).fetchone():raise ValueError('Category not found')
                c.execute('UPDATE categories SET hidden_'+mode+'=? WHERE id=?',(int(bool(payload.get('hidden'))),key))
            elif op=='category-delete':
                key=str(payload.get('id') or '')
                row=c.execute('SELECT builtin FROM categories WHERE id=?',(key,)).fetchone()
                if not row:raise ValueError('Category not found')
                if row[0]:raise ValueError('Built-in categories can be hidden, not deleted')
                if c.execute('SELECT COUNT(*) FROM layers WHERE category_id=?',(key,)).fetchone()[0]:
                    raise ValueError('Category contains layers; move or delete those layers first')
                c.execute('DELETE FROM categories WHERE id=?',(key,))
            elif op=='layer-add':
                cat=str(payload.get('category_id') or '');_category(c,cat)
                name=str(payload.get('name') or '').strip()[:160]
                url=_source_url(str(payload.get('url') or ''))
                if not name:raise ValueError('Layer name required')
                key='source-'+uuid.uuid4().hex
                c.execute('INSERT INTO layers(id,category_id,name,mode,url,kind,created,updated,enabled) VALUES(?,?,?,?,?,?,?,?,1)',(key,cat,name,'online',url,str(payload.get('kind') or 'other')[:30],now(),now()))
            elif op=='layer-rename':
                name=str(payload.get('name') or '').strip()[:160]
                if not name:raise ValueError('Name required')
                c.execute('UPDATE layers SET name=? WHERE id=?',(name,str(payload.get('id') or '')))
            elif op=='layer-move':
                cat=str(payload.get('category_id') or '');_category(c,cat)
                c.execute('UPDATE layers SET category_id=? WHERE id=?',(cat,str(payload.get('id') or '')))
            elif op=='layer-hide':
                c.execute('UPDATE layers SET hidden=? WHERE id=?',(int(bool(payload.get('hidden'))),str(payload.get('id') or '')))
            elif op=='layer-delete':
                key=str(payload.get('id') or '')
                if key in {source[0] for source in SOURCES}:
                    c.execute('UPDATE layers SET hidden=1,enabled=0 WHERE id=?',(key,))
                else:
                    c.execute('DELETE FROM features WHERE layer_id=?',(key,))
                    c.execute('DELETE FROM layers WHERE id=?',(key,))
            elif op=='layer-enable':
                c.execute('UPDATE layers SET enabled=? WHERE id=?',(int(bool(payload.get('enabled'))),str(payload.get('id') or '')))
            elif op=='layer-minzoom':
                key=str(payload.get('id') or '')
                if not c.execute('SELECT 1 FROM layers WHERE id=?',(key,)).fetchone():raise ValueError('Infrastructure layer not found')
                requested=payload.get('min_zoom')
                if requested is None or requested=='': zoom=None
                else:
                    if isinstance(requested,bool) or not isinstance(requested,int) or not 0<=requested<=22:
                        raise ValueError('Minimum zoom must be an integer between 0 and 22, or Always')
                    zoom=requested
                c.execute('UPDATE layers SET min_zoom=?,updated=? WHERE id=?',(zoom,now(),key))
            elif op=='layer-color':
                key=str(payload.get('id') or '')
                requested=str(payload.get('color') or '').strip()
                if requested and not re.fullmatch(r'#[0-9A-Fa-f]{6}',requested):
                    raise ValueError('Layer color must be a six-digit HEX color')
                if not c.execute('SELECT 1 FROM layers WHERE id=?',(key,)).fetchone():
                    raise ValueError('Infrastructure layer not found')
                c.execute('UPDATE layers SET color=?,updated=? WHERE id=?',(requested.lower(),now(),key))
            else:raise ValueError('Unsupported infrastructure operation')
    return catalog()


def _source_url(url):
    url=url.strip().rstrip('/')
    p=urlparse(url)
    if p.scheme!='https' or not p.hostname or p.username or p.password or p.port not in (None,443):
        raise ValueError('Use an HTTPS public ArcGIS FeatureServer layer URL')
    if not (p.path.rstrip('/').endswith('/FeatureServer/0') or '/FeatureServer/' in p.path or '/MapServer/' in p.path):
        raise ValueError('Source must be an ArcGIS REST FeatureServer or MapServer layer')
    if p.query or p.fragment:raise ValueError('Use a service layer URL without query arguments')
    infos=socket.getaddrinfo(p.hostname,443,type=socket.SOCK_STREAM)
    if not infos or any(not ipaddress.ip_address(info[4][0]).is_global for info in infos):
        raise ValueError('Private/local service endpoints are not accepted by default')
    return url


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Provider redirects must be configured as the explicit layer URL')


def _get_json(url,params):
    source=_source_url(url)
    url=source+'/query?'+urlencode(params)
    req=Request(url,headers={'Accept':'application/geo+json, application/json','User-Agent':'TAK-Map-Infrastructure/1.4.0-i687'})
    opener=build_opener(_NoRedirect)
    with opener.open(req,timeout=35) as r:
        if int(r.headers.get('Content-Length') or 0)>MAX_HTTP_BODY:
            raise ValueError('Provider response page exceeds safety limit')
        data=r.read(MAX_HTTP_BODY+1)
        if len(data)>MAX_HTTP_BODY:raise ValueError('Provider page exceeds safety limit')
    result=json.loads(data)
    if result.get('error'):
        raise RuntimeError('GIS provider error: '+str(result['error'].get('message') or result['error'])[:250])
    if result.get('type')!='FeatureCollection' or not isinstance(result.get('features'),list):
        raise ValueError('Provider did not return GeoJSON features; check layer endpoint capabilities')
    return result


def bbox_parse(raw):
    if isinstance(raw,str): raw=raw.split(',')
    if not isinstance(raw,(list,tuple)) or len(raw)!=4:raise ValueError('Bounding box must be west,south,east,north')
    b=[float(v) for v in raw]
    if not all(math.isfinite(v) for v in b) or not(-180<=b[0]<b[2]<=180 and -90<=b[1]<b[3]<=90):
        raise ValueError('Invalid geographic bounds')
    return b


def _query_online(source,bbox,offset=0,count=PAGE_SIZE):
    return _get_json(source['url'],{'where':'1=1','geometry':','.join(map(str,bbox)),
        'geometryType':'esriGeometryEnvelope','spatialRel':'esriSpatialRelIntersects',
        'inSR':4326,'outSR':4326,'outFields':'*','returnGeometry':'true',
        'resultOffset':int(offset),'resultRecordCount':int(count),'f':'geojson'})



def get_count(layer_id,mode,bbox,zoom=None):
    """Count online features in one viewport; bounded response, never fetches geometry."""
    bounds=bbox_parse(bbox)
    with _db() as con: source=_source(con,layer_id,mode)
    if source['mode']!='online':raise ValueError('Counts are only available for online GIS services')
    if zoom is not None and source['min_zoom'] is not None and float(zoom)<source['min_zoom']:
        return {'ok':True,'count':0,'layer_id':layer_id,'below_min_zoom':True}
    url=_source_url(source['url'])+'/query?'+urlencode({
        'where':'1=1','geometry':','.join(map(str,bounds)),
        'geometryType':'esriGeometryEnvelope','spatialRel':'esriSpatialRelIntersects',
        'inSR':4326,'returnCountOnly':'true','f':'json'})
    req=Request(url,headers={'Accept':'application/json','User-Agent':'TAK-Map-Infrastructure/1.4.0-i687'})
    with build_opener(_NoRedirect).open(req,timeout=20) as res:
        if int(res.headers.get('Content-Length') or 0)>1024*1024:raise ValueError('Provider count response too large')
        data=res.read(1024*1024+1)
    if len(data)>1024*1024:raise ValueError('Provider count response too large')
    body=json.loads(data)
    if 'error' in body:raise RuntimeError('GIS provider count error')
    if not isinstance(body.get('count'),int) or body['count']<0:raise ValueError('GIS provider does not support count queries')
    return {'ok':True,'count':body['count'],'layer_id':layer_id}

def _walk(coords):
    if isinstance(coords,(list,tuple)) and len(coords)>=2 and all(isinstance(v,(int,float)) for v in coords[:2]):
        yield float(coords[0]),float(coords[1])
    elif isinstance(coords,(list,tuple)):
        for part in coords: yield from _walk(part)


def _extent(geom):
    if not isinstance(geom,dict):raise ValueError('Missing feature geometry')
    pts=list(_walk(geom.get('coordinates')))
    if not pts or not all(math.isfinite(x) and math.isfinite(y) and -180<=x<=180 and -90<=y<=90 for x,y in pts):
        raise ValueError('Geometry must contain WGS84 longitude/latitude values')
    xs=[p[0] for p in pts];ys=[p[1] for p in pts]
    return min(xs),max(xs),min(ys),max(ys)


def _diameter(props):
    for key,value in props.items():
        name=str(key).upper().replace(' ','_')
        if name not in ('PIPE_DIAMETER','DIAMETER','DIAM','DIAMETER_IN','DIAMETER_MM','DIAMETER_CM','DIAMETER_FT','PIPE_DIA','DIA_IN','NOMINAL_DIAMETER'):continue
        try:
            if isinstance(value,str):
                import re
                match=re.search(r'\d+(?:\.\d+)?',value.replace(',',''))
                if not match:continue
                number=float(match.group(0))
                unit='mm' if 'mm' in value.lower() else 'cm' if 'cm' in value.lower() else 'ft' if ('feet' in value.lower() or ' ft' in value.lower()) else 'in'
            else:number=float(value);unit='in'
            if name.endswith('_MM'):unit='mm'
            elif name.endswith('_CM'):unit='cm'
            elif name.endswith('_FT'):unit='ft'
            number *= {'in':1,'mm':1/25.4,'cm':1/2.54,'ft':12}[unit]
            if 0<number<1500:return round(number,2)
        except (ValueError,TypeError,OverflowError):pass
    return None


def _passes(feature,kind,min_diameter):
    if kind!='sewer' or min_diameter<=0:return True
    d=_diameter(feature.get('properties') or {})
    return d is not None and d>=min_diameter


def _source(c, key,mode=None):
    row=c.execute('SELECT * FROM layers WHERE id=?',(key,)).fetchone()
    if not row or (mode and row['mode']!=mode):raise ValueError('Infrastructure layer not found in selected mode')
    return _row(row)


def _display_geometry(geometry, remaining):
    # Limit display vertices only; persisted and exported geometry remains unchanged.
    gtype=geometry.get('type')
    coords=geometry.get('coordinates')
    count=sum(1 for _ in _walk(coords))
    if count<=min(MAX_FEATURE_VERTICES,remaining):return geometry,count,False
    if min(MAX_FEATURE_VERTICES,remaining)<2:return None,0,True
    # Sample long linework without losing endpoints. Avoid simplifying point-only objects.
    def decimate_line(line, cap):
        if len(line)<=cap:return line
        positions=sorted(set(round(i*(len(line)-1)/(cap-1)) for i in range(cap)))
        return [line[i] for i in positions]
    def thinner(data, cap):
        if isinstance(data,list) and len(data)>=2 and isinstance(data[0],list) and len(data[0])>=2 and isinstance(data[0][0],(int,float)):
            return decimate_line(data,max(2,cap))
        if isinstance(data,list):
            if not data:return data
            result=[]
            for part in data:
                result.append(thinner(part,max(2,cap//len(data))))
            return result
        return data
    if gtype=='Point':return geometry,1,False
    if gtype in ('LineString','MultiLineString','Polygon','MultiPolygon'):
        reduced={**geometry,'coordinates':thinner(coords,min(MAX_FEATURE_VERTICES,remaining))}
        kept=sum(1 for _ in _walk(reduced.get('coordinates')))
        if kept<=remaining:return reduced,kept,True
    return None,0,True


def _pack_view_features(items, source, bbox, raw_limited=False, total_stored=None):
    out=[];vertices=0;geometry_limited=False;seen=set()
    for item in items:
        if len(out)>=MAX_VIEWPORT_FEATURES:raw_limited=True;break
        fid=str(item.get('id',''))
        if fid in seen:continue
        seen.add(fid)
        if not item.get('geometry'):continue
        geom,n,was_changed=_display_geometry(item['geometry'],MAX_DISPLAY_VERTICES-vertices)
        if geom is None:
            geometry_limited=True
            continue
        vertices+=n
        if was_changed:geometry_limited=True
        out.append({**item,'geometry':geom})
    limited=bool(raw_limited)
    return {'ok':True,'features':out,'loaded_count':len(out),
            'partial':limited,'limited':limited,'feature_cap_reached':limited,
            'geometry_simplified':geometry_limited,'vertex_budget_reached':vertices>=MAX_DISPLAY_VERTICES,
            'provider_paging_incomplete':False,'buffered_count':len(out),
            'source':source['name'],'mode':source['mode'],'bbox':bbox,
            'total_stored':total_stored,'vertex_count':vertices}


def get_features(layer_id, mode, bbox, minimum=36, offset=0, chunk=0, zoom=None):
    # Bounded spatial display query, never used by manual downloads.
    bounds=bbox_parse(bbox)
    with _db() as c:source=_source(c,layer_id,mode)
    if zoom is not None and source['min_zoom'] is not None and float(zoom)<source['min_zoom']:
        result=_pack_view_features([],source,bounds,False,total_stored=None)
        result['below_min_zoom']=True
        return result
    if source['mode']=='online' and chunk:
        # One bounded provider page per call. The browser can progressively draw
        # results and abort obsolete pans rather than waiting for all pages.
        requested=max(1,min(PAGE_SIZE,MAX_VIEWPORT_FEATURES,int(chunk)))
        start=max(0,int(offset))
        page=_query_online(source,bounds,start,requested)
        rows=page['features']
        if len(rows)>requested:raise ValueError('Provider exceeded requested page size')
        more=(len(rows)>=requested or bool(page.get('exceededTransferLimit')))
        accepted=[x for x in rows if _passes(x,source['kind'],minimum)]
        result=_pack_view_features(accepted,source,bounds,False)
        result['partial']=more or result['partial']
        result['has_more']=more
        result['limited']=bool(result['feature_cap_reached'])
        result['provider_paging_incomplete']=False
        result['next_offset']=start+len(rows) if more and rows else None
        result['source_status']='loading' if more else 'ready'
        return result
    if source['mode']=='online':
        out=[];position=max(0,int(offset));pages=0;more=True;last_page_size=0
        while len(out)<=MAX_VIEWPORT_FEATURES and pages<MAX_PROVIDER_PAGES:
            count=min(PAGE_SIZE,MAX_VIEWPORT_FEATURES+1-len(out)) if source['kind']!='sewer' else PAGE_SIZE
            # Request fewer records on the last page. Provider may return fewer than requested.
            page=_query_online(source,bounds,position,max(1,count))
            rows=page['features'];pages+=1;last_page_size=len(rows)
            out.extend(x for x in rows if _passes(x,source['kind'],minimum))
            position+=len(rows)
            if not rows or (len(rows)<count and not page.get('exceededTransferLimit')):
                more=False;break
        limited=len(out)>MAX_VIEWPORT_FEATURES or more
        result=_pack_view_features(out[:MAX_VIEWPORT_FEATURES],source,bounds,limited)
        result['next_offset']=position if limited else None
        result['provider_paging_incomplete']=bool(more and pages>=MAX_PROVIDER_PAGES and len(out)<MAX_VIEWPORT_FEATURES)
        result['source_status']='limit' if result['feature_cap_reached'] else 'partial' if result['provider_paging_incomplete'] else 'ready'
        return result
    with _db() as c:
        total=c.execute('SELECT COUNT(*) FROM features WHERE layer_id=?',(layer_id,)).fetchone()[0]
        query='''FROM features f JOIN infrastructure_spatial r ON f.fid=r.fid
                 WHERE f.layer_id=? AND r.minx<=? AND r.maxx>=? AND r.miny<=? AND r.maxy>=?'''
        params=(layer_id,bounds[2],bounds[0],bounds[3],bounds[1])
        # COUNT is index-backed and does not deserialize geometry, even for huge datasets.
        matching=c.execute('SELECT COUNT(*) '+query,params).fetchone()[0]
        raw_limited=matching>MAX_VIEWPORT_FEATURES
        rows=[]
        if not raw_limited:
            rows=c.execute('SELECT f.geometry,f.properties,f.feature_key '+query+' ORDER BY f.fid',params).fetchall()
        else:
            # One bounded indexed query instead of dozens of RTree scans.
            # The deterministic spatial+fid hash samples across the complete
            # matching extent, rather than the first 5,000 source rows.
            width=max(1e-8,bounds[2]-bounds[0]);height=max(1e-8,bounds[3]-bounds[1])
            order=''' ORDER BY (((CAST((f.minx - ?) * 8 / ? AS INTEGER) * 73)
                      + (CAST((f.miny - ?) * 8 / ? AS INTEGER) * 37)
                      + ((f.fid * 3571) % 8191)) % 8191),f.fid LIMIT ?'''
            rows=c.execute('SELECT f.geometry,f.properties,f.feature_key '+query+order,
                           params+(bounds[0],width,bounds[1],height,MAX_VIEWPORT_FEATURES)).fetchall()
        items=[]
        for row in rows:
            f={'type':'Feature','id':row['feature_key'],'geometry':json.loads(row['geometry']),
               'properties':json.loads(row['properties'])}
            if _passes(f,source['kind'],minimum):items.append(f)
        result=_pack_view_features(items,source,bounds,raw_limited,total)
        result['source_status']='limited' if result['limited'] else 'ready'
        return result


def _write_features(c,layer_id,features,start=0):
    added=0
    for i,f in enumerate(features):
        if not isinstance(f,dict) or f.get('type')!='Feature':continue
        geom=f.get('geometry')
        if not geom:continue
        try:ext=_extent(geom)
        except (ValueError,TypeError):continue
        props=f.get('properties') if isinstance(f.get('properties'),dict) else {}
        k=str(f.get('id') if f.get('id') is not None else start+i)[:200]
        c.execute('INSERT OR REPLACE INTO features(layer_id,feature_key,geometry,properties,minx,maxx,miny,maxy) VALUES(?,?,?,?,?,?,?,?)',
            (layer_id,k,json.dumps(geom,separators=(',',':')),json.dumps(props,default=str,separators=(',',':')),*ext))
        added+=1
    return added


def _rename_download(c,job):
    state=c.execute('SELECT status FROM jobs WHERE id=?',(job['id'],)).fetchone()
    if not state or state[0]!='running':return
    staging=job['layer_id'];source=_source(c,job['source_id'],'online')
    target='offline-'+job['id']
    c.execute('INSERT INTO layers(id,category_id,name,mode,kind,parent_id,created,updated,metadata,enabled,color) VALUES(?,?,?,?,?,?,?,?,?,1,?)',
              (target,source['category_id'],source['name']+' (download)','offline',source['kind'],source['id'],now(),now(),json.dumps({'bbox':json.loads(job['bbox']),'provider':source['url'],'downloaded':now()}),source.get('color') or ''))
    c.execute('UPDATE features SET layer_id=? WHERE layer_id=?',(target,staging))
    c.execute('UPDATE jobs SET status=?,updated=? WHERE id=?',('complete',now(),job['id']))


def _download(job_id):
    with DB_LOCK:
        with _db() as c:
            row=c.execute('SELECT * FROM jobs WHERE id=?',(job_id,)).fetchone()
            if not row:return
            job=_row(row)
            if job['status']=='canceled':
                ACTIVE.pop(job_id,None)
                return
            c.execute('UPDATE jobs SET status=?,error=?,updated=? WHERE id=?',('running','',now(),job_id))
    try:
        source_id=job['source_id'];bbox=bbox_parse(json.loads(job['bbox']));cursor=job['offset'];stage=job['layer_id']
        with _db() as c:source=_source(c,source_id,'online')
        while True:
            with _db() as c:
                status=c.execute('SELECT status FROM jobs WHERE id=?',(job_id,)).fetchone()
                if not status or status[0]=='canceled':return
            # Retry only transient provider errors; no app-side bandwidth throttling.
            for attempt in range(4):
                try:
                    page=_query_online(source,bbox,cursor,PAGE_SIZE)
                    break
                except HTTPError as http_error:
                    if http_error.code not in (429,502,503,504) or attempt==3:raise
                    time.sleep(min(2**attempt,8))
            rows=page['features']
            with DB_LOCK:
                with _db() as c:
                    row=c.execute('SELECT status FROM jobs WHERE id=?',(job_id,)).fetchone()
                    if not row or row[0]=='canceled':return
                    before=c.execute('SELECT COUNT(*) FROM features WHERE layer_id=?',(stage,)).fetchone()[0]
                    written=_write_features(c,stage,rows,start=cursor)
                    after=c.execute('SELECT COUNT(*) FROM features WHERE layer_id=?',(stage,)).fetchone()[0]
                    if rows and after<=before:raise ValueError('Provider pagination returned no new features; download incomplete')
                    cursor+=len(rows)
                    c.execute('UPDATE jobs SET offset=?,received=received+?,updated=? WHERE id=?',(cursor,written,now(),job_id))
            if not rows:
                with DB_LOCK:
                    with _db() as c:
                        _rename_download(c,job)
                return
    except Exception as ex:
        with DB_LOCK:
            with _db() as c:c.execute("UPDATE jobs SET status=?,error=?,updated=? WHERE id=? AND status!='canceled'",('interrupted',str(ex)[:500],now(),job_id))
    finally:
        ACTIVE.pop(job_id,None)


def job_action(payload):
    op=str(payload.get('op') or '')
    if op=='download-start':
        source_id=str(payload.get('source_id') or '');bbox=bbox_parse(payload.get('bbox'))
        with _db() as c:_source(c,source_id,'online')
        key=uuid.uuid4().hex
        with DB_LOCK:
            with _db() as c:
                c.execute('INSERT INTO jobs(id,source_id,layer_id,bbox,status,created,updated) VALUES(?,?,?,?,?,?,?)',
                          (key,source_id,'staging-'+key,json.dumps(bbox),'queued',now(),now()))
    else:
        key=str(payload.get('id') or '')
        with DB_LOCK:
            with _db() as c:
                row=c.execute('SELECT * FROM jobs WHERE id=?',(key,)).fetchone()
                if not row:raise ValueError('Unknown download')
                if op=='download-cancel':
                    if row['status']=='complete':raise ValueError('Completed datasets must be deleted as layers')
                    c.execute('UPDATE jobs SET status=?,updated=? WHERE id=?',('canceled',now(),key))
                    c.execute('DELETE FROM features WHERE layer_id=?',(row['layer_id'],))
                    return {'ok':True,'job_id':key,'status':'canceled'}
                if op!='download-resume':raise ValueError('Unsupported download operation')
                if row['status'] not in ('interrupted','queued'):raise ValueError('Only interrupted downloads may be resumed')
                if key in ACTIVE:raise ValueError('Download is already running')
    thread=threading.Thread(target=_download,args=(key,),daemon=True,name='infra-download-'+key[:8])
    ACTIVE[key]=thread;thread.start()
    return {'ok':True,'job_id':key}


def _iter_dataset(path):
    suffix=path.suffix.lower()
    if suffix in ('.geojson','.json'):
        data=json.loads(path.read_text('utf-8'))
        if data.get('type')=='FeatureCollection':
            for f in data.get('features',[]):yield f
        elif data.get('type')=='Feature':yield data
        else:raise ValueError('Only GeoJSON Feature or FeatureCollection is supported')
    elif suffix in ('.gpkg','.shp','.zip'):
        try:import fiona
        except ImportError:raise ValueError('GeoPackage and Shapefile imports require python3-fiona')
        if suffix=='.zip':
            # Do not extract arbitrary ZIP paths. Fiona reads local zipped shapefiles directly.
            with zipfile.ZipFile(path) as z:
                names=z.namelist()
                if not any(n.lower().endswith('.shp') for n in names):raise ValueError('ZIP must contain Shapefile .shp, .shx and .dbf')
                if any(n.startswith('/') or '..' in Path(n).parts for n in names):raise ValueError('Unsafe paths in Shapefile ZIP')
                if len(names)>1000 or sum(x.file_size for x in z.infolist())>MAX_UPLOAD_BYTES:
                    raise ValueError('Shapefile archive exceeds safety limits')
            source='zip://'+str(path)
        else:source=str(path)
        layers=fiona.listlayers(source)
        from fiona.model import to_dict
        try:from pyproj import Transformer, CRS
        except ImportError:Transformer=CRS=None
        for layername in layers:
            with fiona.open(source,layer=layername) as rows:
                transform=None
                if rows.crs and Transformer:
                    crs=CRS.from_user_input(rows.crs)
                    if crs.to_epsg()!=4326:transform=Transformer.from_crs(crs,'EPSG:4326',always_xy=True).transform
                elif rows.crs:
                    raise ValueError('pyproj required for non-WGS84 GIS imports')
                for row in rows:
                    geom= row.get('geometry')
                    if not geom:continue
                    geom=to_dict(geom)
                    if transform:
                        def tx(c):
                            if isinstance(c,(list,tuple)) and len(c)>=2 and all(isinstance(v,(int,float)) for v in c[:2]):
                                return list(transform(c[0],c[1]))+list(c[2:])
                            return [tx(a) for a in c]
                        geom['coordinates']=tx(geom['coordinates'])
                    yield {'type':'Feature','id':str(layername)+'/'+str(row.get('id')),'geometry':geom,'properties':dict(row.get('properties') or {})}
    elif suffix in ('.kml','.kmz'):
        import xml.etree.ElementTree as ET
        if suffix=='.kmz':
            with zipfile.ZipFile(path) as z:
                docs=[x for x in z.namelist() if x.lower().endswith('.kml')]
                if not docs:raise ValueError('KMZ contains no KML')
                if z.getinfo(docs[0]).file_size>MAX_HTTP_BODY:raise ValueError('KML too large')
                body=z.read(docs[0])
        else:body=path.read_bytes()
        root=ET.fromstring(body)
        ns={'k':'http://www.opengis.net/kml/2.2'}
        for p in root.findall('.//k:Placemark',ns):
            props={'name':p.findtext('k:name',default='',namespaces=ns),'description':p.findtext('k:description',default='',namespaces=ns)}
            for name,level in [('Point','Point'),('LineString','LineString'),('Polygon','Polygon')]:
                node=p.find('.//k:'+name+'/k:coordinates',ns)
                if node is None or not node.text:continue
                coords=[[float(v) for v in x.split(',')[:2]] for x in node.text.split()]
                if name=='Point':geom={'type':'Point','coordinates':coords[0]}
                elif name=='LineString':geom={'type':'LineString','coordinates':coords}
                else:geom={'type':'Polygon','coordinates':[coords]}
                yield {'type':'Feature','geometry':geom,'properties':props}
                break
    else:raise ValueError('Supported imports: GeoJSON, GeoPackage, Shapefile ZIP, KML, KMZ')


def import_dataset(path,category_id,name=None,kind='other'):
    path=Path(path)
    if not path.is_file():raise ValueError('Import file missing')
    key='import-'+uuid.uuid4().hex
    with _db() as c:_category(c,category_id)
    total=0
    try:
        with _db() as c:
            c.execute('INSERT INTO layers(id,category_id,name,mode,kind,created,updated,metadata,enabled) VALUES(?,?,?,?,?,?,?,?,1)',
                      (key,category_id,(name or path.stem)[:160],'offline',kind,now(),now(),json.dumps({'imported':now(),'original_file':path.name})))
        buffer=[]
        for i,feature in enumerate(_iter_dataset(path)):
            buffer.append(feature)
            if len(buffer)>=500:
                with _db() as c:total+=_write_features(c,key,buffer,start=i-len(buffer)+1)
                buffer=[]
        if buffer:
            with _db() as c:total+=_write_features(c,key,buffer,start=i-len(buffer)+1)
        if total==0:raise ValueError('No supported geographic features were found')
        return {'ok':True,'layer_id':key,'count':total}
    except Exception:
        with _db() as c:
            c.execute('DELETE FROM features WHERE layer_id=?',(key,));c.execute('DELETE FROM layers WHERE id=?',(key,))
        raise


def _all_features(layer_id):
    with _db() as c:
        src=_source(c,layer_id,'offline')
        cur=c.execute('SELECT geometry,properties,feature_key FROM features WHERE layer_id=? ORDER BY fid',(layer_id,))
        rows=cur.fetchall()
    return src,[{'type':'Feature','id':r['feature_key'],'geometry':json.loads(r['geometry']),'properties':json.loads(r['properties'])} for r in rows]


def export_dataset(layer_id,format):
    fmt=format.lower()
    if fmt not in ('geojson','gpkg','zip','kml','kmz'):raise ValueError('Supported exports: GeoPackage, GeoJSON, Shapefile ZIP, KML, KMZ')
    source,features=_all_features(layer_id)
    if not features:raise ValueError('There are no stored features to export')
    root=_root()/'exports';root.mkdir(parents=True,exist_ok=True)
    base='infrastructure-'+uuid.uuid4().hex[:16]
    path=root/(base+'.'+fmt)
    if fmt=='geojson':
        path.write_text(json.dumps({'type':'FeatureCollection','features':features,'metadata':{'source':source['name'],'exported':now()}},ensure_ascii=False),'utf-8')
    elif fmt in ('gpkg','zip'):
        try:import fiona
        except ImportError:raise ValueError('GeoPackage and Shapefile exports require python3-fiona')
        # Each output geometry family receives its own GIS layer.
        groups={}
        for f in features:groups.setdefault(f['geometry']['type'],[]).append(f)
        if fmt=='gpkg':
            for index,(geom,items) in enumerate(groups.items()):
                fields={}
                for f in items:
                    for key,value in f['properties'].items():
                        if value is not None:fields[str(key)[:40]]='str:254'
                schema={'geometry':geom,'properties':fields}
                with fiona.open(path,'w',driver='GPKG',crs='EPSG:4326',layer=('infra_'+str(index)),schema=schema) as dst:
                    for f in items:
                        props={k:(str(f['properties'].get(k))[:254] if f['properties'].get(k) is not None else None) for k in fields}
                        dst.write({'type':'Feature','geometry':f['geometry'],'properties':props})
        else:
            work=root/(base+'-shp');work.mkdir()
            files=[]
            try:
                for index,(geom,items) in enumerate(groups.items()):
                    target=work/('infra_'+str(index)+'.shp')
                    fields={}
                    for f in items:
                        for k,v in f['properties'].items():
                            if v is not None:fields[str(k)[:10]]='str:254'
                    with fiona.open(target,'w',driver='ESRI Shapefile',crs='EPSG:4326',schema={'geometry':geom,'properties':fields}) as dst:
                        for f in items:
                            dst.write({'type':'Feature','geometry':f['geometry'],'properties':{k:(str(f['properties'].get(k))[:254] if f['properties'].get(k) is not None else None) for k in fields}})
                    files.extend(work.glob('infra_'+str(index)+'.*'))
                with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
                    for file in files:z.write(file,arcname=file.name)
            finally:shutil.rmtree(work,ignore_errors=True)
    else:
        import xml.etree.ElementTree as ET
        kml=ET.Element('kml',xmlns='http://www.opengis.net/kml/2.2');doc=ET.SubElement(kml,'Document')
        for f in features:
            geom=f['geometry']; typ=geom.get('type')
            if typ not in ('Point','LineString','Polygon'):continue
            p=ET.SubElement(doc,'Placemark')
            ET.SubElement(p,'name').text=str(f['properties'].get('name') or source['name'])
            ET.SubElement(p,'description').text=json.dumps(f['properties'],ensure_ascii=False)
            shape=ET.SubElement(p,typ)
            coords=geom['coordinates']
            if typ=='Polygon':
                ring=ET.SubElement(ET.SubElement(shape,'outerBoundaryIs'),'LinearRing');shape=ring;coords=coords[0]
            if typ=='Point':coords=[coords]
            ET.SubElement(shape,'coordinates').text=' '.join(','.join(str(x) for x in pt[:2]) for pt in coords)
        body=ET.tostring(kml,encoding='utf-8',xml_declaration=True)
        if fmt=='kmz':
            with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:z.writestr('doc.kml',body)
        else:path.write_bytes(body)
    return path

# TAK Map i688: offline Infrastructure, non-destructive attribute filters, point symbols,
# indexed full-dataset search and exact feature retrieval. Append-only schema migration.
import heapq as _infra_heapq_i688

_i687_connect_i688 = _connect
_i687_catalog_i688 = catalog
_i687_mutate_i688 = mutate
_i687_features_i688 = get_features

FILTER_OPS_I688 = {'=', '!=', '>', '>=', '<', '<=', 'contains', 'not_contains',
                   'starts_with', 'ends_with', 'between', 'empty', 'not_empty'}

def _connect():
    c = _i687_connect_i688()
    fields = {r[1] for r in c.execute('PRAGMA table_info(layers)')}
    if 'filter_spec' not in fields:
        c.execute("ALTER TABLE layers ADD COLUMN filter_spec TEXT NOT NULL DEFAULT '{\"enabled\":false,\"mode\":\"all\",\"rules\":[]}'")
    if 'point_symbol_mode' not in fields:
        c.execute("ALTER TABLE layers ADD COLUMN point_symbol_mode TEXT NOT NULL DEFAULT 'dot'")
    if 'point_symbol_ref' not in fields:
        c.execute("ALTER TABLE layers ADD COLUMN point_symbol_ref TEXT NOT NULL DEFAULT ''")
    # The FTS index is derived and rebuildable; source features remain authoritative.
    try:
        c.execute("CREATE VIRTUAL TABLE IF NOT EXISTS infra_fts_i688 USING fts5(text, tokenize='unicode61')")
        c.executescript('''
          CREATE TRIGGER IF NOT EXISTS infra_fts_insert_i688 AFTER INSERT ON features BEGIN
            INSERT INTO infra_fts_i688(rowid,text) VALUES (new.fid, new.feature_key || ' ' || new.properties);
          END;
          CREATE TRIGGER IF NOT EXISTS infra_fts_delete_i688 AFTER DELETE ON features BEGIN
            DELETE FROM infra_fts_i688 WHERE rowid=old.fid;
          END;
          CREATE TRIGGER IF NOT EXISTS infra_fts_update_i688 AFTER UPDATE OF properties,feature_key ON features BEGIN
            DELETE FROM infra_fts_i688 WHERE rowid=old.fid;
            INSERT INTO infra_fts_i688(rowid,text) VALUES (new.fid, new.feature_key || ' ' || new.properties);
          END;
        ''')
        c.execute('CREATE TABLE IF NOT EXISTS infra_index_meta_i688 (key TEXT PRIMARY KEY,value TEXT NOT NULL)')
    except sqlite3.OperationalError:
        # Extremely old SQLite builds may lack FTS5. Search has a bounded fallback.
        pass
    c.commit()
    return c


def _validate_filter_i688(raw):
    if not isinstance(raw,dict): raise ValueError('Filter must be an object')
    rules=raw.get('rules',[])
    if not isinstance(rules,list) or len(rules)>12: raise ValueError('Maximum 12 filter rules per layer')
    mode=raw.get('mode','all')
    if mode not in ('all','any'): raise ValueError('Filter combination must be all or any')
    clean=[]
    for rule in rules:
        if not isinstance(rule,dict):raise ValueError('Invalid filter rule')
        field=rule.get('field')
        op=rule.get('op')
        if not isinstance(field,str) or not field.strip() or len(field)>128:
            raise ValueError('Each filter rule requires a valid GIS attribute')
        if op not in FILTER_OPS_I688:raise ValueError('Unsupported filter operator')
        kind=rule.get('type','auto')
        if kind not in ('auto','number','text','date'):raise ValueError('Invalid attribute data type')
        value=rule.get('value','')
        other=rule.get('other','')
        if op not in ('empty','not_empty'):
            if value is None or isinstance(value,(dict,list)) or len(str(value))>256:
                raise ValueError('Invalid filter value')
            if op=='between' and (other is None or isinstance(other,(dict,list)) or len(str(other))>256):
                raise ValueError('Invalid range endpoint')
            if op in ('>','>=','<','<=','between') and kind=='text':
                raise ValueError('Ordering requires numeric or date values')
        clean.append({'field':field.strip(),'op':op,'type':kind,'value':value,'other':other})
    return {'enabled':bool(raw.get('enabled',False)),'mode':mode,'rules':clean}


def _filters_i688(source):
    raw=source.get('filter_spec')
    if not raw:return {'enabled':False,'mode':'all','rules':[]}
    try:return _validate_filter_i688(json.loads(raw) if isinstance(raw,str) else raw)
    except (TypeError,ValueError):return {'enabled':False,'mode':'all','rules':[]}


def _num_i688(x):
    if isinstance(x,bool) or x is None:return None
    try:
        if isinstance(x,str) and not re.fullmatch(r'\s*[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\s*',x):return None
        z=float(x)
        return z if math.isfinite(z) else None
    except (ValueError,TypeError,OverflowError):return None


def _date_i688(x):
    if isinstance(x, (int,float)):return None
    try:return datetime.fromisoformat(str(x).replace('Z','+00:00'))
    except ValueError:return None


def _match_rule_i688(props, rule):
    field=rule['field']
    if field in props:val=props[field]
    else:val=next((v for k,v in props.items() if k.casefold()==field.casefold()),None)
    empty=val is None or val=='' or val==[]
    op=rule['op']
    if op=='empty':return empty
    if op=='not_empty':return not empty
    if empty:return False
    target=rule.get('value','')
    if op in ('contains','not_contains','starts_with','ends_with'):
        text=str(val).casefold();needle=str(target).casefold()
        return {'contains':needle in text,'not_contains':needle not in text,
                'starts_with':text.startswith(needle),'ends_with':text.endswith(needle)}[op]
    kind=rule.get('type','auto')
    a,b=_num_i688(val),_num_i688(target)
    if kind=='date' or (kind=='auto' and (a is None or b is None) and op in ('>','>=','<','<=','between')):
        da,db=_date_i688(val),_date_i688(target)
        if da is not None and db is not None:
            try:
                if op=='between':
                    dc=_date_i688(rule.get('other'))
                    return dc is not None and db<=da<=dc
                return {'>':da>db,'>=':da>=db,'<':da<db,'<=':da<=db,'=':da==db,'!=':da!=db}[op]
            except (TypeError,KeyError):return False
    if kind!='text' and a is not None and b is not None:
        if op=='between':
            c=_num_i688(rule.get('other'))
            return c is not None and b<=a<=c
        return {'>':a>b,'>=':a>=b,'<':a<b,'<=':a<=b,'=':a==b,'!=':a!=b}[op]
    if op not in ('=','!='):return False
    return str(val).casefold()==str(target).casefold() if op=='=' else str(val).casefold()!=str(target).casefold()


def _filter_passes_i688(props,source):
    spec=_filters_i688(source)
    if not spec['enabled'] or not spec['rules']:return True
    values=[_match_rule_i688(props,rule) for rule in spec['rules']]
    return all(values) if spec['mode']=='all' else any(values)


def catalog():
    result=_i687_catalog_i688()
    for src in result['layers']:
        src['filter_spec']=_filters_i688(src)
        try:src['point_symbol_ref']=json.loads(src.get('point_symbol_ref') or 'null')
        except ValueError:src['point_symbol_ref']=None
    result['version']='i688'
    result['online_rendering_enabled']=False
    return result


def mutate(payload):
    op=str(payload.get('op','')).lower()
    if op not in ('layer-filter','layer-symbol'):
        return _i687_mutate_i688(payload)
    key=str(payload.get('id') or '')
    with DB_LOCK:
        with _db() as c:
            source=_source(c,key,'offline')
            if op=='layer-filter':
                spec=_validate_filter_i688(payload.get('filter_spec') or {})
                c.execute('UPDATE layers SET filter_spec=?,updated=? WHERE id=?',
                          (json.dumps(spec,ensure_ascii=False),now(),key))
            else:
                if source['kind'] in ('line','sewer'):
                    raise ValueError('Point marker symbols are only valid for point layers')
                mode=str(payload.get('point_symbol_mode','dot'))
                if mode not in ('dot','registry'):raise ValueError('Choose Circle Dot or Icon Registry')
                icon=payload.get('point_symbol_ref')
                if mode=='registry':
                    if not isinstance(icon,dict) or icon.get('kind') not in ('milstd2525c','custom'):
                        raise ValueError('Choose a valid TAK Icon Registry symbol')
                    if len(json.dumps(icon))>15000:raise ValueError('Icon identity is too large')
                else:icon=None
                c.execute('UPDATE layers SET point_symbol_mode=?,point_symbol_ref=?,updated=? WHERE id=?',
                          (mode,json.dumps(icon) if icon else '',now(),key))
    return catalog()


def get_features(layer_id,mode,bbox,minimum=36,offset=0,chunk=0,zoom=None):
    if mode!='offline':raise ValueError('Map Infrastructure is offline-only; download online sources explicitly')
    bounds=bbox_parse(bbox)
    with _db() as c:source=_source(c,layer_id,'offline')
    if not source['enabled'] or source['hidden']:
        return _pack_view_features([],source,bounds,False,total_stored=0)
    if zoom is not None and source['min_zoom'] is not None and float(zoom)<source['min_zoom']:
        result=_pack_view_features([],source,bounds,False,total_stored=None)
        result['below_min_zoom']=True
        return result
    spec=_filters_i688(source)
    if (not spec['enabled'] or not spec['rules']) and not (source['kind']=='sewer' and minimum>0):
        return _i687_features_i688(layer_id,mode,bounds,minimum,offset,chunk,zoom)
    with _db() as c:
        total=c.execute('SELECT COUNT(*) FROM features WHERE layer_id=?',(layer_id,)).fetchone()[0]
        query='''SELECT f.fid,f.properties,f.minx,f.miny FROM features f
                 JOIN infrastructure_spatial r ON f.fid=r.fid
                 WHERE f.layer_id=? AND r.minx<=? AND r.maxx>=? AND r.miny<=? AND r.maxy>=?'''
        params=(layer_id,bounds[2],bounds[0],bounds[3],bounds[1])
        chosen=[];matching=0
        for item in c.execute(query,params):
            props=json.loads(item['properties'])
            if not _filter_passes_i688(props,source):continue
            if not _passes({'properties':props},source['kind'],minimum):continue
            matching+=1
            # Deterministic spatial spread without materializing every geometry.
            cellx=int((item['minx']-bounds[0])*8/max(bounds[2]-bounds[0],1e-9))
            celly=int((item['miny']-bounds[1])*8/max(bounds[3]-bounds[1],1e-9))
            rank=((cellx*73+celly*37+(item['fid']*3571)%8191)%8191)*10000000+item['fid']%10000000
            entry=(-rank,item['fid'])
            if len(chosen)<MAX_VIEWPORT_FEATURES:_infra_heapq_i688.heappush(chosen,entry)
            elif entry>chosen[0]:_infra_heapq_i688.heapreplace(chosen,entry)
        # Fetch only selected geometries; SQL's per-feature attributes are not truncated.
        fids=sorted(fid for _,fid in chosen)
        rows=[]
        for start in range(0,len(fids),500):
            chunk_ids=fids[start:start+500]
            placeholders=','.join('?' for _ in chunk_ids)
            rows.extend(c.execute('SELECT geometry,properties,feature_key FROM features WHERE fid IN ('+placeholders+')',chunk_ids).fetchall())
    items=[{'type':'Feature','id':r['feature_key'],'geometry':json.loads(r['geometry']),
            'properties':json.loads(r['properties'])} for r in rows]
    result=_pack_view_features(items,source,bounds,matching>MAX_VIEWPORT_FEATURES,total)
    result['matching_count']=matching
    result['source_status']='limited' if result['feature_cap_reached'] else 'ready'
    return result


def layer_fields(layer_id):
    with _db() as c:
        _source(c,layer_id,'offline')
        cur=c.execute('SELECT properties FROM features WHERE layer_id=? ORDER BY fid LIMIT 3000',(layer_id,))
        keys=set()
        for row in cur:
            keys.update(str(k) for k in json.loads(row['properties']))
    return {'ok':True,'layer_id':layer_id,'fields':sorted(keys,key=str.casefold)}


def _ensure_search_index_i688(c):
    try:
        found=c.execute("SELECT value FROM infra_index_meta_i688 WHERE key='backfill_complete'").fetchone()
        if found and found[0]=='1':return True
        # One-time additive backfill. Import/delete triggers keep it current thereafter.
        c.execute('INSERT OR IGNORE INTO infra_fts_i688(rowid,text) SELECT f.fid,f.feature_key || " " || f.properties FROM features f LEFT JOIN infra_fts_i688 idx ON idx.rowid=f.fid WHERE idx.rowid IS NULL')
        c.execute("INSERT OR REPLACE INTO infra_index_meta_i688(key,value) VALUES('backfill_complete','1')")
        return True
    except sqlite3.OperationalError:return False


def _eligible_i688(source,c):
    if source['mode']!='offline' or not source['enabled'] or source['hidden']:return False
    cat=c.execute('SELECT hidden_offline FROM categories WHERE id=?',(source['category_id'],)).fetchone()
    return bool(cat and not cat['hidden_offline'])


def feature_by_id(layer_id,feature_key,minimum=36):
    with _db() as c:
        source=_source(c,layer_id,'offline')
        if not _eligible_i688(source,c):raise ValueError('The Infrastructure layer is not enabled')
        r=c.execute('SELECT feature_key,geometry,properties,minx,maxx,miny,maxy FROM features WHERE layer_id=? AND feature_key=?',(layer_id,str(feature_key))).fetchone()
        if r is None:raise ValueError('Infrastructure object not found')
        properties=json.loads(r['properties'])
        f={'type':'Feature','id':r['feature_key'],'geometry':json.loads(r['geometry']),'properties':properties}
        if not _filter_passes_i688(properties,source) or not _passes(f,source['kind'],minimum):
            raise ValueError('Object does not match the active layer filter')
        return {'ok':True,'feature':f,'layer_id':layer_id,'bbox':[r['minx'],r['miny'],r['maxx'],r['maxy']],
                'min_zoom':source['min_zoom']}


def search_features(query,limit=24,minimum=36):
    query=str(query).strip()[:150]
    words=re.findall(r'[^\W_]+',query,flags=re.UNICODE)
    if not words:return {'ok':True,'results':[],'partial':False}
    limit=max(1,min(50,int(limit)))
    hits=[];partial=False
    with DB_LOCK:
        with _db() as c:
            fts=_ensure_search_index_i688(c)
            if fts:
                expression=' AND '.join('"'+w.replace('"','')+'"*' for w in words[:8])
                query_sql='''SELECT f.feature_key,f.properties,f.layer_id,f.minx,f.maxx,f.miny,f.maxy,
                          l.name AS layer_name,l.category_id,l.mode,l.enabled,l.hidden,l.kind,l.filter_spec,
                          cat.label AS category_label,cat.hidden_offline
                          FROM infra_fts_i688 JOIN features f ON f.fid=infra_fts_i688.rowid
                          JOIN layers l ON f.layer_id=l.id JOIN categories cat ON l.category_id=cat.id
                          WHERE infra_fts_i688 MATCH ? LIMIT 30000'''
                rows=c.execute(query_sql,(expression,))
            else:
                query_sql='''SELECT f.feature_key,f.properties,f.layer_id,f.minx,f.maxx,f.miny,f.maxy,
                           l.name AS layer_name,l.category_id,l.mode,l.enabled,l.hidden,l.kind,l.filter_spec,
                           cat.label AS category_label,cat.hidden_offline
                           FROM features f JOIN layers l ON f.layer_id=l.id
                           JOIN categories cat ON l.category_id=cat.id WHERE f.properties LIKE ? OR f.feature_key LIKE ? LIMIT 30000'''
                pattern='%'+query.replace('%','\\%').replace('_','\\_')+'%'
                rows=c.execute(query_sql,(pattern,pattern))
            checked=0
            for r in rows:
                checked+=1
                if r['mode']!='offline' or not r['enabled'] or r['hidden'] or r['hidden_offline']:continue
                props=json.loads(r['properties'])
                source={'kind':r['kind'],'filter_spec':r['filter_spec']}
                if not _filter_passes_i688(props,source) or not _passes({'properties':props},source['kind'],minimum):continue
                label=next((str(props[k]) for k in ('NAME','name','FACILITY_NAME','STRUCTURE_ID','PIPE_ID','MANHOLE_ID','STREET') if props.get(k) not in (None,'')),str(r['feature_key']))
                hits.append({'id':r['feature_key'],'layer_id':r['layer_id'],'label':label[:180],
                             'layer_name':r['layer_name'],'category':r['category_label'],
                             'bbox':[r['minx'],r['miny'],r['maxx'],r['maxy']]})
                if len(hits)>=limit:break
            partial=checked>=30000
    return {'ok':True,'results':hits,'partial':partial,'search_index':'fts5' if fts else 'fallback'}
