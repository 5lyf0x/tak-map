import importlib.util
import json
from pathlib import Path
import pytest

MODULE=Path(__file__).resolve().parents[1]/'tak_map_backup_i674.py'
spec=importlib.util.spec_from_file_location('tak_map_backup_i674',MODULE)
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
PASSWORD='this-is-a-test-password-2026'

@pytest.fixture
def roots(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'DATA',tmp_path/'data');monkeypatch.setattr(b,'ETC',tmp_path/'etc')
    monkeypatch.setattr(b,'ENV',tmp_path/'config.env');monkeypatch.setattr(b,'BACKUPS',b.DATA/'backup_restore_i674')
    monkeypatch.setattr(b,'EXTRA',{'gateway_data':[b.ETC]})
    b.DATA.mkdir();b.ETC.mkdir()
    return tmp_path

def test_categories_exact():assert len(b.CATEGORIES)==13 and len(set(b.CATEGORIES))==13

def test_encrypt_corruption_and_password(roots):
    src=roots/'source';src.write_bytes(b'abc'*3000)
    dst=roots/'x.takmbk';b.encrypt(src,dst,PASSWORD)
    out=roots/'out';b.decrypt(dst,out,PASSWORD);assert out.read_bytes()==src.read_bytes()
    with pytest.raises(b.BackupError):b.decrypt(dst,roots/'wrong','a-different-password')
    corrupted=roots/'corrupt.takmbk';v=bytearray(dst.read_bytes());v[48]^=12;corrupted.write_bytes(v)
    with pytest.raises(b.BackupError):b.decrypt(corrupted,roots/'bad',PASSWORD)

def test_selective_roundtrip_no_unrelated_mutation(roots):
    p=b.DATA/'tak_map_offline';p.mkdir();(p/'adsb_settings.json').write_text('{"radius":31}')
    (p/'geofences.json').write_text('{"fences":["original"]}')
    (b.DATA/'gateway_data_connection.json').write_text('{"host":"gateway"}')
    a=b.create({'categories':['adsb','geofences'],'password':PASSWORD,'browser':{'adsb':{'localStorage':{'takmap.adsb.range':'31'}}}})
    assert b.inspect({'file':a['file'],'password':PASSWORD})['categories']==['adsb','geofences']
    (p/'adsb_settings.json').write_text('{"radius":9}')
    (p/'geofences.json').write_text('{"fences":["changed"]}')
    result=b.restore({'file':a['file'],'password':PASSWORD,'categories':['adsb'],'confirm':'RESTORE'})
    assert json.loads((p/'adsb_settings.json').read_text())['radius']==31
    assert json.loads((p/'geofences.json').read_text())['fences']==['changed']
    assert (b.DATA/'gateway_data_connection.json').read_text()=='{"host":"gateway"}'
    assert result['browser']['adsb']['localStorage']['takmap.adsb.range']=='31'

def test_independent_object_categories(roots):
    imp=b.DATA/'tak_map_imports';imp.mkdir()
    original={'imports':[{'id':'one','features':[{'kind':'point','object_id':'p1'},{'kind':'route','object_id':'r1'},{'kind':'shape','object_id':'s1'}]}]}
    (imp/'imports.json').write_text(json.dumps(original))
    out=b.create({'categories':['points'],'password':PASSWORD})
    original['imports'][0]['features'][0]['object_id']='changed'
    (imp/'imports.json').write_text(json.dumps(original))
    b.restore({'file':out['file'],'password':PASSWORD,'categories':['points'],'confirm':'RESTORE'})
    items=json.loads((imp/'imports.json').read_text())['imports'][0]['features']
    assert {x['object_id'] for x in items}=={'p1','r1','s1'}

def test_symlink_fail_closed(roots):
    outside=roots/'outside';outside.write_text('secret')
    (b.DATA/'tak_map_veil').symlink_to(outside)
    with pytest.raises(b.BackupError):b.create({'categories':['veil'],'password':PASSWORD})

def test_credential_restore_included(roots):
    (b.ETC/'service-client.key').write_text('private-key')
    (b.DATA/'gateway_data_connection.json').write_text('{"token":"secret"}')
    b.ENV.write_text('TAK_MAP_GATEWAY_DATA_AUTH_MODE=certificate\nTAK_MAP_SERVICE_CLIENT_KEY=/etc/tak-map/service-client.key\nUNRELATED=value\n')
    out=b.create({'categories':['gateway_data'],'password':PASSWORD})
    (b.ETC/'service-client.key').write_text('modified')
    (b.DATA/'gateway_data_connection.json').write_text('modified')
    b.restore({'file':out['file'],'password':PASSWORD,'categories':['gateway_data'],'confirm':'RESTORE'})
    assert (b.ETC/'service-client.key').read_text()=='private-key'
    assert 'secret' in (b.DATA/'gateway_data_connection.json').read_text()

def test_mesh_restore_guard(roots):
    p=b.DATA/'token_mesh';p.mkdir();(p/'group.json').write_text('group')
    out=b.create({'categories':['mesh_sync'],'password':PASSWORD})
    with pytest.raises(b.BackupError,match='explicit journal'):
        b.restore({'file':out['file'],'password':PASSWORD,'categories':['mesh_sync'],'confirm':'RESTORE'})

def test_schedule_isolated_restore_preverifies_and_secret_is_not_in_argv(roots,monkeypatch):
    import types
    p=b.DATA/'token_mesh';p.mkdir();(p/'group-secret.json').write_text('{"key":"example"}')
    out=b.create({'categories':['mesh_sync'],'password':PASSWORD})
    runtime=roots/'runtime';runtime.mkdir()
    original_path=b.Path
    monkeypatch.setattr(b,'Path',lambda value: runtime if str(value)=='/run/tak-map-backup-i674' else original_path(value))
    calls=[]
    def fake_run(cmd,**kw):
        calls.append(cmd)
        return types.SimpleNamespace(returncode=0,stdout=b'',stderr=b'')
    monkeypatch.setattr(b.subprocess,'run',fake_run)
    req={'file':out['file'],'password':PASSWORD,'categories':['mesh_sync'],
         'sync_confirmation':'REPLACE SYNC JOURNALS'}
    result=b.schedule_restore(req)
    assert len(result['read_token'])==64
    assert result['job'] in ' '.join(calls[0])
    assert PASSWORD not in ' '.join(calls[0])
    assert (runtime/result['job']/'request.json').is_file()

def test_browser_inspection_is_encrypted(roots):
    out=b.create({'categories':['veil'],'password':PASSWORD,'browser':{'veil':{'localStorage':{'takmap.veil.auth':'secret-access-token'}}}})
    encrypted=(b.BACKUPS/out['file']).read_bytes()
    assert b'secret-access-token' not in encrypted
    browser=b.archive_browser({'file':out['file'],'password':PASSWORD,'categories':['veil']})
    assert browser['browser']['veil']['localStorage']['takmap.veil.auth']=='secret-access-token'

def test_shared_credentials_independently_restorable(roots, monkeypatch):
    monkeypatch.setattr(b,'EXTRA',{'gateway_data':[b.ETC], 'mesh_sync':[b.ETC], 'data_sync':[b.ETC]})
    (b.ETC/'common-client.key').write_text('original-secret')
    result=b.create({'categories':['gateway_data','mesh_sync','data_sync'],'password':PASSWORD})
    (b.ETC/'common-client.key').write_text('changed')
    b.restore({'file':result['file'],'categories':['data_sync'],'password':PASSWORD,'confirm':'RESTORE','allow_sync_replace':True})
    assert (b.ETC/'common-client.key').read_text()=='original-secret'
