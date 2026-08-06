#!/usr/bin/env python3
from html.parser import HTMLParser
import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

spec = importlib.util.spec_from_file_location("tak_dashboard_i520", ROOT / "tak_dashboard.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
html = module.TAK_MAP_HTML


class Collector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.classes = []
        self.collapse_keys = []
        self.script_ids = []
        self.action_text = []
        self._capture_action = 0
        self._action_buffer = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        node_id = attrs.get("id")
        if node_id:
            self.ids.append(node_id)
        classes = (attrs.get("class") or "").split()
        self.classes.extend(classes)
        if attrs.get("data-collapse-key"):
            self.collapse_keys.append(attrs["data-collapse-key"])
        if tag == "script" and node_id:
            self.script_ids.append(node_id)
        if tag in {"button", "a"}:
            self._capture_action += 1
            self._action_buffer.append([])

    def handle_data(self, data):
        if self._capture_action and self._action_buffer:
            self._action_buffer[-1].append(data)

    def handle_endtag(self, tag):
        if tag in {"button", "a"} and self._capture_action and self._action_buffer:
            text = " ".join("".join(self._action_buffer.pop()).split())
            self.action_text.append(text)
            self._capture_action -= 1


collector = Collector()
collector.feed(html)

assert module.TAK_MAP_ITERATION == "i537"
assert module.tak_map_config()["tak_map_iteration"] == "i537"
cleanup = module.tak_map_config()["interface_cleanup"]
assert cleanup["authoritative_first_paint"] is True
assert cleanup["legacy_adsb_controls_removed"] is True
assert cleanup["legacy_tak_client_controls_removed"] is True

# Current account and ADS-B controls must exist in the initial HTML, before JS.
for required in (
    "takAccountV511",
    "takMapAccountBtnV511",
    "takMapAccountMenuV511",
    "adsbHeaderEnableV476",
    "adsbHeaderCountV486",
    "adsbMenuHostV316",
    "adsbRadiusMiles",
    "adsbUpdateInterval",
    "adsbAltitudeFilterV477",
    "adsbAltitudeThresholdV477",
    "adsbCenterSource",
    "adsbCenterLatLon",
    "adsbFilterCivil",
    "adsbFilterMilitary",
    "adsbFilterGovt",
    "adsbFilterUnknown",
):
    assert collector.ids.count(required) == 1, (required, collector.ids.count(required))

assert collector.collapse_keys.count("adsbSettings") == 1
assert collector.classes.count("tak-adsb-authoritative-i520") == 1
assert collector.classes.count("adsb-type-card-v491") == 4

# Retired first-paint elements and modals must not exist.
for retired in (
    "adsbToggleBtn",
    "takClientSetupBtn",
    "mapCertSetupBtn",
    "takClientModal",
    "takClientReminder",
    "takClientDetectBtn",
):
    assert retired not in collector.ids, retired

for retired_script in (
    "v325TakClientIdentitySetup",
    "v327TakClientPrivateKeyHelp",
    "v328TakClientFileDetection",
    "v330TakClientCertificateAutomation",
):
    assert retired_script not in collector.script_ids, retired_script

for retired_label in ("TAK Client", "Cert Setup", "Map Logout", "Enable ADS-B"):
    assert retired_label not in collector.action_text, retired_label

# No delayed markup replacement is allowed to recreate the retired ADS-B card.
assert "body.innerHTML=menuHtml()" not in html
assert "ensureAdsbLayout" not in html
assert "w.openTakClientSetup=open" not in html
assert "takMapLegacyUiGuardI520" not in html
assert "takClientSetupBtn" not in html
assert "mapCertSetupBtn" not in html
assert "takClientReminder" not in html

adsb_worker = (ROOT / "assets/tak-map-adsb-v491.js").read_text()
card_controls = (ROOT / "assets/tak-map-card-controls-v491.js").read_text()
reference = (ROOT / "takmap.js").read_text()
assert "adsbToggleBtn" not in adsb_worker
assert "adsbToggleBtn" not in card_controls
assert "body.innerHTML=menuHtml()" not in reference
assert '<button id="adsbToggleBtn"' not in reference

# Retired standalone TAK Client UI modules must be absent from packaged JS
# reference bundles as well as the served HTML.
for bundle_name in ("takmap.js", "combined_scripts_v287.js"):
    bundle = (ROOT / bundle_name).read_text()
    for retired_token in (
        "takMapTakClientSetupDismissed",
        "takClientSetupBtn",
        "takClientModal",
        "takClientReminder",
        "takClientKeyHelpModal",
        "takClientDetectStyle",
        "takClientAutomationStyle",
    ):
        assert retired_token not in bundle, (bundle_name, retired_token)
    assert "body.innerHTML=menuHtml()" not in bundle, bundle_name
    assert '<button id="adsbToggleBtn"' not in bundle, bundle_name

print("TAK Map i520 authoritative first-paint cleanup test passed")
