"""XMS2/XTP3 v3 wire framing ported from TokenMeshCrypto.java in D5-r8-r3.
All byte-construction formats are intentionally frozen. No server bridge.
"""
import hashlib
import hmac
import json
import os
import socket
import struct
import uuid
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

DATAGRAM_PORT=42420
DIRECT_START=42421
MAX_FRAME=96*1024


def write_string(value):
    blob=str(value).encode('utf-8')
    if len(blob)>4096:raise ValueError('String too long')
    return struct.pack('>I',len(blob))+blob


def _recv_all(stream, size):
    if size<0 or size>MAX_FRAME+64:raise ValueError('Read too large')
    chunks=[]
    while size:
        data=stream.recv(size)
        if not data:raise EOFError('Truncated mesh packet')
        chunks.append(data);size-=len(data)
    return b''.join(chunks)


def read_string(sock):
    n=struct.unpack('>I',_recv_all(sock,4))[0]
    if n>4096:raise ValueError('Invalid string length')
    return _recv_all(sock,n).decode('utf-8')


def datagram_encrypt(gid,key,data):
    header=b'XMS2'+b'\x02'+uuid.UUID(gid).bytes
    iv=os.urandom(12)
    return header+iv+AESGCM(key).encrypt(iv,data,header)


def datagram_decrypt(packet,gid,key):
    if not 49<=len(packet)<=1200 or packet[:5]!=b'XMS2\x02' or packet[5:21]!=uuid.UUID(gid).bytes:
        raise ValueError('Unknown group/datagram')
    return AESGCM(key).decrypt(packet[21:33],packet[33:],packet[:21])


def proof(key,role,mission_id,client_uid,server_uid,cn,sn=b''):
    # Java ByteBuffer putString four signed-length-prefixed UTF-8 values + 32/32 raw nonces.
    transcript=b''.join(write_string(item) for item in (role,mission_id,client_uid,server_uid))+cn+sn
    return hmac.new(key,transcript,'sha256').digest()


def derive(key,mission_id,client_uid,server_uid,cn,sn):
    info=('XTAK-MESH-V2|'+mission_id+'|'+client_uid+'|'+server_uid).encode('utf-8')
    salt=hashlib.sha256(cn+sn).digest()
    prk=hmac.new(salt,key,'sha256').digest()
    current=b'';result=b''
    for i in range(1,4):
        current=hmac.new(prk,current+info+bytes([i]),'sha256').digest()
        result+=current
    return result[:32],result[32:64],result[64:68]


class Channel:
    def __init__(self,sock,read_key,write_key,prefix,session_id,read_direction,write_direction):
        self.sock=sock;self.read_key=read_key;self.write_key=write_key;self.prefix=prefix
        self.sid=session_id;self.rd=read_direction;self.wd=write_direction;self.rc=0;self.wc=0

    def _aad(self,direction,count):
        return ('XTAK3|'+self.sid+'|'+direction+'|'+str(count)).encode('utf-8')

    def send(self,object_):
        raw=json.dumps(object_,separators=(',',':'),ensure_ascii=False).encode('utf-8')
        if len(raw)>MAX_FRAME:raise ValueError('Oversize mesh frame')
        self.wc+=1
        nonce=self.prefix+struct.pack('>Q',self.wc)
        encrypted=AESGCM(self.write_key).encrypt(nonce,raw,self._aad(self.wd,self.wc))
        self.sock.sendall(struct.pack('>I',len(encrypted))+encrypted)

    def recv(self):
        size=struct.unpack('>I',_recv_all(self.sock,4))[0]
        if not 17<=size<=MAX_FRAME+32:raise ValueError('Oversize mesh frame')
        packet=_recv_all(self.sock,size)
        self.rc+=1
        nonce=self.prefix+struct.pack('>Q',self.rc)
        raw=AESGCM(self.read_key).decrypt(nonce,packet,self._aad(self.rd,self.rc))
        if len(raw)>MAX_FRAME:raise ValueError('Oversize mesh payload')
        object_=json.loads(raw.decode('utf-8'))
        if not isinstance(object_,dict):raise ValueError('Invalid mesh record')
        return object_


def client_handshake(sock,key,gid,client_uid,server_uid):
    cn=os.urandom(32)
    sock.sendall(b'XTP3\x03'+write_string(gid)+write_string(client_uid)+write_string(server_uid)+cn+proof(key,'TOKEN_CLIENT',gid,client_uid,server_uid,cn))
    if _recv_all(sock,5)!=b'XTP3\x03':raise ValueError('Invalid XTP3 server magic')
    claimed=read_string(sock)
    if claimed!=server_uid:raise ValueError('Incorrect server identity')
    sn=_recv_all(sock,32)
    result=_recv_all(sock,32)
    if not hmac.compare_digest(result,proof(key,'TOKEN_SERVER',gid,client_uid,server_uid,cn,sn)):
        raise ValueError('Mesh server authentication failure')
    c2s,s2c,prefix=derive(key,'TOKEN:'+gid,client_uid,server_uid,cn,sn)
    return Channel(sock,s2c,c2s,prefix,'TOKEN:'+gid,'S2C','C2S')


def server_handshake(sock,key,gid,own_uid):
    if _recv_all(sock,5)!=b'XTP3\x03':raise ValueError('Invalid XTP3 client magic')
    group=read_string(sock)
    if group!=gid:raise ValueError('Incorrect group')
    remote=read_string(sock);intended=read_string(sock)
    if not remote or intended!=own_uid:raise ValueError('Incorrect peer identity')
    cn=_recv_all(sock,32)
    result=_recv_all(sock,32)
    if not hmac.compare_digest(result,proof(key,'TOKEN_CLIENT',gid,remote,own_uid,cn)):
        raise ValueError('Mesh client authentication failure')
    sn=os.urandom(32)
    sock.sendall(b'XTP3\x03'+write_string(own_uid)+sn+proof(key,'TOKEN_SERVER',gid,remote,own_uid,cn,sn))
    c2s,s2c,prefix=derive(key,'TOKEN:'+gid,remote,own_uid,cn,sn)
    return remote,Channel(sock,c2s,s2c,prefix,'TOKEN:'+gid,'C2S','S2C')
