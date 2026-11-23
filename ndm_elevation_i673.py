"""Read-only NDM terrain.sqlite viewshed sampling (i673).

Sources are exclusively registered NDM ZIPs. Extracted databases are immutable
TAK Map-owned cache files; original NDM archives are never changed. No elevation
sample is invented on nodata, missing coverage or decoding failure.
"""
from collections import OrderedDict
import array
import math
import os
from pathlib import Path
import shutil
import sqlite3
import struct
import sys
import threading
import zipfile
import zlib

class NdmElevationError(ValueError): pass

class Sampler:
    def __init__(self, catalog, cache_root=None):
        self.catalog=catalog
        self.root=Path(cache_root or os.environ.get('TAK_MAP_NDM_ELEVATION_CACHE','/var/lib/tak-map/ndm/elevation-cache'))
        self.lock=threading.RLock()
        self.processing=set()
        self.errors={}
        self.grids=OrderedDict()
        self.indexes={}
        self.inflight=threading.BoundedSemaphore(3)

    def entries(self):
        public=self.catalog.listing()
        with self.lock:
            raw=self.catalog._load()['datasets']
        entries=[]
        for item in public:
            sid=item.get('dataset_id')
            if (item.get('type')!='terrain' or not item.get('available') or item.get('superseded') or sid not in raw):continue
            entry=dict(item)
            entry['_source']=raw[sid].get('zip_path')
            entries.append(entry)
        entries.sort(key=lambda e:float(e.get('resolution_m') or 999999))
        return entries

    def db_path(self,e):
        sid=e['dataset_id']
        if len(sid)!=64 or any(c not in '0123456789abcdef' for c in sid):raise NdmElevationError('Invalid dataset SHA')
        return self.root/sid/'terrain.sqlite'

    def _prepare(self,e):
        sid=e['dataset_id'];dest=self.db_path(e)
        try:
            dest.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
            path=Path(e['_source']).resolve()
            st=path.stat()
            if not path.is_file() or int(e.get('source_size') or -1)!=st.st_size or int(e.get('source_mtime_ns') or -1)!=st.st_mtime_ns:
                raise NdmElevationError('NDM registered source has changed')
            with zipfile.ZipFile(path) as z:
                info=z.getinfo('terrain.sqlite')
                if info.file_size<=0 or info.file_size>16*1024**3:
                    raise NdmElevationError('Terrain database size not supported')
                if shutil.disk_usage(dest.parent).free<info.file_size+512*1024*1024:
                    raise NdmElevationError('Insufficient free storage for NDM terrain cache')
                temp=dest.with_suffix('.sqlite.part')
                try:
                    with z.open(info) as f,open(temp,'wb') as dst:
                        for block in iter(lambda:f.read(1024*1024),b''):dst.write(block)
                    with sqlite3.connect(temp.as_uri()+'?mode=ro',uri=True,timeout=5) as con:
                        tables={x[0] for x in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                        if not {'tiles','metadata'}<=tables:raise NdmElevationError('Invalid NDM terrain.sqlite tables')
                        schema=con.execute("SELECT value FROM metadata WHERE name='schema'").fetchone()
                        if not schema or schema[0]!='takrig.terrain.sqlite.v1':raise NdmElevationError('Incompatible NDM terrain schema')
                    os.replace(temp,dest)
                finally:
                    if temp.exists():temp.unlink()
        except Exception as err:
            with self.lock:self.errors[sid]=str(err)[:200]
        finally:
            with self.lock:self.processing.discard(sid)

    def prepare(self,e):
        path=self.db_path(e)
        if path.is_file():return 'ready'
        sid=e['dataset_id']
        with self.lock:
            if sid in self.errors:return 'error'
            if sid in self.processing:return 'preparing'
            if len(self.processing)>=2:return 'preparing'
            self.processing.add(sid)
        threading.Thread(target=self._prepare,args=(dict(e),),daemon=True,name='ndm-elev-'+sid[:8]).start()
        return 'preparing'

    def covering(self,bounds):
        w,s,e,n=bounds
        if not all(math.isfinite(v) for v in bounds) or not(-180<=w<=180 and -180<=e<=180 and -90<=s<=90 and -90<=n<=90 and w<=e and s<=n):raise NdmElevationError('Invalid geographic analysis bounds')
        entries=[]
        for a in self.entries():
            b=a.get('bounds')
            if isinstance(b,list) and len(b)==4 and e>=b[0] and w<=b[2] and n>=b[1] and s<=b[3]:entries.append(a)
        return entries

    def coverage(self,bounds):
        entries=self.covering(bounds)
        return {'available':bool(entries),'status':('ready' if entries and all(self.prepare(a)=='ready' for a in entries) else 'preparing' if entries else 'missing'),
          'datasets':[{'id':e['dataset_id'],'region':e.get('region'),'resolution_m':e.get('resolution_m'),'bounds':e.get('bounds')} for e in entries],
          'vertical_datum':'unknown','note':'Actual coverage is verified per sampled point; never blend datasets of unknown datums with external sources.'}

    def _tile_index(self,e):
        sid=e['dataset_id']
        with self.lock:
            if sid in self.indexes:return self.indexes[sid]
        uri=self.db_path(e).as_uri()+'?mode=ro&immutable=1'
        with sqlite3.connect(uri,uri=True,timeout=5) as conn:
            cols={x[1] for x in conn.execute('PRAGMA table_info(tiles)')}
            if not {'tile_id','west','south','east','north','rows','cols','encoding','data'} <= cols:
                raise NdmElevationError('Missing NDM tiles columns')
            rows=list(conn.execute('SELECT tile_id,west,south,east,north,rows,cols FROM tiles'))
        if len(rows)>50000:raise NdmElevationError('Unbounded NDM tile catalog')
        with self.lock:self.indexes[sid]=rows
        return rows

    def _grid(self,e,row,conn):
        sid=e['dataset_id'];tileid=row[0];cachekey=(sid,tileid)
        with self.lock:
            if cachekey in self.grids:
                arr=self.grids.pop(cachekey);self.grids[cachekey]=arr;return arr
        cols=int(row[6]);rws=int(row[5]);payload=conn.execute('SELECT encoding,data FROM tiles WHERE tile_id=?',(tileid,)).fetchone()
        if not payload or payload[0]!='int16le+zlib' or rws<2 or cols<2 or rws*cols>5_000_000:raise NdmElevationError('Invalid NDM grid encoding/dimensions')
        dec=zlib.decompressobj();blob=dec.decompress(payload[1],rws*cols*2+1)
        if not dec.eof or dec.unconsumed_tail or dec.unused_data or len(blob)!=rws*cols*2:raise NdmElevationError('Corrupt NDM grid payload')
        vals=array.array('h');vals.frombytes(blob)
        if sys.byteorder!='little':vals.byteswap()
        with self.lock:
            self.grids[cachekey]=vals
            while len(self.grids)>10:self.grids.popitem(last=False)
        return vals

    @staticmethod
    def bilinear(row,values,lat,lon):
        _,west,south,east,north,rows,cols=row
        # Native NDM DEM grids use west-to-east columns and north-to-south rows.
        if east<=west or north<=south:return None
        x=(lon-west)/(east-west)*(cols-1)
        y=(north-lat)/(north-south)*(rows-1)
        if not (0<=x<=cols-1 and 0<=y<=rows-1):return None
        c0,r0=int(x),int(y);c1,r1=min(cols-1,c0+1),min(rows-1,r0+1)
        pts=[values[r0*cols+c0],values[r0*cols+c1],values[r1*cols+c0],values[r1*cols+c1]]
        if any(v<=-32767 for v in pts):return None
        dx=x-c0;dy=y-r0
        value=(pts[0]*(1-dx)+pts[1]*dx)*(1-dy)+(pts[2]*(1-dx)+pts[3]*dx)*dy
        return round(value,2) if math.isfinite(value) else None

    def sample(self,points):
        if not isinstance(points,list) or not 1<=len(points)<=4096:raise NdmElevationError('Batch must contain 1–4096 points')
        normalized=[]
        for c in points:
            if not isinstance(c,list) or len(c)!=2:raise NdmElevationError('Expected [latitude, longitude] point')
            lat,lon=map(float,c)
            if not math.isfinite(lat) or not math.isfinite(lon) or abs(lat)>90 or abs(lon)>180:raise NdmElevationError('Invalid elevation point')
            normalized.append((lat,lon))
        bounds=(min(v[1] for v in normalized),min(v[0] for v in normalized),max(v[1] for v in normalized),max(v[0] for v in normalized))
        entries=self.covering(bounds)
        if not entries:raise NdmElevationError('No registered NDM terrain covers these points')
        for e in entries:
            if self.prepare(e)!='ready':raise NdmElevationError('NDM terrain cache preparing; retry later')
        if not self.inflight.acquire(blocking=False):raise NdmElevationError('NDM elevation server is busy; retry later')
        try:
            results=[None]*len(normalized);matched=set();connections={}
            try:
                for e in entries:
                    sid=e['dataset_id'];index=self._tile_index(e)
                    connection=sqlite3.connect(self.db_path(e).as_uri()+'?mode=ro&immutable=1',uri=True,timeout=4)
                    connections[sid]=connection
                    for i,(lat,lon) in enumerate(normalized):
                        if results[i] is not None:continue
                        for row in index:
                            _,w,s,x,n,_,_=row
                            if w<=lon<=x and s<=lat<=n:
                                h=self.bilinear(row,self._grid(e,row,connection),lat,lon)
                                if h is not None:results[i]=h;matched.add(sid);break
            finally:
                for connection in connections.values():connection.close()
            count=sum(v is not None for v in results)
            return {'elevations':results,'valid':count,'complete':count==len(results),
                'source':'NDM Elevation · '+', '.join(sorted(str(x.get('region') or x['dataset_id'][:8]) for x in entries if x['dataset_id'] in matched)),
                'vertical_datum':'unknown','resolution_m':min(float(e.get('resolution_m') or 99999) for e in entries),
                'dataset_ids':list(matched)}
        finally:self.inflight.release()
