#!/usr/bin/env python3
"""Static regression contracts for the i479/i480 responsiveness failure."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = (ROOT / "assets" / "tak-map-tool-ux-v491.js").read_text()
LIFECYCLE = (ROOT / "assets" / "tak-map-object-lifecycle-v491.js").read_text()
DASHBOARD = (ROOT / "tak_dashboard.py").read_text()

# i480 froze the renderer by observing class mutations and then toggling a class
# inside the observer callback. Tool UX must be event-driven and observer-free.
assert "MutationObserver" not in TOOL
assert "attributeFilter:['class']" not in TOOL
assert "document.documentElement" not in TOOL

# Basemap collapse synchronization must never relocate shared sidebar controls.
assert "insertBefore(" not in TOOL
assert "insertAdjacentElement(" not in TOOL
assert "appendChild(controls" not in TOOL
assert "precache_dom_relocation':False" in DASHBOARD

# Status suppression is intentionally limited to the exact status elements. Broad
# class selectors previously risked hiding containers that also held controls.
assert ".map-tool-status" not in TOOL
assert ".tool-status-under-search" not in TOOL
assert "#mapStatus,#toolStatus" in TOOL

# i479 rescanned every button after every DOM mutation and forced repeated sidebar
# redraws during startup. Both behaviors must stay removed.
assert "new MutationObserver" not in LIFECYCLE
assert "d.querySelectorAll('button')" not in LIFECYCLE
assert 'd.querySelectorAll("button")' not in LIFECYCLE
assert "document.querySelectorAll('button')" not in LIFECYCLE
assert 'document.querySelectorAll("button")' not in LIFECYCLE
boot = LIFECYCLE[LIFECYCLE.index("function boot(){"):LIFECYCLE.index("const api={", LIFECYCLE.index("function boot(){"))]
assert "renderLocalDataRows(" not in boot
assert "renderDataSyncRows" not in boot
assert "documentWideObserver:false" in LIFECYCLE
assert "startupSidebarRerenders:false" in LIFECYCLE

print("Runtime responsiveness i491 static contracts passed")
