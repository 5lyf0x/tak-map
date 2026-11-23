"""TAK Map TMS-FINAL 2.0 Token Mesh persistent journal and enrollment.

Local synthetic protocol testing is not Android interoperability certification.
Never bridges to TAK Gateway/OTS automatically.
"""
import base64
import contextlib
import hashlib
import json
import os
import secrets
import sqlite3
import threading
import time
import uuid
from pathlib import Path

MAX_PAYLOAD = 32 * 1024 * 1024
KIND = {'POINT', 'ROUTE', 'AREA', 'FILE'}
ACTION = {'ADD', 'UPDATE', 'REMOVE'}


def _b64url(data):
    return base64.urlsafe_b64encode(data).decode('ascii').rstrip('=')


def _unb64url(data):
    if not isinstance(data, str) or len(data) > 4096 or not data or any(c not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_' for c in data):
        raise ValueError('Invalid token encoding')
    return base64.urlsafe_b64decode(data + '=' * (-len(data) % 4))


def decode_invite(text, prefix='XTM1:'):
    if not isinstance(text, str) or not text.startswith(prefix) or len(text) > 4096:
        raise ValueError('Expected ' + prefix + ' invitation')
    try:
        obj = json.loads(_unb64url(text[len(prefix):]))
        if not isinstance(obj, dict) or obj.get('v') != 1:
            raise ValueError('Unsupported invitation version')
        if prefix == 'XTM1:':
            group = str(uuid.UUID(obj['groupId']))
            if group != obj['groupId']:
                raise ValueError('Group UUID must be canonical')
            name = obj['name']
            if not isinstance(name, str) or not 1 <= len(name.strip()) <= 80:
                raise ValueError('Invalid group name')
            key = base64.b64decode(obj['key'], validate=True)
            if len(key) != 32:
                raise ValueError('Invalid 256-bit group key')
            return {'groupId': group, 'name': name.strip(), 'key': obj['key']}
        mission = str(uuid.UUID(obj['missionId']))
        if mission != obj['missionId'] or not isinstance(obj.get('missionName'), str):
            raise ValueError('Invalid Mission identity')
        if len(base64.b64decode(obj['key'], validate=True)) != 32:
            raise ValueError('Invalid Mission key')
        return obj
    except (KeyError, TypeError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError('Invalid invitation: ' + str(exc)) from None


def encode_invite(group):
    obj = {'v': 1, 'groupId': group['groupId'], 'name': group['name'], 'key': group['key']}
    return 'XTM1:' + _b64url(json.dumps(obj, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))


def _utf16_sort(value):
    return str(value).encode('utf-16-be', 'surrogatepass')


def head_rank(op):
    # Baseline seeds cannot override ordinary user edits, even with higher rev.
    baseline = bool(op.get('baseline')) and not bool(op.get('repair'))
    return (0 if baseline else 1, int(op['rev']), _utf16_sort(op['origin']), _utf16_sort(op.get('opId', op.get('op_id', ''))))


class MeshStore:
    def __init__(self, folder):
        self.root = Path(folder)
        self.root.mkdir(parents=True, exist_ok=True)
        self.dbfile = self.root / 'journal.sqlite3'
        self.secretfile = self.root / 'group-secret.json'
        self.lock = threading.RLock()
        self._init()

    @contextlib.contextmanager
    def _db(self):
        connection = sqlite3.connect(self.dbfile, timeout=10)
        try:
            connection.row_factory = sqlite3.Row
            connection.execute('PRAGMA foreign_keys=ON')
            connection.execute('PRAGMA journal_mode=WAL')
            with connection:
                yield connection
        finally:
            connection.close()

    def _init(self):
        with self._db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS settings (k TEXT PRIMARY KEY, v TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS missions (mission TEXT PRIMARY KEY, name TEXT NOT NULL, server_identity TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 0, key TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS clocks (mission TEXT PRIMARY KEY, rev INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS ops (op_id TEXT PRIMARY KEY, mission TEXT NOT NULL, origin TEXT NOT NULL, seq INTEGER NOT NULL, rev INTEGER NOT NULL, kind TEXT NOT NULL, uid TEXT NOT NULL, type TEXT NOT NULL, payload_hash TEXT NOT NULL, payload BLOB NOT NULL, base_fp TEXT NOT NULL, result_fp TEXT NOT NULL, baseline INTEGER NOT NULL, repair INTEGER NOT NULL, created INTEGER NOT NULL, metadata TEXT NOT NULL, UNIQUE(mission,origin,seq));
                CREATE INDEX IF NOT EXISTS ops_origin ON ops(mission,origin,seq);
                CREATE TABLE IF NOT EXISTS heads (mission TEXT NOT NULL, kind TEXT NOT NULL, uid TEXT NOT NULL, op_id TEXT NOT NULL, tombstone INTEGER NOT NULL, PRIMARY KEY(mission,kind,uid));
                CREATE TABLE IF NOT EXISTS checkpoints (mission TEXT NOT NULL, origin TEXT NOT NULL, seq INTEGER NOT NULL, PRIMARY KEY(mission,origin));
            ''')
            row = db.execute("SELECT v FROM settings WHERE k='deviceUid'").fetchone()
            if not row:
                db.execute("INSERT INTO settings(k,v) VALUES ('deviceUid',?)", ('takmap-' + str(uuid.uuid4()),))
        os.chmod(self.dbfile, 0o600)

    def device_uid(self):
        with self._db() as db:
            return db.execute("SELECT v FROM settings WHERE k='deviceUid'").fetchone()[0]

    def group(self):
        with self.lock:
            if not self.secretfile.exists():
                return None
            return json.loads(self.secretfile.read_text(encoding='utf-8'))

    def _save_group(self, group):
        temp = self.secretfile.with_suffix('.tmp')
        fd = os.open(str(temp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(group, f)
                f.flush()
                os.fsync(f.fileno())
            os.replace(temp, self.secretfile)
            os.chmod(self.secretfile, 0o600)
        finally:
            if temp.exists():
                temp.unlink()

    def create(self, name):
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 80:
            raise ValueError('Mesh name must be 1–80 characters')
        with self.lock:
            if self.group():
                raise ValueError('Leave the current Mesh before creating another')
            group = {'groupId': str(uuid.uuid4()), 'name': name.strip(), 'key': base64.b64encode(secrets.token_bytes(32)).decode('ascii')}
            self._save_group(group)
            return {'ok': True, 'invite': encode_invite(group), 'groupId': group['groupId'], 'name': group['name']}

    def join(self, invite):
        group = decode_invite(invite)
        with self.lock:
            if self.group():
                raise ValueError('Leave the current Mesh before joining another')
            self._save_group(group)
        return {'ok': True, 'name': group['name'], 'groupId': group['groupId']}

    def leave(self):
        with self.lock:
            if self.secretfile.exists():
                self.secretfile.unlink()
        return {'ok': True, 'note': 'Membership secret removed; journal and Mission bindings retained, but inactive. Other peers remain enrolled.'}

    def mesh_enabled(self):
        """Persisted network switch; never deletes credentials or Mission journals."""
        with self._db() as db:
            row=db.execute("SELECT v FROM settings WHERE k='meshSyncEnabled'").fetchone()
        return not row or row['v']=='1'

    def set_mesh_enabled(self, enabled):
        if type(enabled) is not bool:
            raise ValueError('Mesh enabled must be a boolean')
        with self.lock, self._db() as db:
            db.execute("INSERT INTO settings(k,v) VALUES('meshSyncEnabled',?) ON CONFLICT(k) DO UPDATE SET v=excluded.v", ('1' if enabled else '0',))
        return {'ok':True,'meshEnabled':enabled}

    def create_mission(self, name):
        if not isinstance(name,str) or not 1<=len(name.strip())<=120:
            raise ValueError('Mission name must be 1–120 characters')
        with self.lock:
            group=self.group()
            if not group:
                raise ValueError('Join or create a Mesh before creating Missions')
            if not self.mesh_enabled():
                raise ValueError('Enable Mesh Sync before creating Missions')
            mission_id=str(uuid.uuid4())
            mission_key=base64.b64encode(secrets.token_bytes(32)).decode('ascii')
            # Local Mesh namespace, never an OTS or Gateway Mission enrollment.
            server_identity='token-mesh:'+group['groupId']
            with self._db() as db:
                db.execute('INSERT INTO missions(mission,name,server_identity,enabled,key) VALUES(?,?,?,?,?)',
                           (mission_id,name.strip(),server_identity,1,mission_key))
            return {'ok':True,'missionId':mission_id,'missionName':name.strip(),
                    'invite':self.mission_invite(mission_id)}

    def mission_invite(self, mission_id):
        if not self.group():
            raise ValueError('Mesh enrollment required')
        try: mission_id=str(uuid.UUID(str(mission_id)))
        except (ValueError,TypeError,AttributeError): raise ValueError('Invalid Mission UUID') from None
        with self._db() as db:
            row=db.execute('SELECT mission,name,server_identity,key FROM missions WHERE mission=?',(mission_id,)).fetchone()
        if not row:raise ValueError('Mission binding not found')
        obj={'v':1,'missionId':row['mission'],'missionName':row['name'],
             'serverIdentity':row['server_identity'],'key':row['key']}
        return 'XMS1:'+_b64url(json.dumps(obj,ensure_ascii=False,separators=(',',':')).encode('utf-8'))

    def mission_join(self, token):
        if not self.group():
            raise ValueError('Mesh enrollment required to join a Mission')
        if not self.mesh_enabled():
            raise ValueError('Enable Mesh Sync before joining Missions')
        mission = decode_invite(token, 'XMS1:')
        with self.lock:
            with self._db() as db:
                db.execute('INSERT INTO missions(mission,name,server_identity,enabled,key) VALUES(?,?,?,?,?) ON CONFLICT(mission) DO UPDATE SET name=excluded.name,server_identity=excluded.server_identity,enabled=1,key=excluded.key',
                           (mission['missionId'], mission['missionName'][:120], str(mission.get('serverIdentity', ''))[:256], 1, mission['key']))
        return {'ok': True, 'missionId': mission['missionId']}

    def mission_list(self):
        with self._db() as db:
            return [dict(mission=r['mission'], name=r['name'], enabled=bool(r['enabled'])) for r in db.execute('SELECT mission,name,enabled FROM missions ORDER BY name')]

    def mission_enabled(self, mission_id, enabled):
        with self._db() as db:
            result = db.execute('UPDATE missions SET enabled=? WHERE mission=?', (int(bool(enabled)), mission_id))
            if not result.rowcount:
                raise ValueError('Mission binding not found')
        return {'ok': True}

    def _validate_operation(self, op, payload):
        if not isinstance(op, dict) or not isinstance(payload, bytes) or len(payload) > MAX_PAYLOAD:
            raise ValueError('Invalid operation payload')
        mission = str(uuid.UUID(op['missionId']))
        if op['missionId'] != mission:
            raise ValueError('Invalid Mission UUID')
        if not op.get('origin') or len(str(op['origin'])) > 256 or not op.get('uid') or len(str(op['uid'])) > 512:
            raise ValueError('Invalid immutable identity')
        if op['type'] not in ACTION or op['kind'] not in KIND:
            raise ValueError('Unsupported operation')
        if not (1 <= int(op['seq']) <= 9223372036854775807 and 0 <= int(op['rev']) <= 9223372036854775807):
            raise ValueError('Invalid sequence/revision')
        if str(uuid.UUID(op['opId'])) != op['opId']:
            raise ValueError('Invalid operation ID')
        if op.get('payloadHash', '') != hashlib.sha256(payload).hexdigest() or int(op.get('payloadSize', -1)) != len(payload):
            raise ValueError('Payload size/hash mismatch')

    def _head(self, db, mission, kind, uid):
        row = db.execute('SELECT o.* FROM heads h JOIN ops o ON h.op_id=o.op_id WHERE h.mission=? AND h.kind=? AND h.uid=?', (mission, kind, uid)).fetchone()
        return dict(row) if row else None

    def receive(self, op, payload):
        self._validate_operation(op, payload)
        mid = op['missionId']
        with self.lock, self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            authorized = db.execute('SELECT enabled FROM missions WHERE mission=?', (mid,)).fetchone()
            if not authorized or not authorized['enabled'] or not self.group():
                raise ValueError('Group enrollment and enabled Mission binding required')
            existing = db.execute('SELECT * FROM ops WHERE op_id=? OR (mission=? AND origin=? AND seq=?)', (op['opId'], mid, op['origin'], int(op['seq']))).fetchone()
            if existing:
                if (existing['op_id'] != op['opId'] or existing['payload_hash'] != op['payloadHash'] or existing['mission'] != mid or existing['origin'] != op['origin'] or existing['seq'] != int(op['seq']) or existing['rev'] != int(op['rev']) or existing['kind'] != op['kind'] or existing['uid'] != op['uid'] or existing['type'] != op['type'] or existing['baseline'] != int(bool(op.get('baseline'))) or existing['repair'] != int(bool(op.get('repair')))):
                    raise ValueError('Operation identity collision')
                return {'ok': True, 'duplicate': True, 'winner': False}
            cp = db.execute('SELECT seq FROM checkpoints WHERE mission=? AND origin=?', (mid, op['origin'])).fetchone()
            if cp and int(op['seq']) <= cp['seq']:
                raise ValueError('Operation predates verified checkpoint')
            meta = {k:v for k,v in op.items() if k != 'payload'}
            db.execute('INSERT INTO ops VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                       (op['opId'],mid,op['origin'],int(op['seq']),int(op['rev']),op['kind'],op['uid'],op['type'],op['payloadHash'],payload,str(op.get('baseFp','')),str(op.get('resultFp','')),int(bool(op.get('baseline'))),int(bool(op.get('repair'))),int(op.get('created',0)),json.dumps(meta,separators=(',',':')),))
            db.execute('INSERT INTO clocks(mission,rev) VALUES(?,?) ON CONFLICT(mission) DO UPDATE SET rev=MAX(rev,excluded.rev)', (mid,int(op['rev'])))
            head = self._head(db,mid,op['kind'],op['uid'])
            wins = head is None or head_rank(op) > head_rank(head)
            if wins:
                db.execute('INSERT INTO heads(mission,kind,uid,op_id,tombstone) VALUES(?,?,?,?,?) ON CONFLICT(mission,kind,uid) DO UPDATE SET op_id=excluded.op_id,tombstone=excluded.tombstone', (mid,op['kind'],op['uid'],op['opId'],int(op['type']=='REMOVE')))
            return {'ok': True, 'duplicate': False, 'winner': wins}

    def local_op(self, mission, kind, uid, action, payload=b'', baseline=False, repair=False):
        if not self.group():
            raise ValueError('Not enrolled')
        with self.lock, self._db() as db:
            row=db.execute('SELECT enabled FROM missions WHERE mission=?',(mission,)).fetchone()
            if not row or not row['enabled']:
                raise ValueError('Mission not authorized')
            origin=self.device_uid()
            seq=db.execute('SELECT COALESCE(MAX(seq),0)+1 FROM ops WHERE mission=? AND origin=?',(mission,origin)).fetchone()[0]
            clock=db.execute('SELECT rev FROM clocks WHERE mission=?',(mission,)).fetchone()
            rev=(clock[0] if clock else 0)+1
            op=dict(missionId=mission,origin=origin,seq=seq,rev=rev,opId=str(uuid.uuid4()),kind=kind,uid=uid,type=action,payloadHash=hashlib.sha256(payload).hexdigest(),payloadSize=len(payload),baseline=baseline,repair=repair,created=int(time.time()*1000))
            # Receive commits atomically, and allocation is serialized under self.lock.
            result=self.receive(op,payload)
            return {'operation':op, **result}

    def water(self, mission):
        with self._db() as db:
            ret={}
            origins=db.execute('SELECT DISTINCT origin FROM ops WHERE mission=? UNION SELECT origin FROM checkpoints WHERE mission=?',(mission,mission)).fetchall()
            for item in origins:
                origin=item[0]
                checkpoint=db.execute('SELECT seq FROM checkpoints WHERE mission=? AND origin=?',(mission,origin)).fetchone()
                cursor=checkpoint[0] if checkpoint else 0
                for row in db.execute('SELECT seq FROM ops WHERE mission=? AND origin=? AND seq>? ORDER BY seq',(mission,origin,cursor)):
                    if row[0]!=cursor+1:
                        break
                    cursor+=1
                ret[origin]=cursor
            return ret

    def payload_for_operation(self, op_id):
        with self._db() as db:
            row=db.execute('SELECT payload FROM ops WHERE op_id=?',(op_id,)).fetchone()
            return bytes(row[0]) if row else None

    def heads(self, mission):
        with self._db() as db:
            result=[]
            for r in db.execute('SELECT o.metadata,h.tombstone FROM heads h JOIN ops o ON h.op_id=o.op_id WHERE h.mission=? ORDER BY o.kind,o.uid',(mission,)):
                result.append({'operation':json.loads(r['metadata']), 'tombstone':bool(r['tombstone'])})
            return result

    def status(self):
        group=self.group()
        missions=self.mission_list()
        with self._db() as db:
            count=db.execute('SELECT COUNT(*) FROM ops').fetchone()[0]
        return {'ok':True,'status':'Enrolled — discovering/authenticating' if group else 'Not enrolled', 'enrolled':bool(group),'meshEnabled':self.mesh_enabled(),'name':group['name'] if group else '', 'groupId':group['groupId'] if group else '', 'deviceUid':self.device_uid(), 'authenticatedPeers':0,'sharedMissions':0,'pendingSync':0,'lastSuccessfulSync':None,'missionBindings':missions,'journalOperations':count,'transportReady':False,'profile':'TMS-FINAL 2.0 candidate; Android interoperability unverified','note':'XMS2/XTP3 transport is implemented; cross-app Android conformance and native object editing remain unverified. No OTS/Gateway bridge.'}


def invite_png(group):
    """Sensitive PNG with full QR and human-readable unmodified XTM1 invite."""
    try:
        import qrcode
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        raise ValueError('QR image export requires python3-qrcode and python3-pil')
    import io
    invite = encode_invite(group)
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=9, border=4)
    qr.add_data(invite)
    qr.make(fit=True)
    image = qr.make_image(fill_color='black', back_color='white').convert('RGB')
    width = max(920, image.width + 64)
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 19)
        title_font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 27)
    except OSError:
        font = ImageFont.load_default()
        title_font = font
    token_lines = [invite[i:i+72] for i in range(0, len(invite), 72)]
    output = Image.new('RGB', (width, image.height+200+len(token_lines)*30), 'white')
    pen = ImageDraw.Draw(output)
    pen.text((32,18), group['name'][:80], fill='black', font=title_font)
    output.paste(image, ((width-image.width)//2, 60))
    pos = image.height+80
    pen.text((32,pos), 'TOKEN MESH — SECRET JOIN CODE (XTM1)', fill='black', font=title_font)
    for i,line in enumerate(token_lines):
        pen.text((32,pos+42+i*30), line, fill='black', font=font)
    pen.text((32,output.height-42), 'Keep private. This token grants group access.', fill='#aa2222', font=font)
    buf=io.BytesIO()
    output.save(buf,format='PNG')
    return buf.getvalue()

def mission_invite_png(mission_name, token):
    """Mission QR with EXACT XMS1 invite; credentials never written to disk."""
    if not isinstance(token,str) or not token.startswith('XMS1:') or len(token)>4096:
        raise ValueError('Invalid XMS1 invitation')
    decode_invite(token,'XMS1:')
    try:
        import qrcode
        from PIL import Image,ImageDraw,ImageFont
    except ImportError:
        raise ValueError('Mission QR export requires python3-qrcode and python3-pil')
    import io
    qr=qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M,box_size=9,border=4)
    qr.add_data(token);qr.make(fit=True)
    image=qr.make_image(fill_color='black',back_color='white').convert('RGB')
    width=max(920,image.width+64)
    try:
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',19)
        title_font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',27)
    except OSError:
        font=ImageFont.load_default();title_font=font
    lines=[token[i:i+72] for i in range(0,len(token),72)]
    canvas=Image.new('RGB',(width,image.height+200+len(lines)*30),'white')
    draw=ImageDraw.Draw(canvas)
    draw.text((32,18),str(mission_name)[:120],fill='black',font=title_font)
    canvas.paste(image,((width-image.width)//2,60))
    pos=image.height+80
    draw.text((32,pos),'MISSION — SECRET JOIN CODE (XMS1)',fill='black',font=title_font)
    for i,line in enumerate(lines):draw.text((32,pos+42+i*30),line,fill='black',font=font)
    draw.text((32,canvas.height-42),'Keep private. This token grants Mission access within the Mesh.',fill='#aa2222',font=font)
    result=io.BytesIO();canvas.save(result,format='PNG');return result.getvalue()

# Wire-facing journal accessor functions deliberately use the existing operation
# and SUMMARY field names. Network-facing code never gets group credentials here.
def _mesh_summary(self,mission):
    heads=[]
    with self._db() as db:
        for row in db.execute('SELECT o.*,h.tombstone FROM heads h JOIN ops o ON o.op_id=h.op_id WHERE h.mission=? ORDER BY h.kind,h.uid',(mission,)):
            heads.append({'missionId':mission,'kind':row['kind'],'uid':row['uid'],'rev':row['rev'],'origin':row['origin'],'opId':row['op_id'],'hash':row['payload_hash'],'tombstone':bool(row['tombstone']),'baseline':bool(row['baseline']),'repair':bool(row['repair'])})
    if len(heads)>5000:
        raise ValueError('Mesh summary exceeds 5000 object heads')
    return {'type':'SUMMARY','highWater':self.water(mission),'heads':heads}


def _mesh_wire_operations(self, mission, remote):
    if not isinstance(remote,dict) or remote.get('type')!='SUMMARY':raise ValueError('Invalid mesh summary')
    rh={}
    for head in remote.get('heads',[]):
        if not isinstance(head,dict):raise ValueError('Invalid remote head')
        if head.get('missionId')!=mission:raise ValueError('Mission head mismatch')
        rh[(head['kind'],head['uid'])]=head
    high=remote.get('highWater') or {}
    if not isinstance(high,dict) or len(high)>2000 or len(rh)>5000:raise ValueError('Invalid remote summary limits')
    send={}
    with self._db() as db:
        for op in db.execute('SELECT * FROM ops WHERE mission=? ORDER BY rev,origin,seq',(mission,)):
            if op['seq']>int(high.get(op['origin'],0)):
                send[op['op_id']]=dict(op)
        for op in db.execute('SELECT o.* FROM heads h JOIN ops o ON o.op_id=h.op_id WHERE h.mission=?',(mission,)):
            other=rh.get((op['kind'],op['uid']))
            if other is None or head_rank(dict(op))>head_rank(other):
                send[op['op_id']]=dict(op)
    return list(send.values())


def _mesh_adopt_checkpoint(self,mission,announced,sender):
    """Adopt only after COMPLETE transfer and verified current-head dominance.

    This does not certify malicious peer completeness. Checkpoint adoption only
    covers the sender's advertised prefix, never its claimed max revision.
    """
    announced=announced or {}
    expected=sender.get('highWater') or {}
    heads=sender.get('heads') or []
    if not isinstance(announced,dict) or len(announced)>2000 or len(heads)>5000:
        raise ValueError('Invalid checkpoint')
    with self.lock,self._db() as db:
        db.execute('BEGIN IMMEDIATE')
        for h in heads:
            if h['missionId']!=mission:raise ValueError('Checkpoint Mission mismatch')
            local=self._head(db,mission,h['kind'],h['uid'])
            if local is None or head_rank(local)<head_rank(h):
                raise ValueError('Cannot adopt incomplete checkpoint; missing current head')
            payload=local['payload']
            if hashlib.sha256(payload).hexdigest()!=local['payload_hash']:
                raise ValueError('Cannot adopt checkpoint: local payload corrupted')
        for origin,seq in announced.items():
            if not isinstance(origin,str) or not 1<=len(origin)<=256 or type(seq) is not int or seq<0 or seq>int(expected.get(origin,0)):
                raise ValueError('Unverified checkpoint origin/boundary')
            current=db.execute('SELECT seq FROM checkpoints WHERE mission=? AND origin=?',(mission,origin)).fetchone()
            if seq>0 and (current is None or seq>current[0]):
                db.execute('INSERT INTO checkpoints(mission,origin,seq) VALUES(?,?,?) ON CONFLICT(mission,origin) DO UPDATE SET seq=MAX(seq,excluded.seq)',(mission,origin,seq))
    return True


def _mesh_binding_enabled(self,mission):
    with self._db() as db:
        row=db.execute('SELECT enabled FROM missions WHERE mission=?',(mission,)).fetchone()
        return bool(row and row[0])


MeshStore.summary=_mesh_summary
MeshStore.operations_for_peer=_mesh_wire_operations
MeshStore.adopt_checkpoint=_mesh_adopt_checkpoint
MeshStore.is_mission_enabled=_mesh_binding_enabled
