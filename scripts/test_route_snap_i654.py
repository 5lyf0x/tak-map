"""Non-network tests for the i654 nearest-road API adapter."""
import io
import json
import pathlib
import sys
import unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import ndm_valhalla_i651 as router

class Resp:
    status=200
    def __init__(self,data):self.data=data
    def __enter__(self):return self
    def __exit__(self,*a):return False
    def read(self,n):return self.data

class SnapTests(unittest.TestCase):
    def test_nearest_endpoint_used(self):
        out=[{'edges':[{'correlated_lat':34.005,'correlated_lon':-118.0},
                       {'correlated_lat':34.00001,'correlated_lon':-118.00002}]}]
        def fake(req,timeout):
            assert req.full_url=='http://127.0.0.1:18882/locate'
            assert req.get_method()=='POST'
            payload=json.loads(req.data)
            assert payload['costing']=='auto'
            assert len(payload['locations'])==1
            return Resp(json.dumps(out).encode())
        with patch.object(router.urllib.request,'urlopen',fake):
            r=router.snap_nearest_road(34,-118)
        assert r['lat']==34.00001
        assert r['lon']==-118.00002
        assert r['distance_m']<4
    def test_empty_response(self):
        with patch.object(router.urllib.request,'urlopen',return_value=Resp(b'[{}]')):
            with self.assertRaises(router.NDMError):router.snap_nearest_road(34,-118)
    def test_invalid_coordinates(self):
        with self.assertRaises(router.NDMError):router.snap_nearest_road(100,0)
        with self.assertRaises(router.NDMError):router.snap_nearest_road(float('nan'),0)
    def test_upstream_unavailable(self):
        import urllib.error
        with patch.object(router.urllib.request,'urlopen',side_effect=urllib.error.URLError('unavailable')):
            with self.assertRaises(router.NDMError) as ex:router.snap_nearest_road(34,-118)
            assert ex.exception.code=='ROUTER_UNAVAILABLE'
    def test_unrestricted_route_is_opt_in(self):
        def route_request(req,timeout):
            body=json.loads(req.data)
            assert req.full_url=='http://127.0.0.1:18882/route'
            assert body['costing_options']['auto']['ignore_access'] is True
            assert body['costing_options']['auto']['ignore_oneways'] is True
            assert body['costing_options']['auto']['ignore_restrictions'] is True
            assert body['costing_options']['auto']['exclude_unpaved'] is False
            return Resp(json.dumps({'trip':{'legs':[{'shape':'encoded'}],'summary':{'length':1}}}).encode())
        with patch.object(router.urllib.request,'urlopen',route_request),patch.object(router,'_decode_polyline6',lambda s:[[-118,34],[-118.01,34.01]]):
            result=router.route([{'lat':34,'lon':-118},{'lat':34.01,'lon':-118.01}],mode='roads',unrestricted=True)
        assert result['ok'] and len(result['geometry']['coordinates'])==2
    def test_legacy_route_still_uses_original_costing(self):
        def route_request(req,timeout):
            body=json.loads(req.data)
            assert 'costing_options' not in body
            return Resp(json.dumps({'trip':{'legs':[{'shape':'encoded'}],'summary':{'length':1}}}).encode())
        with patch.object(router.urllib.request,'urlopen',route_request),patch.object(router,'_decode_polyline6',lambda s:[[-118,34],[-118.01,34.01]]):
            router.route([{'lat':34,'lon':-118},{'lat':34.01,'lon':-118.01}],mode='roads')

if __name__=='__main__':unittest.main()
