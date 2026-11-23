#!/usr/bin/env python3
"""Focused backend ADS-B failover/OFF-network contract for TAK Map i631."""
from pathlib import Path
import os, runpy, tempfile, time, threading

ROOT=Path(__file__).resolve().parents[1]

def aircraft(hexid='A1B2C3'):
    return {'hex':hexid,'flight':'TEST1','lat':34.0,'lon':-118.0,'alt_baro':12000,'gs':240,'track':90,'seen':0.2}

def main():
    os.environ['TAK_MAP_DATA_DIR']=tempfile.mkdtemp(prefix='tak-map-i631-adsb-')
    ns=runpy.run_path(str(ROOT/'tak_dashboard.py'),run_name='tak_map_i631_adsb_test')
    assert ns['TAK_MAP_ITERATION']=='i631'
    g=ns['tak_map_adsb'].__globals__
    assert g['_I631_ADSB_PRIMARY_RETRY_SECONDS']==600.0
    assert g['_i631_provider_url']('primary',{'center_lat':34,'center_lon':-118,'radius_miles':50})=='https://api.airplanes.live/v2/point/34.000000/-118.000000/50'
    assert g['_i631_provider_url']('secondary',{'center_lat':34,'center_lon':-118,'radius_miles':50})=='https://api.adsb.lol/v2/point/34.000000/-118.000000/50'
    # Provider choice is backend-only; final served HTML must not reveal either upstream.
    html=str(ns.get('TAK_MAP_HTML') or '')
    assert 'adsb.lol' not in html.lower()
    assert 'airplanes.live' not in html.lower()

    calls=[]
    def no_network(provider,url,timeout=5):
        calls.append((provider,url))
        raise AssertionError('provider network was called while ADS-B was OFF/cache-only')
    g['_i631_fetch_provider']=no_network
    g['_I631_ADSB_CACHE'].clear();g['_I631_ADSB_LAST_GOOD'].clear()
    out=ns['tak_map_adsb']({'center_lat':34,'center_lon':-118,'radius_miles':50,'_network_allowed':False})
    assert out['ok'] is True and out['aircraft']==[]
    assert calls==[],calls

    # A valid empty primary response is success and must NOT fall through.
    def primary_empty(provider,url,timeout=5):
        calls.append(provider)
        if provider!='primary': raise AssertionError('secondary should not be called after valid empty primary response')
        return {'ac':[],'now':123}
    calls.clear();g['_i631_fetch_provider']=primary_empty
    g['_I631_ADSB_CACHE'].clear();g['_I631_ADSB_STATE']['primary_retry_at']=0
    out=ns['tak_map_adsb']({'center_lat':34,'center_lon':-118,'radius_miles':50,'_network_allowed':True})
    assert out['ok'] is True and out['count']==0 and calls==['primary'],calls

    # Real primary failure falls back immediately to ADSB.lol.
    def primary_down_secondary_ok(provider,url,timeout=5):
        calls.append(provider)
        if provider=='primary': raise RuntimeError('primary unavailable')
        return {'ac':[aircraft()]}
    calls.clear();g['_i631_fetch_provider']=primary_down_secondary_ok
    g['_I631_ADSB_CACHE'].clear();g['_I631_ADSB_STATE']['primary_retry_at']=0
    out=ns['tak_map_adsb']({'center_lat':34,'center_lon':-118,'radius_miles':51,'_network_allowed':True})
    assert out['ok'] is True and out['count']==1 and calls==['primary','secondary'],calls
    assert g['_I631_ADSB_STATE']['primary_retry_at']>time.time()+590

    # During the 10-minute recovery window, primary is not queried again.
    calls.clear();g['_I631_ADSB_CACHE'].clear()
    out=ns['tak_map_adsb']({'center_lat':34,'center_lon':-118,'radius_miles':52,'_network_allowed':True})
    assert out['ok'] is True and out['count']==1 and calls==['secondary'],calls

    # Once the 10-minute gate expires, next enabled request probes primary first
    # and successful recovery restores it without touching secondary.
    def primary_recovers(provider,url,timeout=5):
        calls.append(provider)
        if provider=='primary': return {'ac':[aircraft('D4E5F6')]}
        raise AssertionError('secondary should not run after primary recovery')
    calls.clear();g['_i631_fetch_provider']=primary_recovers
    g['_I631_ADSB_CACHE'].clear();g['_I631_ADSB_STATE']['primary_retry_at']=time.time()-1
    out=ns['tak_map_adsb']({'center_lat':34,'center_lon':-118,'radius_miles':53,'_network_allowed':True})
    assert out['ok'] is True and out['count']==1 and calls==['primary'],calls
    assert g['_I631_ADSB_STATE']['primary_retry_at']==0.0

    # Internal status/cache callers remain network-silent even after cache expiry.
    calls.clear();g['_i631_fetch_provider']=no_network
    g['_I631_ADSB_CACHE'].clear()
    out=ns['tak_map_adsb']({'center_lat':34,'center_lon':-118,'radius_miles':53,'_network_allowed':False})
    assert calls==[],calls

    # If ADS-B is switched OFF while the primary request is still in flight,
    # the backend must not start the secondary fallback afterward.
    client='browser-off-during-primary'
    started=threading.Event(); release=threading.Event(); concurrent_calls=[]; holder={}
    def blocked_primary(provider,url,timeout=5):
        concurrent_calls.append(provider)
        if provider=='primary':
            started.set(); assert release.wait(5), 'primary test release timed out'
            raise RuntimeError('primary failed after browser disabled ADS-B')
        raise AssertionError('secondary started after ADS-B OFF notification')
    g['_i631_fetch_provider']=blocked_primary
    g['_I631_ADSB_CACHE'].clear(); g['_I631_ADSB_STATE']['primary_retry_at']=0
    g['_i631_adsb_set_client_active'](client,True)
    def run_enabled_request():
        holder['out']=ns['tak_map_adsb']({'center_lat':34,'center_lon':-118,'radius_miles':54,'_network_allowed':True,'_client_id':client})
    t=threading.Thread(target=run_enabled_request,daemon=True); t.start()
    assert started.wait(5), 'primary provider did not start'
    g['_i631_adsb_set_client_active'](client,False)
    release.set(); t.join(5); assert not t.is_alive(), 'enabled request did not finish'
    assert concurrent_calls==['primary'],concurrent_calls
    assert holder['out']['ok'] is True

    js=(ROOT/'assets/tak-map-adsb-v491.js').read_text()
    assert "u.searchParams.set('active','1')" in js
    assert "u.searchParams.set('client_id',cfg.clientId)" in js
    assert "function notifyBackendInactive()" in js
    assert "u.searchParams.set('active','0')" in js
    assert "function setEnabled(on,reason)" in js
    assert "if(!on){stopWorker();clearState();statusText('ADS-B disabled.'" in js
    dash=(ROOT/'tak_dashboard.py').read_text()
    assert "qs['_network_allowed'] = (active_value == '1')" in dash
    assert "_i631_adsb_set_client_active(client_id, False)" in dash
    assert "not _i631_adsb_client_active(client_id)" in dash
    assert "if not network_allowed:" in dash
    assert "host = 'api.airplanes.live' if provider == 'primary' else 'api.adsb.lol'" in dash
    assert "_I631_ADSB_PRIMARY_RETRY_SECONDS = 600.0" in dash
    print('TAK Map i631 transparent ADS-B failover and hard OFF network gate passed')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
