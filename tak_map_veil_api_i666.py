"""TAK Map i666 optional, server-side VEIL r50 Live SA synchronization.

Uses only the Python standard library (including an RFC6455 subset), so the
existing Raspberry Pi installer requires no new online Python dependencies.
Nodes must be explicitly paired; UDP-only nodes never trigger auth workflows.
No secret or bearer token is sent to browser APIs, exports, or status.
"""
from __future__ import annotations
import base64
import hashlib
import hmac
import http.client
import ipaddress
import json
import math
import os
from pathlib import Path
import random
import socket
import struct
import threading
import time
from urllib.parse import quote
from uuid import uuid4

from tak_map_veil_i665 import MAX_OBJECTS, _stamp, _clean, _endpoint, _resolved, probe, SERVICES
from tak_map_veil_identity_i668 import identity_envelope
from tak_map_veil_aprs_i672 import aprs_symbol

MAX_LIVE_SA = 3000
MAX_HTTP = 3_000_000
MAX_EVENT = 524288
MAX_WORKERS = 8

class AuthRequired(Exception):
    pass
class NodeUnavailable(Exception):
    pass
class ResyncRequired(Exception):
    pass


def _network(node):
    """Pin every API request to a freshly verified private-LAN IPv4 address."""
    host, port = _endpoint(node['host'], node.get('port',8080))
    if node.get('scheme','http') != 'http':
        raise ValueError('Only HTTP on a trusted LAN is supported until verified TLS is configured')
    ip = _resolved(host)[0]
    return ip,port


def _http(node,path,token=None,body=None,limit=65536):
    ip,port = _network(node)
    conn=http.client.HTTPConnection(ip,port,timeout=3.5)
    try:
        headers={'Accept':'application/json','Host':f'{ip}:{port}','Connection':'close'}
        if token:headers['Authorization']='Bearer '+token
        if body is not None:headers['Content-Type']='application/json'
        conn.request('POST' if body is not None else 'GET',path,
                     body=json.dumps(body,separators=(',',':')).encode() if body is not None else None,headers=headers)
        response=conn.getresponse()
        raw=response.read(limit+1)
        if len(raw)>limit:raise ValueError('VEIL response size limit exceeded')
        if response.status in (401,403):raise AuthRequired('VEIL credentials or session rejected')
        if not 200<=response.status<300:raise NodeUnavailable('VEIL API unavailable (HTTP '+str(response.status)+')')
        payload=json.loads(raw)
        return payload
    except (OSError,TimeoutError,ConnectionError,http.client.HTTPException) as exc:
        raise NodeUnavailable('VEIL API connection unavailable') from exc
    finally:conn.close()


class VeilWebSocket:
    """Small RFC6455 read-only JSON client: bounded handshake, frames, ping/pong.

    No third-party runtime dependency. Client->server control frames are masked.
    Subprotocols/extensions are not negotiated. In particular, no compression.
    """
    def __init__(self,node,token,since=None,boot_id=None):
        ip,port=_network(node)
        query=''
        if isinstance(since,int) and since>=0 and boot_id:
            query='?since='+str(since)+'&bootId='+quote(str(boot_id),safe='')
        path='/api/v1/events'+query
        key=base64.b64encode(os.urandom(16)).decode()
        sock=socket.create_connection((ip,port),timeout=4.0)
        self.sock=sock;self.pending=b'';self.closed=False
        try:
            req=(f'GET {path} HTTP/1.1\r\nHost: {ip}:{port}\r\nUpgrade: websocket\r\n'
                 f'Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n'
                 f'Authorization: Bearer {token}\r\n\r\n')
            sock.sendall(req.encode('ascii'))
            buf=b''
            while b'\r\n\r\n' not in buf and len(buf)<12288:
                part=sock.recv(2048)
                if not part:raise NodeUnavailable('WebSocket connection closed during handshake')
                buf+=part
            if b'\r\n\r\n' not in buf:raise NodeUnavailable('WebSocket response headers too long')
            raw,self.pending=buf.split(b'\r\n\r\n',1)
            lines=raw.decode('latin-1').split('\r\n');status=lines[0]
            if status.startswith('HTTP/1.1 401') or status.startswith('HTTP/1.1 403'):
                raise AuthRequired('VEIL WebSocket authorization rejected')
            if not status.startswith('HTTP/1.1 101'):
                raise NodeUnavailable('VEIL WebSocket upgrade rejected')
            h={a.lower().strip():b.strip() for line in lines[1:] if ':' in line for a,b in [line.split(':',1)]}
            accept=base64.b64encode(hashlib.sha1((key+'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest()).decode()
            if not hmac.compare_digest(h.get('sec-websocket-accept',''),accept):
                raise NodeUnavailable('VEIL WebSocket handshake invalid')
            sock.settimeout(1.2)
        except Exception:
            sock.close();self.closed=True;raise

    def _exact(self,n):
        while len(self.pending)<n:
            piece=self.sock.recv(min(32768,n-len(self.pending)))
            if not piece:raise NodeUnavailable('VEIL WebSocket closed')
            self.pending+=piece
        out,self.pending=self.pending[:n],self.pending[n:]
        return out

    def _send_control(self,opcode,payload=b''):
        if self.closed:return
        mask=os.urandom(4)
        payload=payload[:125]
        self.sock.sendall(bytes([0x80|opcode,0x80|len(payload)])+mask+
                          bytes(v^mask[i%4] for i,v in enumerate(payload)))

    def receive(self):
        """Return JSON event or None on idle timeout; never return unbounded data."""
        parts=[];total=0
        try:
            while True:
                first,second=self._exact(2)
                fin=bool(first&0x80);opcode=first&0x0f
                if second&0x80:raise NodeUnavailable('Invalid masked server WebSocket frame')
                length=second&0x7f
                if length==126:length=struct.unpack('!H',self._exact(2))[0]
                elif length==127:length=struct.unpack('!Q',self._exact(8))[0]
                if length>MAX_EVENT or total+length>MAX_EVENT:raise NodeUnavailable('VEIL event too large')
                payload=self._exact(length)
                if opcode==0x9:self._send_control(0xA,payload);continue
                if opcode==0xA:continue
                if opcode==0x8:raise NodeUnavailable('VEIL WebSocket connection closed')
                if opcode not in (0,1):raise NodeUnavailable('Unexpected VEIL WebSocket frame')
                parts.append(payload);total+=length
                if fin:
                    value=json.loads(b''.join(parts))
                    if not isinstance(value,dict):raise ValueError('Non-object VEIL event')
                    return value
        except socket.timeout:
            if parts:raise NodeUnavailable('Partial VEIL message timed out')
            return None

    def close(self):
        self.closed=True
        try:self.sock.close()
        except OSError:pass


def _canonical(source):
    value=_clean(source,32).lower().replace('-','_')
    if value.startswith('adsb'):return 'adsb'
    if value in ('remoteid','rid','drone','remote_id'):return 'remote_id'
    return value


def normalize_object(node_id,row):
    """VEIL r50 native Live SA row -> TAK Map i665 marker schema."""
    if not isinstance(row,dict):return None
    oid=_clean(row.get('objectId'),160)
    source=_clean(row.get('sourceService'),32)
    service=_canonical(source)
    if not oid or service not in SERVICES:return None
    position=row.get('position')
    if not isinstance(position,dict):return None
    try:
        lat=float(position.get('lat'));lon=float(position.get('lon'))
        if not math.isfinite(lat) or not math.isfinite(lon) or abs(lat)>90 or abs(lon)>180:return None
    except (ValueError,TypeError):return None
    now=time.time()
    when=_stamp(row.get('positionTimestamp')) or _stamp(row.get('timestamp')) or now
    if when>now+120 or when<now-86400:return None
    identity=row.get('identity') if isinstance(row.get('identity'),dict) else {}
    metadata=row.get('metadata') if isinstance(row.get('metadata'),dict) else {}
    track=row.get('track') if isinstance(row.get('track'),dict) else {}
    motion=row.get('motion') if isinstance(row.get('motion'),dict) else {}
    tak=row.get('tak') if isinstance(row.get('tak'),dict) else {}
    taktrack=tak.get('track') if isinstance(tak.get('track'),dict) else {}
    ttl=max(1,min(1800,int(row.get('ttlSeconds') or 45)))
    retention=max(0,min(1800,int(row.get('staleRetentionSeconds') or 0)))
    freshness=_clean(row.get('freshnessState') or 'LIVE',16).upper()
    title=_clean(identity.get('callsign') or identity.get('name') or identity.get('flight') or
                 identity.get('objectName') or metadata.get('name') or oid,120)
    enrich=(row.get('tak') or {}).get('enrichment') if isinstance(row.get('tak'),dict) else None
    if not isinstance(enrich,dict):enrich={}
    raw_enrich=enrich.copy()
    enrich={_clean(k,40):_clean(v,160) for k,v in list(enrich.items())[:16] if isinstance(v,(str,int,float))}
    # Retain explicit aircraft type metadata for original ADSBx type/designator matching.
    # Never infer an ICAO type from callsign or an unrelated CoT classification.
    if service=='adsb':
        for key in ('type_designator','icao_type','icaoType','aircraft_type_code',
                    'aircraftTypeCode','aircraft_type','aircraftType','type',
                    'model','type_description','typeDescription','category'):
            for value in (raw_enrich.get(key),enrich.get(key),metadata.get(key),identity.get(key),row.get(key)):
                if isinstance(value,(str,int,float)) and str(value).strip():
                    enrich[key]=_clean(value,160)
                    break
    # r50 identifies APRS objects by owner callsign + object name, as recorded in the
    # native APRS manager. Preserve that identity for safe same-object reconciliation.
    if service=='aprs' and row.get('objectType')=='aprs_object':
        identity=dict(identity)
        if identity.get('callsign') and identity.get('objectName'):
            identity.setdefault('objectOwner',identity['callsign'])
    safe_identity, canonical=identity_envelope(service,identity,metadata,oid)
    expiry=min(now+1800,when+ttl+retention)
    def first_number(*values):
        for value in values:
            if value is None or value=='' or isinstance(value,bool):continue
            try:
                n=float(value)
                if math.isfinite(n):return n
            except (TypeError,ValueError,OverflowError):pass
        return None
    course=first_number(motion.get('courseDeg'),taktrack.get('courseDeg'),track.get('courseDeg'),
                        track.get('course'),row.get('heading'),row.get('courseDeg'),row.get('trackDeg'))
    course=(course%360.0) if course is not None and abs(course)<=36000 else None
    speed=first_number(motion.get('speedMps'),taktrack.get('speedMps'),track.get('speed'),row.get('speedMps'))
    aprs=aprs_symbol(identity,metadata,row.get('objectType'),tak.get('aprs_symbol')) if service=='aprs' else {}
    if freshness=='STALE' and expiry<=now:return None
    return {'id':f'veil:{node_id}:{oid}','nodeId':node_id,'objectId':oid,'sourceService':source,'service':service,
            'lat':lat,'lon':lon,'hae':position.get('hae'),'type':_clean((row.get('tak') or {}).get('cotType') if isinstance(row.get('tak'),dict) else '',60),
            'title':title,'remarks':_clean(row.get('description') or '',1200),
            'heading':course,'speedMps':speed,
            'timestamp':when,'stale':expiry,'sequence':int(row.get('sequence') or 0),
            'freshness':freshness,'aprs':aprs,'enrichment':enrich,'transport':'api','identity':safe_identity,'canonicalKey':canonical}


class VeilApiSyncManager:
    def __init__(self,receiver):
        self.rx=receiver
        self.lock=threading.RLock()
        self.tokens={};self.credentials={};self.statuses={};self.workers={};self.event_cursors={};self.failed_credentials=set()
        self.stop_event=threading.Event();self.manager_thread=None
        self.secrets_file=Path(receiver.dir)/'veil_api_credentials_i666.json'
        self._load_secrets()
        # Previously installed i665 nodes are intentionally UDP-only until paired.
        with self.rx.lock:
            for node in self.rx.nodes.values():node['apiSubscribed']=bool(node.get('apiSubscribed',False))

    def _load_secrets(self):
        try:
            stat=self.secrets_file.stat()
            if stat.st_mode&0o077:raise ValueError('VEIL credentials file permissions must be 0600')
            data=json.loads(self.secrets_file.read_text())
            if isinstance(data,dict):self.credentials={str(k):v for k,v in data.items() if isinstance(v,dict)}
        except FileNotFoundError:pass
        except (ValueError,OSError):pass

    def _save_secrets(self):
        self.secrets_file.parent.mkdir(parents=True,exist_ok=True)
        temp=self.secrets_file.with_suffix('.tmp')
        with open(temp,'w',encoding='utf-8') as f:
            os.fchmod(f.fileno(),0o600)
            json.dump(self.credentials,f)
            f.flush();os.fsync(f.fileno())
        os.replace(temp,self.secrets_file)

    def _node(self,node_id):
        with self.rx.lock:
            node=self.rx.nodes.get(str(node_id))
            if not node:raise ValueError('VEIL node is not configured')
            return dict(node)

    def _enabled(self,node_id):
        with self.rx.lock:
            return bool(self.rx.config.get('enabled') and
                        self.rx.nodes.get(node_id,{}).get('apiSubscribed'))

    def _state(self,node_id,status,**kwargs):
        with self.lock:
            old=self.statuses.get(node_id,{})
            state=dict(old)
            previous=state.get('apiState')
            state.update(kwargs)
            state['apiState']=status
            if status=='login_required' and previous!='login_required':
                state['authGeneration']=int(old.get('authGeneration') or 0)+1
            if status!='login_required':state['authRequired']=False
            elif 'authRequired' not in kwargs:state['authRequired']=True
            self.statuses[node_id]=state

    def _verify(self,node):
        found=probe(node['host'],node.get('port',8080),node.get('scheme','http'))
        if found['nodeId']!=node['nodeId']:raise NodeUnavailable('VEIL node identity mismatch')
        return found

    def _login(self,node,username,password):
        if not username or not password:raise ValueError('Username and password are required')
        cid='tak-map-'+hashlib.sha256(node['nodeId'].encode()).hexdigest()[:24]
        result=_http(node,'/api/v1/admin/login',body={'username':username,'password':password,
            'clientId':cid,'clientName':'TAK Map','clientType':'api_client'})
        token=result.get('token') if isinstance(result,dict) else None
        if not result.get('authenticated') or not isinstance(token,str) or len(token)<16:
            raise AuthRequired('VEIL API login rejected')
        caps=_http(node,'/api/v1/capabilities',token=token)
        if caps.get('nodeId')!=node['nodeId']:
            raise NodeUnavailable('Authenticated VEIL node ID does not match configured identity')
        return token

    def pair(self,node_id,username,password,remember=False):
        node=self._node(node_id)
        with self.rx.lock:
            if not self.rx.config.get('enabled'):raise ValueError('Enable XTAK VEIL before connecting its API')
        self._verify(node)
        token=self._login(node,username,password)
        with self.rx.lock:
            if not self.rx.config.get('enabled') or node_id not in self.rx.nodes:
                raise ValueError('XTAK VEIL is disabled or node was removed')
            self.rx.nodes[node_id]['apiSubscribed']=True
            self.rx._save()
        with self.lock:
            self.tokens[node_id]=token
            self.failed_credentials.discard(node_id)
            if remember:self.credentials[node_id]={'username':username,'password':password}
            else:self.credentials.pop(node_id,None)
            self._save_secrets()
            self._state(node_id,'synchronizing',authRequired=False,apiError='',lastPair=time.time())
        return {'ok':True,'nodeId':node_id,'apiSubscribed':True,'remembered':bool(remember)}

    def unpair(self,node_id):
        self._node(node_id)
        with self.rx.lock:
            self.rx.nodes[node_id]['apiSubscribed']=False
            self.rx._save()
        with self.lock:
            self.tokens.pop(node_id,None);self.credentials.pop(node_id,None)
            self.event_cursors.pop(node_id,None);self.statuses.pop(node_id,None)
            self.failed_credentials.discard(node_id)
            self._save_secrets()
        return {'ok':True}

    def remove(self,node_id):
        with self.lock:
            self.tokens.pop(node_id,None);self.credentials.pop(node_id,None)
            self.event_cursors.pop(node_id,None);self.statuses.pop(node_id,None)
            self.failed_credentials.discard(node_id)
            self._save_secrets()

    def on_toggle(self):
        with self.rx.lock:enabled=bool(self.rx.config.get('enabled'))
        if not enabled:
            with self.lock:
                self.tokens.clear()
                self.event_cursors.clear()
                for k in self.statuses:self.statuses[k].update(apiState='disabled',authRequired=False)

    def start(self):
        if self.manager_thread and self.manager_thread.is_alive():return
        self.stop_event.clear()
        self.manager_thread=threading.Thread(target=self._supervisor,daemon=True,name='veil-api-supervisor-i666')
        self.manager_thread.start()

    def stop(self):
        self.stop_event.set()
        if self.manager_thread:self.manager_thread.join(timeout=3)

    def _supervisor(self):
        while not self.stop_event.is_set():
            with self.rx.lock:
                enabled=bool(self.rx.config.get('enabled'))
                subscribed=[id for id,n in self.rx.nodes.items() if n.get('apiSubscribed')][:MAX_WORKERS]
            if enabled:
                with self.lock:
                    for nid in subscribed:
                        prev=self.workers.get(nid)
                        if prev and prev.is_alive():continue
                        t=threading.Thread(target=self._worker,args=(nid,),daemon=True,name='veil-api-'+nid[:14])
                        self.workers[nid]=t;t.start()
            self.stop_event.wait(1.5)

    def _auth_check(self,node,token):
        try:
            caps=_http(node,'/api/v1/capabilities',token=token)
            if caps.get('nodeId')!=node['nodeId']:raise NodeUnavailable('VEIL identity mismatch')
            return caps
        except AuthRequired:
            # Confirm reachable and exact advertised identity BEFORE making auth required.
            self._verify(node)
            raise

    def _ensure_token(self,node):
        node_id=node['nodeId']
        token=self.tokens.get(node_id)
        if token:
            try:return token,self._auth_check(node,token)
            except AuthRequired:pass
        creds=self.credentials.get(node_id)
        if creds and node_id not in self.failed_credentials:
            try:
                token=self._login(node,creds.get('username'),creds.get('password'))
                with self.lock:self.tokens[node_id]=token
                return token,self._auth_check(node,token)
            except AuthRequired:self.failed_credentials.add(node_id)
        # A subscribed node with missing/expired token must return a *confirmed*
        # 401 from an actual, reachable and identity-matched protected VEIL API.
        self._verify(node)
        try:
            self._auth_check(node,None)
        except AuthRequired:
            self._state(node_id,'login_required',authRequired=True,apiError='API reauthentication required')
            raise
        # Securely fail if a protected endpoint unexpectedly permits no auth.
        self._state(node_id,'api_error',apiError='VEIL API unexpectedly accepted an unauthenticated request')
        raise NodeUnavailable('Unauthenticated VEIL API is not supported')

    def _snapshot(self,node,token):
        rows=_http(node,'/api/v1/live-sa',token=token,limit=MAX_HTTP)
        if not isinstance(rows,list) or len(rows)>MAX_LIVE_SA:
            raise ValueError('Invalid or oversized VEIL Live SA snapshot')
        return rows

    def _apply_upsert(self,node_id,row,transport='api_event'):
        obj=normalize_object(node_id,row)
        if not obj:return False
        key=(node_id,obj['objectId'])
        obj['transport']=transport
        with self.rx.lock:
            if not self._enabled(node_id):return False
            old=self.rx.objects.get(key)
            # Timestamp is authoritative across CoT and REST/WebSocket. On ties
            # the API is preferred to a cached UDP position.
            if old and old['timestamp']>obj['timestamp']+0.001:return False
            if old and abs(old['timestamp']-obj['timestamp'])<=0.001:
                if old.get('transport','udp')!='udp' and old.get('sequence',0)>=obj.get('sequence',0):return False
            self.rx.objects[key]=obj
            if len(self.rx.objects)>MAX_OBJECTS:
                oldest=min(self.rx.objects,key=lambda k:self.rx.objects[k]['timestamp'])
                self.rx.objects.pop(oldest,None)
        return True

    def _expire(self,node_id,object_id):
        key=(node_id,_clean(object_id,160))
        with self.rx.lock:
            old=self.rx.objects.get(key)
            if old and old.get('transport')!='udp':self.rx.objects.pop(key,None)

    def _apply_event(self,node_id,event):
        if not isinstance(event,dict) or event.get('nodeId')!=node_id:return
        if event.get('type')!='live_sa':return
        action=event.get('action');payload=event.get('payload')
        if action=='update' and isinstance(payload,dict):self._apply_upsert(node_id,payload)
        elif action=='expire' and isinstance(payload,dict):self._expire(node_id,payload.get('objectId'))

    def _apply_envelope(self,node_id,event):
        if event.get('type')=='fault' and event.get('action')=='resync_required':raise ResyncRequired('VEIL replay requires a fresh snapshot')
        if event.get('stream')!='events':return
        if event.get('nodeId')!=node_id:raise NodeUnavailable('VEIL WebSocket event identity mismatch')
        boot=event.get('bootId');seq=event.get('sequence')
        if not isinstance(boot,str) or not isinstance(seq,int) or seq<1:return
        previous=self.event_cursors.get(node_id)
        if previous and previous[0]!=boot:raise ResyncRequired('VEIL restarted')
        if previous and seq<=previous[1]:return
        if previous and seq>previous[1]+1:raise ResyncRequired('VEIL event sequence gap')
        self._apply_event(node_id,event)
        self.event_cursors[node_id]=(boot,seq)
        if event.get('type')=='live_sa':self._state(node_id,'synced',lastApiUpdate=time.time())

    def _synchronize(self,node,token,caps):
        nid=node['nodeId']
        prior=self.event_cursors.get(nid)
        # A restart has no in-memory objects or cursor: always get a snapshot.
        cursor=prior if prior and prior[0]==caps.get('bootId') else None
        ws=VeilWebSocket(node,token,*cursor) if cursor else VeilWebSocket(node,token)
        try:
            if cursor is None:
                # Subscribe *before* fetching the snapshot, buffering concurrent
                # envelopes in the socket; then drain them after snapshot commit.
                rows=self._snapshot(node,token)
                if not self._enabled(nid):return
                snapshot_ids=set()
                for row in rows:
                    if isinstance(row,dict) and row.get('objectId'):snapshot_ids.add(str(row['objectId']))
                    self._apply_upsert(nid,row,'api_snapshot')
                with self.rx.lock:
                    for key,obj in list(self.rx.objects.items()):
                        if key[0]==nid and obj.get('transport') in ('api_snapshot','api_event') and key[1] not in snapshot_ids:
                            self.rx.objects.pop(key,None)
                self.event_cursors.pop(nid,None)
                self._state(nid,'synced',lastSnapshot=time.time(),apiBootId=caps.get('bootId'),apiError='')
            else:self._state(nid,'synced',apiError='')
            last_heartbeat=time.monotonic()
            while self._enabled(nid) and not self.stop_event.is_set():
                event=ws.receive()
                if event is not None:self._apply_envelope(nid,event)
                if time.monotonic()-last_heartbeat>45:
                    self._auth_check(node,token)
                    last_heartbeat=time.monotonic()
        finally:ws.close()

    def _worker(self,node_id):
        backoff=1.0
        while self._enabled(node_id) and not self.stop_event.is_set():
            reachable=False
            try:
                node=self._node(node_id)
                with self.lock:
                    prior_state=self.statuses.get(node_id,{}).get('apiState')
                if prior_state!='login_required':self._state(node_id,'reconnecting',apiError='')
                self._verify(node)
                reachable=True
                token,caps=self._ensure_token(node)
                if not self._enabled(node_id):break
                self._state(node_id,'synchronizing',apiError='',authRequired=False)
                self._synchronize(node,token,caps)
                backoff=1.0
            except AuthRequired:
                # _ensure_token confirmed reachability/auth; a later WS auth failure
                # must be rechecked on the next loop, not treated as a popup.
                with self.lock:
                    if self.statuses.get(node_id,{}).get('apiState')!='login_required':
                        self.tokens.pop(node_id,None)
                backoff=min(30.,max(2.,backoff*1.5))
            except ResyncRequired:
                self.event_cursors.pop(node_id,None)
                self._state(node_id,'resynchronizing',apiError='')
                backoff=0.5
            except (NodeUnavailable,OSError,TimeoutError,socket.gaierror):
                if self._enabled(node_id):
                    self._state(node_id,'reconnecting' if reachable else 'offline',
                        authRequired=False,apiError='VEIL connection interrupted' if reachable else 'VEIL API unreachable')
                backoff=min(30.,backoff*1.8)
            except (ValueError,TypeError,KeyError,json.JSONDecodeError):
                if self._enabled(node_id):self._state(node_id,'api_error',authRequired=False,apiError='Invalid or incompatible VEIL API response')
                backoff=min(30.,backoff*2)
            self.stop_event.wait(min(30.,backoff)+random.uniform(0,.25))

    def status(self):
        with self.rx.lock:
            enabled=bool(self.rx.config.get('enabled'))
            nodes={k:bool(n.get('apiSubscribed',False)) for k,n in self.rx.nodes.items()}
        with self.lock:
            return {nid:{'apiSubscribed':sub,'apiState':('disabled' if not enabled else
                (self.statuses.get(nid,{}).get('apiState','reconnecting') if sub else 'udp_only')),
                'apiAuthGeneration':int(self.statuses.get(nid,{}).get('authGeneration') or 0),
                'apiAuthRequired':bool(enabled and sub and self.statuses.get(nid,{}).get('apiState')=='login_required' and self.statuses.get(nid,{}).get('authRequired')),
                'apiLastSync':self.statuses.get(nid,{}).get('lastSnapshot'),
                'apiLastUpdate':self.statuses.get(nid,{}).get('lastApiUpdate'),
                'apiBootId':self.statuses.get(nid,{}).get('apiBootId'),
                'apiError':self.statuses.get(nid,{}).get('apiError',''),
                'apiCredentialsRemembered':nid in self.credentials}
                for nid,sub in nodes.items()}

    def prompt_check(self,node_id,generation):
        """Re-verify all four gates immediately before opening an auto-modal."""
        with self.rx.lock:
            if not self.rx.config.get('enabled'):return {'ok':True,'show':False}
            node=self.rx.nodes.get(node_id)
            if not node or not node.get('apiSubscribed'):return {'ok':True,'show':False}
            node=dict(node)
        with self.lock:
            state=dict(self.statuses.get(node_id,{}))
            if state.get('apiState')!='login_required' or int(state.get('authGeneration') or 0)!=int(generation):
                return {'ok':True,'show':False}
        try:
            self._verify(node)
            token=self.tokens.get(node_id)
            try:
                self._auth_check(node,token)
                return {'ok':True,'show':False}
            except AuthRequired:
                pass
            if node_id in self.credentials:
                try:
                    self._ensure_token(node)
                    return {'ok':True,'show':False}
                except AuthRequired:pass
            return {'ok':True,'show':bool(self._enabled(node_id))}
        except (NodeUnavailable,ValueError,OSError):return {'ok':True,'show':False}
