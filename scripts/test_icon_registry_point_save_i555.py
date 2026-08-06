#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location('tak_map_i555_point_save_test', ROOT / 'tak_dashboard.py')
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
assert spec.loader
spec.loader.exec_module(m)

sample_path = '34ae1613-9645-4222-a9d2-e5f243dea2865/Animals/ant.png'
assert sample_path in m._i555_registry_load()['by_path']

published = []
confirmed_rows = {}

def fake_publish(features, mission, server_host='', creator_uid=''):
    assert len(features) == 1
    feature = features[0]
    published.append((feature, mission))
    props = feature['properties']
    lon, lat = feature['geometry']['coordinates'][:2]
    confirmed_rows[props['uid']] = {
        'uid': props['uid'], 'event_uid': props['uid'], 'cot_uid': props['uid'],
        'mission_name': mission, 'callsign': props['name'], 'name': props['name'],
        'lat': lat, 'lon': lon, 'remarks': props.get('remarks', ''),
        'cot_type': props.get('cot_type', ''), 'sidc': props.get('sidc', ''),
        'iconsetpath': props.get('iconsetpath', ''),
        'mission_cot_xml_i553': props.get('preserve_original_detail_xml_i555', ''),
        'updated': '2026-07-26T20:00:00Z',
    }
    return {'ok': True, 'readback_confirmed': True, 'version': 'fixture'}

m.tak_map_publish_native_points_to_mission_i526 = fake_publish
m._i555_find_point = lambda uid, mission='', force=False: confirmed_rows.get(uid)
m._tak_invalidate_data_sync_cache = lambda: None

payload = {
    'mission_name': 'REGISTRY-MISSION',
    'name': 'Neutral Ant',
    'lat': 34.1234567,
    'lon': -118.7654321,
    'notes': 'Registry custom point',
    'affiliation': 'neutral',
    'symbol': {'kind': 'custom', 'iconsetpath': sample_path},
}
reply, status = m._i555_save_point(payload)
assert status == 200 and reply['ok'], reply
assert reply['redraw_allowed'] is True
feature, mission = published[-1]
props = feature['properties']
assert mission == 'REGISTRY-MISSION'
assert props['preserve_event_uid_i555'] is True
assert props['uid'].startswith('TAKMAP-MISSION-POINT-')
assert props['icon_mode'] == 'custom-registry'
assert props['iconsetpath'] == sample_path
assert props['iconset_path'] == sample_path
assert props['cot_type'] == 'a-n-G'
assert props['sidc'] == ''
assert reply['point']['registered_custom_icon'] is True
assert reply['point']['symbol_locked'] is False
assert reply['point']['iconsetpath'] == sample_path

# A registry-managed custom point can be freely changed to a reviewed MIL symbol.
existing = confirmed_rows[props['uid']]
existing['updated'] = '2026-07-26T20:01:00Z'
current = m._i555_point_public(existing)
edit_payload = {
    'uid': current['uid'],
    'mission_name': current['mission_name'],
    'expected_fingerprint': current['fingerprint'],
    'name': 'Now Armor',
    'lat': current['lat'],
    'lon': current['lon'],
    'notes': 'Changed custom to MIL',
    'affiliation': 'friendly',
    'symbol': {
        'kind': 'milstd2525c',
        'sidc': 'SFGPUCA--------',
        'name': 'friendly-ground-unit-armor',
        'label': 'Armor',
    },
}
reply2, status2 = m._i555_save_point(edit_payload)
assert status2 == 200 and reply2['ok'], reply2
feature2, _ = published[-1]
props2 = feature2['properties']
assert props2['uid'] == current['uid']
assert props2['iconsetpath'] == ''
assert props2['sidc'] == 'SFGPUCA--------'
assert props2['icon_mode'] == 'milstd2525c'

# A stale fingerprint must fail before publication and must not overwrite.
count_before = len(published)
stale = dict(edit_payload)
stale['expected_fingerprint'] = '0' * 64
reply3, status3 = m._i555_save_point(stale)
assert status3 == 409 and reply3['concurrent_edit'] is True, reply3
assert len(published) == count_before

# An arbitrary or unknown path cannot be assigned as though it were registered.
invalid = dict(payload)
invalid['symbol'] = {'kind': 'custom', 'iconsetpath': 'unknown-set/Group/icon.png'}
reply4, status4 = m._i555_save_point(invalid)
assert status4 == 400 and not reply4['ok']
assert len(published) == count_before

# Existing unregistered icons are protected: non-icon edits preserve every
# unknown custom-icon detail element and attribute, while any attempted
# replacement of that unknown path is rejected.
unknown_uid = 'ATAK-UNKNOWN-CUSTOM-01'
unknown_path = 'external-custom-set/Operational/unique.png'
unknown_source_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<event version="2.0" uid="{unknown_uid}" type="a-h-G" how="h-g-i-g-o"
       time="2026-07-26T20:02:00Z" start="2026-07-26T20:02:00Z" stale="2026-07-27T20:02:00Z">
  <point lat="34.5" lon="-118.5" hae="0" ce="9999999" le="9999999"/>
  <detail>
    <contact callsign="Unknown Custom"/>
    <usericon iconsetpath="{unknown_path}" iconsetUid="exact-set-uid"
              filename="unique.png" package="custom-package.zip" customAttribute="preserve-me"/>
    <custom_icon_package uid="pkg-123" filename="custom-package.zip" checksum="opaque-value"/>
    <remarks>keep metadata</remarks>
  </detail>
</event>'''
confirmed_rows[unknown_uid] = {
    'uid': unknown_uid, 'event_uid': unknown_uid, 'cot_uid': unknown_uid,
    'mission_name': 'REGISTRY-MISSION', 'callsign': 'Unknown Custom',
    'lat': 34.5, 'lon': -118.5, 'remarks': 'keep metadata',
    'cot_type': 'a-h-G', 'sidc': '', 'iconsetpath': unknown_path,
    'mission_cot_xml_i553': unknown_source_xml,
    'updated': '2026-07-26T20:02:00Z',
}
unknown_current = m._i555_point_public(confirmed_rows[unknown_uid])
assert unknown_current['symbol_locked'] is True
preserve_payload = {
    'uid': unknown_uid,
    'mission_name': 'REGISTRY-MISSION',
    'expected_fingerprint': unknown_current['fingerprint'],
    'name': 'Unknown Custom Renamed',
    'lat': 34.5, 'lon': -118.5,
    'notes': 'non-icon edit',
    'affiliation': 'hostile',
    'symbol': {'kind': 'unregistered', 'iconsetpath': unknown_path},
}
reply5, status5 = m._i555_save_point(preserve_payload)
assert status5 == 200 and reply5['ok'], reply5
protected_feature = published[-1][0]
protected_props = protected_feature['properties']
assert protected_props['iconsetpath'] == unknown_path
assert protected_props['icon_mode'] == 'unregistered-custom'
assert protected_props['preserve_original_detail_xml_i555'] == unknown_source_xml

# Exercise the real XML builder wrapper, not only the save payload. Mutable
# fields must update while opaque custom icon/package metadata remains intact.
built = m._i526_point_xml(protected_feature, 'REGISTRY-MISSION', '')
assert built['ok'], built
assert built['protected_original_detail_preserved_i555'] is True
assert 'usericon' in built['preserved_detail_tags_i555']
assert 'custom_icon_package' in built['preserved_detail_tags_i555']
root = m.ET.fromstring(built['xml'].encode('utf-8'))
detail = root.find('detail')
assert detail is not None
contact = detail.find('contact')
remarks = detail.find('remarks')
usericon = detail.find('usericon')
package_meta = detail.find('custom_icon_package')
assert contact is not None and contact.attrib.get('callsign') == 'Unknown Custom Renamed'
assert remarks is not None and 'non-icon edit' in (remarks.text or '')
assert usericon is not None
assert usericon.attrib == {
    'iconsetpath': unknown_path,
    'iconsetUid': 'exact-set-uid',
    'filename': 'unique.png',
    'package': 'custom-package.zip',
    'customAttribute': 'preserve-me',
}
assert package_meta is not None and package_meta.attrib == {
    'uid': 'pkg-123',
    'filename': 'custom-package.zip',
    'checksum': 'opaque-value',
}

confirmed_rows[unknown_uid]['updated'] = '2026-07-26T20:03:00Z'
unknown_current2 = m._i555_point_public(confirmed_rows[unknown_uid])
replace_unknown = dict(preserve_payload)
replace_unknown['expected_fingerprint'] = unknown_current2['fingerprint']
replace_unknown['symbol'] = {'kind': 'unregistered', 'iconsetpath': 'external-custom-set/Operational/other.png'}
count_before = len(published)
reply6, status6 = m._i555_save_point(replace_unknown)
assert status6 == 409 and not reply6['ok']
assert len(published) == count_before

# Unknown custom metadata cannot be edited when the authoritative source event
# is unavailable; refusing is safer than reconstructing and damaging it.
missing_xml_uid = 'ATAK-UNKNOWN-CUSTOM-NO-XML'
confirmed_rows[missing_xml_uid] = {
    'uid': missing_xml_uid, 'event_uid': missing_xml_uid, 'cot_uid': missing_xml_uid,
    'mission_name': 'REGISTRY-MISSION', 'callsign': 'Unknown Without XML',
    'lat': 34.6, 'lon': -118.6, 'remarks': 'must not publish',
    'cot_type': 'a-u-G', 'sidc': '', 'iconsetpath': 'external/no-source.png',
    'updated': '2026-07-26T20:04:00Z',
}
missing_current = m._i555_point_public(confirmed_rows[missing_xml_uid])
count_before = len(published)
missing_payload = {
    'uid': missing_xml_uid,
    'mission_name': 'REGISTRY-MISSION',
    'expected_fingerprint': missing_current['fingerprint'],
    'name': 'Unsafe Rename',
    'lat': 34.6, 'lon': -118.6,
    'notes': 'must refuse',
    'affiliation': 'unknown',
    'symbol': {'kind': 'unregistered', 'iconsetpath': 'external/no-source.png'},
}
reply7, status7 = m._i555_save_point(missing_payload)
assert status7 == 409 and not reply7['ok']
assert 'authoritative source CoT detail metadata is unavailable' in reply7['error']
assert len(published) == count_before

print('i555 registry-managed custom point creation, free symbol changes, concurrency protection, and unknown-icon preservation passed')
