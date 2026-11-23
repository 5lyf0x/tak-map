"""Offline release identity, source/asset registration and upgrade-safety gates for i682."""
import os
from pathlib import Path
import re
import stat
import unittest
from unittest.mock import patch
import tempfile
import json

ROOT=Path(__file__).resolve().parents[1]

class I682Release(unittest.TestCase):
    def test_release_identity_and_browser_cache(self):
        import tak_dashboard as d
        self.assertEqual((ROOT/'VERSION').read_text().strip(),'1.4.0-i690')
        self.assertEqual(d.TAK_MAP_ITERATION,'i690')
        self.assertEqual(d.tak_map_config()['version'],'1.4.0-i690')
        self.assertEqual(d.tak_map_config()['tak_map_iteration'],'i690')
        for fragment in ('tak-map-basemap-stack-i673.js?v=1.4.0-i690',
                         'tak-map-route-elevation-i681.js?v=1.4.0-i690'):
            self.assertIn(fragment,d.TAK_MAP_HTML)
        self.assertIn('i690',d.TAK_MAP_HTML)
        self.assertEqual(d.TAK_MAP_HTML.count('</body></html>'),1)
        self.assertIs(d.INDEX_HTML,d.TAK_MAP_HTML)

    def test_release_assets_and_existing_storage_installer(self):
        installer=(ROOT/'install.sh').read_text()
        self.assertTrue((ROOT/'install.sh').stat().st_mode & stat.S_IXUSR)
        for source in ('assets/tak-map-basemap-stack-i673.js',
                       'assets/tak-map-core-i553.js', 'tak_dashboard.py', 'VERSION'):
            self.assertTrue((ROOT/source).is_file())
        for asset in ('assets/tak-map-basemap-stack-i673.js',
                      'assets/tak-map-core-i553.js'):
            self.assertIn('install -m 0644 '+asset,installer)
        self.assertIn('install -m 0644 VERSION',installer)
        self.assertNotRegex(installer, r'rm\s+-rf\s+["\']?\$DATA_DIR')
        self.assertTrue((ROOT/'RELEASE_NOTES_I682.md').is_file())
        self.assertTrue((ROOT/'tests/test_i682_basemap_blend_browser.py').is_file())

    def test_lower_blend_option_label_logic_exists(self):
        js=(ROOT/'assets/tak-map-basemap-stack-i673.js').read_text()
        self.assertIn("if(value)value.textContent=MODE_LABEL[mode]",js)
        self.assertIn('if(after)after.scrollTop=scrollTop',js)
        self.assertIn("'terrain-relief':'Terrain Relief'",js)
        self.assertIn("'contour-emphasis':'Contour Emphasis'",js)

if __name__=='__main__':unittest.main()
