"""TAK Map i651: bounded NDM package validator, catalog, and non-destructive imports.

Never changes external NDM files. This is an administrative server-side API module,
not a public file browser. Valhalla activation is handled separately.
"""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
import stat
import tarfile
import tempfile
import threading
import time
import zipfile
import zlib

# Only HTTP browser uploads are size-limited. Existing NDM ZIPs are already on
# disk and never pass through the upload API, so they have NO file-size quota.
# Archive member/count/expansion safety checks still apply to either source.
MAX_ZIP_BYTES = min(max(int(os.environ.get('TAK_MAP_NDM_MAX_UPLOAD_MB','4096')),1),4096)*1024*1024
MAX_UNCOMPRESSED = 64*1024*1024*1024
MAX_FILES = 100_000
CATALOG_SCHEMA = 1
DEFAULT_ROOTS = ('/var/lib/takrig-routing/ready','/var/lib/takrig-routing/terrain/ready')
_LOCK = threading.RLock()

class NDMError(ValueError):
    def __init__(self, message, code='NDM_INVALID'):
        super().__init__(message)
        self.code = code


def _safe_name(name):
    if not isinstance(name,str) or '\\' in name or '\x00' in name or not name or name.startswith('/'):
        raise NDMError('Unsafe member path')
    parts=PurePosixPath(name).parts
    base=name.rstrip('/')
    if str(PurePosixPath(base))!=base or '..' in parts or '.' in parts or name.startswith('//') or ':' in parts[0]:
        raise NDMError('Unsafe member path')
    return name


def _zip_entries(z):
    names=set(); total=0
    entries=z.infolist()
    if not entries or len(entries)>MAX_FILES:raise NDMError('Invalid ZIP member count')
    for e in entries:
        name=_safe_name(e.filename)
        if name in names:raise NDMError('Duplicate ZIP path')
        names.add(name)
        typ=(e.external_attr>>16)&0o170000
        if typ and typ not in (stat.S_IFREG,stat.S_IFDIR):raise NDMError('ZIP symlink/special member rejected')
        if e.flag_bits&1:raise NDMError('Encrypted ZIP not supported')
        if e.file_size<0 or e.file_size>MAX_UNCOMPRESSED:raise NDMError('Unbounded ZIP member')
        total+=e.file_size
        if total>MAX_UNCOMPRESSED:raise NDMError('ZIP expansion quota exceeded')
    return names


def _tar_scan(z):
    count=0
    # File-like streaming prevents extracting an untrusted tar on the host.
    with z.open('valhalla_tiles.tar') as fp:
        with tarfile.open(fileobj=fp,mode='r|') as tf:
            for m in tf:
                _safe_name(m.name)
                if not m.isfile() and not m.isdir():raise NDMError('Unsafe TAR link or special member')
                if m.size > 64*1024*1024:raise NDMError('Oversized graph tile')
                if m.isfile() and m.name.endswith('.gph'):
                    count+=1
                    if count>200000:raise NDMError('Graph tile count exceeds limit')
                    # consume bytes via tarfile stream, verifying TAR checksums on read
                    data=tf.extractfile(m)
                    while data.read(1024*1024):pass
    if count<1:raise NDMError('Routing archive contains no graph tiles')
    return count


def _validate_terrain_db(filename, manifest):
    uri=Path(filename).resolve().as_uri()+'?mode=ro&immutable=1'
    con=sqlite3.connect(uri,uri=True,timeout=15)
    try:
        if con.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise NDMError('SQLite integrity check failed')
        tables={r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {'metadata','tiles','tile_overviews'} <= tables:raise NDMError('NDM terrain tables missing')
        meta={a:b for a,b in con.execute('SELECT name,value FROM metadata')}
        if meta.get('schema')!='takrig.terrain.sqlite.v1':raise NDMError('Unsupported terrain database schema')
        expected={'tiles':('tile_id','west','south','east','north','rows','cols','min_elev_m','max_elev_m','encoding','data'),
                  'tile_overviews':('tile_id','resolution_m','west','south','east','north','rows','cols','encoding','data')}
        for table,cols in expected.items():
            actual={a[1] for a in con.execute('PRAGMA table_info('+table+')')}
            if not set(cols)<=actual:raise NDMError('Terrain table columns missing')
        counts={t:con.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in ('tiles','tile_overviews')}
        if counts['tiles']<1 or counts['tiles']>50000 or counts['tile_overviews']>200000:raise NDMError('Invalid terrain tile count')
        if counts['tiles']!=int(manifest.get('tile_count',-1)):raise NDMError('Terrain tile count does not match manifest')
        # Validate compressed grids without decoding entire database simultaneously.
        for table in ('tiles','tile_overviews'):
            for rows,cols,encoding,blob in con.execute('SELECT rows,cols,encoding,data FROM '+table):
                if not isinstance(rows,int) or not isinstance(cols,int) or rows<2 or cols<2 or rows*cols>5_000_000:
                    raise NDMError('Terrain grid dimensions out of bounds')
                if encoding!='int16le+zlib':raise NDMError('Unsupported terrain grid encoding')
                size=rows*cols*2
                dec=zlib.decompressobj()
                try:out=dec.decompress(blob,size+1)
                except zlib.error as e:raise NDMError('Invalid compressed elevation grid') from e
                if len(out)!=size or dec.unconsumed_tail or not dec.eof or dec.unused_data:
                    raise NDMError('Invalid compressed elevation grid')
        return counts
    finally:con.close()


def inspect_zip(path, validate_grids=True):
    path=Path(path)
    # Read-only registration must not inherit the browser upload quota.  In
    # particular, multi-GiB NDM routing graph packages are valid input here.
    try:
        st=path.stat()
    except FileNotFoundError as e:
        raise NDMError('NDM ZIP not found; refresh discovered packages','NOT_FOUND') from e
    except PermissionError as e:
        raise NDMError('TAK Map cannot read the NDM ZIP (file/directory permissions)','PERMISSION_DENIED') from e
    if not stat.S_ISREG(st.st_mode):
        raise NDMError('NDM ZIP path is not a regular file')
    with zipfile.ZipFile(path,'r',allowZip64=True) as z:
        names=_zip_entries(z)
        expanded_bytes=sum(entry.file_size for entry in z.infolist())
        if 'manifest.json' not in names:raise NDMError('Missing NDM manifest')
        if z.getinfo('manifest.json').file_size>512*1024:raise NDMError('Manifest too large')
        manifest=json.loads(z.read('manifest.json').decode('utf-8'))
        if not isinstance(manifest,dict):raise NDMError('Invalid NDM manifest')
        fmt=manifest.get('format')
        info={'format':fmt,'region':manifest.get('state_name') or manifest.get('name') or manifest.get('state_code') or 'Unknown',
              'region_id':manifest.get('region_id') or str(manifest.get('state_code','')).lower(),
              'bounds':manifest.get('bounds'),'files':len(names)}
        if not isinstance(info['bounds'],list) or len(info['bounds'])!=4 or any(not isinstance(v,(int,float)) for v in info['bounds']):
            raise NDMError('Invalid geographic bounds')
        if fmt=='takrig.valhalla.region.v1':
            if manifest.get('valhalla_version')!='3.6.3':raise NDMError('Valhalla graph requires version 3.6.3')
            if not {'manifest.json','valhalla.json','valhalla_tiles.tar'}<=names:raise NDMError('Incomplete NDM routing package')
            cfg=json.loads(z.read('valhalla.json'))
            if not isinstance(cfg,dict) or not isinstance(cfg.get('mjolnir'),dict):raise NDMError('Invalid Valhalla config')
            coverage=manifest.get('routing_coverage',{})
            if coverage.get('index')!='routing_coverage/index.json' or coverage['index'] not in names:
                raise NDMError('Missing NDM routing coverage index')
            index=json.loads(z.read(coverage['index']))
            if not isinstance(index,dict):raise NDMError('Malformed coverage index')
            info.update(type='routing',valhalla_version='3.6.3',graph_tiles=_tar_scan(z),coverage_count=sum(x.startswith('routing_coverage/') and x.endswith('.geojson.gz') for x in names))
            if info['coverage_count']!=int(coverage.get('nonempty_tile_count',-1)):
                raise NDMError('Coverage count mismatch')
        elif fmt=='takrig.terrain.region.v1':
            if manifest.get('database_schema')!='takrig.terrain.sqlite.v1':raise NDMError('Unsupported terrain schema')
            if set(names)!={'manifest.json','terrain.sqlite'}:raise NDMError('Unexpected terrain package members')
            info.update(type='terrain',vertical_datum='unknown',tile_count=int(manifest.get('tile_count',-1)),resolution_m=manifest.get('nominal_resolution_m'))
            if validate_grids:
                with tempfile.TemporaryDirectory(prefix='takmap-ndm-sqlite-') as tmp:
                    dst=Path(tmp)/'terrain.sqlite'
                    with z.open('terrain.sqlite') as source,open(dst,'wb') as out:shutil.copyfileobj(source,out,1024*1024)
                    info.update(_validate_terrain_db(dst,manifest))
        else:raise NDMError('Unsupported NDM package format')
        # Read every entry to enforce ZIP CRC, not just metadata.
        bad=z.testzip()
        if bad:raise NDMError('ZIP CRC failed for '+bad)
    info['zip_size_bytes']=path.stat().st_size
    info['expanded_size_bytes']=expanded_bytes
    return info


def sha256_file(path):
    sha=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):sha.update(chunk)
    return sha.hexdigest()


class Catalog:
    def __init__(self,root=None,external_roots=None):
        self.root=Path(root or os.environ.get('TAK_MAP_NDM_DATA_DIR','/var/lib/tak-map/ndm'))
        self.catalog=self.root/'catalog.json'
        roots=external_roots or os.environ.get('TAK_MAP_NDM_EXISTING_ROOTS',':'.join(DEFAULT_ROOTS)).split(':')
        self.external_roots=[Path(x).resolve() for x in roots if x]

    def _load(self):
        if not self.catalog.is_file():return {'schema':CATALOG_SCHEMA,'datasets':{}}
        content=json.loads(self.catalog.read_text())
        if content.get('schema')!=CATALOG_SCHEMA or not isinstance(content.get('datasets'),dict):
            raise NDMError('Unsupported NDM catalog version')
        return content

    def _save(self,data):
        self.root.mkdir(parents=True,exist_ok=True)
        fd,tmp=tempfile.mkstemp(prefix='.catalog-',dir=self.root)
        try:
            with os.fdopen(fd,'w') as fp:
                os.fchmod(fp.fileno(),0o600)
                json.dump(data,fp,sort_keys=True,indent=2)
                fp.flush();os.fsync(fp.fileno())
            os.replace(tmp,self.catalog)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)

    @staticmethod
    def _public(entry):
        return {k:v for k,v in entry.items() if k not in ('zip_path','folder','external_root')}

    def listing(self):
        """Show one current dataset per region/type/resolution; retain history read-only."""
        with _LOCK:
            data=self._load()
            output=[]
            for key,entry in data['datasets'].items():
                e=self._public(entry)
                p=Path(entry['zip_path'])
                if entry.get('owner')=='ndm-external':
                    try:
                        st=p.stat()
                        e['available']=p.is_file() and st.st_size==entry.get('source_size') and st.st_mtime_ns==entry.get('source_mtime_ns')
                    except OSError:e['available']=False
                else:e['available']=p.is_file()
                e['status']='Active' if entry.get('active') else ('Available' if e['available'] else 'Missing')
                e['superseded']=False
                output.append(e)
            groups={}
            for e in output:
                if not e['available']:continue
                key=(e.get('region_id') or e.get('region','').lower(),e.get('type'),e.get('resolution_m') if e.get('type')=='terrain' else None)
                # Newer source mtime wins even when the registration timestamps tie.
                priority=(int(e.get('source_mtime_ns') or 0),int(e.get('installed_at') or 0),e['dataset_id'])
                if key not in groups or priority>groups[key][0]:groups[key]=(priority,e['dataset_id'])
            for e in output:
                key=(e.get('region_id') or e.get('region','').lower(),e.get('type'),e.get('resolution_m') if e.get('type')=='terrain' else None)
                if not e.get('active') and key in groups and groups[key][1]!=e['dataset_id']:
                    e['superseded']=True
                    e['status']='Superseded'
            return output

    def sync_existing(self,max_new=8):
        """Bounded full validation of changed NDM packages, preserving all old entries/files.
        Caller runs this in a background server worker, never a request thread.
        """
        added=[];failures=[]
        with _LOCK:
            registered=list(self._load()['datasets'].values())
        by_source={(e.get('zip_path'),e.get('source_size'),e.get('source_mtime_ns'))
                   for e in registered if e.get('owner')=='ndm-external'}
        for root in self.external_roots:
            if not root.is_dir():continue
            directories=[root]+[p for p in root.iterdir() if p.is_dir() and not p.is_symlink()]
            for directory in directories:
                for path in sorted(directory.glob('*.zip')):
                    if path.is_symlink() or not path.is_file():continue
                    resolved=path.resolve()
                    if root!=resolved and root not in resolved.parents:continue
                    try:
                        st=resolved.stat()
                        key=(str(resolved),st.st_size,st.st_mtime_ns)
                        if key in by_source:continue
                        # Reject files currently changing; a later pass can register them.
                        entry,duplicate=self._register(resolved,'ndm-external')
                        if resolved.stat().st_size!=st.st_size or resolved.stat().st_mtime_ns!=st.st_mtime_ns:
                            raise NDMError('NDM package changed during registration')
                        by_source.add(key)
                        if not duplicate:added.append(entry['dataset_id'])
                        if len(added)>=max_new:return {'added':added,'errors':failures}
                    except (OSError,ValueError,zipfile.BadZipFile) as exc:
                        failures.append({'name':path.name,'error':str(exc)[:160]})
        return {'added':added,'errors':failures}

    def discover(self):
        # Never return paths to an untrusted client or accept arbitrary paths from it.
        results=[]
        for root in self.external_roots:
            if not root.is_dir():continue
            for directory in [root]+[p for p in root.iterdir() if p.is_dir() and not p.is_symlink()]:
                for p in directory.glob('*.zip'):
                    if p.is_symlink() or not p.is_file():continue
                    resolved=p.resolve()
                    if root!=resolved and root not in resolved.parents:continue
                    stat_result=p.stat()
                    token=hashlib.sha256((str(resolved)+'|'+str(stat_result.st_size)+'|'+str(stat_result.st_mtime_ns)).encode()).hexdigest()
                    results.append({'discovery_id':token,'name':p.name,'size_bytes':stat_result.st_size})
                    if len(results)>=250:return results
        return results

    def _resolve_discovery(self,token):
        if not isinstance(token,str) or len(token)!=64:raise NDMError('Invalid discovery ID')
        for root in self.external_roots:
            if not root.is_dir():continue
            for directory in [root]+[p for p in root.iterdir() if p.is_dir() and not p.is_symlink()]:
                for p in directory.glob('*.zip'):
                    if not p.is_file() or p.is_symlink():continue
                    resolved=p.resolve()
                    if root!=resolved and root not in resolved.parents:continue
                    st=p.stat()
                    expect=hashlib.sha256((str(resolved)+'|'+str(st.st_size)+'|'+str(st.st_mtime_ns)).encode()).hexdigest()
                    if expect==token:return resolved
        raise NDMError('Discovered file no longer available','NOT_FOUND')

    def register_existing(self,token):
        path=self._resolve_discovery(token)
        return self._register(path,'ndm-external')

    def _register(self,path,owner,folder=None):
        before=Path(path).stat()
        info=inspect_zip(path)
        sha=sha256_file(path)
        st=Path(path).stat()
        if st.st_size!=before.st_size or st.st_mtime_ns!=before.st_mtime_ns:
            raise NDMError('NDM package changed while being validated; retry after rebuilding completes')
        entry={'dataset_id':sha,'owner':owner,'zip_path':str(path),'source_size':st.st_size,'source_mtime_ns':st.st_mtime_ns,
               'installed_at':int(time.time()),'state':'registered','active':False,**info}
        if folder:entry['folder']=str(folder)
        with _LOCK:
            data=self._load()
            if sha in data['datasets']:return self._public(data['datasets'][sha]),True
            data['datasets'][sha]=entry
            self._save(data)
            return self._public(entry),False

    def import_stream(self,stream,length):
        if not isinstance(length,int) or length<1:raise NDMError('Invalid import size','INVALID_SIZE')
        if length>MAX_ZIP_BYTES:raise NDMError('Browser NDM ZIP uploads are limited to 4 GiB','TOO_LARGE')
        self.root.mkdir(parents=True,exist_ok=True)
        (self.root/'staging').mkdir(exist_ok=True)
        (self.root/'imports').mkdir(exist_ok=True)
        free=shutil.disk_usage(self.root).free
        if free<length*3+256*1024*1024:raise NDMError('Insufficient free disk space','NO_SPACE')
        fd,temp=tempfile.mkstemp(prefix='ndm-upload-',suffix='.zip',dir=self.root/'staging')
        try:
            with os.fdopen(fd,'wb') as out:
                os.fchmod(out.fileno(),0o600)
                remaining=length
                while remaining:
                    chunk=stream.read(min(1024*1024,remaining))
                    if not chunk:raise NDMError('Incomplete upload')
                    out.write(chunk);remaining-=len(chunk)
                out.flush();os.fsync(out.fileno())
            info=inspect_zip(temp)
            sha=sha256_file(temp)
            with _LOCK:
                data=self._load()
                if sha in data['datasets']:return self._public(data['datasets'][sha]),True
                dest=self.root/'imports'/sha
                if dest.exists():
                    # Handle an interrupted previous import safely; never assume old files match.
                    existing=dest/'source.zip'
                    if not existing.is_file() or sha256_file(existing)!=sha:raise NDMError('Prior import folder conflicts with requested package')
                else:
                    # The archive can contain more uncompressed bytes than its
                    # upload size. Reserve room for the extraction and source
                    # archive in addition to the staged upload, before writing.
                    free_now=shutil.disk_usage(self.root).free
                    needed=int(info['expanded_size_bytes'])+length+256*1024*1024
                    if free_now<needed:
                        raise NDMError('Insufficient disk space to unpack this NDM ZIP safely','NO_SPACE')
                    work=Path(tempfile.mkdtemp(prefix='.ndm-promote-',dir=self.root/'imports'))
                    try:
                        with zipfile.ZipFile(temp) as z:
                            _zip_entries(z)
                            for m in z.infolist():
                                target=work/_safe_name(m.filename)
                                if m.is_dir():target.mkdir(parents=True,exist_ok=True);continue
                                target.parent.mkdir(parents=True,exist_ok=True)
                                with z.open(m) as fi,open(target,'wb') as fo:shutil.copyfileobj(fi,fo,1024*1024)
                                target.chmod(0o600)
                        shutil.copyfile(temp,work/'source.zip')
                        os.replace(work,dest)
                    finally:
                        if work.exists():shutil.rmtree(work)
                path=dest/'source.zip'
                st=path.stat()
                entry={'dataset_id':sha,'owner':'tak-map-import','zip_path':str(path),'folder':str(dest),
                       'source_size':st.st_size,'source_mtime_ns':st.st_mtime_ns,'installed_at':int(time.time()),
                       'state':'registered','active':False,**info}
                data['datasets'][sha]=entry
                self._save(data)
            return self._public(entry),False
        finally:
            try:os.unlink(temp)
            except FileNotFoundError:pass

    def unregister(self,sha):
        with _LOCK:
            data=self._load()
            if sha not in data['datasets']:raise NDMError('Dataset not registered','NOT_FOUND')
            if data['datasets'][sha].get('active'):raise NDMError('Active dataset cannot be detached')
            del data['datasets'][sha]
            self._save(data)
            # NEVER delete files, including TAK Map-owned imports.
            return True

    def detail(self,sha):
        with _LOCK:return self._load()['datasets'].get(sha)
