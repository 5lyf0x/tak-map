"""TAK Map i699: authenticated per-user, revisioned basemap stack storage.

Never trusts a user id supplied by a client. Keys derive from authenticated
session identity, and every write is atomic on the persistent DATA_DIR.
"""
import hashlib
import json
import os
import tempfile
import threading
from pathlib import Path

_ALLOWED_MODES = frozenset(('normal','multiply','screen','overlay','soft-light','hard-light','darken',
                           'lighten','difference','map-details','terrain-relief','contour-emphasis'))
_MAX_IDS = 512
_MAX_ID_LEN = 180


def identity(session):
    if not isinstance(session, dict):
        raise PermissionError('Not authenticated')
    profile = session.get('profile') if isinstance(session.get('profile'), dict) else {}
    uid = str(profile.get('tak_uid') or session.get('tak_uid') or '').strip()
    key = str(profile.get('identity_key') or '').strip()
    mode = str(session.get('auth_mode') or 'ots').strip().lower()
    username = str(session.get('username') or '').strip().casefold()
    if uid:
        principal = 'tak-uid:' + uid.casefold()
    elif key:
        principal = 'identity:' + key.casefold()
    elif username:
        principal = 'account:' + mode + ':' + username
    else:
        raise PermissionError('Authenticated identity missing')
    return hashlib.sha256(principal.encode('utf8')).hexdigest()


def _ids(values):
    if not isinstance(values, list):
        return []
    out = []
    for value in values[:_MAX_IDS]:
        if isinstance(value, str) and 0 < len(value) <= _MAX_ID_LEN and value not in out:
            out.append(value)
    return out


def _percent(x, default=100):
    try:
        value = float(x)
        return min(200, max(0, round(value))) if value == value and abs(value) < 1e9 else default
    except (TypeError, ValueError, OverflowError):
        return default


def normalize(raw):
    if not isinstance(raw, dict):
        raise ValueError('Basemap preferences must be an object')
    order = _ids(raw.get('order'))
    enabled = _ids(raw.get('enabled'))
    valid = set(order) | set(enabled)
    if not valid or len(valid) > _MAX_IDS:
        raise ValueError('Basemap preferences require valid layer identifiers')
    def record(name, fmt):
        data = raw.get(name) if isinstance(raw.get(name), dict) else {}
        return {key:fmt(data[key]) for key in data if key in valid}
    def blend(v): return v if isinstance(v,str) and v in _ALLOWED_MODES else 'normal'
    def tone(v):
        v = v if isinstance(v,dict) else {}
        return {n:_percent(v.get(n),100) for n in ('brightness','contrast','saturation')}
    def detail(v):
        v = v if isinstance(v,dict) else {}
        return {'strength':min(100,_percent(v.get('strength'),75)),
                'threshold':min(100,_percent(v.get('threshold'),65))}
    return {'order':order,'enabled':enabled,'opacity':record('opacity',lambda x:min(100,_percent(x))),
            'blend':record('blend',blend),'tone':record('tone',tone),
            'detail':record('detail',detail),'expanded':raw.get('expanded') is not False}


class BasemapPreferences:
    def __init__(self, data_dir):
        self.root = Path(data_dir) / 'user_basemap_preferences_i699'
        self.lock = threading.RLock()

    def _path(self, user_key):
        if not isinstance(user_key,str) or len(user_key)!=64 or any(c not in '0123456789abcdef' for c in user_key):
            raise ValueError('Invalid user key')
        return self.root / (user_key + '.json')

    def read(self, session):
        user_key = identity(session)
        with self.lock:
            path = self._path(user_key)
            if not path.is_file():
                return {'ok':True,'user_key':user_key,'revision':0,'preferences':None}
            data = json.loads(path.read_text(encoding='utf8'))
            if not isinstance(data,dict) or not isinstance(data.get('revision'),int):
                raise ValueError('Invalid saved basemap preferences')
            return {'ok':True,'user_key':user_key,'revision':data['revision'],
                    'preferences':data.get('preferences')}

    def write(self, session, revision, prefs):
        if isinstance(revision,bool) or not isinstance(revision,int) or revision<0:
            raise ValueError('Expected integer revision')
        user_key = identity(session)
        normalized = normalize(prefs)
        with self.lock:
            current = self.read(session)
            if revision != current['revision']:
                return {'ok':False,'error':'Another session updated these settings; reload latest preferences',
                        'conflict':True,'user_key':user_key,'revision':current['revision']}
            self.root.mkdir(parents=True,exist_ok=True)
            path=self._path(user_key)
            contents=json.dumps({'schema':1,'revision':revision+1,'preferences':normalized},
                                separators=(',',':'),sort_keys=True)+'\n'
            fd,tmp=tempfile.mkstemp(prefix='.prefs-',dir=str(self.root))
            try:
                with os.fdopen(fd,'w',encoding='utf8') as out:
                    out.write(contents);out.flush();os.fsync(out.fileno())
                os.chmod(tmp,0o600)
                os.replace(tmp,path)
            finally:
                if os.path.exists(tmp): os.unlink(tmp)
            return {'ok':True,'user_key':user_key,'revision':revision+1,'preferences':normalized}
