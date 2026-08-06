#!/usr/bin/env python3
from pathlib import Path
import importlib.util, sys
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('tak_i566_live_icons',ROOT/'tak_dashboard.py')
m=importlib.util.module_from_spec(spec); sys.modules[spec.name]=m; spec.loader.exec_module(m)
WATER='db450cbe-2fec-47fb-bd2b-ba2db89b035e/Incident Management/water point.png'
rows=[
 {'uid':'P04','callsign':'DS-P04','type':'a-f-G-E-V-U-S','lat':1,'lon':1},
 {'uid':'P17','callsign':'DS-P17','type':'a-f-G-U-C-I-Z','lat':2,'lon':2},
 {'uid':'P15','callsign':'DS-P15','type':'a-n-F-G-R','lat':3,'lon':3},
 {'data':'P16','mission_name':'M','details':{'type':'a-n-G','callsign':'DS-P16','iconsetPath':WATER,'location':{'lat':4,'lon':4}}},
 {'uid':'P13','callsign':'DS-P13','type':'a-f-G-U-C-E-N','lat':5,'lon':5},
 {'uid':'P18','callsign':'DS-P18','type':'a-f-G-U-C-I-Z','lat':6,'lon':6},
 {'uid':'P19','callsign':'DS-P19','type':'a-f-G-U-C-I-Z','lat':7,'lon':7},
 {'uid':'P10','callsign':'DS-P10','type':'a-f-G-E-W-H','lat':8,'lon':8},
 {'uid':'P09','callsign':'DS-P09','type':'a-f-F-N-S','lat':9,'lon':9},
]
objects=[]
for row in rows:
    marker=m._normalize_tak_marker(row,'mission_uids','datasync')
    assert marker, row
    objects.append(marker)
out=m._i566_finalize_payload({'ok':True,'objects':objects,'mission_uids':rows})
assert len(out['objects'])==9
by={str(x.get('callsign') or x.get('name')):x for x in out['objects']}
water=by['DS-P16']
assert water.get('iconsetPath')==WATER,water
assert not water.get('mil2525_file') and not water.get('sidc'),water
sof=by['DS-P09']
assert sof.get('mil2525_file')=='friendly-ground-unit-special-forces.svg',sof
assert sof.get('sidc')=='SFGPUCCIS------',sof
assert (ROOT/'assets/mil2525/svg/friendly-ground-unit-special-forces.svg').is_file()
assert (ROOT/'assets/mil2525/atak-compatibility-aliases-i553.json').is_file()
source=(ROOT/'tak_dashboard.py').read_text()
assert "'/mil2525/atak-compatibility-aliases-i553.json'" in source
print('i566 live nine-point icon diagnostic regression passed')
