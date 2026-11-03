#!/usr/bin/env python3
"""Finish applying the exact i621 source patch while preserving the GitHub README feature list."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    manifest_path = ROOT / 'assets/tak-map-deferred-i553.json'
    doc = json.loads(manifest_path.read_text(encoding='utf-8'))
    assert doc['version'] == '1.4.0-i620', 'unexpected deferred manifest version'
    doc['version'] = '1.4.0-i621'
    changed = set()
    for script in doc['scripts']:
        if script.get('id') == 'takMapGatewayDataLoaderV476':
            old, new = "const V='i620',POLL_MS=300000;", "const V='i621',POLL_MS=300000;"
            assert old in script['code']
            script['code'] = script['code'].replace(old, new, 1)
            changed.add('gateway')
        elif script.get('id') == 'takMapSidebarPerformanceLoaderV476':
            old, new = "const DEFAULT_VERSION='i620';", "const DEFAULT_VERSION='i621';"
            assert old in script['code']
            script['code'] = script['code'].replace(old, new, 1)
            changed.add('sidebar')
    assert changed == {'gateway', 'sidebar'}, changed
    manifest_path.write_text(json.dumps(doc, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

    readme = ROOT / 'README.md'
    text = readme.read_text(encoding='utf-8')
    title = '# TAK Map v1.4.0 i620\n'
    assert text.startswith(title), 'unexpected GitHub README, refusing to overwrite'
    text = '# TAK Map v1.4.0 i621\n' + text[len(title):]
    anchor = '- **ADS-B Aircraft Tracking** – Monitor aircraft positions, headings, identifiers, movement trails, and aircraft details.\n'
    assert text.count(anchor) == 1, 'ADS-B feature bullet missing or changed'
    extra = ('- **ADS-B Automatic Provider Failover** – Retrieves live aircraft data in priority order: '
             'Airplanes.live → ADSB.lol → ADSB.fi, with automatic recovery, provider cooldowns, '
             'and last-known-good aircraft retention. No TAK Gateway or OpenTAKServer required.\n')
    text = text.replace(anchor, anchor + extra, 1)
    assert 'unzip -o tak-map-v1.4.0-i620.zip' in text
    assert 'cd ~/Downloads/tak-map-v620' in text
    text = text.replace('unzip -o tak-map-v1.4.0-i620.zip', 'unzip -o tak-map-v1.4.0-i621.zip', 1)
    text = text.replace('cd ~/Downloads/tak-map-v620', 'cd ~/Downloads/tak-map-v1.4.0-i621', 1)
    readme.write_text(text, encoding='utf-8')

    assert (ROOT / 'VERSION').read_text().strip() == '1.4.0-i621'
    assert 'airplanes.live' in (ROOT / 'tak_dashboard.py').read_text()
    print('PASS: i621 source patch and preserved GitHub README')

if __name__ == '__main__':
    main()
