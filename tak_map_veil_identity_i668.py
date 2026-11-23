"""Non-destructive, strict emitter identity normalizer for XTAK VEIL i668.

Only validated, source-independent identities are eligible for visual merges.
Unknown or conflicting fields remain separate, never matched by callsign, title,
position, CoT affiliation, or receiver-local numeric identifier.
"""
from __future__ import annotations
import re

ICAO = re.compile(r'^[0-9a-fA-F]{6}$')
MMSI = re.compile(r'^[1-9][0-9]{8}$')
APRS = re.compile(r'^[A-Z0-9]{1,6}(?:-(?:[0-9]|1[0-5]))?$', re.I)

def _text(value, maximum=96):
    if not isinstance(value, (str,int)): return ''
    return str(value).strip()[:maximum]

def _one(values, pattern):
    normalized={x for x in values if x and pattern.fullmatch(x)}
    return next(iter(normalized)) if len(normalized)==1 else None

def canonical_identity(service, identity=None, metadata=None, native_id=''):
    ident=identity if isinstance(identity,dict) else {}
    meta=metadata if isinstance(metadata,dict) else {}
    source=_text(service,40).lower().replace('-','_')
    name=_text(native_id,160)
    if source.startswith('adsb'):
        keys=[_text(obj.get(k)).lower().removeprefix('icao-').removeprefix('icao:') for obj in (ident,meta) for k in ('icao','icao24','icaoHex','hex','aircraftHex')]
        # Only type-tagged object IDs are valid, not arbitrary 6-char CoT UIDs.
        match=re.fullmatch(r'(?:adsb(?:_1090|_978)?|icao)[:/](?:icao[:/])?([0-9a-fA-F]{6})',name,re.I)
        if match: keys.append(match.group(1).lower())
        raw=_one(keys,ICAO)
        return 'adsb:icao:'+raw if raw else None
    if source in ('ais','ais_vessels','aiscast'):
        keys=[_text(obj.get(k)) for obj in (ident,meta) for k in ('mmsi','MMSI')]
        match=re.fullmatch(r'(?:ais|mmsi|ais_vessels)[:/](?:mmsi[:/])?([0-9]{9})',name,re.I)
        if match:keys.append(match.group(1))
        raw=_one(keys,MMSI)
        return 'ais:mmsi:'+raw if raw else None
    if source=='aprs':
        station=_text(ident.get('callsign') or ident.get('station') or meta.get('stationCallsign'),24).upper()
        owner=_text(ident.get('objectOwner') or meta.get('objectOwner'),24).upper()
        obj=_text(ident.get('objectName') or meta.get('objectName'),50).upper()
        if obj and owner and APRS.fullmatch(owner):return 'aprs:object:'+owner+':'+obj
        # An unqualified APRS object name is not unique among stations.
        if obj:return None
        return 'aprs:station:'+station if APRS.fullmatch(station) else None
    if source in ('remote_id','remoteid','rid'):
        typ=_text(ident.get('uasIdType') or ident.get('idType') or meta.get('uasIdType'),28).lower()
        value=_text(ident.get('uasId') or ident.get('serialNumber') or meta.get('uasId'),64).upper()
        # Session, ephemeral, anonymized and undifferentiated IDs are NOT stable.
        stable={'serial_number','serial','ansi_cta_2063_a','caa_registration_id','utm_assigned_uuid','registration'}
        if typ in stable and 4<=len(value)<=64 and re.fullmatch(r'[A-Z0-9-]+',value):
            return 'rid:'+typ+':'+value
    return None

def identity_envelope(service, identity=None, metadata=None, native_id=''):
    """Safe public identity fields plus canonical ID. No other arbitrary metadata."""
    ident=identity if isinstance(identity,dict) else {}
    out={}
    for k in ('icao','icao24','icaoHex','hex','mmsi','callsign','station','objectName','objectOwner',
              'uasIdType','idType','uasId','serialNumber'):
        x=_text(ident.get(k),64)
        if x:out[k]=x
    return out,canonical_identity(service,ident,metadata,native_id)
