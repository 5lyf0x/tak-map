#!/usr/bin/env python3
"""Build-only conversion of US counties bundled with Basemap into runtime polygon GeoJSON.
No GIS dependency is required to RUN TAK Map.
"""
import json
from pathlib import Path
import shapefile
from shapely.geometry import shape, Polygon, MultiPolygon, GeometryCollection, LineString, box
from shapely.ops import unary_union, split, transform
import mpl_toolkits.basemap as b

path=Path(__file__).resolve().parents[1]/'assets/tak-map-offline-us-regions-i698.json'
r=shapefile.Reader(str(Path(b.basemap_datadir)/'UScounties.shp'),encoding='latin1')
state={}; ca=[]
for sr in r.iterShapeRecords():
    code=sr.record['STATE']; name=sr.record['NAME']
    if code in {'PR','DC'}: continue
    geom=shape(sr.shape.__geo_interface__)
    state.setdefault(code,[]).append(geom)
    if code=='CA': ca.append((name,geom))
south={'Los Angeles','Orange','San Diego','Riverside','San Bernardino','Ventura','Santa Barbara','Imperial'}
central={'Monterey','San Benito','Santa Cruz','San Luis Obispo','Kern','Kings','Tulare','Fresno','Madera','Mariposa','Merced','Stanislaus','San Joaquin','Tuolumne','Calaveras','Amador','Alpine','Mono','Inyo'}
assert len(ca)==58 and len(south)==8 and len(central)==19
parts={s:unary_union(geoms) for s,geoms in state.items() if s!='CA'}
parts['CA-N']=unary_union([g for n,g in ca if n not in south|central])
parts['CA-C']=unary_union([g for n,g in ca if n in central])
parts['CA-S']=unary_union([g for n,g in ca if n in south])
# The Aleutians cross the antimeridian. Preserve both longitude wings in [-180,180].
def ak_wrapped(g):
    # Basemap counties use geographic polygons crossing 180. Wrap each vertex via
    # a continuous coordinate branch and split at -180 to avoid world-spanning bbox.
    def left(x,y,z=None):
        return (x-360 if x>0 else x,y) if z is None else (x-360 if x>0 else x,y,z)
    g=transform(left,g)
    left_half=g.intersection(box(-260,0,-180,90))
    right_half=g.intersection(box(-180,0,0,90))
    def shift(x,y,z=None):
        return (x+360,y) if z is None else (x+360,y,z)
    out=unary_union([right_half,transform(shift,left_half)])
    return out
parts['AK']=ak_wrapped(parts['AK'])

# Avoid exaggerating source accuracy. Keep 0.003-degree (~0.3km) geometric simplification;
# the 58 CA county geometries are unioned before simplification.
def polygons(g):
    if g.is_empty: return []
    if g.geom_type=='Polygon': return [g]
    if hasattr(g,'geoms'):
        out=[]
        for sub in g.geoms:out.extend(polygons(sub))
        return out
    return []

def rounded_ring(ring):
    coords=[[round(float(x),5),round(float(y),5)] for x,y in ring.coords]
    if coords and coords[-1]!=coords[0]:coords.append(coords[0])
    return coords
features=[]
names={'AL':'Alabama','AK':'Alaska','AZ':'Arizona','AR':'Arkansas','CO':'Colorado','CT':'Connecticut','DE':'Delaware','FL':'Florida','GA':'Georgia','HI':'Hawaii','ID':'Idaho','IL':'Illinois','IN':'Indiana','IA':'Iowa','KS':'Kansas','KY':'Kentucky','LA':'Louisiana','ME':'Maine','MD':'Maryland','MA':'Massachusetts','MI':'Michigan','MN':'Minnesota','MS':'Mississippi','MO':'Missouri','MT':'Montana','NE':'Nebraska','NV':'Nevada','NH':'New Hampshire','NJ':'New Jersey','NM':'New Mexico','NY':'New York','NC':'North Carolina','ND':'North Dakota','OH':'Ohio','OK':'Oklahoma','OR':'Oregon','PA':'Pennsylvania','RI':'Rhode Island','SC':'South Carolina','SD':'South Dakota','TN':'Tennessee','TX':'Texas','UT':'Utah','VT':'Vermont','VA':'Virginia','WA':'Washington','WV':'West Virginia','WI':'Wisconsin','WY':'Wyoming','CA-N':'Northern California','CA-C':'Central California','CA-S':'Southern California'}
assert len(names)==52 and set(names)==set(parts)
for code,g in sorted(parts.items(),key=lambda kv:names[kv[0]]):
    # Preserve islands/coastlines; complicated islands shorter than ~300m may be absent in the simplified source.
    g=g.simplify(.0015,preserve_topology=True)
    ps=polygons(g)
    coords=[[rounded_ring(p.exterior),*(rounded_ring(x) for x in p.interiors)] for p in ps if not p.is_empty]
    coords=[p for p in coords if p and len(p[0])>=4]
    features.append({'type':'Feature','id':code,'properties':{'id':code,'name':names[code]},'geometry':{'type':'MultiPolygon','coordinates':coords}})
obj={'type':'FeatureCollection','source':'Basemap UScounties shapefile, aggregated by state; California county partitions; simplified for tile coverage','features':features}
path.write_text(json.dumps(obj,separators=(',',':')),encoding='utf-8')
print('generated',path,'bytes',path.stat().st_size,'features',len(features))
print('CA county groups',len([n for n,_ in ca if n not in south|central]),len(central),len(south))
