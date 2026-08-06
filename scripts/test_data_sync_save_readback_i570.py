#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, os, pathlib, sys, tempfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='tak-map-i570-readback-') as td:
    os.environ['TAK_DASHBOARD_DATA_DIR']=td
    spec=importlib.util.spec_from_file_location('tak_dashboard_i570_readback',ROOT/'tak_dashboard.py')
    m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;assert spec.loader;spec.loader.exec_module(m)
    sess={'auth_mode':'ots-user','username':'darktek','callsign':'raptor','tak_uid':'TAKMAP-WEB-USER','profile':{'username':'darktek','tak_uid':'TAKMAP-WEB-USER'}}
    m._i568_set_context('SESSION',sess)
    try:
        active='<event version="2.0" uid="DS-P10" type="a-f-G-E-V-A" how="h-e" time="2026-07-27T12:00:02Z" start="2026-07-27T12:00:02Z" stale="2026-07-27T12:10:02Z"><point lat="34.1001" lon="-117.2002" hae="0" ce="10" le="10"/><detail><contact callsign="DS-P10"/><remarks>updated</remarks></detail></event>'
        terminal='<event version="2.0" uid="DS-P10" type="t-x-d-d" how="h-e" time="2026-07-27T12:00:01Z" start="2026-07-27T12:00:01Z" stale="2026-07-27T12:00:02Z"><point lat="34.1001" lon="-117.2002" hae="0" ce="10" le="10"/><detail/></event>'
        calls=[]
        def primary(path,method='GET',public_host='',timeout=20,**kwargs):
            calls.append((path,timeout))
            assert method=='GET'
            return {'ok':True,'status':200,'body':'<events>'+terminal+active+'</events>','json':{},'error':''}
        m._ots_mission_api_request=primary
        result=m._i528_confirm_readback('Mission One','DS-P10','OTHER-ATAK-CREATOR')
        assert result['ok'],result
        assert calls==[('/Marti/api/missions/Mission%20One/cot',3)],calls
        assert 'creatorUid' not in calls[0][0]
        assert result['creator_uid_filter_primary'] is False
        assert result['creator_uid_fallback_used'] is False
        assert result['readback_row_cached'] is True
        cached=m._i570_snapshot_find('DS-P10','Mission One')
        assert cached and m._i555_object_uid(cached)=='DS-P10',cached
        assert not m._i563_delete_event(cached),cached

        # Compatibility creator filtering is allowed only when the unfiltered form is rejected.
        calls.clear()
        def fallback(path,method='GET',public_host='',timeout=20,**kwargs):
            calls.append(path)
            if '?' not in path:
                return {'ok':False,'status':405,'body':'','json':{},'error':'unsupported'}
            return {'ok':True,'status':200,'body':'<events>'+active+'</events>','json':{},'error':''}
        m._ots_mission_api_request=fallback
        result=m._i528_confirm_readback('Mission One','DS-P10','OTHER-ATAK-CREATOR')
        assert result['ok'],result
        assert calls[0]=='/Marti/api/missions/Mission%20One/cot',calls
        assert calls[1]=='/Marti/api/missions/Mission%20One/cot?creatorUid=OTHER-ATAK-CREATOR',calls
        assert result['creator_uid_fallback_used'] is True
    finally:
        m._i568_clear_context()
print('i570 exact-UID save read-back uses unfiltered authenticated Mission /cot and bounded compatibility fallback')
