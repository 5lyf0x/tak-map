#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'tak_dashboard.py').read_text(errors='replace')
MATCH = re.search(
    r"_I589_CONFIGURE_OTS_UI\s*=\s*r'''(<style id=\"takMapConfigureOtsI589Style\".*?</script>\s*)'''",
    SOURCE,
    re.S,
)
assert MATCH, 'Configure OTS UI block not found'
UI = MATCH.group(1)
EXPECTED = (
    "Type UNENROLL to disconnect and completely remove this TAK Map server's OTS enrollment. "
    "OTS users, groups, Missions, Mission contents, devices and points will not be deleted from OTS."
)
STATUS = {
    'ok': True,
    'version': 'i592',
    'config': {
        'configured': True,
        'enabled': True,
        'login_enabled': True,
        'data_sync_enabled': True,
        'automatic_user_certificate_enrollment': True,
        'automatic_trust_installation': True,
        'base_url': 'https://ots.example',
    },
    'manifest': {
        'status': 'enrolled',
        'file_count': 3,
        'managed_tree_count': 1,
        'remote_certificate_count': 1,
    },
}


def page_html() -> str:
    return f'''<!doctype html><html><head></head><body>
<button id="takClientSetupBtn">Configure OTS</button>
<script>
window.__promptCalls=0;
window.prompt=()=>{{window.__promptCalls++;throw new Error('native prompt must not be used')}};
window.confirm=()=>true;
window.alert=()=>{{}};
const STATUS={json.dumps(STATUS)};
window.fetch=async function(url,opts){{
 if(url==='/api/tak-map/ots/enrollment-status')return {{ok:true,status:200,json:async()=>STATUS}};
 if(url==='/api/tak-map/local-users')return {{ok:true,status:200,json:async()=>({{ok:true,ots_connected:true,users:[]}})}};
 return {{ok:true,status:200,json:async()=>({{ok:true,message:'done',remote_revocation:{{outstanding:[]}}}})}};
}};
</script>{UI}</body></html>'''


def assert_centered(page) -> None:
    box = page.locator('#o589UnenrollDialog .ots-unenroll-panel').bounding_box()
    assert box, 'dialog bounding box missing'
    viewport = page.viewport_size
    assert viewport, 'viewport missing'
    center_x = box['x'] + box['width'] / 2
    center_y = box['y'] + box['height'] / 2
    assert abs(center_x - viewport['width'] / 2) <= 2.0, (center_x, viewport)
    assert abs(center_y - viewport['height'] / 2) <= 2.0, (center_y, viewport)


def main() -> None:
    assert "prompt('Type UNENROLL" not in SOURCE
    assert "devices and points will not be deleted from OTS." in SOURCE
    assert 'configure_ots_unenroll_dialog_i592' in SOURCE

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=True,
            executable_path='/usr/bin/chromium',
            args=['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage', '--no-first-run'],
        )
        page = browser.new_page(viewport={'width': 1280, 'height': 800})
        errors: list[str] = []
        page.on('pageerror', lambda exc: errors.append(str(exc)))
        page.set_content(page_html(), wait_until='domcontentloaded')
        page.wait_for_timeout(250)
        page.evaluate('TakMapConfigureOtsI589.open()')
        page.wait_for_timeout(200)

        page.click('#o589Unenroll')
        page.wait_for_timeout(100)
        overlay = page.locator('#o589UnenrollDialog')
        assert overlay.is_visible()
        assert overlay.get_attribute('aria-hidden') == 'false'
        assert page.evaluate('window.__promptCalls') == 0
        assert page.locator('#o589UnenrollMessage').inner_text() == EXPECTED
        assert_centered(page)

        panel_style = page.locator('#o589UnenrollDialog .ots-unenroll-panel').evaluate(
            "e=>({background:getComputedStyle(e).backgroundImage,border:getComputedStyle(e).borderTopColor})"
        )
        assert 'rgb' in panel_style['background']
        assert panel_style['border'] in ('rgb(183, 190, 195)', 'rgba(183, 190, 195, 1)'), panel_style

        field = page.locator('#o589UnenrollDialog [data-x="u01"]')
        submit = page.locator('#o589UnenrollSubmit')
        assert submit.is_disabled()
        field.fill('unenroll')
        assert submit.is_disabled()
        field.fill('UNENROLL ')
        assert submit.is_disabled()
        field.fill('UNENROLL')
        assert submit.is_enabled()

        page.click('#o589UnenrollCancel')
        assert overlay.is_hidden()
        assert field.input_value() == ''

        page.click('#o589Unenroll')
        assert overlay.is_visible()
        page.keyboard.press('Escape')
        assert overlay.is_hidden()

        page.click('#o589Unenroll')
        assert overlay.is_visible()
        page.locator('#o589UnenrollDialog').click(position={'x': 2, 'y': 2})
        assert overlay.is_hidden()

        assert errors == [], errors
        browser.close()

    print('i592 centered dark-grey/silver OTS unenroll dialog validation passed')


if __name__ == '__main__':
    main()
