#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, os, pathlib, sys, tempfile

ROOT=pathlib.Path(__file__).resolve().parents[1]
CUSTOM='db450cbe-2fec-47fb-bd2b-ba2db89b035e/Incident Management/water point.png'

def uid_row(uid, callsign, cot_type, lat, lon, icon=''):
    return {
        'data':uid,
        'timestamp':'2026-07-27T12:00:00Z',
        'creatorUid':'ATAK-EUD-1',
        'details':{
            'type':cot_type,
            'callsign':callsign,
            'iconsetPath':icon,
            'color':'-1',
            'location':{'lat':lat,'lon':lon},
        },
    }

rows=[
    uid_row('DS-P01','DS-P01','a-f-G-U-C',34.01,-117.01),
    uid_row('DS-P02','DS-P02','a-f-G-E-V',34.02,-117.02),
    uid_row('DS-P03','DS-P03','a-f-G-E-W',34.03,-117.03),
    uid_row('DS-P04','DS-P04','a-f-G-U-C-I',34.04,-117.04),
    uid_row('DS-P05','DS-P05','a-f-G-U-C-A',34.05,-117.05),
    uid_row('DS-P06','DS-P06','a-f-G-U-C-M',34.06,-117.06),
    uid_row('DS-P07','DS-P07','a-f-G-E-V-A',34.07,-117.07),
    uid_row('DS-P09','DS-P09','a-f-F-N-S',34.09,-117.09),
    uid_row('DS-P16','Water Point','a-n-G',34.16,-117.16,CUSTOM),
]

discovery={
    'version':3,
    'type':'Mission',
    'data':[{
        'name':'TAKMAP-DATASYNC-TEST',
        'guid':'guid-1',
        'tool':'public',
        'passwordProtected':True,
        'groups':['__ANON__','Team01'],
        'uids':rows,
        'contents':[],
    }],
}

with tempfile.TemporaryDirectory(prefix='tak-map-i569-live-contract-') as td:
    os.environ['TAK_DASHBOARD_DATA_DIR']=td
    spec=importlib.util.spec_from_file_location('tak_dashboard_i569_live_contract',ROOT/'tak_dashboard.py')
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;assert spec.loader;spec.loader.exec_module(m)
    cfg={'api_url':'https://ots.test','base_url':'https://ots.test','marti_url':'https://opentakserver:8443'}
    sess={'auth_mode':'ots-user','username':'darktek','callsign':'raptor','tak_uid':'ATAK-EUD-1','profile':{'username':'darktek','tak_uid':'ATAK-EUD-1'}}
    calls=[]
    def fake(path, **kwargs):
        calls.append((path,dict(kwargs)))
        if path=='/Marti/api/missions?passwordProtected=true':
            return {'ok':True,'status':200,'body':__import__('json').dumps(discovery),'json':discovery,'error':'','identity_mode':'per-user-enrolled-marti-certificate'}
        raise AssertionError('Unexpected live Mission network request: '+path)
    m._i569_mission_request=fake
    def unexpected(*args,**kwargs):
        raise AssertionError('Unexpected generic request path: '+repr(args))
    m._i568_request_json_before=unexpected
    m._i568_set_context('SESSION',sess)
    try:
        result,acquired=m._i568_build_snapshot(cfg,sess,'SESSION','live-contract-test')
    finally:
        m._i568_clear_context()

    assert [x[0] for x in calls]==['/Marti/api/missions?passwordProtected=true'],calls
    summary=acquired['summary']
    assert summary['mission_count']==1,summary
    assert summary['discovery_mission_uid_count']==9,summary
    assert summary['password_protected_mission_count']==1,summary
    assert summary['network_get_contents_calls']==0,summary
    assert summary['cot_enrichment_attempted_count']==0,summary
    assert summary['cot_enrichment_skipped_password_protected_count']==1,summary
    assert acquired['mission_names']==['TAKMAP-DATASYNC-TEST'],acquired['mission_names']

    visible=result.get('objects') or []
    raw=result.get('mission_uids') or []
    assert len(raw)==9,(len(raw),raw)
    by_uid={str(row.get('uid') or row.get('cot_uid') or row.get('event_uid') or row.get('data')):row for row in visible if isinstance(row,dict)}
    assert len(by_uid)==9,(len(by_uid),[r.get('uid') for r in visible])
    water=by_uid['DS-P16']
    assert water.get('data_sync_current_iconset_path_i567')==CUSTOM,water
    sof=by_uid['DS-P09']
    assert sof.get('mil2525_file')=='friendly-ground-unit-special-forces.svg',sof
    assert result['data_sync_remote_seed_i569']['missionuid_discovery_authoritative'] is True
    assert result['data_sync_background_worker_i569']['acquisition']['authoritative_discovery']=='/Marti/api/missions?passwordProtected=true'

    # Exercise the same background state transition consumed by the browser card.
    key=m._i568_state_key(cfg,sess)
    state=m._i568_state(key)
    initial=m._i568_response_payload(state)
    assert initial.get('initial_ots_refresh_in_progress') is True,initial
    scheduled,why=m._i568_schedule_refresh(key,cfg,sess,'SESSION','startup-live-contract',force=True)
    assert scheduled and why=='scheduled',(scheduled,why)
    import time
    deadline=time.monotonic()+5
    card=None
    while time.monotonic()<deadline:
        card=m._i568_response_payload(state)
        if len(card.get('objects') or [])==9:
            break
        time.sleep(.02)
    assert card and len(card.get('objects') or [])==9,card
    assert card['data_sync_background_i569']['state']=='ready',card['data_sync_background_i569']

print('i569 live OpenTAKServer password-protected Mission contract and nine-object projection passed')
