#!/usr/bin/env python3
import unittest,io,time,tempfile,json,threading,sqlite3,sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import tak_map_offline_regions_i698 as regions
import tak_map_offline_downloader_i698 as download
import tak_dashboard as dashboard

PNG=bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000b49444154789c636000020000050001a5f645400000000049454e44ae426082')

class Handler(BaseHTTPRequestHandler):
    requests={};fail=True
    def log_message(self,*args):pass
    def do_GET(self):
        Handler.requests[self.path]=Handler.requests.get(self.path,0)+1
        if Handler.fail and self.path.endswith('/3/2/3'):
            self.send_response(503);self.end_headers();self.wfile.write(b'fail');return
        self.send_response(200);self.send_header('Content-Type','image/png');self.send_header('Content-Length',str(len(PNG)));self.end_headers();self.wfile.write(PNG)

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
    @classmethod
    def tearDownClass(cls):cls.server.shutdown();cls.server.server_close()
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
        p=Path(self.t.name)
        self.h=dict(dashboard.__dict__)
        self.h['TAK_MAP_OFFLINE_DIR']=p
        self.h['TAK_MAP_OFFLINE_FILE']=p/'offline_maps.json'
        self.h['TAK_MAP_OFFLINE_DOWNLOAD_MAX_TILES']=3
        self.h['TAK_MAP_OFFLINE_DOWNLOAD_CONCURRENCY']=2
        self.h['TAK_MAP_OFFLINE_DOWNLOAD_JOBS']={}
        self.h['TAK_MAP_OFFLINE_DOWNLOAD_LOCK']=threading.RLock()
        self.h['TAK_MAP_BASEMAPS']=[{'id':'fixture','label':'Fixture','group':'Test','url':f'http://127.0.0.1:{self.server.server_port}/{{z}}/{{x}}/{{y}}','maxZoom':19}]
        self.h['_i505_load_custom_basemaps']=lambda:[]
        # Bind record helpers to local globals by running original code objects in
        # a test-only isolated namespace with helper globals redirected.
        self.h['_load_offline_maps']=lambda:json.loads(self.h['TAK_MAP_OFFLINE_FILE'].read_text()).get('maps',[]) if self.h['TAK_MAP_OFFLINE_FILE'].exists() else []
        def upsert(rec):
            rows=self.h['_load_offline_maps']();rows=[x for x in rows if x.get('id')!=rec.get('id')]+[rec]
            self.h['TAK_MAP_OFFLINE_FILE'].write_text(json.dumps({'maps':rows}));return rows
        self.h['_upsert_offline_map_record']=upsert
        self.h['_offline_map_record']=lambda mid:next((x for x in self.h['_load_offline_maps']() if x['id']==mid),None)
        self.h['_offline_record_from_job']=dashboard._offline_record_from_job
        self.h['tak_map_offline_eud_package']=lambda mid:None
        def update(jid,**kw):
            with self.h['TAK_MAP_OFFLINE_DOWNLOAD_LOCK']:
                self.h['TAK_MAP_OFFLINE_DOWNLOAD_JOBS'][jid].update(kw)
        self.h['_update_offline_job']=update
        self.engine=download.OfflineMapsI698(self.h)
        Handler.requests={};Handler.fail=True
    def wait(self,result):
        self.assertTrue(result['ok'],result)
        j=result['job'];id_=j['id'];deadline=time.monotonic()+15
        while time.monotonic()<deadline:
            job=self.h['TAK_MAP_OFFLINE_DOWNLOAD_JOBS'][id_]
            if job['status'] in ('done','error','paused','canceled'):return job
            time.sleep(.025)
        self.fail('Timed out waiting for worker')
    def test_all_us_states_and_ca_three_regions(self):
        choices=regions.catalog();self.assertEqual(len(choices),52)
        ids={c['id'] for c in choices};self.assertNotIn('CA',ids)
        self.assertTrue({'AK','HI','CA-N','CA-C','CA-S','WY'}<=ids)
    def test_polygon_clipping_and_internal_chunk_calculation(self):
        a=self.engine.estimate({'source_id':'fixture','area_id':'AZ','min_zoom':8,'max_zoom':8})
        self.assertTrue(a['ok'],a)
        self.assertGreater(a['internal_jobs'],1);self.assertLess(a['tile_count'],
            regions.tile_total('',a['bounds'],8,8))
        self.assertEqual(a['max_tiles'],3)
    def test_all_52_regions_have_tiles_and_alaska_dateline(self):
        for choice in regions.catalog():
            n=regions.tile_total(choice['id'],None,5,5)
            self.assertGreater(n,0,choice)
        alaska=regions.polygon_tile_spans('AK',8)
        xs=[a for _,a,b in alaska]+[b for _,a,b in alaska]
        self.assertLess(min(xs),10)
        self.assertGreater(max(xs),250)

    def test_failed_tile_manifest_and_targeted_retry(self):
        # 1x? at zoom 3 this bbox includes only the failing tile 3/2/3 and
        # neighbor tiles. We want a partial recovery with successful tiles.
        b={'west':-91,'south':0,'east':-1,'north':42}
        estimate=self.engine.estimate({'source_id':'fixture','bounds':b,'min_zoom':3,'max_zoom':3})
        self.assertTrue(estimate['ok'],estimate)
        job=self.wait(self.engine.start({'source_id':'fixture','bounds':b,'min_zoom':3,'max_zoom':3,'name':'One map'}))
        self.assertEqual(job['status'],'done',job)
        maps=self.h['_load_offline_maps']();self.assertEqual(len(maps),1)
        rec=maps[0];self.assertEqual(rec['name'],'One map')
        self.assertEqual(rec['internal_jobs'],estimate['internal_jobs'])
        c=sqlite3.connect(rec['path'])
        self.assertEqual(c.execute('select count(*) from offline_batches_i698').fetchone()[0],estimate['internal_jobs'])
        self.assertEqual(c.execute("select count(*) from offline_batches_i698 where status='checked'").fetchone()[0],estimate['internal_jobs'])
        c.close()
        self.assertEqual(rec['download_status'],'incomplete')
        self.assertEqual(rec['failed_tile_count'],1)
        self.assertEqual(Handler.requests.get('/3/2/3'),4,'initial + three retries')
        self.assertTrue(rec['retry_available'])
        self.assertTrue(self.engine.finish(rec['id'])['ok'])
        self.assertEqual(self.h['_load_offline_maps']()[0]['download_status'],'accepted_incomplete')
        count_before=sum(Handler.requests.values())
        Handler.fail=False
        retry=self.wait(self.engine.retry(rec['id']))
        self.assertEqual(retry['status'],'done',retry)
        rec2=self.h['_load_offline_maps']()[0]
        self.assertEqual(rec2['failed_tile_count'],0)
        self.assertEqual(rec2['requested_tile_count'],estimate['tile_count'])
        self.assertEqual(rec2['internal_jobs'],estimate['internal_jobs'])
        self.assertEqual(rec2['download_status'],'complete')
        self.assertEqual(sum(Handler.requests.values())-count_before,1,'retry missing tile only')
        self.assertEqual(len(self.h['_load_offline_maps']()),1)
        conn=sqlite3.connect(rec2['path']);self.assertEqual(conn.execute('select count(*) from offline_failed_tiles_i698').fetchone()[0],0);conn.close()

if __name__=='__main__':unittest.main(verbosity=2)
