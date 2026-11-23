"""Sanitized XTAK VEIL r50 APRS symbol envelope for TAK Map UDP and API."""
from __future__ import annotations

def _symbol(value):
    return value if isinstance(value,str) and len(value)==1 and 33<=ord(value)<=126 else ''

def _weather(value):
    if isinstance(value,bool): return value
    if isinstance(value,(dict,list)): return True
    if isinstance(value,str): return value.lower()=='true'
    return False

def aprs_symbol(identity=None,metadata=None,object_type='',raw=None):
    identity=identity if isinstance(identity,dict) else {}
    metadata=metadata if isinstance(metadata,dict) else {}
    raw=raw if isinstance(raw,dict) else {}
    symbol=_symbol(identity.get('symbol') or raw.get('symbolCode') or raw.get('symbol'))
    table=_symbol(identity.get('symbolTable') or raw.get('symbolTable'))
    overlay=_symbol(identity.get('overlay') or raw.get('overlay'))
    # Preserve exact raw fields. weather=False is not interpreted as present.
    weather=_weather(metadata.get('weather')) or _weather(raw.get('weather')) or symbol=='_'
    kind=str(object_type or raw.get('objectType') or '')[:64]
    if kind not in ('aprs_station','aprs_object'):kind=''
    return {'symbolCode':symbol,'symbolTable':table,'overlay':overlay,'objectType':kind,'weather':'true' if weather else 'false'}
