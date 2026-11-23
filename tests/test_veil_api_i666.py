"""Phase 2 contract, four-gate auth, credential, event reconciliation and WS checks."""
from pathlib import Path
import base64
import hashlib
import json
import os
import socket
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tak_map_veil_i665 import VeilReceiver
import tak_map_veil_api_i666 as a

NODE={'nodeId':'veil-node-a','name':'VEIL A','host':'192.168.1.77','port':8080,'scheme':'http','apiSubscribed':False}
TOKEN='test-token-which-is-long-enough'

def row(oid='adsb:A1B2C3',lat=34.1,when=None,sequence=3,service='adsb_1090'):
    when=time.time() if when is None else when
    return {'objectId':oid,'sourceService':service,'position':{'lat':lat,'lon':-118.4},
            'identity':{'callsign':'VEIL TEST'},'positionTimestamp':int(when*1000),
            'timestamp':int(when*1000),'ttlSeconds':150,'sequence':sequence,'freshnessState':'LIVE'}

class Phase2Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.rx=VeilReceiver(self.tmp.name)
        self.rx.nodes={NODE['nodeId']:dict(NODE)}
        self.rx.settings({'enabled':True})
        self.api=a.VeilApiSyncManager(self.rx)
        self.api._verify=lambda node:dict(NODE)
    def tearDown(self):
        self.api.stop()
        self.rx.stop()
        self.tmp.cleanup()
    def subscribe(self):
        self.rx.nodes[NODE['nodeId']]['apiSubscribed']=True
        self.rx._save()
    def auth_state(self):
        self.subscribe();self.api._state(NODE['nodeId'],'login_required',authRequired=True)
        self.api._auth_check=lambda node,token: (_ for _ in ()).throw(a.AuthRequired())
        return self.api.status()[NODE['nodeId']]['apiAuthGeneration']
    def test_migrated_node_udp_only(self):
        self.assertFalse(self.rx.nodes[NODE['nodeId']]['apiSubscribed'])
        self.assertEqual(self.api.status()[NODE['nodeId']]['apiState'],'udp_only')
    def test_no_prompt_when_no_subscription(self):
        g=self.auth_state();self.rx.nodes[NODE['nodeId']]['apiSubscribed']=False
        self.assertFalse(self.api.prompt_check(NODE['nodeId'],g)['show'])
    def test_no_prompt_while_disabled(self):
        g=self.auth_state();self.rx.settings({'enabled':False})
        self.assertFalse(self.api.prompt_check(NODE['nodeId'],g)['show'])
    def test_no_prompt_offline(self):
        g=self.auth_state()
        self.api._verify=lambda node: (_ for _ in ()).throw(a.NodeUnavailable())
        self.assertFalse(self.api.prompt_check(NODE['nodeId'],g)['show'])
    def test_no_prompt_if_auth_valid(self):
        g=self.auth_state();self.api._auth_check=lambda node,token:{'nodeId':NODE['nodeId']}
        self.assertFalse(self.api.prompt_check(NODE['nodeId'],g)['show'])
    def test_only_confirmed_reachable_subscriber_prompts(self):
        g=self.auth_state()
        self.assertTrue(self.api.prompt_check(NODE['nodeId'],g)['show'])
    def test_old_auth_generation_not_promoted(self):
        g=self.auth_state();self.assertFalse(self.api.prompt_check(NODE['nodeId'],g+1)['show'])
    def test_no_duplicate_generation_same_transition(self):
        g=self.auth_state();self.api._state(NODE['nodeId'],'login_required',authRequired=True)
        self.assertEqual(self.api.status()[NODE['nodeId']]['apiAuthGeneration'],g)
    def test_status_contains_no_secrets(self):
        self.api.tokens[NODE['nodeId']]=TOKEN
        self.api.credentials[NODE['nodeId']]={'username':'admin','password':'SECRET123'}
        self.assertNotIn('SECRET123',json.dumps(self.api.status()))
        self.assertNotIn(TOKEN,json.dumps(self.api.status()))
    def test_pair_explicit_subscription_and_opt_in_secret(self):
        with patch.object(a,'_http',side_effect=lambda node,path,**kwargs:{'authenticated':True,'token':TOKEN} if path.endswith('/admin/login') else {'nodeId':NODE['nodeId']}):
            p=self.api.pair(NODE['nodeId'],'admin','my-secret',remember=True)
        self.assertTrue(p['apiSubscribed'])
        self.assertTrue(self.rx.nodes[NODE['nodeId']]['apiSubscribed'])
        self.assertEqual(self.api.tokens[NODE['nodeId']],TOKEN)
        self.assertEqual(os.stat(self.api.secrets_file).st_mode & 0o777,0o600)
        self.assertEqual(json.loads(self.api.secrets_file.read_text())[NODE['nodeId']]['password'],'my-secret')
        self.assertNotIn('my-secret',json.dumps(self.rx.status()))
    def test_pair_no_remember_never_writes_password(self):
        with patch.object(a,'_http',side_effect=lambda node,path,**kwargs:{'authenticated':True,'token':TOKEN} if path.endswith('/admin/login') else {'nodeId':NODE['nodeId']}):
            self.api.pair(NODE['nodeId'],'admin','secret',remember=False)
        self.assertFalse(self.api.credentials)
        self.assertNotIn('secret',self.rx.file.read_text())
    def test_unpair_removes_subscription_and_secret(self):
        self.subscribe();self.api.credentials[NODE['nodeId']]={'username':'a','password':'b'}
        self.api._save_secrets();self.api.unpair(NODE['nodeId'])
        self.assertFalse(self.rx.nodes[NODE['nodeId']]['apiSubscribed'])
        self.assertFalse(self.api.credentials)
        self.assertEqual(json.loads(self.api.secrets_file.read_text()),{})
    def test_off_clears_auth_token_and_prompt(self):
        g=self.auth_state();self.api.tokens[NODE['nodeId']]=TOKEN
        self.rx.settings({'enabled':False});self.api.on_toggle()
        self.assertEqual(self.api.tokens,{})
        self.assertFalse(self.api.status()[NODE['nodeId']]['apiAuthRequired'])
    def test_valid_adsb_snapshot_row_maps_marker(self):
        o=a.normalize_object(NODE['nodeId'],row())
        self.assertEqual(o['service'],'adsb');self.assertEqual(o['lat'],34.1)
        self.assertEqual(o['title'],'VEIL TEST')
    def test_no_position_no_marker(self):
        r=row();r.pop('position')
        self.assertIsNone(a.normalize_object(NODE['nodeId'],r))
    def test_invalid_coordinates_rejected(self):
        self.assertIsNone(a.normalize_object(NODE['nodeId'],row(lat=999)))
    def test_old_position_does_not_overwrite_newer(self):
        self.subscribe();t=time.time()
        self.assertTrue(self.api._apply_upsert(NODE['nodeId'],row(lat=34.3,when=t,sequence=5)))
        self.assertFalse(self.api._apply_upsert(NODE['nodeId'],row(lat=34.2,when=t-20,sequence=9)))
        self.assertAlmostEqual(self.rx.objects[(NODE['nodeId'],'adsb:A1B2C3')]['lat'],34.3)
    def test_snapshot_event_share_one_store_key(self):
        self.subscribe();self.api._apply_upsert(NODE['nodeId'],row(),transport='api_snapshot')
        self.api._apply_upsert(NODE['nodeId'],row(sequence=4),transport='api_event')
        self.assertEqual(len(self.rx.objects),1)
    def test_cross_node_not_deduplicated_in_phase2(self):
        self.subscribe();self.rx.nodes['veil-node-b']=dict(NODE,nodeId='veil-node-b',apiSubscribed=True)
        self.api._apply_upsert(NODE['nodeId'],row())
        self.api._apply_upsert('veil-node-b',row())
        self.assertEqual(len(self.rx.objects),2)
    def test_expire_only_api_record(self):
        self.subscribe();self.api._apply_upsert(NODE['nodeId'],row())
        self.api._expire(NODE['nodeId'],'adsb:A1B2C3')
        self.assertEqual(self.rx.objects,{})
    def test_expire_preserves_fresh_udp(self):
        self.subscribe();self.api._apply_upsert(NODE['nodeId'],row())
        self.rx.objects[(NODE['nodeId'],'adsb:A1B2C3')]['transport']='udp'
        self.api._expire(NODE['nodeId'],'adsb:A1B2C3')
        self.assertEqual(len(self.rx.objects),1)
    def test_replay_duplicate_and_gap(self):
        self.subscribe()
        e=lambda seq,boot='boot-1':{'stream':'events','type':'live_sa','action':'update','nodeId':NODE['nodeId'],
                                   'sequence':seq,'bootId':boot,'payload':row()}
        self.api._apply_envelope(NODE['nodeId'],e(11));self.api._apply_envelope(NODE['nodeId'],e(11))
        self.assertEqual(self.api.event_cursors[NODE['nodeId']],('boot-1',11))
        with self.assertRaises(a.ResyncRequired):self.api._apply_envelope(NODE['nodeId'],e(14))
        with self.assertRaises(a.ResyncRequired):self.api._apply_envelope(NODE['nodeId'],e(12,'boot-2'))
    def test_fault_requires_resnapshot(self):
        with self.assertRaises(a.ResyncRequired):self.api._apply_envelope(NODE['nodeId'],{'type':'fault','action':'resync_required'})
    def test_remembered_silent_login(self):
        self.subscribe();self.api.credentials[NODE['nodeId']]={'username':'admin','password':'saved'}
        with patch.object(a,'_http',side_effect=lambda node,path,**kwargs:{'authenticated':True,'token':TOKEN} if path.endswith('login') else {'nodeId':NODE['nodeId']}):
            token,caps=self.api._ensure_token(self.rx.nodes[NODE['nodeId']])
        self.assertEqual(token,TOKEN);self.assertEqual(caps['nodeId'],NODE['nodeId'])
    def test_invalid_saved_login_not_retried_forever(self):
        self.subscribe();self.api.credentials[NODE['nodeId']]={'username':'admin','password':'bad'}
        counts=[]
        def fake(node,path,**kwargs):
            counts.append(path)
            raise a.AuthRequired()
        with patch.object(a,'_http',side_effect=fake):
            for i in range(2):
                with self.assertRaises(a.AuthRequired):self.api._ensure_token(self.rx.nodes[NODE['nodeId']])
        self.assertEqual(counts.count('/api/v1/admin/login'),1)
    def test_two_node_state_isolation(self):
        self.subscribe();self.rx.nodes['veil-node-b']=dict(NODE,nodeId='veil-node-b',apiSubscribed=False)
        self.api._state(NODE['nodeId'],'login_required',authRequired=True)
        self.assertEqual(self.api.status()['veil-node-b']['apiState'],'udp_only')
    def test_no_external_python_dependency(self):
        self.assertNotIn('websocket',Path(__file__).resolve().parents[1].joinpath('requirements.txt').read_text())

class WebsocketContract(unittest.TestCase):
    def test_rfc6455_handshake_and_message(self):
        server=socket.socket();server.bind(('127.0.0.1',0));server.listen(1);port=server.getsockname()[1]
        messages=[]
        def handle():
            conn,_=server.accept()
            try:
                conn.settimeout(3);req=b''
                while b'\r\n\r\n' not in req:req+=conn.recv(4096)
                raw=req.decode('latin1')
                self.assertIn('Authorization: Bearer test-token',raw)
                key=raw.split('Sec-WebSocket-Key: ',1)[1].split('\r\n',1)[0]
                accept=base64.b64encode(hashlib.sha1((key+'258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest()).decode()
                conn.sendall(('HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Accept: '+accept+'\r\n\r\n').encode())
                # Send a ping followed by one text frame.
                data=json.dumps({'type':'live_sa','action':'update','sequence':7}).encode()
                conn.sendall(bytes([0x89,2])+b'hi'+bytes([0x81,len(data)])+data)
                messages.append(True)
            finally:conn.close();server.close()
        th=threading.Thread(target=handle,daemon=True);th.start()
        with patch.object(a,'_network',return_value=('127.0.0.1',port)):
            ws=a.VeilWebSocket(NODE,'test-token');event=ws.receive();ws.close()
        th.join(timeout=2)
        self.assertEqual(event['sequence'],7);self.assertTrue(messages)

if __name__=='__main__':unittest.main()
