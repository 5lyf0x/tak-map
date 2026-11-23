"""TAK Map i003: thread-safe read-only MBTiles registry and bounded connection pool.

Only the tile GET path uses this registry. Catalog edits still use the original
atomic application store. No tile bytes or MBTiles schema are modified here.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote
from collections import Counter
from threading import Condition, RLock
import json
import os
import sqlite3
import time


@dataclass(frozen=True)
class TileRecord:
    map_id: str
    path: str
    scheme: str
    fmt: str
    status: str
    min_zoom: int
    max_zoom: int
    bounds: str


@dataclass(frozen=True)
class TileResult:
    data: bytes | None
    ctype: str = 'application/octet-stream'
    status: str = 'missing'
    completed: bool = False


class _Pool:
    def __init__(self, key):
        self.key = key
        self.idle = []  # (connection, last_used_monotonic)
        self.busy = 0
        self.stale = False


class OfflineTileStore:
    """Bounded pooling across ThreadingHTTPServer request threads.

    A connection is checked out by at most one worker; check_same_thread=False
    is only used with exclusive checkout, not concurrent SQLite cursor access.
    """
    def __init__(self, max_per_map=3, max_global=12, idle_seconds=35, wait_seconds=2):
        self.max_per_map = max(1, min(8, int(max_per_map)))
        self.max_global = max(self.max_per_map, min(32, int(max_global)))
        self.idle_seconds = max(5, int(idle_seconds))
        self.wait_seconds = max(.1, float(wait_seconds))
        self.lock = RLock()
        self.cond = Condition(self.lock)
        self.catalog_stamp = None
        self.registry = {}
        self.pools = {}
        self.open_count = 0
        self.counters = Counter()
        self.request_latencies_ms = []

    def _stat_catalog(self, catalog_path):
        try:
            s = Path(catalog_path).stat()
            return (str(catalog_path), s.st_dev, s.st_ino, s.st_mtime_ns, s.st_size)
        except FileNotFoundError:
            return (str(catalog_path), None)

    def _discard_pool_locked(self, pool):
        pool.stale = True
        for conn, _ in pool.idle:
            try: conn.close()
            except sqlite3.Error: pass
            self.open_count -= 1
        pool.idle.clear()
        if pool.busy == 0:
            self.pools.pop(pool.key, None)
        self.cond.notify_all()

    def invalidate(self):
        """Called after an atomic catalog save, rename, import or deletion."""
        with self.cond:
            self.catalog_stamp = None
            for pool in list(self.pools.values()):
                self._discard_pool_locked(pool)

    def _refresh_locked(self, catalog_path):
        stamp = self._stat_catalog(catalog_path)
        if stamp == self.catalog_stamp:
            self.counters['catalog_hits'] += 1
            return
        # Fail closed if external editing produces malformed JSON. Do not write
        # or 'clean' the persistent catalog in the hot tile request path.
        try:
            src = json.loads(Path(catalog_path).read_text(encoding='utf-8'))
            maps = src.get('maps', []) if isinstance(src, dict) else []
            if not isinstance(maps, list): raise ValueError('Invalid map list')
        except FileNotFoundError:
            maps = []
        except (ValueError, OSError) as exc:
            self.counters['catalog_read_errors'] += 1
            raise RuntimeError('Offline map catalog could not be read') from exc
        recs = {}
        for m in maps:
            if not isinstance(m, dict): continue
            mid = str(m.get('id') or '').strip()
            fp = str(m.get('path') or '').strip()
            if not mid or not fp: continue
            scheme = str(m.get('tile_row_scheme') or 'tms').strip().lower()
            if scheme not in ('tms','xyz'): scheme='tms'
            try: mn = max(0, min(22, int(m.get('min_zoom') or 0)))
            except (ValueError, TypeError): mn = 0
            try: mx = max(mn, min(22, int(m.get('max_zoom') if m.get('max_zoom') is not None else 22)))
            except (ValueError, TypeError): mx = 22
            status = str(m.get('download_status') or '').lower().strip()
            if not status: status = 'complete' if str(m.get('created_by') or '').lower() != 'download' else 'partial'
            if m.get('partial') or m.get('resume_available'):status='partial'
            recs[mid] = TileRecord(mid, fp, scheme, str(m.get('format') or '').lower(), status, mn, mx, str(m.get('bounds') or ''))
        self.registry = recs
        self.catalog_stamp = stamp
        self.counters['catalog_parses'] += 1
        # A different catalog identity or record mapping invalidates handles;
        # read-only connections to unchanged files can remain warm.
        for pool in list(self.pools.values()):
            r = recs.get(pool.key[0])
            if not r or (r.path, r.scheme) != (pool.key[1], pool.key[2]):
                self._discard_pool_locked(pool)

    def _evict_idle_locked(self, expired_only=False):
        now=time.monotonic()
        for pool in list(self.pools.values()):
            remaining=[]
            for conn, last in pool.idle:
                if pool.stale or (now-last >= self.idle_seconds):
                    try: conn.close()
                    except sqlite3.Error: pass
                    self.open_count -= 1
                else: remaining.append((conn,last))
            pool.idle=remaining
            if pool.stale and not pool.busy: self.pools.pop(pool.key,None)
        if not expired_only and self.open_count >= self.max_global:
            candidates=[(last,pool,conn) for pool in self.pools.values() for conn,last in pool.idle]
            if candidates:
                _,pool,conn=min(candidates,key=lambda item:item[0])
                pool.idle=[x for x in pool.idle if x[0] is not conn]
                try: conn.close()
                except sqlite3.Error: pass
                self.open_count -= 1

    def _checkout(self, key):
        deadline=time.monotonic()+self.wait_seconds
        while True:
            with self.cond:
                self._evict_idle_locked(expired_only=True)
                pool=self.pools.get(key)
                if not pool:
                    pool=_Pool(key);self.pools[key]=pool
                if pool.idle:
                    conn,_=pool.idle.pop()
                    pool.busy+=1
                    self.counters['pool_reuses']+=1
                    return pool,conn
                if pool.busy < self.max_per_map:
                    if self.open_count>=self.max_global:self._evict_idle_locked(expired_only=False)
                    if self.open_count<self.max_global:
                        pool.busy+=1
                        self.open_count+=1  # reserve the connection slot
                        break
                remaining=deadline-time.monotonic()
                if remaining<=0:
                    self.counters['pool_timeouts']+=1
                    raise TimeoutError('Offline tile database is busy')
                self.cond.wait(min(.08,remaining))
        uri='file:'+quote(key[1],safe='/')+'?mode=ro'
        try:
            conn=sqlite3.connect(uri,uri=True,timeout=.45,check_same_thread=False)
            conn.execute('PRAGMA query_only=ON')
        except Exception:
            with self.cond:
                pool.busy-=1;self.open_count-=1
                if pool.stale and pool.busy==0:self.pools.pop(pool.key,None)
                self.cond.notify_all()
            raise
        with self.cond:self.counters['sqlite_opens']+=1
        return pool,conn

    def _return(self,pool,conn,healthy=True):
        with self.cond:
            pool.busy-=1
            if pool.stale or not healthy:
                try:conn.close()
                except sqlite3.Error:pass
                self.open_count-=1
            else:
                pool.idle.append((conn,time.monotonic()))
            if pool.stale and pool.busy==0:self.pools.pop(pool.key,None)
            self.cond.notify_all()

    def lookup(self,catalog_path,map_id):
        with self.cond:
            self._refresh_locked(catalog_path)
            return self.registry.get(str(map_id or '').strip())

    def fetch(self,catalog_path,map_id,z,x,y):
        start=time.perf_counter()
        try:
            result=self._fetch_impl(catalog_path,map_id,z,x,y)
        except (TimeoutError, sqlite3.Error, OSError, RuntimeError):
            result=TileResult(None,status='error')
        dt=(time.perf_counter()-start)*1000
        with self.cond:
            self.counters['requests']+=1
            self.counters['status_'+result.status]+=1
            self.request_latencies_ms.append(round(dt,3))
            if len(self.request_latencies_ms)>256: self.request_latencies_ms=self.request_latencies_ms[-256:]
        return result

    def _fetch_impl(self,catalog_path,map_id,z,x,y):
        try:z,x,y=int(z),int(x),int(y)
        except (TypeError,ValueError):return TileResult(None,status='invalid')
        if z<0 or z>22 or x<0 or y<0 or x>=1<<z or y>=1<<z:
            return TileResult(None,status='invalid')
        r=self.lookup(catalog_path,map_id)
        if r is None:return TileResult(None,status='unknown')
        complete=r.status=='complete'
        if z<r.min_zoom or z>r.max_zoom:return TileResult(None,status='zoom',completed=complete)
        fp=Path(r.path)
        try: st=fp.stat()
        except (OSError,ValueError):return TileResult(None,status='missing-file',completed=complete)
        if not fp.is_file():return TileResult(None,status='missing-file',completed=complete)
        # Include inode/mtime/size. Changes to in-progress files invalidate the
        # old handle, so SQLite can see newly committed resume/retry tiles.
        key=(r.map_id,str(fp.resolve()),r.scheme,st.st_dev,st.st_ino,st.st_mtime_ns,st.st_size)
        with self.cond:
            for pool in list(self.pools.values()):
                if pool.key[0]==r.map_id and pool.key!=key:
                    self._discard_pool_locked(pool)
        row=y if r.scheme=='xyz' else ((1<<z)-1-y)
        pool,conn=self._checkout(key)
        healthy=True
        try:
            cursor=conn.execute('SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=? LIMIT 1',(z,x,row))
            fetched=cursor.fetchone()
            if not fetched:return TileResult(None,status='missing',completed=complete)
            raw=fetched[0]
            data=raw.tobytes() if isinstance(raw,memoryview) else bytes(raw)
        except sqlite3.Error:
            healthy=False
            raise
        finally:
            self._return(pool,conn,healthy)
        if data[:8]==b'\x89PNG\r\n\x1a\n':ctype='image/png'
        elif data[:3]==b'\xff\xd8\xff':ctype='image/jpeg'
        elif data[:4]==b'RIFF' and b'WEBP' in data[:16]:ctype='image/webp'
        else:ctype='image/jpeg' if r.fmt in ('jpeg','jpg') else 'image/png' if r.fmt=='png' else 'application/octet-stream'
        return TileResult(data,ctype,'ok',complete)

    def diagnostic_summary(self):
        with self.cond:
            times=sorted(self.request_latencies_ms)
            def rank(p):return times[min(len(times)-1,int((len(times)-1)*p))] if times else None
            return dict(self.counters,connections_open=self.open_count,active_pools=len(self.pools),p50_ms=rank(.5),p95_ms=rank(.95))
