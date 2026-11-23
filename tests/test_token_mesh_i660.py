import base64, hashlib, json, tempfile, uuid, unittest
from token_mesh_i660 import MeshStore, decode_invite, encode_invite, head_rank, invite_png

class MeshTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.s=MeshStore(self.tmp.name);self.s.create('TEST');self.mid=str(uuid.uuid4())
  m={'v':1,'missionId':self.mid,'missionName':'Mission','key':base64.b64encode(b'A'*32).decode(),'serverIdentity':'test'}
  self.s.mission_join('XMS1:'+base64.urlsafe_b64encode(json.dumps(m).encode()).decode().rstrip('='))
 def op(self,seq,uid='p',rev=None,typ='ADD',baseline=False):
  p=b'<event/>' if typ!='REMOVE' else b''
  return ({'missionId':self.mid,'origin':'remote','seq':seq,'rev':seq if rev is None else rev,'opId':str(uuid.uuid4()),'kind':'POINT','uid':uid,'type':typ,'payloadHash':hashlib.sha256(p).hexdigest(),'payloadSize':len(p),'baseline':baseline,'repair':False},p)
 def test_invite_and_png(self):
  g=self.s.group();self.assertEqual(decode_invite(encode_invite(g)),g);self.assertTrue(invite_png(g).startswith(b'\x89PNG'))
  self.assertEqual(self.s.device_uid(),MeshStore(self.tmp.name).device_uid())
 def test_gap_then_fill(self):
  for seq in (1,2,4):self.s.receive(*self.op(seq,str(seq)))
  self.assertEqual(self.s.water(self.mid)['remote'],2)
  self.s.receive(*self.op(3,'3'));self.assertEqual(self.s.water(self.mid)['remote'],4)
 def test_baseline_tombstone_restart(self):
  self.s.receive(*self.op(1,rev=5));self.s.receive(*self.op(2,rev=99,baseline=True))
  self.assertEqual(self.s.heads(self.mid)[0]['operation']['rev'],5)
  self.s.receive(*self.op(3,rev=10,typ='REMOVE'))
  self.assertTrue(MeshStore(self.tmp.name).heads(self.mid)[0]['tombstone'])
 def test_replay_collision_hash(self):
  op,data=self.op(1);self.s.receive(op,data);self.assertTrue(self.s.receive(op,data)['duplicate'])
  with self.assertRaises(ValueError):self.s.receive(dict(op,opId=str(uuid.uuid4())),data)
  with self.assertRaises(ValueError):self.s.receive(dict(op,seq=2,opId=str(uuid.uuid4())),b'invalid')
 def test_leave_and_status_secret(self):
  secret=self.s.group()['key'];self.assertNotIn(secret,json.dumps(self.s.status()))
  self.s.receive(*self.op(1));self.s.leave();self.assertFalse(self.s.status()['enrolled'])
  self.assertEqual(len(self.s.heads(self.mid)),1)
 def test_comparator(self):
  x=self.op(1)[0];y=dict(x,origin='other',opId=str(uuid.uuid4()))
  self.assertNotEqual(head_rank(x),head_rank(y));self.assertLess(head_rank(dict(y,baseline=True,rev=999)),head_rank(x))
 def test_invalid_join_safe(self):
  before=self.s.group()
  with self.assertRaises(ValueError):self.s.join('XTM1:wrong')
  self.assertEqual(self.s.group(),before)
if __name__=='__main__':unittest.main()
