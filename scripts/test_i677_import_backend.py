"""i677 API-backed import identity: repeated filename creates unique new records."""
import io,json,sys,tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import tak_dashboard as m

def upload(blob,filename='Demo Trail.geojson'):
    boundary='----tak-i677-boundary'
    payload=(('--'+boundary+'\r\nContent-Disposition: form-data; name="files"; filename="'+filename+'"\r\nContent-Type: application/geo+json\r\n\r\n').encode()+blob+b'\r\n'+('--'+boundary+'--\r\n').encode())
    class Req:
        headers={'Content-Type':'multipart/form-data; boundary='+boundary,'Content-Length':str(len(payload))}
        rfile=io.BytesIO(payload)
        def _send_json(self,obj,status=200):self.answer=(obj,status);return self.answer
    h=Req();response,status=m.handle_tak_map_import_upload(h)
    assert status==200 and response['ok'],(status,response)
    return response
with tempfile.TemporaryDirectory() as d:
    p=Path(d)
    with patch.object(m,'TAK_MAP_IMPORT_DIR',p),patch.object(m,'TAK_MAP_IMPORT_FILE',p/'imports.json'):
        ids=[]
        for n in range(2):
            coords=[[-118.0,34.0]]+[[-118.01-0.0002*i,34.01+0.0002*i] for i in range(21+n)]+[[-117.0,35.0]]
            body=json.dumps({'type':'FeatureCollection','features':[{'type':'Feature','geometry':{'type':'LineString','coordinates':coords},'properties':{'name':'Demo Trail','route_control_point_count':13}}]}).encode()
            data=upload(body)
            assert len(data['added'])==1
            item=data['added'][0];ids.append(item['id']); assert item['name']=='Demo Trail.geojson'
            actual=item['features'][0]['coords'];assert len(actual)==len(coords)
            assert actual[0]==[34.0,-118.0] and actual[-1]==[35.0,-117.0]
        assert ids[0]!=ids[1]
        items=m.tak_map_imported()['imports']
        assert len(items)==2 and [i['id'] for i in items]==ids
        assert len(items[0]['features'][0]['coords'])!=len(items[1]['features'][0]['coords'])
print('PASS i677 real import handler: two saved same-name GeoJSON routes, unique IDs, full geometry retained and readable')
