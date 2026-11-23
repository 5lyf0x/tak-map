"""TAK Map VEIL Phase 1: persistent LAN node management and bounded live CoT UDP receiver.

The UDP transport is unauthenticated. Sender IP and VEIL node ID are checked against
explicitly configured nodes; never treat these as cryptographic authentication.
"""
from __future__ import annotations
import csv
import datetime as dt
import io
import ipaddress
import json
import math
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import threading
import time
from urllib.request import Request, build_opener, ProxyHandler
from xml.etree import ElementTree as ET
from tak_map_veil_identity_i668 import identity_envelope
from tak_map_veil_aprs_i672 import aprs_symbol

MAX_OBJECTS = 3000
MAX_PACKET = 32768
MAX_BODY = 16384
DEFAULT_PORT = 6970
SERVICES = {'adsb', 'ais', 'aprs', 'remote_id'}

def _stamp(value):
    if not value: return None
    try:
        val=str(value).strip()
        if re.fullmatch(r'\d{10,16}(?:\.\d+)?',val):
            n=float(val); return n/1000.0 if n > 10**11 else n
        return dt.datetime.fromisoformat(val.replace('Z','+00:00')).timestamp()
    except (OverflowError,ValueError,TypeError):return None

def _clean(value, maximum=180):
    return ''.join(c for c in str(value or '') if c.isprintable())[:maximum].strip()

def _endpoint(host, port):
    host=_clean(host,160).strip('[]').rstrip('.')
    if not re.fullmatch(r'[a-zA-Z0-9.-]+',host): raise ValueError('Invalid hostname / address')
    try:
        ip=ipaddress.ip_address(host)
        if ip.version!=4 or not ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_unspecified:
            raise ValueError('VEIL node must use a private LAN IPv4 address')
    except ValueError as e:
        if 'VEIL node must' in str(e): raise
        if not host.endswith('.local') or len(host)>120: raise ValueError('Use a private IPv4 address or .local hostname')
    port=int(port)
    if not 1<=port<=65535:raise ValueError('Invalid node port')
    return host,port

def _resolved(host):
    ips=set()
    for entry in socket.getaddrinfo(host,None,socket.AF_INET,socket.SOCK_STREAM):
        ip=entry[4][0]
        addr=ipaddress.ip_address(ip)
        if not addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_multicast or addr.is_unspecified: raise ValueError('Node hostname resolves outside private LAN')
        ips.add(ip)
    if not ips:raise ValueError('Node has no private IPv4 address')
    return sorted(ips)

def probe(host,port=8080,scheme='http'):
    host,port=_endpoint(host,port)
    scheme=str(scheme or 'http').lower()
    if scheme!='http': raise ValueError('HTTPS nodes require a separately configured trusted certificate; plain HTTP discovery only in Phase 1')
    ips=_resolved(host)
    # Resolve hostname ourselves to guard DNS rebinding, use concrete verified IP.
    opener=build_opener(ProxyHandler({}))
    last=None
    for ip in ips:
        try:
            with opener.open(Request(f'http://{ip}:{port}/api/v1/discovery',headers={'Accept':'application/json'}),timeout=2.0) as res:
                body=res.read(MAX_BODY+1)
                if len(body)>MAX_BODY:raise ValueError('Node discovery response too large')
                data=json.loads(body)
                if not isinstance(data,dict) or not data.get('nodeId'):raise ValueError('Not a VEIL discovery document')
                return {'nodeId':_clean(data['nodeId'],120),'name':_clean(data.get('displayName') or data.get('name') or 'VEIL node',80),
                        'host':ip,'port':port,'scheme':'http','nodeVersion':_clean(data.get('nodeVersion'),40),
                        'services':[_clean(x,32) for x in (data.get('activeServices') or []) if isinstance(x,str)][:12],
                        'authRequired':bool(data.get('authRequired',True)),'verified':True}
        except (OSError,ValueError,TypeError,json.JSONDecodeError) as e:last=str(e)
    raise ValueError('Discovery probe failed: '+_clean(last,140))

def discover():
    if not shutil.which('avahi-browse'):return {'ok':False,'error':'avahi-browse unavailable; install avahi-utils or add nodes manually','nodes':[]}
    try:
        proc=subprocess.run(['avahi-browse','-rtp','_xtak-sensor._tcp'],text=True,capture_output=True,timeout=5,check=False)
        rows=list(csv.reader(io.StringIO(proc.stdout or ''),delimiter=';',escapechar='\\'))
    except (OSError,subprocess.TimeoutExpired):return {'ok':False,'error':'LAN mDNS scan timed out','nodes':[]}
    results={}; fail=0
    for row in rows[:150]:
        if len(row)<9 or row[0]!='=' or row[4]!='_xtak-sensor._tcp':continue
        try:
            node=probe(row[7],int(row[8]))
            results[node['nodeId']]=node
        except (ValueError,OSError):fail+=1
        if len(results)>=40:break
    return {'ok':True,'nodes':sorted(results.values(),key=lambda n:n['name'].lower()),'unverified':fail}

class VeilReceiver:
    def __init__(self, directory):
        self.dir=Path(directory);self.file=self.dir/'veil_nodes_i665.json'
        self.lock=threading.RLock();self.thread=None;self.stopping=threading.Event();self.sock=None
        self.nodes={};self.objects={};self.last_error='';self.packets=0;self.rejected=0
        self.config={'enabled':False,'port':DEFAULT_PORT,'visible':True,'showNodeMarkers':False,'crossSourceDedup':False,'mergeVeilDuplicates':True,'autoReconnect':True,
                     'services':{'adsb':True,'ais':True,'aprs':True,'remote_id':True}}
        self._load()
    def _load(self):
        try:
            data=json.loads(self.file.read_text())
            if isinstance(data.get('nodes'),list):self.nodes={n['nodeId']:n for n in data['nodes'] if isinstance(n,dict) and n.get('nodeId')}
            if isinstance(data.get('config'),dict):self.config.update({k:v for k,v in data['config'].items() if k in self.config})
            self.config['port']=int(self.config['port'])
        except (OSError,ValueError,TypeError):pass
    def _save(self):
        self.dir.mkdir(parents=True,exist_ok=True)
        tmp=self.file.with_suffix('.tmp')
        with open(tmp,'w',encoding='utf-8') as f:
            os.fchmod(f.fileno(),0o600)
            json.dump({'schema':1,'config':self.config,'nodes':list(self.nodes.values())},f,sort_keys=True,indent=2)
            f.flush();os.fsync(f.fileno())
        os.replace(tmp,self.file)
    def settings(self,patch):
        with self.lock:
            if 'enabled' in patch:self.config['enabled']=bool(patch['enabled'])
            if 'visible' in patch:self.config['visible']=bool(patch['visible'])
            if 'showNodeMarkers' in patch:self.config['showNodeMarkers']=bool(patch['showNodeMarkers'])
            if 'autoReconnect' in patch:self.config['autoReconnect']=bool(patch['autoReconnect'])
            if 'crossSourceDedup' in patch:self.config['crossSourceDedup']=bool(patch['crossSourceDedup'])
            if 'mergeVeilDuplicates' in patch:self.config['mergeVeilDuplicates']=bool(patch['mergeVeilDuplicates'])
            if 'port' in patch:
                port=int(patch['port'])
                if not 1024<=port<=65535:raise ValueError('UDP port must be 1024–65535')
                self.config['port']=port
            if isinstance(patch.get('services'),dict):
                for key in SERVICES:
                    if key in patch['services']:self.config['services'][key]=bool(patch['services'][key])
            self._save()
        self._close_socket()
        return self.status()
    def add(self,items):
        if not isinstance(items,list) or len(items)>30:raise ValueError('Select 1–30 nodes')
        verified=[]
        for item in items:
            if not isinstance(item,dict):raise ValueError('Invalid node')
            p=probe(item.get('host',''),item.get('port',8080),item.get('scheme','http'))
            if item.get('nodeId') and str(item['nodeId'])!=p['nodeId']:raise ValueError('Node identity changed during verification')
            if item.get('name'):p['name']=_clean(item['name'],80)
            verified.append(p)
        with self.lock:
            for node in verified:
                existing=self.nodes.get(node['nodeId']) or {}
                self.nodes[node['nodeId']]={**existing,**node,'addedAt':existing.get('addedAt') or time.time()}
            if len(self.nodes)>40:raise ValueError('Maximum 40 nodes')
            self._save()
        return {'ok':True,'added':len(verified),'nodes':self.status()['nodes']}
    def remove(self,node_id):
        with self.lock:
            self.nodes.pop(str(node_id),None)
            self.objects={k:v for k,v in self.objects.items() if v['nodeId']!=node_id}
            self._save()
        return self.status()
    def _close_socket(self):
        sock=self.sock;self.sock=None
        if sock:
            try:sock.close()
            except OSError:pass
    def start(self):
        if self.thread and self.thread.is_alive():return
        self.stopping.clear()
        self.thread=threading.Thread(target=self._run,daemon=True,name='tak-map-veil-udp-i665');self.thread.start()
    def stop(self):
        self.stopping.set();self._close_socket()
        if self.thread:self.thread.join(timeout=2)
    def _run(self):
        bound_port=None
        while not self.stopping.is_set():
            with self.lock:enabled=bool(self.config['enabled']);port=int(self.config['port'])
            if not enabled:
                self._close_socket();bound_port=None;self.stopping.wait(.4);continue
            if self.sock is None:
                try:
                    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
                    s.settimeout(.6);s.bind(('0.0.0.0',port));self.sock=s;bound_port=port;self.last_error=''
                except OSError as exc:
                    self.last_error=f'UDP port {port}: {exc}';self._close_socket();self.stopping.wait(2);continue
            if bound_port!=port:self._close_socket();continue
            try:data,peer=self.sock.recvfrom(MAX_PACKET+1)
            except socket.timeout:
                self._prune();continue
            except OSError:
                self._close_socket();continue
            if len(data)>MAX_PACKET or not self.ingest(data,peer[0]):self.rejected+=1
            self._prune()
        self._close_socket()
    def ingest(self,data,source_ip):
        if len(data)>MAX_PACKET or b'<!DOCTYPE' in data.upper() or b'<!ENTITY' in data.upper():return False
        try:
            root=ET.fromstring(data)
            if root.tag!='event':return False
            point=root.find('point');detail=root.find('detail');ext=detail.find('xtak_veil') if detail is not None else None
            if point is None or ext is None or ext.get('version')!='1':return False
            node_id=_clean(ext.get('node'),120);obj_id=_clean(ext.get('objectId'),160)
            if not node_id or not obj_id:return False
            service=_clean(ext.get('service'),30).lower().replace('-','_')
            # VEIL r50 publishes ADS-B under sourceService=adsb_1090 (not adsb).
            if service in ('adsb_1090','adsb1090','adsb_978','adsb978'):service='adsb'
            if service in ('remoteid','rid','drone'):service='remote_id'
            if service not in SERVICES:return False
            lat=float(point.get('lat'));lon=float(point.get('lon'))
            if not math.isfinite(lat) or not math.isfinite(lon) or abs(lat)>90 or abs(lon)>180:return False
            t=_stamp(ext.get('positionTimestamp')) or _stamp(root.get('time'))
            now=time.time()
            if t is None or t>now+120 or t<now-86400:return False
            stale=_stamp(root.get('stale')) or t+60
            if stale<=now-10:return False
            sequence=int(ext.get('sequence') or 0)
            call=detail.find('contact') if detail is not None else None
            track=detail.find('track') if detail is not None else None
            aprs=ext.find('aprs_symbol');enrich=ext.find('enrichment')
            with self.lock:
                node=self.nodes.get(node_id)
                if not self.config['enabled'] or not node or source_ip not in _resolved(node['host']):return False
                key=(node_id,obj_id);old=self.objects.get(key)
                if old and t<old['timestamp']:return True
                if old and t==old['timestamp'] and sequence<=old['sequence']:return True
                _identity={k:ext.get(k) for k in ('icao','icao24','hex','mmsi','callsign','station','objectName','objectOwner','uasId','uasIdType') if ext.get(k)}
                if service=='aprs':
                    contact_callsign=_clean(call.get('callsign') if call is not None else '',24)
                    if contact_callsign:_identity.setdefault('callsign',contact_callsign)
                    # r50 object IDs are aprs-object:CALLSIGN:OBJECT; do not infer from map position.
                    if str(obj_id).startswith('aprs-object:'):
                        parts=str(obj_id).split(':',2)
                        if len(parts)==3:
                            _identity.setdefault('objectOwner',parts[1])
                            _identity.setdefault('objectName',parts[2])
                _safe_id,_canonical=identity_envelope(service,_identity,{},obj_id)
                obj={'id':f'veil:{node_id}:{obj_id}','nodeId':node_id,'objectId':obj_id,'service':service,
                     'lat':lat,'lon':lon,'hae':point.get('hae'),'type':_clean(root.get('type'),60),
                     'title':_clean(call.get('callsign') if call is not None else obj_id,120),
                     'remarks':_clean(detail.findtext('remarks') if detail is not None else '',1200),
                     'heading':track.get('course') if track is not None else None,'speedMps':track.get('speed') if track is not None else None,
                     'timestamp':t,'stale':min(stale,now+1800),'sequence':sequence,'freshness':_clean(ext.get('freshnessState'),24),
                     'aprs':aprs_symbol(raw=dict(aprs.attrib)) if service=='aprs' and aprs is not None else {},'enrichment':dict(enrich.attrib) if enrich is not None else {},'identity':_safe_id,'canonicalKey':_canonical,'transport':'udp'}
                self.objects[key]=obj;self.packets+=1
                node['lastPacket']=now;node['lastPosition']=t
                if len(self.objects)>MAX_OBJECTS:
                    oldest=sorted(self.objects,key=lambda k:self.objects[k]['timestamp'])
                    for k in oldest[:len(self.objects)-MAX_OBJECTS]:self.objects.pop(k,None)
            return True
        except (ET.ParseError,ValueError,TypeError,OverflowError,KeyError,OSError):return False
    def _prune(self):
        now=time.time()
        with self.lock:
            for k,obj in list(self.objects.items()):
                if obj['stale']<now or obj['timestamp']<now-1800:self.objects.pop(k,None)
    @staticmethod
    def lan_addresses():
        try:
            r=subprocess.run(['ip','-4','-o','addr','show','up'],text=True,capture_output=True,timeout=1.5)
            rows=[]
            for line in (r.stdout or '').splitlines():
                m=re.search(r'\binet\s+(\d+\.\d+\.\d+\.\d+)/',line)
                if not m:continue
                ip=ipaddress.ip_address(m.group(1))
                if ip.is_private and not ip.is_loopback and not ip.is_link_local:rows.append(str(ip))
            return list(dict.fromkeys(rows))[:12]
        except (OSError,subprocess.TimeoutExpired):return []
    def status(self):
        now=time.time()
        with self.lock:
            nodes=[]
            for node in self.nodes.values():
                last=node.get('lastPacket') or 0
                count=sum(1 for x in self.objects.values() if x['nodeId']==node['nodeId'])
                nodes.append({**node,'state':'receiving' if self.config['enabled'] and last and now-last<90 else 'configured' if not self.config['enabled'] else 'waiting',
                              'objects':count})
            service_counts={name:sum(1 for x in self.objects.values() if x['service']==name) for name in SERVICES}
            return {'ok':True,'config':dict(self.config),'nodes':nodes,'objectsCount':len(self.objects),'counts':service_counts,
                    'receiving':sum(n['state']=='receiving' for n in nodes),'packets':self.packets,'rejected':self.rejected,
                    'receiverActive':bool(self.sock),'error':self.last_error,'lanIPs':self.lan_addresses()}
    def snapshot(self):
        with self.lock:
            return {'ok':True,'objects':list(self.objects.values()) if self.config['enabled'] and self.config['visible'] else [],'time':time.time()}
