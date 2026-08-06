#!/usr/bin/env python3
from pathlib import Path
root=Path(__file__).resolve().parents[1]
js=(root/'assets/tak-map-context-sidebar-i570.js').read_text()
assert 'TakMapContextSidebarI570' in js
assert 'L.DomEvent.disableClickPropagation(panel)' in js
assert 'L.DomEvent.disableScrollPropagation(panel)' in js
for event in ('click','mousedown','pointerdown','touchstart','dblclick','contextmenu','wheel'):
    assert repr(event) in js or ('"'+event+'"') in js, event
assert 'stopPropagation' in js
install=(root/'install.sh').read_text()
assert 'tak-map-context-sidebar-i570.js' in install
print('i570 contextual sidebar isolates pointer, mouse, touch, wheel, and click propagation from Leaflet')
