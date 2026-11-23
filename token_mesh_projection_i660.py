"""Read-only CoT mesh projection. Original payload bytes remain canonical in journal."""
import xml.etree.ElementTree as ET

def _tag(x):return x.tag.split('}',1)[-1]

def _coord(x):
    try:
        lat=float(x.attrib['lat']);lon=float(x.attrib['lon'])
        if -90<=lat<=90 and -180<=lon<=180:return [lat,lon]
    except (TypeError,KeyError,ValueError):pass
    return None

def projected_objects(store):
    result=[]
    for binding in store.mission_list():
        if not binding['enabled']:continue
        for head in store.heads(binding['mission']):
            if head['tombstone']:continue
            op=head['operation'];kind=op.get('kind','')
            if kind not in ('POINT','ROUTE','AREA'):continue
            try:
                payload=store.payload_for_operation(op['opId'])
                if not payload or len(payload)>32*1024*1024:continue
                root=ET.fromstring(payload)
                if _tag(root)!='event':continue
                points=[_coord(x) for x in root.iter() if _tag(x)=='point']
                points=[x for x in points if x is not None]
                links=[]
                for node in root.iter():
                    if _tag(node)=='link' and ('point' in node.attrib):
                        try:
                            lat,lon=map(float,node.attrib['point'].split(',')[:2]);
                            if -90<=lat<=90 and -180<=lon<=180:links.append([lat,lon])
                        except (ValueError,TypeError):pass
                coords=links if kind in ('ROUTE','AREA') and len(links)>=2 else points
                if not coords:continue
                title=op.get('uid','Mesh Object')
                for node in root.iter():
                    if _tag(node)=='contact' and node.get('callsign'):
                        title=node.get('callsign');break
                result.append({'uid':str(op.get('uid',''))[:256], 'kind':kind,'name':str(title)[:160], 'mission':binding['name'],'coords':coords[:10000], 'source':'Mesh'})
            except (ValueError,ET.ParseError,KeyError,TypeError):continue
            if len(result)>=2000:return result
    return result
