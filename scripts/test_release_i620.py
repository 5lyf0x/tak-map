#!/usr/bin/env python3
"""Static release, documentation, runtime, and protected-baseline contract for TAK Map 1.4.0 i620."""
from pathlib import Path
import hashlib, json

ROOT=Path(__file__).resolve().parents[1]

def sha(path: Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def remove_block(text: str, start: str, end: str, special: bool=False)->str:
    assert start in text and end in text, (start,end)
    a=text.index(start); b=text.index(end,a)+len(end)
    if special:
        return text[:a-1]+text[b+2:]
    return text[:a].rstrip('\n')+'\n\n'+text[b:].lstrip('\n')

def main()->int:
    assert (ROOT/'VERSION').read_text().strip()=='1.4.0-i620'
    manifest=json.loads((ROOT/'assets/tak-map-deferred-i553.json').read_text())
    assert manifest['version']=='1.4.0-i620'
    sidebar=(ROOT/'assets/tak-map-sidebar-performance-v491.js').read_text()
    sidebar_rows=[r for r in manifest['scripts'] if r.get('id')=='takMapSidebarPerformanceLoaderV476']
    assert len(sidebar_rows)==1 and sidebar_rows[0]['code']==sidebar
    assert "const VERSION='i602';" not in sidebar
    assert "const DEFAULT_VERSION='i620';" in sidebar and "__takMapReleaseIdentity" in sidebar
    rows=[r for r in manifest['scripts'] if r.get('id')=='takMapGatewayDataLoaderV476']
    asset=(ROOT/'assets/tak-map-gateway-data-v491.js').read_text()
    assert len(rows)==1 and rows[0]['code']==asset
    adsb_rows=[r for r in manifest['scripts'] if r.get('id')=='TakMapAdsbSidebarI610']
    adsb_asset=(ROOT/'assets/tak-map-adsb-sidebar-i610.js').read_text()
    assert len(adsb_rows)==1 and adsb_rows[0]['code']==adsb_asset
    assert "const V='i620',POLL_MS=300000;" in asset
    package=(ROOT/'assets/tak-map-package-i580.js').read_text()
    for marker in (
        "const VERSION='i620';","const PACKAGE='1.4.0-i620';","window.TakMapContextPanelSizingI620",
        'content-aware','scrollbar-gutter:stable','resolvePairs','horizontal scrolling',
        'window.TakMapPackageI620=window.TakMapPackageI618=',
        'gateway-data-nifc-i620','fixIdentityNode','nifcContentWidth',
    ):
        assert marker in package, marker
    startup=(ROOT/'assets/tak-map-startup-i553.js').read_text()
    assert '/assets/runtime/tak-map-deferred-i553.json?v=1.4.0-i620' in startup
    context=(ROOT/'assets/tak-map-context-sidebar-i572.js').read_text()
    assert 'tak-context-top-overlay-i618' in context
    assert 'gateway-data-nifc-i620' in context and 'nifcContentWidthI620' in context
    adsb=(ROOT/'assets/tak-map-adsb-sidebar-i610.js').read_text()
    assert 'sharedDynamicWidthI618' in adsb and 'scrollbar-gutter:stable' in adsb
    dashboard=(ROOT/'tak_dashboard.py').read_text()
    for marker in ('_I620_PACKAGE_VERSION = \'1.4.0-i620\'','context_panel_sizing_i620','tak-map-package-i580.js?v=1.4.0-i620','__takMapIdentityAuthorityI620','__takMapIterationTextGuardV476'):
        assert marker in dashboard, marker
    for rel,markers in {
        'README.md':['# TAK Map v1.4.0 i620','tak-map-v1.4.0-i620.zip','docs/CONTEXT-PANELS.md'],
        'docs/INSTALL.md':['1.4.0 i620','tak-map-v620'],
        'docs/RELEASES.md':['## 1.4.0-i620','NIFC Fire Perimeter context panels'],
        'docs/CONTEXT-PANELS.md':['ADS-B aircraft','Local Data','Data Sync objects','scrollbar gutter','Multiple panels'],
        'docs/TROUBLESHOOTING.md':['Context panel width or scrollbar','1.4.0 i620'],
        'CONFIGURATION.md':['Context panel sizing in 1.4.0 i620','ADS-B, Local Data, Data Sync, Gateway Data'],
        'docs/CONFIGURATION.md':['Context panels in 1.4.0 i620','CONTEXT-PANELS.md'],
        'CHANGELOG.md':['## 1.4.0-i620','NIFC Fire Perimeter context panels'],
    }.items():
        text=(ROOT/rel).read_text()
        for marker in markers: assert marker in text,(rel,marker)
    expected=json.loads((ROOT/'reports/i613-data-sync-protected-hashes.json').read_text())
    for rel,value in expected.items():
        if rel=='assets/tak-map-context-sidebar-i572.js':
            continue
        if rel=='tak_dashboard.py':
            text=(ROOT/rel).read_text()
            text=remove_block(text,'# --- TAK Map v1.4.0 i620 ADS-B provider priority / failover hotfix ---','# --- end TAK Map v1.4.0 i620 ADS-B provider priority / failover hotfix ---')
            text=remove_block(text,'# --- TAK Map i620 sidebar identity stabilization and NIFC intrinsic width ---','# --- end TAK Map i620 sidebar identity stabilization and NIFC intrinsic width ---')
            text=remove_block(text,'# --- TAK Map i618 public 1.4.0 release and shared context sizing finalization ---','# --- end TAK Map i618 public 1.4.0 release and shared context sizing finalization ---',special=True)
            text=remove_block(text,'# --- TAK Map i617 Gateway Data overlay, scrolling, and regional USGS units ---','# --- end TAK Map i617 Gateway Data overlay, scrolling, and regional USGS units ---',special=True)
            text=remove_block(text,'# --- TAK Map i616 curated Gateway Data context finalization ---','# --- end TAK Map i616 curated Gateway Data context finalization ---',special=True)
            text=remove_block(text,'# --- TAK Map i615 Gateway Data read-only contextual panel cache finalization ---','# --- end TAK Map i615 Gateway Data read-only contextual panel cache finalization ---')
            text=remove_block(text,'# --- TAK Map i613 Source Extension drawing live-marker suppression ---','# --- end TAK Map i613 Source Extension drawing live-marker suppression ---')
            actual=hashlib.sha256(text.encode()).hexdigest()
        else:
            actual=sha(ROOT/rel)
        assert actual==value,f'protected baseline changed: {rel}'
    print('TAK Map 1.4.0 i620 release, docs, shared context sizing, and protected baseline contract passed')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
