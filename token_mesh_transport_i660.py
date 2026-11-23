"""TAK Map Token Mesh server-side XMS2/XTP3 participant.

Protocol compatibility target: Android XTP3 v3. No browser-owned sockets,
no OpenTAKServer or TAK Gateway publication, no peer key disclosure.
"""
import base64
import hashlib
import json
import logging
import os
import socket
import subprocess
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from token_mesh_wire_i660 import (DATAGRAM_PORT,DIRECT_START,MAX_FRAME,
    Channel,client_handshake,server_handshake,datagram_encrypt,datagram_decrypt)
from token_mesh_i660 import MAX_PAYLOAD,head_rank

log=logging.getLogger('tak-map.token-mesh')
MAX_HELLO=1200
MAX_CHUNK=48*1024
MAX_PEERS=128


class MeshTransport:
    def __init__(self,store):
        self.store=store
        self.running=False
        self.thread=None
        self.udp=None
        self.tcp=None
        self.port=0
        self.instance=str(uuid.uuid4())
        self.peers={}
        self.sessions={}
        self.lock=threading.RLock()
        self.last_error=''
        self.last_success=None
        self.executor=ThreadPoolExecutor(max_workers=8,thread_name_prefix='takmesh')
        self._next_retry={}
        self._group_id=None
        self._known_addresses=set()
        self._active_sessions=set()
        targets=os.environ.get('TAK_MAP_MESH_PEER_TARGETS','')
        for token in targets.split(','):
            token=token.strip()
            try:
                ip=socket.inet_aton(token)
                if not token.startswith('127.') and not token.startswith('0.'):
                    self._known_addresses.add(token)
            except OSError:
                pass

    def start(self):
        if self.running:return
        self.running=True
        self.thread=threading.Thread(target=self._loop,name='tak-map-token-mesh-i660',daemon=True)
        self.thread.start()

    def stop(self):
        self.running=False
        self._close()
        self.executor.shutdown(wait=False,cancel_futures=True)

    def _close(self):
        with self.lock:
            sock=self.udp;self.udp=None
            srv=self.tcp;self.tcp=None;self.port=0;self._group_id=None
            self.peers.clear();self.sessions.clear();self._active_sessions.clear()
        for x in (sock,srv):
            if x:
                try:x.close()
                except OSError:pass

    def _bind(self,group):
        if not group:return
        with self.lock:
            if self._group_id==group['groupId'] and self.udp and self.tcp:return
        self._close()
        udp=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        tcp=None
        try:
            udp.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            udp.setsockopt(socket.SOL_SOCKET,socket.SO_BROADCAST,1)
            udp.bind(('',DATAGRAM_PORT));udp.settimeout(1.0)
            for port in range(DIRECT_START,DIRECT_START+32):
                trial=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                trial.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
                try:
                    trial.bind(('',port));trial.listen(16);trial.settimeout(1.0)
                    tcp=trial;break
                except OSError:
                    trial.close()
            if not tcp:raise OSError('No available direct TCP listener port in 42421–42452')
            with self.lock:
                self.udp=udp;self.tcp=tcp;self.port=tcp.getsockname()[1];self._group_id=group['groupId'];self.last_error=''
            threading.Thread(target=self._receive_loop,args=(udp,group['groupId']),daemon=True,name='takmesh-udp').start()
            threading.Thread(target=self._accept_loop,args=(tcp,group['groupId']),daemon=True,name='takmesh-tcp').start()
        except Exception as exc:
            self.last_error='Listener bind failed: '+str(exc)[:180]
            udp.close()
            if tcp:tcp.close()

    def _loop(self):
        while self.running:
            try:
                group=self.store.group() if self.store.mesh_enabled() else None
                if not group:
                    if self.udp or self.tcp:self._close()
                else:
                    self._bind(group)
                    if self.udp and self.tcp:
                        self._broadcast(group)
                        self._try_sync(group)
            except Exception as exc:
                self.last_error='Mesh control: '+type(exc).__name__+' '+str(exc)[:140]
            for _ in range(35):
                if not self.running:break
                time.sleep(.2)

    @staticmethod
    def _broadcast_addresses():
        result=set()
        try:
            output=subprocess.check_output(['ip','-j','-4','address','show'],timeout=2)
            for iface in json.loads(output):
                if iface.get('operstate')=='DOWN':continue
                for addr in iface.get('addr_info',[]):
                    broad=addr.get('broadcast')
                    if broad:result.add(broad)
        except (OSError,ValueError,subprocess.SubprocessError):
            pass
        if not result:result.add('255.255.255.255')
        return result

    def _broadcast(self,group):
        key=base64.b64decode(group['key'],validate=True)
        hello={'type':'TOKEN_HELLO','v':3,'groupId':group['groupId'],
               'origin':self.store.device_uid(),'callsign':os.environ.get('TAK_MAP_MESH_CALLSIGN','TAK Map')[:80],
               'team':'','directPeerPort':self.port,'instanceId':self.instance,'sentAt':int(time.time()*1000)}
        packet=datagram_encrypt(group['groupId'],key,json.dumps(hello,separators=(',',':')).encode())
        if len(packet)>1200:raise ValueError('Hello exceeds XMS2 safe datagram')
        targets=self._broadcast_addresses() | set(self._known_addresses)
        with self.lock:
            targets.update(p['address'] for p in self.peers.values() if p.get('address'))
            sock=self.udp
        if not sock:return
        for address in list(targets)[:128]:
            try:sock.sendto(packet,(address,DATAGRAM_PORT))
            except OSError:pass

    def _receive_loop(self,sock,gid):
        while self.running and sock==self.udp and self._group_id==gid:
            try:
                packet,source=sock.recvfrom(MAX_HELLO+1)
                group=self.store.group() if self.store.mesh_enabled() else None
                if not group or group['groupId']!=gid:break
                data=datagram_decrypt(packet,gid,base64.b64decode(group['key'],validate=True))
                if len(data)>4096:continue
                hello=json.loads(data.decode('utf-8'))
                if hello.get('type')!='TOKEN_HELLO' or hello.get('v')!=3 or hello.get('groupId')!=gid:continue
                uid=hello.get('origin')
                if not isinstance(uid,str) or not 1<=len(uid)<=256 or uid==self.store.device_uid():continue
                port=hello.get('directPeerPort')
                if type(port) is not int or not 1<=port<=65535:continue
                with self.lock:
                    if len(self.peers)>=MAX_PEERS and uid not in self.peers:continue
                    self.peers[uid]={'uid':uid,'callsign':str(hello.get('callsign',''))[:80],
                        'address':source[0],'port':port,'instance':str(hello.get('instanceId',''))[:80],
                        'last_seen':time.monotonic(),'authenticated_until':self.peers.get(uid,{}).get('authenticated_until',0)}
            except socket.timeout:pass
            except (ValueError,UnicodeError,KeyError,OSError):pass

    def _accept_loop(self,server,gid):
        while self.running and server==self.tcp and self._group_id==gid:
            try:
                conn,addr=server.accept()
                conn.settimeout(20)
                self.executor.submit(self._server_session,conn,addr,gid)
            except socket.timeout:pass
            except (OSError,RuntimeError):break

    def _try_sync(self,group):
        now=time.monotonic()
        with self.lock:
            for uid,peer in list(self.peers.items()):
                if now-peer['last_seen']>30:self.peers.pop(uid,None)
            targets=list(self.peers.values())
        own=self.store.device_uid()
        for peer in targets:
            if not self.store.mesh_enabled():return
            if own>=peer['uid']:continue
            for binding in self.store.mission_list():
                if not binding['enabled']:continue
                key=(peer['uid'],binding['mission'])
                with self.lock:
                    if key in self._active_sessions or now<self._next_retry.get(key,0):continue
                    self._active_sessions.add(key)
                    self._next_retry[key]=now+7
                self.executor.submit(self._client_session,peer,group,binding['mission'],key)

    def _auth(self,uid):
        with self.lock:
            if uid in self.peers:
                self.peers[uid]['authenticated_until']=time.monotonic()+45

    def _client_session(self,peer,group,mission,key):
        try:
            if not self.store.mesh_enabled():return
            with socket.create_connection((peer['address'],peer['port']),timeout=5) as sock:
                sock.settimeout(20)
                ch=client_handshake(sock,base64.b64decode(group['key']),group['groupId'],self.store.device_uid(),peer['uid'])
                ch.send({'type':'TOKEN_PING','groupId':group['groupId'],'uid':self.store.device_uid()})
                pong=ch.recv()
                if pong.get('type')!='TOKEN_PONG' or pong.get('uid')!=peer['uid']:
                    raise ValueError('Invalid authenticated TOKEN_PONG')
                self._auth(peer['uid'])
                ch.send({'type':'MISSION_OPEN','missionId':mission})
                response=ch.recv()
                if response.get('type')=='MISSION_REJECT':
                    with self.lock:self._next_retry[key]=time.monotonic()+(60 if response.get('reason')=='unavailable' else 3)
                    return
                if response.get('type')!='MISSION_ACCEPT' or response.get('missionId')!=mission:
                    raise ValueError('MISSION_ACCEPT invalid')
                local=self.store.summary(mission)
                ch.send(local)
                remote=ch.recv();self._validate_summary(remote,mission)
                count_sent=self._send_ops(ch,mission,remote,local['highWater'])
                ch.send({'type':'CLIENT_DONE'})
                count_recv=self._receive_ops(ch,mission,remote,'SERVER_DONE')
                ch.send({'type':'CLIENT_ACK_DONE'})
                self._success(peer['uid'],mission,count_sent,count_recv)
        except Exception as exc:
            self._failure(key,exc)
        finally:
            with self.lock:self._active_sessions.discard(key)

    def _server_session(self,sock,addr,gid):
        uid=None;mission=None;key=None
        try:
            with sock:
                group=self.store.group() if self.store.mesh_enabled() else None
                if not group or group['groupId']!=gid:return
                uid,ch=server_handshake(sock,base64.b64decode(group['key']),gid,self.store.device_uid())
                ping=ch.recv()
                if ping.get('type')!='TOKEN_PING' or ping.get('groupId')!=gid or ping.get('uid')!=uid:
                    raise ValueError('Authenticated ping mismatch')
                ch.send({'type':'TOKEN_PONG','groupId':gid,'uid':self.store.device_uid()})
                self._auth(uid)
                hello=ch.recv()
                if hello.get('type')!='MISSION_OPEN':return
                mission=hello.get('missionId')
                if not self.store.is_mission_enabled(mission):
                    ch.send({'type':'MISSION_REJECT','missionId':mission,'reason':'unavailable'});return
                key=(uid,mission)
                with self.lock:
                    if key in self._active_sessions:
                        ch.send({'type':'MISSION_REJECT','missionId':mission,'reason':'busy','retryAfterMs':1500});return
                    self._active_sessions.add(key)
                ch.send({'type':'MISSION_ACCEPT','missionId':mission})
                remote=ch.recv();self._validate_summary(remote,mission)
                local=self.store.summary(mission)
                ch.send(local)
                nrecv=self._receive_ops(ch,mission,remote,'CLIENT_DONE')
                nsent=self._send_ops(ch,mission,remote,local['highWater'])
                ch.send({'type':'SERVER_DONE'})
                ack=ch.recv()
                if ack.get('type')!='CLIENT_ACK_DONE':raise ValueError('Missing CLIENT_ACK_DONE')
                self._success(uid,mission,nsent,nrecv)
        except Exception as exc:
            self.last_error='Mesh session failed ('+type(exc).__name__+'): '+str(exc)[:160]
        finally:
            if key:
                with self.lock:self._active_sessions.discard(key)

    def _validate_summary(self,summary,mission):
        if summary.get('type')!='SUMMARY' or not isinstance(summary.get('highWater'),dict) or not isinstance(summary.get('heads'),list):
            raise ValueError('Malformed SUMMARY')
        if len(summary['highWater'])>2000 or len(summary['heads'])>5000:
            raise ValueError('Oversize SUMMARY')
        for h in summary['heads']:
            if not isinstance(h,dict) or h.get('missionId')!=mission:
                raise ValueError('Foreign Mission head')

    def _send_ops(self,ch,mission,summary,checkpoint_high):
        operations=self.store.operations_for_peer(mission,summary)
        sent=0
        for op in operations:
            if not self.store.mesh_enabled():raise ValueError('Mesh disabled during send')
            data=bytes(op['payload'])
            meta=json.loads(op['metadata'])
            meta['missionName']=meta.get('missionName','')
            meta['serverIdentity']=meta.get('serverIdentity','')
            meta['baseFp']=meta.get('baseFp','')
            meta['resultFp']=meta.get('resultFp','')
            meta['payload']=''
            ch.send({'type':'OP_META','operation':meta})
            for index,start in enumerate(range(0,len(data),MAX_CHUNK)):
                if index % 8 == 0 and not self.store.mesh_enabled():raise ValueError('Mesh disabled during send')
                ch.send({'type':'OP_CHUNK','index':index,'data':base64.b64encode(data[start:start+MAX_CHUNK]).decode('ascii')})
            ch.send({'type':'OP_END','id':op['op_id'],'hash':op['payload_hash'],'size':len(data)})
            sent+=1
        ch.send({'type':'CHECKPOINT','highWater':checkpoint_high})
        return sent

    def _receive_ops(self,ch,mission,summary,done):
        received=0
        pending=None;chunks=[];size=0;index=0
        checkpoint=None
        while True:
            if not self.store.mesh_enabled():raise ValueError('Mesh disabled during receive')
            frame=ch.recv()
            typ=frame.get('type')
            if typ==done:
                if pending is not None:raise ValueError('Premature mission phase completion')
                if checkpoint:
                    self.store.adopt_checkpoint(mission,checkpoint,summary)
                return received
            if typ=='CHECKPOINT':
                if pending is not None or checkpoint is not None:raise ValueError('Invalid checkpoint placement')
                checkpoint=frame.get('highWater')
                if not isinstance(checkpoint,dict):raise ValueError('Malformed checkpoint')
                continue
            if typ=='OP_META':
                if pending is not None or checkpoint is not None:raise ValueError('Truncated operation')
                pending=frame.get('operation')
                if not isinstance(pending,dict) or pending.get('missionId')!=mission:
                    raise ValueError('Foreign Mission operation')
                if type(pending.get('payloadSize')) is not int or not 0<=pending['payloadSize']<=MAX_PAYLOAD:
                    raise ValueError('Invalid advertised payload length')
                chunks=[];size=0;index=0
                continue
            if typ=='OP_CHUNK':
                if pending is None or frame.get('index')!=index or not isinstance(frame.get('data'),str):
                    raise ValueError('Invalid OP_CHUNK order')
                chunk=base64.b64decode(frame['data'],validate=True)
                if len(chunk)>MAX_CHUNK or size+len(chunk)>pending['payloadSize']:
                    raise ValueError('Invalid OP_CHUNK size')
                chunks.append(chunk);size+=len(chunk);index+=1
                continue
            if typ=='OP_END':
                if pending is None:raise ValueError('Unexpected OP_END')
                if frame.get('id')!=pending.get('opId') or frame.get('hash')!=pending.get('payloadHash') or frame.get('size')!=pending.get('payloadSize'):
                    raise ValueError('Inconsistent OP_END metadata')
                if size!=pending['payloadSize']:raise ValueError('Truncated operation payload')
                data=b''.join(chunks)
                result=self.store.receive(pending,data)
                if not result['duplicate']:received+=1
                pending=None;chunks=[];size=0;index=0
                continue
            raise ValueError('Unexpected Token Mesh record '+str(typ)[:60])

    def _success(self,uid,mission,sent,received):
        self.last_success={'peer':uid,'mission':mission,'sent':sent,'received':received,'time':int(time.time())}
        self.last_error=''
        self._auth(uid)

    def _failure(self,key,exc):
        with self.lock:self._next_retry[key]=time.monotonic()+15
        self.last_error='Mesh '+type(exc).__name__+': '+str(exc)[:160]

    def status(self):
        now=time.monotonic()
        with self.lock:
            peers=[{'uid':p['uid'],'callsign':p['callsign'],'address':p['address'],'port':p['port'],
                'authenticated':p['authenticated_until']>now,'seenSecondsAgo':max(0,round(now-p['last_seen']))}
                for p in self.peers.values() if now-p['last_seen']<30]
        return {'transportReady':bool(self.tcp and self.udp and self.store.group() and self.store.mesh_enabled()),'listenerPort':self.port,
            'visiblePeers':len(peers),'authenticatedPeers':sum(p['authenticated'] for p in peers),
            'peers':peers,'lastSuccessfulSync':self.last_success,'transportError':self.last_error}
