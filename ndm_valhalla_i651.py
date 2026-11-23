"""TAK Map i651: operator-gated Valhalla 3.6.3 adapter; never auto-activates.

Graph configuration and service remain localhost-only; route requests never proxy user URLs.
"""
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import urllib.error
import urllib.request
import zipfile

from ndm_packages_i651 import Catalog,NDMError,sha256_file

VALHALLA_VERSION='3.6.3'
SERVICE_PORT=18882
VENDOR_BIN=Path('/opt/tak-map/vendor/valhalla-3.6.3/valhalla/bin/valhalla_service')


def _wheel_binary():
    val=os.environ.get('TAK_MAP_VALHALLA_BIN','').strip()
    return Path(val) if val else VENDOR_BIN


def _version_ok(binary):
    if not binary.is_file() or not os.access(binary,os.X_OK):return False
    try:
        p=subprocess.run([str(binary),'--version'],capture_output=True,text=True,timeout=8)
        return p.returncode==0 and VALHALLA_VERSION in (p.stdout+p.stderr)
    except (OSError,subprocess.TimeoutExpired):return False


def _require_graph(catalog,dataset_id):
    row=catalog.detail(dataset_id)
    if not row or row.get('type')!='routing' or row.get('valhalla_version')!=VALHALLA_VERSION:
        raise NDMError('A registered Valhalla 3.6.3 routing dataset must be selected','NO_GRAPH')
    zip_path=Path(row['zip_path'])
    if not zip_path.is_file() or sha256_file(zip_path)!=dataset_id:
        raise NDMError('Routing package was moved or checksum changed','GRAPH_MISMATCH')
    return row


def prepare_graph(catalog,dataset_id):
    row=_require_graph(catalog,dataset_id)
    root=catalog.root
    graph_dir=root/'graphs'/dataset_id
    graph_dir.parent.mkdir(parents=True,exist_ok=True)
    archive=graph_dir/'valhalla_tiles.tar'
    with zipfile.ZipFile(row['zip_path']) as z:
        cfg=json.loads(z.read('valhalla.json'))
        original=z.getinfo('valhalla_tiles.tar')
        if archive.is_file():
            # The source ZIP is checked above; verify already-extracted graph content as well.
            digest_path=graph_dir/'graph.sha256'
            existing_digest=sha256_file(archive)
            if not digest_path.is_file() or digest_path.read_text().strip()!=existing_digest:
                raise NDMError('Installed graph failed checksum verification','GRAPH_MISMATCH')
        else:
            tmp=Path(tempfile.mkdtemp(prefix='.graph-',dir=graph_dir.parent))
            try:
                h=hashlib.sha256()
                with z.open('valhalla_tiles.tar') as src,open(tmp/'valhalla_tiles.tar','wb') as dst:
                    for chunk in iter(lambda:src.read(1024*1024),b''):
                        dst.write(chunk);h.update(chunk)
                if (tmp/'valhalla_tiles.tar').stat().st_size!=original.file_size:
                    raise NDMError('Graph extraction truncated')
                (tmp/'graph.sha256').write_text(h.hexdigest()+'\n')
                tmp.rename(graph_dir)
            finally:
                if tmp.exists():shutil.rmtree(tmp)
    cfg=copy.deepcopy(cfg)
    cfg.setdefault('mjolnir',{})
    mj=cfg['mjolnir']
    mj['tile_extract']=str(archive)
    mj['tile_dir']=str(graph_dir/'tiles-disabled')
    mj['max_cache_size']=128*1024*1024
    mj['id_table_size']=64*1024*1024
    mj['use_lru_mem_cache']=True
    # stale resources must never refer to an NDM processing or world-wide external path
    for key in ('traffic_extract','admin','landmarks','timezone','transit_dir','transit_feeds_dir'):
        mj.pop(key,None)
    cfg.setdefault('httpd',{}).setdefault('service',{})
    httpd=cfg['httpd']['service']
    httpd['listen']=f'tcp://127.0.0.1:{SERVICE_PORT}'
    httpd['loopback']='ipc:///tmp/takmap-valhalla-loopback-i651'
    httpd['interrupt']='ipc:///tmp/takmap-valhalla-interrupt-i651'
    httpd['timeout_seconds']=25
    # Remove inherited NDM build-time elevation path and isolate service IPC sockets.
    cfg.setdefault('additional_data',{}).pop('elevation',None)
    for component in ('loki','thor','odin','meili'):
        service=cfg.setdefault(component,{}).setdefault('service',{})
        if 'proxy' in service:
            service['proxy']=f'ipc:///tmp/takmap-valhalla-{component}-i651'
    cfg.setdefault('service_limits',{})
    cfgdir=root/'prepared'
    cfgdir.mkdir(parents=True,exist_ok=True)
    config_file=cfgdir/(dataset_id+'.json')
    fd,tmp=tempfile.mkstemp(dir=cfgdir,prefix='.valhalla-',suffix='.tmp')
    try:
        with os.fdopen(fd,'w') as fp:
            json.dump(cfg,fp,sort_keys=True,indent=2)
            fp.flush();os.fsync(fp.fileno())
        os.replace(tmp,config_file)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    return {'dataset_id':dataset_id,'config_ready':True,'graph_size_bytes':archive.stat().st_size,
            'graph_sha256':(graph_dir/'graph.sha256').read_text().strip(),'service_listen':f'127.0.0.1:{SERVICE_PORT}',
            'valhalla_binary_installed':_version_ok(_wheel_binary()),'router_enabled':False}


def service_state(catalog=None):
    try:
        with urllib.request.urlopen(f'http://127.0.0.1:{SERVICE_PORT}/status',timeout=1.5) as r:
            ok=r.status==200
    except (OSError,urllib.error.URLError):ok=False
    state='ready' if ok else 'disabled'
    if not ok:
        try:
            result=subprocess.run(['systemctl','is-active','tak-map-valhalla.service'],capture_output=True,text=True,timeout=2)
            if result.stdout.strip() in ('activating','reloading'):
                state='starting'
            elif result.stdout.strip()=='failed':
                state='error'
        except (OSError,subprocess.TimeoutExpired):pass
    return {'router_state':state,'service_listen':f'127.0.0.1:{SERVICE_PORT}',
            'binary_ready':_version_ok(_wheel_binary()),'routing_enabled':ok,
            'activation':'operator-only','valhalla_version':VALHALLA_VERSION}


def _decode_polyline6(encoded):
    if not isinstance(encoded,str) or len(encoded)>4_000_000:raise NDMError('Invalid upstream route geometry')
    coords=[];lat=lon=idx=0
    while idx<len(encoded):
        values=[]
        for _ in (0,1):
            shift=num=0
            while True:
                if idx>=len(encoded) or shift>35:raise NDMError('Malformed Valhalla polyline')
                val=ord(encoded[idx])-63;idx+=1
                if val<0 or val>63:raise NDMError('Malformed Valhalla polyline')
                num|=(val&31)<<shift
                shift+=5
                if val<32:break
            values.append((~(num>>1)) if (num&1) else (num>>1))
        lat+=values[0];lon+=values[1]
        if abs(lat)>90_000_000 or abs(lon)>180_000_000:raise NDMError('Valhalla geometry outside geographic range')
        coords.append([lon/1e6,lat/1e6])
        if len(coords)>150000:raise NDMError('Route geometry exceeds limit')
    return coords


def route(locations,mode,unrestricted=False):
    if mode not in ('roads','offroad'):raise NDMError('Invalid routing mode')
    if not isinstance(locations,list) or not (2<=len(locations)<=20):raise NDMError('Specify 2–20 routing points')
    clean=[]
    for p in locations:
        if not isinstance(p,dict):raise NDMError('Invalid waypoint')
        try:lat=float(p['lat']);lon=float(p['lon'])
        except (ValueError,TypeError,KeyError):raise NDMError('Invalid waypoint coordinates')
        if not math.isfinite(lat) or not math.isfinite(lon) or abs(lat)>90 or abs(lon)>180:
            raise NDMError('Invalid waypoint coordinates')
        clean.append({'lat':lat,'lon':lon})
    data={'locations':clean,'costing':'auto','units':'kilometers','directions_options':{'units':'kilometers'},
          'shape_format':'polyline6'}
    if mode=='offroad':data['costing_options']={'auto':{'use_tracks':1.0}}
    if unrestricted:
        # Route editing: include all graph-represented road/track classes and
        # suppress access/direction/turn filters where the Valhalla build allows.
        # Does not invent absent graph edges or certify legal motor-vehicle access.
        data['costing_options']={'auto':{'exclude_unpaved':False,'use_tracks':1.0,
             'ignore_access':True,'ignore_oneways':True,'ignore_restrictions':True}}
    payload=json.dumps(data).encode('utf-8')
    req=urllib.request.Request(f'http://127.0.0.1:{SERVICE_PORT}/route',data=payload,method='POST',headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=25) as resp:
            raw=resp.read(6*1024*1024+1)
            if len(raw)>6*1024*1024:raise NDMError('Upstream routing response too large','REQUEST_LIMIT')
    except urllib.error.HTTPError as e:
        raise NDMError(f'Routing engine returned HTTP {e.code}','NO_DRIVABLE_PATH')
    except (OSError,urllib.error.URLError) as e:
        raise NDMError('Local Valhalla service is unavailable','ROUTER_UNAVAILABLE') from e
    parsed=json.loads(raw)
    trip=parsed.get('trip',{})
    coords=[]
    for leg in trip.get('legs',[]):
        legcoords=_decode_polyline6(leg.get('shape'))
        coords.extend(legcoords[1:] if coords and coords[-1]==legcoords[0] else legcoords)
    if len(coords)<2:raise NDMError('Valhalla produced no drivable route','NO_DRIVABLE_PATH')
    summary=trip.get('summary') or {}
    return {'ok':True,'geometry':{'type':'LineString','coordinates':coords},'distance_km':summary.get('length'),
            'time_seconds':summary.get('time'),'waypoints':clean,'mode':mode,
            'warning':'Off-road track preference is not proof of legal vehicle access.' if mode=='offroad' else None,
            'source':'local-valhalla-3.6.3'}


# i654 staged route editor: bounded nearest-road preview (localhost Valhalla only).
def snap_nearest_road(lat, lon):
    try:
        lat=float(lat);lon=float(lon)
    except (ValueError,TypeError):
        raise NDMError('Invalid waypoint coordinates','INVALID_WAYPOINT')
    if not math.isfinite(lat) or not math.isfinite(lon) or abs(lat)>90 or abs(lon)>180:
        raise NDMError('Invalid waypoint coordinates','INVALID_WAYPOINT')
    body=json.dumps({'locations':[{'lat':lat,'lon':lon}],'costing':'auto','verbose':False,
                     'costing_options':{'auto':{'exclude_unpaved':False,'use_tracks':1.0,
                         'ignore_access':True,'ignore_oneways':True,'ignore_restrictions':True}}},separators=(',',':')).encode()
    req=urllib.request.Request(f'http://127.0.0.1:{SERVICE_PORT}/locate',data=body,
                               method='POST',headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=6) as response:
            raw=response.read(131073)
            if len(raw)>131072:raise NDMError('Locate response too large','REQUEST_LIMIT')
    except urllib.error.HTTPError as e:
        raise NDMError(f'Routing engine returned HTTP {e.code}','NO_NEARBY_ROAD') from e
    except (OSError,urllib.error.URLError) as e:
        raise NDMError('Local routing service is unavailable','ROUTER_UNAVAILABLE') from e
    try:
        data=json.loads(raw)
        # Valhalla /locate returns an array for each requested location.
        row=data[0] if isinstance(data,list) and data else {}
        candidates=[(float(edge['correlated_lat']),float(edge['correlated_lon']))
                    for edge in row.get('edges',[]) if 'correlated_lat' in edge and 'correlated_lon' in edge]
        candidates=[(a,b) for a,b in candidates if math.isfinite(a) and math.isfinite(b) and abs(a)<=90 and abs(b)<=180]
        if not candidates:raise ValueError('No correlated road')
        def distance_m(point):
            a,b=point
            p1,p2=math.radians(lat),math.radians(a)
            dp,dl=p2-p1,math.radians(b-lon)
            h=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
            return 6371008.8*2*math.asin(min(1,math.sqrt(max(0,h))))
        nearest=min(candidates,key=distance_m)
        return {'ok':True,'lat':nearest[0],'lon':nearest[1],
                'distance_m':round(distance_m(nearest),2),'source':'local-valhalla-3.6.3'}
    except (KeyError,TypeError,ValueError,IndexError) as e:
        raise NDMError('No compatible mapped road near this point','NO_NEARBY_ROAD') from e
