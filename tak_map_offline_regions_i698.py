"""Offline Maps geographic region and tile-span selection (i698).

Build-time county/state boundaries are bundled as GeoJSON; no GIS libraries or
network access are needed at runtime. The same polygons are served to the UI
and rasterized to XYZ tile spans for the downloader and estimator.
"""
from __future__ import annotations
from functools import lru_cache
from pathlib import Path
import json
import math

GEOJSON_PATH = Path(__file__).resolve().parent / 'assets' / 'tak-map-offline-us-regions-i698.json'
MERCATOR_MAX = 85.05112878

@lru_cache(maxsize=1)
def collection():
    data=json.loads(GEOJSON_PATH.read_text(encoding='utf-8'))
    if data.get('type')!='FeatureCollection' or len(data.get('features') or [])!=52:
        raise ValueError('Offline region boundary package is incomplete')
    return data

@lru_cache(maxsize=1)
def regions():
    return {f['id']:f for f in collection()['features']}

def catalog():
    return [{'id':f['id'],'label':f['properties']['name']} for f in collection()['features']]

def feature(region_id):
    return regions().get(str(region_id or '').strip())

def bounds_for_feature(f):
    xs=[];ys=[]
    for poly in f['geometry']['coordinates']:
        for ring in poly:
            for lon,lat in ring:
                xs.append(lon);ys.append(lat)
    return {'west':max(-180.0,min(xs)),'south':max(-MERCATOR_MAX,min(ys)),
            'east':min(180.0,max(xs)),'north':min(MERCATOR_MAX,max(ys))}

def _float_xy(lon,lat,z):
    n=2**int(z)
    lat=max(-MERCATOR_MAX,min(MERCATOR_MAX,float(lat)))
    x=(float(lon)+180.0)*n/360.0
    y=(1.0-math.asinh(math.tan(math.radians(lat)))/math.pi)*n/2.0
    return max(0.,min(float(n),x)),max(0.,min(float(n),y))

def _merge(spans,n):
    valid=[]
    for a,b in spans:
        lo=max(0,int(a));hi=min(n-1,int(b))
        if hi>=lo:valid.append((lo,hi))
    if not valid:return ()
    valid.sort()
    out=[]
    a,b=valid[0]
    for lo,hi in valid[1:]:
        if lo<=b+1:b=max(b,hi)
        else:out.append((a,b));a,b=lo,hi
    out.append((a,b))
    return tuple(out)

@lru_cache(maxsize=2)
def polygon_tile_spans(region_id,z):
    """Return sorted tuples (y,xmin,xmax) for tiles intersecting a region.

    Scan-convert polygon interiors at tile-row centers and include boundary
    segments explicitly. This retains thin peninsulas/islands and excludes
    bounding-box tiles over ocean or neighboring states. Long contiguous tile
    runs remain compressed instead of materializing millions of (z,x,y)s.
    """
    f=feature(region_id)
    if not f:raise ValueError('Unknown U.S. state or California region')
    z=int(z)
    if z<0 or z>19:raise ValueError('Invalid zoom')
    n=2**z
    tiles_by_y={}
    for poly in f['geometry']['coordinates']:
        # Per-polygon even-odd winding: inner rings exclude their interior.
        crossings={}
        boundary={}
        for ring in poly:
            pts=[_float_xy(lon,lat,z) for lon,lat in ring]
            if len(pts)<4:continue
            for (ax,ay),(bx,by) in zip(pts,pts[1:]):
                ylo=max(0,int(math.floor(min(ay,by))))
                yhi=min(n-1,int(math.floor(max(ay,by))))
                if yhi<ylo:continue
                if ay==by:
                    y=min(n-1,max(0,int(math.floor(ay))))
                    boundary.setdefault(y,[]).append((math.floor(min(ax,bx)),math.floor(max(ax,bx))))
                    continue
                for y in range(ylo,yhi+1):
                    b0=max(float(y),min(ay,by));b1=min(float(y+1),max(ay,by))
                    if b0<=b1:
                        x0=ax+(bx-ax)*(b0-ay)/(by-ay)
                        x1=ax+(bx-ax)*(b1-ay)/(by-ay)
                        boundary.setdefault(y,[]).append((math.floor(min(x0,x1)),math.floor(max(x0,x1))))
                    center=y+0.5
                    if min(ay,by)<=center<max(ay,by):
                        x=ax+(bx-ax)*(center-ay)/(by-ay)
                        crossings.setdefault(y,[]).append(x)
        for y in boundary.keys()|crossings.keys():
            runs=list(boundary.get(y,()))
            xs=sorted(crossings.get(y,()))
            for k in range(0,len(xs)-1,2):
                lo=math.ceil(xs[k]-.5);hi=math.floor(xs[k+1]-.5)
                if lo<=hi:runs.append((lo,hi))
            if runs:tiles_by_y.setdefault(y,[]).extend(runs)
    out=[]
    for y in sorted(tiles_by_y):
        for lo,hi in _merge(tiles_by_y[y],n):
            out.append((y,lo,hi))
    return tuple(out)

def rectangle_tile_spans(bounds,z):
    """Legacy Current View/Draw selection with exact existing rectangle bounds."""
    west,south,east,north=(float(bounds[k]) for k in ('west','south','east','north'))
    if east<west:west,east=east,west
    if north<south:south,north=north
    n=2**int(z)
    ax,ay=_float_xy(west,north,z);bx,by=_float_xy(east,south,z)
    xmin=max(0,min(n-1,int(ax)));xmax=max(0,min(n-1,int(bx)))
    ymin=max(0,min(n-1,int(ay)));ymax=max(0,min(n-1,int(by)))
    return tuple((y,xmin,xmax) for y in range(ymin,ymax+1))

def spans(area_id,bounds,min_zoom,max_zoom):
    for z in range(int(min_zoom),int(max_zoom)+1):
        rows=polygon_tile_spans(area_id,z) if area_id else rectangle_tile_spans(bounds,z)
        yield z,rows

def tile_total(area_id,bounds,min_zoom,max_zoom):
    return sum(hi-lo+1 for _,rows in spans(area_id,bounds,min_zoom,max_zoom) for _,lo,hi in rows)

def tiles(area_id,bounds,min_zoom,max_zoom):
    for z,rows in spans(area_id,bounds,min_zoom,max_zoom):
        for y,xmin,xmax in rows:
            for x in range(xmin,xmax+1):
                yield (z,x,y)
