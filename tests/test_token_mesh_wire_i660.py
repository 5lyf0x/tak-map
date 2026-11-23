import base64,hashlib,json,socket,tempfile,threading,time,unittest,uuid
from token_mesh_wire_i660 import *
from token_mesh_i660 import MeshStore,encode_invite
from token_mesh_transport_i660 import MeshTransport

class WireTests(unittest.TestCase):
 def test_datagram(self):
  gid=str(uuid.uuid4());key=b'Z'*32;msg=b'{"type":"TOKEN_HELLO"}'
  self.assertEqual(datagram_decrypt(datagram_encrypt(gid,key,msg),gid,key),msg)
  with self.assertRaises(Exception):datagram_decrypt(datagram_encrypt(gid,key,msg),gid,b'A'*32)
 def test_socket_handshake_and_records(self):
  gid=str(uuid.uuid4());key=b'X'*32
  server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1)
  errors=[]
  def handler():
   try:
    conn,_=server.accept();conn.settimeout(3)
    with conn:
     uid,ch=server_handshake(conn,key,gid,'device-b')
     self.assertEqual(uid,'device-a')
     self.assertEqual(ch.recv()['type'],'TOKEN_PING')
     ch.send({'type':'TOKEN_PONG','uid':'device-b'})
   except Exception as e:errors.append(e)
  t=threading.Thread(target=handler);t.start()
  with socket.create_connection(server.getsockname(),timeout=3) as c:
   ch=client_handshake(c,key,gid,'device-a','device-b')
   ch.send({'type':'TOKEN_PING'})
   self.assertEqual(ch.recv()['uid'],'device-b')
  t.join(timeout=5);server.close();self.assertFalse(errors,errors)
 def test_two_store_mission_sync(self):
  with tempfile.TemporaryDirectory() as a_dir,tempfile.TemporaryDirectory() as b_dir:
   a=MeshStore(a_dir);b=MeshStore(b_dir)
   ga=a.create('Test');b.join(ga['invite'])
   mid=str(uuid.uuid4());m={'v':1,'missionId':mid,'missionName':'M','serverIdentity':'local','key':base64.b64encode(b'K'*32).decode()}
   mt='XMS1:'+base64.urlsafe_b64encode(json.dumps(m).encode()).decode().rstrip('=')
   a.mission_join(mt);b.mission_join(mt)
   a.local_op(mid,'POINT','a','ADD',b'<event uid="a"/>')
   b.local_op(mid,'POINT','b','ADD',b'<event uid="b"/>')
   net_a=MeshTransport(a);net_b=MeshTransport(b);net_b.running=True;net_b._bind(b.group())
   try:
    p={'uid':b.device_uid(),'address':'127.0.0.1','port':net_b.port}
    net_a._client_session(p,a.group(),mid,(p['uid'],mid))
    self.assertEqual(len(a.heads(mid)),2)
    self.assertEqual(len(b.heads(mid)),2)
    self.assertEqual(set(a.water(mid)),set(b.water(mid)))
    self.assertIsNotNone(net_a.last_success,(net_a.last_error,net_b.last_error))
   finally:
    net_b.running=False;net_b._close();net_a.executor.shutdown(wait=False);net_b.executor.shutdown(wait=True)
if __name__=='__main__':unittest.main()
