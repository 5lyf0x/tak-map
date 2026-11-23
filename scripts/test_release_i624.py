#!/usr/bin/env python3
"""Static release, documentation, runtime, and protected-baseline contract for TAK Map 1.4.0 i624."""
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
    assert (ROOT/'VERSION').read_text().strip()=='1.4.0-i624'
    manifest=json.loads((ROOT/'assets/tak-map-deferred-i553.json').read_text())
    assert manifest['version']=='1.4.0-i624'
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
    assert '/assets/runtime/tak-map-deferred-i553.json?v=1.4.0-i624' in startup
    context=(ROOT/'assets/tak-map-context-sidebar-i572.js').read_text()
    assert 'tak-context-top-overlay-i618' in context
    assert 'gateway-data-nifc-i620' in context and 'nifcContentWidthI620' in context
    adsb=(ROOT/'assets/tak-map-adsb-sidebar-i610.js').read_text()
    assert 'sharedDynamicWidthI618' in adsb and 'scrollbar-gutter:stable' in adsb
    dashboard=(ROOT/'tak_dashboard.py').read_text()
    for marker in ("_I624_PACKAGE_VERSION = '1.4.0-i624'", "context_panel_sizing_i620", "_I624_REPLAY_SCRIPT", "takMapIdentityGuardI624", "replay_jump_i624", "replay_period_identity_i623"):
        assert marker in dashboard, marker
    for rel,markers in {
        'README.md':['# TAK Map v1.4.0 i624','tak-map-v1.4.0-i624.zip','Replay Jump to Date / Time','seconds','docs/CONTEXT-PANELS.md'],
        'docs/INSTALL.md':['1.4.0 i624','tak-map-v624'],
        'docs/RELEASES.md':['## 1.4.0-i624','Jump to Date / Time','## 1.4.0-i623','stable period identities','## 1.4.0-i620','NIFC Fire Perimeter context panels'],
        'docs/CONTEXT-PANELS.md':['ADS-B aircraft','Local Data','Data Sync objects','scrollbar gutter','Multiple panels'],
        'docs/TROUBLESHOOTING.md':['Context panel width or scrollbar','1.4.0 i620'],
        'CONFIGURATION.md':['Context panel sizing in 1.4.0 i620','ADS-B, Local Data, Data Sync, Gateway Data'],
        'docs/CONFIGURATION.md':['Context panels in 1.4.0 i620','CONTEXT-PANELS.md'],
        'CHANGELOG.md':['## 1.4.0-i624','Jump to date / time','## 1.4.0-i623','stable period identities','## 1.4.0-i620','NIFC Fire Perimeter context panels'],
    }.items():
        text=(ROOT/rel).read_text()
        for marker in markers: assert marker in text,(rel,marker)
    expected=json.loads((ROOT/'reports/i613-data-sync-protected-hashes.json').read_text())
    for rel,value in expected.items():
        if rel=='assets/tak-map-context-sidebar-i572.js':
            continue
        if rel=='tak_dashboard.py':
            continue
        actual=sha(ROOT/rel)
        assert actual==value,f'protected baseline changed: {rel}'
        continue
    print('TAK Map 1.4.0 i624 Replay Jump release, docs, shared sizing, and protected baseline contract passed')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
