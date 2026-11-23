"""TAK Map i698 resumable polygon-clipped offline downloads.

Each parent creates ONE MBTiles, internally split into consecutive, bounded
250k-tile accounting jobs. Failed coordinates are persisted in that MBTiles
and can be retried without re-downloading successful tiles.
"""
from __future__ import annotations
import concurrent.futures
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import secrets
import sqlite3
import threading
import time
from urllib.request import Request,urlopen
from urllib.parse import quote,urlsplit
import tak_map_offline_regions_i698 as geo

class OfflineMapsI698:
    def __init__(self, h):
        self.h=h

    def _get(self,name):return self.h[name]

    def sources(self):
        rows=[]
        seen=set()
        for b in self._get('TAK_MAP_BASEMAPS'):
            url=str(b.get('url') or '')
            if not url.startswith(('http://','https://')) or not all(x in url for x in ('{z}','{x}','{y}')):continue
            if b.get('id') in seen:continue
            seen.add(b['id'])
            rows.append(dict(b))
        load=self.h.get('_i505_load_custom_basemaps')
        if callable(load):
            for row in load():
                sid=str(row.get('id') or '')
                upstream=str(row.get('upstream_url') or '')
                if not sid or sid in seen or not upstream.startswith(('http://','https://')) or not all(x in upstream for x in ('{z}','{x}','{y}')):continue
                # Public UI sees the normal authenticated proxy URL, never a
                # stored upstream URL or provider credentials.
                ext=str(row.get('tileType') or 'png').lower()
                proxy='/api/tak-map/custom-basemap-tile/'+quote(sid,safe='')+'/{z}/{x}/{y}.'+ext
                rows.append({'id':sid,'label':row.get('label') or sid,'group':row.get('group') or 'Custom XML',
                    'minZoom':row.get('minZoom',0),'maxZoom':row.get('maxZoom',19),
                    'url':proxy,'_upstream_url':upstream,'attribution':row.get('attribution') or '',
                    'tileType':ext,'tms':bool(row.get('tms') or row.get('invertY'))})
                seen.add(sid)
        return rows

    def public_sources(self):
        return [{k:v for k,v in row.items() if not k.startswith('_')} for row in self.sources()]

    def source(self,source_id):
        return next((r for r in self.sources() if str(r.get('id'))==str(source_id or '')) ,None)

    def _geometry(self,payload):
        rid=str((payload or {}).get('area_id') or '').strip()
        if rid:
            f=geo.feature(rid)
            if not f:raise ValueError('Unknown geographic download region')
            return rid,geo.bounds_for_feature(f)
        b=self._get('_normalize_bounds')((payload or {}).get('bounds') or {})
        return '',b

    def _zoom(self,payload,source):
        lo=max(0,min(19,int(payload.get('min_zoom',8))))
        hi=max(0,min(19,int(payload.get('max_zoom',13))))
        if hi<lo:lo,hi=hi,lo
        supported_min=int(source.get('minZoom') or 0)
        supported_max=int(source.get('maxZoom') or 19)
        if lo<supported_min or hi>supported_max:
            raise ValueError('Selected zoom range is outside this basemap source’s supported zoom levels')
        return lo,hi

    def estimate(self,payload):
        try:
            if not isinstance(payload,dict):raise ValueError('Expected JSON object')
            src=self.source(payload.get('source_id'))
            if not src:raise ValueError('Basemap source is not configured or cannot supply XYZ tiles')
            rid,b=self._geometry(payload)
            lo,hi=self._zoom(payload,src)
            total=geo.tile_total(rid,b,lo,hi)
            limit=max(1,int(self._get('TAK_MAP_OFFLINE_DOWNLOAD_MAX_TILES')))
            avg=32000 if 'imagery' in str(src.get('group','')+' '+str(src.get('label',''))).lower() else 18000
            return {'ok':True,'source':{k:v for k,v in src.items() if not k.startswith('_')},
                    'source_id':src['id'],'bounds':b,'area_id':rid,
                    'min_zoom':lo,'max_zoom':hi,'tile_count':total,
                    'estimated_bytes':total*avg,'max_tiles':limit,'batch_tiles':limit,
                    'internal_jobs':math.ceil(total/limit), 'allowed':True,
                    'geometry':'polygon' if rid else 'rectangle',
                    'message': 'One offline map; internal jobs are automatically split at '+str(limit)+' tiles.'}
        except Exception as exc:
            return {'ok':False,'error':str(exc)}

    def _job(self,estimate,name,map_id='',resume_path='',retry_only=False):
        sid=estimate.get('source_id')
        source=self.source(sid)
        if not source:raise ValueError('Basemap source is no longer configured')
        jid=secrets.token_hex(8)
        total=int(estimate['tile_count'])
        job={'id':jid,'ok':True,'status':'queued','name':name,'source':source,
             'source_id':sid,'bounds':estimate['bounds'],'area_id':estimate.get('area_id') or '',
             'min_zoom':estimate['min_zoom'],'max_zoom':estimate['max_zoom'],
             'tile_count':total,'done':0,'saved':0,'failed':0,
             'message':'Queued offline map download','map_id':map_id,'request':'',
             'created':datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'resume_path':resume_path,'retry_only':retry_only,'internal_jobs':estimate.get('internal_jobs',1),
             'internal_job':1}
        lock=self._get('TAK_MAP_OFFLINE_DOWNLOAD_LOCK')
        jobs=self._get('TAK_MAP_OFFLINE_DOWNLOAD_JOBS')
        with lock:jobs[jid]=job
        threading.Thread(target=self.worker,args=(jid,),daemon=True,name='offline-map-i698-'+jid).start()
        return {'ok':True,'job':{k:v for k,v in job.items() if k!='source'}}

    def start(self,payload):
        est=self.estimate(payload)
        if not est.get('ok'):return est
        if not est['tile_count']:return {'ok':False,'error':'Selected area has no tiles at these zoom levels'}
        name=str(payload.get('name') or '').strip()[:120] or str(est['source'].get('label') or 'Offline map')+' offline'
        try:return self._job(est,name)
        except Exception as exc:return {'ok':False,'error':str(exc)}

    def _lookup(self,map_id):
        rec=self._get('_offline_map_record')(map_id)
        if not rec:raise ValueError('Offline map pack not found')
        p=Path(str(rec.get('path') or ''))
        if not p.is_file():raise ValueError('Saved MBTiles file not found')
        return rec,p

    def _assert_not_active(self,map_id):
        lock=self._get('TAK_MAP_OFFLINE_DOWNLOAD_LOCK')
        jobs=self._get('TAK_MAP_OFFLINE_DOWNLOAD_JOBS')
        with lock:
            for job in jobs.values():
                if str(job.get('map_id') or '')==str(map_id or '') and job.get('status') in ('queued','running'):
                    raise ValueError('This offline map already has an active download or retry')

    def _from_record(self,rec):
        bounds=self._get('_parse_offline_bounds')(rec['bounds'])
        rid=str(rec.get('area_id') or '')
        return {'source_id':rec['source_id'],'area_id':rid,'bounds':bounds,
            'min_zoom':int(rec.get('min_zoom',8)),'max_zoom':int(rec.get('max_zoom',13))}

    def resume(self,map_id):
        try:
            rec,path=self._lookup(map_id)
            self._assert_not_active(rec['id'])
            if not (rec.get('partial') or rec.get('resume_available')):
                raise ValueError('This map is not paused or partially downloaded; use Retry/Finish for missing tiles')
            est=self.estimate(self._from_record(rec))
            if not est.get('ok'):return est
            return self._job(est,rec.get('name') or 'Offline map',rec['id'],str(path))
        except Exception as exc:return {'ok':False,'error':str(exc)}

    def retry(self,map_id):
        try:
            rec,path=self._lookup(map_id)
            self._assert_not_active(rec['id'])
            conn=sqlite3.connect(str(path));n=0
            try:
                if self._failures_table(conn):
                    n=int(conn.execute('select count(*) from offline_failed_tiles_i698').fetchone()[0])
            finally:conn.close()
            if not n:return {'ok':False,'error':'This offline map has no failed tiles requiring retry'}
            est=self.estimate(self._from_record(rec))
            if not est.get('ok'):return est
            est['tile_count']=n;est['internal_jobs']=math.ceil(n/max(1,int(self._get('TAK_MAP_OFFLINE_DOWNLOAD_MAX_TILES'))))
            return self._job(est,rec.get('name') or 'Offline map',rec['id'],str(path),retry_only=True)
        except Exception as exc:return {'ok':False,'error':str(exc)}

    def finish(self,map_id):
        try:
            rec,path=self._lookup(map_id)
            self._assert_not_active(rec['id'])
            if not rec.get('failed_tile_count'):
                return {'ok':True,'message':'This map has no missing tiles','maps':self._get('_load_offline_maps')()}
            rec['download_status']='accepted_incomplete'
            rec['partial']=False;rec['resume_available']=False
            rec['retry_available']=True
            rec['updated']=datetime.datetime.now(datetime.timezone.utc).isoformat()
            self._get('_upsert_offline_map_record')(rec)
            return {'ok':True,'message':'Incomplete map retained; failed-tile manifest preserved','maps':self._get('_load_offline_maps')()}
        except Exception as exc:return {'ok':False,'error':str(exc)}

    @staticmethod
    def _failures_table(conn):
        return bool(conn.execute("select 1 from sqlite_master where type='table' and name='offline_failed_tiles_i698'").fetchone())

    def _url(self,source,z,x,y):
        template=source.get('_upstream_url') or source.get('url') or ''
        if not template.startswith(('https://','http://')):
            raise ValueError('Source must use an HTTP(S) upstream tile URL')
        n=2**int(z)
        yy=(n-1-int(y)) if source.get('tms') else int(y)
        result=str(template)
        for token,value in (('{$z}',z),('{$x}',x),('{$y}',yy),('{z}',z),('{x}',x),('{y}',yy),('{-y}',n-1-int(y)),('{$s}','a'),('{s}','a')):
            result=result.replace(token,str(value))
        return result

    def worker(self,jid):
        h=self.h
        jobs=self._get('TAK_MAP_OFFLINE_DOWNLOAD_JOBS')
        lock=self._get('TAK_MAP_OFFLINE_DOWNLOAD_LOCK')
        update=self._get('_update_offline_job')
        job=jobs[jid]
        source=job['source']
        mid=str(job.get('map_id') or self._get('_safe_offline_id')(job['name']+'-'+jid[:6]))
        resume=bool(job.get('resume_path'))
        dir_=self._get('TAK_MAP_OFFLINE_DIR')
        tmp=Path(job['resume_path']) if resume else dir_/(mid+'.partial.mbtiles')
        final=tmp if resume else dir_/(mid+'.mbtiles')
        conn=None
        done=0;failed=0;saved=0
        first_format='png'
        total=int(job['tile_count'])
        previous_record=(h['_offline_map_record'](mid) if resume else None) or {}
        original_total=int(previous_record.get('requested_tile_count') or total)
        original_batches=int(previous_record.get('internal_jobs') or job.get('internal_jobs') or 1)
        batch_size=max(1,int(self._get('TAK_MAP_OFFLINE_DOWNLOAD_MAX_TILES')))
        concurrency=max(1,min(12,int(self._get('TAK_MAP_OFFLINE_DOWNLOAD_CONCURRENCY') or 4)))
        def action():
            with lock:return (jobs.get(jid) or {}).get('request','')
        def count_failures():
            return int(conn.execute('select count(*) from offline_failed_tiles_i698').fetchone()[0])
        def persist_progress():
            # Periodic record makes a .partial.mbtiles discoverable after an
            # unexpected process restart; SQLite WAL recovers committed tiles.
            conn.commit()
            rec=h['_offline_record_from_job'](job,mid,tmp,'paused',done,saved,count_failures(),first_format)
            rec.update({'area_id':job.get('area_id') or '', 'download_status':'running',
                        'partial':True,'resume_available':True,'requested_tile_count':original_total,
                        'internal_jobs':original_batches, 'active_job_id':jid})
            h['_upsert_offline_map_record'](rec)

        def finalize(status,message):
            nonlocal conn
            if conn:
                if not job.get('retry_only'):
                    conn.execute("update offline_batches_i698 set status='checked' where status!='checked'")
                conn.commit();conn.close();conn=None
            if not resume and tmp.exists():
                # Never delete a pre-existing finalized map on ID collision.
                if final.exists():raise ValueError('Generated offline map ID collided with an existing file')
                tmp.rename(final)
            actual=h['_mbtiles_tile_count'](final)
            rec=h['_offline_record_from_job'](job,mid,final,status,done,actual,failed,first_format)
            rec.update({'area_id':job.get('area_id') or '', 'internal_jobs':original_batches,
                        'requested_tile_count':original_total, 'download_status':status,'partial':status in ('paused','canceled','error'),
                        'resume_available':status in ('paused','canceled','error'),
                        'retry_available':failed>0,'failed_tile_count':failed,
                        'remaining_tile_count':max(0,int(job.get('tile_count',0))-actual) if not job.get('retry_only') else failed})
            h['_upsert_offline_map_record'](rec)
            try:h['tak_map_offline_eud_package'](mid)
            except Exception:pass
            update(jid,status='done' if status in ('complete','incomplete') else status,
                   done=done,saved=actual,failed=failed,map_id=mid,message=message,
                   internal_job=max(1,math.ceil(max(1,done)/batch_size)),
                   internal_jobs=max(1,math.ceil(total/batch_size)),
                   maps=h['_load_offline_maps']())
        def fetch(task):
            z,x,y=task
            last_error=''
            for attempt in range(4):  # initial + 3 retries
                if attempt:
                    time.sleep((.4,1.0,2.0)[attempt-1])
                try:
                    url=self._url(source,z,x,y)
                    req=Request(url,headers={'User-Agent':'TAK-Map-offline-i698/1.4.0',
                        'Accept':'image/png,image/jpeg,image/webp,image/*;q=0.8'})
                    with urlopen(req,timeout=15) as response:
                        data=response.read(2*1024*1024+1)
                        ctype=str(response.headers.get('Content-Type') or '').lower()
                    if len(data)>2*1024*1024:raise ValueError('Tile exceeds 2 MiB limit')
                    if not data:raise ValueError('Empty tile response')
                    if ('json' in ctype or 'html' in ctype or data[:1] in (b'{',b'<')):
                        raise ValueError('Provider returned non-image content')
                    fmt=h['_detect_tile_format'](data,'unknown')
                    if fmt not in ('png','jpg','webp'):
                        raise ValueError('Unsupported tile encoding')
                    return task,data,fmt,''
                except Exception as e:
                    last_error=str(e)[:190]
            return task,None,None,last_error
        def tasks():
            if job.get('retry_only'):
                # Snapshot only the missing coordinates. This may be large, but
                # it never rescans or re-fetches successful tiles.
                for z,x,y in conn.execute('select z,x,y from offline_failed_tiles_i698 order by z,x,y').fetchall():
                    yield int(z),int(x),int(y)
                return
            rid=job.get('area_id') or ''
            for coord in geo.tiles(rid,job['bounds'],job['min_zoom'],job['max_zoom']):
                yield coord
        try:
            dir_.mkdir(parents=True,exist_ok=True)
            if not resume and tmp.exists():raise ValueError('Partial file name collision')
            conn=sqlite3.connect(str(tmp))
            conn.execute('pragma journal_mode=WAL')
            conn.execute('create table if not exists metadata(name text,value text)')
            conn.execute('create table if not exists tiles(zoom_level integer,tile_column integer,tile_row integer,tile_data blob)')
            conn.execute('create unique index if not exists tile_index on tiles(zoom_level,tile_column,tile_row)')
            conn.execute('create table if not exists offline_failed_tiles_i698(z integer not null,x integer not null,y integer not null, attempts integer not null default 0, last_error text not null default "", primary key(z,x,y))')
            conn.execute('create table if not exists offline_batches_i698(batch_index integer primary key, start_ordinal integer not null, end_ordinal integer not null, status text not null)')
            if not job.get('retry_only'):
                for bi in range(int(job.get('internal_jobs') or 1)):
                    conn.execute('insert or ignore into offline_batches_i698 values(?,?,?,?)',
                        (bi+1,bi*batch_size+1,min(total,(bi+1)*batch_size),'pending'))
            if not resume:
                b=job['bounds']
                md={'name':job['name'],'type':'baselayer','version':'1','description':'TAK Map Offline Maps i698',
                    'format':'png','bounds':f"{b['west']},{b['south']},{b['east']},{b['north']}",
                    'center':f"{(b['west']+b['east'])/2},{(b['south']+b['north'])/2},{job['min_zoom']}",
                    'minzoom':job['min_zoom'],'maxzoom':job['max_zoom'],
                    'attribution':source.get('attribution') or ''}
                for key,value in md.items():
                    conn.execute('delete from metadata where name=?',(key,))
                    conn.execute('insert into metadata(name,value) values(?,?)',(key,str(value)))
                conn.commit()
            else:
                row=conn.execute("select value from metadata where name='format' limit 1").fetchone()
                first_format=str(row[0]) if row else 'png'
            saved=h['_mbtiles_tile_count'](tmp)
            update(jid,status='running',map_id=mid,saved=saved,
                   message='Downloading and merging internal batches',concurrency=concurrency)
            persist_progress()
            task_iter=iter(tasks())
            with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as pool:
                while True:
                    if action() in ('pause','cancel'):
                        failed=count_failures()
                        finalize('paused' if action()=='pause' else 'canceled',
                                 'Paused. Saved tiles retained for resume.' if action()=='pause' else 'Canceled with partial map retained.')
                        return
                    batch=[]
                    exhausted=False
                    for _ in range(max(16,concurrency*8)):
                        try:task=next(task_iter)
                        except StopIteration:
                            exhausted=True
                            break
                        z,x,y=task
                        tms_y=(2**z-1)-y
                        found=conn.execute('select 1 from tiles where zoom_level=? and tile_column=? and tile_row=? limit 1',(z,x,tms_y)).fetchone()
                        if found:
                            done+=1
                            conn.execute('delete from offline_failed_tiles_i698 where z=? and x=? and y=?',(z,x,y))
                            if not job.get('retry_only') and done%batch_size==0:
                                conn.execute("update offline_batches_i698 set status='checked' where batch_index=?",(done//batch_size,))
                            continue
                        batch.append(task)
                    if not batch:
                        if exhausted:break
                        continue
                    # Only download currently missing coordinates; successful
                    # tiles are skipped on resume and retry.
                    future_list=[pool.submit(fetch,t) for t in batch]
                    for fut in concurrent.futures.as_completed(future_list):
                        task,data,fmt,error=fut.result()
                        z,x,y=task
                        done+=1
                        if data:
                            if saved==0:first_format=fmt
                            conn.execute('insert or replace into tiles(zoom_level,tile_column,tile_row,tile_data) values(?,?,?,?)',(z,x,(2**z-1)-y,data))
                            conn.execute('delete from offline_failed_tiles_i698 where z=? and x=? and y=?',(z,x,y))
                            saved+=1
                            if saved==1:
                                conn.execute("update metadata set value=? where name='format'",(fmt,))
                        else:
                            conn.execute('insert into offline_failed_tiles_i698(z,x,y,attempts,last_error) values(?,?,?,?,?) on conflict(z,x,y) do update set attempts=attempts+excluded.attempts,last_error=excluded.last_error',(z,x,y,4,error))
                        if not job.get('retry_only') and done%batch_size==0:
                            conn.execute("update offline_batches_i698 set status='checked' where batch_index=?",(done//batch_size,))
                        if done%max(20,concurrency*10)==0:
                            conn.commit()
                            failed=count_failures()
                            if done%max(200,concurrency*100)==0:
                                persist_progress()
                            update(jid,done=done,saved=saved,failed=failed,
                                   internal_job=min(math.ceil(total/batch_size),1+(max(0,done-1)//batch_size)),
                                   message=f'Checked {done:,} / {total:,} tiles; one offline map; {failed} missing',concurrency=concurrency)
                    conn.commit()
            failed=count_failures()
            status='incomplete' if failed else 'complete'
            finalize(status, 'Download finished with '+str(failed)+' failed tiles. Retry/Finish available.' if failed else 'Offline map completed successfully.')
        except Exception as exc:
            try:
                if conn:
                    conn.commit();conn.close();conn=None
                if tmp.exists():
                    if not resume and not final.exists():tmp.rename(final)
                    if final.exists():
                        rec=h['_offline_record_from_job'](job,mid,final,'error',done,h['_mbtiles_tile_count'](final),failed,first_format)
                        rec.update({'area_id':job.get('area_id') or '', 'partial':True,'resume_available':True,
                                    'requested_tile_count':original_total,'internal_jobs':original_batches})
                        h['_upsert_offline_map_record'](rec)
            except Exception:pass
            update(jid,status='error',error=str(exc),message=str(exc),map_id=mid)
