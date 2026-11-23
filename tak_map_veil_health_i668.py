"""Phase 3 read-only VEIL health, using the *existing* Phase 2 session.

Never creates subscriptions, obtains new credentials, or triggers a separate login.
Requires master enable + explicit API subscription + active authorized token.
"""
from __future__ import annotations
from collections import Counter
import math
import threading
import time
from tak_map_veil_api_i666 import _http, NodeUnavailable, AuthRequired

def _safe(value, depth=0):
    if depth>3:return None
    if isinstance(value,bool):return value
    if isinstance(value,(int,float)):return value if math.isfinite(value) else None
    if isinstance(value,str):return value[:140]
    if isinstance(value,list):return [_safe(x,depth+1) for x in value[:8]]
    if isinstance(value,dict):return {str(k)[:50]:_safe(v,depth+1) for k,v in list(value.items())[:24]}
    return None

# Narrow, explicit read-only projection. Never return network interfaces, IPs,
# raw logs, passwords, configuration, or unbounded diagnostic bundles.
def sanitize_health(data):
    if not isinstance(data,dict):raise ValueError('VEIL health response is invalid')
    fields=('veilUptimeSeconds','nodeUptimeSeconds','cpuTemperatureC',
            'load','memory','storage','throttling',
            'lastSampleAt','lastEventAt','sdr','usb','decoderHealth','activeService','warnings')
    out={k:_safe(data[k]) for k in fields if k in data}
    # Cut large active service descriptions and non-health internals.
    service=out.get('activeService')
    if isinstance(service,dict):
        out['activeService']={k:service[k] for k in ('id','name','state','enabled','status','health') if k in service}
    sdr=out.get('sdr')
    if isinstance(sdr,dict):
        out['sdr']={k:sdr[k] for k in ('connected','usable','busy','state','message') if k in sdr}
    warnings=out.get('warnings')
    if isinstance(warnings,list):
        out['warnings']=[{k:x[k] for k in ('code','message') if k in x} if isinstance(x,dict) else str(x)[:140] for x in warnings[:8]]
    return out

class VeilHealthI668:
    def __init__(self,receiver,api):
        self.rx=receiver;self.api=api;self.lock=threading.Lock();self.cache={}
    def read(self,node_id):
        with self.rx.lock:
            if not self.rx.config.get('enabled'):
                return {'ok':True,'state':'disabled','health':None}
            n=self.rx.nodes.get(node_id)
            if not n:return {'ok':False,'state':'not_configured','health':None}
            if not n.get('apiSubscribed'):
                return {'ok':True,'state':'udp_only','health':None,
                        'lastUdpPacket':n.get('lastPacket')}
            node=dict(n)
            observations=[x for x in self.rx.objects.values() if x.get('nodeId')==node_id]
            counts=dict(Counter(x['service'] for x in observations))
            last_packet=n.get('lastPacket')
        with self.api.lock:
            token=self.api.tokens.get(node_id)
            api_state=self.api.statuses.get(node_id,{}).get('apiState','reconnecting')
            last_sync=self.api.statuses.get(node_id,{}).get('lastSnapshot')
            last_api_update=self.api.statuses.get(node_id,{}).get('lastApiUpdate')
        base={'ok':True,'state':api_state,'lastUdpPacket':last_packet,'lastSnapshot':last_sync,
              'lastApiUpdate':last_api_update,'counts':counts,'observationCount':len(observations)}
        if not token or api_state not in ('synced','synchronizing'):
            return {**base,'health':None,'healthReason':'No currently authenticated API session'}
        now=time.time()
        with self.lock:
            cached=self.cache.get(node_id)
            if cached and cached['fetchedAt']>now-22:
                return {**base,**cached}
        # This read does not change auth state and cannot request credentials.
        try:
            self.api._verify(node)
            data=_http(node,'/api/v1/health',token=token,limit=131072)
            safe=sanitize_health(data)
            record={'health':safe,'fetchedAt':time.time(),'healthReason':''}
            with self.lock:self.cache[node_id]=record
            return {**base,**record}
        except AuthRequired:
            return {**base,'health':None,'healthReason':'API authorization unavailable; use normal Connect API flow'}
        except (NodeUnavailable,OSError,TimeoutError,ValueError):
            return {**base,'health':None,'healthReason':'VEIL health currently unavailable'}
