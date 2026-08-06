#!/usr/bin/env python3
from __future__ import annotations
import json, os, runpy, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
XML = '''<customMapSource><name>{name}</name><minZoom>0</minZoom><maxZoom>19</maxZoom><tileType>PNG</tileType><url><![CDATA[{url}]]></url></customMapSource>'''

def load(data_dir: str, name: str):
    os.environ['TAK_DASHBOARD_DATA_DIR'] = data_dir
    return runpy.run_path(str(ROOT/'tak_dashboard.py'), run_name=name)

def main() -> int:
    with tempfile.TemporaryDirectory(prefix='tak-map-i517-') as td:
        m1 = load(td, 'tak_map_i517_first')
        first = m1['_i505_parse_basemap_xml'](XML.format(name='Shared One', url='https://EXAMPLE.invalid/tiles/{$z}/{$x}/{$y}.png').encode(), 'one.xml', 'manual')
        duplicate = m1['_i505_parse_basemap_xml'](XML.format(name='Renamed Duplicate', url='https://example.invalid/tiles/{z}/{x}/{y}.png').encode(), 'two.xml', 'manual')
        duplicate['id'] = 'different-id-that-must-not-survive'
        m1['_i505_upsert_custom_basemaps']([first])
        m1['_i505_upsert_custom_basemaps']([duplicate])
        rows = m1['_i505_load_custom_basemaps']()
        assert len(rows) == 1, rows
        assert rows[0]['id'] == first['id'], rows
        assert rows[0]['label'] == 'Renamed Duplicate', rows
        assert rows[0]['shared_catalog'] is True and rows[0]['server_persisted'] is True, rows
        stored = json.loads(Path(m1['TAK_MAP_CUSTOM_BASEMAPS_FILE']).read_text())
        assert stored['version'] == 'i517' and stored['scope'] == 'shared', stored
        assert len(stored['basemaps']) == 1, stored

        # A separate module load models a service restart/new browser lifecycle.
        m2 = load(td, 'tak_map_i517_restart')
        cfg = m2['tak_map_config']()
        assert cfg['tak_map_iteration'] == 'i537', cfg
        imported = [x for x in cfg['basemaps'] if x.get('importedBasemap')]
        assert len(imported) == 1 and imported[0]['label'] == 'Renamed Duplicate', imported
        meta = cfg['composite_basemaps']
        assert meta['shared_server_catalog'] is True
        assert meta['import_permission'] == 'authenticated-user'
        assert meta['remove_permission'] == 'administrator-only'
        assert meta['startup_catalog_hydration'] is True
        assert meta['favorites'] is False and meta['personal_basemaps'] is False

        result = m2['_i505_custom_basemap_result']('Loaded.')
        assert result['version'] == 'i517' and result['catalog_scope'] == 'shared', result
        assert result['server_persisted'] is True and result['removal_admin_only'] is True, result

        # The outer request guard must reject removal by a normal authenticated user.
        class Fake:
            path = '/api/tak-map/custom-basemap-delete'
            def _tak_map_auth_ok(self): return True
            def _tak_map_session(self): return {'username':'operator','is_admin':False}
            def _send_json(self, payload, status=200, headers=None):
                self.payload, self.status = payload, status
                return payload, status
        fake = Fake()
        response = m2['Handler'].do_POST(fake)
        assert fake.status == 403 and fake.payload['admin_required'] is True, response

        html = m2['TAK_MAP_HTML']
        assert 'takMapSharedBasemapCatalogV517' in html
        assert "fetch('/api/tak-map/custom-basemaps'" in html
        assert 'tak-map-basemap-nonadmin-v517' in html
        assert '>i537<' in html, 'sidebar/footer iteration was not updated to i532'
        assert 'data.takMapIteration=V' in html or 'dataset.takMapIteration=V' in html
        assert m2['TAK_MAP_ITERATION'] == 'i537'
        assert 'min-height:100dvh' in m2['TAK_MAP_LOGIN_HTML']

    print('i517 shared persistent basemap catalog, duplicate prevention, admin removal, restart hydration, login centering, and iteration tests passed')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
