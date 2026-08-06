#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / 'assets' / 'tak-map-icon-registry-i555.js').read_text(encoding='utf-8')

# Approved A2 wide-grid / slim-inspector layout.
assert 'grid-template-columns:220px minmax(0,1fr) 248px' in source
assert 'grid-template-columns:repeat(8,minmax(0,1fr))' in source
assert 'registry-inspector-i555' in source
assert 'Operational Summary' not in source  # compact UI, not a redundant visible label
assert 'CoT Type' in source
assert 'Symbol Path' in source
assert '<span>Identity</span>' in source
assert 'Icon Set UID' in source
assert "['Icon Set', 'TAK Map Reviewed MIL-STD-2525C']" in source

# Display-only alpha-bound normalization: 96 canvas / 72 footprint in cards,
# 128 / 96 in the selected preview. The registry bytes are not rewritten.
assert 'async function normalizedUrl' in source
assert 'pixels[(y*scanSize+x)*4+3] > 8' in source
assert 'iconImg(icon,96,72)' in source
assert 'iconImg(icon,128,96)' in source
assert 'state.normalizedCache' in source

# Related panel: alternate affiliations first and exactly 12 total options.
assert "const variantOrder = ['hostile','neutral','unknown','friendly']" in source
assert 'return variants.concat(nearby).slice(0,12)' in source
assert '<span>Related</span>' in source
assert 'related-grid-i555' in source

# Create Point is icon-only and has combined Location plus true Mission selector.
assert 'Create Point' in source
assert 'id="pointLocationI555"' in source
assert 'Latitude, Longitude' in source
assert 'id="pointSaveDestinationI555"' in source
assert 'id="pointMissionI555"' in source
assert 'Data Sync Mission' in source
assert 'Choose Symbol' in source
assert 'Save Point' in source
assert 'pointColorInput' not in source
assert 'type="color"' not in source
assert "source:'TAK Map Point Tool i555'" in source

# Matching source-owned Edit Point window.
assert "modal.id = 'takMapPointEditorI555'" in source
assert 'Edit Point' in source
assert 'id="pointEditorLocationI555"' in source
assert 'Unsaved Changes' in source
assert 'Reset Changes' in source
assert 'Save Changes' in source
assert 'expected_fingerprint:point.fingerprint' in source
assert 'OpenTAKServer did not confirm the update.' in source
assert 'redraw only after confirmation' in source.lower() or 'redrawn only after confirmation' in source.lower()

# Real i555 point API and source-safe popup edit path.
assert "const POINT_API = '/api/tak-map/data-sync-point-i555'" in source
assert 'data-i555-point-edit="1"' in source
assert "document.addEventListener('click', handlePopupPointEdit, true)" in source
assert 'symbol_locked' in source

print('i555 approved registry, Related section, and matching point create/edit UI checks passed')
