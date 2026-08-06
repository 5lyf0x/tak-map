#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, json, pathlib, re, sys
from collections import Counter

ROOT=pathlib.Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'assets/mil2525/atak-symbology-transport-i580.json').read_text())
assert manifest['version']=='1.3.0-i580'
assert manifest['concept_count']==162
assert manifest['decision_counts']=={'generic':14,'keep':22,'replace':126}
assert manifest['policy']['custom_icons_remaining']==0
assert len(manifest['concepts'])==162

aff_cot={'F':'f','H':'h','N':'n','U':'u'}
for concept,row in manifest['concepts'].items():
    assert row['decision'] in {'replace','keep','generic'}
    assert set(row['affiliations'])==set('FHNU')
    for aff,pair in row['affiliations'].items():
        display=pair['display']; transport=pair['transport']
        assert display['name'].startswith({'F':'friendly-','H':'hostile-','N':'neutral-','U':'unknown-'}[aff])
        assert transport['sidc'] and transport['cot_type']
        assert re.match(r'^a-'+aff_cot[aff]+r'(?:-|$)',transport['cot_type'])
        assert transport['usericon_path']==f"COT_MAPPING_2525C/a-{aff_cot[aff]}/{transport['cot_type']}"
        # 2525C warfighting and Emergency Management scheme symbols both put
        # affiliation in position 2.
        assert len(transport['sidc'])==15 and transport['sidc'][1]==aff

special={
 ('emergency-food-distribution','F'):('EFOPBL----H----','a-f-O-B-L'),
 ('emergency-hospital','F'):('SFGPIXH---H----','a-f-G-I-X-H'),
 ('emergency-rescue-helicopter','F'):('SFAPMHH--------','a-f-A-M-H-H'),
 ('emergency-search-and-rescue','F'):('SFAPMHH--------','a-f-A-M-H-H'),
 ('air-medevac-helicopter','F'):('SFAPMHO--------','a-f-A-M-H-O'),
}
for (concept,aff),expected in special.items():
    t=manifest['concepts'][concept]['affiliations'][aff]['transport']
    assert (t['sidc'],t['cot_type'])==expected

spec=importlib.util.spec_from_file_location('tak_i581_symbology',ROOT/'tak_dashboard.py')
mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod
assert spec.loader is not None; spec.loader.exec_module(mod)
assert mod.TAK_MAP_ITERATION=='i581'
cfg=mod.tak_map_config()
assert cfg['version']=='1.3.0-i581'
assert cfg['atak_symbology_transport_i580']['concept_count']==162
assert cfg['atak_symbology_transport_i580']['initial_load_release_gate'] is True
assert '/assets/runtime/tak-map-startup-i553.js?v=1.3.0-i581' in mod.TAK_MAP_HTML
assert '/assets/runtime/tak-map-data-sync-access-i576.js?v=1.3.0-i581' in mod.TAK_MAP_HTML

samples=[
 ('friendly-emergency-food-distribution','SFEPQ----------','a-f-E-Q','EFOPBL----H----','a-f-O-B-L'),
 ('friendly-emergency-hospital','SFEPA----------','a-f-E-A','SFGPIXH---H----','a-f-G-I-X-H'),
 ('friendly-emergency-rescue-helicopter','SFEPRH---------','a-f-E-R-H','SFAPMHH--------','a-f-A-M-H-H'),
 ('friendly-emergency-search-and-rescue','SFEPR----------','a-f-E-R','SFAPMHH--------','a-f-A-M-H-H'),
 ('friendly-air-medevac-helicopter','SFAPMHM--------','a-f-A-M-H-M','SFAPMHO--------','a-f-A-M-H-O'),
]
for name,display_sidc,display_cot,transport_sidc,transport_cot in samples:
    feature={'type':'Feature','geometry':{'type':'Point','coordinates':[-117.1,34.1]},'properties':{
        'name':'TEST','mil2525_name':name,'sidc':display_sidc,'cot_type':display_cot}}
    mapped=mod._i580_transport_feature(feature)
    props=mapped['properties']
    assert props['sidc']==transport_sidc and props['cot_type']==transport_cot
    assert props['takmap_display_sidc_i580']==display_sidc
    assert mod._i526_point_type(mapped)==transport_cot
    built=mod._i526_point_xml(mapped,'I580-TEST','')
    assert built['ok'] and built['sidc']==transport_sidc and built['cot_type']==transport_cot
    xml=built['xml']
    assert f'type="{transport_cot}"' in xml
    assert f'sidc="{transport_sidc}"' in xml
    assert 'symbologyConceptI580=' in xml and 'displaySidcI580=' in xml and 'transportSidcI580=' in xml
    assert f'iconsetpath="COT_MAPPING_2525C/a-f/{transport_cot}"' in xml

# Same-affiliation generic mappings never cross affiliation.
for concept,row in manifest['concepts'].items():
    if row['decision']!='generic': continue
    for aff,pair in row['affiliations'].items():
        assert pair['transport']['sidc'][1]==aff
        assert pair['transport']['cot_type'].split('-')[1]==aff_cot[aff]

print(json.dumps({'ok':True,'version':'i581','concepts':162,'decisions':manifest['decision_counts'],'affiliation_cases':648,'special_official_mappings':5},indent=2))
