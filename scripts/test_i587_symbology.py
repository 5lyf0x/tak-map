#!/usr/bin/env python3
from __future__ import annotations
import json,pathlib,re
ROOT=pathlib.Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'assets/mil2525/atak-symbology-transport-i580.json').read_text())
assert manifest['version']=='1.3.0-i580'
assert manifest['concept_count']==162
assert manifest['decision_counts']=={'generic':14,'keep':22,'replace':126}
assert manifest['policy']['custom_icons_remaining']==0
assert len(manifest['concepts'])==162
aff_cot={'F':'f','H':'h','N':'n','U':'u'}
cases=0
for concept,row in manifest['concepts'].items():
    assert row['decision'] in {'replace','keep','generic'}
    assert set(row['affiliations'])==set('FHNU')
    for aff,pair in row['affiliations'].items():
        display=pair['display']; transport=pair['transport']
        assert display['name'].startswith({'F':'friendly-','H':'hostile-','N':'neutral-','U':'unknown-'}[aff])
        assert len(transport['sidc'])==15 and transport['sidc'][1]==aff
        assert re.match(r'^a-'+aff_cot[aff]+r'(?:-|$)',transport['cot_type'])
        assert transport['usericon_path']==f"COT_MAPPING_2525C/a-{aff_cot[aff]}/{transport['cot_type']}"
        cases+=1
special={
 ('emergency-food-distribution','F'):('EFOPBL----H----','a-f-O-B-L'),
 ('emergency-hospital','F'):('SFGPIXH---H----','a-f-G-I-X-H'),
 ('emergency-rescue-helicopter','F'):('SFAPMHH--------','a-f-A-M-H-H'),
 ('emergency-search-and-rescue','F'):('SFAPMHH--------','a-f-A-M-H-H'),
 ('air-medevac-helicopter','F'):('SFAPMHO--------','a-f-A-M-H-O'),
 ('ground-equipment-van','F'):('SFGPEVCML------','a-f-G-E-V-C-M-L'),
}
for (concept,aff),expected in special.items():
    t=manifest['concepts'][concept]['affiliations'][aff]['transport']
    assert (t['sidc'],t['cot_type'])==expected
server=(ROOT/'tak_dashboard.py').read_text()
assert '# --- TAK Map i580 reviewed ATAK transport symbology ---' in server
assert "'friendly_affiliation_preserved': True" in server
print(json.dumps({'ok':True,'version':'i587','concepts':162,'decisions':manifest['decision_counts'],'affiliation_cases':cases,'special_official_mappings':len(special)},indent=2))
