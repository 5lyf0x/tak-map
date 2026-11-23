"""Offline VEIL r50-compatible CoT and multi-node receiver checks (no actual hardware)."""
import pathlib
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from tak_map_veil_i665 import VeilReceiver, _stamp, _endpoint, discover, probe

NODES=[{'nodeId':'node-a','name':'A','host':'192.168.1.57','port':8080},
       {'nodeId':'node-b','name':'B','host':'192.168.1.58','port':8080}]
def cot(node='node-a',service='adsb',oid='abc123',t=None,seq=1,stale=None,lat=34.1, lon=-118.5,aprs=False):
    now=time.time();t=now if t is None else t
    root=ET.Element('event',{'version':'2.0','uid':'VEIL-'+node+'-'+oid,'type':'a-u-A-C-F','how':'m-g',
                     'time':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(t)),
                     'stale':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime(stale if stale is not None else now+180))})
    ET.SubElement(root,'point',{'lat':str(lat),'lon':str(lon),'hae':'1400','ce':'1','le':'1'})
    detail=ET.SubElement(root,'detail');ET.SubElement(detail,'contact',{'callsign':'TEST'})
    ET.SubElement(detail,'track',{'speed':'55.0','course':'280'})
    ET.SubElement(detail,'remarks').text='<not markup> TEST'
    xt=ET.SubElement(detail,'xtak_veil',{'version':'1','node':node,'service':service,
                  'objectId':oid,'sequence':str(seq),'freshnessState':'LIVE','positionTimestamp':str(int(t*1000))})
    if aprs:ET.SubElement(xt,'aprs_symbol',{'symbolCode':'_','symbolTable':'/','weather':'true'})
    ET.SubElement(xt,'enrichment',{'hex':'ABC123','schema':'1'})
    return ET.tostring(root,encoding='utf-8')

class VeilTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.v=VeilReceiver(self.temp.name)
        self.v.nodes={n['nodeId']:dict(n) for n in NODES}
        self.v.settings({'enabled':True})
    def tearDown(self):self.v.stop();self.temp.cleanup()
    def test_parse_datetime(self):self.assertIsNotNone(_stamp('2026-11-07T10:00:00Z'))
    def test_private_addresses(self):
        self.assertEqual(_endpoint('192.168.1.57',8080)[0],'192.168.1.57')
        for host in ['127.0.0.1','169.254.169.254','8.8.8.8','localhost','bad.com']:
            with self.assertRaises(ValueError):_endpoint(host,8080)
    def test_first_packet(self):
        self.assertTrue(self.v.ingest(cot(),NODES[0]['host']))
        self.assertEqual(self.v.status()['counts']['adsb'],1)
        self.assertEqual(self.v.snapshot()['objects'][0]['heading'],'280')
    def test_actual_r50_adsb_source_service(self):
        self.assertTrue(self.v.ingest(cot(service='adsb_1090'),NODES[0]['host']))
        self.assertEqual(self.v.status()['counts']['adsb'],1)
    def test_multi_node(self):
        self.v.ingest(cot(),NODES[0]['host']);self.v.ingest(cot(node='node-b',service='ais'),NODES[1]['host'])
        self.assertEqual(self.v.status()['objectsCount'],2)
    def test_node_ip_verification(self):self.assertFalse(self.v.ingest(cot(),NODES[1]['host']))
    def test_unknown_node(self):self.assertFalse(self.v.ingest(cot(node='unknown'),NODES[0]['host']))
    def test_duplicate_timestamp_and_sequence(self):
        fixed=time.time()-5
        self.v.ingest(cot(t=fixed,seq=4,lat=34.1),NODES[0]['host'])
        self.v.ingest(cot(t=fixed,seq=2,lat=45.0),NODES[0]['host'])
        self.assertEqual(self.v.snapshot()['objects'][0]['lat'],34.1)
    def test_older_new_sequence_cannot_rollback(self):
        fixed=time.time()-4
        self.v.ingest(cot(t=fixed,seq=4,lat=34.1),NODES[0]['host'])
        self.v.ingest(cot(t=fixed-1,seq=5,lat=45),NODES[0]['host'])
        self.assertEqual(self.v.snapshot()['objects'][0]['lat'],34.1)
    def test_newer_position_updates(self):
        fixed=time.time()-5
        self.v.ingest(cot(t=fixed,seq=2,lat=34.1),NODES[0]['host'])
        self.v.ingest(cot(t=fixed+2,seq=3,lat=34.2),NODES[0]['host'])
        self.assertEqual(self.v.snapshot()['objects'][0]['lat'],34.2)
    def test_invalid_coordinate(self):self.assertFalse(self.v.ingest(cot(lat=999),NODES[0]['host']))
    def test_invalid_xml(self):self.assertFalse(self.v.ingest(b'<!DOCTYPE x [<!ENTITY y "oops">]><event/>',NODES[0]['host']))
    def test_stale_rejection(self):self.assertFalse(self.v.ingest(cot(stale=time.time()-120),NODES[0]['host']))
    def test_aprs_symbol(self):
        self.v.ingest(cot(service='aprs',aprs=True),NODES[0]['host'])
        self.assertEqual(self.v.snapshot()['objects'][0]['aprs']['weather'],'true')
    def test_remote_id(self):
        self.v.ingest(cot(service='remoteId'),NODES[0]['host'])
        self.assertEqual(self.v.status()['counts']['remote_id'],1)
    def test_disable_preserves_nodes(self):
        self.v.ingest(cot(),NODES[0]['host']);self.v.settings({'enabled':False})
        self.assertEqual(self.v.snapshot()['objects'],[])
        self.assertEqual(len(self.v.status()['nodes']),2)
    def test_persist_restart(self):
        v=VeilReceiver(self.temp.name)
        self.assertEqual(len(v.status()['nodes']),2)
        self.assertEqual(v.status()['config']['enabled'],True)
    def test_no_packet_when_disabled(self):
        self.v.settings({'enabled':False})
        self.assertFalse(self.v.ingest(cot(),NODES[0]['host']))
    def test_rejected_missing_veil(self):
        p=cot().replace(b'xtak_veil',b'not_veil')
        self.assertFalse(self.v.ingest(p,NODES[0]['host']))
    def test_batch_add_dedup(self):
        self.v.nodes={};self.v._save()
        def fake(host,port,scheme):
            return dict(NODES[0],scheme='http',verified=True,nodeVersion='r50',services=[])
        with patch('tak_map_veil_i665.probe',side_effect=fake):
            result=self.v.add([{'host':'192.168.1.57'},{'host':'192.168.1.57'}])
        self.assertTrue(result['ok']);self.assertEqual(len(self.v.nodes),1)
    def test_remove_node_objects(self):
        self.v.ingest(cot(),NODES[0]['host']);self.v.remove('node-a')
        self.assertEqual(len(self.v.snapshot()['objects']),0)
    def test_discover_missing_avahi(self):
        with patch('tak_map_veil_i665.shutil.which',return_value=None):
            self.assertFalse(discover()['ok'])

if __name__=='__main__':unittest.main()
