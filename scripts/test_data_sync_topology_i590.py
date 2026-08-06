#!/usr/bin/env python3
import importlib.util, json, os, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('TAK_MAP_DATA_DIR', tempfile.mkdtemp(prefix='tak-map-i590-'))
spec=importlib.util.spec_from_file_location('tak_dashboard_i590', ROOT/'tak_dashboard.py')
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

# Remote OTS: Mission API succeeds, no local PostgreSQL URI. The historical
# PostgreSQL error must be converted into an optional skipped source.
mod._candidate_ots_pg_uris=lambda:([],[])
remote={
 'ok':False,'error':'No OpenTAKServer PostgreSQL URI found.','missions':[{'name':'REMOTE'}],
 'objects':[{'uid':'REMOTE-1','mission':'REMOTE','lat':34.0,'lon':-117.0}],
 'mission_content':[],'mission_uids':[],'packages':[],'sources':[],
 'data_sync_remote_seed_i568':{'per_user_authenticated_source':True,'mission_count':1},
 'data_sync_background_worker_i569':{'acquisition':{'discovery_ok':True,'mission_count':1}},
}
out=mod._i590_normalize_remote_payload(remote, {'summary':{'discovery_ok':True,'mission_count':1}})
assert out['ok'] is True and out['error']==''
assert out['data_sync_topology_i590']['mode']=='remote-mission-api'
assert out['data_sync_sources_i590']['postgresql']['skipped'] is True
assert len(out['objects'])==1

# Local/co-located path: a payload without a remote marker is byte-for-byte
# semantically unchanged by the i590 normalizer.
local={'ok':True,'missions':[{'name':'LOCAL'}],'objects':[{'uid':'LOCAL-1'}],
       'sources':[{'source':'postgres:missions','ok':True,'rows':1}]}
local_out=mod._i590_normalize_remote_payload(local)
assert local_out==local

# Hybrid: a working PostgreSQL source remains present and the mode is hybrid.
mod._candidate_ots_pg_uris=lambda:(['postgresql://redacted'],[])
hybrid=dict(remote); hybrid['ok']=True; hybrid['error']=''; hybrid['sources']=[{'source':'postgres:missions','ok':True,'rows':1}]
hybrid_out=mod._i590_normalize_remote_payload(hybrid, {'summary':{'discovery_ok':True,'mission_count':1}})
assert hybrid_out['data_sync_topology_i590']['mode']=='hybrid'
assert hybrid_out['data_sync_sources_i590']['postgresql']['ok'] is True

# Remote healthy / PostgreSQL configured but temporarily unavailable remains a
# usable partial snapshot and exposes the source warning independently.
failed_pg=dict(remote); failed_pg['sources']=[{'source':'postgres:missions','ok':False,'error':'connection refused'}]
failed_pg_out=mod._i590_normalize_remote_payload(failed_pg, {'summary':{'discovery_ok':True,'mission_count':1}})
assert failed_pg_out['ok'] is True and failed_pg_out['partial'] is True
assert failed_pg_out['data_sync_sources_i590']['postgresql']['failed'] is True
assert failed_pg_out.get('warnings')
print(json.dumps({'ok':True,'remote':out['data_sync_topology_i590'],'hybrid':hybrid_out['data_sync_topology_i590']},indent=2))
