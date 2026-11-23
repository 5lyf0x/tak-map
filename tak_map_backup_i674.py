"""TAK Map i674 selective encrypted backup/restore engine.

Root-only action helper. No secret in argv; requests arrive on stdin. Restore only
within fixed TAK Map-owned path allowlists. Archives are self-contained and
password encrypted with scrypt + per-chunk AES-256-GCM.
"""
from __future__ import annotations
import base64
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import secrets
import shutil
import sqlite3
import stat
import struct
import sys
import tempfile
import subprocess
import zipfile
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

DATA=Path(os.environ.get('TAK_DASHBOARD_DATA_DIR','/var/lib/tak-map'))
ETC=Path('/etc/tak-map')
ENV=Path('/etc/tak-map.env')
BACKUPS=DATA/'backup_restore_i674'
FORMAT='tak-map-selective-backup-v1'
MAGIC=b'TAKMBK1\0'
CHUNK=4*1024*1024
CATEGORIES=('points','shapes','routes','basemaps','veil','geofences','adsb','gateway_data','mesh_sync','data_sync','local_data','offline_maps','satellite')
# Map-owned persistent state only. No Gateway/NDM/VEIL server data.
SOURCES={
 'basemaps':['tak_map_offline/map_prefs.json','tak_map_offline/tak_map_prefs.json','custom_basemaps','basemaps'],
 'veil':['tak_map_veil'],
 'geofences':['tak_map_offline/geofences.json'],
 'adsb':['tak_map_offline/adsb_settings.json'],
 'gateway_data':['gateway_data_connection.json','client-certs','ots_connection.json','ots_trust','ots_user_credentials','ots_user_credentials.master','tak_client_identity.json','ots_enrollment_manifest_i586.json','ots_enrollment_manifest_i587.json','ots_enrollment_manifest_i588.json','ots_enrollment_manifest_i589.json'],
 'mesh_sync':['token_mesh'],
 'data_sync':['ots_user_credentials','ots_user_credentials.master','tak_client_identity.json','data_sync_snapshots_i568','data_sync_deleted_uid_fences_i563.json','data_sync_transport_authority_i584_hf2','mission_unlock_users_i572','mission_unlock_users_i575','mission_access_index_i591','tak_map_data_sync_associations_i635.json'],
 'local_data':['tak_map_offline/popup_edits.json','tak_map_imports'],
 'offline_maps':['tak_map_offline/offline_maps.json','tak_map_offline/packages','tak_map_offline/elevation','tak_map_offline/dem'],
 'satellite':['satellite','satellite_tracking','tak_map_satellites'],
}
# Sensitive certs and env keys. The env file is backed up by *selected key*, not as
# a monolithic settings file that would contaminate independent restore categories.
EXTRA={'gateway_data':[ETC],'mesh_sync':[ETC],'data_sync':[ETC]}
ENV_PREFIXES={
 'adsb':('TAK_DASH_ADSB_','TAK_MAP_ADSB_'),
 'basemaps':('TAK_MAP_BASEMAP_','TAK_DASH_MAP_DEFAULT_BASEMAP'),
 'geofences':('TAK_MAP_GEOFENCE_','TAK_DASH_GEOFENCE_'),
 'gateway_data':('TAK_MAP_GATEWAY_','TAK_MAP_REPLAY_','TAK_MAP_SERVICE_','TAK_MAP_OTS_','TAK_DASH_OTS_','TAK_DASHBOARD_'),
 'mesh_sync':('TAK_MAP_MESH_','TAK_MAP_TOKEN_MESH_','TAK_MESH_'),
 'veil':('TAK_MAP_VEIL_','TAK_MAP_XTAK_','XTAK_VEIL_'),
 'data_sync':('TAK_MAP_DATA_SYNC_','TAK_MAP_MISSION_'),
 'satellite':('TAK_MAP_SATELLITE_','TAK_MAP_CELESTRAK_'),
 'offline_maps':('TAK_MAP_OFFLINE_','TAK_DASH_OFFLINE_'),
}
class BackupError(ValueError):pass

def check_path(path:Path,root:Path)->None:
    if not path.is_relative_to(root):raise BackupError('Path escapes managed root')
    cur=root
    if cur.is_symlink():raise BackupError('Managed root is a symlink')
    for part in path.relative_to(root).parts:
        cur=cur/part
        if cur.is_symlink():raise BackupError('Symlink in managed data: '+str(cur))

def file_list(selected):
    found={};used=set()
    def add(cat,path,target):
        name=target if target not in used else 'duplicate/'+cat+'/'+target
        if name in used:raise BackupError('Duplicate source path in a category')
        used.add(name)
        found[name]=(cat,path,target)
    for cat in selected:
        for rel in SOURCES.get(cat,[]):
            path=DATA/rel;check_path(path,DATA)
            if path.is_file() and not (cat=='local_data' and rel=='tak_map_imports/imports.json'):
                add(cat,path,'var/'+rel)
            elif path.is_dir():
                for root,dirs,files in os.walk(path,followlinks=False):
                    root=Path(root)
                    for name in dirs+files:check_path(root/name,DATA)
                    for name in files:
                        f=root/name
                        if f.is_file() and not f.name.endswith(('-wal','-shm')) and not (cat=='local_data' and f==DATA/'tak_map_imports/imports.json'):
                            add(cat,f,'var/'+f.relative_to(DATA).as_posix())
        for path in EXTRA.get(cat,[]):
            if not path.exists():continue
            check_path(path,ETC)
            for root,dirs,files in os.walk(path,followlinks=False):
                root=Path(root)
                for name in dirs+files:check_path(root/name,ETC)
                for name in files:
                    f=root/name
                    if f.is_file() and not f.name.endswith(('-wal','-shm')):
                        add(cat,f,'etc/'+f.relative_to(ETC).as_posix())
    return found

def classify(obj):
    kind=str(obj.get('kind') or (obj.get('properties') or {}).get('kind') or '').lower()
    geo=str(obj.get('geometry_type') or obj.get('geometry') or obj.get('type') or '').lower()
    if kind in ('shape','area','polygon','line','drawing'):return 'shapes'
    if kind in ('route','track'):return 'routes'
    if kind in ('point','marker','waypoint','pin'):return 'points'
    if any(x in geo for x in ('polygon','multi')):return 'shapes'
    if 'linestring' in geo:return 'routes'
    if 'point' in geo:return 'points'
    return 'local_data'

def read_imports():
    p=DATA/'tak_map_imports/imports.json'
    if not p.exists():return []
    obj=json.loads(p.read_text())
    if not isinstance(obj,dict) or not isinstance(obj.get('imports'),list):raise BackupError('Invalid imports catalog')
    return obj['imports']

def objects_for(cat):
    out=[]
    for imp in read_imports():
        if not isinstance(imp,dict):continue
        rows=[x for x in imp.get('features',[]) if isinstance(x,dict) and classify(x)==cat]
        if rows:out.append({**imp,'features':rows})
    return out

def env_records(selected):
    if not ENV.exists():return {}
    lines=ENV.read_text().splitlines(keepends=True)
    groups={cat:[] for cat in selected}
    for line in lines:
        if '=' not in line or line.lstrip().startswith('#'):continue
        key=line.split('=',1)[0].strip()
        for cat in selected:
            if any(key.startswith(p) for p in ENV_PREFIXES.get(cat,())):
                groups[cat].append(line);break
    return {cat:''.join(lines) for cat,lines in groups.items() if lines}

def derive(pw,salt):
    if not isinstance(pw,str) or len(pw)<12 or len(pw)>512:raise BackupError('Backup password must be 12–512 characters')
    return Scrypt(salt=salt,length=32,n=2**15,r=8,p=1).derive(pw.encode())

def encrypt(source:Path,target:Path,password):
    salt=secrets.token_bytes(16);prefix=secrets.token_bytes(8);aes=AESGCM(derive(password,salt))
    tmp=target.with_name(target.name+'.partial-'+secrets.token_hex(5))
    try:
        with source.open('rb') as f, tmp.open('xb') as out:
            out.write(MAGIC+salt+prefix)
            i=0
            while True:
                block=f.read(CHUNK)
                if not block:break
                sealed=aes.encrypt(prefix+i.to_bytes(4,'big'),block,MAGIC+i.to_bytes(4,'big'))
                out.write(struct.pack('>I',len(sealed)));out.write(sealed);i+=1
                if i>2**32-2:raise BackupError('Archive too large')
            out.write(struct.pack('>I',0));out.flush();os.fsync(out.fileno())
        os.chmod(tmp,0o640);os.replace(tmp,target)
    finally:tmp.unlink(missing_ok=True)

def decrypt(source:Path,target:Path,password):
    with source.open('rb') as inp, target.open('xb') as out:
        header=inp.read(32)
        if len(header)!=32 or header[:8]!=MAGIC:raise BackupError('Invalid TAK Map encrypted backup format')
        aes=AESGCM(derive(password,header[8:24]));prefix=header[24:32]
        i=0
        while True:
            sizebuf=inp.read(4)
            if len(sizebuf)!=4:raise BackupError('Truncated encrypted backup')
            n=struct.unpack('>I',sizebuf)[0]
            if not n:
                if inp.read(1):raise BackupError('Trailing backup data')
                break
            if n>CHUNK+16:raise BackupError('Oversized encrypted backup chunk')
            sealed=inp.read(n)
            if len(sealed)!=n:raise BackupError('Truncated encrypted backup')
            try:plain=aes.decrypt(prefix+i.to_bytes(4,'big'),sealed,MAGIC+i.to_bytes(4,'big'))
            except Exception:raise BackupError('Wrong password or damaged archive') from None
            out.write(plain);i+=1
            if i>2**32-2:raise BackupError('Invalid archive chunk count')
        out.flush();os.fsync(out.fileno())

def validate_zip(z):
    try:manifest=json.loads(z.read('manifest.json'))
    except Exception:raise BackupError('Missing or invalid backup manifest')
    if manifest.get('format')!=FORMAT:raise BackupError('Unsupported backup schema')
    cats=manifest.get('categories')
    if not isinstance(cats,list) or any(x not in CATEGORIES for x in cats) or len(set(cats))!=len(cats):raise BackupError('Invalid categories')
    entries=manifest.get('files')
    if not isinstance(entries,list) or len(entries)>150000:raise BackupError('Invalid file index')
    names=set(z.namelist())
    indexed={'manifest.json'}
    for entry in entries:
        name=entry.get('name','');group=entry.get('category','')
        if not isinstance(name,str) or name in indexed or name not in names or group not in cats:raise BackupError('Invalid backup entry')
        pp=PurePosixPath(name)
        if pp.is_absolute() or '..' in pp.parts or len(pp.parts)<2 or pp.parts[0] not in ('var','etc','duplicate','objects','browser','environment'):raise BackupError('Unsafe backup path')
        target=entry.get('target',name)
        if not isinstance(target,str):raise BackupError('Invalid target')
        targetpath=PurePosixPath(target)
        if name.startswith('duplicate/'):
            if len(pp.parts)<4 or pp.parts[1]!=group or '/'.join(pp.parts[2:])!=target:
                raise BackupError('Invalid duplicate category path')
        elif 'target' in entry:raise BackupError('Unexpected backup target override')
        if name.startswith(('var/','etc/','duplicate/')):
            if targetpath.is_absolute() or '..' in targetpath.parts or len(targetpath.parts)<2 or targetpath.parts[0] not in ('var','etc'):
                raise BackupError('Unsafe restore destination')
        info=z.getinfo(name)
        if info.is_dir() or (info.external_attr>>16)&0o170000==0o120000:raise BackupError('Invalid archived file')
        if info.file_size!=entry.get('size') or info.file_size>32*1024**3:raise BackupError('Invalid entry size')
        h=hashlib.sha256()
        with z.open(name) as f:
            while (part:=f.read(1024*1024)):h.update(part)
        if h.hexdigest()!=entry.get('sha256'):raise BackupError('Backup integrity check failed')
        indexed.add(name)
    if indexed!=names:raise BackupError('Unexpected entries in backup')
    return manifest

def manifest_entry(z,name,data,category,target=None):
    if isinstance(data,Path):
        h=hashlib.sha256();n=0
        with data.open('rb') as f:
            while (b:=f.read(1024*1024)):h.update(b);n+=len(b)
        z.write(data,name)
    else:
        h=hashlib.sha256(data);n=len(data);z.writestr(name,data)
    return dict({'name':name,'category':category,'size':n,'sha256':h.hexdigest()},**({'target':target} if target and target!=name else {}))

def create(req):
    cats=req.get('categories');pw=req.get('password');browser=req.get('browser') or {}
    if not isinstance(cats,list) or not cats or len(cats)!=len(set(cats)) or any(x not in CATEGORIES for x in cats):raise BackupError('Invalid backup selection')
    if not isinstance(browser,dict):raise BackupError('Invalid browser payload')
    BACKUPS.mkdir(mode=0o750,parents=True,exist_ok=True)
    try:shutil.chown(BACKUPS,'takmap','takmap')
    except LookupError:pass
    stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    filename='tak-map-backup-'+stamp+'-'+secrets.token_hex(5)+'.takmbk'
    with tempfile.TemporaryDirectory(prefix='takmap-backup-',dir=BACKUPS) as work:
        ziptmp=Path(work)/'archive.zip'
        entries=[]
        with zipfile.ZipFile(ziptmp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=5,allowZip64=True) as z:
            for name,(cat,path,target) in file_list(cats).items():
                if path.suffix in ('.sqlite3','.sqlite','.db'):
                    snapshot=Path(work)/('snapshot-'+secrets.token_hex(8)+'.sqlite3')
                    with sqlite3.connect(f'file:{path}?mode=ro',uri=True,timeout=10) as source_db, sqlite3.connect(snapshot) as target_db:
                        source_db.backup(target_db)
                    try:entries.append(manifest_entry(z,name,snapshot,cat,target))
                    finally:snapshot.unlink(missing_ok=True)
                else:entries.append(manifest_entry(z,name,path,cat,target))
            for cat in cats:
                if cat in ('points','shapes','routes','local_data'):
                    entries.append(manifest_entry(z,'objects/'+cat+'.json',json.dumps(objects_for(cat),separators=(',',':')).encode(),cat))
                if cat in browser:
                    raw=json.dumps(browser[cat],separators=(',',':')).encode()
                    if len(raw)>256*1024**2:raise BackupError('Browser data too large for one category')
                    entries.append(manifest_entry(z,'browser/'+cat+'.json',raw,cat))
            for cat,lines in env_records(cats).items():
                entries.append(manifest_entry(z,'environment/'+cat+'.txt',lines.encode(),cat))
            manifest={'format':FORMAT,'source_version':'1.4.0-i674','created_utc':stamp,'categories':cats,'files':entries,
                      'note':'Password and existing client/server trust are required for restore. Browser data is captured from the active browser.'}
            z.writestr('manifest.json',json.dumps(manifest,sort_keys=True,separators=(',',':')))
        with zipfile.ZipFile(ziptmp) as z:validate_zip(z)
        output=BACKUPS/filename
        encrypt(ziptmp,output,pw)
    try:shutil.chown(output,user='takmap',group='takmap')
    except (LookupError,PermissionError):pass
    return {'ok':True,'file':filename,'bytes':output.stat().st_size,'categories':cats,'files':len(entries)}

def inspect(req):
    filename=req.get('file')
    if not isinstance(filename,str) or not filename.endswith('.takmbk') or Path(filename).name!=filename:raise BackupError('Invalid backup file')
    source=(BACKUPS/filename)
    if not source.is_file() or source.is_symlink():raise BackupError('Backup not found')
    with tempfile.TemporaryDirectory(prefix='takmap-verify-',dir=BACKUPS) as work:
        clear=Path(work)/'clear.zip'
        decrypt(source,clear,req.get('password'))
        with zipfile.ZipFile(clear) as z:manifest=validate_zip(z)
    return {'ok':True,'categories':manifest['categories'],'created_utc':manifest['created_utc'],'source_version':manifest['source_version'],'files':len(manifest['files']),'size':source.stat().st_size}

def _restore_imports(z,selected):
    names={f'objects/{cat}.json' for cat in selected if cat in ('points','shapes','routes','local_data')}
    if not names:return None
    imports=read_imports()
    unchanged=[]
    for imp in imports:
        if not isinstance(imp,dict):continue
        kept=[f for f in imp.get('features',[]) if isinstance(f,dict) and classify(f) not in selected]
        if kept:unchanged.append({**imp,'features':kept})
    byid={str(imp.get('id')):imp for imp in unchanged}
    for name in sorted(names):
        if name not in z.namelist():raise BackupError('Selected object category missing')
        records=json.loads(z.read(name))
        if not isinstance(records,list):raise BackupError('Invalid object catalog')
        for imp in records:
            if not isinstance(imp,dict) or not isinstance(imp.get('features'),list):raise BackupError('Invalid object record')
            cat=name.split('/')[-1].split('.')[0]
            if any(not isinstance(f,dict) or classify(f)!=cat for f in imp['features']):raise BackupError('Category mismatch in objects')
            ident=str(imp.get('id') or '')
            if not ident:raise BackupError('Missing import ID')
            if ident in byid:byid[ident]['features'].extend(imp['features'])
            else:byid[ident]=imp
    for imp in byid.values():
        kinds={'point':0,'route':0,'shape':0,'other':0}
        for f in imp.get('features',[]):
            typ=classify(f)
            kinds[{'points':'point','routes':'route','shapes':'shape'}.get(typ,'other')]+=1
        imp['counts']=kinds
    return json.dumps({'imports':list(byid.values())},ensure_ascii=False,indent=2).encode()

def _env_merge(z,selected):
    incoming={}
    for cat in selected:
        name='environment/'+cat+'.txt'
        if name in z.namelist():
            for line in z.read(name).decode().splitlines(keepends=True):
                if '=' in line and not line.lstrip().startswith('#'):
                    key=line.split('=',1)[0].strip()
                    if any(key.startswith(p) for p in ENV_PREFIXES.get(cat,())):incoming[key]=line
    if not incoming:return None
    lines=ENV.read_text().splitlines(keepends=True) if ENV.exists() else []
    result=[];written=set()
    for line in lines:
        key=line.split('=',1)[0].strip() if '=' in line else ''
        if any(any(key.startswith(p) for p in ENV_PREFIXES.get(cat,())) for cat in selected):
            if key in incoming and key not in written:result.append(incoming[key]);written.add(key)
        else:result.append(line)
    for key,line in incoming.items():
        if key not in written:result.append(line)
    return ''.join(result).encode()

def restore(req):
    selected=req.get('categories');filename=req.get('file');pw=req.get('password')
    if req.get('confirm')!='RESTORE':raise BackupError('Explicit restore confirmation required')
    if not isinstance(selected,list) or not selected or len(set(selected))!=len(selected) or any(x not in CATEGORIES for x in selected):raise BackupError('Invalid restore selection')
    if not isinstance(filename,str) or Path(filename).name!=filename or not filename.endswith('.takmbk'):raise BackupError('Invalid backup filename')
    source=BACKUPS/filename
    if not source.is_file() or source.is_symlink():raise BackupError('Backup not found')
    with tempfile.TemporaryDirectory(prefix='takmap-restore-',dir=BACKUPS) as work:
        work=Path(work);clear=work/'archive.zip';decrypt(source,clear,pw)
        with zipfile.ZipFile(clear) as z:
            manifest=validate_zip(z)
            if any(c not in manifest['categories'] for c in selected):raise BackupError('Selected category absent from backup')
            if req.get('preview_only') is True:
                return {'ok':True,'preview':True,'categories':selected,'file_count':sum(x['category'] in selected for x in manifest['files'])}
            changes={}
            for entry in manifest['files']:
                if entry['category'] not in selected:continue
                name=entry['name'];target=entry.get('target',name)
                if target.startswith('var/'):
                    dest=DATA/target[4:];check_path(dest,DATA)
                elif target.startswith('etc/'):
                    dest=ETC/target[4:];check_path(dest,ETC)
                else:continue
                changes[dest]=(name,z.read(name) if entry['size']<=8*1024*1024 else None)
            object_data=_restore_imports(z,selected)
            if object_data is not None:changes[DATA/'tak_map_imports/imports.json']=(None,object_data)
            env_data=_env_merge(z,selected)
            if env_data is not None:changes[ENV]=(None,env_data)
            # Never replace a live token-mesh or Data Sync journal while operating.
            if any(c in selected for c in ('mesh_sync','data_sync')) and not req.get('allow_sync_replace'):
                raise BackupError('Mesh/Data Sync restore requires explicit journal replacement approval; stop active synchronization and check revisions first')
            # Durable encrypted rollback of the selected server-owned categories.
            # This is created before any mutation and kept on disk for recovery.
            rollback_archive=create({'categories':selected,'password':pw,'browser':{}})['file']
            # A complete pre-restore copy of files touched is mandatory; restore failures
            # return the previous contents even if individual replacements succeeded.
            rollback=work/'rollback';rollback.mkdir()
            existed={}
            for i,(dst,(source_name,val)) in enumerate(changes.items()):
                existed[dst]=dst.exists()
                if dst.exists():
                    if not dst.is_file() or dst.is_symlink():raise BackupError('Unsafe destination')
                    shutil.copy2(dst,rollback/str(i))
            applied=[]
            try:
                for i,(dst,(source_name,val)) in enumerate(changes.items()):
                    dst.parent.mkdir(parents=True,exist_ok=True)
                    if val is None:
                        name=source_name
                        temp=dst.with_name(dst.name+'.i674-'+secrets.token_hex(6))
                        with z.open(name) as inp,temp.open('xb') as out:shutil.copyfileobj(inp,out,1024*1024)
                    else:
                        temp=dst.with_name(dst.name+'.i674-'+secrets.token_hex(6));temp.write_bytes(val)
                    mode=0o600 if dst==ENV or dst.is_relative_to(ETC) else 0o640
                    os.chmod(temp,mode)
                    if existed[dst]:
                        st=dst.stat();os.chown(temp,st.st_uid,st.st_gid)
                    elif dst.is_relative_to(DATA):
                        try:shutil.chown(temp,'takmap','takmap')
                        except LookupError:pass
                    os.replace(temp,dst);applied.append(dst)
            except Exception:
                for dst in reversed(applied):
                    if existed[dst]:shutil.copy2(rollback/str(list(changes).index(dst)),dst)
                    else:dst.unlink(missing_ok=True)
                raise
            browser={}
            for cat in selected:
                name='browser/'+cat+'.json'
                if name in z.namelist():browser[cat]=json.loads(z.read(name))
            return {'ok':True,'restored':selected,'files_restored':len(applied),'rollback_file':rollback_archive,'browser':browser,'message':'Server data restored. Apply returned browser state in the original browser, then reload.'}



def archive_browser(req):
    filename=req.get('file');selected=req.get('categories')
    if not isinstance(filename,str) or Path(filename).name!=filename or not filename.endswith('.takmbk'):
        raise BackupError('Invalid backup filename')
    if not isinstance(selected,list) or any(c not in CATEGORIES for c in selected):raise BackupError('Invalid selection')
    with tempfile.TemporaryDirectory(prefix='takmap-browser-',dir=BACKUPS) as work:
        plain=Path(work)/'archive.zip';decrypt(BACKUPS/filename,plain,req.get('password'))
        with zipfile.ZipFile(plain) as z:
            m=validate_zip(z)
            if any(c not in m['categories'] for c in selected):raise BackupError('Category missing')
            out={}
            for cat in selected:
                name='browser/'+cat+'.json'
                if name in z.namelist():out[cat]=json.loads(z.read(name))
    return {'ok':True,'browser':out}

def schedule_restore(req):
    """Preverify then restore after stopping the TAK Map service (no live journal swap)."""
    selected=req.get('categories')
    if not isinstance(selected,list) or not any(c in selected for c in ('mesh_sync','data_sync')):
        raise BackupError('Offline restore is reserved for Mesh/Data Sync journals')
    if req.get('sync_confirmation')!='REPLACE SYNC JOURNALS':
        raise BackupError('Explicit Mesh/Data Sync journal replacement confirmation required')
    # This ensures wrong password, invalid categories and corrupt archive never stop the service.
    peek=dict(req,preview_only=True,confirm='RESTORE')
    restore(peek)
    jobid=secrets.token_hex(12)
    read_token=secrets.token_hex(32)
    access=BACKUPS/('restore-access-'+jobid+'.json')
    access.write_text(json.dumps({'sha256':hashlib.sha256(read_token.encode()).hexdigest(),
                                  'expires':int(dt.datetime.now(dt.timezone.utc).timestamp())+1800}))
    os.chmod(access,0o600)
    try:shutil.chown(access,'takmap','takmap')
    except LookupError:pass
    runtime=Path('/run/tak-map-backup-i674');runtime.mkdir(mode=0o700,parents=True,exist_ok=True)
    os.chmod(runtime,0o700)
    jobdir=runtime/jobid;jobdir.mkdir(mode=0o700)
    inputfile=jobdir/'request.json'
    inputfile.write_text(json.dumps(dict(req,confirm='RESTORE',allow_sync_replace=True)))
    os.chmod(inputfile,0o600)
    name='tak-map-restore-i674-'+jobid
    cmd=['/usr/bin/systemd-run','--quiet','--unit='+name,'--on-active=3s',
         '/usr/bin/python3','/opt/tak-map/tak_map_backup_i674.py','restore-job',str(jobdir)]
    proc=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=25)
    if proc.returncode:
        shutil.rmtree(jobdir,ignore_errors=True)
        access.unlink(missing_ok=True)
        raise BackupError('Could not schedule maintenance restore: '+proc.stderr.decode(errors='replace')[:160])
    return {'ok':True,'scheduled':True,'job':jobid,'read_token':read_token,'message':'A guarded maintenance restore is scheduled. TAK Map will restart automatically; stay on this page to see the result.'}

def restore_job(directory):
    """Systemd transient unit executes after web response has completed."""
    directory=Path(directory)
    if not directory.is_relative_to(Path('/run/tak-map-backup-i674')) or directory.is_symlink() or not directory.is_dir():
        raise BackupError('Invalid restore job path')
    requestfile=directory/'request.json'
    if requestfile.is_symlink() or not requestfile.is_file():raise BackupError('Restore request missing')
    req=json.loads(requestfile.read_text())
    jobid=directory.name
    status=BACKUPS/('restore-job-'+jobid+'.json')
    BACKUPS.mkdir(parents=True,exist_ok=True)
    stopped=False
    try:
        subprocess.run(['/usr/bin/systemctl','stop','tak-map.service'],timeout=50,check=True)
        stopped=True
        result=restore(req)
        # Only after the service has stopped. Files are committed, and startup
        # reloads journal identity and saved configuration.
        answer={'ok':True,'job':jobid,'restored':result['restored'],
                'files_restored':result['files_restored'],'rollback_file':result.get('rollback_file'),
                'message':'Server restore completed; apply returned browser snapshot.'}
    except Exception as exc:
        answer={'ok':False,'job':jobid,'error':str(exc)[:300]}
    finally:
        try:
            subprocess.run(['/usr/bin/systemctl','start','tak-map.service'],timeout=90,check=True)
        except Exception as exc:
            answer={'ok':False,'job':jobid,'error':'Restore attempted, but TAK Map restart failed: '+str(exc)[:200]}
        fd,tmp=tempfile.mkstemp(prefix='.i674-status-',dir=BACKUPS)
        with os.fdopen(fd,'w') as f:json.dump(answer,f)
        os.chmod(tmp,0o600)
        try:shutil.chown(tmp,'takmap','takmap')
        except LookupError:pass
        os.replace(tmp,status)
        shutil.rmtree(directory,ignore_errors=True)
    return answer

def main():
    if os.geteuid()!=0:raise BackupError('Backup engine must be run through the privileged TAK Map action helper')
    action=sys.argv[1] if len(sys.argv)>1 else ''
    if action=='restore-job':
        if len(sys.argv)!=3:raise BackupError('Restore job path required')
        restore_job(sys.argv[2]);return
    request=json.load(sys.stdin)
    if action=='create':r=create(request)
    elif action=='inspect':r=inspect(request)
    elif action=='restore':r=restore(request)
    elif action=='schedule':r=schedule_restore(request)
    elif action=='browser':r=archive_browser(request)
    else:raise BackupError('Unknown backup operation')
    print(json.dumps(r,separators=(',',':')))

if __name__=='__main__':
    try:main()
    except (BackupError,ValueError,KeyError,PermissionError,FileNotFoundError,zipfile.BadZipFile) as e:
        print(json.dumps({'ok':False,'error':str(e)}));sys.exit(2)
