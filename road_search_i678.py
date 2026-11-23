"""Explicit, resource-bounded, local OSM road/trail name index for TAK Map i678.

No automatic job, no changes to NDM PBFs, and no broadened permissions.
Requires a readable local regional PBF and osmium-tool installed by the operator.
"""
import json
import math
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import threading
import time

REGIONS = frozenset(('us-west', 'us-midwest', 'us-northeast', 'us-south', 'us-pacific', 'united-states'))


def _particulars(feature):
    tags = feature.get('properties') or {}
    if not isinstance(tags, dict):
        return None
    highway = str(tags.get('highway') or '').lower().strip()
    if not highway:
        return None
    name = str(tags.get('name') or '').strip()[:240]
    ref = str(tags.get('ref') or '').strip()[:160]
    if not name and not ref:
        return None
    kind = 'Trail' if highway in ('path', 'footway', 'bridleway', 'track', 'cycleway', 'steps', 'pedestrian') else 'Road'
    routable = highway not in ('path', 'footway', 'bridleway', 'steps', 'pedestrian', 'proposed', 'construction')
    geom = feature.get('geometry') or {}
    if geom.get('type') not in ('LineString', 'MultiLineString'):
        return None
    coords = geom.get('coordinates') or []
    if geom['type'] == 'LineString':
        coords = [coords]
    points = []
    for line in coords:
        if not isinstance(line, list):
            continue
        for item in line:
            if len(points) >= 100:
                break
            if isinstance(item, list) and len(item) >= 2:
                try:
                    x, y = float(item[0]), float(item[1])
                    if -180 <= x <= 180 and -90 <= y <= 90 and math.isfinite(x) and math.isfinite(y):
                        points.append([x, y])
                except (ValueError, TypeError):
                    continue
    if not points:
        return None
    midpoint = points[len(points)//2]
    return name or ref, ref, kind, int(routable), midpoint[1], midpoint[0], json.dumps(points, separators=(',', ':'))


class RoadSearchIndex:
    def __init__(self, data_root='/var/lib/tak-map', source_root='/var/lib/takrig-routing/regions'):
        self.root = Path(data_root) / 'road-search'
        self.source_root = Path(source_root)
        self.lock = threading.RLock()
        self.job = {'status': 'idle', 'detail': 'No road index build requested'}
        self.thread = None

    def _db(self, region):
        return self.root / (region + '.sqlite')

    def status(self):
        with self.lock:
            return dict(self.job)

    def start(self, region):
        if region not in REGIONS:
            raise ValueError('Unknown permitted regional source')
        if self.thread and self.thread.is_alive():
            raise ValueError('A road-name indexing job is already running')
        path = self.source_root / region / 'source.osm.pbf'
        if not path.is_file() or not os.access(path, os.R_OK):
            raise ValueError('Regional PBF is not readable by TAK Map; configure authorized access without changing NDM ownership')
        binary = shutil.which('osmium')
        if not binary:
            raise ValueError('osmium CLI is required to index roads and trails; no package installation was attempted')
        self.root.mkdir(parents=True, exist_ok=True)
        if shutil.disk_usage(self.root).free < 8 * (1024**3):
            raise ValueError('At least 8 GiB of free working space is required before indexing')
        with self.lock:
            self.job={'status':'indexing','region':region,'started':time.time(),'features':0,'detail':'Streaming names from the regional OSM PBF'}
        self.thread=threading.Thread(target=self._run,args=(region,str(path),binary),daemon=True)
        self.thread.start()
        return dict(self.job)

    def _run(self, region, path, binary):
        dst=self._db(region)
        tmp=dst.with_suffix('.building.sqlite')
        count=0
        proc=None
        try:
            tmp.unlink(missing_ok=True)
            conn=sqlite3.connect(tmp)
            conn.execute('PRAGMA journal_mode=OFF')
            conn.execute('PRAGMA synchronous=OFF')
            conn.execute('CREATE TABLE roads (id INTEGER PRIMARY KEY, name TEXT, ref TEXT, kind TEXT, routable INTEGER, lat REAL, lon REAL, geometry TEXT)')
            conn.execute("CREATE VIRTUAL TABLE roads_fts USING fts5(name,ref, content='roads',content_rowid='id',tokenize='unicode61')")
            # osmium builds a location index to reconstruct way geometry.
            # nice lowers CPU priority; output is streamed, never held in RAM.
            proc=subprocess.Popen([binary,'export',path,'-f','geojsonseq','-o','-'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,bufsize=1024*1024,
                                  preexec_fn=lambda: os.nice(10))
            batch=[]
            for raw in proc.stdout:
                try:
                    f=json.loads(raw)
                    row=_particulars(f)
                    if row:
                        batch.append(row)
                except (ValueError, UnicodeDecodeError, TypeError):
                    continue
                if len(batch)>=1200:
                    conn.executemany('INSERT INTO roads(name,ref,kind,routable,lat,lon,geometry) VALUES (?,?,?,?,?,?,?)',batch)
                    conn.commit()
                    count+=len(batch)
                    batch.clear()
                    with self.lock:
                        self.job['features']=count
                    if tmp.stat().st_size > 6*(1024**3):
                        raise RuntimeError('Index exceeded the 6 GiB safety limit')
            if batch:
                conn.executemany('INSERT INTO roads(name,ref,kind,routable,lat,lon,geometry) VALUES (?,?,?,?,?,?,?)',batch)
                conn.commit()
                count+=len(batch)
            err=proc.stderr.read(16384).decode('utf8','replace')
            code=proc.wait(timeout=120)
            if code:
                raise RuntimeError('osmium export failed: '+err[-400:])
            conn.execute("INSERT INTO roads_fts(roads_fts) VALUES ('rebuild')")
            conn.commit()
            conn.close()
            tmp.replace(dst)
            with self.lock:
                self.job.update(status='ready',features=count,detail='Named roads and trails indexed')
        except Exception as exc:
            try:
                if proc and proc.poll() is None:
                    proc.kill()
                    proc.communicate(timeout=5)
            except Exception:
                pass
            try:
                conn.close()
            except Exception:
                pass
            tmp.unlink(missing_ok=True)
            with self.lock:
                self.job.update(status='failed',detail=str(exc)[:500])

    def query(self, text, region='us-west', near=None):
        if region not in REGIONS:
            raise ValueError('Unknown regional source')
        q = re.findall(r'[\w-]+', str(text or '').lower(), flags=re.UNICODE)[:6]
        if len(' '.join(q)) < 2:
            return []
        db=self._db(region)
        if not db.is_file():
            return []
        match=' '.join('"'+word.replace('"','')+'"*' for word in q)
        con=sqlite3.connect('file:'+str(db)+'?mode=ro',uri=True)
        try:
            rows=con.execute('SELECT r.id,r.name,r.ref,r.kind,r.routable,r.lat,r.lon,r.geometry FROM roads_fts f JOIN roads r ON r.id=f.rowid WHERE roads_fts MATCH ? LIMIT 50',(match,)).fetchall()
        finally:
            con.close()
        def rank(r):
            if near is None:return 0
            return (r[5]-near[0])**2+(r[6]-near[1])**2
        return [{'id':r[0], 'name':r[1], 'ref':r[2], 'kind':r[3], 'routable':bool(r[4]), 'lat':r[5], 'lon':r[6], 'geometry':json.loads(r[7]), 'region':region} for r in sorted(rows,key=rank)[:20]]
