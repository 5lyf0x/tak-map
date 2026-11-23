"""i685 infrastructure persistence, streaming, imports/exports, sewer filtering and resumable jobs."""
import json, os, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import tak_map_infrastructure_i685 as infra


def sample(n=1,diam=48):
    return {'type':'Feature','id':str(n),'geometry':{'type':'LineString','coordinates':[[-118.6,34.1],[-118.5,34.2]]},'properties':{'PIPE_DIAMETER':diam,'PIPE_MATERIAL':'RCP','NAME':'Test main'}}

class InfrastructureTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='infra-i685-')
        self.old=os.environ.get('TAK_MAP_INFRA_DIR')
        os.environ['TAK_MAP_INFRA_DIR']=self.temp.name
    def tearDown(self):
        if self.old is None:os.environ.pop('TAK_MAP_INFRA_DIR',None)
        else:os.environ['TAK_MAP_INFRA_DIR']=self.old
        self.temp.cleanup()
    def test_category_catalog_both_modes_and_hide_restore(self):
        state=infra.catalog()
        self.assertEqual(len(state['categories']),14)
        self.assertTrue(any(x['id']=='water' for x in state['categories']))
        self.assertTrue(any(x['id']=='bridges' for x in state['categories']))
        self.assertTrue(any(x['mode']=='online' for x in state['layers']))
        state=infra.mutate({'op':'category-create','name':'County Utilities'})
        cat=next(x for x in state['categories'] if x['label']=='County Utilities')
        state=infra.mutate({'op':'category-hide','id':cat['id'],'hidden':True})
        self.assertTrue(next(x for x in state['categories'] if x['id']==cat['id'])['hidden'])
        state=infra.mutate({'op':'category-hide','id':cat['id'],'hidden':False})
        self.assertFalse(next(x for x in state['categories'] if x['id']==cat['id'])['hidden'])
        state=infra.mutate({'op':'layer-delete','id':'lacounty-sewer-mains'})
        self.assertTrue(next(x for x in state['layers'] if x['id']=='lacounty-sewer-mains')['hidden'])
        self.assertTrue(next(x for x in infra.catalog()['layers'] if x['id']=='lacounty-sewer-mains')['hidden'])
    def test_sewer_36_filter_and_spatial_index(self):
        f=Path(self.temp.name)/'sewer.geojson'
        data=[sample('a',35),sample('b',36),sample('c',48),sample('d','914.4 mm'),sample('e','900 mm')]
        f.write_text(json.dumps({'type':'FeatureCollection','features':data}))
        out=infra.import_dataset(f,'water','Sewer Dataset','sewer')
        self.assertEqual(out['count'],5)
        identifier=out['layer_id']
        result=infra.get_features(identifier,'offline',[-119,34,-118,35],36)
        self.assertEqual({x['id'] for x in result['features']},{'b','c','d'})
        result=infra.get_features(identifier,'offline',[-119,34,-118,35],48)
        self.assertEqual({x['id'] for x in result['features']},{'c'})
        result=infra.get_features(identifier,'offline',[-119,34,-118,35],0)
        self.assertEqual(len(result['features']),5)
        result=infra.get_features(identifier,'offline',[-120,33,-119,34],0)
        self.assertFalse(result['features'])
        with self.assertRaises(ValueError):infra.get_features(identifier,'online',[-119,34,-118,35],0)
    def test_export_import_round_trip(self):
        f=Path(self.temp.name)/'points.geojson'
        f.write_text(json.dumps({'type':'FeatureCollection','features':[
            {'type':'Feature','id':'p1','geometry':{'type':'Point','coordinates':[-118.6,34.2]},'properties':{'name':'First','PIPE_DIAMETER':48}},
            {'type':'Feature','id':'p2','geometry':{'type':'Point','coordinates':[-118.4,34.0]},'properties':{'name':'Second','PIPE_DIAMETER':60}}]}))
        original=infra.import_dataset(f,'water','Test Dataset','sewer')
        for fmt in ('geojson','gpkg','zip','kml','kmz'):
            export=infra.export_dataset(original['layer_id'],fmt)
            self.assertTrue(export.exists(),fmt)
            result=infra.import_dataset(export,'water','Round Trip '+fmt,'sewer')
            self.assertEqual(result['count'],2,fmt)
    def test_download_jobs_stage_commit_resume_and_keep_previous(self):
        previous=Path(self.temp.name)/'seed.geojson'
        previous.write_text(json.dumps({'type':'FeatureCollection','features':[sample('saved',60)]}))
        saved=infra.import_dataset(previous,'water','Existing Download','sewer')['layer_id']
        calls={'n':0}
        def fake(source,bbox,offset=0,count=1000):
            calls['n']+=1
            if calls['n']==1:raise RuntimeError('temporary failure')
            if offset==0:return {'features':[sample(i,48) for i in range(1000)]}
            return {'features':[sample('last',60)]} if offset==1000 else {'features':[]}
        with patch.object(infra,'_query_online',side_effect=fake):
            result=infra.job_action({'op':'download-start','source_id':'lacounty-sewer-mains','bbox':[-119,34,-118,35]})
            job=result['job_id']
            thread=infra.ACTIVE.get(job)
            if thread:thread.join(timeout=10)
            state=infra.catalog()
            self.assertEqual(next(x for x in state['jobs'] if x['id']==job)['status'],'interrupted')
            result=infra.job_action({'op':'download-resume','id':job})
            thread=infra.ACTIVE.get(job)
            if thread:thread.join(timeout=10)
        state=infra.catalog()
        self.assertEqual(next(x for x in state['jobs'] if x['id']==job)['status'],'complete')
        layer_id='offline-'+job
        downloaded=infra.get_features(layer_id,'offline',[-119,34,-118,35],36)
        self.assertEqual(len(downloaded['features']),1001)
        self.assertEqual(len(infra.get_features(saved,'offline',[-119,34,-118,35],36)['features']),1)
    def test_cancel_download_never_promotes_staging_and_is_retry_safe(self):
        from threading import Event
        started,release=Event(),Event()
        def held_page(source,bbox,offset=0,count=1000):
            started.set()
            self.assertTrue(release.wait(timeout=10))
            return {'features':[sample('delayed',48)]}
        with patch.object(infra,'_query_online',side_effect=held_page):
            result=infra.job_action({'op':'download-start','source_id':'lacounty-sewer-mains','bbox':[-119,34,-118,35]})
            job=result['job_id']
            self.assertTrue(started.wait(timeout=10))
            stopped=infra.job_action({'op':'download-cancel','id':job})
            self.assertEqual(stopped['status'],'canceled')
            release.set()
            thread=infra.ACTIVE.get(job)
            if thread:thread.join(timeout=10)
        state=infra.catalog()
        self.assertEqual(next(x for x in state['jobs'] if x['id']==job)['status'],'canceled')
        self.assertFalse(any(x['id']=='offline-'+job for x in state['layers']))
        with infra._db() as c:
            self.assertEqual(c.execute('SELECT COUNT(*) FROM features WHERE layer_id=?',('staging-'+job,)).fetchone()[0],0)

    def test_protect_local_provider_urls(self):
        for url in ('http://127.0.0.1/FeatureServer/0','file:///etc/passwd',
            'https://localhost/FeatureServer/0','https://127.0.0.1/FeatureServer/0'):
            with self.subTest(url=url),self.assertRaises(ValueError):infra._source_url(url)

if __name__=='__main__':unittest.main()
